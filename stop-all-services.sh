#!/bin/bash
# Stop all running services

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║  Stopping All Services                                    ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Stop background processes
log_info "Stopping background services..."
if [ -d "logs/services" ]; then
    for pidfile in logs/services/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            service_name=$(basename "$pidfile" .pid)
            
            if ps -p "$pid" > /dev/null 2>&1; then
                log_info "Stopping $service_name (PID: $pid)..."
                kill "$pid" 2>/dev/null || true
                sleep 1
                
                # Force kill if still running
                if ps -p "$pid" > /dev/null 2>&1; then
                    log_warning "Force stopping $service_name..."
                    kill -9 "$pid" 2>/dev/null || true
                fi
                
                log_success "$service_name stopped"
            else
                log_warning "$service_name not running (PID: $pid)"
            fi
            
            rm "$pidfile"
        fi
    done
else
    log_info "No PID files found in logs/services/"
fi

# Stop any remaining Python processes
log_info "Checking for remaining Python processes..."

# Stop API server (uvicorn)
if pgrep -f "uvicorn server.app" > /dev/null; then
    log_info "Stopping API Server (uvicorn)..."
    pkill -f "uvicorn server.app" || true
    sleep 1
    if pgrep -f "uvicorn server.app" > /dev/null; then
        log_warning "Force stopping API Server..."
        pkill -9 -f "uvicorn server.app" || true
    fi
    log_success "API Server stopped"
fi

# Stop Discord bot
if pgrep -f "ultimate_discord_intelligence_bot" > /dev/null; then
    log_info "Stopping Discord Bot processes..."
    pkill -f "ultimate_discord_intelligence_bot" || true
    sleep 1
    
    # Force kill if needed
    if pgrep -f "ultimate_discord_intelligence_bot" > /dev/null; then
        log_warning "Force stopping Discord Bot..."
        pkill -9 -f "ultimate_discord_intelligence_bot" || true
    fi
    log_success "Discord Bot stopped"
fi

# Clean up any log files from full stack deployment
if [ -f "logs/api-server.log" ]; then
    log_info "Archiving API server logs..."
    mv logs/api-server.log "logs/api-server-$(date +%Y%m%d-%H%M%S).log"
fi

if [ -f "logs/discord-bot.log" ]; then
    log_info "Archiving Discord bot logs..."
    mv logs/discord-bot.log "logs/discord-bot-$(date +%Y%m%d-%H%M%S).log"
fi

# Stop Docker services
log_info "Checking Docker services..."
if command -v docker &> /dev/null; then
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD=""
    fi
    
    if [ -n "$COMPOSE_CMD" ]; then
        if [ -f "ops/deployment/docker/docker-compose.yml" ]; then
            log_info "Stopping Docker Compose services..."
            cd ops/deployment/docker
            $COMPOSE_CMD down
            cd - > /dev/null
            log_success "Docker services stopped"
        fi
    fi
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  All Services Stopped                                     ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

log_info "To start services again, run: ./start-all-services.sh"
