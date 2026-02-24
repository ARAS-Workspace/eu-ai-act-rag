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

"""Pipeline orchestrator — pure engine.

Executes workflow steps defined in PipelineConfig:
  1. SPARQL steps: render template → query → run script → store in context
  2. Fetch: run URI selection script → download ZIP → extract to temp dir
  3. Parse: extract articles, recitals, annexes from Formex XML
  4. Convert: write markdown corpus with postprocess normalization

Temp dir is created at start and cleaned up when pipeline finishes.
No domain logic. All decisions come from data.yaml.
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import PipelineConfig
from src.converter import convert_document
from src.fetcher import fetch_document
from src.logger import PipelineSummary, get_logger
from src.parser import parse_document
from src.result import Fail, Ok, Result
from src.sparql.client import execute_query
from src.sparql.processor import execute_script
from src.sparql.queries import render_step

log = get_logger(__name__)


def _source_dict(config: PipelineConfig) -> dict[str, str]:
    """Flatten source config to a plain dict for script scope."""
    return asdict(config.source)


def _run_sparql(config: PipelineConfig, summary: PipelineSummary) -> Result[dict[str, Any]]:
    """Execute all SPARQL workflow steps, building up context."""
    context: dict[str, Any] = {}
    source = _source_dict(config)
    counter = summary.counter("sparql")

    for step in config.sparql.steps:
        log.info("── SPARQL step: %s ──", step.name)

        query = render_step(step, config)

        query_result = execute_query(
            endpoint=config.sparql.endpoint,
            query=query,
            timeout=config.sparql.timeout,
        )
        if not query_result.ok:
            log.warning("Step '%s' query failed: %s", step.name, query_result.error)
            counter.failed += 1
            if step.required:
                return Fail(error=f"Required step '{step.name}' failed: {query_result.error}")
            continue

        script_result = execute_script(
            script=step.script,
            bindings=query_result.data,
            context=context,
            source=source,
            step_name=step.name,
        )
        if not script_result.ok:
            log.warning("Step '%s' script failed: %s", step.name, script_result.error)
            counter.failed += 1
            if step.required:
                return Fail(error=f"Required step '{step.name}' script failed: {script_result.error}")
            continue

        context[step.name] = script_result.data
        counter.ok += 1
        log.info("Step '%s' complete", step.name)

    return Ok(data=context)


def _run_fetch(
    config: PipelineConfig,
    context: dict[str, Any],
    tmp_dir: Path,
    summary: PipelineSummary,
) -> Result[Path]:
    """Execute the fetch workflow step."""
    counter = summary.counter("fetch")
    source = _source_dict(config)

    result = fetch_document(config.fetch, context, source, tmp_dir)
    if result.ok:
        counter.ok += 1
    else:
        counter.failed += 1
    return result


def run_pipeline(config: PipelineConfig, output_dir: Path) -> Result[dict[str, Any]]:
    """Run the full workflow: sparql → fetch → parse → convert.

    Args:
        config: Loaded pipeline configuration from data.yaml.
        output_dir: Absolute path where corpus files will be written.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary = PipelineSummary()

    # 1. SPARQL
    sparql_result = _run_sparql(config, summary)
    if not sparql_result.ok:
        log.error("SPARQL phase failed: %s", sparql_result.error)
        log.info(summary.report())
        return sparql_result  # type: ignore[return-value]

    context = sparql_result.data
    context["_timestamp"] = timestamp
    context["_source"] = _source_dict(config)

    # Temp dir for fetch + parse (cleaned up after convert)
    tmp_dir = Path(tempfile.mkdtemp(prefix="corpus-builder-"))
    log.info("Temp dir: %s", tmp_dir)

    try:
        # 2. Fetch
        fetch_result = _run_fetch(config, context, tmp_dir, summary)
        if not fetch_result.ok:
            log.error("Fetch phase failed: %s", fetch_result.error)
            log.info(summary.report())
            return fetch_result  # type: ignore[return-value]

        source_dir: Path = fetch_result.data

        # 3. Parse
        parse_result = parse_document(source_dir)
        if not parse_result.ok:
            log.error("Parse failed: %s", parse_result.error)
            log.info(summary.report())
            return parse_result  # type: ignore[return-value]

        # 4. Convert (with postprocess normalization)
        convert_result = convert_document(
            doc=parse_result.data,
            config=config.corpus,
            postprocess=config.postprocess,
            context=context,
            output_dir=output_dir,
            summary=summary,
        )
        if not convert_result.ok:
            log.error("Convert failed: %s", convert_result.error)

        log.info(summary.report())
        return Ok(data=context)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        log.info("Cleaned up temp dir: %s", tmp_dir)