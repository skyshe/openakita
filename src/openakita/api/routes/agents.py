"""Agent profile API routes."""

import logging
from fastapi import APIRouter, HTTPException, Request

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()

# Valid IM bot types
VALID_BOT_TYPES = frozenset({"feishu", "telegram", "dingtalk", "wework", "onebot", "qqbot"})


# ─── Pydantic models ─────────────────────────────────────────────────────


class BotCreateRequest(BaseModel):
    id: str = Field(..., min_length=1)
    type: str = Field(...)
    name: str = Field("")
    agent_profile_id: str = Field("default")
    enabled: bool = Field(True)
    credentials: dict = Field(default_factory=dict)


class BotUpdateRequest(BaseModel):
    name: str | None = None
    agent_profile_id: str | None = None
    enabled: bool | None = None
    credentials: dict | None = None


class BotToggleRequest(BaseModel):
    enabled: bool


class ProfileCreateRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    icon: str = Field("🤖", max_length=4)
    color: str = Field("#6b7280", max_length=20)
    skills: list[str] = Field(default_factory=list)
    skills_mode: str = Field("all")
    custom_prompt: str = Field("", max_length=2000)


class ProfileUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    icon: str | None = Field(None, max_length=4)
    color: str | None = Field(None, max_length=20)
    skills: list[str] | None = None
    skills_mode: str | None = None
    custom_prompt: str | None = Field(None, max_length=2000)


# ─── Bot CRUD routes ─────────────────────────────────────────────────────


@router.get("/api/agents/bots")
async def list_bots():
    """List all configured bots from settings.im_bots."""
    from openakita.config import settings

    return {"bots": list(settings.im_bots)}


@router.post("/api/agents/bots")
async def create_bot(body: BotCreateRequest):
    """Add a new bot. Validates id uniqueness and type."""
    from openakita.config import runtime_state, settings

    if body.id.strip() == "":
        raise HTTPException(status_code=400, detail="id must be non-empty")
    if body.type not in VALID_BOT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"type must be one of: {', '.join(sorted(VALID_BOT_TYPES))}",
        )
    if not isinstance(body.credentials, dict):
        raise HTTPException(status_code=400, detail="credentials must be a dict")

    existing_ids = {b.get("id") for b in settings.im_bots if isinstance(b, dict)}
    if body.id in existing_ids:
        raise HTTPException(status_code=400, detail=f"bot id '{body.id}' already exists")

    bot = {
        "id": body.id,
        "type": body.type,
        "name": body.name,
        "agent_profile_id": body.agent_profile_id,
        "enabled": body.enabled,
        "credentials": body.credentials,
    }
    settings.im_bots = list(settings.im_bots) + [bot]
    runtime_state.save()
    logger.info(f"[Agents API] Created bot: {body.id}")
    return {"status": "ok", "bot": bot}


@router.put("/api/agents/bots/{bot_id}")
async def update_bot(bot_id: str, body: BotUpdateRequest):
    """Update an existing bot. Partial update (only provided fields are changed)."""
    from openakita.config import runtime_state, settings

    bots = list(settings.im_bots)
    idx = next((i for i, b in enumerate(bots) if isinstance(b, dict) and b.get("id") == bot_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"bot '{bot_id}' not found")

    bot = dict(bots[idx])
    if body.name is not None:
        bot["name"] = body.name
    if body.agent_profile_id is not None:
        bot["agent_profile_id"] = body.agent_profile_id
    if body.enabled is not None:
        bot["enabled"] = body.enabled
    if body.credentials is not None:
        bot["credentials"] = body.credentials

    bots[idx] = bot
    settings.im_bots = bots
    runtime_state.save()
    logger.info(f"[Agents API] Updated bot: {bot_id}")
    return {"status": "ok", "bot": bot}


@router.delete("/api/agents/bots/{bot_id}")
async def delete_bot(bot_id: str):
    """Remove a bot."""
    from openakita.config import runtime_state, settings

    bots = list(settings.im_bots)
    new_bots = [b for b in bots if isinstance(b, dict) and b.get("id") != bot_id]
    if len(new_bots) == len(bots):
        raise HTTPException(status_code=404, detail=f"bot '{bot_id}' not found")

    settings.im_bots = new_bots
    runtime_state.save()
    logger.info(f"[Agents API] Deleted bot: {bot_id}")
    return {"status": "ok"}


@router.post("/api/agents/bots/{bot_id}/toggle")
async def toggle_bot(bot_id: str, body: BotToggleRequest):
    """Enable or disable a bot."""
    from openakita.config import runtime_state, settings

    bots = list(settings.im_bots)
    idx = next((i for i, b in enumerate(bots) if isinstance(b, dict) and b.get("id") == bot_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"bot '{bot_id}' not found")

    bot = dict(bots[idx])
    bot["enabled"] = body.enabled
    bots[idx] = bot
    settings.im_bots = bots
    runtime_state.save()
    logger.info(f"[Agents API] Toggled bot {bot_id}: enabled={body.enabled}")
    return {"status": "ok", "bot": bot}


# ─── Agent profile routes ───────────────────────────────────────────────


@router.get("/api/agents/profiles")
async def list_agent_profiles():
    """Return available agent profiles (system presets + user-created)."""
    from openakita.agents.presets import SYSTEM_PRESETS
    from openakita.agents.profile import ProfileStore
    from openakita.config import settings

    if not settings.multi_agent_enabled:
        return {"profiles": [], "multi_agent_enabled": False}

    seen_ids: set[str] = set()
    profiles = []
    for p in SYSTEM_PRESETS:
        seen_ids.add(p.id)
        profiles.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "icon": p.icon,
            "color": p.color,
            "type": p.type.value if hasattr(p.type, "value") else str(p.type),
            "skills": getattr(p, "skills", []),
            "skills_mode": p.skills_mode.value if hasattr(p, "skills_mode") else "all",
            "custom_prompt": getattr(p, "custom_prompt", ""),
            "name_i18n": p.name_i18n,
            "description_i18n": p.description_i18n,
        })

    store = ProfileStore(settings.data_dir / "agents")
    for p in store.list_all():
        if p.id not in seen_ids:
            profiles.append(p.to_dict())

    return {"profiles": profiles, "multi_agent_enabled": True}


@router.post("/api/agents/profiles")
async def create_agent_profile(body: ProfileCreateRequest):
    """Create a new custom agent profile."""
    from openakita.agents.profile import AgentProfile, AgentType, ProfileStore, SkillsMode
    from openakita.config import settings

    if not settings.multi_agent_enabled:
        raise HTTPException(status_code=400, detail="Multi-agent mode is not enabled")

    valid_modes = {"all", "inclusive", "exclusive"}
    if body.skills_mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"skills_mode must be one of: {', '.join(valid_modes)}")

    store = ProfileStore(settings.data_dir / "agents")

    if store.exists(body.id):
        raise HTTPException(status_code=400, detail=f"Profile '{body.id}' already exists")

    profile = AgentProfile(
        id=body.id,
        name=body.name,
        description=body.description,
        type=AgentType.CUSTOM,
        skills=body.skills,
        skills_mode=SkillsMode(body.skills_mode),
        custom_prompt=body.custom_prompt,
        icon=body.icon,
        color=body.color,
        created_by="user",
    )

    store.save(profile)
    logger.info(f"[Agents API] Created profile: {body.id}")
    return {"status": "ok", "profile": profile.to_dict()}


@router.put("/api/agents/profiles/{profile_id}")
async def update_agent_profile(profile_id: str, body: ProfileUpdateRequest):
    """Update a custom agent profile (system profiles have restricted updates)."""
    from openakita.agents.profile import ProfileStore
    from openakita.config import settings

    if not settings.multi_agent_enabled:
        raise HTTPException(status_code=400, detail="Multi-agent mode is not enabled")

    if body.skills_mode is not None:
        valid_modes = {"all", "inclusive", "exclusive"}
        if body.skills_mode not in valid_modes:
            raise HTTPException(status_code=400, detail=f"skills_mode must be one of: {', '.join(valid_modes)}")

    store = ProfileStore(settings.data_dir / "agents")
    update_data = body.model_dump(exclude_none=True)

    try:
        updated = store.update(profile_id, update_data)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    logger.info(f"[Agents API] Updated profile: {profile_id}")
    return {"status": "ok", "profile": updated.to_dict()}


@router.delete("/api/agents/profiles/{profile_id}")
async def delete_agent_profile(profile_id: str):
    """Delete a custom agent profile."""
    from openakita.agents.profile import ProfileStore
    from openakita.config import settings

    if not settings.multi_agent_enabled:
        raise HTTPException(status_code=400, detail="Multi-agent mode is not enabled")

    store = ProfileStore(settings.data_dir / "agents")

    try:
        deleted = store.delete(profile_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")

    logger.info(f"[Agents API] Deleted profile: {profile_id}")
    return {"status": "ok"}


@router.get("/api/agents/health")
async def get_agent_health():
    """Get health metrics from the orchestrator."""
    try:
        from openakita.main import _orchestrator
        if _orchestrator:
            return {"health": _orchestrator.get_health_stats()}
    except Exception:
        pass
    return {"health": {}}


@router.get("/api/agents/collaboration/{session_id}")
async def get_collaboration_info(session_id: str, request: Request):
    """Get collaboration info for a session (active_agents, delegation_chain)."""
    session_manager = getattr(request.app.state, "session_manager", None)
    if not session_manager:
        raise HTTPException(status_code=503, detail="Session manager not available")

    session = session_manager.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    ctx = session.context
    active_agents = getattr(ctx, "active_agents", [])
    delegation_chain = getattr(ctx, "delegation_chain", [])

    return {
        "session_id": session_id,
        "active_agents": active_agents,
        "delegation_chain": delegation_chain,
    }
