from typing import Literal

from pydantic import BaseModel, Field


class CandidateProduct(BaseModel):
    internal_code: str
    description: str
    gtin: str | None = None
    ncm: str | None = None
    unit: str | None = None


class SupplierProduct(BaseModel):
    supplier_code: str
    description: str
    gtin: str | None = None
    ncm: str | None = None
    unit: str | None = None


class MatchRequest(BaseModel):
    supplier_product: SupplierProduct
    candidates: list[CandidateProduct]


class MatchSuggestion(BaseModel):
    internal_code: str | None = None
    confidence: float = Field(ge=0, le=1)
    status: str
    reasons: list[str]


class BatchMatchRequest(BaseModel):
    supplier_cnpj: str | None = None
    items: list[SupplierProduct]


class MappingReview(BaseModel):
    action: Literal["approve", "adjust", "block"]
    target_product_id: int | None = None
    reviewed_by: str = "POC"
    rationale: str | None = None