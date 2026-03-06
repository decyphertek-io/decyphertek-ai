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

# Add to PATH in all existing shell config files
PATH_LINE='export PATH="$HOME/.decyphertek.ai/bin:$PATH"'
ADDED_TO=""

for RC_FILE in "$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile" "$HOME/.zshrc"; do
    if [ -f "$RC_FILE" ]; then
        if ! grep -q "/.decyphertek.ai/bin" "$RC_FILE" 2>/dev/null; then
            echo "" >> "$RC_FILE"
            echo "# Decyphertek AI CLI" >> "$RC_FILE"
            echo "$PATH_LINE" >> "$RC_FILE"
            echo -e "${GREEN}[✓]${NC} Added to PATH in $RC_FILE"
            ADDED_TO="$RC_FILE"
        fi
    fi
done

# If nothing existed, create .profile as fallback
if [ -z "$ADDED_TO" ]; then
    echo "" >> "$HOME/.profile"
    echo "# Decyphertek AI CLI" >> "$HOME/.profile"
    echo "$PATH_LINE" >> "$HOME/.profile"
    echo -e "${GREEN}[✓]${NC} Added to PATH in $HOME/.profile"
    ADDED_TO="$HOME/.profile"
fi

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo -e "${BLUE}Installed to:${NC} ${INSTALL_DIR}/${APP_NAME}"
echo ""
echo -e "${BLUE}Run:${NC}"
echo -e "  source ${ADDED_TO}  # Reload shell config"
echo -e "  decyphertek.ai      # Start the CLI"
echo ""
echo -e "${BLUE}Or run directly:${NC}"
echo -e "  ${INSTALL_DIR}/${APP_NAME}"
echo ""
