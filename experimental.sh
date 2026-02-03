#!/bin/bash
#
# Decyphertek.ai Termux Installer & Builder
# One-command installation for Android/Termux ARM devices
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/decyphertek-io/decyphertek-ai/main/experimental.sh | bash
#
# This script will:
# 1. Install required Termux packages
# 2. Clone the decyphertek-ai repository
# 3. Build all agents and MCP servers natively for ARM
# 4. Set up PATH and launch the application
#

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║         DECYPHERTEK.AI - TERMUX INSTALLER (ARM)              ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if running in Termux
if [ ! -d "$PREFIX" ]; then
    echo "⚠ WARNING: This script is designed for Termux on Android"
    echo "⚠ It may not work correctly on other systems"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "▸ Step 1: Installing Termux packages..."
echo ""
pkg update -y
pkg install -y python openssl git binutils clang make

echo ""
echo "▸ Step 2: Installing uv package manager..."
echo ""
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "✓ uv: $(uv --version)"
echo ""

# Determine installation directory
INSTALL_DIR="$HOME/decyphertek-ai"

# Check if repo already exists
if [ -d "$INSTALL_DIR" ]; then
    echo "▸ Step 3: Existing installation found. Updating..."
    echo ""
    cd "$INSTALL_DIR"
    git pull
else
    echo "▸ Step 3: Cloning decyphertek-ai repository..."
    echo ""
    git clone https://github.com/decyphertek-io/decyphertek-ai.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo ""
echo "▸ Step 4: Building CLI (this may take 5-10 minutes on mobile)..."
echo ""
cd "$INSTALL_DIR/cli"
bash build.sh

echo ""
echo "▸ Step 5: Building Adminotaur agent..."
echo ""
cd "$INSTALL_DIR/../agent-store/adminotaur"
if [ -f "build.sh" ]; then
    bash build.sh
else
    echo "⚠ Adminotaur build script not found, skipping..."
fi

echo ""
echo "▸ Step 6: Building MCP servers..."
echo ""

# Build web-search
cd "$INSTALL_DIR/../mcp-store/web-search"
if [ -f "build.sh" ]; then
    echo "  → Building web-search..."
    bash build.sh
fi

# Build worldnewsapi
cd "$INSTALL_DIR/../mcp-store/worldnewsapi"
if [ -f "build.sh" ]; then
    echo "  → Building worldnewsapi..."
    bash build.sh
fi

# Build rag-chat
cd "$INSTALL_DIR/../mcp-store/rag-chat"
if [ -f "build.sh" ]; then
    echo "  → Building rag-chat..."
    bash build.sh
fi

echo ""
echo "▸ Step 7: Setting up PATH..."
echo ""

# Add to .bashrc if not already present
if ! grep -q "decyphertek-ai/cli/dist" "$HOME/.bashrc"; then
    echo "" >> "$HOME/.bashrc"
    echo "# Decyphertek.ai" >> "$HOME/.bashrc"
    echo "export PATH=\"\$HOME/decyphertek-ai/cli/dist:\$PATH\"" >> "$HOME/.bashrc"
    echo "alias decyphertek='decyphertek.ai'" >> "$HOME/.bashrc"
    echo "✓ Added to .bashrc"
else
    echo "✓ Already in .bashrc"
fi

# Export for current session
export PATH="$HOME/decyphertek-ai/cli/dist:$PATH"

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║                 INSTALLATION COMPLETE!                        ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "✓ Decyphertek.ai installed successfully!"
echo ""
echo "To launch the application:"
echo "  $ decyphertek.ai"
echo ""
echo "Or use the alias:"
echo "  $ decyphertek"
echo ""
echo "For future sessions, restart your shell or run:"
echo "  $ source ~/.bashrc"
echo ""

# Ask if user wants to launch now
read -p "Launch Decyphertek.ai now? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    "$HOME/decyphertek-ai/cli/dist/decyphertek.ai"
fi
