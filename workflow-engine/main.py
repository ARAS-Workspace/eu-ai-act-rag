# SPDX-License-Identifier: MIT
"""
█████╗ ██████╗  █████╗ ███████╗
██╔══██╗██╔══██╗██╔══██╗██╔════╝
███████║██████╔╝███████║███████╗
██╔══██║██╔══██╗██╔══██║╚════██║
██║  ██║██║  ██║██║  ██║███████║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
Copyright (C) 2026 Riza Emre ARAS <r.emrearas@proton.me>

Licensed under the MIT License.
See LICENSE and THIRD_PARTY_LICENSES for details.

EU AI Act RAG — Workflow Engine

Konfigurasyon odakli corpus olusturucu motoru.
YAML workflow tanimini okur, SPARQL ile EUR-Lex/Cellar'dan
Formex XML indirir, ayristirip Markdown corpus dosyalarina donusturur.

Pipeline: SPARQL -> Fetch -> Parse -> Convert (Postprocess)

---

Config-driven corpus builder engine.
Reads a YAML workflow definition, fetches Formex XML from EUR-Lex/Cellar
via SPARQL, parses it, and converts to Markdown corpus files.

Pipeline: SPARQL -> Fetch -> Parse -> Convert (Postprocess)

Usage: python main.py --workflow=../workflows/eu-ai-act.yaml
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.config import load_config
from src.logger import get_logger
from src.pipeline import run_pipeline

log = get_logger("main")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="corpus-builder",
        description="Execute a YAML workflow: SPARQL → XML → Markdown corpus",
    )
    parser.add_argument(
        "--workflow",
        type=Path,
        required=True,
        help="Path to workflow YAML (e.g. ../workflows/eu-ai-act.yaml)",
    )
    args = parser.parse_args()

    workflow = args.workflow.resolve()
    if not workflow.exists():
        log.error("Workflow file not found: %s", workflow)
        return 1

    cfg_result = load_config(workflow)
    if not cfg_result.ok:
        log.error(cfg_result.error)
        return 1

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = workflow.stem
    output_dir = (Path("dist") / f"{stem}-{stamp}" / "corpus").resolve()

    log.info("Workflow: %s", workflow.name)
    log.info("Output: %s", output_dir)

    result = run_pipeline(cfg_result.data, output_dir=output_dir)
    if not result.ok:
        log.error("Pipeline failed: %s", result.error)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())