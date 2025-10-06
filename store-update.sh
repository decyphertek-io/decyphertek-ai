#!/bin/bash

# Store Update Script for DecypherTek AI
# Syncs updated files to agent-store, mcp-store, and app-store repositories

echo "🔄 DecypherTek AI Store Update Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "src/store/agent/adminotaur/adminotaur.py" ]; then
    print_error "Please run this script from the decyphertek-ai root directory"
    exit 1
fi

print_status "Starting store synchronization..."

# 1. Agent Store - Adminotaur
print_status "Syncing Adminotaur to agent-store..."
if [ -d "/home/adminotaur/Documents/git/agent-store/adminotaur" ]; then
    cp src/store/agent/adminotaur/adminotaur.py /home/adminotaur/Documents/git/agent-store/adminotaur/adminotaur.py
    cp src/store/agent/adminotaur/adminotaur.md /home/adminotaur/Documents/git/agent-store/adminotaur/adminotaur.md
    print_success "Adminotaur files synced to agent-store"
else
    print_warning "agent-store directory not found at /home/adminotaur/Documents/git/agent-store/adminotaur"
fi

# 2. MCP Store - RAG
print_status "Syncing RAG to mcp-store..."
if [ -d "/home/adminotaur/Documents/git/mcp-store/servers/rag" ]; then
    cp src/store/mcp/rag/rag.py /home/adminotaur/Documents/git/mcp-store/servers/rag/rag.py
    cp src/store/mcp/rag/requirements.txt /home/adminotaur/Documents/git/mcp-store/servers/rag/requirements.txt
    print_success "RAG files synced to mcp-store"
else
    print_warning "mcp-store rag directory not found at /home/adminotaur/Documents/git/mcp-store/servers/rag"
fi

# 3. MCP Store - Web Search (if updated)
print_status "Syncing Web Search to mcp-store..."
if [ -d "/home/adminotaur/Documents/git/mcp-store/servers/web-search" ]; then
    cp src/store/mcp/web-search/web.py /home/adminotaur/Documents/git/mcp-store/servers/web-search/web.py
    cp src/store/mcp/web-search/requirements.txt /home/adminotaur/Documents/git/mcp-store/servers/web-search/requirements.txt
    print_success "Web Search files synced to mcp-store"
else
    print_warning "mcp-store web-search directory not found at /home/adminotaur/Documents/git/mcp-store/servers/web-search"
fi

# 4. App Store - app.json (if updated)
print_status "Syncing app.json to app-store..."
if [ -d "/home/adminotaur/Documents/git/app-store" ]; then
    # Only sync if we have a local app.json to sync
    if [ -f "app.json" ]; then
        cp app.json /home/adminotaur/Documents/git/app-store/app.json
        print_success "app.json synced to app-store"
    else
        print_status "No local app.json found to sync"
    fi
else
    print_warning "app-store directory not found at /home/adminotaur/Documents/git/app-store"
fi

echo ""
print_success "Store synchronization complete!"
echo ""
print_status "Synced files:"
echo "  📁 Agent Store: adminotaur.py, adminotaur.md"
echo "  📁 MCP Store: rag.py, rag.py requirements.txt"
echo "  📁 MCP Store: web-search.py, web-search requirements.txt"
echo "  📁 App Store: app.json (if present)"
echo ""
print_status "You can now commit and push changes to the respective repositories"
