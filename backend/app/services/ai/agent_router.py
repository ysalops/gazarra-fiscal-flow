from fastapi import HTTPException

from app.agents.registry import AgentSpec, get_agent


DEFAULT_AGENT = "agente-fiscal-gazarra"


ROUTING_RULES = [
    (
        [
            "de/para",
            "de para",
            "product mapper",
            "produto",
            "gtin",
            "ean",
            "ncm",
            "código fornecedor",
            "codigo fornecedor",
        ],
        "product-mapper-gazarra",
    ),
    (
        [
            "sped",
            "efd icms",
            "efd contrib",
            "efd-contrib",
            "registro 0200",
        ],
        "revisao-sped-gazarra",
    ),
    (
        [
            "guia",
            "vencimento",
            "pagamento",
            "arrecadação",
            "arrecadacao",
        ],
        "conferencia-guias-gazarra",
    ),
    (
        [
            "domínio",
            "dominio",
            "importação",
            "importacao",
        ],
        "integracao-dominio-gazarra",
    ),
    (
        [
            "documento faltante",
            "documentos faltantes",
            "completude",
            "temos tudo",
            "faltando",
        ],
        "completude-fiscal-gazarra",
    ),
    (
        [
            "pendência",
            "pendencias",
            "pendências",
            "exceção",
            "excecoes",
            "exceções",
            "o que falta para fechar",
            "fechar a empresa",
        ],
        "painel-excecoes-gazarra",
    ),
    (
        [
            "auditoria",
            "pós-importação",
            "pos-importacao",
            "divergência",
            "divergencia",
            "reconciliar",
        ],
        "auditoria-pos-importacao-gazarra",
    ),
    (
        [
            "apuração",
            "apuracao",
            "memória de cálculo",
            "memoria de calculo",
        ],
        "apuracao-preliminar-gazarra",
    ),
    (
        [
            "reforma tributária",
            "reforma tributaria",
            "cbs",
            "ibs",
            "issqn",
        ],
        "reforma-cbs-ibs-gazarra",
    ),
    (
        [
            "dctfweb",
            "mit",
        ],
        "06-dctfweb-mit",
    ),
    (
        [
            "e-social",
            "esocial",
        ],
        "08-esocial",
    ),
    (
        [
            "folha",
            "folha mensal",
        ],
        "15-folha-mensal",
    ),
    (
        [
            "admissão",
            "admissao",
        ],
        "16-admissao",
    ),
    (
        [
            "rescisão",
            "rescisao",
        ],
        "11-rescisao",
    ),
    (
        [
            "férias",
            "ferias",
            "13º",
            "13 salario",
            "13 salário",
        ],
        "10-ferias-13",
    ),
    (
        [
            "fgts",
        ],
        "14-fgts-digital",
    ),
    (
        [
            "inss",
        ],
        "12-inss",
    ),
    (
        [
            "irrf",
        ],
        "13-irrf",
    ),
]


def select_agent(
    message: str,
    requested_agent: str = "auto",
) -> AgentSpec:
    if requested_agent and requested_agent != "auto":
        agent = get_agent(requested_agent)

        if agent is None:
            raise HTTPException(
                status_code=404,
                detail="Agente solicitado não encontrado.",
            )

        return agent

    normalized = message.lower().strip()

    for keywords, agent_name in ROUTING_RULES:
        if any(keyword in normalized for keyword in keywords):
            agent = get_agent(agent_name)

            if agent is not None:
                return agent

    agent = get_agent(DEFAULT_AGENT)

    if agent is None:
        raise HTTPException(
            status_code=500,
            detail="Agente fiscal padrão não foi carregado.",
        )

    return agent
