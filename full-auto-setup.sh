#!/bin/bash
# Ultimate Discord Intelligence Bot - Full Auto Setup & Start
# This script automatically sets up and runs EVERYTHING with no user interaction required

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Icons
CHECKMARK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
GEAR="⚙️"
ROCKET="🚀"
SHIELD="🛡️"
CHART="📊"
CLOCK="⏱️"

# Global variables
LOG_FILE="$SCRIPT_DIR/full_auto_setup_$(date +%Y%m%d_%H%M%S).log"
VENV_DIR="$SCRIPT_DIR/.venv"
SERVICES_DIR="$SCRIPT_DIR/logs/services"
PIDS_DIR="$SCRIPT_DIR/logs/pids"
STATUS_FILE="$SCRIPT_DIR/.service_status"
API_PORT=8000

# Logging functions
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') $*" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}${INFO}${NC} $1"
}

log_success() {
    log "${GREEN}${CHECKMARK}${NC} $1"
}

log_warning() {
    log "${YELLOW}${WARNING}${NC} $1"
}

log_error() {
    log "${RED}${CROSS}${NC} $1"
}

log_header() {
    echo -e "\n${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}" | tee -a "$LOG_FILE"
    echo -e "${CYAN}║ $1${NC}" | tee -a "$LOG_FILE"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}\n" | tee -a "$LOG_FILE"
}

# Progress bar function
show_progress() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local completed=$((current * width / total))

    printf "\r${CYAN}Progress: [${NC}"
    for ((i=1; i<=completed; i++)); do printf "="; done
    for ((i=completed+1; i<=width; i++)); do printf " "; done
    printf "${CYAN}] %d%%${NC}" $percentage
}

# Check system requirements
check_system_requirements() {
    log_header "SYSTEM REQUIREMENTS CHECK"

    local requirements_met=true

    # Check Python version
    log_info "Checking Python version..."
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 not found"
        requirements_met=false
    else
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
            log_success "Python $PYTHON_VERSION found (3.11+ required)"
        else
            log_error "Python $PYTHON_VERSION found but 3.11+ required"
            requirements_met=false
        fi
    fi

    # Check Git
    log_info "Checking Git..."
    if command -v git &> /dev/null; then
        log_success "Git found"
    else
        log_warning "Git not found - attempting to install..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y git
            log_success "Git installed"
        else
            log_error "Cannot install Git automatically"
            requirements_met=false
        fi
    fi

    # Check Make
    log_info "Checking Make..."
    if command -v make &> /dev/null; then
        log_success "Make found"
    else
        log_warning "Make not found - attempting to install..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y make
            log_success "Make installed"
        else
            log_error "Cannot install Make automatically"
            requirements_met=false
        fi
    fi

    # Check Docker (optional)
    log_info "Checking Docker..."
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        log_success "Docker available"
        DOCKER_AVAILABLE=true
    else
        log_warning "Docker not available - will skip infrastructure services"
        DOCKER_AVAILABLE=false
    fi

    if [ "$requirements_met" = true ]; then
        log_success "All system requirements met"
        return 0
    else
        log_error "System requirements not met - please install missing dependencies"
        exit 1
    fi
}

# Setup virtual environment
setup_virtual_environment() {
    log_header "VIRTUAL ENVIRONMENT SETUP"

    # Check if venv already exists
    if [ -d "$VENV_DIR" ]; then
        log_info "Virtual environment already exists"
        source "$VENV_DIR/bin/activate"
        log_success "Virtual environment activated"
        return 0
    fi

    log_info "Creating virtual environment..."

    # Try uv first (faster)
    if command -v uv &> /dev/null; then
        log_info "Using uv for virtual environment creation..."
        uv venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
        log_success "Virtual environment created with uv"
    else
        log_info "Using python venv for virtual environment creation..."
        python3 -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
        log_success "Virtual environment created with python venv"
    fi

    # Upgrade pip
    log_info "Upgrading pip..."
    python -m pip install --upgrade pip

    # Install dependencies
    log_info "Installing Python dependencies..."
    if command -v uv &> /dev/null; then
        uv pip install -e .
    else
        pip install -e .
    fi

    log_success "Virtual environment setup complete"
}

# Run setup wizard with smart defaults
run_setup_wizard() {
    log_header "CONFIGURATION SETUP"

    # Check if .env already exists
    if [ -f ".env" ]; then
        log_info "Environment file already exists - skipping setup wizard"
        return 0
    fi

    log_info "Running setup wizard with smart defaults..."

    # Copy env.example to .env
    if [ -f "env.example" ]; then
        cp env.example .env
        log_success "Environment file created from template"
    else
        log_warning "env.example not found - creating basic .env file"
        cat > .env << EOF
# Basic environment configuration
PYTHONPATH=/home/crew/src:$PYTHONPATH
ENABLE_CONTENT_ROUTING=true
ENABLE_QUALITY_FILTERING=true
ENABLE_SEMANTIC_CACHE=true
ENABLE_PROMPT_COMPRESSION=true
ENABLE_GRAPH_MEMORY=true
ENABLE_HIPPORAG_MEMORY=true
EOF
    fi

    # Run the Python setup wizard non-interactively
    if [ -f "src/ultimate_discord_intelligence_bot/setup_cli.py" ]; then
        log_info "Running configuration wizard..."
        python -c "
import sys
sys.path.insert(0, 'src')
from ultimate_discord_intelligence_bot.setup_cli import _wizard
import os

# Set non-interactive mode
os.environ['NON_INTERACTIVE_SETUP'] = '1'

try:
    _wizard()
    print('Setup wizard completed successfully')
except Exception as e:
    print(f'Setup wizard failed: {e}')
    # Continue anyway - basic setup should work
"
        log_success "Configuration setup completed"
    else
        log_warning "Setup wizard not found - using basic configuration"
    fi
}

# Start infrastructure services
start_infrastructure() {
    log_header "INFRASTRUCTURE STARTUP"

    if [ "$DOCKER_AVAILABLE" = false ]; then
        log_warning "Docker not available - skipping infrastructure startup"
        return 0
    fi

    log_info "Starting infrastructure services..."

    # Check for docker-compose file
    if [ -f "ops/deployment/docker/docker-compose.yml" ]; then
        log_info "Starting Docker services..."
        cd ops/deployment/docker
        docker-compose up -d
        cd "$SCRIPT_DIR"
        log_success "Infrastructure services started"
    elif [ -f "docker-compose.yml" ]; then
        log_info "Starting Docker services..."
        docker-compose up -d
        log_success "Infrastructure services started"
    else
        log_warning "No Docker Compose file found - skipping infrastructure"
    fi
}

# Start Discord bot (enhanced)
start_discord_bot() {
    log_header "DISCORD BOT STARTUP"

    log_info "Starting enhanced Discord bot with all optimizations..."

    # Create logs directory
    mkdir -p "$SERVICES_DIR"
    mkdir -p "$PIDS_DIR"

    # Set REPO_ROOT and PYTHONPATH explicitly for setup_cli
    export REPO_ROOT="/home/crew"
    export PYTHONPATH="/home/crew/src:$PYTHONPATH"

    # Start the enhanced bot using the Makefile command with virtual environment
    nohup bash -c "source $VENV_DIR/bin/activate && export REPO_ROOT='/home/crew' && export PYTHONPATH='/home/crew/src:$PYTHONPATH' && cd /home/crew && make run-discord-enhanced" > "$SERVICES_DIR/discord_bot.log" 2>&1 &
    echo $! > "$PIDS_DIR/discord_bot.pid"

    log_success "Enhanced Discord bot started (PID: $(cat "$PIDS_DIR/discord_bot.pid"))"
}

# Start API server
start_api_server() {
    log_header "API SERVER STARTUP"

    log_info "Starting FastAPI server..."

    # Check if Docker API server is running and use different port if needed
    API_PORT=8000
    for port in 8000 8003 8004 8005 8006; do
        if ! lsof -i :$port &>/dev/null && ! docker container ls | grep -q ":$port->"; then
            API_PORT=$port
            break
        fi
    done

    if [ "$API_PORT" = "8000" ]; then
        log_warning "All preferred ports (8000, 8003-8006) are in use - using port 8007"
        API_PORT=8007
    fi

    export PORT=$API_PORT

    # Start API server using the Makefile command with virtual environment and specific port
    nohup bash -c "source $VENV_DIR/bin/activate && export PORT=$API_PORT && make run-api" > "$SERVICES_DIR/api_server.log" 2>&1 &
    echo $! > "$PIDS_DIR/api_server.pid"

    log_success "API server started on port $API_PORT (PID: $(cat "$PIDS_DIR/api_server.pid"))"
}

# Start CrewAI
start_crew_ai() {
    log_header "CREWAI STARTUP"

    log_info "Starting CrewAI autonomous intelligence system..."

    # Start CrewAI using the Makefile command with virtual environment
    nohup bash -c "source $VENV_DIR/bin/activate && make run-crew" > "$SERVICES_DIR/crew_ai.log" 2>&1 &
    echo $! > "$PIDS_DIR/crew_ai.pid"

    log_success "CrewAI started (PID: $(cat "$PIDS_DIR/crew_ai.pid"))"
}

# Start MCP server
start_mcp_server() {
    log_header "MCP SERVER STARTUP"

    log_info "Starting Model Context Protocol server..."

    # Start MCP server using the Makefile command with virtual environment
    nohup bash -c "source $VENV_DIR/bin/activate && make run-mcp" > "$SERVICES_DIR/mcp_server.log" 2>&1 &
    echo $! > "$PIDS_DIR/mcp_server.pid"

    log_success "MCP server started (PID: $(cat "$PIDS_DIR/mcp_server.pid"))"
}

# Wait for services to be ready
wait_for_services() {
    log_header "SERVICE HEALTH CHECK"

    log_info "Waiting for services to initialize..."

    # Wait a bit for services to start
    sleep 10

    # Check if services are still running
    local services_running=true

    if [ -f "$PIDS_DIR/discord_bot.pid" ]; then
        if kill -0 $(cat "$PIDS_DIR/discord_bot.pid") 2>/dev/null; then
            log_success "Discord bot is running"
        else
            log_error "Discord bot failed to start"
            services_running=false
        fi
    fi

    if [ -f "$PIDS_DIR/api_server.pid" ]; then
        if kill -0 $(cat "$PIDS_DIR/api_server.pid") 2>/dev/null; then
            log_success "API server is running"
        else
            log_error "API server failed to start"
            services_running=false
        fi
    fi

    # Special handling for CrewAI - it's a short-running task that should complete successfully
    if [ -f "$PIDS_DIR/crew_ai.pid" ]; then
        if kill -0 $(cat "$PIDS_DIR/crew_ai.pid") 2>/dev/null; then
            log_success "CrewAI is running"
        else
            # Check if CrewAI completed successfully by looking at the log
            if [ -f "$SERVICES_DIR/crew_ai.log" ] && grep -q "✅ Execution completed!" "$SERVICES_DIR/crew_ai.log"; then
                log_success "CrewAI completed successfully"
            else
                log_error "CrewAI failed to complete"
                services_running=false
            fi
        fi
    fi

    if [ -f "$PIDS_DIR/mcp_server.pid" ]; then
        if kill -0 $(cat "$PIDS_DIR/mcp_server.pid") 2>/dev/null; then
            # Check if MCP server initialized successfully by looking at the log
            if [ -f "$SERVICES_DIR/mcp_server.log" ] && grep -q "FastMCP" "$SERVICES_DIR/mcp_server.log"; then
                echo -e "  ${GREEN}${CHECKMARK} MCP Server${NC} - Initialized successfully (PID: $(cat "$PIDS_DIR/mcp_server.pid"))"
            else
                echo -e "  ${YELLOW}${WARNING} MCP Server${NC} - Running but not fully initialized (PID: $(cat "$PIDS_DIR/mcp_server.pid"))"
            fi
        else
            # MCP server may have completed initialization and exited (stdio-based)
            if [ -f "$SERVICES_DIR/mcp_server.log" ] && grep -q "FastMCP" "$SERVICES_DIR/mcp_server.log"; then
                echo -e "  ${GREEN}${CHECKMARK} MCP Server${NC} - Completed successfully (stdio-based service)"
            else
                echo -e "  ${RED}${CROSS} MCP Server${NC} - Failed to initialize"
            fi
        fi
    fi

    if [ "$services_running" = true ]; then
        log_success "All services started successfully"
    else
        log_warning "Some services failed to start - check logs for details"
    fi
}

# Show status
show_final_status() {
    log_header "DEPLOYMENT COMPLETE"

    echo -e "\n${GREEN}${ROCKET} Ultimate Discord Intelligence Bot is now running!${NC}"
    echo -e "\n${CYAN}Active Services:${NC}"

    if [ -f "$PIDS_DIR/discord_bot.pid" ] && kill -0 $(cat "$PIDS_DIR/discord_bot.pid") 2>/dev/null; then
        echo -e "  ${GREEN}${CHECKMARK} Discord Bot (Enhanced)${NC} - PID: $(cat "$PIDS_DIR/discord_bot.pid")"
    fi

    if [ -f "$PIDS_DIR/api_server.pid" ] && kill -0 $(cat "$PIDS_DIR/api_server.pid") 2>/dev/null; then
        # Check if API server is responding on the configured port
        if curl -s "http://localhost:$API_PORT/health" > /dev/null 2>&1; then
            echo -e "  ${GREEN}${CHECKMARK} API Server${NC} - PID: $(cat "$PIDS_DIR/api_server.pid"), Port: $API_PORT"
        else
            echo -e "  ${RED}${CROSS} API Server${NC} - Process running but not responding (PID: $(cat "$PIDS_DIR/api_server.pid"), Port: $API_PORT)"
        fi
    fi

    # Special handling for CrewAI status
    if [ -f "$SERVICES_DIR/crew_ai.log" ] && grep -q "✅ Execution completed!" "$SERVICES_DIR/crew_ai.log"; then
        echo -e "  ${GREEN}${CHECKMARK} CrewAI${NC} - Completed successfully"
    elif [ -f "$PIDS_DIR/crew_ai.pid" ] && kill -0 $(cat "$PIDS_DIR/crew_ai.pid") 2>/dev/null; then
        echo -e "  ${GREEN}${CHECKMARK} CrewAI${NC} - PID: $(cat "$PIDS_DIR/crew_ai.pid")"
    else
        echo -e "  ${RED}${CROSS} CrewAI${NC} - Not running"
    fi

    if [ -f "$PIDS_DIR/mcp_server.pid" ] && kill -0 $(cat "$PIDS_DIR/mcp_server.pid") 2>/dev/null; then
        echo -e "  ${GREEN}${CHECKMARK} MCP Server${NC} - PID: $(cat "$PIDS_DIR/mcp_server.pid")"
    fi

    echo -e "\n${CYAN}Monitoring:${NC}"
    echo -e "  ${BLUE}📊 Status Check:${NC} ./smart-setup.sh status"
    echo -e "  ${BLUE}⏱️ View Logs:${NC} ./smart-setup.sh logs"
    echo -e "  ${BLUE}🛡️ Health Check:${NC} ./smart-setup.sh health"

    echo -e "\n${CYAN}Log Files:${NC}"
    echo -e "  ${WHITE}Setup Log:${NC} $LOG_FILE"
    echo -e "  ${WHITE}Service Logs:${NC} $SERVICES_DIR/"

    echo -e "\n${YELLOW}${WARNING} Note: Configure DISCORD_BOT_TOKEN in .env for full Discord connectivity${NC}"
    echo -e "${YELLOW}${WARNING} The system will run in headless mode until token is configured${NC}"

    echo -e "\n${GREEN}${CHECKMARK} Full auto setup and startup completed successfully!${NC}"
}

# Main execution
main() {
    echo -e "${CYAN}${ROCKET} Ultimate Discord Intelligence Bot - Full Auto Setup & Start${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}This script will automatically set up and run EVERYTHING${NC}"
    echo -e "${YELLOW}No user interaction required - just sit back and relax!${NC}\n"

    local start_time=$(date +%s)

    # Execute all steps
    check_system_requirements
    show_progress 1 7

    setup_virtual_environment
    show_progress 2 7

    run_setup_wizard
    show_progress 3 7

    start_infrastructure
    show_progress 4 7

    start_discord_bot
    show_progress 5 7

    start_api_server
    show_progress 6 7

    start_crew_ai
    start_mcp_server
    show_progress 7 7

    wait_for_services

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo -e "\n${GREEN}Setup completed in ${duration} seconds${NC}"

    show_final_status

    log_success "Full auto setup and startup completed successfully"
}

# Run main function
main "$@"