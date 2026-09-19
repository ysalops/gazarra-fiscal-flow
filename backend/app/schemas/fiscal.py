from typing import List, Optional
from pydantic import BaseModel


class FiscalMetadata(BaseModel):
    source: str
    environment: str
    generated_at: str


class FiscalCompany(BaseModel):
    id: int
    name: str
    cnpj: str
    tax_regime: str
    city: str
    state: str


class RevenueSummary(BaseModel):
    without_st: float
    with_st: float


class TaxSummary(BaseModel):
    das: float
    effective_rate: float
    st: float
    difal: float


class SimplesSummary(BaseModel):
    accumulated: float
    limit: float
    used_percentage: float
    remaining_percentage: float

    icms_iss_sublimit: float
    icms_iss_used_percentage: float
    icms_iss_remaining_percentage: float


class MonthlyHistoryItem(BaseModel):
    competence: str

    revenue_without_st: float
    revenue_with_st: float

    das: float
    effective_rate: float

    st: float
    difal: float


class STStateItem(BaseModel):
    state: str
    cfop: str
    product: str
    invoice_value: float
    st_value: float


class DifalItem(BaseModel):
    supplier: str
    invoice_number: str
    document_value: float
    calculation_base: float
    icms_advance: float


class CertificateItem(BaseModel):
    type: str
    status: str
    issued_at: Optional[str] = None
    expires_at: Optional[str] = None


class ObligationItem(BaseModel):
    name: str
    competence: str
    delivered_at: Optional[str] = None
    due_at: str
    status: str


class ComparisonItem(BaseModel):
    name: str
    current_value: float
    previous_value: float
    variation_percentage: float


class FiscalDashboardResponse(BaseModel):
    metadata: FiscalMetadata
    company: FiscalCompany
    competence: str
    revenue: RevenueSummary
    taxes: TaxSummary
    simples: SimplesSummary
    monthly_comparison: List[ComparisonItem]
    yearly_comparison: List[ComparisonItem]
    history: List[MonthlyHistoryItem]
    st_by_state: List[STStateItem]
    difal_details: List[DifalItem]
    certificates: List[CertificateItem]
    obligations: List[ObligationItem]
