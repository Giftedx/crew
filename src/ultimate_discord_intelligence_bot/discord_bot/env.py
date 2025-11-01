from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv  # type: ignore


try:
    from scripts.helpers.ui_constants import DEFAULT_FEATURE_FLAGS
except ImportError:
    # Fallback when scripts.helpers not available
    DEFAULT_FEATURE_FLAGS = {}


def check_environment() -> bool:
    """Check if required environment variables are set.

    This mirrors the original script's logic but is centralized for reuse.
    """
    load_dotenv()

    optional_services: list[str] = []

    # Auto-detect Google credentials if not explicitly set
    try:
        if not os.getenv("GOOGLE_CREDENTIALS"):
            base = os.getenv("CREWAI_BASE_DIR") or str(Path.home() / "crew_data")
            candidates = [
                Path(base).expanduser() / "Config" / "google-credentials.json",
                Path("/home/crew/crew_data/Config/google-credentials.json"),
            ]
            for cand in candidates:
                try:
                    if cand.exists() and cand.is_file():
                        os.environ["GOOGLE_CREDENTIALS"] = str(cand)
                        break
                except Exception:
                    continue
    except Exception:
        pass

    if not os.getenv("GOOGLE_CREDENTIALS"):
        os.environ["DISABLE_GOOGLE_DRIVE"] = "true"
        optional_services.append("Google Drive uploads")
    else:
        if os.getenv("DISABLE_GOOGLE_DRIVE") == "true":
            os.environ.pop("DISABLE_GOOGLE_DRIVE", None)

    try:
        auth_method = os.getenv("GOOGLE_AUTH_METHOD", "service_account").lower()
        has_folder = bool(os.getenv("GOOGLE_DRIVE_FOLDER_ID"))
        if auth_method == "service_account" and os.getenv("GOOGLE_CREDENTIALS") and not has_folder:
            os.environ["DISABLE_GOOGLE_DRIVE"] = "true"
            if "Google Drive uploads" not in optional_services:
                optional_services.append("Google Drive uploads")
            print(
                "INFO: Google Drive disabled (service account requires GOOGLE_DRIVE_FOLDER_ID pointing to a Shared Drive folder)"
            )
    except Exception:
        pass

    if not os.getenv("DISCORD_WEBHOOK"):
        os.environ["DISCORD_WEBHOOK"] = "https://discord.com/api/webhooks/dummy"
        optional_services.append("Discord notifications")

    if not os.getenv("DISCORD_PRIVATE_WEBHOOK"):
        os.environ["DISCORD_PRIVATE_WEBHOOK"] = "https://discord.com/api/webhooks/dummy_private"
        optional_services.append("Private Discord alerts")

    if optional_services:
        print(f"INFO: Optional services disabled: {', '.join(optional_services)}")
        print("💡 Add API keys to .env for full functionality")

    gateway_enabled = os.getenv("ENABLE_DISCORD_GATEWAY", "1").lower() in {
        "1",
        "true",
        "yes",
    }
    required_vars: dict[str, str] = {}
    if gateway_enabled:
        required_vars["DISCORD_BOT_TOKEN"] = "Discord bot token"

    missing: list[str] = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var}: {description}")

    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        if "DISCORD_BOT_TOKEN: Discord bot token" in missing:
            print(
                "💡 To run without the Discord gateway, set ENABLE_DISCORD_GATEWAY=0 (headless agent mode)\n"
                "   The agent will still ingest/process and post via webhooks if configured."
            )
            os.environ["ENABLE_DISCORD_GATEWAY"] = "0"
            print("↩️  ENABLE_DISCORD_GATEWAY=0 (auto) - proceeding in headless agent mode")
            return True
        return False

    return True


def enable_autonomous_defaults() -> None:
    """Enable autonomous-mode defaults without overriding user settings."""

    def _set_default(key: str, val: str) -> None:
        if not os.getenv(key):
            os.environ[key] = val

    for k, v in DEFAULT_FEATURE_FLAGS.items():
        _set_default(k, v)

    if not os.getenv("INGEST_DB_PATH"):
        os.environ["INGEST_DB_PATH"] = str(Path(__file__).resolve().parents[3] / "data" / "ingest.db")


__all__ = ["check_environment", "enable_autonomous_defaults"]
