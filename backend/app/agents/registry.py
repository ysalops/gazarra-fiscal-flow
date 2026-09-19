from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


SPECS_DIR = Path(__file__).resolve().parent / "specs"


@dataclass(frozen=True)
class AgentSpec:
    name: str
    title: str
    category: str
    version: str
    status: str
    permissions: List[str]
    path: str
    content: str


def _parse_frontmatter(content: str) -> dict:
    lines = content.splitlines()

    if not lines or lines[0].strip() != "---":
        return {}

    metadata = {}

    for line in lines[1:]:
        stripped = line.strip()

        if stripped == "---":
            break

        if ":" not in stripped:
            continue

        key, value = stripped.split(":", 1)
        metadata[key.strip()] = value.strip()

    return metadata


def _extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()

        if stripped.startswith("# "):
            return stripped[2:].strip()

    return fallback


def _category_from_path(path: Path) -> str:
    parent = path.parent.name

    mapping = {
        "Fiscal_Flow": "Fiscal Flow",
        "GAZARRA_Agentes_Reconstruidos_v1": "Fiscal",
        "GAZARRA_Agentes_Reconstruidos_v2": "Trabalhista e Obrigações",
        "GAZARRA_Reforma_Tributaria_v2": "Reforma Tributária",
    }

    return mapping.get(parent, parent.replace("_", " "))


def load_agent_registry() -> Dict[str, AgentSpec]:
    registry: Dict[str, AgentSpec] = {}

    if not SPECS_DIR.exists():
        return registry

    for path in sorted(SPECS_DIR.rglob("*.md")):
        content = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        metadata = _parse_frontmatter(content)
        name = metadata.get("name", "").strip()

        # README, changelog e arquivos de fontes não são agentes executáveis.
        if not name:
            continue

        permissions = [
            item.strip()
            for item in metadata.get(
                "permissions",
                "read, report",
            ).split(",")
            if item.strip()
        ]

        spec = AgentSpec(
            name=name,
            title=_extract_title(content, name),
            category=_category_from_path(path),
            version=metadata.get("version", "1.0"),
            status=metadata.get("status", "homologacao"),
            permissions=permissions,
            path=str(path.relative_to(SPECS_DIR)),
            content=content,
        )

        # Em caso de versão repetida, a última pasta em ordem alfabética vence.
        # Isso faz a pasta GAZARRA_Reforma_Tributaria_v2 prevalecer sobre a v1.
        registry[name] = spec

    return registry


_AGENT_REGISTRY = load_agent_registry()


def get_agent_registry() -> Dict[str, AgentSpec]:
    return _AGENT_REGISTRY


def get_agent(name: str) -> Optional[AgentSpec]:
    return _AGENT_REGISTRY.get(name)


def list_agents() -> List[AgentSpec]:
    return sorted(
        _AGENT_REGISTRY.values(),
        key=lambda item: (
            item.category,
            item.title,
        ),
    )
