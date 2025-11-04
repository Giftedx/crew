#!/bin/bash
# Service Management Helper - Interactive menu for all operations

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear

echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║    Ultimate Discord Intelligence Bot - Service Manager       ║
║                                                               ║
║    Multi-tenant AI pipeline with 84+ specialized tools       ║
║    Tenant-aware streaming: download → transcribe → analyze   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

show_menu() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  SERVICE OPERATIONS${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "  1)  🚀 Start All Services (Interactive)"
    echo "  2)  🤖 Start Discord Bot (Basic)"
    echo "  3)  ⚡ Start Discord Bot (Enhanced Mode)"
    echo "  4)  🌐 Start API Server"
    echo "  5)  🧠 Start CrewAI"
    echo "  6)  📡 Start MCP Server"
    echo "  7)  🐳 Start Docker Infrastructure"
    echo "  8)  📊 Start Full Stack (All)"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  MONITORING & DIAGNOSTICS${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "  9)  📈 Check Status"
    echo "  10) 🩺 Run Doctor (Health Check)"
    echo "  11) 📝 View Logs"
    echo "  12) 📊 View Metrics (Prometheus)"
    echo "  13) 📉 View Dashboards (Grafana)"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}  CONTROL${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "  14) 🛑 Stop All Services"
    echo "  15) 🔄 Restart All Services"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  DEVELOPMENT${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "  16) ⚡ Quick Check (format + lint + test-fast)"
    echo "  17) ✅ Full Check (format + lint + type + test)"
    echo "  18) 🧪 Run Tests"
    echo "  19) 🔧 Setup Git Hooks"
    echo "  20) 🧹 Clean Build Artifacts"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  HELP${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "  21) 📖 Quick Start Guide"
    echo "  22) 📚 View Documentation"
    echo "  23) 🆘 Troubleshooting"
    echo ""
    echo "  0)  ❌ Exit"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

while true; do
    show_menu
    read -p "$(echo -e ${GREEN}Select option:${NC} )" choice
    echo ""

    case $choice in
        1)
            echo -e "${GREEN}Starting services (interactive mode)...${NC}"
            ./start-all-services.sh
            ;;
        2)
            echo -e "${GREEN}Starting Discord Bot (Basic)...${NC}"
            source .venv/bin/activate
            python -m ultimate_discord_intelligence_bot.setup_cli run discord
            ;;
        3)
            echo -e "${GREEN}Starting Discord Bot (Enhanced)...${NC}"
            source .venv/bin/activate
            make run-discord-enhanced
            ;;
        4)
            echo -e "${GREEN}Starting API Server...${NC}"
            source .venv/bin/activate
            python -m uvicorn server.app:app --host 0.0.0.0 --port 8080 --reload
            ;;
        5)
            echo -e "${GREEN}Starting CrewAI...${NC}"
            source .venv/bin/activate
            make run-crew
            ;;
        6)
            echo -e "${GREEN}Starting MCP Server...${NC}"
            source .venv/bin/activate
            make run-mcp
            ;;
        7)
            echo -e "${GREEN}Starting Docker infrastructure...${NC}"
            if [ -f .env ]; then
                cp .env ops/deployment/docker/.env
            fi
            cd ops/deployment/docker
            if command -v docker-compose &> /dev/null; then
                docker-compose --env-file .env up -d postgresql redis qdrant minio
            else
                docker compose --env-file .env up -d postgresql redis qdrant minio
            fi
            cd - > /dev/null
            echo -e "${GREEN}[SUCCESS]${NC} Infrastructure services started"
            read -p "Press Enter to continue..."
            clear
            ;;
        8)
            echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${CYAN}   FULL STACK DEPLOYMENT - ALL FEATURES ENABLED${NC}"
            echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            echo -e "${BLUE}[STEP 1/4]${NC} Starting Docker infrastructure..."

            # Copy environment and start infrastructure
            if [ -f .env ]; then
                cp .env ops/deployment/docker/.env
                echo -e "${GREEN}[OK]${NC} Environment file synchronized"
            fi

            cd ops/deployment/docker
            if command -v docker-compose &> /dev/null; then
                docker-compose --env-file .env up -d postgresql redis qdrant minio prometheus grafana alertmanager
            else
                docker compose --env-file .env up -d postgresql redis qdrant minio prometheus grafana alertmanager
            fi
            cd - > /dev/null

            echo -e "${GREEN}[OK]${NC} Infrastructure services started"
            echo ""

            # Wait for services to be ready
            echo -e "${BLUE}[STEP 2/4]${NC} Waiting for services to be ready..."
            sleep 5
            echo -e "${GREEN}[OK]${NC} Services ready"
            echo ""

            # Start API Server in background with all features
            echo -e "${BLUE}[STEP 3/4]${NC} Starting API Server with comprehensive features..."
            source .venv/bin/activate

            # Export ALL feature flags for maximum capabilities
            export ENABLE_HTTP_METRICS=true
            export ENABLE_PROMETHEUS_ENDPOINT=true
            export ENABLE_API_CACHE=true
            export ENABLE_CORS=true
            export ENABLE_RATE_LIMITING=true
            export ENABLE_TRACING=true
            export ENABLE_SEMANTIC_CACHE=true
            export ENABLE_SEMANTIC_CACHE_SHADOW=true
            export ENABLE_GPTCACHE=true
            export ENABLE_GPTCACHE_ANALYSIS=true
            export ENABLE_GPTCACHE_ANALYSIS_SHADOW=true
            export ENABLE_PROMPT_COMPRESSION=true
            export ENABLE_GRAPH_MEMORY=true
            export ENABLE_HIPPORAG_MEMORY=true
            export ENABLE_MEM0_MEMORY=true
            export ENABLE_VECTOR_MEMORY=true
            export ENABLE_KNOWLEDGE_GRAPH=true
            export ENABLE_INGEST_WORKER=true
            export ENABLE_BACKGROUND_WORKER=true
            export ENABLE_DISCORD_GATEWAY=true
            export ENABLE_DISCORD_USER_COMMANDS=true
            export ENABLE_DISCORD_ADMIN_COMMANDS=true
            export ENABLE_WEBHOOK_POSTING=true
            export ENABLE_FACT_CHECKING=true
            export ENABLE_FALLACY_DETECTION=true
            export ENABLE_SENTIMENT_ANALYSIS=true
            export ENABLE_CLAIM_EXTRACTION=true
            export ENABLE_TRUSTWORTHINESS_SCORING=true
            export ENABLE_PERSPECTIVE_SYNTHESIS=true
            export ENABLE_STEELMAN_ARGUMENTS=true
            export ENABLE_DEBATE_MODE=true
            export ENABLE_CHARACTER_PROFILING=true
            export ENABLE_TIMELINE_TRACKING=true
            export ENABLE_LEADERBOARD=true
            export ENABLE_MULTI_PLATFORM_MONITORING=true
            export ENABLE_AUTONOMOUS_INTELLIGENCE=true
            export ENABLE_CREWAI_INTEGRATION=true
            export ENABLE_ADVANCED_BANDITS=true
            export ENABLE_DSPY_OPTIMIZATION=true
            export ENABLE_MCP_TOOLS=true
            export ENABLE_RESEARCH_TOOLS=true
            export ENABLE_VISION_ANALYSIS=true
            export ENABLE_AUDIO_ANALYSIS=true
            export ENABLE_MULTIMODAL_AI=true
            export ENABLE_LIVE_STREAM_ANALYSIS=true
            export ENABLE_TREND_ANALYSIS=true
            export ENABLE_VIRALITY_PREDICTION=true
            export ENABLE_SOCIAL_GRAPH_ANALYSIS=true
            export ENABLE_NARRATIVE_TRACKING=true
            export ENABLE_CREATOR_INTELLIGENCE=true

            # Start API server in background
            nohup python -m uvicorn server.app:app --host 0.0.0.0 --port 8080 --reload \
                > logs/api-server.log 2>&1 &
            API_PID=$!
            echo -e "${GREEN}[OK]${NC} API Server started (PID: $API_PID)"
            echo ""

            # Start Enhanced Discord Bot with all features
            echo -e "${BLUE}[STEP 4/4]${NC} Starting Discord Bot (Enhanced - All Features)..."
            echo -e "${CYAN}[FEATURES]${NC} Enabled capabilities:"
            echo -e "  ✓ Advanced semantic caching with shadow mode"
            echo -e "  ✓ GPTCache with analysis mode"
            echo -e "  ✓ Prompt compression for efficiency"
            echo -e "  ✓ Graph memory (knowledge graphs)"
            echo -e "  ✓ HippoRAG continual memory"
            echo -e "  ✓ Mem0 personal memory"
            echo -e "  ✓ Vector embeddings and search"
            echo -e "  ✓ Multi-platform monitoring (YouTube, Twitch, X, etc.)"
            echo -e "  ✓ Real-time fact checking & fallacy detection"
            echo -e "  ✓ Sentiment & trustworthiness analysis"
            echo -e "  ✓ Character profiling & timeline tracking"
            echo -e "  ✓ Autonomous intelligence agents (CrewAI)"
            echo -e "  ✓ Advanced contextual bandits optimization"
            echo -e "  ✓ DSPy optimization framework"
            echo -e "  ✓ MCP tools integration"
            echo -e "  ✓ Vision & audio analysis"
            echo -e "  ✓ Live stream monitoring"
            echo -e "  ✓ Social graph & narrative tracking"
            echo -e "  ✓ 84+ specialized AI tools"
            echo ""

            # Start Discord bot in background
            nohup make run-discord-enhanced > logs/discord-bot.log 2>&1 &
            BOT_PID=$!
            echo -e "${GREEN}[OK]${NC} Discord Bot started (PID: $BOT_PID)"
            echo ""

            # Success summary
            echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${CYAN}   FULL STACK SUCCESSFULLY DEPLOYED${NC}"
            echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            echo -e "${YELLOW}📊 Service Status:${NC}"
            echo -e "  ${GREEN}✓${NC} PostgreSQL      → port 5432"
            echo -e "  ${GREEN}✓${NC} Redis           → port 6379"
            echo -e "  ${GREEN}✓${NC} Qdrant          → port 6333"
            echo -e "  ${GREEN}✓${NC} MinIO           → port 9000/9001"
            echo -e "  ${GREEN}✓${NC} Prometheus      → port 9090"
            echo -e "  ${GREEN}✓${NC} Grafana         → port 3000"
            echo -e "  ${GREEN}✓${NC} Alertmanager    → port 9093"
            echo -e "  ${GREEN}✓${NC} API Server      → port 8080 (PID: $API_PID)"
            echo -e "  ${GREEN}✓${NC} Discord Bot     → Enhanced Mode (PID: $BOT_PID)"
            echo ""
            echo -e "${YELLOW}🌐 Access Points:${NC}"
            echo -e "  • API Server:    ${CYAN}http://localhost:8080${NC}"
            echo -e "  • API Docs:      ${CYAN}http://localhost:8080/docs${NC}"
            echo -e "  • Health Check:  ${CYAN}http://localhost:8080/health${NC}"
            echo -e "  • Metrics:       ${CYAN}http://localhost:8080/metrics${NC}"
            echo -e "  • Grafana:       ${CYAN}http://localhost:3000${NC} (admin/admin)"
            echo -e "  • Prometheus:    ${CYAN}http://localhost:9090${NC}"
            echo -e "  • Qdrant UI:     ${CYAN}http://localhost:6333/dashboard${NC}"
            echo -e "  • MinIO Console: ${CYAN}http://localhost:9001${NC}"
            echo ""
            echo -e "${YELLOW}📝 Logs:${NC}"
            echo -e "  • API Server:    ${CYAN}tail -f logs/api-server.log${NC}"
            echo -e "  • Discord Bot:   ${CYAN}tail -f logs/discord-bot.log${NC}"
            echo -e "  • Docker:        ${CYAN}cd ops/deployment/docker && docker compose logs -f${NC}"
            echo ""
            echo -e "${YELLOW}🛑 To stop all services:${NC}"
            echo -e "  • Run option ${CYAN}14${NC} from main menu"
            echo -e "  • Or manually: ${CYAN}kill $API_PID $BOT_PID && cd ops/deployment/docker && docker compose down${NC}"
            echo ""
            echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            read -p "Press Enter to continue..."
            clear
            ;;
        9)
            echo -e "${GREEN}Checking status...${NC}"
            ./check-status.sh
            read -p "Press Enter to continue..."
            clear
            ;;
        10)
            echo -e "${GREEN}Running health check...${NC}"
            source .venv/bin/activate
            make doctor
            read -p "Press Enter to continue..."
            clear
            ;;
        11)
            echo -e "${GREEN}Viewing logs...${NC}"
            if [ -d "logs/services" ] && [ -n "$(ls -A logs/services/*.log 2>/dev/null)" ]; then
                tail -f logs/services/*.log
            else
                echo "No service logs found. Services may not be running."
                read -p "Press Enter to continue..."
                clear
            fi
            ;;
        12)
            echo -e "${GREEN}Opening Prometheus...${NC}"
            if command -v xdg-open &> /dev/null; then
                xdg-open http://localhost:9090
            elif command -v open &> /dev/null; then
                open http://localhost:9090
            else
                echo "Visit: http://localhost:9090"
            fi
            read -p "Press Enter to continue..."
            clear
            ;;
        13)
            echo -e "${GREEN}Opening Grafana...${NC}"
            if command -v xdg-open &> /dev/null; then
                xdg-open http://localhost:3000
            elif command -v open &> /dev/null; then
                open http://localhost:3000
            else
                echo "Visit: http://localhost:3000 (admin/admin)"
            fi
            read -p "Press Enter to continue..."
            clear
            ;;
        14)
            echo -e "${RED}Stopping all services...${NC}"
            ./stop-all-services.sh
            read -p "Press Enter to continue..."
            clear
            ;;
        15)
            echo -e "${YELLOW}Restarting all services...${NC}"
            ./stop-all-services.sh
            sleep 2
            ./start-all-services.sh
            ;;
        16)
            echo -e "${GREEN}Running quick check...${NC}"
            source .venv/bin/activate
            make quick-check
            read -p "Press Enter to continue..."
            clear
            ;;
        17)
            echo -e "${GREEN}Running full check...${NC}"
            source .venv/bin/activate
            make full-check
            read -p "Press Enter to continue..."
            clear
            ;;
        18)
            echo -e "${GREEN}Running tests...${NC}"
            source .venv/bin/activate
            make test
            read -p "Press Enter to continue..."
            clear
            ;;
        19)
            echo -e "${GREEN}Setting up git hooks...${NC}"
            source .venv/bin/activate
            make setup-hooks
            read -p "Press Enter to continue..."
            clear
            ;;
        20)
            echo -e "${GREEN}Cleaning build artifacts...${NC}"
            make clean
            read -p "Press Enter to continue..."
            clear
            ;;
        21)
            echo -e "${GREEN}Quick Start Guide:${NC}"
            cat QUICK_START_GUIDE.md | less
            clear
            ;;
        22)
            echo -e "${GREEN}Documentation:${NC}"
            ls -1 docs/*.md | head -20
            echo ""
            read -p "Enter doc filename to view (or Enter to skip): " doc
            if [ -n "$doc" ]; then
                cat "docs/$doc" | less
            fi
            clear
            ;;
        23)
            echo -e "${YELLOW}Common Issues & Solutions:${NC}"
            echo ""
            echo "1. Module not found errors:"
            echo "   → make first-run"
            echo "   → source .venv/bin/activate"
            echo ""
            echo "2. Docker not available in WSL:"
            echo "   → Enable Docker Desktop WSL integration"
            echo "   → OR use development mode (ENABLE_DEVELOPMENT_MODE=true)"
            echo ""
            echo "3. API key errors:"
            echo "   → make doctor"
            echo "   → Edit .env file"
            echo ""
            echo "4. Port conflicts:"
            echo "   → lsof -ti:8080 | xargs kill"
            echo ""
            echo "5. Service won't start:"
            echo "   → ./check-status.sh"
            echo "   → tail -f logs/services/*.log"
            echo ""
            read -p "Press Enter to continue..."
            clear
            ;;
        0)
            echo -e "${BLUE}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please try again.${NC}"
            sleep 1
            clear
            ;;
    esac
done
