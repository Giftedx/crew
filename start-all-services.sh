#!/bin/bash
# Ultimate Discord Intelligence Bot - Complete System Startup
# This script starts all services and components of the system

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║  Ultimate Discord Intelligence Bot - System Startup       ║
║  Multi-tenant AI pipeline with 84+ specialized tools      ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if running in WSL
if grep -qEi "(Microsoft|WSL)" /proc/version &> /dev/null; then
    log_info "Running in WSL environment"
    IN_WSL=true
else
    IN_WSL=false
fi

# Step 1: Check Python environment
log_info "Step 1/8: Checking Python environment..."
if [ ! -d ".venv" ]; then
    log_warning "Virtual environment not found. Creating one..."
    make first-run
else
    log_success "Virtual environment found"
fi

# Activate virtual environment
source .venv/bin/activate
log_success "Virtual environment activated"

# Step 2: Check .env file
log_info "Step 2/8: Checking environment configuration..."
if [ ! -f ".env" ]; then
    log_warning ".env file not found. Creating from template..."
    make init-env
    log_warning "IMPORTANT: Edit .env file and set required API keys:"
    log_warning "  - DISCORD_BOT_TOKEN"
    log_warning "  - OPENAI_API_KEY or OPENROUTER_API_KEY"
    log_warning "  - Optional: QDRANT_URL, REDIS_URL, etc."
    read -p "Press Enter after editing .env file to continue..."
else
    log_success ".env file found"
fi

# Step 3: Validate configuration
log_info "Step 3/8: Running system doctor..."
if make doctor; then
    log_success "System health check passed"
else
    log_warning "System health check found issues. Check the output above."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 4: Start infrastructure services
log_info "Step 4/8: Starting infrastructure services..."

# Check for Docker
if ! command -v docker &> /dev/null; then
    log_warning "Docker not found. Will use development mode with in-memory services."
    export ENABLE_DEVELOPMENT_MODE=true
    export MOCK_VECTOR_STORE=true
    export QDRANT_URL=":memory:"
else
        log_info "Starting Docker infrastructure..."
        cd ops/deployment/docker

        # Copy .env file if it exists
        if [ -f ../../../.env ]; then
            cp ../../../.env .env
            log_info "Environment file copied"
        fi

        if command -v docker-compose &> /dev/null; then
            COMPOSE_CMD="docker-compose"
        elif docker compose version &> /dev/null; then
            COMPOSE_CMD="docker compose"
        else
            log_error "Neither 'docker-compose' nor 'docker compose' found"
            exit 1
        fi

        log_info "Starting infrastructure services (Qdrant, Redis, PostgreSQL, MinIO)..."

    # Start only infrastructure services (not application services)
    $COMPOSE_CMD --env-file .env up -d postgresql redis qdrant minio

    log_info "Waiting for services to be healthy..."
    sleep 10

    # Check service health
    for service in postgresql redis qdrant minio; do
        if $COMPOSE_CMD ps | grep -q "$service.*healthy\|$service.*Up"; then
            log_success "$service is running"
        else
            log_warning "$service may not be healthy yet"
        fi
    done

    cd "$SCRIPT_DIR"
    log_success "Infrastructure services started"
fi

# Step 5: Run quick checks
log_info "Step 5/8: Running code quality checks..."
if make quick-check; then
    log_success "Quick checks passed"
else
    log_warning "Some checks failed. Review output above."
fi

# Step 6: Display startup options
log_info "Step 6/8: Startup options..."
echo ""
echo -e "${GREEN}Available services to start:${NC}"
echo "  1) Discord Bot (main intelligence bot)"
echo "  2) Discord Bot Enhanced (with semantic cache, compression, graph memory)"
echo "  3) FastAPI Server (HTTP API + A2A endpoints)"
echo "  4) CrewAI Autonomous Intelligence"
echo "  5) All Local Services (Bot + API + CrewAI)"
echo "  6) Full Stack (Infrastructure + All Services)"
echo "  7) MCP Server"
echo "  8) Custom (select individual components)"
echo "  9) Status Check Only"
echo ""

read -p "Select option (1-9): " -n 1 -r OPTION
echo ""

# Step 7: Start selected services
log_info "Step 7/8: Starting selected services..."

start_discord_bot() {
    log_info "Starting Discord Bot..."
    python -m ultimate_discord_intelligence_bot.setup_cli run discord
}

start_discord_bot_enhanced() {
    log_info "Starting Discord Bot (Enhanced Mode)..."
    ENABLE_GPTCACHE=true \
    ENABLE_SEMANTIC_CACHE_SHADOW=true \
    ENABLE_GPTCACHE_ANALYSIS_SHADOW=true \
    ENABLE_PROMPT_COMPRESSION=true \
    ENABLE_GRAPH_MEMORY=true \
    ENABLE_HIPPORAG_MEMORY=true \
    python -m ultimate_discord_intelligence_bot.setup_cli run discord
}

start_api_server() {
    log_info "Starting FastAPI Server..."
    python -m uvicorn server.app:app --host 0.0.0.0 --port 8080 --reload
}

start_crewai() {
    log_info "Starting CrewAI Autonomous Intelligence..."
    python -m ultimate_discord_intelligence_bot.setup_cli run crew
}

start_mcp_server() {
    log_info "Starting MCP Server..."
    if python -c "import importlib.util; exit(0 if importlib.util.find_spec('fastmcp') else 1)" 2>/dev/null; then
        make run-mcp
    else
        log_warning "fastmcp not installed. Installing..."
        pip install -e '.[mcp]'
        make run-mcp
    fi
}

case $OPTION in
    1)
        start_discord_bot
        ;;
    2)
        start_discord_bot_enhanced
        ;;
    3)
        start_api_server
        ;;
    4)
        start_crewai
        ;;
    5)
        log_info "Starting all local services..."
        log_info "You'll need multiple terminal windows for this."
        log_info "Opening services in background with logging..."

        # Create logs directory
        mkdir -p logs/services

        # Start services in background
        nohup python -m ultimate_discord_intelligence_bot.setup_cli run discord > logs/services/discord-bot.log 2>&1 &
        echo $! > logs/services/discord-bot.pid
        log_success "Discord Bot started (PID: $(cat logs/services/discord-bot.pid))"

        nohup python -m uvicorn server.app:app --host 0.0.0.0 --port 8080 > logs/services/api-server.log 2>&1 &
        echo $! > logs/services/api-server.pid
        log_success "API Server started (PID: $(cat logs/services/api-server.pid))"

        nohup python -m ultimate_discord_intelligence_bot.setup_cli run crew > logs/services/crewai.log 2>&1 &
        echo $! > logs/services/crewai.pid
        log_success "CrewAI started (PID: $(cat logs/services/crewai.pid))"

        log_info "Services started in background. Logs in logs/services/"
        log_info "To stop: kill \$(cat logs/services/*.pid)"
        log_info "Tailing logs..."
        tail -f logs/services/*.log
        ;;
    6)
        log_info "Starting full stack..."
        if [ "$IN_WSL" = true ] && ! command -v docker &> /dev/null; then
            log_error "Docker not available in WSL. Please enable Docker Desktop WSL integration."
            exit 1
        fi

        # Copy .env to docker directory so docker-compose can use it
        if [ -f .env ]; then
            cp .env ops/deployment/docker/.env
            log_info "Environment file copied to docker directory"
        fi

        cd ops/deployment/docker
        $COMPOSE_CMD --env-file .env up -d
        cd "$SCRIPT_DIR"

        log_success "Full stack started with Docker Compose"
        log_info "Access points:"
        log_info "  - API Server: http://localhost:8080"
        log_info "  - Grafana: http://localhost:3000 (admin/admin)"
        log_info "  - Prometheus: http://localhost:9090"
        log_info "  - Qdrant: http://localhost:6333"
        log_info "  - MinIO: http://localhost:9001"
        ;;
    7)
        start_mcp_server
        ;;
    8)
        log_info "Custom component selection..."
        echo "Select components to start (space-separated numbers):"
        echo "  1) Discord Bot"
        echo "  2) Discord Bot Enhanced"
        echo "  3) API Server"
        echo "  4) CrewAI"
        echo "  5) MCP Server"
        read -p "Components: " COMPONENTS

        mkdir -p logs/services

        for comp in $COMPONENTS; do
            case $comp in
                1)
                    nohup python -m ultimate_discord_intelligence_bot.setup_cli run discord > logs/services/discord-bot.log 2>&1 &
                    echo $! > logs/services/discord-bot.pid
                    log_success "Discord Bot started"
                    ;;
                2)
                    ENABLE_GPTCACHE=true \
                    ENABLE_SEMANTIC_CACHE_SHADOW=true \
                    ENABLE_GPTCACHE_ANALYSIS_SHADOW=true \
                    ENABLE_PROMPT_COMPRESSION=true \
                    ENABLE_GRAPH_MEMORY=true \
                    ENABLE_HIPPORAG_MEMORY=true \
                    nohup python -m ultimate_discord_intelligence_bot.setup_cli run discord > logs/services/discord-bot-enhanced.log 2>&1 &
                    echo $! > logs/services/discord-bot-enhanced.pid
                    log_success "Discord Bot Enhanced started"
                    ;;
                3)
                    nohup python -m uvicorn server.app:app --host 0.0.0.0 --port 8080 > logs/services/api-server.log 2>&1 &
                    echo $! > logs/services/api-server.pid
                    log_success "API Server started"
                    ;;
                4)
                    nohup python -m ultimate_discord_intelligence_bot.setup_cli run crew > logs/services/crewai.log 2>&1 &
                    echo $! > logs/services/crewai.pid
                    log_success "CrewAI started"
                    ;;
                5)
                    nohup make run-mcp > logs/services/mcp-server.log 2>&1 &
                    echo $! > logs/services/mcp-server.pid
                    log_success "MCP Server started"
                    ;;
            esac
        done

        log_info "Selected services started. Logs in logs/services/"
        ;;
    9)
        log_info "Status check only - skipping service start"
        ;;
    *)
        log_error "Invalid option"
        exit 1
        ;;
esac

# Step 8: Display status and next steps
log_info "Step 8/8: System status..."
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  System Startup Complete!                                ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$OPTION" != "9" ]; then
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  • Monitor logs: tail -f logs/services/*.log"
    echo "  • Check health: make doctor"
    echo "  • Run tests: make test"
    echo "  • View metrics: http://localhost:9090 (if Prometheus running)"
    echo "  • View dashboards: http://localhost:3000 (if Grafana running)"
    echo ""
fi

echo -e "${BLUE}Useful Commands:${NC}"
echo "  • Stop all: pkill -f 'ultimate_discord_intelligence_bot' or docker-compose down"
echo "  • Restart: ./start-all-services.sh"
echo "  • Quick check: make quick-check"
echo "  • Full check: make full-check"
echo "  • View docs: cat docs/DEVELOPER_ONBOARDING_GUIDE.md"
echo ""

echo -e "${GREEN}System ready!${NC}"
