from __future__ import annotations
import asyncio
import contextlib
import os
import sys
import traceback
from platform.http.http_utils import REQUEST_TIMEOUT_SECONDS, retrying_post
from platform.config.configuration import get_config as _get_secure_config
from core.time import default_utc_now
from .discord_env import _DISCORD_AVAILABLE, LIGHTWEIGHT_IMPORT, build_intents, commands
from .env import check_environment, enable_autonomous_defaults
from .ingest import start_ingest_workers
from .registrations import _register_events, _register_prefix_commands, _register_slash_commands
from .tools_bootstrap import attach_tools, load_tools


def create_full_bot():
    intents = build_intents()
    bot = commands.Bot(
        command_prefix="!", intents=intents, description="Ultimate Discord Intelligence Bot - Full System"
    )
    tools = load_tools()
    attach_tools(bot, tools)
    try:
        from ultimate_discord_intelligence_bot.background_intelligence_worker import BackgroundIntelligenceWorker
        from ultimate_discord_intelligence_bot.orchestration import OrchestrationStrategy, get_orchestrator

        orchestrator = get_orchestrator(OrchestrationStrategy.AUTONOMOUS)
        background_worker = BackgroundIntelligenceWorker(
            orchestrator=orchestrator, storage_dir="data/background_workflows"
        )
        bot.background_worker = background_worker
        bot.orchestrator = orchestrator
        print("✅ Background worker initialized with unified orchestrator (unlimited analysis time enabled)")
    except Exception as e:
        print(f"⚠️ Background worker not available: {e}")
        bot.background_worker = None
        bot.orchestrator = None
    _register_events(bot)
    user_cmds_enabled = os.getenv("ENABLE_DISCORD_USER_COMMANDS", "0").lower() in {"1", "true", "yes"}
    admin_cmds_enabled = os.getenv("ENABLE_DISCORD_ADMIN_COMMANDS", "0").lower() in {"1", "true", "yes"}
    mode = "agent-only" if not user_cmds_enabled else "user-commands"
    print(f"🧭 Startup mode: {mode} (admin={('on' if admin_cmds_enabled else 'off')})")
    _register_prefix_commands(bot)
    _register_slash_commands(bot)
    return bot


async def main():
    print("🚀 Starting Full Discord Intelligence Bot...")
    gateway_enabled = os.getenv("ENABLE_DISCORD_GATEWAY", "1").lower() in {"1", "true", "yes"}
    if LIGHTWEIGHT_IMPORT or not _DISCORD_AVAILABLE:
        print("⚠️  Discord gateway library not available; switching to headless mode.")
        gateway_enabled = False
    user_cmds_enabled = os.getenv("ENABLE_DISCORD_USER_COMMANDS", "0").lower() in {"1", "true", "yes"}
    admin_cmds_enabled = os.getenv("ENABLE_DISCORD_ADMIN_COMMANDS", "0").lower() in {"1", "true", "yes"}
    if not check_environment():
        sys.exit(1)
    print("✅ Environment variables validated")
    enable_autonomous_defaults()

    async def _run_headless_agent(user_on: bool, admin_on: bool) -> None:
        print(
            f"🧠 Running in headless agent mode (user_cmds={('on' if user_on else 'off')}, admin={('on' if admin_on else 'off')})"
        )
        if os.getenv("ENABLE_INGEST_WORKER", "0") in {"1", "true", "True"}:
            await start_ingest_workers(asyncio.get_running_loop())
        else:
            print("INFO: Ingest workers disabled (ENABLE_INGEST_WORKER=0)")
        print("📨 Discord posts will use webhooks if configured; no gateway commands are exposed.")

        async def _heartbeat_loop():
            try:
                cfg = _get_secure_config()
                try:
                    webhook = cfg.get_webhook("discord_private")
                except Exception:
                    webhook = os.getenv("DISCORD_PRIVATE_WEBHOOK")
                if not webhook:
                    return
                interval = max(300, int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "900")))
                while True:
                    try:
                        ts = default_utc_now().isoformat()
                        retrying_post(
                            webhook,
                            json_payload={"content": f"🫀 Heartbeat: headless agent alive @ {ts}"},
                            headers={"Content-Type": "application/json"},
                            timeout_seconds=REQUEST_TIMEOUT_SECONDS,
                        )
                    except Exception:
                        pass
                    await asyncio.sleep(interval)
            except Exception:
                return

        with contextlib.suppress(Exception):
            asyncio.get_running_loop().create_task(_heartbeat_loop())
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass

    if not gateway_enabled:
        await _run_headless_agent(user_cmds_enabled, admin_cmds_enabled)
    else:
        token = (os.getenv("DISCORD_BOT_TOKEN") or "").strip()
        if not token:
            print("⚠️  DISCORD_BOT_TOKEN not set; running in headless mode.")
            await _run_headless_agent(user_cmds_enabled, admin_cmds_enabled)
            return
        bot = None
        try:
            bot = create_full_bot()
            print("🤖 Starting Discord connection...")
            await bot.start(token, reconnect=False)
        except Exception as e:
            print(f"❌ Failed to start bot: {e}")
            traceback.print_exc()
            auto_fb = os.getenv("AUTO_FALLBACK_HEADLESS", "1").lower() in {"1", "true", "yes", "on"}
            try:
                cfg = _get_secure_config()
                try:
                    webhook = cfg.get_webhook("discord_private")
                except Exception:
                    webhook = os.getenv("DISCORD_PRIVATE_WEBHOOK") or os.getenv("DISCORD_WEBHOOK")
                if webhook:
                    content = "⚠️ Gateway connection failed; falling back to headless mode"
                    retrying_post(
                        webhook,
                        json_payload={"content": content[:1900]},
                        headers={"Content-Type": "application/json"},
                        timeout_seconds=REQUEST_TIMEOUT_SECONDS,
                    )
            except Exception:
                pass
            try:
                if bot is not None:
                    await bot.close()
            except Exception:
                pass
            if auto_fb:
                print("↩️  Falling back to headless agent mode (AUTO_FALLBACK_HEADLESS=1)")
                await _run_headless_agent(user_cmds_enabled, admin_cmds_enabled)
            else:
                sys.exit(1)


__all__ = ["create_full_bot", "main"]
