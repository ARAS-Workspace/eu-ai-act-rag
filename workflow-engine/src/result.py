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

"""Result pattern for error handling without exceptions.

Provides Ok[T] and Fail types as an alternative to raising exceptions.
Every function that can fail returns Result[T] = Ok[T] | Fail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    """Successful result carrying typed data."""

    data: T
    ok: bool = field(default=True, init=False)


@dataclass(frozen=True, slots=True)
class Fail:
    """Failed result carrying error message and optional context."""

    error: str
    context: Any = None
    ok: bool = field(default=False, init=False)


Result = Ok[T] | Fail