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

# Add to PATH — .bashrc and .profile only (if they exist)
PATH_LINE='export PATH="$HOME/.decyphertek.ai/bin:$PATH"'

for RC_FILE in "$HOME/.bashrc" "$HOME/.profile"; do
    if [ -f "$RC_FILE" ]; then
        if ! grep -q "/.decyphertek.ai/bin" "$RC_FILE" 2>/dev/null; then
            echo "" >> "$RC_FILE"
            echo "# Decyphertek AI CLI" >> "$RC_FILE"
            echo "$PATH_LINE" >> "$RC_FILE"
            echo -e "${GREEN}[✓]${NC} Added to PATH in $RC_FILE"
        else
            echo -e "${GREEN}[✓]${NC} PATH already set in $RC_FILE"
        fi
    fi
done

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo -e "${BLUE}Installed to:${NC} ${INSTALL_DIR}/${APP_NAME}"
echo ""
echo -e "${BLUE}Run:${NC}"
echo -e "  source ~/.bashrc    # Reload shell config"
echo -e "  decyphertek.ai      # Start the CLI"
echo ""
echo -e "${BLUE}Or run directly:${NC}"
echo -e "  ${INSTALL_DIR}/${APP_NAME}"
echo ""
