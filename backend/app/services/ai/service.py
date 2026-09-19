from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.agents.registry import AgentSpec
from app.core.config import settings
from app.schemas.ai import (
    AIChatContext,
    AIChatRequest,
    AIChatResponse,
)
from app.services.ai.agent_router import select_agent
from app.services.ai.context_builder import (
    compact_context_for_prompt,
    get_fiscal_context,
)
from app.services.llm.router import get_llm_provider


CRITICAL_AGENTS = {
    "agente-fiscal-gazarra",
    "product-mapper-gazarra",
    "revisao-sped-gazarra",
    "conferencia-guias-gazarra",
    "integracao-dominio-gazarra",
    "auditoria-pos-importacao-gazarra",
    "apuracao-preliminar-gazarra",
    "reforma-cbs-ibs-gazarra",
}


def _comparison(
    items: List[dict],
    name: str,
) -> Optional[dict]:
    for item in items or []:
        if item.get("name", "").upper() == name.upper():
            return item

    return None


def _currency(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0

    formatted = f"{number:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def _percentage(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0

    return f"{number:.2f}%".replace(".", ",")


def _variation_text(item: Optional[dict]) -> str:
    if not item:
        return "sem base comparativa disponível"

    variation = float(item.get("variation_percentage", 0))

    if variation > 0:
        direction = "aumento"
    elif variation < 0:
        direction = "redução"
    else:
        direction = "estabilidade"

    return f"{direction} de {_percentage(abs(variation))}"


def _demo_answer(
    request: AIChatRequest,
    fiscal: Dict[str, Any],
    agent: AgentSpec,
) -> str:
    company = fiscal.get("company", {})
    revenue = fiscal.get("revenue", {})
    taxes = fiscal.get("taxes", {})
    simples = fiscal.get("simples", {})
    monthly = fiscal.get("monthly_comparison", [])
    yearly = fiscal.get("yearly_comparison", [])
    obligations = fiscal.get("obligations", [])
    certificates = fiscal.get("certificates", [])

    message = request.message.lower()

    das_month = _comparison(monthly, "DAS")
    st_month = _comparison(monthly, "ST")
    difal_month = _comparison(monthly, "DIFAL")
    das_year = _comparison(yearly, "DAS")

    pending_obligations = [
        item
        for item in obligations
        if item.get("status", "").lower() not in {
            "entregue",
            "regular",
            "ok",
        }
    ]

    attention_certificates = [
        item
        for item in certificates
        if item.get("status", "").lower() not in {
            "regular",
            "ok",
        }
    ]

    prefix = (
        f"Análise demonstrativa de {company.get('name', 'empresa')} "
        f"na competência {request.competence}, usando o agente “{agent.title}”."
    )

    if "das" in message or "alíquota" in message or "aliquota" in message:
        answer = (
            f"{prefix}\n\n"
            f"O DAS está em {_currency(taxes.get('das'))}, com alíquota efetiva de "
            f"{_percentage(taxes.get('effective_rate'))}. Em relação ao mês anterior, "
            f"houve {_variation_text(das_month)}. Na comparação anual, "
            f"há {_variation_text(das_year)}. O faturamento sem ST da competência é "
            f"{_currency(revenue.get('without_st'))}."
        )

    elif "difal" in message:
        answer = (
            f"{prefix}\n\n"
            f"O DIFAL da competência está em {_currency(taxes.get('difal'))}. "
            f"Na comparação com o mês anterior, houve {_variation_text(difal_month)}. "
            "O detalhamento por fornecedor/documento deve ser conferido antes de qualquer "
            "conclusão fiscal definitiva."
        )

    elif "st" in message or "substituição tributária" in message or "substituicao tributaria" in message:
        answer = (
            f"{prefix}\n\n"
            f"O valor de ST é {_currency(taxes.get('st'))}, com {_variation_text(st_month)} "
            "em relação ao mês anterior. A análise final deve considerar UF, CFOP, produto, "
            "NCM/CEST e vigência da regra aplicável."
        )

    elif any(
        term in message
        for term in [
            "pendência",
            "pendencias",
            "pendências",
            "falta",
            "fechar",
            "exceção",
            "excecoes",
        ]
    ):
        if pending_obligations:
            obligation_text = ", ".join(
                f"{item.get('name')} ({item.get('status')})"
                for item in pending_obligations
            )
        else:
            obligation_text = "não há obrigação marcada como pendente no contexto disponível"

        if attention_certificates:
            certificate_text = ", ".join(
                f"{item.get('type')} ({item.get('status')})"
                for item in attention_certificates
            )
        else:
            certificate_text = "não há certidão marcada com status de atenção no contexto disponível"

        answer = (
            f"{prefix}\n\n"
            f"No recorte atual, {obligation_text}. Quanto às certidões, {certificate_text}. "
            "Esta checagem cobre somente os dados hoje disponíveis no Dashboard Fiscal; "
            "completude documental, Domínio, SPED e demais fontes ainda precisam ser integrados "
            "para uma conclusão de fechamento."
        )

    else:
        answer = (
            f"{prefix}\n\n"
            f"Resumo da competência: faturamento sem ST de {_currency(revenue.get('without_st'))}, "
            f"faturamento com ST de {_currency(revenue.get('with_st'))}, DAS de "
            f"{_currency(taxes.get('das'))}, ST de {_currency(taxes.get('st'))} e DIFAL de "
            f"{_currency(taxes.get('difal'))}. A alíquota efetiva está em "
            f"{_percentage(taxes.get('effective_rate'))}. O limite do Simples está "
            f"{_percentage(simples.get('used_percentage'))} utilizado."
        )

    return (
        f"{answer}\n\n"
        "Observação: a GAZARRA IA está em modo demonstrativo e estes dados são simulados. "
        "Nenhuma transmissão, pagamento, alteração cadastral ou decisão fiscal foi executada."
    )


def _build_system_prompt(
    agent: AgentSpec,
    source: str,
    environment: str,
) -> str:
    return f"""
Você é a GAZARRA IA, assistente corporativa interna da operação fiscal.

OBJETIVO
Apoiar análise, conferência, explicação e priorização do trabalho fiscal usando apenas o contexto fornecido e as regras do agente selecionado.

REGRAS OBRIGATÓRIAS
- Não invente dados, documentos, integrações, leis, resultados ou evidências ausentes.
- Diferencie fatos do contexto, inferências e itens que exigem validação humana.
- Nunca afirme que transmitiu obrigação, pagou guia, alterou cadastro, importou no Domínio ou executou ação externa.
- Ações críticas dependem de autorização e revisão humana.
- Preserve segregação por empresa e competência.
- Se a fonte for mock/demo, informe claramente que os dados são simulados.
- Não substitua a aprovação técnica do contador.
- Responda em português do Brasil, de forma objetiva e profissional.
- Quando a pergunta não puder ser respondida pelos dados disponíveis, diga exatamente o que está faltando.

FONTE ATUAL DOS DADOS: {source}
AMBIENTE: {environment}

AGENTE OPERACIONAL SELECIONADO
{agent.content}
""".strip()


def _build_user_prompt(
    request: AIChatRequest,
    fiscal_context: str,
) -> str:
    return f"""
EMPRESA ID: {request.company_id}
COMPETÊNCIA: {request.competence}

CONTEXTO ESTRUTURADO DO FISCAL FLOW / DASHBOARD:
{fiscal_context}

PERGUNTA DO USUÁRIO:
{request.message}

Responda somente com base no contexto fornecido e nas regras do agente.
""".strip()


def _provider_metadata() -> Tuple[str, Optional[str], bool]:
    provider_name = settings.llm_provider.lower().strip()

    if provider_name == "openai":
        return (
            "openai",
            settings.openai_model or None,
            bool(settings.openai_api_key),
        )

    if provider_name == "bedrock":
        return (
            "bedrock",
            settings.bedrock_model_id or None,
            bool(settings.bedrock_model_id),
        )

    return (
        "demo",
        None,
        False,
    )


def chat(request: AIChatRequest) -> AIChatResponse:
    agent = select_agent(
        message=request.message,
        requested_agent=request.agent,
    )

    fiscal = get_fiscal_context(
        company_id=request.company_id,
        competence=request.competence,
    )

    metadata = fiscal.get("metadata") or {}
    company = fiscal.get("company") or {}

    source = metadata.get("source", "mock")
    environment = metadata.get("environment", "demo")

    provider_name, model_name, provider_configured = _provider_metadata()

    answer: str
    warning: Optional[str] = None
    demo_mode = provider_name == "demo" or not provider_configured

    if demo_mode:
        answer = _demo_answer(
            request=request,
            fiscal=fiscal,
            agent=agent,
        )

        if provider_name != "demo" and not provider_configured:
            warning = (
                f"O provedor {provider_name} foi selecionado, mas as credenciais/modelo "
                "não estão completamente configurados. A resposta foi gerada no modo demonstrativo."
            )
            provider_name = "demo"
            model_name = None

    else:
        provider = get_llm_provider()

        if provider is None:
            answer = _demo_answer(
                request=request,
                fiscal=fiscal,
                agent=agent,
            )
            provider_name = "demo"
            model_name = None
            demo_mode = True
            warning = "Nenhum provedor de LLM ativo."

        else:
            system_prompt = _build_system_prompt(
                agent=agent,
                source=source,
                environment=environment,
            )

            user_prompt = _build_user_prompt(
                request=request,
                fiscal_context=compact_context_for_prompt(fiscal),
            )

            answer = provider.analyze(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

    return AIChatResponse(
        answer=answer,
        agent_used=agent.name,
        agent_title=agent.title,
        provider=provider_name,
        model=model_name,
        demo_mode=demo_mode,
        requires_human_review=(
            agent.name in CRITICAL_AGENTS
        ),
        context=AIChatContext(
            company_id=request.company_id,
            company_name=company.get(
                "name",
                f"Empresa {request.company_id}",
            ),
            competence=request.competence,
            source=source,
            environment=environment,
        ),
        sources_used=[
            f"Dashboard Fiscal ({source})",
            f"Agente: {agent.name}",
        ],
        generated_at=datetime.now(timezone.utc),
        warning=warning,
    )
