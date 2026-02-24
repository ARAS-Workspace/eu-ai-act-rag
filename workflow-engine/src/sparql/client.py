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
"""Generic SPARQL HTTP client using urllib.

Sends POST requests to a SPARQL endpoint and returns parsed JSON bindings.
No domain logic — pure transport layer.
"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import certifi

from src.logger import get_logger
from src.result import Fail, Ok, Result

log = get_logger(__name__)

Binding = dict[str, dict[str, str]]

_ssl_ctx = ssl.create_default_context(cafile=certifi.where())


def execute_query(
    endpoint: str,
    query: str,
    timeout: int = 30,
) -> Result[list[Binding]]:
    """POST a SPARQL query and return the parsed result bindings."""
    encoded_body = urllib.parse.urlencode({"query": query}).encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=encoded_body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/sparql-results+json",
        },
        method="POST",
    )

    log.info("SPARQL query → %s (%d bytes)", endpoint, len(encoded_body))

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx) as resp:
            raw: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        return Fail(
            error=f"SPARQL HTTP {exc.code}: {exc.reason}",
            context=body,
        )
    except urllib.error.URLError as exc:
        return Fail(error=f"SPARQL connection error: {exc.reason}")
    except TimeoutError:
        return Fail(error=f"SPARQL timeout after {timeout}s")

    bindings: list[Binding] = raw.get("results", {}).get("bindings", [])
    log.info("SPARQL returned %d bindings", len(bindings))
    return Ok(data=bindings)