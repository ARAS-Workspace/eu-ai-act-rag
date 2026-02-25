#!/bin/bash
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

# EU AI Act RAG Playground - Start Script
# Activates Python virtual environment and runs Streamlit playground

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Project root directory (2 levels up: playground/ -> project root)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Virtual environment path
VENV_PATH="$PROJECT_ROOT/.venv"

# Check if venv exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Python virtual environment not found at $VENV_PATH"
    echo "Please create venv first: python -m venv .venv"
    exit 1
fi

# Activate virtual environment
echo "Activating Python virtual environment..."
source "$VENV_PATH/bin/activate"

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "Error: streamlit not found in virtual environment"
    echo "Please install dependencies: pip install -r app/requirements.txt"
    exit 1
fi

# Change to app directory
# shellcheck disable=SC2164
cd "$SCRIPT_DIR/app"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Run Streamlit
echo "Starting EU AI Act RAG Playground..."
streamlit run app.py
