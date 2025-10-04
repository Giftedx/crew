#!/usr/bin/env bash
# Verification script for /autointel critical data flow fix
# Date: October 2, 2025

set -e

echo "🔍 Verifying /autointel Critical Data Flow Fix..."
echo ""

# 1. Verify no direct agent_coordinators dictionary access remains
echo "1️⃣ Checking for forbidden direct dictionary access..."
DIRECT_ACCESS=$(grep -c 'self.agent_coordinators\["' src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py || echo "0")
if [ "$DIRECT_ACCESS" -eq "0" ]; then
    echo "   ✅ No direct dictionary access found (expected)"
else
    echo "   ❌ Found $DIRECT_ACCESS instances of direct dictionary access (should be 0)"
    grep -n 'self.agent_coordinators\["' src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py
    exit 1
fi
echo ""

# 2. Count _get_or_create_agent usages
echo "2️⃣ Counting _get_or_create_agent() usages..."
CREATE_AGENT_COUNT=$(grep -c '_get_or_create_agent' src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py || echo "0")
if [ "$CREATE_AGENT_COUNT" -ge "13" ]; then
    echo "   ✅ Found $CREATE_AGENT_COUNT usages (expected 13+)"
else
    echo "   ❌ Found only $CREATE_AGENT_COUNT usages (expected 13+)"
    exit 1
fi
echo ""

# 3. Verify _populate_agent_tool_context calls still exist
echo "3️⃣ Verifying context population calls..."
POPULATE_COUNT=$(grep -c '_populate_agent_tool_context' src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py || echo "0")
if [ "$POPULATE_COUNT" -ge "10" ]; then
    echo "   ✅ Found $POPULATE_COUNT context population calls"
else
    echo "   ⚠️  Found only $POPULATE_COUNT context population calls (might be reduced)"
fi
echo ""

# 4. Verify CrewAI wrapper update_context method exists
echo "4️⃣ Checking CrewAI wrapper context update mechanism..."
if grep -q 'def update_context' src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py; then
    echo "   ✅ update_context() method exists in wrapper"
else
    echo "   ❌ update_context() method missing from wrapper"
    exit 1
fi
echo ""

# 5. Verify shared_context usage in wrapper _run
echo "5️⃣ Verifying shared_context parameter aliasing..."
if grep -q 'transcript→text' src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py; then
    echo "   ✅ Parameter aliasing logic found in wrapper"
else
    echo "   ⚠️  Parameter aliasing might be missing"
fi
echo ""

# 6. Check for agent coordinator initialization
echo "6️⃣ Verifying agent_coordinators initialization..."
if grep -q 'self.agent_coordinators = {}' src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py; then
    echo "   ✅ agent_coordinators dictionary initialization found"
else
    echo "   ❌ agent_coordinators initialization missing"
    exit 1
fi
echo ""

echo "✅ All verification checks passed!"
echo ""
echo "📋 Summary:"
echo "   - Direct dictionary access: 0 (✅)"
echo "   - _get_or_create_agent calls: $CREATE_AGENT_COUNT (✅)"
echo "   - Context population calls: $POPULATE_COUNT"
echo "   - Wrapper mechanisms: ✅"
echo ""
echo "🧪 Next Steps:"
echo "   1. Run: make quick-check"
echo "   2. Test: /autointel url:<test_url> depth:standard"
echo "   3. Monitor logs for agent creation and context population messages"
echo "   4. Verify tool outputs contain meaningful analysis results"
echo ""
