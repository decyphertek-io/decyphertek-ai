#!/bin/bash

# DecypherTek AI - Linux Desktop Build Script
# Creates .deb and Flatpak packages for Linux desktop

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
echo -e "${BLUE}║   DecypherTek AI - Linux Build         ║${NC}"
echo -e "${BLUE}║   .deb and Flatpak Packages            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if Poetry is available
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}✗ Error: Poetry not found${NC}"
    echo -e "${YELLOW}Install Poetry: curl -sSL https://install.python-poetry.org | python3 -${NC}"
    exit 1
fi

# Clean previous builds
echo -e "${YELLOW}[1/4] Cleaning previous builds...${NC}"
rm -rf build/linux
rm -rf build/flatpak
echo -e "${GREEN}✓ Cleaned previous builds${NC}"
echo ""

# Build .deb package
echo -e "${YELLOW}[2/4] Building .deb package...${NC}"
poetry run flet build linux src \
    --project "decyphertek-ai" \
    --description "DecypherTek AI - Modern AI Assistant" \
    --product "DecypherTek AI" \
    --org "com.decyphertek" \
    --company "DecypherTek" \
    --copyright "© 2025 DecypherTek" \
    --build-version "1.0.0" \
    --build-number "1" \
    --exclude __pycache__ .venv .git logs

if [ -d "build/linux" ]; then
    echo -e "${GREEN}✓ .deb package built successfully${NC}"
    echo -e "${BLUE}  Location: build/linux/${NC}"
else
    echo -e "${RED}✗ .deb build failed${NC}"
    exit 1
fi
echo ""

# Build Flatpak package
echo -e "${YELLOW}[3/4] Building Flatpak package...${NC}"
poetry run flet build linux src \
    --project "decyphertek-ai" \
    --description "DecypherTek AI - Modern AI Assistant" \
    --product "DecypherTek AI" \
    --org "com.decyphertek" \
    --company "DecypherTek" \
    --copyright "© 2025 DecypherTek" \
    --build-version "1.0.0" \
    --build-number "1" \
    --exclude __pycache__ .venv .git logs \
    --template flatpak

if [ -d "build/flatpak" ]; then
    echo -e "${GREEN}✓ Flatpak package built successfully${NC}"
    echo -e "${BLUE}  Location: build/flatpak/${NC}"
else
    echo -e "${YELLOW}⚠ Flatpak build not available (requires Flatpak template)${NC}"
fi
echo ""

# Summary
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Build Complete!              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Packages created:${NC}"
if [ -d "build/linux" ]; then
    echo -e "  📦 .deb package: ${GREEN}build/linux/${NC}"
fi
if [ -d "build/flatpak" ]; then
    echo -e "  📦 Flatpak package: ${GREEN}build/flatpak/${NC}"
fi
echo ""
echo -e "${YELLOW}Installation:${NC}"
echo -e "  .deb: ${BLUE}sudo dpkg -i build/linux/*.deb${NC}"
echo -e "  Flatpak: ${BLUE}flatpak install build/flatpak/*.flatpak${NC}"
echo ""
echo -e "${BLUE}Note: Users will need to configure their OpenRouter API key after installation.${NC}"
