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
"""EU AI Act RAG Playground — Streamlit chat interface for testing the AutoRAG worker."""

import os
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as st_components
from dotenv import load_dotenv

from export_utils import (
    export_conversation_json,
    export_conversation_markdown,
    get_export_filename,
)
from translations import get_locale, set_locale, t

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "prod")

WORKER_URL = (
    "http://localhost:8791"
    if ENVIRONMENT == "dev"
    else "https://eu-ai-act-rag-worker.aras.tc"
)

TURNSTILE_ENABLED = ENVIRONMENT != "dev"

_turnstile_component = st_components.declare_component(
    "turnstile",
    path=str(Path(__file__).parent / "components" / "turnstile"),
)

ALLOWED_MODELS = [
    "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "@cf/meta/llama-3.1-8b-instruct",
    "@cf/meta/llama-3.1-70b-instruct",
    "@cf/mistral/mistral-7b-instruct-v0.1",
    "@cf/google/gemma-7b-it",
    "@cf/qwen/qwen1.5-7b-chat-awq",
]


def render_sources(source_items: list, meta: dict) -> None:
    """Render sources block with expandable content for each chunk."""
    with st.chat_message("assistant", avatar="🔍"):
        st.markdown(f"**{t('sources.title')}** ({len(source_items)})")

        for src in source_items:
            score_pct = src["score"] * 100
            label = f"`{src['filename']}` ({t('sources.score')}: {score_pct:.1f}%)"

            content = src.get("content", "")
            if content:
                with st.expander(label, expanded=False):
                    st.markdown(content)
            else:
                st.markdown(f"- {label}")

        if meta:
            st.caption(
                f"{t('metadata.searchQuery')}: {meta.get('search_query', '-')} · "
                f"{t('metadata.duration')}: {meta.get('duration_ms', 0)}ms"
            )


# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title=t("app.title"),
    page_icon=t("app.pageIcon"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Session State
# ---------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "pending" not in st.session_state:
    st.session_state["pending"] = False
if "last_debug" not in st.session_state:
    st.session_state["last_debug"] = None
if "turnstile_reset" not in st.session_state:
    st.session_state["turnstile_reset"] = 0


# ---------------------------------------------------------------------------
# Save Dialog
# ---------------------------------------------------------------------------

@st.dialog(t("export.title"))
def save_dialog():
    """Export conversation as Markdown or JSON."""
    export_cols = st.columns(2)

    with export_cols[0]:
        md_content = export_conversation_markdown(
            st.session_state["messages"], locale=get_locale()
        )
        st.download_button(
            label=t("export.markdown"),
            data=md_content,
            file_name=get_export_filename("md"),
            mime="text/markdown",
            use_container_width=True,
            help=t("export.markdownTooltip"),
        )

    with export_cols[1]:
        json_content = export_conversation_json(st.session_state["messages"])
        st.download_button(
            label=t("export.json"),
            data=json_content,
            file_name=get_export_filename("json"),
            mime="application/json",
            use_container_width=True,
            help=t("export.jsonTooltip"),
        )

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

header_cols = st.columns([6, 1, 1, 1, 1])

with header_cols[0]:
    st.title(t("app.title"))

with header_cols[1]:
    if st.button(
        "🇺🇸",
        use_container_width=True,
        type="secondary" if get_locale() == "tr" else "primary",
    ):
        set_locale("en")
        st.rerun()

with header_cols[2]:
    if st.button(
        "🇹🇷",
        use_container_width=True,
        type="secondary" if get_locale() == "en" else "primary",
    ):
        set_locale("tr")
        st.rerun()

with header_cols[3]:
    if st.button(
        "💾",
        use_container_width=True,
        disabled=st.session_state["pending"] or not st.session_state["messages"],
    ):
        save_dialog()

with header_cols[4]:
    if st.button(
        "🗑️",
        use_container_width=True,
        disabled=st.session_state["pending"] or not st.session_state["messages"],
    ):
        st.session_state["messages"] = []
        st.rerun()

# ---------------------------------------------------------------------------
# Sidebar — Search Options
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header(t("sidebar.searchOptions"))

    so_model = st.selectbox(t("sidebar.model"), options=ALLOWED_MODELS, index=0)

    so_rewrite_query = st.toggle(t("sidebar.rewriteQuery"), value=True)

    so_reranking = st.toggle(t("sidebar.reRanking"), value=True)

    so_max_results = st.slider(
        t("sidebar.maxResults"), min_value=1, max_value=50, value=20
    )

    so_score_threshold = st.slider(
        t("sidebar.scoreThreshold"),
        min_value=0.0,
        max_value=1.0,
        value=0.4,
        step=0.05,
    )


# ---------------------------------------------------------------------------
# Welcome Message
# ---------------------------------------------------------------------------

if not st.session_state["messages"]:
    with st.chat_message("assistant"):
        st.markdown(t("chat.welcome"))
        st.markdown(t("chat.examples"))

# ---------------------------------------------------------------------------
# Chat History
# ---------------------------------------------------------------------------

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

    if msg["role"] == "assistant" and msg.get("sources"):
        render_sources(msg["sources"], msg.get("metadata", {}))

# ---------------------------------------------------------------------------
# Turnstile Widget
# ---------------------------------------------------------------------------

if TURNSTILE_ENABLED:
    st.session_state["turnstile_token"] = _turnstile_component(
        reset_count=st.session_state["turnstile_reset"],
        key="turnstile",
        default=None,
    )

# ---------------------------------------------------------------------------
# Chat Input
# ---------------------------------------------------------------------------

if prompt := st.chat_input(
    t("chat.placeholder"), disabled=st.session_state["pending"]
):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.session_state["pending"] = True
    st.rerun()

if st.session_state["pending"]:
    with st.chat_message("assistant"):
        # noinspection PyTypeChecker
        with st.spinner(t("chat.thinking")):
            try:
                payload = {
                    "messages": [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state["messages"]
                    ],
                    "locale": get_locale(),
                    "searchOptions": {
                        "model": so_model,
                        "rewriteQuery": so_rewrite_query,
                        "reRanking": so_reranking,
                        "maxResults": so_max_results,
                        "scoreThreshold": so_score_threshold,
                    },
                }

                url = f"{WORKER_URL}/api/v1/chat/completions"

                headers = {}
                if TURNSTILE_ENABLED:
                    token = st.session_state.get("turnstile_token")
                    if token:
                        headers["X-Turnstile-Token"] = token

                resp = requests.post(url, json=payload, headers=headers, timeout=60)

                if TURNSTILE_ENABLED:
                    st.session_state["turnstile_reset"] += 1

                # Store debug info in session state
                try:
                    resp_body = resp.json()
                except (ValueError, requests.JSONDecodeError):
                    resp_body = resp.text[:2000]

                st.session_state["last_debug"] = {
                    "url": url,
                    "status": resp.status_code,
                    "content_type": resp.headers.get("content-type", "N/A"),
                    "size": len(resp.content),
                    "elapsed": resp.elapsed.total_seconds(),
                    "payload": payload,
                    "response": resp_body,
                }

                if resp.status_code == 200:
                    data = resp.json()
                    response_text = data.get(
                        "response", t("errors.emptyResponse")
                    )
                    sources = data.get("sources", [])
                    metadata = data.get("metadata", {})

                    st.session_state["messages"].append(
                        {
                            "role": "assistant",
                            "content": response_text,
                            "sources": sources,
                            "metadata": metadata,
                        }
                    )
                else:
                    error_data = (
                        resp.json()
                        if resp.headers.get("content-type", "").startswith(
                            "application/json"
                        )
                        else {}
                    )
                    st.error(
                        error_data.get("error", {}).get(
                            "message",
                            f"{t('errors.requestFailed')}: {resp.status_code}",
                        )
                    )

            except requests.ConnectionError as e:
                st.session_state["last_debug"] = {"error": f"ConnectionError: {e}"}
            except requests.Timeout as e:
                st.session_state["last_debug"] = {"error": f"Timeout: {e}"}
            except Exception as e:
                st.session_state["last_debug"] = {"error": f"{type(e).__name__}: {e}"}

    st.session_state["pending"] = False
    st.rerun()

# ---------------------------------------------------------------------------
# Debug Panel (persists after rerun)
# ---------------------------------------------------------------------------

if os.getenv("ENVIRONMENT", "prod") == "dev" and st.session_state["last_debug"]:
    dbg = st.session_state["last_debug"]
    with st.expander("🐛 DEBUG — Last Request", expanded=False):
        if "error" in dbg:
            st.error(dbg["error"])
        else:
            st.caption(
                f"**URL:** `{dbg['url']}` | "
                f"**Status:** `{dbg['status']}` | "
                f"**Content-Type:** `{dbg['content_type']}` | "
                f"**Size:** `{dbg['size']}` bytes | "
                f"**Elapsed:** `{dbg['elapsed']:.2f}s`"
            )
            st.caption("**Request payload:**")
            st.json(dbg["payload"])
            st.caption("**Response body:**")
            if isinstance(dbg["response"], dict):
                st.json(dbg["response"])
            else:
                st.code(dbg["response"], language="text")
