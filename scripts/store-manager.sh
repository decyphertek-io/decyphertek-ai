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

echo "Setting up Poetry environment in: $COMPONENT_DIR"

# Change to component directory - CRITICAL for Poetry to create .venv in the right place
cd "$COMPONENT_DIR"

# Check for pyproject.toml
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found in $COMPONENT_DIR"
    exit 1
fi

# Same config as launch.sh - this is what makes it work!
export POETRY_VIRTUALENVS_IN_PROJECT=true
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring

# Run poetry install - it will auto-create .venv in the CURRENT directory
poetry install --no-root

# Verify .venv was created
if [ -d ".venv" ]; then
    echo "✓ Virtual environment created at: $COMPONENT_DIR/.venv"
else
    echo "ERROR: .venv was not created in $COMPONENT_DIR"
    exit 1
fi

echo "✓ Setup complete for $COMPONENT_DIR"

