"""Router for Agent Persona configuration."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.agents.personas import persona_manager

router = APIRouter(prefix="/api/personas", tags=["personas"])


class PersonaUpdateRequest(BaseModel):
    """Request model for updating an agent's persona."""

    agent: str
    persona: str


class PersonaResetRequest(BaseModel):
    """Request model for resetting agent personas."""

    agent: Optional[str] = None


@router.get("")
async def get_personas() -> Dict[str, Any]:
    """Retrieve active personas and default personas."""
    return {
        "personas": persona_manager.get_all_personas(),
        "defaults": persona_manager.get_defaults(),
    }


@router.post("")
async def update_persona(request: PersonaUpdateRequest) -> Dict[str, Any]:
    """Update custom persona prompt for a specific agent."""
    valid_agents = list(persona_manager.get_defaults().keys())
    if not request.agent or request.agent.lower() not in valid_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown agent '{request.agent}'. Valid agents: {valid_agents}",
        )

    persona_text = request.persona.strip() if request.persona else ""
    if len(persona_text) < 10 or len(request.persona) > 10000:
        raise HTTPException(
            status_code=400,
            detail="Persona prompt must be between 10 and 10,000 characters.",
        )

    success = persona_manager.set_persona(request.agent, request.persona)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown agent '{request.agent}'. Valid agents: {valid_agents}",
        )
    return {
        "status": "ok",
        "message": f"Persona updated for agent '{request.agent}'",
        "personas": persona_manager.get_all_personas(),
    }


@router.post("/reset")
async def reset_personas(request: Optional[PersonaResetRequest] = None) -> Dict[str, Any]:
    """Reset specified agent persona or all personas to system defaults."""
    agent_target = request.agent if request else None
    valid_agents = list(persona_manager.get_defaults().keys())
    if agent_target and agent_target.strip():
        if agent_target.lower() not in valid_agents:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown agent '{agent_target}'. Valid agents: {valid_agents}",
            )
        persona_manager.reset_persona(agent_target)
    else:
        persona_manager.reset_persona(None)

    return {
        "status": "ok",
        "message": f"Persona(s) reset to default for: {agent_target or 'all'}",
        "personas": persona_manager.get_all_personas(),
    }
