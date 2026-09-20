from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AIChatRequest(BaseModel):
    company_id: Optional[int] = Field(default=None, ge=1)
    competence: Optional[str] = Field(default=None, min_length=7, max_length=7)
    message: str = Field(..., min_length=2, max_length=12000)
    # Compatibilidade com versões anteriores. V16.2 usa agent_mode + agents.
    agent: str = Field(default="auto", max_length=150)
    agent_mode: str = Field(default="auto", pattern="^(auto|none|manual|all)$")
    agents: List[str] = Field(default_factory=list, max_length=2)
    conversation_id: Optional[str] = Field(default=None, max_length=64)
    attachments: List[str] = Field(default_factory=list, max_length=8)


class AIAgentInfo(BaseModel):
    name: str
    title: str
    category: str
    version: str
    status: str
    permissions: List[str]
    summary: str = ""
    capabilities: List[str] = Field(default_factory=list)
    recommended_for: List[str] = Field(default_factory=list)
    human_review: bool = False
    summary_source: str = "spec"


class AIStatusResponse(BaseModel):
    status: str
    provider: str
    configured: bool
    model: Optional[str] = None
    agents_loaded: int
    data_source: str
    environment: str


class AIChatContext(BaseModel):
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    competence: Optional[str] = None
    source: str
    environment: str


class AIChatResponse(BaseModel):
    answer: str
    conversation_id: Optional[str] = None
    agent_used: str
    agent_title: str
    agents_used: List[str] = Field(default_factory=list)
    agent_titles: List[str] = Field(default_factory=list)
    agent_mode: str = "auto"
    provider: str
    model: Optional[str] = None
    demo_mode: bool
    requires_human_review: bool
    context: AIChatContext
    sources_used: List[str]
    generated_at: datetime
    warning: Optional[str] = None


class AIAttachmentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    size: int
    kind: str
    has_text: bool
    page_count: Optional[int] = None
    validation_count: int = 0
    visual_pages: List[int] = Field(default_factory=list)


class AIConversationSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class AIConversationMessage(BaseModel):
    id: int
    role: str
    content: str
    agent: Optional[str] = None
    created_at: datetime


class AIConversationDetail(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[AIConversationMessage]
