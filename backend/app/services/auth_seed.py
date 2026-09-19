from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.entities import User, UserCompanyAccess


def seed_demo_users(db: Session) -> None:
    if not settings.seed_demo_users:
        return

    admin = db.scalar(select(User).where(User.email == settings.demo_admin_email))
    if admin is None:
        admin = User(
            name="Administrador GAZARRA",
            email=settings.demo_admin_email,
            password_hash=hash_password(settings.demo_admin_password),
            role="admin",
            active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    analyst = db.scalar(select(User).where(User.email == settings.demo_analyst_email))
    if analyst is None:
        analyst = User(
            name="Analista Demonstrativo",
            email=settings.demo_analyst_email,
            password_hash=hash_password(settings.demo_analyst_password),
            role="analyst",
            active=True,
        )
        db.add(analyst)
        db.commit()
        db.refresh(analyst)

    # O analista demo começa somente com a empresa Alpha (ID 1).
    existing = db.scalar(
        select(UserCompanyAccess).where(
            UserCompanyAccess.user_id == analyst.id,
            UserCompanyAccess.company_id == 1,
        )
    )
    if existing is None:
        db.add(
            UserCompanyAccess(
                user_id=analyst.id,
                company_id=1,
                assigned_by=admin.id,
            )
        )
        db.commit()
