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

"""Markdown converter — transforms parsed data into corpus files.

Generates YAML frontmatter + Markdown body from parsed Formex structures.
Templates come from data.yaml corpus config.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from src.config import CorpusConfig, PostprocessConfig, SectionDef
from src.logger import PipelineSummary, get_logger
from src.parser import Article, ParsedDocument
from src.result import Ok, Result

log = get_logger(__name__)


def _normalize(text: str, config: PostprocessConfig) -> str:
    """Apply postprocess normalization rules to text."""
    for rule in config.normalize:
        text = text.replace(rule.find, rule.replace)
    return text


def _resolve_template(template: str, values: dict[str, str]) -> str:
    """Replace {key} placeholders in a template string."""
    result = template
    for key, value in values.items():
        result = result.replace("{" + key + "}", value)
    return result


def _resolve_frontmatter_base(
    base: dict[str, Any],
    context: dict[str, Any],
    source: dict[str, str],
    timestamp: str,
) -> dict[str, Any]:
    """Resolve {{...}} placeholders in frontmatter_base."""
    def _resolve(obj: Any) -> Any:
        if isinstance(obj, str):
            result = obj
            result = result.replace("{{language_code}}", source.get("language_code", ""))
            result = result.replace("{{celex}}", source.get("celex", ""))
            result = result.replace("{{timestamp}}", timestamp)
            # context.metadata.work_uri pattern
            if "{{context." in result:
                for match in re.finditer(r"\{\{context\.(\w+)\.(\w+)}}", result):
                    step, key = match.group(1), match.group(2)
                    val = context.get(step, {}).get(key, "")
                    result = result.replace(match.group(0), str(val))
            return result
        if isinstance(obj, dict):
            return {k: _resolve(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_resolve(v) for v in obj]
        return obj

    return _resolve(base)


def _build_frontmatter(
    section: SectionDef,
    values: dict[str, str],
    base: dict[str, Any],
    cross_refs: list[dict[str, str]],
    eurovoc: list[str],
) -> str:
    """Build YAML frontmatter string."""
    fm: dict[str, Any] = {}

    # Section-specific fields
    for key, template in section.frontmatter.items():
        fm[key] = _resolve_template(template, values)

    # Base fields (source, language, etc.)
    fm.update(base)

    # Cross-references and EuroVoc
    if cross_refs:
        fm["cross_references"] = cross_refs
    if eurovoc:
        fm["eurovoc"] = eurovoc

    return yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)


def _article_to_markdown(article: Article) -> str:
    """Convert an Article to markdown body text."""
    lines: list[str] = []

    for para in article.paragraphs:
        lines.append(f"## {para.number}.")
        lines.append("")

        if para.text:
            lines.append(para.text)
            lines.append("")

        for item in para.items:
            prefix = f"({item.letter})" if item.letter else "-"
            lines.append(f"{prefix} {item.text}")
            lines.append("")

    return "\n".join(lines)


def convert_document(
    doc: ParsedDocument,
    config: CorpusConfig,
    postprocess: PostprocessConfig,
    context: dict[str, Any],
    output_dir: Path,
    summary: PipelineSummary,
) -> Result[dict[str, int]]:
    """Convert parsed document to markdown corpus files.

    Args:
        doc: Parsed Formex document with articles, recitals, annexes.
        config: Corpus output configuration from data.yaml.
        postprocess: Text normalization rules.
        context: Accumulated SPARQL context with metadata, cross-refs, eurovoc.
        output_dir: Root directory for corpus output (e.g. dist/corpus).
        summary: Pipeline summary for tracking success/fail counts.
    """
    source = context.get("_source", {})
    timestamp = context.get("_timestamp", "")
    cross_refs = context.get("cross_references", [])
    eurovoc = context.get("eurovoc", [])

    base_fm = _resolve_frontmatter_base(config.frontmatter_base, context, source, timestamp)

    stats: dict[str, int] = {"articles": 0, "recitals": 0, "annexes": 0}

    # Articles
    if "articles" in config.sections:
        sec = config.sections["articles"]
        out_dir = output_dir / sec.dir
        out_dir.mkdir(parents=True, exist_ok=True)
        counter = summary.counter("articles")

        for article in doc.articles:
            values = {
                "number": article.number,
                "title": article.title,
                "chapter": article.chapter,
                "chapter_title": article.chapter_title,
            }
            heading = _resolve_template(sec.heading, values)
            frontmatter = _build_frontmatter(sec, values, base_fm, cross_refs, eurovoc)
            body = _article_to_markdown(article)
            content = _normalize(
                f"---\n{frontmatter}---\n\n# {heading}\n\n{body}", postprocess,
            )

            filename = _resolve_template(sec.filename, values)
            (out_dir / filename).write_text(content, encoding="utf-8")
            counter.ok += 1
            stats["articles"] += 1

    # Recitals
    if "recitals" in config.sections:
        sec = config.sections["recitals"]
        out_dir = output_dir / sec.dir
        out_dir.mkdir(parents=True, exist_ok=True)
        counter = summary.counter("recitals")

        for recital in doc.recitals:
            values = {"number": recital.number}
            heading = _resolve_template(sec.heading, values)
            frontmatter = _build_frontmatter(sec, values, base_fm, cross_refs, eurovoc)
            content = _normalize(
                f"---\n{frontmatter}---\n\n# {heading}\n\n{recital.text}\n", postprocess,
            )

            filename = _resolve_template(sec.filename, values)
            (out_dir / filename).write_text(content, encoding="utf-8")
            counter.ok += 1
            stats["recitals"] += 1

    # Annexes
    if "annexes" in config.sections:
        sec = config.sections["annexes"]
        out_dir = output_dir / sec.dir
        out_dir.mkdir(parents=True, exist_ok=True)
        counter = summary.counter("annexes")

        for annex in doc.annexes:
            values = {"number": annex.number, "title": annex.title}
            heading = _resolve_template(sec.heading, values)
            frontmatter = _build_frontmatter(sec, values, base_fm, cross_refs, eurovoc)
            content = _normalize(
                f"---\n{frontmatter}---\n\n# {heading}\n\n{annex.content}\n", postprocess,
            )

            filename = _resolve_template(sec.filename, values)
            (out_dir / filename).write_text(content, encoding="utf-8")
            counter.ok += 1
            stats["annexes"] += 1

    log.info(
        "Converted: %d articles, %d recitals, %d annexes",
        stats["articles"], stats["recitals"], stats["annexes"],
    )
    return Ok(data=stats)