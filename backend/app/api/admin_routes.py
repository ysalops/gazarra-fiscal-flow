import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, require_admin
from app.db.session import get_db
from app.models.entities import AuditLog, User, UserCompanyAccess
from app.schemas.auth import (
    CompanyAccessItem,
    CompanyAssignmentRequest,
    CreateUserRequest,
    UserInfo,
)
from app.services.fiscal.mock_provider import MockFiscalProvider


router = APIRouter(prefix="/api/admin", tags=["Administração"])
provider = MockFiscalProvider()


def _user_info(user: User) -> UserInfo:
    return UserInfo(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        active=user.active,
    )


@router.get("/users", response_model=List[UserInfo])
def list_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.scalars(select(User).order_by(User.name.asc())).all()
    return [_user_info(user) for user in users]


@router.post("/users", response_model=UserInfo)
def create_user(
    payload: CreateUserRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    email = payload.email.lower().strip()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="Já existe usuário com este e-mail.")

    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    db.add(
        AuditLog(
            user_id=admin.id,
            action="user_created",
            entity="user",
            entity_id=str(user.id),
            details=json.dumps({"email": user.email, "role": user.role}, ensure_ascii=False),
        )
    )
    db.commit()
    return _user_info(user)


@router.get("/users/{user_id}/companies", response_model=List[CompanyAccessItem])
def user_companies(
    user_id: int,
    search: str = Query(default="", max_length=120),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    assigned_ids = set(
        db.scalars(
            select(UserCompanyAccess.company_id).where(
                UserCompanyAccess.user_id == user_id
            )
        ).all()
    )

    normalized = search.strip().lower()
    digits = "".join(ch for ch in normalized if ch.isdigit())
    companies = []
    for company in provider.list_companies():
        cnpj_digits = "".join(ch for ch in (company.cnpj or "") if ch.isdigit())
        matches = (
            not normalized
            or normalized in company.name.lower()
            or (digits and digits in cnpj_digits)
            or normalized in (company.cnpj or "").lower()
        )
        if matches:
            companies.append(
                CompanyAccessItem(
                    id=company.id,
                    name=company.name,
                    cnpj=company.cnpj,
                    assigned=company.id in assigned_ids,
                )
            )
    return companies[:50]


@router.put("/users/{user_id}/companies")
def set_user_companies(
    user_id: int,
    payload: CompanyAssignmentRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if user.role == "admin":
        raise HTTPException(
            status_code=400,
            detail="Administradores já possuem acesso a todas as empresas.",
        )

    valid_ids = {company.id for company in provider.list_companies()}
    requested_ids = set(payload.company_ids)
    invalid = requested_ids - valid_ids
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Empresas inválidas: {sorted(invalid)}",
        )

    db.execute(delete(UserCompanyAccess).where(UserCompanyAccess.user_id == user_id))
    for company_id in sorted(requested_ids):
        db.add(
            UserCompanyAccess(
                user_id=user_id,
                company_id=company_id,
                assigned_by=admin.id,
            )
        )

    db.add(
        AuditLog(
            user_id=admin.id,
            action="company_access_updated",
            entity="user",
            entity_id=str(user_id),
            details=json.dumps({"company_ids": sorted(requested_ids)}, ensure_ascii=False),
        )
    )
    db.commit()
    return {
        "status": "ok",
        "user_id": user_id,
        "company_ids": sorted(requested_ids),
    }


@router.get("/audit")
def audit_log(
    limit: int = Query(default=30, ge=1, le=200),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    ).all()
    return [
        {
            "id": row.id,
            "user_id": row.user_id,
            "action": row.action,
            "entity": row.entity,
            "entity_id": row.entity_id,
            "details": row.details,
            "created_at": row.created_at,
        }
        for row in rows
    ]
