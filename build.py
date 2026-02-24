#!/usr/bin/env python3
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
"""Build corpus from data.yaml workflow definition.

Usage:
    python build.py
    python build.py --output dist/corpus
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Engine lives in workflow-engine/
_ENGINE_DIR = Path(__file__).resolve().parent / "workflow-engine"
sys.path.insert(0, str(_ENGINE_DIR))

from src.config import load_config
from src.logger import get_logger
from src.pipeline import run_pipeline

log = get_logger("build")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="build",
        description="Build markdown corpus from workflow definition",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dist/corpus"),
        help="Output directory for corpus files (default: dist/corpus)",
    )
    args = parser.parse_args()

    workflow = Path(__file__).resolve().parent / "data.yaml"

    cfg_result = load_config(workflow)
    if not cfg_result.ok:
        log.error(cfg_result.error)
        return 1

    output_dir = args.output.resolve()
    log.info("Output: %s", output_dir)

    result = run_pipeline(cfg_result.data, output_dir=output_dir)
    if not result.ok:
        log.error("Pipeline failed: %s", result.error)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())