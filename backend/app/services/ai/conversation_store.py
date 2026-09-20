from __future__ import annotations

from datetime import datetime
import json
import uuid
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import AIConversation, AIMessage, User


def _title_from_message(message: str) -> str:
    cleaned = " ".join((message or "").strip().split())
    if not cleaned:
        return "Nova conversa"
    return cleaned[:80] + ("…" if len(cleaned) > 80 else "")


def get_or_create_conversation(
    db: Session,
    user: User,
    conversation_id: Optional[str],
    first_message: str,
) -> AIConversation:
    if conversation_id:
        conversation = db.get(AIConversation, conversation_id)
        if conversation is None or conversation.user_id != user.id:
            raise HTTPException(status_code=404, detail="Conversa não encontrada.")
        return conversation

    conversation = AIConversation(
        id=str(uuid.uuid4()),
        user_id=user.id,
        title=_title_from_message(first_message),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def add_message(
    db: Session,
    conversation: AIConversation,
    *,
    role: str,
    content: str,
    agent: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> AIMessage:
    message = AIMessage(
        conversation_id=conversation.id,
        role=role,
        content=content,
        agent=agent,
        metadata_json=(
            json.dumps(metadata, ensure_ascii=False, default=str)
            if metadata
            else None
        ),
        created_at=datetime.utcnow(),
    )
    conversation.updated_at = datetime.utcnow()
    db.add(message)
    db.add(conversation)
    db.commit()
    db.refresh(message)
    return message


def list_conversations(db: Session, user: User, limit: int = 40) -> list[AIConversation]:
    return list(
        db.scalars(
            select(AIConversation)
            .where(AIConversation.user_id == user.id)
            .order_by(AIConversation.updated_at.desc())
            .limit(limit)
        ).all()
    )


def get_conversation_with_messages(
    db: Session,
    user: User,
    conversation_id: str,
) -> tuple[AIConversation, list[AIMessage]]:
    conversation = db.get(AIConversation, conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")

    messages = list(
        db.scalars(
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation_id)
            .order_by(AIMessage.created_at.asc(), AIMessage.id.asc())
        ).all()
    )
    return conversation, messages


def delete_conversation(db: Session, user: User, conversation_id: str) -> None:
    conversation, messages = get_conversation_with_messages(db, user, conversation_id)
    for message in messages:
        db.delete(message)
    db.delete(conversation)
    db.commit()


def conversation_history_for_prompt(
    db: Session,
    user: User,
    conversation_id: Optional[str],
    *,
    max_messages: int = 10,
) -> list[dict[str, str]]:
    if not conversation_id:
        return []

    conversation, messages = get_conversation_with_messages(db, user, conversation_id)
    del conversation
    selected = messages[-max_messages:]
    return [
        {"role": item.role, "content": item.content}
        for item in selected
        if item.role in {"user", "assistant"}
    ]
