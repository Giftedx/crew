#!/usr/bin/env python3
"""
API Configuration Diagnostic Tool

Relocated from repository root (formerly test_apis.py) to scripts/diagnostics/.
Use this as an ad-hoc health check, not a pytest test.
Run: python scripts/diagnostics/api_diagnostic.py
"""

import os
import sys

# Add src to path
sys.path.append("src")

from dotenv import load_dotenv


def print_header(title):
    print(f"\n{'=' * 50}")
    print(f"🔍 {title}")
    print(f"{'=' * 50}")


def print_status(service, status, message):
    icon = "✅" if status else "❌"
    print(f"{icon} {service}: {message}")


def check_env_vars():
    print_header("Environment Variables Check")

    # Load .env file
    load_dotenv()

    required_vars = {
        "DISCORD_BOT_TOKEN": "Discord bot token",
        "QDRANT_URL": "Qdrant vector database URL",
    }

    optional_vars = {
        "OPENAI_API_KEY": "OpenAI API key",
        "OPENROUTER_API_KEY": "OpenRouter API key",
        "DISCORD_WEBHOOK_URL": "Discord webhook URL",
        "DISCORD_PRIVATE_WEBHOOK_URL": "Discord private webhook URL",
        "SERPLY_API_KEY": "Serply search API key",
        "EXA_API_KEY": "Exa search API key",
        "PERPLEXITY_API_KEY": "Perplexity API key",
        "WOLFRAM_ALPHA_APP_ID": "WolframAlpha app ID",
    }

    print("📋 Required Variables:")
    missing_required = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Check for common issues
            if len(value.strip()) != len(value):
                print_status(var, False, f"Has whitespace (length: {len(value)}, trimmed: {len(value.strip())})")
            elif "\n" in value or "\r" in value:
                print_status(var, False, f"Contains line breaks (length: {len(value)})")
            else:
                print_status(var, True, f"Set correctly ({len(value)} chars)")
        else:
            print_status(var, False, "Missing")
            missing_required.append(var)

    print("\n📋 Optional Variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            if len(value.strip()) != len(value):
                print_status(var, False, f"Has whitespace (length: {len(value)})")
            elif "\n" in value or "\r" in value:
                print_status(var, False, f"Contains line breaks (length: {len(value)})")
            else:
                print_status(var, True, f"Set ({len(value)} chars)")
        else:
            print_status(var, False, "Not configured")

    # Check for LLM API
    print("\n🤖 LLM API Check:")
    has_openai = bool(os.getenv("OPENAI_API_KEY", "").strip())
    has_openrouter = bool(os.getenv("OPENROUTER_API_KEY", "").strip())

    if has_openai or has_openrouter:
        print_status(
            "LLM API",
            True,
            f"Available ({'OpenAI' if has_openai else ''}{' & ' if has_openai and has_openrouter else ''}{'OpenRouter' if has_openrouter else ''})",
        )
    else:
        print_status("LLM API", False, "No LLM API configured")
        missing_required.append("OPENAI_API_KEY or OPENROUTER_API_KEY")

    return len(missing_required) == 0


def test_discord_token():
    print_header("Discord Bot Token Test")

    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        print_status("Discord Token", False, "Not configured")
        return False

    # Basic format validation
    if not token.startswith(("MTk", "Nz", "Bot ")):
        print_status("Discord Token", False, f"Invalid format (starts with: {token[:10]}...)")
        return False

    try:
        # Optional: check discord presence without importing heavy module at runtime
        import importlib.util as _il

        has_discord = _il.find_spec("discord") is not None
        print_status("Discord.py", has_discord, "Library available" if has_discord else "Not installed")
        print_status("Discord Token", True, f"Format looks correct ({len(token)} chars)")
        return True
    except Exception as e:
        print_status("Discord.py", False, f"Probe failed: {str(e)[:60]}")


def test_openai_api():
    print_header("OpenAI API Test")

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print_status("OpenAI Key", False, "Not configured")
        return False

    if not api_key.startswith("sk-"):
        print_status("OpenAI Key", False, f"Invalid format (starts with: {api_key[:10]}...)")
        return False

    try:
        import openai

        print_status("OpenAI Library", True, "Available")

        # Test API call
        try:
            client = openai.OpenAI(api_key=api_key)
            # Simple test - list models (cheap call)
            models = client.models.list()
            print_status("OpenAI API", True, f"Connection successful ({len(models.data)} models available)")
            return True
        except Exception as e:
            error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
            print_status("OpenAI API", False, f"API call failed: {error_msg}")
            return False
    except ImportError:
        print_status("OpenAI Library", False, "Not installed")
        return False


def test_qdrant():
    print_header("Qdrant Vector Database Test")

    url = os.getenv("QDRANT_URL", "").strip()
    if not url:
        print_status("Qdrant URL", False, "Not configured")
        return False

    try:
        from qdrant_client import QdrantClient

        print_status("Qdrant Library", True, "Available")

        # Test connection
        api_key = os.getenv("QDRANT_API_KEY", "").strip() or None
        client = QdrantClient(url=url, api_key=api_key)
        collections = client.get_collections()
        print_status("Qdrant Connection", True, f"Connected ({len(collections.collections)} collections)")
        return True
    except ImportError:
        print_status("Qdrant Library", False, "Not installed")
        return False
    except Exception as e:
        error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
        print_status("Qdrant Connection", False, f"Connection failed: {error_msg}")
        return False


def test_optional_apis():
    print_header("Optional APIs Test")

    results = {}

    # Test Serply
    serply_key = os.getenv("SERPLY_API_KEY", "").strip()
    if serply_key:
        try:
            import requests

            response = requests.get(
                "https://api.serply.io/v1/search",
                params={"q": "test", "num": 1},
                headers={"X-API-KEY": serply_key},
                timeout=10,
            )
            if response.status_code == 200:
                print_status("Serply API", True, "Connection successful")
                results["serply"] = True
            else:
                print_status("Serply API", False, f"HTTP {response.status_code}")
                results["serply"] = False
        except Exception as e:
            print_status("Serply API", False, f"Error: {str(e)[:50]}...")
            results["serply"] = False
    else:
        print_status("Serply API", False, "Not configured")
        results["serply"] = False

    # Test other APIs similarly...
    exa_key = os.getenv("EXA_API_KEY", "").strip()
    print_status("Exa API", bool(exa_key), "Configured" if exa_key else "Not configured")

    perplexity_key = os.getenv("PERPLEXITY_API_KEY", "").strip()
    print_status("Perplexity API", bool(perplexity_key), "Configured" if perplexity_key else "Not configured")

    return results


def test_bot_tools():
    print_header("Bot Tools Test")

    try:
        from ultimate_discord_intelligence_bot.tools.fact_check_tool import FactCheckTool

        fact_tool = FactCheckTool()
        result = fact_tool.run("The sky is blue")
        status = result.get("status") == "success"
        print_status("Fact Check Tool", status, "Working" if status else f"Error: {result.get('error', 'Unknown')}")
    except Exception as e:
        print_status("Fact Check Tool", False, f"Import/run error: {str(e)[:50]}...")

    try:
        from ultimate_discord_intelligence_bot.tools.logical_fallacy_tool import LogicalFallacyTool

        fallacy_tool = LogicalFallacyTool()
        result = fallacy_tool.run("Everyone believes this so it must be true")
        has_fallacies = len(result.get("fallacies", [])) > 0
        print_status(
            "Fallacy Detection", has_fallacies, f"Working ({len(result.get('fallacies', []))} fallacies detected)"
        )
    except Exception as e:
        print_status("Fallacy Detection", False, f"Error: {str(e)[:50]}...")


def main():
    print("🔍 Ultimate Discord Intelligence Bot - API Diagnostic")
    print("=" * 60)
    print("This tool will test all your configured APIs and identify issues.")
    print()

    # Test each component
    env_ok = check_env_vars()
    discord_ok = test_discord_token()
    openai_ok = test_openai_api()
    qdrant_ok = test_qdrant()
    optional_results = test_optional_apis()
    test_bot_tools()

    # Final summary
    print_header("Summary & Recommendations")

    if env_ok and discord_ok and (openai_ok) and qdrant_ok:
        print("🎉 All required APIs are configured and working!")
        print("✅ Your bot should work perfectly.")
    else:
        print("⚠️  Some issues found:")
        if not env_ok:
            print("   • Fix environment variable loading")
        if not discord_ok:
            print("   • Fix Discord bot token")
        if not openai_ok:
            print("   • Fix OpenAI API configuration")
        if not qdrant_ok:
            print("   • Fix Qdrant database connection")

    # Optional improvements
    optional_count = sum(1 for v in optional_results.values() if v)
    print(f"\n💡 Optional APIs: {optional_count} configured")

    print("\n🚀 Next Steps:")
    print("   1. Fix any ❌ issues shown above")
    print("   2. Run: python -m ultimate_discord_intelligence_bot.setup_cli run discord")
    print("   3. Test with: !status in Discord")


if __name__ == "__main__":
    main()
