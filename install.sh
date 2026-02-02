#!/bin/bash

# Decyphertek AI CLI Installer
# Self-contained installation to ~/.decyphertek.ai

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
INSTALL_DIR="$HOME/.decyphertek.ai/bin"
APP_NAME="decyphertek.ai"
GITHUB_REPO="decyphertek-io/decyphertek-ai"
DOWNLOAD_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/main/cli/dist/${APP_NAME}"

echo ""
echo "========================================="
echo "  Decyphertek AI CLI Installer"
echo "========================================="
echo ""

# Check for curl
if ! command -v curl &> /dev/null; then
    echo "Error: curl is required but not installed"
    exit 1
fi

# Create directory
echo -e "${BLUE}[INFO]${NC} Creating installation directory..."
mkdir -p "${INSTALL_DIR}"

# Download
echo -e "${BLUE}[INFO]${NC} Downloading ${APP_NAME}..."
if curl -L -f -s "${DOWNLOAD_URL}" -o "${INSTALL_DIR}/${APP_NAME}"; then
    echo -e "${GREEN}[✓]${NC} Downloaded ${APP_NAME}"
else
    echo "Error: Failed to download ${APP_NAME}"
    exit 1
fi

# Set permissions
chmod +x "${INSTALL_DIR}/${APP_NAME}"

# Add to PATH if not already there
SHELL_RC=""
if [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

if [ -n "$SHELL_RC" ]; then
    if ! grep -q "/.decyphertek.ai/bin" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# Decyphertek AI CLI" >> "$SHELL_RC"
        echo 'export PATH="$HOME/.decyphertek.ai/bin:$PATH"' >> "$SHELL_RC"
        echo -e "${GREEN}[✓]${NC} Added to PATH in $SHELL_RC"
    fi
fi

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo -e "${BLUE}Installed to:${NC} ${INSTALL_DIR}/${APP_NAME}"
echo ""
echo -e "${BLUE}Run:${NC}"
echo -e "  source $SHELL_RC  # Reload shell config"
echo -e "  decyphertek.ai    # Start the CLI"
echo ""
echo -e "${BLUE}Or run directly:${NC}"
echo -e "  ${INSTALL_DIR}/${APP_NAME}"
echo ""
