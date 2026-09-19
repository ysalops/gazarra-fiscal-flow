from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.registry import list_agents
from app.core.config import settings
from app.core.security import ensure_company_access, get_current_user
from app.db.session import get_db
from app.models.entities import User
from app.schemas.ai import AIAgentInfo, AIChatRequest, AIChatResponse, AIStatusResponse
from app.services.ai.service import chat


router = APIRouter(prefix="/api/ai", tags=["GAZARRA IA"])


@router.get("/status", response_model=AIStatusResponse)
def ai_status(user: User = Depends(get_current_user)):
    provider = settings.llm_provider.lower().strip()
    if provider == "openai":
        configured = bool(settings.openai_api_key)
        model = settings.openai_model or None
    elif provider == "bedrock":
        configured = bool(settings.bedrock_model_id)
        model = settings.bedrock_model_id or None
    else:
        provider = "demo"
        configured = False
        model = None

    return AIStatusResponse(
        status="ok",
        provider=provider,
        configured=configured,
        model=model,
        agents_loaded=len(list_agents()),
        data_source="mock",
        environment="demo",
    )


@router.get("/agents", response_model=List[AIAgentInfo])
def ai_agents(user: User = Depends(get_current_user)):
    return [
        AIAgentInfo(
            name=agent.name,
            title=agent.title,
            category=agent.category,
            version=agent.version,
            status=agent.status,
            permissions=agent.permissions,
        )
        for agent in list_agents()
    ]


@router.post("/chat", response_model=AIChatResponse)
def ai_chat(
    payload: AIChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_company_access(db, user, payload.company_id)
    return chat(payload)
