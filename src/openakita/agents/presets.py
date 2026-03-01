"""
系统预置 AgentProfile 定义 + 首次启动自动部署
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .profile import AgentProfile, AgentType, ProfileStore, SkillsMode

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

SYSTEM_PRESETS: list[AgentProfile] = [
    AgentProfile(
        id="default",
        name="小秋",
        description="通用全能助手，拥有所有技能",
        type=AgentType.SYSTEM,
        skills=[],
        skills_mode=SkillsMode.ALL,
        custom_prompt="",
        icon="🐕",
        color="#4A90D9",
        fallback_profile_id=None,
        created_by="system",
        name_i18n={"zh": "小秋", "en": "Akita"},
        description_i18n={
            "zh": "通用全能助手，拥有所有技能",
            "en": "General-purpose assistant with all skills",
        },
    ),
    AgentProfile(
        id="office-doc",
        name="文助",
        description="办公文档处理专家，擅长 Word/PPT/Excel",
        type=AgentType.SYSTEM,
        skills=["docx", "pptx", "xlsx", "pdf"],
        skills_mode=SkillsMode.INCLUSIVE,
        custom_prompt=(
            "你是办公文档处理专家。优先使用文档相关工具处理用户需求。"
            "如果用户需求超出文档处理范围，建议用户切换到通用助手。"
        ),
        icon="📄",
        color="#27AE60",
        fallback_profile_id="default",
        created_by="system",
        name_i18n={"zh": "文助", "en": "DocHelper"},
        description_i18n={
            "zh": "办公文档处理专家，擅长 Word/PPT/Excel",
            "en": "Office document specialist for Word/PPT/Excel",
        },
    ),
    AgentProfile(
        id="code-assistant",
        name="码哥",
        description="代码开发助手，擅长编码、调试和 Git 操作",
        type=AgentType.SYSTEM,
        skills=["run-shell", "read-file", "write-file", "list-directory", "web-search"],
        skills_mode=SkillsMode.INCLUSIVE,
        custom_prompt=(
            "你是编程开发助手。优先帮助用户编写代码、调试问题、管理 Git 仓库。"
            "对于非编程任务，建议用户切换到合适的专用助手。"
        ),
        icon="💻",
        color="#8E44AD",
        fallback_profile_id="default",
        created_by="system",
        name_i18n={"zh": "码哥", "en": "CodeBro"},
        description_i18n={
            "zh": "代码开发助手，擅长编码、调试和 Git 操作",
            "en": "Coding assistant for development, debugging and Git",
        },
    ),
    AgentProfile(
        id="browser-agent",
        name="网探",
        description="网络浏览与信息采集专家",
        type=AgentType.SYSTEM,
        skills=[
            "web-search", "news-search",
            "browser-click", "browser-get-content", "browser-list-tabs",
            "browser-navigate", "browser-new-tab", "browser-open",
            "browser-screenshot", "browser-status", "browser-switch-tab",
            "browser-task", "browser-type",
            "desktop-screenshot",
        ],
        skills_mode=SkillsMode.INCLUSIVE,
        custom_prompt=(
            "你是网络浏览与信息采集专家。擅长搜索信息、浏览网页、截图取证。"
            "对于不需要网络操作的任务，建议切换到通用助手。"
        ),
        icon="🌐",
        color="#E67E22",
        fallback_profile_id="default",
        created_by="system",
        name_i18n={"zh": "网探", "en": "WebScout"},
        description_i18n={
            "zh": "网络浏览与信息采集专家",
            "en": "Web browsing and information gathering specialist",
        },
    ),
    AgentProfile(
        id="data-analyst",
        name="数析",
        description="数据分析师，擅长数据处理、可视化和统计",
        type=AgentType.SYSTEM,
        skills=["xlsx", "run-shell", "read-file", "write-file", "list-directory"],
        skills_mode=SkillsMode.INCLUSIVE,
        custom_prompt=(
            "你是数据分析专家。擅长数据清洗、统计分析、图表可视化。"
            "优先使用 Python/pandas 等工具处理数据。"
        ),
        icon="📊",
        color="#2980B9",
        fallback_profile_id="default",
        created_by="system",
        name_i18n={"zh": "数析", "en": "DataPro"},
        description_i18n={
            "zh": "数据分析师，擅长数据处理、可视化和统计",
            "en": "Data analyst for processing, visualization and statistics",
        },
    ),
]


def deploy_system_presets(store: ProfileStore) -> int:
    """
    部署系统预置 Profile（首次启动或升级时调用）。

    - 不存在的预置 Profile 直接创建
    - 已存在的 SYSTEM Profile 若 skills 列表与预置不同则同步更新
      （保留用户自定义的 custom_prompt/name/icon 等字段）

    Returns:
        新增或升级的 Profile 数量
    """
    deployed = 0
    for preset in SYSTEM_PRESETS:
        if not store.exists(preset.id):
            store.save(preset)
            deployed += 1
            logger.info(f"Deployed system preset: {preset.id} ({preset.name})")
        else:
            existing = store.get(preset.id)
            if (
                existing
                and existing.is_system
                and sorted(existing.skills) != sorted(preset.skills)
            ):
                data = existing.to_dict()
                data["skills"] = preset.skills
                data["skills_mode"] = preset.skills_mode.value
                updated = AgentProfile.from_dict(data)
                store._cache[preset.id] = updated
                store._persist(updated)
                deployed += 1
                logger.info(
                    f"Upgraded system preset skills: {preset.id} "
                    f"({existing.skills} -> {preset.skills})"
                )
    if deployed:
        logger.info(f"Deployed/upgraded {deployed} system preset profile(s)")
    return deployed


def cleanup_stale_dynamic_agents(agents_dir: str | Path, max_age_days: int = 7) -> int:
    """
    清理过期的 DYNAMIC 类型 Agent Profile 文件。

    启动时调用，删除 created_at 超过 max_age_days 的 dynamic_* profile 文件。
    不清理 SYSTEM 和 CUSTOM 类型。

    Returns:
        清理的 Profile 数量
    """
    import json
    from datetime import datetime, timezone
    from pathlib import Path as _Path

    profiles_dir = _Path(agents_dir) / "profiles"
    if not profiles_dir.exists():
        return 0

    cutoff = datetime.now(timezone.utc).timestamp() - (max_age_days * 86400)
    cleaned = 0

    for fp in profiles_dir.glob("*.json"):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            if data.get("type") != "dynamic":
                continue

            created_at = data.get("created_at", "")
            if not created_at:
                continue

            created_ts = datetime.fromisoformat(created_at).timestamp()
            if created_ts < cutoff:
                fp.unlink()
                cleaned += 1
                logger.info(
                    f"Cleaned up stale dynamic agent: {fp.stem} "
                    f"(created_at={created_at})"
                )
        except Exception as e:
            logger.warning(f"Failed to check/clean dynamic agent {fp.name}: {e}")

    if cleaned:
        logger.info(f"Cleaned up {cleaned} stale dynamic agent profile(s)")
    return cleaned


def ensure_presets_on_mode_enable(agents_dir: str | Path) -> None:
    """
    多Agent模式首次开启时调用，确保预置 Profile 已部署。
    同时清理过期的 DYNAMIC Agent。

    Args:
        agents_dir: data/agents/ 目录路径
    """
    from pathlib import Path

    agents_dir = Path(agents_dir)
    store = ProfileStore(agents_dir)
    deployed = deploy_system_presets(store)
    if deployed:
        logger.info(
            f"Multi-agent mode enabled: deployed {deployed} preset(s) to {agents_dir}"
        )

    cleaned = cleanup_stale_dynamic_agents(agents_dir)
    if cleaned:
        logger.info(
            f"Multi-agent mode startup: cleaned {cleaned} stale dynamic profile(s)"
        )
