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

"""Loads data.yaml workflow definition into typed dataclasses.

Pure loader — no domain logic. YAML structure IS the workflow contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from src.result import Fail, Ok, Result


# ── SPARQL ─────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class SparqlStep:
    """One workflow step: SPARQL template + processing script."""
    name: str
    description: str
    template: str
    script: str


@dataclass(frozen=True, slots=True)
class SparqlConfig:
    endpoint: str
    timeout: int
    steps: list[SparqlStep]


# ── Source ─────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class SourceConfig:
    celex: str
    title: str
    language: str
    language_code: str


# ── Fetch ──────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class RetryConfig:
    attempts: int
    delay_seconds: int


@dataclass(frozen=True, slots=True)
class FetchConfig:
    uri_select_script: str
    accept_header: str
    content_type: str
    retry: RetryConfig


# ── Postprocess ───────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class NormalizeRule:
    find: str
    replace: str


@dataclass(frozen=True, slots=True)
class PostprocessConfig:
    normalize: list[NormalizeRule]


# ── Corpus ─────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class SectionDef:
    dir: str
    filename: str
    heading: str
    frontmatter: dict[str, str]


@dataclass(frozen=True, slots=True)
class CorpusConfig:
    frontmatter_base: dict[str, Any]
    sections: dict[str, SectionDef]


# ── Top-level ──────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class PipelineConfig:
    source: SourceConfig
    sparql: SparqlConfig
    fetch: FetchConfig
    postprocess: PostprocessConfig
    corpus: CorpusConfig


# ── Loader ─────────────────────────────────────────────────────

def _build_steps(raw_steps: list[dict[str, Any]]) -> list[SparqlStep]:
    return [
        SparqlStep(
            name=s["name"],
            description=s["description"],
            template=s["template"],
            script=s["script"],
        )
        for s in raw_steps
    ]


def _build_postprocess(raw: dict[str, Any]) -> PostprocessConfig:
    rules = [
        NormalizeRule(find=r["find"], replace=r["replace"])
        for r in raw.get("normalize", [])
    ]
    return PostprocessConfig(normalize=rules)


def _build_sections(raw: dict[str, Any]) -> dict[str, SectionDef]:
    return {
        name: SectionDef(
            dir=s["dir"],
            filename=s["filename"],
            heading=s["heading"],
            frontmatter=s.get("frontmatter", {}),
        )
        for name, s in raw.items()
    }


def load_config(path: Path) -> Result[PipelineConfig]:
    """Load data.yaml into PipelineConfig. No validation beyond structure."""
    if not path.exists():
        return Fail(error=f"Config file not found: {path}")

    try:
        raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return Fail(error=f"YAML parse error: {exc}", context=str(path))

    try:
        retry = raw["fetch"]["retry"]

        config = PipelineConfig(
            source=SourceConfig(**raw["source"]),
            sparql=SparqlConfig(
                endpoint=raw["sparql"]["endpoint"],
                timeout=raw["sparql"]["timeout"],
                steps=_build_steps(raw["sparql"]["steps"]),
            ),
            fetch=FetchConfig(
                uri_select_script=raw["fetch"]["uri_select_script"],
                accept_header=raw["fetch"]["accept_header"],
                content_type=raw["fetch"].get("content_type", "xml"),
                retry=RetryConfig(
                    attempts=retry["attempts"],
                    delay_seconds=retry["delay_seconds"],
                ),
            ),
            postprocess=_build_postprocess(raw.get("postprocess", {})),
            corpus=CorpusConfig(
                frontmatter_base=raw["corpus"]["frontmatter_base"],
                sections=_build_sections(raw["corpus"]["sections"]),
            ),
        )
    except (KeyError, TypeError) as exc:
        return Fail(error=f"Config structure error: {exc}", context=str(path))

    return Ok(data=config)