#!/bin/bash

# Discord Bot Scoped Launch Script
# Starts the read-only presentation Discord bot with proper environment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if virtual environment exists and activate it
check_venv() {
    local venv_path="$PROJECT_ROOT/venv"

    if [[ ! -d "$venv_path" ]]; then
        log_warning "Virtual environment not found at $venv_path"
        log_info "Creating virtual environment..."
        python3 -m venv "$venv_path"
    fi

    log_info "Activating virtual environment..."
    source "$venv_path/bin/activate"
    log_success "Virtual environment activated"
}

# Install dependencies if needed
install_deps() {
    log_info "Checking dependencies..."

    # Check if discord.py is installed
    if ! python -c "import discord" 2>/dev/null; then
        log_warning "Discord.py not found, installing..."
        pip install discord.py
    fi

    # Check if dotenv is installed
    if ! python -c "import dotenv" 2>/dev/null; then
        log_warning "python-dotenv not found, installing..."
        pip install python-dotenv
    fi

    log_success "Dependencies verified"
}

# Check environment variables
check_env() {
    log_info "Checking environment configuration..."

    # Load .env file if it exists
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        source "$PROJECT_ROOT/.env"
        log_success "Loaded .env file"
    else
        log_warning ".env file not found"
    fi

    # Check required environment variables
    if [[ -z "${DISCORD_BOT_TOKEN:-}" ]]; then
        log_error "DISCORD_BOT_TOKEN not set"
        log_info "Please set DISCORD_BOT_TOKEN in your environment or .env file"
        exit 1
    fi

    log_success "Environment variables validated"
}

# Set default feature flags for scoped operation
set_feature_flags() {
    log_info "Setting feature flags for scoped operation..."

    # Core processing flags
    export ENABLE_INGEST_CONCURRENT="${ENABLE_INGEST_CONCURRENT:-1}"
    export ENABLE_HTTP_RETRY="${ENABLE_HTTP_RETRY:-1}"
    export ENABLE_RL_GLOBAL="${ENABLE_RL_GLOBAL:-1}"
    export ENABLE_RL_ROUTING="${ENABLE_RL_ROUTING:-1}"

    # Analysis flags
    export ENABLE_ANALYSIS_SENTIMENT="${ENABLE_ANALYSIS_SENTIMENT:-1}"
    export ENABLE_ANALYSIS_CLAIMS="${ENABLE_ANALYSIS_CLAIMS:-1}"
    export ENABLE_ANALYSIS_TOPICS="${ENABLE_ANALYSIS_TOPICS:-1}"
    export ENABLE_ANALYSIS_FALLACIES="${ENABLE_ANALYSIS_FALLACIES:-1}"

    # Memory and storage flags
    export ENABLE_MEMORY_QDRANT="${ENABLE_MEMORY_QDRANT:-0}"  # Use in-mem for scoped mode
    export ENABLE_MEMORY_ARCHIVER="${ENABLE_MEMORY_ARCHIVER:-1}"
    export ENABLE_MEMORY_RETENTION="${ENABLE_MEMORY_RETENTION:-1}"

    # Privacy and compliance flags
    export ENABLE_PII_DETECTION="${ENABLE_PII_DETECTION:-1}"
    export ENABLE_CONTENT_MODERATION="${ENABLE_CONTENT_MODERATION:-1}"
    export ENABLE_AUDIT_LOGGING="${ENABLE_AUDIT_LOGGING:-1}"

    log_success "Feature flags configured for scoped operation"
}

# Show startup information
show_startup_info() {
    echo ""
    echo -e "${BLUE}🤖 Starting Scoped Discord Intelligence Bot${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
    log_info "Mode: Read-Only Presentation"
    log_info "Command Families: /system-*, !ops-*, !dev-*, !analytics-*"
    log_info "Analysis: Off-platform processing only"
    log_info "Access: Limited scope, no direct tool exposure"
    echo ""
    log_info "Available commands:"
    echo "  📊 System:     /system-status, /system-tools, /system-performance, /system-audit"
    echo "  🔧 Operations: !ops-status, !ops-queue, !ops-metrics"
    echo "  🛠️  Development: !dev-tools, !dev-agents, !dev-test"
    echo "  📈 Analytics:  !analytics-usage, !analytics-performance, !analytics-errors"
    echo ""
}

# Main execution
main() {
    log_info "Initializing scoped Discord bot..."

    # Change to project root
    cd "$PROJECT_ROOT"

    # Setup environment
    check_venv
    install_deps
    check_env
    set_feature_flags

    # Show startup information
    show_startup_info

    # Launch the scoped bot
    log_info "Launching scoped Discord bot..."
    exec python "$SCRIPT_DIR/scoped_discord_bot.py"
}

# Handle signals
trap 'log_warning "Received shutdown signal"; exit 0' SIGINT SIGTERM

# Run main function
main "$@"
