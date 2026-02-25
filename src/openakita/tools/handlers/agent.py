"""
Multi-agent handler — delegate_to_agent and create_agent.

Only registered when settings.multi_agent_enabled is True.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...core.agent import Agent

logger = logging.getLogger(__name__)

DYNAMIC_AGENT_POLICIES = {
    "max_agents_per_session": 3,
    "max_delegation_depth": 5,
    "forbidden_tools": {"create_agent"},
    "max_lifetime_minutes": 60,
}


class AgentToolHandler:
    """Handles delegate_to_agent and create_agent tool calls."""

    TOOLS = ["delegate_to_agent", "create_agent"]

    def __init__(self, agent: Agent):
        self.agent = agent

    async def handle(self, tool_name: str, params: dict[str, Any]) -> str:
        if tool_name == "delegate_to_agent":
            return await self._delegate(params)
        elif tool_name == "create_agent":
            return await self._create(params)
        return f"❌ Unknown agent tool: {tool_name}"

    # ------------------------------------------------------------------
    # delegate_to_agent
    # ------------------------------------------------------------------

    async def _delegate(self, params: dict[str, Any]) -> str:
        agent_id = (params.get("agent_id") or "").strip()
        message = (params.get("message") or "").strip()
        reason = (params.get("reason") or "").strip()

        if not agent_id:
            return "❌ agent_id is required"
        if not message:
            return "❌ message is required"

        orchestrator = self._get_orchestrator()
        if orchestrator is None:
            return "❌ Orchestrator not available — multi-agent mode may not be fully initialised"

        session = getattr(self.agent, "_current_session", None)
        if session is None:
            return "❌ No active session — delegation requires a session context"

        current_agent = getattr(
            getattr(session, "context", None), "agent_profile_id", "default"
        ) or "default"

        logger.info(
            f"[AgentToolHandler] Delegation: {current_agent} -> {agent_id} | reason={reason}"
        )

        try:
            result = await orchestrator.delegate(
                session=session,
                from_agent=current_agent,
                to_agent=agent_id,
                message=message,
                reason=reason,
            )
            return str(result)
        except Exception as e:
            logger.error(f"[AgentToolHandler] Delegation failed: {e}", exc_info=True)
            return f"❌ Delegation to {agent_id} failed: {e}"

    # ------------------------------------------------------------------
    # create_agent
    # ------------------------------------------------------------------

    async def _create(self, params: dict[str, Any]) -> str:
        name = (params.get("name") or "").strip()
        description = (params.get("description") or "").strip()
        skills = params.get("skills") or []
        custom_prompt = (params.get("custom_prompt") or "").strip()

        if not name:
            return "❌ name is required"
        if not description:
            return "❌ description is required"

        session = getattr(self.agent, "_current_session", None)
        if session is None:
            return "❌ No active session — agent creation requires a session context"

        # Enforce per-session limit
        ctx = getattr(session, "context", None)
        history: list[dict] = getattr(ctx, "agent_switch_history", []) if ctx else []
        created_count = sum(1 for h in history if h.get("type") == "dynamic_create")
        max_allowed = DYNAMIC_AGENT_POLICIES["max_agents_per_session"]
        if created_count >= max_allowed:
            return f"❌ Maximum dynamic agents per session reached ({max_allowed})"

        from ...agents.profile import (
            AgentProfile,
            AgentType,
            ProfileStore,
            SkillsMode,
        )
        from ...config import settings

        session_key = getattr(session, "session_key", "") or getattr(session, "id", "")
        short_key = str(session_key)[:8] if session_key else "anon"
        profile_id = f"dynamic_{name.lower().replace(' ', '_')}_{short_key}"

        profile = AgentProfile(
            id=profile_id,
            name=name,
            description=description,
            type=AgentType.DYNAMIC,
            skills=skills,
            skills_mode=SkillsMode.INCLUSIVE if skills else SkillsMode.ALL,
            custom_prompt=custom_prompt,
            icon="🤖",
            color="#6b7280",
            created_by="ai",
        )

        store = ProfileStore(settings.data_dir / "agents")
        store.save(profile)

        # Record in session history (if available)
        if ctx is not None and hasattr(ctx, "agent_switch_history"):
            ctx.agent_switch_history.append({
                "type": "dynamic_create",
                "agent_id": profile_id,
                "name": name,
                "at": datetime.now(timezone.utc).isoformat(),
            })

        logger.info(f"[AgentToolHandler] Created dynamic agent: {profile_id}")
        return f"✅ Agent created: {profile_id} ({name})"

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _get_orchestrator(self):
        """Try to find the orchestrator from the main module globals."""
        try:
            from ...main import _orchestrator
            return _orchestrator
        except (ImportError, AttributeError):
            return None


def create_handler(agent: Agent):
    """Factory function following the project convention."""
    handler = AgentToolHandler(agent)
    return handler.handle
