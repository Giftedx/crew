#!/usr/bin/env bash
# Quick fix script for /autointel performance issues
# See docs/operations/AUTOINTEL_PERFORMANCE_ISSUES.md for details

set -e

echo "🔧 Applying /autointel Performance Fixes"
echo "========================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env from template"
fi

echo ""
echo "📋 Applying fixes to .env..."
echo ""

# Function to add or update env var
add_or_update_env() {
    local key=$1
    local value=$2
    local comment=$3

    if grep -q "^${key}=" .env; then
        # Update existing
        sed -i.bak "s|^${key}=.*|${key}=${value}|" .env
        echo "  ✓ Updated: ${key}=${value}"
    elif grep -q "^# ${key}=" .env; then
        # Uncomment and set
        sed -i.bak "s|^# ${key}=.*|${key}=${value}|" .env
        echo "  ✓ Enabled: ${key}=${value}"
    else
        # Add new
        echo "" >> .env
        [ -n "$comment" ] && echo "# $comment" >> .env
        echo "${key}=${value}" >> .env
        echo "  ✓ Added: ${key}=${value}"
    fi
}

# 1. Disable PostHog telemetry (reduces log noise)
echo "1️⃣ Disabling PostHog telemetry..."
add_or_update_env "CREWAI_DISABLE_TELEMETRY" "1" "Disable CrewAI PostHog analytics"
add_or_update_env "TELEMETRY_OPT_OUT" "1" ""

# 2. Enable parallel execution (speed improvements)
echo ""
echo "2️⃣ Enabling parallel execution..."
add_or_update_env "ENABLE_PARALLEL_MEMORY_OPS" "1" "Enable parallel memory operations for faster workflow"
add_or_update_env "ENABLE_PARALLEL_ANALYSIS" "1" ""
add_or_update_env "ENABLE_PARALLEL_FACT_CHECKING" "1" ""

# 3. Enable orphaned result notifications
echo ""
echo "3️⃣ Enabling orphaned result notifications..."
add_or_update_env "ENABLE_ORPHANED_RESULT_NOTIFICATIONS" "1" "Notify when workflows complete after Discord token expiry"
add_or_update_env "ORPHANED_RESULTS_CHECK_INTERVAL" "300" "Check every 5 minutes"

# 4. Performance optimizations
echo ""
echo "4️⃣ Applying performance optimizations..."
add_or_update_env "ENABLE_PROMPT_COMPRESSION" "1" "Reduce token usage"
add_or_update_env "ENABLE_GPTCACHE" "1" "Enable caching"
add_or_update_env "ENABLE_SEMANTIC_CACHE_SHADOW" "1" "Enable semantic cache in shadow mode"

# 5. Suggest faster model (optional - commented out)
echo ""
echo "5️⃣ Model suggestions (optional)..."
if ! grep -q "OPENAI_MODEL_NAME" .env; then
    echo "# Uncomment for faster (but potentially lower quality) responses:" >> .env
    echo "# OPENAI_MODEL_NAME=gpt-4o-mini" >> .env
    echo "  ℹ️  Added commented suggestion: OPENAI_MODEL_NAME=gpt-4o-mini"
else
    echo "  ℹ️  OPENAI_MODEL_NAME already configured"
fi

# Cleanup backup
rm -f .env.bak

echo ""
echo "✅ Fixes applied successfully!"
echo ""
echo "📝 Summary of changes:"
echo "  • Disabled PostHog telemetry (quieter logs)"
echo "  • Enabled parallel execution (faster workflows)"
echo "  • Enabled orphaned result notifications (better UX)"
echo "  • Enabled caching and compression (better performance)"
echo ""
echo "⚠️  Known limitations:"
echo "  • Discord interaction tokens expire after 15 minutes"
echo "  • Long workflows (>15min) may not post final results to Discord"
echo "  • Consider implementing webhook fallback (see docs)"
echo ""
echo "📖 For more details, see:"
echo "   docs/operations/AUTOINTEL_PERFORMANCE_ISSUES.md"
echo ""
echo "🔄 Restart your Discord bot for changes to take effect:"
echo "   python -m ultimate_discord_intelligence_bot.setup_cli run discord"
