from typing import Any

from sqlalchemy.orm import Session

from app.core.security import allowed_company_ids, ensure_company_access
from app.models.entities import User
from app.services.fiscal.mock_provider import MockFiscalProvider


_provider = MockFiscalProvider()


OLLAMA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_companies",
            "description": (
                "Lista as empresas que o usuário autenticado tem permissão para acessar. "
                "Use esta ferramenta sempre que o usuário perguntar quais empresas/clientes existem, "
                "quais ele pode acessar ou pedir uma lista de empresas."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fiscal_dashboard",
            "description": (
                "Consulta os dados fiscais estruturados de uma empresa e competência, "
                "incluindo faturamento, DAS, ST, DIFAL, comparativos, certidões e obrigações."
            ),
            "parameters": {
                "type": "object",
                "required": ["company_id", "competence"],
                "properties": {
                    "company_id": {
                        "type": "integer",
                        "description": "ID da empresa permitida ao usuário.",
                    },
                    "competence": {
                        "type": "string",
                        "description": "Competência no formato YYYY-MM, por exemplo 2026-05.",
                    },
                },
            },
        },
    },
]


def get_ollama_tools() -> list[dict]:
    return OLLAMA_TOOLS


def _dump_model(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    return value


def execute_tool(
    name: str,
    arguments: dict[str, Any],
    *,
    user: User,
    db: Session,
) -> Any:
    if name == "list_companies":
        permitted_ids = allowed_company_ids(db, user)
        companies = []
        for company in _provider.list_companies():
            if permitted_ids is not None and company.id not in permitted_ids:
                continue
            companies.append(
                {
                    "id": company.id,
                    "name": company.name,
                    "cnpj": company.cnpj,
                    "city": getattr(company, "city", None),
                    "state": getattr(company, "state", None),
                }
            )
        return {
            "count": len(companies),
            "companies": companies,
            "access_scope": "all" if user.role == "admin" else "assigned",
        }

    if name == "get_fiscal_dashboard":
        company_id = int(arguments.get("company_id"))
        competence = str(arguments.get("competence") or "").strip()
        ensure_company_access(db, user, company_id)
        dashboard = _provider.get_dashboard(
            company_id=company_id,
            competence=competence,
        )
        return _dump_model(dashboard)

    return {
        "error": "tool_not_found",
        "tool": name,
    }
