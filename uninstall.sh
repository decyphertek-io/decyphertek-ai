#!/bin/bash

# Decyphertek AI CLI Uninstaller
# Removes ~/.decyphertek.ai and ~/.ssh/decyphertek.ai

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "========================================="
echo "  Decyphertek AI CLI Uninstaller"
echo "========================================="
echo ""

# Confirm
echo -e "${YELLOW}[WARNING]${NC} This will remove:"
echo "  - ~/.decyphertek.ai/ (CLI, agents, creds, config)"
echo "  - ~/.ssh/decyphertek.ai (SSH keys)"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

# Remove ~/.decyphertek.ai
if [ -d "$HOME/.decyphertek.ai" ]; then
    echo -e "${BLUE}[INFO]${NC} Removing ~/.decyphertek.ai..."
    rm -rf "$HOME/.decyphertek.ai"
    echo -e "${GREEN}[✓]${NC} Removed ~/.decyphertek.ai"
fi

# Remove SSH keys
if [ -f "$HOME/.ssh/decyphertek.ai" ]; then
    echo -e "${BLUE}[INFO]${NC} Removing SSH keys..."
    rm -f "$HOME/.ssh/decyphertek.ai" "$HOME/.ssh/decyphertek.ai.pub"
    echo -e "${GREEN}[✓]${NC} Removed SSH keys"
fi

# Remove PATH entry from shell config
for RC in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$RC" ] && grep -q "/.decyphertek.ai/bin" "$RC" 2>/dev/null; then
        echo -e "${BLUE}[INFO]${NC} Removing PATH entry from $RC..."
        sed -i '/# Decyphertek AI CLI/,+1d' "$RC"
        echo -e "${GREEN}[✓]${NC} Removed PATH entry"
    fi
done

echo ""
echo -e "${GREEN}Uninstall complete!${NC}"
echo ""
