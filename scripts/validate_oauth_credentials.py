#!/usr/bin/env python3
"""
OAuth Credentials and Scopes Validation Script

This script validates OAuth credentials and scopes for all supported platforms:
- YouTube Data API v3
- Twitch Helix API
- TikTok Research API
- Instagram Graph API
- X (Twitter) API v2

Usage:
    python scripts/validate_oauth_credentials.py
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultimate_discord_intelligence_bot.creator_ops.auth.oauth_manager import (
    InstagramOAuthManager,
    TikTokOAuthManager,
    TwitchOAuthManager,
    XOAuthManager,
    YouTubeOAuthManager,
)
from ultimate_discord_intelligence_bot.creator_ops.auth.scopes import ScopeValidator


def check_environment_variables() -> Dict[str, Any]:
    """Check for required environment variables."""
    print("🔍 Checking Environment Variables...")

    # Required API keys
    required_vars = {
        "DISCORD_BOT_TOKEN": "Discord bot authentication",
        "OPENAI_API_KEY": "OpenAI API access (or OPENROUTER_API_KEY)",
        "OPENROUTER_API_KEY": "OpenRouter API access (alternative to OpenAI)",
        "QDRANT_URL": "Vector database connection",
    }

    # Platform-specific OAuth credentials
    platform_vars = {
        "YOUTUBE_CLIENT_ID": "YouTube OAuth client ID",
        "YOUTUBE_CLIENT_SECRET": "YouTube OAuth client secret",
        "TWITCH_CLIENT_ID": "Twitch OAuth client ID",
        "TWITCH_CLIENT_SECRET": "Twitch OAuth client secret",
        "TIKTOK_CLIENT_KEY": "TikTok OAuth client key",
        "TIKTOK_CLIENT_SECRET": "TikTok OAuth client secret",
        "INSTAGRAM_APP_ID": "Instagram OAuth app ID",
        "INSTAGRAM_APP_SECRET": "Instagram OAuth app secret",
        "X_CLIENT_ID": "X (Twitter) OAuth client ID",
        "X_CLIENT_SECRET": "X (Twitter) OAuth client secret",
    }

    results = {
        "required_vars": {},
        "platform_vars": {},
        "missing_required": [],
        "missing_platform": [],
        "status": "success",
    }

    # Check required variables
    for var, description in required_vars.items():
        value = os.getenv(var)
        if var == "OPENAI_API_KEY":
            # Allow either OpenAI or OpenRouter
            if not (os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")):
                results["missing_required"].append(
                    f"{var} (or OPENROUTER_API_KEY): {description}"
                )
            else:
                results["required_vars"][var] = "✅ Set (or alternative provided)"
        elif value:
            results["required_vars"][var] = "✅ Set"
        else:
            results["missing_required"].append(f"{var}: {description}")

    # Check platform variables (optional for basic functionality)
    for var, description in platform_vars.items():
        value = os.getenv(var)
        if value:
            results["platform_vars"][var] = "✅ Set"
        else:
            results["missing_platform"].append(f"{var}: {description}")

    if results["missing_required"]:
        results["status"] = "error"

    return results


def validate_oauth_scopes() -> Dict[str, Any]:
    """Validate OAuth scopes for all platforms."""
    print("🔍 Validating OAuth Scopes...")

    validator = ScopeValidator()
    results = {"platforms": {}, "status": "success"}

    # Test scope validation for each platform
    platforms = ["youtube", "twitch", "tiktok", "instagram", "x"]

    for platform in platforms:
        platform_results = {
            "compliance_summary": {},
            "scope_validation": {},
            "status": "success",
        }

        try:
            # Get compliance summary
            summary = validator.get_platform_compliance_summary(platform)
            platform_results["compliance_summary"] = summary

            # Test scope validation for different purposes
            if platform == "youtube":
                purposes = ["readonly", "full"]
            elif platform == "twitch":
                purposes = ["basic", "streamer", "moderator", "full"]
            elif platform == "tiktok":
                purposes = ["basic", "content", "publish"]
            elif platform == "instagram":
                purposes = ["basic", "insights", "content"]
            elif platform == "x":
                purposes = ["read", "write", "full"]

            for purpose in purposes:
                try:
                    # Get minimal scopes for this purpose
                    minimal_scopes = validator.get_minimal_scopes(platform, purpose)

                    # Validate the minimal scopes
                    validation_result = validator.validate_scopes(
                        platform, minimal_scopes, purpose
                    )

                    platform_results["scope_validation"][purpose] = {
                        "minimal_scopes": minimal_scopes,
                        "validation_result": validation_result.data
                        if validation_result.success
                        else validation_result.error,
                        "status": "success" if validation_result.success else "error",
                    }

                except Exception as e:
                    platform_results["scope_validation"][purpose] = {
                        "error": str(e),
                        "status": "error",
                    }
                    platform_results["status"] = "error"

        except Exception as e:
            platform_results["error"] = str(e)
            platform_results["status"] = "error"
            results["status"] = "error"

        results["platforms"][platform] = platform_results

    return results


def test_oauth_managers() -> Dict[str, Any]:
    """Test OAuth manager initialization (without actual API calls)."""
    print("🔍 Testing OAuth Manager Initialization...")

    results = {"managers": {}, "status": "success"}

    # Test each OAuth manager
    managers = {
        "youtube": YouTubeOAuthManager,
        "twitch": TwitchOAuthManager,
        "tiktok": TikTokOAuthManager,
        "instagram": InstagramOAuthManager,
        "x": XOAuthManager,
    }

    for platform, manager_class in managers.items():
        try:
            # Get credentials from environment
            if platform == "youtube":
                client_id = os.getenv("YOUTUBE_CLIENT_ID", "test_client_id")
                client_secret = os.getenv("YOUTUBE_CLIENT_SECRET", "test_client_secret")
            elif platform == "twitch":
                client_id = os.getenv("TWITCH_CLIENT_ID", "test_client_id")
                client_secret = os.getenv("TWITCH_CLIENT_SECRET", "test_client_secret")
            elif platform == "tiktok":
                client_id = os.getenv("TIKTOK_CLIENT_KEY", "test_client_key")
                client_secret = os.getenv("TIKTOK_CLIENT_SECRET", "test_client_secret")
            elif platform == "instagram":
                client_id = os.getenv("INSTAGRAM_APP_ID", "test_app_id")
                client_secret = os.getenv("INSTAGRAM_APP_SECRET", "test_app_secret")
            elif platform == "x":
                client_id = os.getenv("X_CLIENT_ID", "test_client_id")
                client_secret = os.getenv("X_CLIENT_SECRET", "test_client_secret")

            # Initialize manager with test credentials
            # Use platform-specific parameter names
            if platform == "tiktok":
                manager_class(
                    client_key=client_id,
                    client_secret=client_secret,
                    redirect_uri="http://localhost:8080/callback",
                    scopes=["test_scope"],
                )
            elif platform == "instagram":
                manager_class(
                    app_id=client_id,
                    app_secret=client_secret,
                    redirect_uri="http://localhost:8080/callback",
                    scopes=["test_scope"],
                )
            else:
                manager_class(
                    client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri="http://localhost:8080/callback",
                    scopes=["test_scope"],
                )

            results["managers"][platform] = {
                "initialization": "✅ Success",
                "client_id_set": "✅ Set"
                if client_id != "test_client_id"
                else "⚠️ Using test value",
                "client_secret_set": "✅ Set"
                if client_secret != "test_client_secret"
                else "⚠️ Using test value",
                "status": "success",
            }

        except Exception as e:
            results["managers"][platform] = {
                "initialization": f"❌ Failed: {str(e)}",
                "client_id_set": "❌ Not set",
                "client_secret_set": "❌ Not set",
                "status": "error",
            }
            results["status"] = "error"

    return results


def generate_oauth_report(
    env_results: Dict[str, Any],
    scope_results: Dict[str, Any],
    manager_results: Dict[str, Any],
) -> str:
    """Generate a comprehensive OAuth validation report."""
    report = []
    report.append("# OAuth Credentials and Scopes Validation Report")
    report.append("=" * 60)
    report.append("")

    # Environment Variables Section
    report.append("## Environment Variables")
    report.append("")

    if env_results["required_vars"]:
        report.append("### ✅ Required Variables (Set)")
        for var, status in env_results["required_vars"].items():
            report.append(f"- {var}: {status}")
        report.append("")

    if env_results["missing_required"]:
        report.append("### ❌ Missing Required Variables")
        for var in env_results["missing_required"]:
            report.append(f"- {var}")
        report.append("")

    if env_results["platform_vars"]:
        report.append("### ✅ Platform Variables (Set)")
        for var, status in env_results["platform_vars"].items():
            report.append(f"- {var}: {status}")
        report.append("")

    if env_results["missing_platform"]:
        report.append("### ⚠️ Missing Platform Variables (Optional)")
        for var in env_results["missing_platform"]:
            report.append(f"- {var}")
        report.append("")

    # OAuth Scopes Section
    report.append("## OAuth Scopes Validation")
    report.append("")

    for platform, platform_data in scope_results["platforms"].items():
        report.append(f"### {platform.title()} Platform")

        if "compliance_summary" in platform_data:
            summary = platform_data["compliance_summary"]
            if "error" not in summary:
                report.append(
                    f"- Available purposes: {', '.join(summary.get('available_purposes', []))}"
                )
                report.append(f"- Total scopes: {summary.get('total_scopes', 0)}")
                report.append(
                    f"- Sensitive scopes: {len(summary.get('sensitive_scopes', []))}"
                )
            else:
                report.append(f"- ❌ Error: {summary['error']}")

        if "scope_validation" in platform_data:
            report.append("- Scope validation by purpose:")
            for purpose, validation in platform_data["scope_validation"].items():
                if validation["status"] == "success":
                    report.append(f"  - {purpose}: ✅ Valid")
                else:
                    report.append(
                        f"  - {purpose}: ❌ {validation.get('error', 'Validation failed')}"
                    )

        report.append("")

    # OAuth Managers Section
    report.append("## OAuth Manager Initialization")
    report.append("")

    for platform, manager_data in manager_results["managers"].items():
        report.append(f"### {platform.title()} Manager")
        report.append(f"- Initialization: {manager_data['initialization']}")
        report.append(f"- Client ID: {manager_data['client_id_set']}")
        report.append(f"- Client Secret: {manager_data['client_secret_set']}")
        report.append("")

    # Summary
    report.append("## Summary")
    report.append("")

    overall_status = "✅ SUCCESS"
    if (
        env_results["status"] == "error"
        or scope_results["status"] == "error"
        or manager_results["status"] == "error"
    ):
        overall_status = "❌ ISSUES FOUND"

    report.append(f"**Overall Status: {overall_status}**")
    report.append("")

    if env_results["missing_required"]:
        report.append("### Required Actions:")
        report.append("1. Set missing required environment variables")
        report.append("2. Restart the application after setting variables")
        report.append("")

    if env_results["missing_platform"]:
        report.append("### Optional Actions:")
        report.append(
            "1. Set platform-specific OAuth credentials for full functionality"
        )
        report.append("2. Configure OAuth redirect URIs in platform developer consoles")
        report.append("")

    return "\n".join(report)


def main():
    """Main validation function."""
    print("🚀 Starting OAuth Credentials and Scopes Validation")
    print("=" * 60)
    print("")

    # Run all validation checks
    env_results = check_environment_variables()
    scope_results = validate_oauth_scopes()
    manager_results = test_oauth_managers()

    # Generate and display report
    report = generate_oauth_report(env_results, scope_results, manager_results)
    print(report)

    # Save report to file
    report_path = Path("oauth_validation_report.md")
    with open(report_path, "w") as f:
        f.write(report)

    print(f"📄 Report saved to: {report_path}")

    # Exit with appropriate code
    if env_results["status"] == "error":
        print("\n❌ Validation failed due to missing required environment variables")
        sys.exit(1)
    else:
        print("\n✅ OAuth validation completed successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()
