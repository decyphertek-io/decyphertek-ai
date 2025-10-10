#!/bin/bash

# Decyphertek AI Uninstaller
# This script removes decyphertek.ai and its desktop launcher

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

# Confirm uninstallation
confirm_uninstall() {
    echo ""
    print_warning "This will remove Decyphertek AI and all associated files."
    echo ""
    read -p "Are you sure you want to uninstall? (y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Uninstallation cancelled."
        exit 0
    fi
}

# Remove the application
remove_app() {
    if [ -f "${INSTALL_DIR}/${APP_NAME}" ]; then
        print_info "Removing application from ${INSTALL_DIR}/${APP_NAME}..."
        rm -f "${INSTALL_DIR}/${APP_NAME}"
        print_success "Application removed"
    else
        print_warning "Application not found at ${INSTALL_DIR}/${APP_NAME}"
    fi
}

# Remove desktop launcher
remove_desktop_launcher() {
    if [ -f "${DESKTOP_FILE}" ]; then
        print_info "Removing desktop launcher..."
        rm -f "${DESKTOP_FILE}"
        print_success "Desktop launcher removed"
    else
        print_warning "Desktop launcher not found at ${DESKTOP_FILE}"
    fi
}

# Remove user data directory
remove_user_data() {
    # Get the actual user's home directory (not root's)
    if [ -n "$SUDO_USER" ]; then
        USER_HOME=$(eval echo ~$SUDO_USER)
    else
        USER_HOME="$HOME"
    fi
    
    USER_DATA_DIR="${USER_HOME}/.decyphertek-ai"
    
    if [ -d "${USER_DATA_DIR}" ]; then
        print_info "Removing user data directory at ${USER_DATA_DIR}..."
        rm -rf "${USER_DATA_DIR}"
        print_success "User data directory removed"
    else
        print_warning "User data directory not found at ${USER_DATA_DIR}"
    fi
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
    print_success "Uninstallation completed successfully!"
    echo ""
    echo -e "${GREEN}Decyphertek AI has been removed from your system.${NC}"
    echo ""
    echo -e "${YELLOW}Note:${NC} If you had desktop shortcuts or panel launchers,"
    echo "you may need to remove them manually."
    echo ""
}

# Main uninstallation process
main() {
    echo ""
    echo "========================================="
    echo "  Decyphertek AI Uninstaller"
    echo "========================================="
    echo ""
    
    check_root
    confirm_uninstall
    remove_app
    remove_desktop_launcher
    remove_user_data
    update_desktop_database
    display_completion
}

# Run main function
main
