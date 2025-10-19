#!/usr/bin/env bash
# Enable Background Intelligence Processing - No Time Limits
#
# This script converts the /autointel command from synchronous (15-minute limit)
# to asynchronous background processing (unlimited time).
#
# Usage:
#   ./scripts/enable_background_processing.sh
#
# What it does:
#   1. Checks for required DISCORD_WEBHOOK environment variable
#   2. Creates data directory for workflow storage
#   3. Provides integration instructions
#   4. Validates the setup

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   Background Intelligence Processing Setup${NC}"
echo -e "${BLUE}   Unlimited Time Analysis - No 15-Minute Constraint${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Step 1: Check for .env file
echo -e "${YELLOW}[1/5]${NC} Checking environment configuration..."

if [[ ! -f "${PROJECT_ROOT}/.env" ]]; then
    echo -e "${RED}✗ Error: .env file not found${NC}"
    echo ""
    echo "Please create .env from template:"
    echo "  cp .env.example .env"
    echo ""
    exit 1
fi

# Step 2: Check for DISCORD_WEBHOOK
echo -e "${YELLOW}[2/5]${NC} Checking Discord webhook configuration..."

# Load .env
source "${PROJECT_ROOT}/.env" 2>/dev/null || true

if [[ -z "${DISCORD_WEBHOOK:-}" ]]; then
    echo -e "${RED}✗ DISCORD_WEBHOOK not configured${NC}"
    echo ""
    echo -e "${YELLOW}Action Required:${NC}"
    echo ""
    echo "1. Go to Discord server settings → Integrations → Webhooks"
    echo "2. Click 'New Webhook'"
    echo "3. Choose the channel where results should be posted"
    echo "4. Copy the webhook URL"
    echo "5. Add to .env file:"
    echo ""
    echo "   DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN"
    echo ""
    echo "6. Run this script again"
    echo ""
    exit 1
else
    echo -e "${GREEN}✓ DISCORD_WEBHOOK configured${NC}"
    # Mask the webhook URL for security
    masked_webhook=$(echo "${DISCORD_WEBHOOK}" | sed 's/\(webhooks\/[0-9]*\/\).*/\1***/')
    echo "  → ${masked_webhook}"
fi

# Step 3: Create data directory
echo -e "${YELLOW}[3/5]${NC} Creating workflow storage directory..."

WORKFLOW_DIR="${PROJECT_ROOT}/data/background_workflows"
mkdir -p "${WORKFLOW_DIR}"

if [[ -d "${WORKFLOW_DIR}" ]]; then
    echo -e "${GREEN}✓ Workflow storage directory created${NC}"
    echo "  → ${WORKFLOW_DIR}"
else
    echo -e "${RED}✗ Failed to create directory${NC}"
    exit 1
fi

# Step 4: Validate module imports
echo -e "${YELLOW}[4/5]${NC} Validating Python modules..."

cd "${PROJECT_ROOT}"

# Check if venv is activated or activate it
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    if [[ -f ".venv/bin/activate" ]]; then
        source .venv/bin/activate
    else
        echo -e "${RED}✗ Virtual environment not found${NC}"
        echo "Please create venv: python -m venv .venv"
        exit 1
    fi
fi

# Test imports
python -c "
try:
    from ultimate_discord_intelligence_bot.background_intelligence_worker import BackgroundIntelligenceWorker
    from ultimate_discord_intelligence_bot.background_autointel_handler import handle_autointel_background, handle_retrieve_results
    print('✓ All modules imported successfully')
except ImportError as e:
    print(f'✗ Import error: {e}')
    exit(1)
" || {
    echo -e "${RED}✗ Module validation failed${NC}"
    echo ""
    echo "Please ensure all dependencies are installed:"
    echo "  pip install -e ."
    exit 1
}

echo -e "${GREEN}✓ All required modules available${NC}"

# Step 5: Provide integration instructions
echo -e "${YELLOW}[5/5]${NC} Setup complete! Next steps for integration..."
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Background Processing Ready${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cat << 'EOF'
Integration Steps:

1. Initialize Background Worker
   Add to your Discord bot setup (e.g., scripts/start_full_bot.py):

   ```python
   from ultimate_discord_intelligence_bot.autonomous_orchestrator import (
       AutonomousIntelligenceOrchestrator,
   )
   from ultimate_discord_intelligence_bot.background_intelligence_worker import (
       BackgroundIntelligenceWorker,
   )

   # Initialize orchestrator
   orchestrator = AutonomousIntelligenceOrchestrator()

   # Initialize background worker
   background_worker = BackgroundIntelligenceWorker(
       orchestrator=orchestrator,
       storage_dir="data/background_workflows",
   )
   ```

2. Replace /autointel Command Handler
   Change from synchronous to asynchronous:

   ```python
   from ultimate_discord_intelligence_bot.background_autointel_handler import (
       handle_autointel_background,
   )

   @bot.tree.command(
       name="autointel",
       description="Autonomous intelligence analysis (unlimited time)"
   )
   async def autointel_command(
       interaction: discord.Interaction,
       url: str,
       depth: str = "standard"
   ):
       await handle_autointel_background(
           interaction=interaction,
           orchestrator=orchestrator,
           background_worker=background_worker,
           url=url,
           depth=depth,
       )
   ```

3. Add /retrieve_results Command
   For manual result retrieval:

   ```python
   from ultimate_discord_intelligence_bot.background_autointel_handler import (
       handle_retrieve_results,
   )

   @bot.tree.command(
       name="retrieve_results",
       description="Retrieve completed intelligence analysis"
   )
   async def retrieve_results_command(
       interaction: discord.Interaction,
       workflow_id: str
   ):
       await handle_retrieve_results(
           interaction=interaction,
           background_worker=background_worker,
           workflow_id=workflow_id,
       )
   ```

4. Sync Commands
   After modifying commands:

   ```python
   await bot.tree.sync()  # Global (up to 1 hour)
   # OR for dev server:
   await bot.tree.sync(guild=discord.Object(id=YOUR_GUILD_ID))
   ```

5. Test the System
   Run a long analysis to verify unlimited time:

   /autointel url:https://youtube.com/watch?v=... depth:comprehensive

   Expected behavior:
   ✓ Immediate acknowledgment (< 3 seconds)
   ✓ Background processing continues beyond 15 minutes
   ✓ Results delivered via webhook when complete
   ✓ No interaction token errors

EOF

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Documentation:${NC}"
echo "  → BACKGROUND_PROCESSING_IMPLEMENTATION.md"
echo ""
echo -e "${YELLOW}Key Benefits:${NC}"
echo "  ✅ No 15-minute time limit"
echo "  ✅ Rigorous fact-checking without rushing"
echo "  ✅ Comprehensive validation of all claims"
echo "  ✅ Automatic webhook delivery"
echo "  ✅ Persistent result storage"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${GREEN}Setup complete! 🚀${NC}"
echo ""
