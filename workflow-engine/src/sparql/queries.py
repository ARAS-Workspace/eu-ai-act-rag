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
"""SPARQL query template renderer.

Replaces {{variable}} placeholders in templates with source config values.
Pure string interpolation — no SPARQL knowledge.
"""

from __future__ import annotations

from src.config import PipelineConfig, SparqlStep
from src.logger import get_logger

log = get_logger(__name__)


def render_template(template: str, variables: dict[str, str]) -> str:
    """Replace all {{key}} placeholders in template with variable values."""
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered


def get_template_variables(config: PipelineConfig) -> dict[str, str]:
    """Extract template variables from source config."""
    return {
        "celex": config.source.celex,
        "language": config.source.language,
        "language_code": config.source.language_code,
    }


def render_step(step: SparqlStep, config: PipelineConfig) -> str:
    """Render a step's SPARQL template with source variables."""
    variables = get_template_variables(config)
    rendered = render_template(step.template, variables)
    log.info("Rendered template for step '%s'", step.name)
    return rendered