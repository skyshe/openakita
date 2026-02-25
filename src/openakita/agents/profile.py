"""
AgentProfile 数据模型 + ProfileStore

AgentProfile 是 Agent 的"蓝图"，定义名称、角色、技能列表、自定义提示词等。
ProfileStore 负责持久化和检索 Profile，支持 SYSTEM 预置保护。
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from openakita.utils.atomic_io import atomic_json_write

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    SYSTEM = "system"
    CUSTOM = "custom"
    DYNAMIC = "dynamic"


class SkillsMode(str, Enum):
    INCLUSIVE = "inclusive"  # 仅含 skills 列表中的技能
    EXCLUSIVE = "exclusive"  # 排除 skills 列表中的技能
    ALL = "all"  # 全部技能


# SYSTEM Profile 中不可被用户修改的核心字段
_SYSTEM_IMMUTABLE_FIELDS = frozenset({
    "id", "type", "created_by", "skills", "skills_mode",
})


@dataclass
class AgentProfile:
    id: str
    name: str
    description: str = ""
    type: AgentType = AgentType.CUSTOM

    # 技能配置
    skills: list[str] = field(default_factory=list)
    skills_mode: SkillsMode = SkillsMode.ALL

    # 自定义提示词（追加到系统提示词中）
    custom_prompt: str = ""

    # 显示
    icon: str = "🤖"
    color: str = "#4A90D9"

    # 能力边界
    fallback_profile_id: str | None = None

    # 元数据
    created_by: str = "system"
    created_at: str = ""

    # 国际化：{"zh": "小秋", "en": "Akita"}
    name_i18n: dict[str, str] = field(default_factory=dict)
    description_i18n: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = AgentType(self.type)
        if isinstance(self.skills_mode, str):
            self.skills_mode = SkillsMode(self.skills_mode)
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @property
    def is_system(self) -> bool:
        return self.type == AgentType.SYSTEM

    def get_display_name(self, lang: str = "zh") -> str:
        """按语言返回显示名称，找不到则回退到 name"""
        return self.name_i18n.get(lang, self.name)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["type"] = self.type.value
        d["skills_mode"] = self.skills_mode.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentProfile:
        data = dict(data)
        if "type" in data:
            data["type"] = AgentType(data["type"])
        if "skills_mode" in data:
            data["skills_mode"] = SkillsMode(data["skills_mode"])
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


class ProfileStore:
    """
    AgentProfile 持久化存储。

    存储路径: {base_dir}/profiles/{profile_id}.json
    线程安全：使用 RLock 保护内存缓存。
    SYSTEM Profile 保护：禁止删除，PUT 只允许修改自定义字段。

    注意：get() 和 list_all() 从内存缓存读取（初始化时从磁盘加载）。
    多个 ProfileStore 实例可能看到不同的缓存状态，但每个实例在初始化时都会从磁盘加载，
    因此可以正常工作。如需实时读取磁盘，可在调用前重新创建 ProfileStore 实例。
    """

    def __init__(self, base_dir: str | Path):
        self._base_dir = Path(base_dir)
        self._profiles_dir = self._base_dir / "profiles"
        self._profiles_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, AgentProfile] = {}
        self._lock = threading.RLock()
        self._load_all()

    def _load_all(self) -> None:
        """从磁盘加载所有 Profile 到缓存"""
        loaded = 0
        for fp in self._profiles_dir.glob("*.json"):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                profile = AgentProfile.from_dict(data)
                self._cache[profile.id] = profile
                loaded += 1
            except Exception as e:
                logger.warning(f"Failed to load profile {fp.name}: {e}")
        if loaded:
            logger.info(f"ProfileStore loaded {loaded} profile(s) from {self._profiles_dir}")

    def get(self, profile_id: str) -> AgentProfile | None:
        with self._lock:
            return self._cache.get(profile_id)

    def list_all(self) -> list[AgentProfile]:
        with self._lock:
            return list(self._cache.values())

    def save(self, profile: AgentProfile) -> None:
        """保存 Profile（新建或更新）"""
        with self._lock:
            existing = self._cache.get(profile.id)
            if existing and existing.is_system:
                self._validate_system_update(existing, profile)
            self._cache[profile.id] = profile
            self._persist(profile)
        logger.info(f"ProfileStore saved: {profile.id} ({profile.type.value})")

    def update(self, profile_id: str, updates: dict[str, Any]) -> AgentProfile:
        """
        部分更新 Profile 字段。

        对 SYSTEM Profile，过滤掉不可修改的核心字段。
        """
        with self._lock:
            existing = self._cache.get(profile_id)
            if existing is None:
                raise KeyError(f"Profile not found: {profile_id}")

            if existing.is_system:
                blocked = set(updates.keys()) & _SYSTEM_IMMUTABLE_FIELDS
                if blocked:
                    logger.warning(
                        f"SYSTEM profile {profile_id}: "
                        f"ignoring immutable fields: {blocked}"
                    )
                    updates = {
                        k: v for k, v in updates.items()
                        if k not in _SYSTEM_IMMUTABLE_FIELDS
                    }

            data = existing.to_dict()
            data.update(updates)
            profile = AgentProfile.from_dict(data)
            self._cache[profile_id] = profile
            self._persist(profile)

        logger.info(f"ProfileStore updated: {profile_id}")
        return profile

    def delete(self, profile_id: str) -> bool:
        """删除 Profile。SYSTEM 类型禁止删除。"""
        with self._lock:
            existing = self._cache.get(profile_id)
            if existing is None:
                return False
            if existing.is_system:
                raise PermissionError(
                    f"Cannot delete SYSTEM profile: {profile_id}"
                )
            del self._cache[profile_id]
            fp = self._profiles_dir / f"{profile_id}.json"
            if fp.exists():
                fp.unlink()
        logger.info(f"ProfileStore deleted: {profile_id}")
        return True

    def exists(self, profile_id: str) -> bool:
        with self._lock:
            return profile_id in self._cache

    def count(self) -> int:
        with self._lock:
            return len(self._cache)

    def _persist(self, profile: AgentProfile) -> None:
        fp = self._profiles_dir / f"{profile.id}.json"
        atomic_json_write(fp, profile.to_dict())

    @staticmethod
    def _validate_system_update(
        existing: AgentProfile, new: AgentProfile,
    ) -> None:
        """检查对 SYSTEM Profile 的修改是否合法"""
        for f in _SYSTEM_IMMUTABLE_FIELDS:
            old_val = getattr(existing, f)
            new_val = getattr(new, f)
            if old_val != new_val:
                raise PermissionError(
                    f"Cannot modify immutable field '{f}' on SYSTEM profile "
                    f"'{existing.id}': {old_val!r} -> {new_val!r}"
                )
