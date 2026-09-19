import re
import unicodedata
from difflib import SequenceMatcher

from app.schemas.product import (
    SupplierProduct,
    CandidateProduct,
    MatchSuggestion,
)


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        ch for ch in value
        if not unicodedata.combining(ch)
    )

    value = re.sub(
        r"[^A-Za-z0-9 ]+",
        " ",
        value,
    ).lower()

    return " ".join(value.split())


def text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(
        None,
        normalize_text(a),
        normalize_text(b),
    ).ratio()


def score_candidate(
    source: SupplierProduct,
    target: CandidateProduct,
) -> tuple[float, list[str]]:

    score = 0.0
    reasons = []

    if (
        source.gtin
        and target.gtin
        and source.gtin == target.gtin
    ):
        score += 0.70
        reasons.append("GTIN/EAN exato")

    if (
        source.ncm
        and target.ncm
        and source.ncm == target.ncm
    ):
        score += 0.15
        reasons.append("NCM igual")

    if (
        source.unit
        and target.unit
        and normalize_text(source.unit)
        == normalize_text(target.unit)
    ):
        score += 0.05
        reasons.append("Unidade igual")

    similarity = text_similarity(
        source.description,
        target.description,
    )

    score += min(
        similarity * 0.20,
        0.20,
    )

    if similarity >= 0.75:
        reasons.append(
            f"Descrição semelhante ({similarity:.0%})"
        )

    return min(score, 1.0), reasons


def suggest_match(
    source: SupplierProduct,
    candidates: list[CandidateProduct],
) -> MatchSuggestion:

    if not candidates:
        return MatchSuggestion(
            internal_code=None,
            confidence=0,
            status="blocked",
            reasons=[
                "Nenhum produto interno disponível para comparação"
            ],
        )

    scored = []

    for candidate in candidates:
        score, reasons = score_candidate(
            source,
            candidate,
        )

        scored.append(
            (
                score,
                candidate,
                reasons,
            )
        )

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    best_score, best_candidate, reasons = scored[0]

    if best_score >= 0.90:
        status = "auto_candidate"
    elif best_score >= 0.70:
        status = "review"
    else:
        status = "blocked"

    return MatchSuggestion(
        internal_code=best_candidate.internal_code,
        confidence=round(best_score, 4),
        status=status,
        reasons=(
            reasons
            or ["Sem critérios fortes de correspondência"]
        ),
    )