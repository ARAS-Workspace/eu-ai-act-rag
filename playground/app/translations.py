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
"""Translation helper — JSON-based i18n with dot-notation key access."""

import json
import os
import streamlit as st


def load_translations(locale: str) -> dict:
    path = os.path.join(os.path.dirname(__file__), "locales", f"{locale}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_locale() -> str:
    return st.session_state.get("locale", "en")


def set_locale(locale: str) -> None:
    st.session_state["locale"] = locale


def t(key: str) -> str:
    locale = get_locale()

    if "translations" not in st.session_state or st.session_state.get("_translations_locale") != locale:
        st.session_state["translations"] = load_translations(locale)
        st.session_state["_translations_locale"] = locale

    keys = key.split(".")
    value = st.session_state["translations"]
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k, key)
        else:
            return key
    return value if isinstance(value, str) else key
