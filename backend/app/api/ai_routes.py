from typing import List

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.agents.registry import get_agent, list_agents
from app.core.config import settings
from app.core.security import ensure_company_access, get_current_user
from app.db.session import SessionLocal, get_db
from app.models.entities import User
from app.schemas.ai import (
    AIAgentInfo,
    AIAttachmentResponse,
    AIChatRequest,
    AIChatResponse,
    AIConversationDetail,
    AIConversationMessage,
    AIConversationSummary,
    AIStatusResponse,
)
from app.services.ai.attachments import save_attachment
from app.services.ai.agent_catalog import get_catalog_item, refresh_catalog_item
from app.services.ai.conversation_store import (
    delete_conversation,
    get_conversation_with_messages,
    list_conversations,
)
from app.services.ai.service import chat, stream_chat_events


router = APIRouter(prefix="/api/ai", tags=["GAZARRA IA"])


@router.get("/status", response_model=AIStatusResponse)
def ai_status(user: User = Depends(get_current_user)):
    provider = settings.llm_provider.lower().strip()
    if provider == "ollama":
        configured = bool(settings.ollama_base_url and settings.ollama_model)
        model = settings.ollama_model or None
    elif provider == "openai":
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
    return [AIAgentInfo(**get_catalog_item(agent)) for agent in list_agents()]


@router.post("/agents/{agent_name}/summary", response_model=AIAgentInfo)
def ai_agent_summary(
    agent_name: str,
    user: User = Depends(get_current_user),
):
    # O resumo é gerado uma vez e cacheado. Quando LLM_PROVIDER=bedrock,
    # o próprio Claude lê a especificação do agente e produz o catálogo.
    try:
        item = refresh_catalog_item(agent_name)
    except KeyError:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Agente não encontrado.")
    return AIAgentInfo(**item)


@router.post("/attachments", response_model=AIAttachmentResponse)
async def ai_upload_attachment(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    metadata = await save_attachment(file, user.id)
    return AIAttachmentResponse(**metadata)


@router.get("/conversations", response_model=List[AIConversationSummary])
def ai_conversations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return [
        AIConversationSummary(
            id=item.id,
            title=item.title,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in list_conversations(db, user)
    ]


@router.get("/conversations/{conversation_id}", response_model=AIConversationDetail)
def ai_conversation_detail(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation, messages = get_conversation_with_messages(db, user, conversation_id)
    return AIConversationDetail(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            AIConversationMessage(
                id=item.id,
                role=item.role,
                content=item.content,
                agent=item.agent,
                created_at=item.created_at,
            )
            for item in messages
        ],
    )


@router.delete("/conversations/{conversation_id}")
def ai_delete_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    delete_conversation(db, user, conversation_id)
    return {"status": "ok"}


def _validate_optional_company(payload: AIChatRequest, user: User, db: Session) -> None:
    if payload.company_id is not None:
        ensure_company_access(db, user, payload.company_id)


@router.post("/chat", response_model=AIChatResponse)
def ai_chat(
    payload: AIChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_optional_company(payload, user, db)
    return chat(payload, user=user, db=db)


def _stream_with_own_session(payload: AIChatRequest, user_id: int):
    # FastAPI 0.115 pode encerrar dependências yield antes do fim do StreamingResponse.
    # A stream usa uma sessão própria para manter histórico/tools estáveis até o último chunk.
    stream_db = SessionLocal()
    try:
        stream_user = stream_db.get(User, user_id)
        if stream_user is None or not stream_user.active:
            yield '{"type":"error","message":"Usuário inválido ou inativo."}\n'
            return
        yield from stream_chat_events(payload, user=stream_user, db=stream_db)
    finally:
        stream_db.close()


@router.post("/chat/stream")
def ai_chat_stream(
    payload: AIChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_optional_company(payload, user, db)
    return StreamingResponse(
        _stream_with_own_session(payload, user.id),
        media_type="application/x-ndjson; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
