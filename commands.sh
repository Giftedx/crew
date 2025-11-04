#!/bin/bash
# Quick command reference - Everything you need

cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║          Quick Command Reference - Crew Project               ║
╚═══════════════════════════════════════════════════════════════╝

🎮 MAIN COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ./manage-services.sh        Interactive menu (USE THIS!)
  ./start-all-services.sh     Start services with wizard
  ./check-status.sh           See what's running
  ./check-env.sh              Validate configuration
  ./stop-all-services.sh      Stop everything

📊 MONITORING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  docker compose ps           List containers
  docker compose logs -f      View all logs
  docker stats                Resource usage
  ./check-status.sh           Comprehensive status

🔧 DEVELOPMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  make quick-check            Fast checks (8s)
  make full-check             Complete checks
  make test                   Run tests
  make doctor                 Health check
  make format                 Format code

🚀 START SPECIFIC SERVICES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  make run-discord            Discord bot (basic)
  make run-discord-enhanced   Discord bot (AI features)
  make run-crew               CrewAI agents
  make run-mcp                MCP server

  # API Server
  python -m uvicorn server.app:app --reload

🐳 DOCKER COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  cd ops/deployment/docker

  docker compose up -d                 Start all
  docker compose down                  Stop all
  docker compose restart SERVICE       Restart one
  docker compose logs -f SERVICE       View logs
  docker compose ps                    List status

🌐 ACCESS POINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  API:        http://localhost:8080
  Grafana:    http://localhost:3000 (admin/admin)
  Prometheus: http://localhost:9090
  Qdrant:     http://localhost:6333/dashboard
  MinIO:      http://localhost:9001 (minioadmin/minioadmin)

🆘 TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ./check-env.sh              Check configuration
  make doctor                 Diagnose issues
  docker compose logs         Check errors

  # Kill port
  kill $(lsof -ti :8080)

  # Fresh start
  docker compose down -v
  ./start-all-services.sh

📚 DOCUMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SYSTEM_GUIDE.md             Complete guide
  QUICK_START_GUIDE.md        Quick reference
  FIXES_APPLIED.md            What was fixed today
  docs/                       All documentation

💡 FIRST TIME?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. ./check-env.sh           Verify config
  2. ./manage-services.sh     Launch menu
  3. Select Option 3          Start Discord Bot Enhanced
  4. Test in Discord!         !analyze https://youtube.com/...

🎯 MOST COMMON WORKFLOWS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # Local development
  make run-discord-enhanced

  # Full production stack
  ./manage-services.sh → Option 8

  # Check everything
  ./check-status.sh

  # Stop everything
  ./stop-all-services.sh

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Need help? Run: ./manage-services.sh (Option 23)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
