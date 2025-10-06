#!/bin/bash

# Component installer script for agents and MCP servers
# Usage: ./install-component.sh <component_path>

set -e

COMPONENT_DIR="$1"

if [ -z "$COMPONENT_DIR" ] || [ ! -d "$COMPONENT_DIR" ]; then
    echo "Error: Component directory not provided or doesn't exist"
    exit 1
fi

cd "$COMPONENT_DIR"

echo "[Install] Setting up Poetry environment in: $COMPONENT_DIR"

# Set environment variables
export POETRY_VIRTUALENVS_PATH="$COMPONENT_DIR"
export POETRY_VIRTUALENVS_IN_PROJECT=false
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring

# Configure Poetry
poetry config virtualenvs.path "$COMPONENT_DIR"

# Generate lock file
echo "[Install] Generating poetry.lock..."
poetry lock

# Create virtual environment
echo "[Install] Creating virtual environment..."
poetry env use python3

# Install dependencies
echo "[Install] Installing dependencies..."
poetry install --no-root

# Verify .venv exists
VENV_PATH="$COMPONENT_DIR/.venv"
if [ -d "$VENV_PATH" ]; then
    echo "[Install] ✓ Virtual environment created at: $VENV_PATH"
    exit 0
else
    echo "[Install] ✗ Failed to create virtual environment"
    exit 1
fi

