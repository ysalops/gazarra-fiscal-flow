from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AIChatRequest(BaseModel):
    company_id: int = Field(..., ge=1)
    competence: str = Field(
        ...,
        min_length=7,
        max_length=7,
        examples=["2026-05"],
    )
    message: str = Field(..., min_length=2, max_length=4000)
    agent: str = Field(default="auto", max_length=150)
    conversation_id: Optional[str] = None


class AIAgentInfo(BaseModel):
    name: str
    title: str
    category: str
    version: str
    status: str
    permissions: List[str]


class AIStatusResponse(BaseModel):
    status: str
    provider: str
    configured: bool
    model: Optional[str] = None
    agents_loaded: int
    data_source: str
    environment: str


class AIChatContext(BaseModel):
    company_id: int
    company_name: str
    competence: str
    source: str
    environment: str


class AIChatResponse(BaseModel):
    answer: str
    agent_used: str
    agent_title: str
    provider: str
    model: Optional[str] = None
    demo_mode: bool
    requires_human_review: bool
    context: AIChatContext
    sources_used: List[str]
    generated_at: datetime
    warning: Optional[str] = None
