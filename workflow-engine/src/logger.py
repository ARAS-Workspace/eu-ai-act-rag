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

"""Structured logger with per-step counters and final summary.

Collects success/fail counts per pipeline step so the orchestrator
can print a CI-friendly summary at the end.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field

_FMT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"


def get_logger(name: str) -> logging.Logger:
    """Return a stdlib logger configured with a consistent format."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(_FMT, datefmt="%H:%M:%S"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


@dataclass
class StepCounter:
    """Tracks success/fail counts for a single pipeline step."""

    name: str
    ok: int = 0
    failed: int = 0


@dataclass
class PipelineSummary:
    """Accumulates counters across all pipeline steps."""

    steps: dict[str, StepCounter] = field(default_factory=dict)

    def counter(self, name: str) -> StepCounter:
        """Get or create a counter for a named step."""
        if name not in self.steps:
            self.steps[name] = StepCounter(name=name)
        return self.steps[name]

    def report(self) -> str:
        """Format a human-readable summary block."""
        lines: list[str] = ["", "Pipeline Summary", "=" * 40]
        for step in self.steps.values():
            parts = [f"{step.name}: {step.ok} ok"]
            if step.failed:
                parts.append(f"{step.failed} failed")
            lines.append("  ".join(parts))
        lines.append("=" * 40)
        return "\n".join(lines)