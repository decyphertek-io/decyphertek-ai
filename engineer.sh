#!/bin/bash

# Decyphertek AI Reverse Engineering Script
# This script downloads and extracts the PyInstaller bundle for debugging

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WORK_DIR="$HOME/.reverse-engineer"
GITHUB_RELEASE_URL="https://github.com/decyphertek-io/decyphertek-ai/releases/download/latest/decyphertek.ai"
APP_NAME="decyphertek.ai"

# Print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Install Poetry if not already installed
install_poetry() {
    if command -v poetry &> /dev/null; then
        print_success "Poetry is already installed"
        return
    fi
    
    print_info "Poetry not found. Installing python3-poetry..."
    
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y python3-poetry
        print_success "Poetry installed via apt"
    else
        print_warning "apt not found. Installing Poetry via pip..."
        pip install --user poetry
        print_success "Poetry installed via pip"
    fi
}

# Create working directory
create_work_dir() {
    print_info "Creating working directory at ${WORK_DIR}..."
    
    if [ -d "${WORK_DIR}" ]; then
        print_warning "Directory exists. Cleaning up old files..."
        rm -rf "${WORK_DIR}"
    fi
    
    mkdir -p "${WORK_DIR}"
    cd "${WORK_DIR}"
    print_success "Working directory created"
}

# Initialize Poetry project
init_poetry_project() {
    print_info "Initializing Poetry project..."
    
    # Create a minimal pyproject.toml
    cat > pyproject.toml <<EOF
[tool.poetry]
name = "reverse-engineer"
version = "0.1.0"
description = "Reverse engineering tools for PyInstaller bundles"
authors = ["Decyphertek"]

[tool.poetry.dependencies]
python = "^3.8"
pyinstxtractor-ng = "^2023.10"
uncompyle6 = "^3.9.1"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF
    
    print_success "Poetry project initialized"
}

# Install dependencies with Poetry
install_dependencies() {
    print_info "Installing reverse engineering tools with Poetry..."
    
    poetry install
    
    print_success "Dependencies installed"
}

# Download the executable
download_executable() {
    print_info "Downloading ${APP_NAME} from GitHub..."
    
    if wget -q "${GITHUB_RELEASE_URL}" -O "${APP_NAME}"; then
        print_success "Downloaded ${APP_NAME}"
        chmod +x "${APP_NAME}"
    else
        print_error "Failed to download ${APP_NAME}"
        print_info "URL: ${GITHUB_RELEASE_URL}"
        exit 1
    fi
}

# Extract PyInstaller bundle
extract_bundle() {
    print_info "Extracting PyInstaller bundle..."
    
    poetry run pyinstxtractor "${APP_NAME}"
    
    EXTRACTED_DIR="${APP_NAME}_extracted"
    
    if [ -d "${EXTRACTED_DIR}" ]; then
        print_success "Bundle extracted to ${EXTRACTED_DIR}"
    else
        print_error "Extraction failed - directory not found"
        exit 1
    fi
}

# Decompile PYC files
decompile_pyc_files() {
    print_info "Decompiling .pyc files..."
    
    EXTRACTED_DIR="${APP_NAME}_extracted"
    DECOMPILED_DIR="${WORK_DIR}/decompiled"
    
    mkdir -p "${DECOMPILED_DIR}"
    
    # Find all .pyc files and decompile them
    find "${EXTRACTED_DIR}" -name "*.pyc" -type f | while read -r pyc_file; do
        filename=$(basename "$pyc_file" .pyc)
        print_info "Decompiling: $filename"
        
        # Try to decompile (may fail for some files)
        poetry run uncompyle6 -o "${DECOMPILED_DIR}/${filename}.py" "$pyc_file" 2>/dev/null || \
            print_warning "Could not decompile: $filename"
    done
    
    print_success "Decompilation complete. Check ${DECOMPILED_DIR}"
}

# Display results
display_results() {
    echo ""
    print_success "Reverse engineering completed!"
    echo ""
    echo -e "${GREEN}Working Directory:${NC}"
    echo -e "  ${BLUE}${WORK_DIR}${NC}"
    echo ""
    echo -e "${GREEN}Extracted Files:${NC}"
    echo -e "  ${BLUE}${WORK_DIR}/${APP_NAME}_extracted/${NC}"
    echo ""
    echo -e "${GREEN}Decompiled Python Files:${NC}"
    echo -e "  ${BLUE}${WORK_DIR}/decompiled/${NC}"
    echo ""
    echo -e "${YELLOW}Note:${NC} Decompilation may not be perfect for all files."
    echo "Review the decompiled code carefully and compare with your original source."
    echo ""
    echo -e "${GREEN}Next Steps:${NC}"
    echo -e "  ${BLUE}cd ${WORK_DIR}${NC}"
    echo -e "  ${BLUE}ls -la ${APP_NAME}_extracted/${NC}  - View extracted files"
    echo -e "  ${BLUE}ls -la decompiled/${NC}             - View decompiled Python files"
    echo ""
}

# Main process
main() {
    echo ""
    echo "========================================="
    echo "  Decyphertek AI Reverse Engineering"
    echo "========================================="
    echo ""
    
    install_poetry
    create_work_dir
    init_poetry_project
    install_dependencies
    download_executable
    extract_bundle
    decompile_pyc_files
    display_results
}

# Run main function
main
