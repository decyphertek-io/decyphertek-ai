#!/bin/bash

set -e

# ============================================================
# Decyphertek AI CLI Build + GitHub Release Script
# Builds the CLI binary and uploads it to GitHub Releases
# Requires: gh (GitHub CLI), uv, git
# Usage: bash build-release.sh [version]
#   version defaults to v1.0.0 if not provided
# ============================================================

REPO="decyphertek-io/decyphertek-ai"
ASSET_NAME="decyphertek.ai"
VERSION="${1:-v1.0.0}"
DIST_PATH="dist/${ASSET_NAME}"

echo "=== Decyphertek AI CLI Build + Release Script ==="
echo "Version : ${VERSION}"
echo "Repo    : ${REPO}"
echo ""

# ── Preflight checks ──────────────────────────────────────
if ! command -v gh &> /dev/null; then
    echo "✗ gh (GitHub CLI) not found."
    echo "  Install: https://cli.github.com/"
    exit 1
fi

if ! command -v uv &> /dev/null; then
    echo "⚠ uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "✓ uv    : $(uv --version)"
echo "✓ gh    : $(gh --version | head -1)"
echo ""

# ── Build ─────────────────────────────────────────────────
echo "Installing dependencies with uv (Python 3.12)..."
uv venv --clear --python 3.12
source .venv/bin/activate
uv pip install pyinstaller cryptography pyyaml

echo ""
echo "Cleaning previous build..."
rm -rf dist build *.spec

echo ""
echo "Building executable with PyInstaller..."
pyinstaller --onefile \
    --name "${ASSET_NAME}" \
    --clean \
    cli-ai.py

echo ""
echo "Cleaning up build artifacts..."
rm -rf .venv build
find . -maxdepth 1 -name "*.spec" -delete

echo ""
echo "✓ Build complete: ${DIST_PATH}"

# ── GitHub Release ────────────────────────────────────────
echo ""
echo "Checking gh auth..."
gh auth status

echo ""
echo "Creating GitHub Release ${VERSION} and uploading ${ASSET_NAME}..."

# Create release (or update if it already exists) and upload asset
if gh release view "${VERSION}" --repo "${REPO}" &>/dev/null; then
    echo "Release ${VERSION} already exists — uploading asset (overwrite)..."
    gh release upload "${VERSION}" "${DIST_PATH}" \
        --repo "${REPO}" \
        --clobber
else
    gh release create "${VERSION}" "${DIST_PATH}" \
        --repo "${REPO}" \
        --title "Decyphertek AI CLI ${VERSION}" \
        --notes "Used and managed by decyphertek-ai."
fi

echo ""
echo "Cleaning up dist folder..."
rm -rf dist

echo ""
echo "✓ Release complete!"
echo "  https://github.com/${REPO}/releases/tag/${VERSION}"
