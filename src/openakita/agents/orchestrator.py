"""
AgentOrchestrator — central multi-agent coordinator.

Lightweight in-process design using asyncio. Replaces the old ZMQ-based system.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from openakita.channels import MessageGateway

logger = logging.getLogger(__name__)

MAX_DELEGATION_DEPTH = 5
DEFAULT_TIMEOUT = 120.0  # seconds


@dataclass
class DelegationRequest:
    """A request to delegate work to another agent."""

    from_agent: str
    to_agent: str
    message: str
    session_key: str
    depth: int = 0
    parent_request_id: str | None = None


@dataclass
class AgentHealth:
    """Health metrics for an agent."""

    agent_id: str
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    total_latency_ms: float = 0.0
    last_error: str | None = None
    last_active: float = field(default_factory=time.time)

    @property
    def success_rate(self) -> float:
        return self.successful / max(self.total_requests, 1)

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / max(self.successful, 1)


class AgentMailbox:
    """Per-agent async message queue."""

    def __init__(self, agent_id: str, maxsize: int = 100):
        self.agent_id = agent_id
        self._queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=maxsize)

    async def send(self, message: dict) -> None:
        await self._queue.put(message)

    async def receive(self, timeout: float = DEFAULT_TIMEOUT) -> dict | None:
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    @property
    def pending(self) -> int:
        return self._queue.qsize()


class AgentOrchestrator:
    """
    Central coordinator for multi-agent mode.

    Responsibilities:
    - Route messages to the correct agent based on session's agent_profile_id
    - Support agent delegation with depth limits
    - Handle timeouts, failures, cancellation
    - Track agent health metrics
    """

    def __init__(self) -> None:
        self._mailboxes: dict[str, AgentMailbox] = {}
        self._health: dict[str, AgentHealth] = {}
        self._active_tasks: dict[str, asyncio.Task] = {}

        # Lazy-initialised dependencies
        self._profile_store = None  # ProfileStore
        self._pool = None           # AgentInstancePool
        self._fallback = None       # FallbackResolver
        self._gateway: MessageGateway | None = None

    # ------------------------------------------------------------------
    # External wiring
    # ------------------------------------------------------------------

    def set_gateway(self, gateway: MessageGateway | None) -> None:
        """Inject the MessageGateway reference (set after both are created)."""
        self._gateway = gateway

    # ------------------------------------------------------------------
    # Lazy dependency bootstrap
    # ------------------------------------------------------------------

    def _ensure_deps(self) -> None:
        """Lazily initialise ProfileStore, AgentInstancePool, FallbackResolver.

        Raises RuntimeError if any dependency fails to initialise.
        """
        try:
            if self._profile_store is None:
                from openakita.agents.profile import ProfileStore
                from openakita.config import settings

                self._profile_store = ProfileStore(settings.data_dir / "agents")

            if self._pool is None:
                from openakita.agents.factory import AgentFactory, AgentInstancePool

                self._pool = AgentInstancePool(AgentFactory())

            if self._fallback is None:
                from openakita.agents.fallback import FallbackResolver

                self._fallback = FallbackResolver(self._profile_store)
        except Exception as e:
            logger.error(f"[Orchestrator] Failed to initialise dependencies: {e}", exc_info=True)
            raise RuntimeError(f"Orchestrator dependency init failed: {e}") from e

    # ------------------------------------------------------------------
    # Mailbox / health helpers
    # ------------------------------------------------------------------

    def get_mailbox(self, agent_id: str) -> AgentMailbox:
        if agent_id not in self._mailboxes:
            self._mailboxes[agent_id] = AgentMailbox(agent_id)
        return self._mailboxes[agent_id]

    def _get_health(self, agent_id: str) -> AgentHealth:
        if agent_id not in self._health:
            self._health[agent_id] = AgentHealth(agent_id=agent_id)
        return self._health[agent_id]

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def handle_message(self, session: Any, message: str) -> str:
        """
        Main entry point — called from agent_handler in main.py.
        Routes the message to the appropriate agent based on session context.
        """
        self._ensure_deps()

        # Use session.id (UUID) as the canonical key for both the agent pool
        # and active-task tracking so we avoid mismatches.
        sid = session.id
        agent_profile_id = getattr(session.context, "agent_profile_id", "default")

        task = asyncio.create_task(
            self._dispatch(
                session=session,
                message=message,
                agent_profile_id=agent_profile_id,
                depth=0,
            )
        )
        self._active_tasks[sid] = task
        try:
            return await task
        finally:
            self._active_tasks.pop(sid, None)

    # ------------------------------------------------------------------
    # Dispatch with timeout / fallback / error handling
    # ------------------------------------------------------------------

    async def _dispatch(
        self,
        session: Any,
        message: str,
        agent_profile_id: str,
        depth: int,
        timeout: float = DEFAULT_TIMEOUT,
        from_agent: str | None = None,
    ) -> str:
        """Dispatch a message to a specific agent with timeout and error handling."""
        if depth >= MAX_DELEGATION_DEPTH:
            return f"⚠️ 委派深度超限 (max={MAX_DELEGATION_DEPTH})"

        # Clear delegation chain at start of new request (depth 0)
        if depth == 0:
            session.context.delegation_chain = []
        # Record delegation in chain when depth > 0
        elif depth > 0:
            chain = getattr(session.context, "delegation_chain", [])
            chain.append({
                "from": from_agent or "parent",
                "to": agent_profile_id,
                "depth": depth,
                "timestamp": time.time(),
            })
            session.context.delegation_chain = chain

        health = self._get_health(agent_profile_id)
        health.total_requests += 1
        health.last_active = time.time()
        start = time.monotonic()

        try:
            result = await asyncio.wait_for(
                self._execute_agent(session, message, agent_profile_id),
                timeout=timeout,
            )
            elapsed = (time.monotonic() - start) * 1000
            health.successful += 1
            health.total_latency_ms += elapsed

            self._fallback.record_success(agent_profile_id)
            return result

        except asyncio.TimeoutError:
            health.failed += 1
            health.last_error = "timeout"
            self._fallback.record_failure(agent_profile_id)
            logger.warning(
                f"[Orchestrator] Agent {agent_profile_id} timed out after {timeout}s"
            )
            return await self._try_fallback_or(
                session, message, agent_profile_id, depth, timeout,
                default=f"⏱️ Agent `{agent_profile_id}` 处理超时 ({timeout}s)",
            )

        except asyncio.CancelledError:
            health.failed += 1
            health.last_error = "cancelled"
            return "🚫 请求已取消"

        except Exception as e:
            health.failed += 1
            health.last_error = str(e)
            logger.error(
                f"[Orchestrator] Agent {agent_profile_id} failed: {e}",
                exc_info=True,
            )
            self._fallback.record_failure(agent_profile_id)
            return await self._try_fallback_or(
                session, message, agent_profile_id, depth, timeout,
                default=f"❌ Agent `{agent_profile_id}` 处理失败: {e}",
            )

    async def _try_fallback_or(
        self,
        session: Any,
        message: str,
        agent_profile_id: str,
        depth: int,
        timeout: float,
        *,
        default: str,
    ) -> str:
        """
        If the FallbackResolver says we should degrade, dispatch to the
        fallback profile; otherwise return *default*.
        """
        if self._fallback.should_use_fallback(agent_profile_id):
            effective_id = self._fallback.get_effective_profile(agent_profile_id)
            if effective_id != agent_profile_id:
                logger.info(
                    f"[Orchestrator] Falling back from "
                    f"{agent_profile_id} to {effective_id}"
                )
                return await self._dispatch(
                    session, message, effective_id, depth + 1, timeout,
                    from_agent=agent_profile_id,
                )
        return default

    # ------------------------------------------------------------------
    # Agent execution
    # ------------------------------------------------------------------

    async def _execute_agent(
        self, session: Any, message: str, agent_profile_id: str
    ) -> str:
        """Execute a message using the specified agent profile."""
        if self._profile_store is None or self._pool is None:
            return "⚠️ Orchestrator 未正确初始化，请检查日志"

        profile = self._profile_store.get(agent_profile_id)
        if profile is None:
            profile = self._profile_store.get("default")
        if profile is None:
            return f"⚠️ 无法找到 Agent Profile: {agent_profile_id}"

        agent = await self._pool.get_or_create(session.id, profile)

        session_messages = session.context.get_messages()
        response = await agent.chat_with_session(
            message=message,
            session_messages=session_messages,
            session_id=session.id,
            session=session,
            gateway=self._gateway,
        )
        return response

    # ------------------------------------------------------------------
    # Delegation (called by agent tools)
    # ------------------------------------------------------------------

    async def delegate(
        self,
        session: Any,
        from_agent: str,
        to_agent: str,
        message: str,
        depth: int = 0,
        reason: str = "",
    ) -> str:
        """
        Delegate work from one agent to another.
        Called by agent tools (e.g. delegate_to_agent).
        """
        self._ensure_deps()
        logger.info(
            f"[Orchestrator] Delegation: {from_agent} -> {to_agent} (depth={depth})"
        )
        # Emit handoff event for SSE stream (session.context.handoff_events)
        if session and hasattr(session, "context") and hasattr(session.context, "handoff_events"):
            session.context.handoff_events.append({
                "from_agent": from_agent,
                "to_agent": to_agent,
                "reason": reason or "",
            })
        return await self._dispatch(
            session, message, to_agent, depth + 1, from_agent=from_agent
        )

    # ------------------------------------------------------------------
    # Multi-agent collaboration
    # ------------------------------------------------------------------

    async def start_collaboration(self, session: Any, agent_ids: list[str]) -> str:
        """Start a multi-agent collaboration session."""
        ctx = session.context
        ctx.active_agents = list(set(agent_ids))
        logger.info(
            f"[Orchestrator] Collaboration started: {agent_ids} in {session.session_key}"
        )
        return f"✅ Collaboration started with {len(agent_ids)} agents"

    async def get_active_agents(self, session: Any) -> list[str]:
        """Get currently active agents in a session."""
        return getattr(session.context, "active_agents", [])

    def get_delegation_chain(self, session: Any) -> list[dict]:
        """Get the delegation chain for the current session."""
        return getattr(session.context, "delegation_chain", [])

    # ------------------------------------------------------------------
    # Cancellation
    # ------------------------------------------------------------------

    def cancel_request(self, session_id: str) -> bool:
        """Cancel an active request for a session (by session.id UUID)."""
        task = self._active_tasks.get(session_id)
        if task and not task.done():
            task.cancel()
            return True
        return False

    # ------------------------------------------------------------------
    # Health / monitoring
    # ------------------------------------------------------------------

    def get_health_stats(self) -> dict[str, dict]:
        """Get health metrics for all agents."""
        return {
            agent_id: {
                "total_requests": h.total_requests,
                "successful": h.successful,
                "failed": h.failed,
                "success_rate": round(h.success_rate, 3),
                "avg_latency_ms": round(h.avg_latency_ms, 1),
                "last_error": h.last_error,
                "pending_messages": (
                    self._mailboxes[agent_id].pending
                    if agent_id in self._mailboxes
                    else 0
                ),
            }
            for agent_id, h in self._health.items()
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start background tasks (pool reaper, etc.)."""
        self._ensure_deps()
        await self._pool.start()
        logger.info("[Orchestrator] Started")

    async def shutdown(self) -> None:
        """Clean shutdown: cancel active tasks, release pool."""
        for task in self._active_tasks.values():
            if not task.done():
                task.cancel()
        self._active_tasks.clear()

        if self._pool:
            await self._pool.stop()

        logger.info("[Orchestrator] Shutdown complete")
