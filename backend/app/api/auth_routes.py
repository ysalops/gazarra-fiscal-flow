from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    get_current_user,
    verify_password,
)
from app.db.session import get_db
from app.models.entities import User
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo


router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


def _user_info(user: User) -> UserInfo:
    return UserInfo(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        active=user.active,
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower().strip()))
    if user is None or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
        )
    return LoginResponse(
        access_token=create_access_token(user),
        user=_user_info(user),
    )


@router.get("/me", response_model=UserInfo)
def me(user: User = Depends(get_current_user)):
    return _user_info(user)


@router.post("/logout")
def logout(user: User = Depends(get_current_user)):
    # Token assinado e stateless: o frontend simplesmente o descarta.
    return {"status": "ok", "user_id": user.id}
