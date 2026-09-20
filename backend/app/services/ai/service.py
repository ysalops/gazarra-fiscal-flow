from __future__ import annotations

from datetime import datetime, timezone
import json
import re
import time
import unicodedata
from typing import Any, Dict, Iterable, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.agents.registry import AgentSpec
from app.core.config import settings
from app.models.entities import User
from app.schemas.ai import AIChatContext, AIChatRequest, AIChatResponse
from app.services.ai.agent_router import select_agent
from app.services.ai.attachments import attachments_prompt_context, load_attachments
from app.services.ai.context_builder import compact_context_for_prompt, get_fiscal_context
from app.services.ai.conversation_store import (
    add_message,
    conversation_history_for_prompt,
    get_or_create_conversation,
)
from app.services.ai.tool_registry import execute_tool, get_ollama_tools
from app.services.llm.router import get_llm_provider


CRITICAL_AGENTS = {
    "integracao-dominio-gazarra",
    "auditoria-pos-importacao-gazarra",
    "apuracao-preliminar-gazarra",
    "revisao-sped-gazarra",
    "conferencia-guias-gazarra",
}

MONTHS_PT = {
    "janeiro": "01", "jan": "01",
    "fevereiro": "02", "fev": "02",
    "marco": "03", "mar": "03",
    "abril": "04", "abr": "04",
    "maio": "05", "mai": "05",
    "junho": "06", "jun": "06",
    "julho": "07", "jul": "07",
    "agosto": "08", "ago": "08",
    "setembro": "09", "set": "09",
    "outubro": "10", "out": "10",
    "novembro": "11", "nov": "11",
    "dezembro": "12", "dez": "12",
}


def _normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(value.lower().strip().split())


def _currency(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    formatted = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def _percentage(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return f"{number:.2f}%".replace(".", ",")


def _provider_metadata() -> Tuple[str, Optional[str], bool]:
    provider_name = settings.llm_provider.lower().strip()
    if provider_name == "ollama":
        return "ollama", settings.ollama_model or None, bool(settings.ollama_base_url and settings.ollama_model)
    if provider_name == "openai":
        return "openai", settings.openai_model or None, bool(settings.openai_api_key)
    if provider_name == "bedrock":
        return "bedrock", settings.bedrock_model_id or None, bool(settings.bedrock_model_id)
    return "demo", None, False


def _extract_competence(message: str, fallback: Optional[str] = None) -> Optional[str]:
    normalized = _normalize_text(message)
    iso = re.search(r"\b(20\d{2})[-/](0?[1-9]|1[0-2])\b", normalized)
    if iso:
        return f"{iso.group(1)}-{int(iso.group(2)):02d}"
    br = re.search(r"\b(0?[1-9]|1[0-2])/(20\d{2})\b", normalized)
    if br:
        return f"{br.group(2)}-{int(br.group(1)):02d}"
    for month_name, month_number in MONTHS_PT.items():
        match = re.search(rf"\b{month_name}\b(?:\s+de)?\s+(20\d{{2}})\b", normalized)
        if match:
            return f"{match.group(1)}-{month_number}"
    return fallback


def _is_company_list_request(message: str) -> bool:
    normalized = _normalize_text(message)
    company_terms = ("empresa", "empresas", "cliente", "clientes")
    access_terms = (
        "posso acessar", "tenho acesso", "meu acesso", "meus acessos",
        "existem na base", "tem na base", "listar", "liste", "mostre", "quais",
    )
    return any(term in normalized for term in company_terms) and any(term in normalized for term in access_terms)


def _company_list_answer(result: Dict[str, Any]) -> str:
    companies = result.get("companies") or []
    if not companies:
        return "Não há empresas disponíveis para o seu usuário neste momento."
    scope_text = (
        "Você possui acesso a todas as empresas cadastradas neste ambiente."
        if result.get("access_scope") == "all"
        else "Estas são as empresas atribuídas ao seu usuário."
    )
    lines = []
    for company in companies:
        detail = []
        if company.get("cnpj"):
            detail.append(f"CNPJ {company['cnpj']}")
        location = " / ".join(v for v in [company.get("city"), company.get("state")] if v)
        if location:
            detail.append(location)
        suffix = f" — {' · '.join(detail)}" if detail else ""
        lines.append(f"- {company.get('name', 'Empresa')}{suffix}")
    return f"{scope_text}\n\n" + "\n".join(lines)


def _resolve_requested_company(
    message: str,
    *,
    user: User,
    db: Session,
    fallback_company_id: Optional[int],
) -> tuple[Optional[dict], bool]:
    result = execute_tool("list_companies", {}, user=user, db=db)
    companies = result.get("companies") or []
    normalized = _normalize_text(message)
    message_digits = re.sub(r"\D", "", message or "")

    for company in companies:
        name = _normalize_text(company.get("name", ""))
        aliases = {name}
        simplified = name
        for prefix in ("cliente demonstrativo ", "cliente ", "empresa "):
            if simplified.startswith(prefix):
                simplified = simplified[len(prefix):].strip()
        if simplified:
            aliases.add(simplified)
            aliases.add(simplified.split()[-1])
        cnpj_digits = re.sub(r"\D", "", str(company.get("cnpj") or ""))
        if any(alias and re.search(rf"\b{re.escape(alias)}\b", normalized) for alias in aliases):
            return company, True
        if cnpj_digits and cnpj_digits in message_digits:
            return company, True

    explicit_company = bool(re.search(r"\b(?:empresa|cliente)\s+[a-z0-9]", normalized))
    if explicit_company:
        return None, True
    if fallback_company_id is not None:
        for company in companies:
            if int(company.get("id")) == int(fallback_company_id):
                return company, False
    return None, False


def _is_objective_fiscal_request(message: str) -> bool:
    normalized = _normalize_text(message)
    metric = any(term in normalized for term in (
        "das", "aliquota efetiva", "faturamento", "difal",
        "substituicao tributaria", "valor de st", " st ", "resumo fiscal",
    ))
    if not metric:
        return False
    # "O que é DAS?" deve ser conversa normal. Fast-path somente quando há intenção de consultar dado.
    query_signal = any(term in normalized for term in (
        "qual foi", "quanto", "valor", "em 20", "competencia", "competência",
        "maio", "abril", "marco", "março", "fevereiro", "janeiro", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
        "empresa ", "cliente ", "resumo fiscal",
    ))
    return query_signal


def _fiscal_metric_answer(dashboard: Dict[str, Any], message: str, competence: str) -> str:
    company = dashboard.get("company") or {}
    taxes = dashboard.get("taxes") or {}
    revenue = dashboard.get("revenue") or {}
    normalized = _normalize_text(message)
    parts: List[str] = []
    if "das" in normalized:
        parts.append(f"DAS (Documento de Arrecadação do Simples Nacional): {_currency(taxes.get('das'))}")
    if "aliquota" in normalized:
        parts.append(f"Alíquota efetiva: {_percentage(taxes.get('effective_rate'))}")
    if "difal" in normalized:
        parts.append(f"DIFAL: {_currency(taxes.get('difal'))}")
    padded = f" {normalized} "
    if "substituicao tributaria" in normalized or "valor de st" in normalized or " st " in padded:
        parts.append(f"ST: {_currency(taxes.get('st'))}")
    if "faturamento" in normalized:
        parts.append(f"Faturamento sem ST: {_currency(revenue.get('without_st'))}")
        parts.append(f"Faturamento com ST: {_currency(revenue.get('with_st'))}")
    if "resumo fiscal" in normalized or not parts:
        parts = [
            f"Faturamento sem ST: {_currency(revenue.get('without_st'))}",
            f"Faturamento com ST: {_currency(revenue.get('with_st'))}",
            f"DAS: {_currency(taxes.get('das'))}",
            f"Alíquota efetiva: {_percentage(taxes.get('effective_rate'))}",
            f"ST: {_currency(taxes.get('st'))}",
            f"DIFAL: {_currency(taxes.get('difal'))}",
        ]
    return (
        f"{company.get('name', 'Empresa')} — competência {competence}:\n\n"
        + "\n".join(f"- {item}" for item in parts)
    )


def _likely_internal_data_request(message: str) -> bool:
    normalized = _normalize_text(message)
    terms = (
        "empresa", "cliente", "dashboard", "na base", "nos dados", "meu acesso",
        "faturamento", "competencia", "competência", "fechamento", "pendencia", "pendência",
        "quanto pagou", "quanto foi", "desta empresa", "desse cliente",
    )
    return any(term in normalized for term in terms)


def _requires_human_review(agent: AgentSpec, message: str) -> bool:
    if agent.name not in CRITICAL_AGENTS:
        return False
    normalized = _normalize_text(message)
    action_terms = (
        "transmit", "pagar", "pagamento", "alterar", "corrigir no dominio", "corrigir no domínio",
        "importar", "aprovar", "executar", "enviar obrigacao", "enviar obrigação",
    )
    return any(term in normalized for term in action_terms)


def _build_system_prompt(agent: AgentSpec, source: str, environment: str) -> str:
    specialist = ""
    if agent.name != "gazarra-general":
        specialist = f"\n\nAGENTE ESPECIALIZADO ATIVADO\n{agent.content}"
    return f"""
Você é a GAZARRA IA, assistente de uso geral da equipe GAZARRA.

Você pode conversar sobre assuntos gerais, explicar conceitos, ajudar a escrever textos, organizar ideias,
analisar conteúdos enviados e apoiar tarefas profissionais. Seu diferencial é que, quando a pergunta envolve
a operação da GAZARRA, você pode usar agentes especializados, arquivos anexados e ferramentas autorizadas.

REGRAS PARA DADOS INTERNOS
- Nunca invente dados de clientes, empresas, dashboard, documentos ou integrações.
- Quando precisar de um dado interno e houver ferramenta apropriada, use a ferramenta.
- Resultados das ferramentas já respeitam as permissões do usuário.
- Se faltar empresa, competência ou documento para uma consulta específica, peça apenas a informação que falta.
- Nunca afirme ter transmitido obrigação, pago guia, alterado cadastro ou executado ação externa.
- Dados de ambiente mock/demo devem ser tratados como demonstrativos.

REGRAS DE RESPOSTA
- Responda em português do Brasil, salvo se o usuário pedir outro idioma.
- Seja natural e útil. Não force o assunto fiscal quando a pergunta não for fiscal.
- Não exponha raciocínio interno, cadeia de pensamento ou detalhes técnicos desnecessários.
- Se a pergunta pedir informação atual da internet, esclareça que este modelo local não possui navegação web nesta POC.

FONTE INTERNA ATUAL: {source}
AMBIENTE: {environment}
{specialist}
""".strip()


def _build_user_prompt(
    request: AIChatRequest,
    *,
    fiscal_context: Optional[str],
    attachment_context: str,
) -> str:
    blocks: list[str] = []
    if request.company_id:
        blocks.append(f"EMPRESA EM CONTEXTO OPCIONAL: ID {request.company_id}")
    if request.competence:
        blocks.append(f"COMPETÊNCIA EM CONTEXTO OPCIONAL: {request.competence}")
    if fiscal_context:
        blocks.append(f"CONTEXTO INTERNO ESTRUTURADO:\n{fiscal_context}")
    if attachment_context:
        blocks.append(f"ANEXOS DESTA MENSAGEM:\n{attachment_context}")
    blocks.append(f"PERGUNTA DO USUÁRIO:\n{request.message}")
    return "\n\n".join(blocks)


def _base_context(request: AIChatRequest) -> tuple[Optional[Dict[str, Any]], str, str, Dict[str, Any]]:
    fiscal: Optional[Dict[str, Any]] = None
    source = "mock"
    environment = "demo"
    company: Dict[str, Any] = {}
    if request.company_id and request.competence:
        fiscal = get_fiscal_context(request.company_id, request.competence)
        metadata = fiscal.get("metadata") or {}
        company = fiscal.get("company") or {}
        source = metadata.get("source", source)
        environment = metadata.get("environment", environment)
    return fiscal, source, environment, company


def _direct_answer(
    request: AIChatRequest,
    *,
    user: User,
    db: Session,
) -> Optional[dict[str, Any]]:
    if _is_company_list_request(request.message):
        result = execute_tool("list_companies", {}, user=user, db=db)
        return {
            "answer": _company_list_answer(result),
            "tools": ["list_companies"],
            "company": {},
            "competence": request.competence,
            "source": "mock",
            "environment": "demo",
        }

    if not _is_objective_fiscal_request(request.message):
        return None

    target_company, explicit = _resolve_requested_company(
        request.message,
        user=user,
        db=db,
        fallback_company_id=request.company_id,
    )
    if target_company is None:
        return {
            "answer": (
                "Qual empresa você quer consultar? Você pode informar o nome na própria pergunta, "
                "por exemplo: “Qual foi o DAS da Beta em maio de 2026?”."
                if not explicit
                else "Não localizei essa empresa entre as empresas que seu usuário pode acessar."
            ),
            "tools": ["list_companies"],
            "company": {},
            "competence": request.competence,
            "source": "mock",
            "environment": "demo",
        }

    competence = _extract_competence(request.message, request.competence)
    if not competence:
        return {
            "answer": f"Qual competência você quer consultar para {target_company.get('name', 'essa empresa')}?",
            "tools": ["list_companies"],
            "company": target_company,
            "competence": None,
            "source": "mock",
            "environment": "demo",
        }

    dashboard = execute_tool(
        "get_fiscal_dashboard",
        {"company_id": int(target_company["id"]), "competence": competence},
        user=user,
        db=db,
    )
    metadata = dashboard.get("metadata") or {}
    return {
        "answer": _fiscal_metric_answer(dashboard, request.message, competence),
        "tools": ["get_fiscal_dashboard"],
        "company": dashboard.get("company") or target_company,
        "competence": competence,
        "source": metadata.get("source", "mock"),
        "environment": metadata.get("environment", "demo"),
    }


def _response(
    *,
    answer: str,
    conversation_id: Optional[str],
    request: AIChatRequest,
    agent: AgentSpec,
    provider_name: str,
    model_name: Optional[str],
    demo_mode: bool,
    source: str,
    environment: str,
    company: Optional[dict],
    competence: Optional[str],
    tools_used: list[str],
    attachment_names: list[str],
    warning: Optional[str] = None,
) -> AIChatResponse:
    company = company or {}
    sources: list[str] = []
    if tools_used == ["list_companies"]:
        sources.append("Cadastro de empresas e permissões")
    if "get_fiscal_dashboard" in tools_used:
        sources.append(f"Dashboard Fiscal ({source})")
    sources.extend(f"Arquivo: {name}" for name in attachment_names)
    if agent.name != "gazarra-general":
        sources.append(f"Agente: {agent.name}")
    sources.extend(f"Tool: {tool}" for tool in tools_used)

    return AIChatResponse(
        answer=answer,
        conversation_id=conversation_id,
        agent_used=agent.name,
        agent_title=agent.title,
        provider=provider_name,
        model=model_name,
        demo_mode=demo_mode,
        requires_human_review=_requires_human_review(agent, request.message),
        context=AIChatContext(
            company_id=company.get("id") or request.company_id,
            company_name=company.get("name"),
            competence=competence or request.competence,
            source=source,
            environment=environment,
        ),
        sources_used=sources,
        generated_at=datetime.now(timezone.utc),
        warning=warning,
    )


def chat(request: AIChatRequest, *, user: User, db: Session) -> AIChatResponse:
    history = conversation_history_for_prompt(db, user, request.conversation_id)
    conversation = get_or_create_conversation(db, user, request.conversation_id, request.message)
    add_message(db, conversation, role="user", content=request.message)

    agent = select_agent(request.message, request.agent)
    provider_name, model_name, configured = _provider_metadata()
    demo_mode = provider_name == "demo" or not configured
    warning: Optional[str] = None
    attachments = load_attachments(request.attachments, user.id)
    attachment_names = [item.get("filename", "arquivo") for item in attachments]

    direct = _direct_answer(request, user=user, db=db)
    tools_used: list[str] = []
    if direct:
        answer = direct["answer"]
        tools_used = direct["tools"]
        source = direct["source"]
        environment = direct["environment"]
        company = direct["company"]
        competence = direct["competence"]
    else:
        fiscal, source, environment, company = _base_context(request)
        competence = request.competence
        provider = get_llm_provider() if configured else None
        if provider is None:
            answer = (
                "A GAZARRA IA está sem um provedor de linguagem ativo. "
                "Configure o Ollama, Bedrock ou outro provedor para conversar livremente."
            )
            demo_mode = True
            warning = "Nenhum provedor de LLM ativo."
        else:
            system_prompt = _build_system_prompt(agent, source, environment)
            user_prompt = _build_user_prompt(
                request,
                fiscal_context=compact_context_for_prompt(fiscal) if fiscal else None,
                attachment_context=attachments_prompt_context(attachments),
            )
            if provider_name == "ollama" and _likely_internal_data_request(request.message) and not attachments:
                answer, tools_used = provider.chat_with_tools(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    tools=get_ollama_tools(),
                    executor=lambda name, arguments: execute_tool(name, arguments, user=user, db=db),
                )
            else:
                # Providers atuais recebem o histórico indiretamente apenas no streaming.
                history_text = ""
                if history:
                    history_text = "\n\nHISTÓRICO RECENTE:\n" + "\n".join(
                        f"{item['role']}: {item['content']}" for item in history[-8:]
                    )
                answer = provider.analyze(system_prompt, user_prompt + history_text)

    response = _response(
        answer=answer,
        conversation_id=conversation.id,
        request=request,
        agent=agent,
        provider_name=provider_name,
        model_name=model_name,
        demo_mode=demo_mode,
        source=source,
        environment=environment,
        company=company,
        competence=competence,
        tools_used=tools_used,
        attachment_names=attachment_names,
        warning=warning,
    )
    add_message(
        db,
        conversation,
        role="assistant",
        content=response.answer,
        agent=response.agent_used,
        metadata={"sources": response.sources_used, "provider": response.provider},
    )
    return response


def _json_event(event_type: str, **payload: Any) -> str:
    return json.dumps({"type": event_type, **payload}, ensure_ascii=False, default=str) + "\n"


def _text_chunks(text: str, size: int = 22) -> Iterable[str]:
    for index in range(0, len(text), size):
        yield text[index:index + size]


def stream_chat_events(request: AIChatRequest, *, user: User, db: Session) -> Iterable[str]:
    history = conversation_history_for_prompt(db, user, request.conversation_id)
    conversation = get_or_create_conversation(db, user, request.conversation_id, request.message)
    add_message(db, conversation, role="user", content=request.message)

    agent = select_agent(request.message, request.agent)
    provider_name, model_name, configured = _provider_metadata()
    demo_mode = provider_name == "demo" or not configured
    attachments = load_attachments(request.attachments, user.id)
    attachment_names = [item.get("filename", "arquivo") for item in attachments]
    images = [item.get("image_base64") for item in attachments if item.get("image_base64")]

    yield _json_event(
        "start",
        conversation_id=conversation.id,
        agent_used=agent.name,
        agent_title=agent.title,
    )

    direct = _direct_answer(request, user=user, db=db)
    tools_used: list[str] = []
    warning: Optional[str] = None
    answer_parts: list[str] = []

    if direct:
        answer = direct["answer"]
        tools_used = direct["tools"]
        source = direct["source"]
        environment = direct["environment"]
        company = direct["company"]
        competence = direct["competence"]
        for chunk in _text_chunks(answer):
            answer_parts.append(chunk)
            yield _json_event("delta", text=chunk)
            time.sleep(0.012)
    else:
        fiscal, source, environment, company = _base_context(request)
        competence = request.competence
        provider = get_llm_provider() if configured else None
        if provider is None:
            answer = "A GAZARRA IA está sem um provedor de linguagem ativo. Configure um provedor para continuar."
            demo_mode = True
            warning = "Nenhum provedor de LLM ativo."
            for chunk in _text_chunks(answer):
                answer_parts.append(chunk)
                yield _json_event("delta", text=chunk)
        else:
            system_prompt = _build_system_prompt(agent, source, environment)
            user_prompt = _build_user_prompt(
                request,
                fiscal_context=compact_context_for_prompt(fiscal) if fiscal else None,
                attachment_context=attachments_prompt_context(attachments),
            )

            # Para perguntas internas complexas, deixamos o agente/tool resolver primeiro.
            # Perguntas gerais e análise de anexos usam streaming real do Ollama.
            if provider_name == "ollama" and _likely_internal_data_request(request.message) and not attachments:
                answer, tools_used = provider.chat_with_tools(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    tools=get_ollama_tools(),
                    executor=lambda name, arguments: execute_tool(name, arguments, user=user, db=db),
                )
                for chunk in _text_chunks(answer):
                    answer_parts.append(chunk)
                    yield _json_event("delta", text=chunk)
                    time.sleep(0.008)
            elif provider_name == "ollama" and hasattr(provider, "stream_analyze"):
                for chunk in provider.stream_analyze(
                    system_prompt,
                    user_prompt,
                    history=history,
                    images=images,
                ):
                    answer_parts.append(chunk)
                    yield _json_event("delta", text=chunk)
            else:
                answer = provider.analyze(system_prompt, user_prompt)
                for chunk in _text_chunks(answer):
                    answer_parts.append(chunk)
                    yield _json_event("delta", text=chunk)
                    time.sleep(0.008)

    answer = "".join(answer_parts).strip()
    response = _response(
        answer=answer,
        conversation_id=conversation.id,
        request=request,
        agent=agent,
        provider_name=provider_name,
        model_name=model_name,
        demo_mode=demo_mode,
        source=source,
        environment=environment,
        company=company,
        competence=competence,
        tools_used=tools_used,
        attachment_names=attachment_names,
        warning=warning,
    )
    add_message(
        db,
        conversation,
        role="assistant",
        content=response.answer,
        agent=response.agent_used,
        metadata={"sources": response.sources_used, "provider": response.provider},
    )
    yield _json_event("done", data=response.model_dump(mode="json"))
