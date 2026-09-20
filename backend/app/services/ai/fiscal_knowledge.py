from __future__ import annotations

import re
import unicodedata
from typing import Optional


FISCAL_GLOSSARY = {
    "das": {
        "aliases": ["das"],
        "title": "DAS",
        "definition": (
            "DAS significa Documento de Arrecadação do Simples Nacional. "
            "É a guia utilizada para recolher, de forma unificada, os tributos abrangidos pelo Simples Nacional, "
            "conforme o enquadramento e as regras aplicáveis à empresa."
        ),
    },
    "simples nacional": {
        "aliases": ["simples nacional"],
        "title": "Simples Nacional",
        "definition": (
            "O Simples Nacional é um regime compartilhado de arrecadação, cobrança e fiscalização de tributos "
            "voltado a microempresas e empresas de pequeno porte que atendam aos requisitos legais."
        ),
    },
    "icms-st": {
        "aliases": ["icms-st", "icms st", "substituicao tributaria", "substituição tributária"],
        "title": "ICMS-ST",
        "definition": (
            "ICMS-ST é o ICMS sujeito ao regime de substituição tributária. Nesse regime, a responsabilidade pelo "
            "recolhimento do imposto relativo a determinadas operações pode ser atribuída a outro contribuinte da cadeia, "
            "conforme a legislação aplicável."
        ),
    },
    "difal": {
        "aliases": ["difal", "diferencial de aliquota", "diferencial de alíquota"],
        "title": "DIFAL",
        "definition": (
            "DIFAL é o diferencial de alíquota do ICMS. Ele aparece em situações específicas envolvendo operações "
            "interestaduais; a responsabilidade pelo recolhimento e a forma de cálculo dependem da operação e da legislação aplicável."
        ),
    },
    "ncm": {
        "aliases": ["ncm", "nomenclatura comum do mercosul"],
        "title": "NCM",
        "definition": (
            "NCM significa Nomenclatura Comum do Mercosul. É o código usado para classificar mercadorias, servindo de referência "
            "para tratamento tributário, estatístico e aduaneiro."
        ),
    },
    "cfop": {
        "aliases": ["cfop"],
        "title": "CFOP",
        "definition": (
            "CFOP significa Código Fiscal de Operações e de Prestações. Ele identifica a natureza fiscal de entradas, saídas, "
            "aquisições e prestações registradas em documentos e escriturações fiscais."
        ),
    },
    "sped": {
        "aliases": ["sped", "sistema publico de escrituracao digital", "sistema público de escrituração digital"],
        "title": "SPED",
        "definition": (
            "SPED significa Sistema Público de Escrituração Digital. É a infraestrutura digital usada para padronizar e transmitir "
            "escriturações e documentos fiscais, contábeis e relacionados, conforme cada obrigação aplicável."
        ),
    },
    "iss": {
        "aliases": ["iss", "issqn", "imposto sobre servicos", "imposto sobre serviços"],
        "title": "ISS / ISSQN",
        "definition": (
            "ISS, também chamado ISSQN, é o Imposto Sobre Serviços de Qualquer Natureza. Em regra, é de competência municipal e "
            "incide sobre serviços previstos na legislação aplicável."
        ),
    },
}


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().strip().split())


def _mentioned_entries(message: str) -> list[dict]:
    normalized = _normalize(message)
    matches: list[dict] = []
    for item in FISCAL_GLOSSARY.values():
        if any(re.search(rf"\b{re.escape(_normalize(alias))}\b", normalized) for alias in item["aliases"]):
            matches.append(item)
    return matches


def trusted_fiscal_context(message: str) -> str:
    """Retorna referências curtas e estáveis para reduzir alucinações em conceitos fiscais básicos."""
    entries = _mentioned_entries(message)
    if not entries:
        return ""
    lines = ["REFERÊNCIAS FISCAIS CURADAS DA GAZARRA (use estas definições; não invente expansões de siglas):"]
    lines.extend(f"- {entry['title']}: {entry['definition']}" for entry in entries)
    lines.append(
        "Para aplicação jurídica/tributária concreta, considere regime, operação, ente competente e legislação vigente; "
        "não conclua além dos dados disponíveis."
    )
    return "\n".join(lines)


def direct_definition_answer(message: str) -> Optional[str]:
    """Responde definições fiscais básicas sem depender do modelo local."""
    normalized = _normalize(message)
    definition_signal = any(
        signal in normalized
        for signal in (
            "o que e ",
            "oque e ",
            "o que significa ",
            "qual o significado",
            "explique ",
            "me explique ",
            "defina ",
        )
    )
    if not definition_signal:
        return None

    # Não intercepta consultas de dados concretos; essas devem seguir tools/contexto.
    data_signal = any(
        signal in normalized
        for signal in (
            "empresa ", "cliente ", "competencia", "quanto", "qual foi", "valor",
            "maio", "abril", "marco", "fevereiro", "janeiro", "junho", "julho",
            "agosto", "setembro", "outubro", "novembro", "dezembro",
        )
    )
    if data_signal:
        return None

    entries = _mentioned_entries(message)
    if len(entries) != 1:
        return None

    entry = entries[0]
    return (
        f"**{entry['title']}**\n\n"
        f"{entry['definition']}\n\n"
        "Se você quiser, eu também posso explicar com um exemplo prático ou relacionar o conceito aos dados de uma empresa da GAZARRA."
    )
