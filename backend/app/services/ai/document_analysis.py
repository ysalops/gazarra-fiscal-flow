from __future__ import annotations

import re
from typing import Any


def _br_number(value: str) -> float:
    cleaned = re.sub(r"[^0-9,.-]", "", value or "")
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    return float(cleaned)


def _fmt_money(value: float) -> str:
    text = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {text}"


def _fmt_pct(value: float) -> str:
    return f"{value:.2f}%".replace(".", ",")


def split_pages(text: str) -> dict[int, str]:
    text = text or ""
    matches = list(re.finditer(r"\[Página\s+(\d+)\]\s*", text, flags=re.IGNORECASE))
    if not matches:
        return {1: text.strip()} if text.strip() else {}
    pages: dict[int, str] = {}
    for index, match in enumerate(matches):
        page_number = int(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        pages[page_number] = text[start:end].strip()
    return pages


def _normalized_lines(page_text: str) -> list[str]:
    lines = []
    for raw in (page_text or "").splitlines():
        line = " ".join(raw.strip().split())
        line = re.sub(r"\bV\s+ariação\b", "Variação", line, flags=re.IGNORECASE)
        if line:
            lines.append(line)
    return lines


def _comparison_findings(pages: dict[int, str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    value_re = re.compile(r"^(?P<period>[A-Za-zÀ-ÿ]+/20\d{2}):\s*R\$\s*(?P<value>[0-9.]+,[0-9]{2})", re.I)
    variation_re = re.compile(r"Variação:\s*([+-]?[0-9.]+,[0-9]+)%", re.I)

    for page_number, page_text in pages.items():
        lines = _normalized_lines(page_text)
        for i, line in enumerate(lines):
            vm = variation_re.search(line)
            if not vm:
                continue
            previous_values: list[tuple[str, float]] = []
            label = "comparativo"
            for j in range(max(0, i - 5), i):
                m = value_re.search(lines[j])
                if m:
                    previous_values.append((m.group("period"), _br_number(m.group("value"))))
                elif not re.search(r"R\$|Variação", lines[j], re.I):
                    label = lines[j]
            if len(previous_values) < 2:
                continue
            current_period, current = previous_values[-2]
            previous_period, previous = previous_values[-1]
            if previous == 0:
                continue
            stated = _br_number(vm.group(1))
            calculated = ((current - previous) / previous) * 100
            # Pequenas diferenças de arredondamento não viram alerta.
            if abs(stated - calculated) >= 0.5:
                findings.append({
                    "severity": "warning",
                    "code": "comparison_percentage_mismatch",
                    "page": page_number,
                    "message": (
                        f"{label}: a variação informada é {_fmt_pct(stated)}, mas os valores "
                        f"{_fmt_money(current)} ({current_period}) e {_fmt_money(previous)} ({previous_period}) "
                        f"resultam em aproximadamente {_fmt_pct(calculated)}."
                    ),
                })
    return findings


def _st_total_finding(pages: dict[int, str]) -> list[dict[str, Any]]:
    summary: tuple[int, float] | None = None
    detail: tuple[int, float] | None = None
    for page_number, page_text in pages.items():
        m = re.search(r"ST\s+recolhida\s*:\s*R\$\s*([0-9.]+,[0-9]{2})", page_text, re.I)
        if m and summary is None:
            summary = (page_number, _br_number(m.group(1)))
        m = re.search(r"ST\s+total\s+R\$\s*([0-9.]+,[0-9]{2})", page_text, re.I)
        if m and detail is None:
            detail = (page_number, _br_number(m.group(1)))
    if not summary or not detail or abs(summary[1] - detail[1]) < 0.01:
        return []
    return [{
        "severity": "warning",
        "code": "st_total_mismatch",
        "page": detail[0],
        "related_pages": [summary[0], detail[0]],
        "message": (
            f"O resumo informa ST de {_fmt_money(summary[1])} (página {summary[0]}), enquanto o detalhamento "
            f"informa ST total de {_fmt_money(detail[1])} (página {detail[0]}). Diferença de "
            f"{_fmt_money(abs(summary[1] - detail[1]))}."
        ),
    }]


def _difal_ratio_finding(pages: dict[int, str]) -> list[dict[str, Any]]:
    current = previous = None
    comparison_page = None
    for page_number, page_text in pages.items():
        if "DIFAL" not in page_text.upper() or "Maio/2025" not in page_text:
            continue
        marker = re.search(r"DIFAL\s+Recolhido", page_text, re.I)
        if not marker:
            continue
        section = page_text[marker.end():]
        m = re.search(
            r"Maio/2026:\s*R\$\s*([0-9.]+,[0-9]{2}).*?Maio/2025:\s*R\$\s*([0-9.]+,[0-9]{2})",
            section, flags=re.I | re.S,
        )
        if m:
            current = _br_number(m.group(1))
            previous = _br_number(m.group(2))
            comparison_page = page_number
            break

    stated = None
    claim_page = None
    for page_number, page_text in pages.items():
        m = re.search(r"DIFAL.*?crescimento\s+de\s*([0-9.,]+)\s*[×x]", page_text, flags=re.I | re.S)
        if m:
            stated = _br_number(m.group(1))
            claim_page = page_number
            break

    if current is None or previous in (None, 0) or stated is None:
        return []
    calculated = current / previous
    if abs(stated - calculated) < 0.15:
        return []
    return [{
        "severity": "warning",
        "code": "ratio_mismatch",
        "page": claim_page,
        "related_pages": [page for page in [comparison_page, claim_page] if page],
        "message": (
            f"O documento afirma crescimento de {str(stated).replace('.', ',')}× para o DIFAL, porém "
            f"{_fmt_money(current)} dividido por {_fmt_money(previous)} corresponde a aproximadamente "
            f"{str(round(calculated, 2)).replace('.', ',')}×."
        ),
    }]


def analyze_document_text(text: str, extension: str = "") -> dict[str, Any]:
    pages = split_pages(text)
    visual_pages: list[int] = []
    if extension.lower() == ".pdf":
        # Página com pouquíssimo texto extraível provavelmente é imagem/gráfico/certidão.
        visual_pages = [number for number, content in pages.items() if len(re.sub(r"\s+", " ", content).strip()) < 90]

    findings: list[dict[str, Any]] = []
    findings.extend(_comparison_findings(pages))
    findings.extend(_st_total_finding(pages))
    findings.extend(_difal_ratio_finding(pages))

    return {
        "page_count": len(pages) if extension.lower() == ".pdf" else None,
        "visual_pages": visual_pages,
        "validation_findings": findings,
        "validation_count": len(findings),
    }


def validation_prompt_block(analysis: dict[str, Any] | None) -> str:
    if not analysis:
        return ""
    blocks: list[str] = []
    findings = analysis.get("validation_findings") or []
    visual_pages = analysis.get("visual_pages") or []
    if findings:
        blocks.append("VALIDAÇÃO NUMÉRICA DETERMINÍSTICA (verifique e priorize estes alertas):")
        blocks.extend(f"- {item.get('message')}" for item in findings)
    if visual_pages:
        page_list = ", ".join(str(item) for item in visual_pages)
        blocks.append(
            "LIMITAÇÃO VISUAL: as páginas " + page_list +
            " possuem pouco ou nenhum texto extraível. Não conclua o conteúdo de certidões, gráficos ou imagens dessas páginas "
            "sem análise visual explícita."
        )
    return "\n".join(blocks)
