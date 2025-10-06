#!/bin/bash
# DecypherTek AI - Store Manager Setup Script
# Sets up Poetry environment for agents, MCP servers, and apps

set -e

# Check arguments
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <component_directory>"
    exit 1
fi

COMPONENT_DIR="$1"

if [ ! -d "$COMPONENT_DIR" ]; then
    echo "Error: Directory $COMPONENT_DIR does not exist"
    exit 1
fi

cd "$COMPONENT_DIR"

# Check for pyproject.toml
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found in $COMPONENT_DIR"
    exit 1
fi

echo "Setting up Poetry environment in: $COMPONENT_DIR"

# Configure Poetry for this directory (same as launch.sh)
export POETRY_VIRTUALENVS_PATH="$COMPONENT_DIR"
export POETRY_VIRTUALENVS_IN_PROJECT=false
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring

# Set Poetry config
poetry config virtualenvs.path "$COMPONENT_DIR"

# Generate lock file
echo "Generating poetry.lock..."
poetry lock

# Create virtual environment
echo "Creating virtual environment..."
poetry env use python3

# Install dependencies
echo "Installing dependencies..."
poetry install --no-root

echo "✓ Setup complete for $COMPONENT_DIR"
echo "✓ Virtual environment created at: $COMPONENT_DIR/.venv"

