from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import (
    allowed_company_ids,
    ensure_company_access,
    get_current_user,
)
from app.db.session import get_db
from app.models.entities import User
from app.schemas.fiscal import FiscalCompany, FiscalDashboardResponse
from app.services.fiscal.mock_provider import MockFiscalProvider


router = APIRouter(prefix="/api/fiscal", tags=["Fiscal Dashboard"])
provider = MockFiscalProvider()


@router.get("/companies", response_model=List[FiscalCompany])
def list_fiscal_companies(
    search: str = Query(default="", max_length=120),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    permitted_ids = allowed_company_ids(db, user)
    normalized = search.strip().lower()
    digits = "".join(ch for ch in normalized if ch.isdigit())

    result = []
    for company in provider.list_companies():
        if permitted_ids is not None and company.id not in permitted_ids:
            continue

        cnpj = company.cnpj or ""
        cnpj_digits = "".join(ch for ch in cnpj if ch.isdigit())
        if normalized:
            matched = (
                normalized in company.name.lower()
                or normalized in cnpj.lower()
                or (digits and digits in cnpj_digits)
            )
            if not matched:
                continue

        result.append(company)

    return result[:50]


@router.get("/companies/{company_id}/competences", response_model=List[str])
def list_fiscal_competences(
    company_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_company_access(db, user, company_id)
    return provider.list_competences(company_id)


@router.get("/dashboard", response_model=FiscalDashboardResponse)
def get_fiscal_dashboard(
    company_id: int = Query(..., ge=1),
    competence: str = Query(..., examples=["2026-05"]),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_company_access(db, user, company_id)
    return provider.get_dashboard(company_id=company_id, competence=competence)
