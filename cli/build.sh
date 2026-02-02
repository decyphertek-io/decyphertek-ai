#!/bin/bash

set -e

echo "=== Decyphertek AI Build Script ==="
echo ""

if ! command -v uv &> /dev/null; then
    echo "⚠ uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "✓ uv: $(uv --version)"
echo ""

echo "Installing dependencies with uv (Python 3.12)..."
uv venv --clear --python 3.12
source .venv/bin/activate
uv pip install pyinstaller cryptography

echo ""
echo "Building executable with PyInstaller..."
pyinstaller --onefile \
    --name decyphertek-cli.ai \
    --clean \
    cli-ai.py

echo ""
echo "Cleaning up build artifacts..."
rm -rf .venv build *.spec

echo ""
echo "✓ Build complete! Executable: dist/decyphertek-cli.ai"
echo "✓ Clean build - no .venv or artifacts left behind"
