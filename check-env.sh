#!/bin/bash
# Quick environment check script

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Checking .env configuration...${NC}\n"

if [ ! -f .env ]; then
    echo -e "${RED}✗ .env file not found${NC}"
    echo "Run: make init-env"
    exit 1
fi

echo -e "${GREEN}✓ .env file exists${NC}\n"

check_var() {
    local var_name=$1
    local required=$2

    if grep -q "^${var_name}=..*" .env 2>/dev/null && ! grep -q "^${var_name}=.*placeholder" .env 2>/dev/null; then
        value=$(grep "^${var_name}=" .env | cut -d= -f2 | head -c 20)
        echo -e "${GREEN}✓${NC} $var_name is set (${value}...)"
        return 0
    else
        if [ "$required" = "required" ]; then
            echo -e "${RED}✗${NC} $var_name is NOT set or using placeholder"
            return 1
        else
            echo -e "${YELLOW}!${NC} $var_name is NOT set (optional)"
            return 0
        fi
    fi
}

echo "Required variables:"
check_var "DISCORD_BOT_TOKEN" "required"
discord_ok=$?

check_var "OPENROUTER_API_KEY" "optional"
openrouter_ok=$?

check_var "OPENAI_API_KEY" "optional"
openai_ok=$?

echo ""
echo "Optional variables:"
check_var "QDRANT_URL" "optional"
check_var "REDIS_URL" "optional"
check_var "POSTGRES_URL" "optional"

echo ""

if [ $discord_ok -ne 0 ]; then
    echo -e "${RED}ERROR: DISCORD_BOT_TOKEN must be set${NC}"
    echo "Get token from: https://discord.com/developers/applications"
    exit 1
fi

if [ $openrouter_ok -ne 0 ] && [ $openai_ok -ne 0 ]; then
    echo -e "${YELLOW}WARNING: Neither OPENROUTER_API_KEY nor OPENAI_API_KEY is set${NC}"
    echo "At least one LLM API key is required for the bot to work"
    echo "Get keys from:"
    echo "  - OpenRouter: https://openrouter.ai/keys"
    echo "  - OpenAI: https://platform.openai.com/api-keys"
    exit 1
fi

echo -e "${GREEN}✓ Configuration looks good!${NC}"
echo ""
echo "You can now start services with:"
echo "  ./manage-services.sh"
echo "  ./start-all-services.sh"
