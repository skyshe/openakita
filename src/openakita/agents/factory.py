"""
AgentFactory — 根据 AgentProfile 创建差异化 Agent 实例
AgentInstancePool — per-session 实例管理 + 空闲回收
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import TYPE_CHECKING, Any

from .profile import AgentProfile, SkillsMode

if TYPE_CHECKING:
    from openakita.core.agent import Agent

logger = logging.getLogger(__name__)

_IDLE_TIMEOUT_SECONDS = 30 * 60  # 30 分钟空闲回收
_REAP_INTERVAL_SECONDS = 60  # 每分钟检查一次


class AgentFactory:
    """
    根据 AgentProfile 创建 Agent 实例。

    - 按 profile 配置过滤技能
    - 注入自定义提示词
    - 设置 agent name/icon
    """

    async def create(self, profile: AgentProfile, **kwargs: Any) -> Agent:
        """
        创建并初始化一个 Agent 实例。

        Args:
            profile: Agent 蓝图
            **kwargs: 传递给 Agent.__init__ 的额外参数
        """
        from openakita.core.agent import Agent

        agent = Agent(name=profile.get_display_name(), **kwargs)
        agent._agent_profile = profile

        await agent.initialize(start_scheduler=False)

        self._apply_skill_filter(agent, profile)

        if profile.custom_prompt:
            agent._custom_prompt_suffix = profile.custom_prompt

        logger.info(
            f"AgentFactory created: {profile.id} "
            f"(skills_mode={profile.skills_mode.value}, "
            f"skills={profile.skills})"
        )
        return agent

    @staticmethod
    def _apply_skill_filter(agent: Agent, profile: AgentProfile) -> None:
        """按 profile 配置过滤技能"""
        if profile.skills_mode == SkillsMode.ALL or not profile.skills:
            return

        registry = agent.skill_registry
        all_skills = [skill.name for skill in registry.list_all()]

        if profile.skills_mode == SkillsMode.INCLUSIVE:
            keep = set(profile.skills)
            for skill_name in all_skills:
                if skill_name not in keep:
                    registry.unregister(skill_name)
        elif profile.skills_mode == SkillsMode.EXCLUSIVE:
            exclude = set(profile.skills)
            for skill_name in all_skills:
                if skill_name in exclude:
                    registry.unregister(skill_name)


class _PoolEntry:
    __slots__ = ("agent", "profile_id", "session_id", "created_at", "last_used")

    def __init__(self, agent: Agent, profile_id: str, session_id: str):
        self.agent = agent
        self.profile_id = profile_id
        self.session_id = session_id
        self.created_at = time.monotonic()
        self.last_used = time.monotonic()

    def touch(self) -> None:
        self.last_used = time.monotonic()

    @property
    def idle_seconds(self) -> float:
        return time.monotonic() - self.last_used


class AgentInstancePool:
    """
    Agent 实例池 — per-session 绑定 + 空闲自动回收。

    - get_or_create(session_id, profile) → Agent
    - release(session_id) → 标记空闲
    - 后台 reaper 定期回收空闲超时的实例
    """

    def __init__(
        self,
        factory: AgentFactory | None = None,
        idle_timeout: float = _IDLE_TIMEOUT_SECONDS,
    ):
        self._factory = factory or AgentFactory()
        self._idle_timeout = idle_timeout
        self._pool: dict[str, _PoolEntry] = {}
        # threading.RLock protects _pool from concurrent access between async
        # methods and the synchronous _reap_idle() reaper.
        self._lock = threading.RLock()
        # Per-session asyncio locks prevent duplicate agent creation when
        # multiple coroutines call get_or_create for the same session concurrently.
        self._create_locks: dict[str, asyncio.Lock] = {}
        self._reaper_task: asyncio.Task | None = None

    async def start(self) -> None:
        """启动后台回收线程"""
        self._reaper_task = asyncio.create_task(self._reap_loop())
        logger.info("AgentInstancePool reaper started")

    async def stop(self) -> None:
        """停止并清空实例池"""
        if self._reaper_task:
            self._reaper_task.cancel()
            try:
                await self._reaper_task
            except asyncio.CancelledError:
                pass
        with self._lock:
            self._pool.clear()
        logger.info("AgentInstancePool stopped")

    async def get_or_create(
        self, session_id: str, profile: AgentProfile,
    ) -> Agent:
        """获取已有实例或创建新实例（per-session 串行化防止重复创建）"""
        with self._lock:
            entry = self._pool.get(session_id)
            if entry and entry.profile_id == profile.id:
                entry.touch()
                return entry.agent

        # Serialize creation per session_id to avoid duplicate agents.
        # Locks are kept for reuse — cleaned up by the reaper alongside pool entries.
        if session_id not in self._create_locks:
            self._create_locks[session_id] = asyncio.Lock()
        create_lock = self._create_locks[session_id]

        async with create_lock:
            # Double-check after acquiring lock
            with self._lock:
                entry = self._pool.get(session_id)
                if entry and entry.profile_id == profile.id:
                    entry.touch()
                    return entry.agent

            agent = await self._factory.create(profile)
            new_entry = _PoolEntry(agent, profile.id, session_id)

            old: _PoolEntry | None = None
            with self._lock:
                old = self._pool.pop(session_id, None)
                if old:
                    logger.info(
                        f"Pool replacing agent for session {session_id}: "
                        f"{old.profile_id} -> {profile.id}"
                    )
                self._pool[session_id] = new_entry

            # Clean up old agent outside lock
            if old and hasattr(old.agent, "shutdown"):
                try:
                    await old.agent.shutdown()
                except Exception as e:
                    logger.warning(f"Failed to shutdown replaced agent: {e}")

        return agent

    def get_existing(self, session_id: str) -> Agent | None:
        """Return an existing Agent for *session_id* without creating a new one.

        Used by control endpoints (cancel / skip / insert) that must operate
        on the exact agent instance that is currently handling a conversation.
        """
        with self._lock:
            entry = self._pool.get(session_id)
            if entry:
                entry.touch()
                return entry.agent
        return None

    def release(self, session_id: str) -> None:
        """标记会话结束，实例进入空闲等待回收"""
        with self._lock:
            entry = self._pool.get(session_id)
            if entry:
                entry.touch()

    def get_stats(self) -> dict:
        with self._lock:
            entries = list(self._pool.values())
        return {
            "total": len(entries),
            "by_profile": {},
            "sessions": [
                {
                    "session_id": e.session_id,
                    "profile_id": e.profile_id,
                    "idle_seconds": round(e.idle_seconds, 1),
                }
                for e in entries
            ],
        }

    async def _reap_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(_REAP_INTERVAL_SECONDS)
                self._reap_idle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"AgentInstancePool reaper error: {e}")

    def _reap_idle(self) -> None:
        with self._lock:
            # Also clean up create_locks for sessions no longer in pool
            stale_locks = [sid for sid in self._create_locks if sid not in self._pool]
            for sid in stale_locks:
                lock = self._create_locks[sid]
                if not lock.locked():
                    self._create_locks.pop(sid, None)

            to_remove = [
                sid for sid, entry in self._pool.items()
                if entry.idle_seconds > self._idle_timeout
            ]
            for sid in to_remove:
                entry = self._pool.pop(sid)
                logger.info(
                    f"Pool reaped idle agent: session={sid}, "
                    f"profile={entry.profile_id}, "
                    f"idle={entry.idle_seconds:.0f}s"
                )
                # Schedule async cleanup if agent has shutdown method
                try:
                    loop = asyncio.get_running_loop()
                    if hasattr(entry.agent, 'shutdown'):
                        loop.call_soon_threadsafe(
                            lambda a=entry.agent: asyncio.ensure_future(a.shutdown())
                        )
                except Exception:
                    pass
