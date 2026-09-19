import json
from typing import Any, Dict

from app.services.fiscal.mock_provider import MockFiscalProvider


_fiscal_provider = MockFiscalProvider()


def get_fiscal_context(
    company_id: int,
    competence: str,
) -> Dict[str, Any]:
    dashboard = _fiscal_provider.get_dashboard(
        company_id=company_id,
        competence=competence,
    )

    if hasattr(dashboard, "model_dump"):
        return dashboard.model_dump(mode="json")

    return dashboard.dict()


def compact_context_for_prompt(
    fiscal_context: Dict[str, Any],
) -> str:
    # Nesta primeira versão usamos o contexto fiscal estruturado inteiro.
    # Quando Domínio/Jettax/RAG entrarem, este ponto vira o agregador de contexto.
    return json.dumps(
        fiscal_context,
        ensure_ascii=False,
        indent=2,
    )
