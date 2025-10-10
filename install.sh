#!/bin/bash

# Decyphertek AI Installer
# This script downloads, installs, and creates a desktop launcher for decyphertek.ai

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt"
APP_NAME="decyphertek.ai"
GITHUB_REPO="decyphertek-io/decyphertek-ai"
DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/releases/latest/download/${APP_NAME}"
DESKTOP_FILE="/usr/share/applications/decyphertek-ai.desktop"

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

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Check for required commands
check_dependencies() {
    print_info "Checking dependencies..."
    
    if ! command -v curl &> /dev/null; then
        print_error "curl is not installed. Please install it first:"
        echo "  Ubuntu/Debian: sudo apt install curl"
        echo "  Fedora/RHEL: sudo dnf install curl"
        echo "  Arch: sudo pacman -S curl"
        exit 1
    fi
    
    print_success "Dependencies check passed"
}

# Download the application
download_app() {
    print_info "Downloading ${APP_NAME}..."
    
    if curl -L -f -s "${DOWNLOAD_URL}" -o "${INSTALL_DIR}/${APP_NAME}"; then
        print_success "Downloaded ${APP_NAME}"
    else
        print_error "Failed to download ${APP_NAME}"
        print_info "Please check if the release exists at: ${DOWNLOAD_URL}"
        exit 1
    fi
}

# Set permissions
set_permissions() {
    print_info "Setting executable permissions..."
    chmod +x "${INSTALL_DIR}/${APP_NAME}"
    print_success "Permissions set"
}

# Create desktop launcher
create_desktop_launcher() {
    print_info "Creating desktop launcher..."
    
    cat > "${DESKTOP_FILE}" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Decyphertek AI
Comment=Decyphertek AI Application
Exec=${INSTALL_DIR}/${APP_NAME}
Icon=applications-science
Terminal=false
Categories=Utility;Application;
Keywords=decyphertek;ai;
StartupNotify=true
EOF
    
    chmod +x "${DESKTOP_FILE}"
    print_success "Desktop launcher created at ${DESKTOP_FILE}"
}

# Update desktop database
update_desktop_database() {
    print_info "Updating desktop database..."
    
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database /usr/share/applications/ 2>/dev/null || true
        print_success "Desktop database updated"
    else
        print_warning "update-desktop-database not found, skipping database update"
    fi
}

# Display completion message
display_completion() {
    echo ""
    print_success "Installation completed successfully!"
    echo ""
    echo -e "${GREEN}The application has been installed to:${NC}"
    echo -e "  ${BLUE}${INSTALL_DIR}/${APP_NAME}${NC}"
    echo ""
    echo -e "${GREEN}A desktop launcher has been created!${NC}"
    echo -e "  ${BLUE}Look for 'Decyphertek AI' in your application menu${NC}"
    echo ""
    echo -e "${GREEN}You can also:${NC}"
    echo -e "  ${BLUE}1.${NC} Find it in your XFCE application menu"
    echo -e "  ${BLUE}2.${NC} Right-click on desktop > Create Launcher > Browse to find 'Decyphertek AI'"
    echo -e "  ${BLUE}3.${NC} Run directly from terminal: ${BLUE}${INSTALL_DIR}/${APP_NAME}${NC}"
    echo ""
}

# Main installation process
main() {
    echo ""
    echo "========================================="
    echo "  Decyphertek AI Installer"
    echo "========================================="
    echo ""
    
    check_root
    check_dependencies
    download_app
    set_permissions
    create_desktop_launcher
    update_desktop_database
    display_completion
}

# Run main function
main
