from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

from app.agents.registry import AgentSpec, get_agent, list_agents
from app.core.config import settings


CACHE_PATH = Path("/app/data/agent_catalog.json")
CRITICAL_AGENT_NAMES = {
    "integracao-dominio-gazarra",
    "auditoria-pos-importacao-gazarra",
    "apuracao-preliminar-gazarra",
    "revisao-sped-gazarra",
    "conferencia-guias-gazarra",
}


def _spec_hash(agent: AgentSpec) -> str:
    return hashlib.sha256(agent.content.encode("utf-8", errors="replace")).hexdigest()[:20]


def _strip_frontmatter(content: str) -> str:
    if not content.startswith("---"):
        return content
    parts = content.split("---", 2)
    return parts[2].strip() if len(parts) >= 3 else content


def _first_useful_paragraph(agent: AgentSpec) -> str:
    content = _strip_frontmatter(agent.content)
    sections = re.split(r"\n#{1,4}\s+", content)
    candidates: list[str] = []
    for section in sections:
        cleaned = re.sub(r"```.*?```", "", section, flags=re.S)
        cleaned = re.sub(r"\|[^\n]+\|", "", cleaned)
        paragraphs = [" ".join(p.split()) for p in re.split(r"\n\s*\n", cleaned) if p.strip()]
        for paragraph in paragraphs:
            paragraph = re.sub(r"^[#*\-\d.\s]+", "", paragraph).strip()
            if len(paragraph) >= 55 and not paragraph.lower().startswith(("name:", "version:", "status:")):
                candidates.append(paragraph)
    if candidates:
        value = candidates[0]
        return value[:320] + ("…" if len(value) > 320 else "")
    return f"Agente especializado em {agent.category.lower()}, baseado na especificação interna da GAZARRA."


def _fallback_capabilities(agent: AgentSpec) -> list[str]:
    mapping = {
        "read": "Leitura e consulta",
        "research": "Pesquisa orientada",
        "report": "Relatórios e síntese",
        "compare": "Comparação e conferência",
        "calculate": "Cálculos preliminares",
        "ingest": "Captura documental",
        "integrate": "Integração de sistemas",
        "prepare": "Preparação de dados",
        "summarize": "Resumo de exceções",
        "audit": "Auditoria",
        "propose": "Propostas e recomendações",
        "orchestrate": "Orquestração de fluxo",
        "validate": "Validação",
    }
    result = [mapping.get(item, item.replace("_", " ").title()) for item in agent.permissions]
    return list(dict.fromkeys(result))[:5]


def _recommended_for(agent: AgentSpec) -> list[str]:
    title = agent.title.lower()
    suggestions: list[str] = []
    keyword_map = [
        ("sped", "SPED / EFD e divergências de escrituração"),
        ("product", "De/Para, GTIN, NCM e cadastro de produtos"),
        ("produto", "Cadastro e tratamento tributário de produtos"),
        ("reforma", "CBS, IBS, ISSQN e reforma tributária"),
        ("guia", "Conferência de guias, valores e vencimentos"),
        ("domínio", "Integração e preparação para o Domínio"),
        ("completude", "Documentos faltantes e completude do fechamento"),
        ("auditoria", "Divergências e auditoria pós-importação"),
        ("apuração", "Apuração preliminar e memória de cálculo"),
        ("fiscal", "Fechamento, tributos e inconsistências fiscais"),
        ("dctf", "DCTFWeb e MIT"),
        ("reinf", "EFD-Reinf"),
        ("esocial", "eSocial"),
        ("folha", "Folha de pagamento"),
        ("admiss", "Admissões"),
        ("rescis", "Rescisões"),
        ("férias", "Férias e 13º salário"),
        ("fgts", "FGTS Digital"),
        ("inss", "INSS"),
        ("irrf", "IRRF da folha"),
    ]
    for needle, label in keyword_map:
        if needle in title and label not in suggestions:
            suggestions.append(label)
    if not suggestions:
        suggestions.append(agent.category)
    return suggestions[:4]


def fallback_catalog_item(agent: AgentSpec) -> dict[str, Any]:
    return {
        "name": agent.name,
        "title": agent.title,
        "category": agent.category,
        "version": agent.version,
        "status": agent.status,
        "permissions": agent.permissions,
        "summary": _first_useful_paragraph(agent),
        "capabilities": _fallback_capabilities(agent),
        "recommended_for": _recommended_for(agent),
        "human_review": agent.name in CRITICAL_AGENT_NAMES,
        "summary_source": "spec",
        "spec_hash": _spec_hash(agent),
    }


def _load_cache() -> dict[str, Any]:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(cache: dict[str, Any]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def get_catalog_item(agent: AgentSpec) -> dict[str, Any]:
    cache = _load_cache()
    cached = cache.get(agent.name)
    if cached and cached.get("spec_hash") == _spec_hash(agent):
        base = fallback_catalog_item(agent)
        base.update(cached)
        return base
    return fallback_catalog_item(agent)


def list_catalog_items() -> list[dict[str, Any]]:
    return [get_catalog_item(agent) for agent in list_agents()]


def _extract_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I | re.S)
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start:end + 1])
    return json.loads(text)


def refresh_catalog_item(agent_name: str) -> dict[str, Any]:
    agent = get_agent(agent_name)
    if agent is None:
        raise KeyError(agent_name)
    fallback = fallback_catalog_item(agent)
    from app.services.llm.router import get_llm_provider
    provider = get_llm_provider()
    if provider is None:
        return fallback

    system_prompt = (
        "Você cataloga agentes internos de software. Leia a especificação fornecida e produza somente JSON válido, "
        "sem markdown. Não invente capacidades ausentes. Seja objetivo e use português do Brasil."
    )
    user_prompt = f"""
ESPECIFICAÇÃO DO AGENTE
---
{agent.content}
---

Retorne exatamente um objeto JSON com:
- summary: 1 ou 2 frases explicando o que o agente faz;
- capabilities: lista de 2 a 5 capacidades concretas;
- recommended_for: lista de 2 a 4 situações em que deve ser escolhido;
- human_review: boolean, verdadeiro quando decisões/ações do agente exigirem validação humana.
""".strip()

    try:
        generated = _extract_json(provider.analyze(system_prompt, user_prompt))
        item = dict(fallback)
        if isinstance(generated.get("summary"), str) and generated["summary"].strip():
            item["summary"] = generated["summary"].strip()[:600]
        if isinstance(generated.get("capabilities"), list):
            item["capabilities"] = [str(x).strip() for x in generated["capabilities"] if str(x).strip()][:5]
        if isinstance(generated.get("recommended_for"), list):
            item["recommended_for"] = [str(x).strip() for x in generated["recommended_for"] if str(x).strip()][:4]
        if isinstance(generated.get("human_review"), bool):
            item["human_review"] = generated["human_review"]
        item["summary_source"] = settings.llm_provider.lower().strip() or "llm"
        item["spec_hash"] = _spec_hash(agent)
        cache = _load_cache()
        cache[agent.name] = item
        _save_cache(cache)
        return item
    except Exception:
        return fallback
