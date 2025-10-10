#!/bin/bash

# Decyphertek AI Installer with systemd support
# This script downloads, installs, and sets up decyphertek.ai as a systemd service

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
SERVICE_NAME="decyphertek.ai"
GITHUB_REPO="decyphertek-io/decyphertek-ai"
DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/releases/latest/download/${APP_NAME}"
SYSTEMD_SERVICE="/etc/systemd/system/${SERVICE_NAME}.service"

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
    
    if ! command -v systemctl &> /dev/null; then
        print_warning "systemd not found. Service management will not be available."
        SYSTEMD_AVAILABLE=false
    else
        SYSTEMD_AVAILABLE=true
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

# Create systemd service file
create_systemd_service() {
    if [ "$SYSTEMD_AVAILABLE" = false ]; then
        print_warning "Skipping systemd service creation (systemd not available)"
        return
    fi
    
    print_info "Creating systemd service file..."
    
    cat > "${SYSTEMD_SERVICE}" <<EOF
[Unit]
Description=Decyphertek AI Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/${APP_NAME}
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    print_success "Systemd service file created at ${SYSTEMD_SERVICE}"
}

# Reload systemd daemon
setup_systemd_service() {
    if [ "$SYSTEMD_AVAILABLE" = false ]; then
        return
    fi
    
    print_info "Reloading systemd daemon..."
    systemctl daemon-reload
    
    print_success "Systemd service configured (not enabled by default)"
}

# Display completion message
display_completion() {
    echo ""
    print_success "Installation completed successfully!"
    echo ""
    
    echo -e "${GREEN}Run the application:${NC}"
    echo -e "  ${BLUE}${INSTALL_DIR}/${APP_NAME}${NC}  - Run directly"
    echo ""
    
    if [ "$SYSTEMD_AVAILABLE" = true ]; then
        echo -e "${GREEN}Or manage as a service (optional):${NC}"
        echo -e "  ${BLUE}sudo systemctl start ${SERVICE_NAME}.service${NC}    - Start the service"
        echo -e "  ${BLUE}sudo systemctl stop ${SERVICE_NAME}.service${NC}     - Stop the service"
        echo -e "  ${BLUE}sudo systemctl restart ${SERVICE_NAME}.service${NC}  - Restart the service"
        echo -e "  ${BLUE}sudo systemctl status ${SERVICE_NAME}.service${NC}   - Check service status"
        echo -e "  ${BLUE}sudo systemctl enable ${SERVICE_NAME}.service${NC}   - Enable on boot (if desired)"
        echo -e "  ${BLUE}sudo systemctl disable ${SERVICE_NAME}.service${NC}  - Disable on boot"
        echo ""
        echo -e "${GREEN}View logs:${NC}"
        echo -e "  ${BLUE}sudo journalctl -u ${SERVICE_NAME}.service -f${NC}  - Follow logs in real-time"
        echo -e "  ${BLUE}sudo journalctl -u ${SERVICE_NAME}.service${NC}     - View all logs"
    fi
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
    create_systemd_service
    setup_systemd_service
    display_completion
}

# Run main function
main
