# SPDX-License-Identifier: MIT
#
#  █████╗ ██████╗  █████╗ ███████╗
# ██╔══██╗██╔══██╗██╔══██╗██╔════╝
# ███████║██████╔╝███████║███████╗
# ██╔══██║██╔══██╗██╔══██║╚════██║
# ██║  ██║██║  ██║██║  ██║███████║
# ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
# Copyright (C) 2026 Riza Emre ARAS <r.emrearas@proton.me>
#
# Licensed under the MIT License.
# See LICENSE and THIRD_PARTY_LICENSES for details.

"""Data quality validator — deterministic coverage checks.

Runs between parse and convert stages. Advisory mode only:
never blocks the pipeline, only logs warnings and generates a report.

Checks:
  1. Count validation — expected articles, recitals, annexes
  2. Empty content detection — items with no body text
  3. Sequential numbering — gaps in article numbers
  4. Structural integrity — missing title or chapter context
  5. Coverage ratio — parsed_len / source_len per item
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from lxml import etree

from src.config import ValidationConfig
from src.logger import PipelineSummary, get_logger
from src.parser import Annex, Article, ParsedDocument, Recital, _text
from src.result import Ok, Result

log = get_logger(__name__)


# ── Report Dataclasses ────────────────────────────────────────


@dataclass
class ItemValidation:
    """Validation result for a single article/recital/annex."""

    item_type: str
    item_id: str
    source_len: int
    parsed_len: int
    coverage_ratio: float
    warnings: list[str] = field(default_factory=list)


@dataclass
class DeterministicResult:
    """Results of all deterministic checks."""

    article_count: int
    recital_count: int
    annex_count: int
    expected_articles: int
    expected_recitals: int
    expected_annexes: int
    empty_items: list[str] = field(default_factory=list)
    numbering_gaps: list[str] = field(default_factory=list)
    missing_structure: list[str] = field(default_factory=list)
    low_coverage: list[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Complete validation report."""

    timestamp: str
    deterministic: DeterministicResult
    items: list[ItemValidation] = field(default_factory=list)
    total_pass: int = 0
    total_warn: int = 0
    total_fail: int = 0


# ── Source Text Extraction ────────────────────────────────────


def _build_source_text_map(source_dir: Path) -> dict[str, str]:
    """Re-parse XML files to extract raw text per element.

    Returns a dict keyed by ``"article:1"``, ``"recital:45"``, ``"annex:III"``.
    """
    source_map: dict[str, str] = {}

    act_files = sorted(source_dir.glob("*.000101.fmx.xml"))
    if not act_files:
        return source_map

    try:
        tree = etree.parse(str(act_files[0]))  # noqa: S320
    except etree.XMLSyntaxError:
        return source_map

    root = tree.getroot()

    for art_el in root.iter("ARTICLE"):
        number = _text(art_el.find("TI.ART")).replace("Article", "").strip()
        source_map[f"article:{number}"] = _text(art_el)

    for consid in root.iter("CONSID"):
        np = consid.find("NP")
        if np is None:
            continue
        number = _text(np.find("NO.P")).strip("()")
        source_map[f"recital:{number}"] = _text(consid)

    annex_files = sorted(
        f
        for f in source_dir.glob("*.fmx.xml")
        if ".toc." not in f.name
        and ".doc." not in f.name
        and ".000101." not in f.name
    )
    for annex_path in annex_files:
        try:
            atree = etree.parse(str(annex_path))  # noqa: S320
        except etree.XMLSyntaxError:
            continue
        aroot = atree.getroot()
        ti = _text(aroot.find("TITLE/TI"))
        number = ti.replace("ANNEX", "").strip() if "ANNEX" in ti else ti
        source_map[f"annex:{number}"] = _text(aroot)

    return source_map


# ── Parsed Text Helpers ───────────────────────────────────────


def _get_parsed_text(item: Article | Recital | Annex) -> str:
    """Extract the full text content from a parsed item."""
    if isinstance(item, Article):
        parts: list[str] = []
        for p in item.paragraphs:
            if p.text:
                parts.append(p.text)
        return "\n".join(parts)
    if isinstance(item, Recital):
        return item.text
    if isinstance(item, Annex):
        return item.content
    return ""


# ── Deterministic Checks ─────────────────────────────────────


def _check_sequential_numbering(articles: list[Article]) -> list[str]:
    """Check for gaps in article numbering."""
    gaps: list[str] = []
    numbers: list[int] = []
    for a in articles:
        try:
            numbers.append(int(a.number))
        except ValueError:
            continue
    numbers.sort()
    for i in range(1, len(numbers)):
        if numbers[i] != numbers[i - 1] + 1:
            gaps.append(f"article: gap between {numbers[i - 1]} and {numbers[i]}")
    return gaps


def _check_structural_integrity(articles: list[Article]) -> list[str]:
    """Check that all articles have title and chapter context."""
    issues: list[str] = []
    for a in articles:
        if not a.title:
            issues.append(f"article:{a.number} missing title")
        if not a.chapter:
            issues.append(f"article:{a.number} missing chapter context")
    return issues


def _run_deterministic(
    doc: ParsedDocument,
    source_map: dict[str, str],
    config: ValidationConfig,
) -> tuple[DeterministicResult, list[ItemValidation]]:
    """Run all deterministic validation checks."""
    empty_items: list[str] = []
    low_coverage: list[str] = []
    items: list[ItemValidation] = []

    all_parsed: list[tuple[str, str, Article | Recital | Annex]] = []
    for a in doc.articles:
        all_parsed.append(("article", a.number, a))
    for r in doc.recitals:
        all_parsed.append(("recital", r.number, r))
    for x in doc.annexes:
        all_parsed.append(("annex", x.number, x))

    for item_type, item_id, item in all_parsed:
        parsed_text = _get_parsed_text(item)
        source_key = f"{item_type}:{item_id}"
        source_text = source_map.get(source_key, "")
        source_len = len(source_text)
        parsed_len = len(parsed_text)

        if not parsed_text.strip():
            empty_items.append(source_key)

        ratio = (
            parsed_len / source_len
            if source_len > 0
            else (1.0 if parsed_len == 0 else 0.0)
        )
        warnings: list[str] = []
        if ratio < config.coverage_ratio_threshold:
            low_coverage.append(f"{source_key} ratio={ratio:.2f}")
            warnings.append(f"Low coverage ratio: {ratio:.2f}")

        items.append(
            ItemValidation(
                item_type=item_type,
                item_id=item_id,
                source_len=source_len,
                parsed_len=parsed_len,
                coverage_ratio=round(ratio, 4),
                warnings=warnings,
            )
        )

    det = DeterministicResult(
        article_count=len(doc.articles),
        recital_count=len(doc.recitals),
        annex_count=len(doc.annexes),
        expected_articles=config.expected_articles,
        expected_recitals=config.expected_recitals,
        expected_annexes=config.expected_annexes,
        empty_items=empty_items,
        numbering_gaps=_check_sequential_numbering(doc.articles),
        missing_structure=_check_structural_integrity(doc.articles),
        low_coverage=low_coverage,
    )

    return det, items


# ── Report ────────────────────────────────────────────────────


def _tally(
    det: DeterministicResult,
) -> tuple[int, int, int]:
    """Count pass/warn/fail across all checks."""
    total_pass = 0
    total_warn = 0
    total_fail = 0

    for _label, actual, expected in [
        ("articles", det.article_count, det.expected_articles),
        ("recitals", det.recital_count, det.expected_recitals),
        ("annexes", det.annex_count, det.expected_annexes),
    ]:
        if actual == expected:
            total_pass += 1
        else:
            total_fail += 1

    total_fail += len(det.empty_items)
    total_warn += len(det.numbering_gaps)
    total_warn += len(det.missing_structure)
    total_warn += len(det.low_coverage)

    return total_pass, total_warn, total_fail


def _save_report(report: ValidationReport, output_dir: Path) -> Path:
    """Save validation report as JSON alongside the corpus directory."""
    report_path = output_dir.parent / "validation-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(asdict(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return report_path


def _log_summary(report: ValidationReport) -> None:
    """Log a human-readable validation summary."""
    det = report.deterministic
    log.info("Validation Summary")
    log.info("=" * 40)
    log.info("  Articles: %d/%d", det.article_count, det.expected_articles)
    log.info("  Recitals: %d/%d", det.recital_count, det.expected_recitals)
    log.info("  Annexes:  %d/%d", det.annex_count, det.expected_annexes)

    if det.empty_items:
        log.warning("  Empty items: %s", ", ".join(det.empty_items))
    if det.numbering_gaps:
        log.warning("  Numbering gaps: %s", ", ".join(det.numbering_gaps))
    if det.missing_structure:
        log.warning("  Missing structure: %s", ", ".join(det.missing_structure))
    if det.low_coverage:
        log.warning("  Low coverage: %s", ", ".join(det.low_coverage))

    log.info(
        "  Result: %d pass, %d warn, %d fail",
        report.total_pass,
        report.total_warn,
        report.total_fail,
    )
    log.info("=" * 40)


# ── Main Entry Point ─────────────────────────────────────────


def validate_document(
    doc: ParsedDocument,
    source_dir: Path,
    config: ValidationConfig,
    output_dir: Path,
    summary: PipelineSummary,
    timestamp: str,
) -> Result[ValidationReport]:
    """Run all validation checks. Always returns Ok (advisory mode)."""
    counter = summary.counter("validation")
    log.info("── Validation ──")

    source_map = _build_source_text_map(source_dir)
    log.info("Extracted source text for %d elements", len(source_map))

    det, items = _run_deterministic(doc, source_map, config)

    total_pass, total_warn, total_fail = _tally(det)

    report = ValidationReport(
        timestamp=timestamp,
        deterministic=det,
        items=items,
        total_pass=total_pass,
        total_warn=total_warn,
        total_fail=total_fail,
    )

    report_path = _save_report(report, output_dir)
    log.info("Validation report: %s", report_path)
    _log_summary(report)

    counter.ok = total_pass
    counter.failed = total_fail

    return Ok(data=report)
