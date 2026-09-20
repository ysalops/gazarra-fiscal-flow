from __future__ import annotations

import unicodedata
from typing import Iterable

from fastapi import HTTPException

from app.agents.registry import AgentSpec, get_agent


GENERAL_AGENT = AgentSpec(
    name="gazarra-general",
    title="GAZARRA IA",
    category="Geral",
    version="1.0",
    status="ativo",
    permissions=["read", "assist"],
    path="internal/general",
    content=(
        "Assistente geral da GAZARRA. Responde perguntas amplas, apoia redação, "
        "explicações, análise e organização do trabalho. Quando a pergunta exigir "
        "dados internos ou conhecimento especializado, o roteador deve usar agentes "
        "e ferramentas autorizadas do backend."
    ),
)


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(value.lower().split())


# Pesos altos para intenções específicas; termos genéricos recebem peso baixo.
# Isso evita que um fechamento fiscal seja enviado ao Product Mapper só porque contém nomes de produtos.
WEIGHTED_RULES: dict[str, list[tuple[str, int]]] = {
    "agente-fiscal-gazarra": [
        ("fechamento fiscal", 12), ("resumo fiscal", 10), ("simples nacional", 7),
        ("das", 6), ("difal", 6), ("st recolhida", 6), ("substituicao tributaria", 6),
        ("icms", 4), ("iss", 4), ("tributo", 4), ("fiscal", 3), ("cfop", 3),
        ("cst", 3), ("csosn", 3), ("nf-e", 2), ("nfe", 2),
    ],
    "product-mapper-gazarra": [
        ("de/para", 12), ("de para", 10), ("product mapper", 12), ("gtin", 8),
        ("ean", 7), ("codigo fornecedor", 7), ("codigo interno", 6), ("ncm", 5),
        ("produto", 1),
    ],
    "cadastro-tributario-produtos-gazarra": [
        ("cadastro tributario", 10), ("tributacao do produto", 9), ("ncm", 5),
        ("cest", 6), ("cst", 4), ("csosn", 4),
    ],
    "revisao-sped-gazarra": [
        ("sped", 12), ("efd icms", 10), ("efd contrib", 10), ("efd-contrib", 10),
        ("registro 0200", 9), ("registro sped", 8),
    ],
    "conferencia-guias-gazarra": [
        ("conferencia de guia", 10), ("guia", 5), ("vencimento", 4),
        ("arrecadacao", 4), ("pagamento", 3),
    ],
    "integracao-dominio-gazarra": [
        ("dominio", 10), ("integracao dominio", 12), ("importacao dominio", 10),
    ],
    "captura-documental-gazarra": [
        ("captura documental", 12), ("coletar xml", 8), ("baixar xml", 7),
    ],
    "completude-fiscal-gazarra": [
        ("completude", 12), ("documentos faltantes", 10), ("documento faltante", 10),
        ("temos tudo", 7), ("faltando", 4),
    ],
    "painel-excecoes-gazarra": [
        ("painel de excecoes", 12), ("excecao", 7), ("pendencia", 5),
        ("o que falta para fechar", 10),
    ],
    "auditoria-pos-importacao-gazarra": [
        ("auditoria pos-importacao", 12), ("pos-importacao", 8), ("reconciliar", 7),
        ("divergencia apos importacao", 8),
    ],
    "apuracao-preliminar-gazarra": [
        ("apuracao preliminar", 12), ("memoria de calculo", 9), ("apuracao", 5),
    ],
    "validacao-pre-importacao-gazarra": [
        ("validacao pre-importacao", 12), ("pre-importacao", 9),
    ],
    "orquestrador-fiscal-flow-gazarra": [
        ("orquestrar fechamento", 12), ("fluxo fiscal", 6), ("fiscal flow", 8),
    ],
    "reforma-cbs-ibs-gazarra": [
        ("reforma tributaria", 12), ("cbs", 8), ("ibs", 8), ("issqn", 7),
    ],
    "06-dctfweb-mit": [("dctfweb", 12), ("mit", 8)],
    "07-efd-reinf": [("efd-reinf", 12), ("reinf", 10)],
    "08-esocial": [("esocial", 12), ("e-social", 12)],
    "09-holerite": [("holerite", 12), ("contracheque", 10)],
    "10-ferias-13": [("ferias", 9), ("13 salario", 9), ("13º", 9)],
    "11-rescisao": [("rescisao", 12)],
    "12-inss": [("inss", 12)],
    "13-irrf": [("irrf", 12)],
    "14-fgts-digital": [("fgts", 12)],
    "15-folha-mensal": [("folha mensal", 12), ("folha de pagamento", 10), ("folha", 4)],
    "16-admissao": [("admissao", 12)],
    "governanca-gazarra": [("governanca", 10), ("seguranca", 6), ("permissao", 5)],
}


def _score_agents(message: str) -> list[tuple[int, AgentSpec]]:
    normalized = _normalize(message)
    scored: list[tuple[int, AgentSpec]] = []
    for agent_name, rules in WEIGHTED_RULES.items():
        score = sum(weight for term, weight in rules if _normalize(term) in normalized)
        if score <= 0:
            continue
        agent = get_agent(agent_name)
        if agent is not None:
            scored.append((score, agent))
    return sorted(scored, key=lambda item: (-item[0], item[1].title))


def _validate_manual_agents(names: Iterable[str]) -> list[AgentSpec]:
    result: list[AgentSpec] = []
    for name in list(dict.fromkeys(names))[:2]:
        agent = get_agent(name)
        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agente '{name}' não encontrado.")
        result.append(agent)
    if not result:
        raise HTTPException(status_code=400, detail="Selecione pelo menos um agente no modo manual.")
    return result


def select_agents(
    message: str,
    *,
    mode: str = "auto",
    requested_agents: list[str] | None = None,
) -> list[AgentSpec]:
    mode = (mode or "auto").strip().lower()
    if mode == "none":
        return [GENERAL_AGENT]
    if mode == "manual":
        return _validate_manual_agents(requested_agents or [])
    if mode not in {"auto", "all"}:
        mode = "auto"

    scored = _score_agents(message)
    if not scored:
        return [GENERAL_AGENT]

    first_score = scored[0][0]
    selected = [scored[0][1]]

    # Automático normalmente usa um especialista. Se a segunda intenção for realmente forte
    # e complementar, pode usar dois. "Todos" permite até dois entre todo o catálogo elegível.
    if len(scored) > 1:
        second_score, second_agent = scored[1]
        threshold = 5 if mode == "all" else max(7, int(first_score * 0.70))
        if second_score >= threshold and second_agent.name != selected[0].name:
            selected.append(second_agent)
    return selected[:2]


def select_agent(message: str, requested_agent: str = "auto") -> AgentSpec:
    """Compatibilidade com chamadas antigas da POC."""
    if requested_agent and requested_agent != "auto":
        return _validate_manual_agents([requested_agent])[0]
    return select_agents(message, mode="auto")[0]
