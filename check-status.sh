#!/bin/bash
# Check status of all services

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
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║  Service Status Check                                     ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check Python processes
echo -e "\n${BLUE}=== Background Services ===${NC}"
if [ -d "logs/services" ] && [ -n "$(ls -A logs/services/*.pid 2>/dev/null)" ]; then
    for pidfile in logs/services/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            service_name=$(basename "$pidfile" .pid)
            
            if ps -p "$pid" > /dev/null 2>&1; then
                uptime=$(ps -o etime= -p "$pid" | tr -d ' ')
                log_success "$service_name (PID: $pid, uptime: $uptime)"
            else
                log_error "$service_name (PID: $pid) - NOT RUNNING"
            fi
        fi
    done
else
    log_info "No background services found"
fi

# Check for Python processes
echo -e "\n${BLUE}=== Python Processes ===${NC}"
if pgrep -fa "ultimate_discord_intelligence_bot|uvicorn|crew_mcp" | grep -v grep > /dev/null; then
    pgrep -fa "ultimate_discord_intelligence_bot|uvicorn|crew_mcp" | grep -v grep | while read line; do
        log_success "$line"
    done
else
    log_info "No Python services running"
fi

# Check Docker services
echo -e "\n${BLUE}=== Docker Services ===${NC}"
if command -v docker &> /dev/null; then
    if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q "discord-intelligence"; then
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep "discord-intelligence" | while read line; do
            log_success "$line"
        done
    else
        log_info "No Docker services running"
    fi
else
    log_info "Docker not available"
fi

# Check ports
echo -e "\n${BLUE}=== Port Status ===${NC}"
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_success "$service (port $port)"
    else
        log_info "$service (port $port) - not listening"
    fi
}

check_port 8080 "API Server"
check_port 6333 "Qdrant"
check_port 6379 "Redis"
check_port 5432 "PostgreSQL"
check_port 9000 "MinIO"
check_port 9090 "Prometheus"
check_port 3000 "Grafana"

# Check configuration
echo -e "\n${BLUE}=== Configuration ===${NC}"
if [ -f ".env" ]; then
    log_success ".env file exists"
    
    # Check critical keys
    if grep -q "DISCORD_BOT_TOKEN=.*[^-placeholder]" .env 2>/dev/null; then
        log_success "DISCORD_BOT_TOKEN configured"
    else
        log_warning "DISCORD_BOT_TOKEN not configured"
    fi
    
    if grep -q "OPENROUTER_API_KEY=.*[^-placeholder]" .env 2>/dev/null || grep -q "OPENAI_API_KEY=.*[^-placeholder]" .env 2>/dev/null; then
        log_success "LLM API key configured"
    else
        log_warning "No LLM API key configured"
    fi
else
    log_error ".env file missing"
fi

# Check virtual environment
echo -e "\n${BLUE}=== Environment ===${NC}"
if [ -d ".venv" ]; then
    log_success "Virtual environment exists"
    
    if [ -f ".venv/bin/python" ]; then
        python_version=$(.venv/bin/python --version 2>&1)
        log_success "Python: $python_version"
    fi
else
    log_warning "Virtual environment not found"
fi

# Network checks
echo -e "\n${BLUE}=== Network Connectivity ===${NC}"
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    log_success "API Server responding"
elif curl -s http://localhost:8080 > /dev/null 2>&1; then
    log_success "API Server reachable"
else
    log_info "API Server not reachable"
fi

if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    log_success "Qdrant responding"
else
    log_info "Qdrant not reachable"
fi

# Recent logs
echo -e "\n${BLUE}=== Recent Activity ===${NC}"
if [ -d "logs/services" ] && [ -n "$(ls -A logs/services/*.log 2>/dev/null)" ]; then
    for logfile in logs/services/*.log; do
        if [ -f "$logfile" ]; then
            service_name=$(basename "$logfile" .log)
            last_lines=$(tail -n 1 "$logfile" 2>/dev/null)
            if [ -n "$last_lines" ]; then
                echo -e "${BLUE}[$service_name]${NC} ${last_lines:0:80}..."
            fi
        fi
    done
else
    log_info "No service logs found"
fi

echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Status Check Complete                                    ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo -e "\n${BLUE}Commands:${NC}"
echo "  Start services: ./start-all-services.sh"
echo "  Stop services:  ./stop-all-services.sh"
echo "  View logs:      tail -f logs/services/*.log"
echo "  Run doctor:     make doctor"
echo ""
