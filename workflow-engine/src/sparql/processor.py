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
"""SPARQL result processor — executes inline scripts from data.yaml.

Pure engine: receives bindings + script code, executes it, returns output.
No domain knowledge — all logic lives in data.yaml scripts.
"""

from __future__ import annotations

from typing import Any

from src.logger import get_logger
from src.result import Fail, Ok, Result

log = get_logger(__name__)


def execute_script(
    script: str,
    bindings: list[dict[str, Any]],
    context: dict[str, Any],
    source: dict[str, str],
    step_name: str,
) -> Result[Any]:
    """Execute a data.yaml inline script with the given scope.

    The script receives:
        bindings — raw SPARQL JSON result bindings
        context  — accumulated outputs from previous steps
        source   — source config dict (celex, language, ...)

    The script must set an `output` variable. That value is returned.
    """
    namespace: dict[str, Any] = {
        "bindings": bindings,
        "context": context,
        "source": source,
        "output": None,
    }

    try:
        exec(script, {"__builtins__": __builtins__}, namespace)  # noqa: S102
    except Exception as exc:
        return Fail(
            error=f"Script error in step '{step_name}': {type(exc).__name__}: {exc}",
            context=script[:200],
        )

    if "output" not in namespace or namespace["output"] is None:
        return Fail(
            error=f"Script in step '{step_name}' did not set 'output'",
            context=script[:200],
        )

    log.info("Step '%s' script executed — output type: %s", step_name, type(namespace["output"]).__name__)
    return Ok(data=namespace["output"])