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

"""Document fetcher — downloads content from URI resolved via workflow script.

No hardcoded URLs. URI comes from SPARQL context via data.yaml script.
Downloads to a temporary directory provided by the pipeline orchestrator.
"""

from __future__ import annotations

import ssl
import time
import urllib.error
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

import certifi

from src.config import FetchConfig
from src.logger import get_logger
from src.result import Fail, Ok, Result
from src.sparql.processor import execute_script

log = get_logger(__name__)

_ssl_ctx = ssl.create_default_context(cafile=certifi.where())


def select_uri(
    script: str,
    context: dict[str, Any],
    source: dict[str, str],
) -> Result[str]:
    """Run the URI selection script from data.yaml to pick a download URL."""
    result = execute_script(
        script=script,
        bindings=[],
        context=context,
        source=source,
        step_name="uri_select",
    )
    if not result.ok:
        return result  # type: ignore[return-value]
    if not isinstance(result.data, str) or not result.data:
        return Fail(error="URI selection script returned empty or non-string output")
    return Ok(data=result.data)


def _download(url: str, accept: str, timeout: int = 30) -> Result[bytes]:
    """Single download attempt."""
    req = urllib.request.Request(
        url,
        headers={"Accept": accept},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx) as resp:
            return Ok(data=resp.read())
    except urllib.error.HTTPError as exc:
        return Fail(error=f"HTTP {exc.code}: {exc.reason}", context=url)
    except urllib.error.URLError as exc:
        return Fail(error=f"Connection error: {exc.reason}", context=url)
    except TimeoutError:
        return Fail(error=f"Timeout after {timeout}s", context=url)


def _extract_zip(data: bytes, out_dir: Path) -> Result[list[Path]]:
    """Extract ZIP archive contents to output directory."""
    try:
        zf = zipfile.ZipFile(BytesIO(data))
    except zipfile.BadZipFile as exc:
        return Fail(error=f"Invalid ZIP: {exc}")

    extracted: list[Path] = []
    for name in zf.namelist():
        target = out_dir / name
        target.write_bytes(zf.read(name))
        extracted.append(target)
        log.info("Extracted: %s", name)

    return Ok(data=extracted)


def fetch_document(
    config: FetchConfig,
    context: dict[str, Any],
    source: dict[str, str],
    tmp_dir: Path,
) -> Result[Path]:
    """Select URI via script, download with retry, extract to tmp_dir."""
    uri_result = select_uri(config.uri_select_script, context, source)
    if not uri_result.ok:
        return uri_result  # type: ignore[return-value]

    url: str = uri_result.data
    log.info("Selected URI: %s", url)

    # Download with retry
    data: bytes | None = None
    last_error = ""

    for attempt in range(1, config.retry.attempts + 1):
        log.info("Download attempt %d/%d", attempt, config.retry.attempts)
        dl_result = _download(url, config.accept_header)
        if dl_result.ok:
            data = dl_result.data
            break
        last_error = dl_result.error
        log.warning("Attempt %d failed: %s", attempt, last_error)
        if attempt < config.retry.attempts:
            time.sleep(config.retry.delay_seconds)

    if data is None:
        return Fail(error=f"All {config.retry.attempts} download attempts failed: {last_error}")

    log.info("Downloaded %d bytes", len(data))

    # Extract if ZIP
    if config.content_type == "zip":
        extract_result = _extract_zip(data, tmp_dir)
        if not extract_result.ok:
            return extract_result  # type: ignore[return-value]
        log.info("Extracted %d files to %s", len(extract_result.data), tmp_dir)
    else:
        # Non-ZIP: write raw content
        (tmp_dir / "content.xml").write_bytes(data)

    return Ok(data=tmp_dir)