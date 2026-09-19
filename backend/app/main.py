from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, SessionLocal

# Importa os modelos para registrá-los no metadata
from app.models import entities  # noqa: F401

from app.api.routes import router
from app.api.fiscal_routes import (
    router as fiscal_router,
)
from app.api.ai_routes import (
    router as ai_router,
)
from app.api.auth_routes import router as auth_router
from app.api.admin_routes import router as admin_router
from app.services.auth_seed import seed_demo_users


app = FastAPI(
    title="GAZARRA POC API",
    version="0.4.0",
    description=(
        "POC do Fiscal Flow + "
        "Product Mapper + "
        "Dashboard Fiscal + "
        "GAZARRA IA"
    ),
)


# =========================================================
# CORS
# =========================================================

origins = [
    x.strip()
    for x in settings.cors_origins.split(",")
    if x.strip()
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_demo_users(db)
    finally:
        db.close()


# =========================================================
# ROTAS EXISTENTES DA POC
# =========================================================

app.include_router(
    router,
    prefix="/api",
)


# =========================================================
# DASHBOARD FISCAL
# =========================================================

app.include_router(
    fiscal_router
)


# =========================================================
# GAZARRA IA
# =========================================================

app.include_router(
    ai_router
)


# =========================================================
# AUTENTICAÇÃO E ADMINISTRAÇÃO
# =========================================================

app.include_router(auth_router)
app.include_router(admin_router)
