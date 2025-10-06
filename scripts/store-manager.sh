#!/bin/bash
# DecypherTek AI - Store Manager Setup Script
# Sets up Poetry environment for agents, MCP servers, and apps

set -e

# Check arguments
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <component_directory>"
    exit 1
fi

# Convert to absolute path to be safe
COMPONENT_DIR="$(cd "$1" && pwd)"

if [ ! -d "$COMPONENT_DIR" ]; then
    echo "Error: Directory $COMPONENT_DIR does not exist"
    exit 1
fi

echo "[store-manager.sh] Setting up Poetry environment in: $COMPONENT_DIR"

# Change to component directory - CRITICAL for Poetry to create .venv in the right place
cd "$COMPONENT_DIR"

# Check for pyproject.toml
if [ ! -f "pyproject.toml" ]; then
    echo "[store-manager.sh] ERROR: pyproject.toml not found"
    exit 1
fi

echo "[store-manager.sh] Found pyproject.toml, configuring Poetry..."

# CRITICAL: Remove any conflicting global Poetry config
echo "[store-manager.sh] Clearing any global virtualenvs.path setting..."
poetry config virtualenvs.path --unset 2>/dev/null || true

# Same config as launch.sh
export POETRY_VIRTUALENVS_IN_PROJECT=true
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring

echo "[store-manager.sh] Poetry config check:"
poetry config virtualenvs.in-project
echo "[store-manager.sh] Running: poetry install --no-root"

# Let Poetry create the venv and install dependencies
poetry install --no-root

echo "[store-manager.sh] Poetry install completed, checking for .venv..."

# Verify .venv exists
if [ -d ".venv" ]; then
    echo "[store-manager.sh] ✓ Virtual environment created at: $COMPONENT_DIR/.venv"
else
    echo "[store-manager.sh] ERROR: .venv was not created!"
    echo "[store-manager.sh] Poetry config:"
    poetry config --list | grep virtualenvs
    exit 1
fi

echo "[store-manager.sh] ✓ Setup complete"

