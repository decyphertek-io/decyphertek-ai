#!/bin/bash

# DecypherTek AI - Custom Edition
# Automated setup and launch script

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

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   DecypherTek AI - Custom Edition      ║${NC}"
echo -e "${BLUE}║   Automated Setup & Launch             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}[1/5] Checking Python version...${NC}"
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
echo -e "${YELLOW}[2/5] Checking for Poetry...${NC}"
if command -v poetry &> /dev/null; then
    POETRY_VERSION=$(poetry --version 2>&1 | awk '{print $3}')
    echo -e "${GREEN}✓ Poetry $POETRY_VERSION found${NC}"
    USE_POETRY=true
else
    echo -e "${YELLOW}⚠ Poetry not found. Will use pip instead.${NC}"
    echo -e "${BLUE}  Install Poetry for better dependency management:${NC}"
    echo -e "${BLUE}  curl -sSL https://install.python-poetry.org | python3 -${NC}"
    USE_POETRY=false
fi
echo ""

# Setup environment and install dependencies
if [ "$USE_POETRY" = true ]; then
    echo -e "${YELLOW}[3/5] Setting up Poetry environment...${NC}"
    
    # Ensure keyring is disabled (belt and suspenders approach)
    export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
    
    # Check if virtual environment exists
    if ! poetry env info &> /dev/null; then
        echo -e "${BLUE}  Creating new Poetry virtual environment...${NC}"
        poetry env use python3
    fi
    
    echo -e "${YELLOW}[4/5] Installing dependencies with Poetry...${NC}"
    poetry install --no-root
    
    echo -e "${GREEN}✓ Poetry environment ready${NC}"
    echo ""
    
    echo -e "${YELLOW}[5/5] Launching DecypherTek AI...${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Launch the app
    poetry run python src/main.py
    
else
    echo -e "${YELLOW}[3/5] Checking for virtual environment...${NC}"
    
    # Create venv if it doesn't exist
    if [ ! -d "venv" ]; then
        echo -e "${BLUE}  Creating virtual environment...${NC}"
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    else
        echo -e "${GREEN}✓ Virtual environment exists${NC}"
    fi
    echo ""
    
    echo -e "${YELLOW}[4/5] Installing dependencies with pip...${NC}"
    source venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
    echo ""
    
    echo -e "${YELLOW}[5/5] Launching DecypherTek AI...${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Launch the app
    python src/main.py
fi

