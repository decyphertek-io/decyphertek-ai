#!/bin/bash

# DecypherTek AI - Custom Edition
# Automated setup and launch script with centralized data directory

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Centralized data directory
DATA_DIR="$HOME/.decyphertek-ai"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   DecypherTek AI - Custom Edition      ║${NC}"
echo -e "${BLUE}║   Automated Setup & Launch             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}[1/6] Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
    echo -e "${RED}✗ Error: Python 3.10+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"
echo ""

# Check if Poetry is installed
echo -e "${YELLOW}[2/6] Checking for Poetry...${NC}"
if command -v poetry &> /dev/null; then
    POETRY_VERSION=$(poetry --version 2>&1 | awk '{print $3}')
    echo -e "${GREEN}✓ Poetry $POETRY_VERSION found${NC}"
    USE_POETRY=true
else
    echo -e "${RED}✗ Poetry not found${NC}"
    echo -e "${BLUE}  Install Poetry with: curl -sSL https://install.python-poetry.org | python3 -${NC}"
    exit 1
fi
echo ""

# Create centralized data directory
echo -e "${YELLOW}[3/6] Setting up data directory...${NC}"
if [ ! -d "$DATA_DIR" ]; then
    echo -e "${BLUE}  Creating $DATA_DIR${NC}"
    mkdir -p "$DATA_DIR"
    mkdir -p "$DATA_DIR/store/agent"
    mkdir -p "$DATA_DIR/store/mcp"
    mkdir -p "$DATA_DIR/store/app"
    mkdir -p "$DATA_DIR/documents"
    mkdir -p "$DATA_DIR/notes"
    echo -e "${GREEN}✓ Data directory created${NC}"
else
    echo -e "${GREEN}✓ Data directory exists${NC}"
fi
echo ""

# Setup Poetry environment in project directory
echo -e "${YELLOW}[4/6] Setting up Poetry environment...${NC}"

# Configure Poetry to create .venv in project directory (not global)
export POETRY_VIRTUALENVS_IN_PROJECT=true
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring

# Check if virtual environment exists in project
VENV_PATH=".venv"
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${BLUE}  Creating new Poetry virtual environment in .venv${NC}"
    poetry install --no-root
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
    # Check if dependencies need updating
    if [ "$1" == "--update" ] || [ "$1" == "-u" ]; then
        echo -e "${BLUE}  Updating dependencies...${NC}"
        poetry update
    fi
fi
echo ""

echo -e "${YELLOW}[5/6] Installing dependencies with Poetry...${NC}"
if [ -d "$VENV_PATH" ]; then
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
else
    poetry install --no-root
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi
echo -e "${GREEN}✓ Poetry environment ready${NC}"
echo ""

echo -e "${YELLOW}[6/6] Launching DecypherTek AI...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Data directory: $DATA_DIR${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Launch the app
poetry run python src/main.py
