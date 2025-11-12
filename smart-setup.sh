#!/bin/bash
# Ultimate Discord Intelligence Bot - Smart Setup & Start Script
# This script provides comprehensive setup and intelligent service management
# for the complete Discord Intelligence Bot ecosystem

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
LOG_FILE="$SCRIPT_DIR/setup_start_$(date +%Y%m%d_%H%M%S).log"
SERVICES_DIR="$SCRIPT_DIR/logs/services"
PIDS_DIR="$SCRIPT_DIR/logs/pids"
STATUS_FILE="$SCRIPT_DIR/.service_status"
DOCKER_COMPOSE_FILE="$SCRIPT_DIR/ops/deployment/docker/docker-compose.yml"

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
    echo -e "\n${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}" | tee -a "$LOG_FILE"
    echo -e "${BLUE}║${NC} ${WHITE}$1${NC}${BLUE}$(printf '%*s' $((55-${#1})) '')║${NC}" | tee -a "$LOG_FILE"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}\n" | tee -a "$LOG_FILE"
}

# Progress tracking
show_progress() {
    local current=$1
    local total=$2
    local message=$3
    local percent=$((current * 100 / total))
    local progress_bar=""

    for ((i=0; i<50; i++)); do
        if ((i < percent/2)); then
            progress_bar+="█"
        else
            progress_bar+="░"
        fi
    done

    echo -ne "\r${CYAN}[${progress_bar}] ${percent}%${NC} $message"
}

# Service status management
save_service_status() {
    local service=$1
    local status=$2
    local pid=${3:-""}
    echo "$service:$status:$(date +%s):$pid" >> "$STATUS_FILE"
}

get_service_status() {
    local service=$1
    if [ -f "$STATUS_FILE" ]; then
        grep "^$service:" "$STATUS_FILE" | tail -1 | cut -d: -f2
    fi
}

# System requirement checks
check_system_requirements() {
    log_header "SYSTEM REQUIREMENTS CHECK"

    local requirements_met=true
    local step=1
    local total_steps=8

    show_progress $step $total_steps "Checking Python version..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        if [[ "$(printf '%s\n' "$PYTHON_VERSION" "3.11" | sort -V | head -n1)" = "3.11" ]]; then
            log_success "Python $PYTHON_VERSION found"
        else
            log_warning "Python $PYTHON_VERSION found (recommended: 3.11+)"
        fi
    else
        log_error "Python3 not found"
        requirements_met=false
    fi
    ((step++))

    show_progress $step $total_steps "Checking Docker..."
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version 2>&1 | cut -d' ' -f3 | tr -d ',')
        log_success "Docker $DOCKER_VERSION found"
        DOCKER_AVAILABLE=true
    else
        log_warning "Docker not found - will use development mode"
        DOCKER_AVAILABLE=false
    fi
    ((step++))

    show_progress $step $total_steps "Checking Git..."
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version 2>&1 | cut -d' ' -f3)
        log_success "Git $GIT_VERSION found"
    else
        log_error "Git not found"
        requirements_met=false
    fi
    ((step++))

    show_progress $step $total_steps "Checking Make..."
    if command -v make &> /dev/null; then
        MAKE_VERSION=$(make --version 2>&1 | head -1 | cut -d' ' -f3)
        log_success "Make $MAKE_VERSION found"
    else
        log_error "Make not found"
        requirements_met=false
    fi
    ((step++))

    show_progress $step $total_steps "Checking curl..."
    if command -v curl &> /dev/null; then
        log_success "curl found"
    else
        log_warning "curl not found - some features may be limited"
    fi
    ((step++))

    show_progress $step $total_steps "Checking jq..."
    if command -v jq &> /dev/null; then
        log_success "jq found"
    else
        log_warning "jq not found - JSON processing limited"
    fi
    ((step++))

    show_progress $step $total_steps "Checking system memory..."
    if command -v free &> /dev/null; then
        MEM_GB=$(free -g | awk 'NR==2{printf "%.1f", $2}')
        if (( $(echo "$MEM_GB >= 4" | bc -l) )); then
            log_success "${MEM_GB}GB RAM available"
        else
            log_warning "${MEM_GB}GB RAM available (recommended: 4GB+)"
        fi
    fi
    ((step++))

    show_progress $step $total_steps "Checking disk space..."
    DISK_GB=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    if (( DISK_GB >= 10 )); then
        log_success "${DISK_GB}GB free disk space"
    else
        log_warning "${DISK_GB}GB free disk space (recommended: 10GB+)"
    fi
    ((step++))

    echo # New line after progress bar

    if [ "$requirements_met" = true ]; then
        log_success "All critical requirements met"
        return 0
    else
        log_error "Some requirements not met - please install missing dependencies"
        return 1
    fi
}

# Setup virtual environment
setup_virtual_environment() {
    log_header "VIRTUAL ENVIRONMENT SETUP"

    if [ -d ".venv" ]; then
        log_info "Virtual environment already exists"
        source .venv/bin/activate
        log_success "Virtual environment activated"
        return 0
    fi

    log_info "Creating virtual environment..."

    # Try uv first (faster), fallback to python
    if command -v uv &> /dev/null; then
        log_info "Using uv for virtual environment creation"
        python3 -m venv .venv
        source .venv/bin/activate
        uv pip install -e '.[dev]'
    else
        log_info "Using python venv for virtual environment creation"
        python3 -m venv .venv
        source .venv/bin/activate
        pip install --upgrade pip
        pip install -e '.[dev]'
    fi

    log_success "Virtual environment created and dependencies installed"
}

# Run comprehensive setup wizard
run_setup_wizard() {
    log_header "COMPREHENSIVE ENVIRONMENT SETUP"

    log_info "Running setup wizard..."

    # Check if .env exists
    if [ ! -f ".env" ]; then
        log_info "Creating .env from template..."
        cp env.example .env
        log_success ".env file created"
    else
        log_info ".env file already exists"
    fi

    # Run the setup wizard non-interactively with smart defaults
    log_info "Configuring environment with smart defaults..."

    # Set PYTHONPATH for proper module resolution
    export PYTHONPATH="$SCRIPT_DIR"

    # Run wizard with smart defaults
    python -m ultimate_discord_intelligence_bot.setup_cli wizard --yes --use-example

    if [ $? -eq 0 ]; then
        log_success "Environment setup completed"
    else
        log_error "Environment setup failed"
        return 1
    fi
}

# Install system dependencies
install_system_dependencies() {
    log_header "SYSTEM DEPENDENCIES INSTALLATION"

    local deps_installed=false

    # Check if running on Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        log_info "Detected Ubuntu/Debian system"

        # Check what needs to be installed
        local to_install=""

        if ! command -v ffmpeg &> /dev/null; then
            to_install="$to_install ffmpeg"
        fi

        if ! dpkg -l | grep -q libnss3; then
            to_install="$to_install libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgtk-3-0"
        fi

        if [ -n "$to_install" ]; then
            log_info "Installing system dependencies: $to_install"
            sudo apt-get update
            sudo apt-get install -y $to_install
            deps_installed=true
        else
            log_info "All system dependencies already installed"
        fi
    elif command -v brew &> /dev/null; then
        log_info "Detected macOS with Homebrew"

        if ! command -v ffmpeg &> /dev/null; then
            log_info "Installing ffmpeg via Homebrew..."
            brew install ffmpeg
            deps_installed=true
        else
            log_info "ffmpeg already installed"
        fi
    else
        log_warning "Unknown system - please install ffmpeg manually"
    fi

    if [ "$deps_installed" = true ]; then
        log_success "System dependencies installed"
    fi
}

# Health check function
run_health_check() {
    log_header "SYSTEM HEALTH CHECK"

    log_info "Running comprehensive health check..."

    # Set PYTHONPATH
    export PYTHONPATH="$SCRIPT_DIR"

    # Run doctor check
    if python -m ultimate_discord_intelligence_bot.setup_cli doctor; then
        log_success "All health checks passed"
        return 0
    else
        log_warning "Some health checks failed - continuing with setup"
        return 1
    fi
}

# Infrastructure services management
start_infrastructure() {
    log_header "INFRASTRUCTURE SERVICES STARTUP"

    if [ "$DOCKER_AVAILABLE" != true ]; then
        log_warning "Docker not available - infrastructure services will use development mode"
        export ENABLE_DEVELOPMENT_MODE=true
        export MOCK_VECTOR_STORE=true
        export QDRANT_URL=":memory:"
        log_success "Development mode configured"
        return 0
    fi

    log_info "Starting infrastructure services with Docker..."

    # Navigate to docker directory
    cd ops/deployment/docker

    # Determine docker compose command
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        log_error "Neither docker-compose nor docker compose found"
        return 1
    fi

    # Copy .env file if it exists
    if [ -f ../../../.env ]; then
        cp ../../../.env .env
        log_info "Environment file copied to docker directory"
    fi

    # Start infrastructure services
    log_info "Starting PostgreSQL, Redis, Qdrant, and MinIO..."
    $COMPOSE_CMD up -d postgresql redis qdrant minio

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        show_progress $attempt $max_attempts "Checking service health..."

        healthy_count=0
        total_count=0

        for service in postgresql redis qdrant minio; do
            ((total_count++))
            if $COMPOSE_CMD ps | grep -q "$service.*healthy\|$service.*Up"; then
                ((healthy_count++))
            fi
        done

        if [ $healthy_count -eq $total_count ]; then
            echo # New line
            log_success "All infrastructure services are healthy"
            cd "$SCRIPT_DIR"
            return 0
        fi

        sleep 2
        ((attempt++))
    done

    echo # New line
    log_warning "Some services may not be fully healthy yet, but continuing..."
    cd "$SCRIPT_DIR"
    return 0
}

# Service management functions
start_discord_bot() {
    local mode=${1:-"basic"}

    mkdir -p "$SERVICES_DIR" "$PIDS_DIR"

    log_info "Starting Discord Bot ($mode mode)..."

    export PYTHONPATH="$SCRIPT_DIR"

    if [ "$mode" = "enhanced" ]; then
        ENABLE_GPTCACHE=true \
        ENABLE_SEMANTIC_CACHE_SHADOW=true \
        ENABLE_GPTCACHE_ANALYSIS_SHADOW=true \
        ENABLE_PROMPT_COMPRESSION=true \
        ENABLE_GRAPH_MEMORY=true \
        ENABLE_HIPPORAG_MEMORY=true \
        nohup python -m ultimate_discord_intelligence_bot.setup_cli run discord > "$SERVICES_DIR/discord-bot.log" 2>&1 &
    else
        nohup python -m ultimate_discord_intelligence_bot.setup_cli run discord > "$SERVICES_DIR/discord-bot.log" 2>&1 &
    fi

    local pid=$!
    echo $pid > "$PIDS_DIR/discord-bot.pid"

    save_service_status "discord-bot" "running" "$pid"
    log_success "Discord Bot started (PID: $pid)"
}

start_api_server() {
    mkdir -p "$SERVICES_DIR" "$PIDS_DIR"

    log_info "Starting FastAPI Server..."

    export PYTHONPATH="$SCRIPT_DIR"

    nohup python -m uvicorn server.app:app --host 0.0.0.0 --port 8080 --reload > "$SERVICES_DIR/api-server.log" 2>&1 &

    local pid=$!
    echo $pid > "$PIDS_DIR/api-server.pid"

    save_service_status "api-server" "running" "$pid"
    log_success "API Server started (PID: $pid)"
}

start_crew_ai() {
    mkdir -p "$SERVICES_DIR" "$PIDS_DIR"

    log_info "Starting CrewAI Autonomous Intelligence..."

    export PYTHONPATH="$SCRIPT_DIR"

    nohup python -m ultimate_discord_intelligence_bot.setup_cli run crew > "$SERVICES_DIR/crewai.log" 2>&1 &

    local pid=$!
    echo $pid > "$PIDS_DIR/crewai.pid"

    save_service_status "crewai" "running" "$pid"
    log_success "CrewAI started (PID: $pid)"
}

start_mcp_server() {
    mkdir -p "$SERVICES_DIR" "$PIDS_DIR"

    log_info "Starting MCP Server..."

    export PYTHONPATH="$SCRIPT_DIR"

    # Check if fastmcp is available
    if python -c "import importlib.util; exit(0 if importlib.util.find_spec('fastmcp') else 1)" 2>/dev/null; then
        nohup make run-mcp > "$SERVICES_DIR/mcp-server.log" 2>&1 &
    else
        log_warning "fastmcp not installed. Installing..."
        pip install -e '.[mcp]'
        nohup make run-mcp > "$SERVICES_DIR/mcp-server.log" 2>&1 &
    fi

    local pid=$!
    echo $pid > "$PIDS_DIR/mcp-server.pid"

    save_service_status "mcp-server" "running" "$pid"
    log_success "MCP Server started (PID: $pid)"
}

# Stop services
stop_services() {
    log_header "STOPPING SERVICES"

    if [ -d "$PIDS_DIR" ]; then
        for pid_file in "$PIDS_DIR"/*.pid; do
            if [ -f "$pid_file" ]; then
                local service_name=$(basename "$pid_file" .pid)
                local pid=$(cat "$pid_file")

                if kill -0 "$pid" 2>/dev/null; then
                    log_info "Stopping $service_name (PID: $pid)..."
                    kill "$pid"
                    sleep 2

                    if kill -0 "$pid" 2>/dev/null; then
                        log_warning "Force killing $service_name..."
                        kill -9 "$pid"
                    fi
                fi

                rm -f "$pid_file"
                save_service_status "$service_name" "stopped"
            fi
        done
    fi

    # Stop Docker services if running
    if [ "$DOCKER_AVAILABLE" = true ] && [ -f "$DOCKER_COMPOSE_FILE" ]; then
        cd ops/deployment/docker
        $COMPOSE_CMD down
        cd "$SCRIPT_DIR"
    fi

    log_success "All services stopped"
}

# Show service status
show_status() {
    log_header "SERVICE STATUS"

    echo -e "${CYAN}Service Status:${NC}"
    echo -e "${CYAN}═══════════════${NC}"

    if [ -f "$STATUS_FILE" ]; then
        while IFS=: read -r service status timestamp pid; do
            local time_ago=$(( $(date +%s) - timestamp ))
            local time_str=""

            if [ $time_ago -lt 60 ]; then
                time_str="${time_ago}s ago"
            elif [ $time_ago -lt 3600 ]; then
                time_str="$((time_ago/60))m ago"
            else
                time_str="$((time_ago/3600))h ago"
            fi

            if [ "$status" = "running" ] && [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                echo -e "  ${GREEN}${CHECKMARK}${NC} $service - Running (PID: $pid, started $time_str)"
            elif [ "$status" = "running" ]; then
                echo -e "  ${YELLOW}${WARNING}${NC} $service - Started $time_str (PID not found)"
            else
                echo -e "  ${RED}${CROSS}${NC} $service - Stopped ($time_str ago)"
            fi
        done < "$STATUS_FILE"
    else
        echo -e "  ${YELLOW}${INFO}${NC} No service status information available"
    fi

    echo
    echo -e "${CYAN}Infrastructure Services:${NC}"
    echo -e "${CYAN}═════════════════════════${NC}"

    if [ "$DOCKER_AVAILABLE" = true ]; then
        cd ops/deployment/docker
        if command -v docker-compose &> /dev/null; then
            COMPOSE_CMD="docker-compose"
        elif docker compose version &> /dev/null; then
            COMPOSE_CMD="docker compose"
        fi

        $COMPOSE_CMD ps --format "table {{.Name}}\t{{.Status}}" | while read -r line; do
            if [[ $line == *"Up"* ]]; then
                echo -e "  ${GREEN}${CHECKMARK}${NC} $line"
            elif [[ $line == *"healthy"* ]]; then
                echo -e "  ${GREEN}${CHECKMARK}${NC} $line"
            else
                echo -e "  ${RED}${CROSS}${NC} $line"
            fi
        done
        cd "$SCRIPT_DIR"
    else
        echo -e "  ${YELLOW}${WARNING}${NC} Docker not available"
    fi

    echo
    echo -e "${CYAN}Log Files:${NC}"
    echo -e "${CYAN}═══════════${NC}"
    if [ -d "$SERVICES_DIR" ]; then
        for log_file in "$SERVICES_DIR"/*.log; do
            if [ -f "$log_file" ]; then
                local size=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null || echo "0")
                local size_kb=$((size / 1024))
                echo -e "  ${BLUE}${INFO}${NC} $(basename "$log_file") - ${size_kb}KB"
            fi
        done
    fi
}

# Main menu
show_main_menu() {
    echo -e "\n${MAGENTA}${ROCKET} Ultimate Discord Intelligence Bot - Smart Setup & Start${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo
    echo -e "${GREEN}Setup & Configuration:${NC}"
    echo "  1) ${GEAR} Full Setup & Configuration (Recommended)"
    echo "  2) ${SHIELD} Quick Setup (Skip system checks)"
    echo "  3) ${CHART} Health Check Only"
    echo
    echo -e "${GREEN}Service Management:${NC}"
    echo "  4) ${ROCKET} Start Full System (All Services + Infrastructure)"
    echo "  5) ${ROCKET} Start Enhanced Discord Bot (with all optimizations)"
    echo "  6) ${ROCKET} Start Basic Discord Bot"
    echo "  7) ${ROCKET} Start API Server Only"
    echo "  8) ${ROCKET} Start CrewAI Only"
    echo "  9) ${ROCKET} Start MCP Server Only"
    echo " 10) ${ROCKET} Custom Service Selection"
    echo
    echo -e "${GREEN}Monitoring & Control:${NC}"
    echo " 11) ${CHART} Show Service Status"
    echo " 12) ${CROSS} Stop All Services"
    echo " 13) ${CLOCK} View Logs"
    echo
    echo -e "${GREEN}Advanced:${NC}"
    echo " 14) ${GEAR} Reconfigure Environment"
    echo " 15) ${SHIELD} Update Dependencies"
    echo " 16) ${CROSS} Clean Restart (Stop all, clean, restart)"
    echo
    echo -e "${RED}0) Exit${NC}"
    echo
}

# Full setup function
full_setup() {
    log_header "FULL SYSTEM SETUP & CONFIGURATION"

    local step=1
    local total_steps=7

    show_progress $step $total_steps "Checking system requirements..."
    if ! check_system_requirements; then
        log_error "System requirements check failed"
        return 1
    fi
    ((step++))

    show_progress $step $total_steps "Installing system dependencies..."
    install_system_dependencies
    ((step++))

    show_progress $step $total_steps "Setting up virtual environment..."
    setup_virtual_environment
    ((step++))

    show_progress $step $total_steps "Running setup wizard..."
    if ! run_setup_wizard; then
        log_error "Setup wizard failed"
        return 1
    fi
    ((step++))

    show_progress $step $total_steps "Starting infrastructure services..."
    start_infrastructure
    ((step++))

    show_progress $step $total_steps "Running health checks..."
    run_health_check
    ((step++))

    show_progress $step $total_steps "Finalizing setup..."
    log_success "Full setup completed successfully"
    ((step++))

    echo # New line
    log_header "SETUP COMPLETE"
    echo -e "${GREEN}${CHECKMARK} Your Discord Intelligence Bot is ready!${NC}"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "  • Run option 4 to start the full system"
    echo "  • Run option 11 to check service status"
    echo "  • View logs in: $SERVICES_DIR/"
    echo "  • Check metrics at: http://localhost:9090 (if Prometheus running)"
    echo
}

# Quick setup function
quick_setup() {
    log_header "QUICK SETUP"

    log_info "Skipping system checks and proceeding with setup..."

    setup_virtual_environment
    run_setup_wizard
    start_infrastructure
    run_health_check

    log_success "Quick setup completed"
}

# Start full system
start_full_system() {
    log_header "STARTING FULL SYSTEM"

    log_info "Starting all services..."

    # Start infrastructure first
    start_infrastructure

    # Start application services
    start_discord_bot "enhanced"
    start_api_server
    start_crew_ai
    start_mcp_server

    log_success "Full system started"
    show_status
}

# Custom service selection
custom_services() {
    log_header "CUSTOM SERVICE SELECTION"

    echo -e "${CYAN}Select services to start:${NC}"
    echo "  1) Discord Bot (Basic)"
    echo "  2) Discord Bot (Enhanced)"
    echo "  3) API Server"
    echo "  4) CrewAI"
    echo "  5) MCP Server"
    echo
    echo -e "${YELLOW}Enter service numbers separated by spaces (e.g., '1 3 4'):${NC}"
    read -p "Services: " selected_services

    for service in $selected_services; do
        case $service in
            1) start_discord_bot "basic" ;;
            2) start_discord_bot "enhanced" ;;
            3) start_api_server ;;
            4) start_crew_ai ;;
            5) start_mcp_server ;;
            *) log_warning "Unknown service: $service" ;;
        esac
    done

    log_success "Selected services started"
}

# View logs
view_logs() {
    log_header "SERVICE LOGS"

    if [ ! -d "$SERVICES_DIR" ]; then
        log_warning "No service logs directory found"
        return
    fi

    echo -e "${CYAN}Available log files:${NC}"
    local i=1
    local log_files=()

    for log_file in "$SERVICES_DIR"/*.log; do
        if [ -f "$log_file" ]; then
            echo "  $i) $(basename "$log_file")"
            log_files[$i]="$log_file"
            ((i++))
        fi
    done

    if [ ${#log_files[@]} -eq 0 ]; then
        log_warning "No log files found"
        return
    fi

    echo
    read -p "Select log file to view (number or 'all'): " choice

    if [ "$choice" = "all" ]; then
        echo -e "${CYAN}Tailing all log files...${NC}"
        tail -f "$SERVICES_DIR"/*.log
    elif [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -lt $i ]; then
        echo -e "${CYAN}Viewing ${log_files[$choice]}...${NC}"
        less "${log_files[$choice]}"
    else
        log_error "Invalid choice"
    fi
}

# Update dependencies
update_dependencies() {
    log_header "UPDATING DEPENDENCIES"

    log_info "Updating Python dependencies..."

    if command -v uv &> /dev/null; then
        uv pip install -e '.[dev]' --upgrade
    else
        pip install -e '.[dev]' --upgrade
    fi

    log_success "Dependencies updated"
}

# Clean restart
clean_restart() {
    log_header "CLEAN RESTART"

    log_info "Stopping all services..."
    stop_services

    log_info "Cleaning up..."
    make clean

    log_info "Restarting full system..."
    start_full_system

    log_success "Clean restart completed"
}

# Main function
main() {
    # Initialize
    mkdir -p "$SERVICES_DIR" "$PIDS_DIR"

    # Parse command line arguments
    if [ $# -gt 0 ]; then
        case $1 in
            setup) full_setup; exit $? ;;
            quick) quick_setup; exit $? ;;
            start) start_full_system; exit $? ;;
            stop) stop_services; exit $? ;;
            status) show_status; exit $? ;;
            logs) view_logs; exit $? ;;
            health) run_health_check; exit $? ;;
            --help|-h)
                echo "Usage: $0 [command]"
                echo
                echo "Commands:"
                echo "  setup    - Run full setup and configuration"
                echo "  quick    - Run quick setup (skip checks)"
                echo "  start    - Start full system"
                echo "  stop     - Stop all services"
                echo "  status   - Show service status"
                echo "  logs     - View service logs"
                echo "  health   - Run health check"
                echo "  (no args) - Interactive menu"
                exit 0
                ;;
        esac
    fi

    # Interactive menu
    while true; do
        show_main_menu
        read -p "Select option (0-16): " choice

        case $choice in
            0) log_info "Goodbye!"; exit 0 ;;
            1) full_setup ;;
            2) quick_setup ;;
            3) run_health_check ;;
            4) start_full_system ;;
            5) start_discord_bot "enhanced" ;;
            6) start_discord_bot "basic" ;;
            7) start_api_server ;;
            8) start_crew_ai ;;
            9) start_mcp_server ;;
            10) custom_services ;;
            11) show_status ;;
            12) stop_services ;;
            13) view_logs ;;
            14) run_setup_wizard ;;
            15) update_dependencies ;;
            16) clean_restart ;;
            *) log_error "Invalid option. Please select 0-16." ;;
        esac

        echo
        read -p "Press Enter to continue..."
    done
}

# Cleanup on exit
trap 'echo -e "\n${YELLOW}Interrupted. Run ./smart-setup.sh stop to stop services.${NC}"' INT TERM

# Run main function
main "$@"