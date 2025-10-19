from __future__ import annotations

import os
import time
from typing import Any

try:
    from src.core.time import default_utc_now
except ImportError:
    # Fallback if core time module is not available (py311 target)
    from datetime import datetime

    def default_utc_now():
        return datetime.now(datetime.UTC)


from .discord_env import LIGHTWEIGHT_IMPORT, app_commands, commands, discord

try:
    from .ingest import start_ingest_workers
except ImportError:
    # Fallback if ingest module is not available
    async def start_ingest_workers(loop):
        print("⚠️ Ingest workers not available")


def _register_events(bot: Any) -> None:
    @bot.event
    async def on_ready():  # pragma: no cover - side effects
        try:
            user = getattr(bot, "user", None)
            print(f"🤖 Bot logged in as {user}")
            print(f"📊 Connected to {len(getattr(bot, 'guilds', []))} guilds")
        except Exception:
            print("🤖 Bot ready")
        try:
            synced = await bot.tree.sync()
            print(f"✅ Synced {len(synced)} slash commands")
        except Exception as e:
            print(f"⚠️  Could not sync slash commands: {e}")
        print("✅ Discord Intelligence Bot is ready!")

        # Optionally start background ingest worker(s)
        try:
            if os.getenv("ENABLE_INGEST_WORKER", "0") in {"1", "true", "True"} and not getattr(
                bot, "_ingest_workers_started", False
            ):
                bot._ingest_workers_started = True  # type: ignore[attr-defined]
                await start_ingest_workers(bot.loop)
        except Exception as e:
            print(f"⚠️  Failed to start ingest workers: {e}")

    @bot.event
    async def on_command_error(ctx, error):  # pragma: no cover
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❓ Command not found. Use `!help` for available commands.")
        else:
            try:
                await ctx.send(f"❌ Error: {error}")
            except Exception:
                pass
            print(f"Command error: {error}")


def _register_prefix_commands(bot: Any) -> None:
    if LIGHTWEIGHT_IMPORT:
        return
    if os.getenv("ENABLE_DISCORD_USER_COMMANDS", "0").lower() not in {"1", "true", "yes"}:
        return

    @bot.command(name="status")
    async def status_cmd(ctx):
        start = time.time()
        tools_status = {
            "Pipeline Tool": bool(getattr(bot, "pipeline_tool", None)),
            "Debate Tool": bool(getattr(bot, "debate_tool", None)),
            "Fact Check Tool": bool(getattr(bot, "fact_check_tool", None)),
            "Fallacy Tool": bool(getattr(bot, "fallacy_tool", None)),
        }
        try:
            embed = discord.Embed(  # type: ignore
                title="🟢 Bot Status",
                description="Operational overview",
                color=0x00FF00,
            )
            embed.add_field(
                name="🔧 Core Tools",
                value="\n".join([f"• {k}: {'✅' if v else '❌'}" for k, v in tools_status.items()]) or "No tools",
                inline=False,
            )
            elapsed_ms = (time.time() - start) * 1000
            embed.timestamp = default_utc_now()
            embed.set_footer(text=f"Status generated in {elapsed_ms:.1f}ms")
            await ctx.send(embed=embed)
        except Exception:
            await ctx.send("Status: " + ", ".join([f"{k}={'on' if v else 'off'}" for k, v in tools_status.items()]))

    @bot.command(name="help_full")
    async def help_full(ctx):
        try:
            embed = discord.Embed(
                title="🤖 Ultimate Discord Intelligence Bot",
                description="Debate analysis and fact-checking system",
                color=0x00FF00,
            )
            embed.add_field(
                name="Usage",
                value=(
                    "Use slash commands from the / menu (if enabled).\n"
                    "Common toggles: ENABLE_DISCORD_USER_COMMANDS=1, ENABLE_AUTO_URL_ANALYSIS=1"
                ),
                inline=False,
            )
            embed.timestamp = default_utc_now()
            embed.set_footer(text="Help reference")
            await ctx.send(embed=embed)
        except Exception:
            await ctx.send("Ultimate Discord Intelligence Bot — use / for commands if enabled")

    # Also support users who type '/autointel ...' as plain text (not slash UI)
    @bot.event
    async def on_message(message):  # pragma: no cover
        try:
            if getattr(message.author, "bot", False):
                return
            content = getattr(message, "content", "") or ""
            if content.lower().startswith("/autointel"):
                # Reuse the same parsing logic as the prefix command
                text = content

                import re

                def _first_url(s: str) -> str | None:
                    m = re.search(r"https?://\S+", s)
                    return m.group(0) if m else None

                def _extract_depth(s: str) -> str | None:
                    m = re.search(r"(?i)depth\s*:\s*([^\n]+)", s)
                    return m.group(1).strip() if m else None

                def _normalize_depth(raw: str | None) -> str:
                    if not raw:
                        return "standard"
                    v = raw.strip().lower()
                    if v.startswith("exp") or "experimental" in v:
                        return "experimental"
                    if v.startswith("comp") or "comprehensive" in v:
                        return "comprehensive"
                    if v.startswith("deep"):
                        return "deep"
                    return "standard"

                url = _first_url(text)
                depth = _normalize_depth(_extract_depth(text))

                if not url:
                    try:
                        await message.channel.send(
                            "❌ Could not parse URL. Usage examples:\n"
                            "• /autointel url:https://youtu.be/VIDEO depth:Experimental - Cutting-Edge AI\n"
                            "• !autointel https://youtu.be/VIDEO depth:experimental",
                        )
                    except Exception:
                        pass
                    return

                # Build interaction-like adapter
                class _Response:
                    async def defer(self):
                        return None

                    async def send_message(self, content: str | None = None, ephemeral: bool = False):  # noqa: ARG002
                        if content:
                            await message.channel.send(content)

                class _Followup:
                    async def send(self, content: str | None = None, ephemeral: bool = False):  # noqa: ARG002
                        if content:
                            await message.channel.send(content)

                class _Adapter:
                    def __init__(self, msg):
                        self._msg = msg
                        self.response = _Response()
                        self.followup = _Followup()
                        self.guild_id = getattr(getattr(msg, "guild", None), "id", None)
                        self.channel = getattr(msg, "channel", None)

                adapter = _Adapter(message)
                try:
                    await message.channel.send(f"🤖 Starting autointel for: {url} (depth: {depth})")
                except Exception:
                    pass
                await _execute_autointel(adapter, url, depth)
                return  # Don't process as a normal command
        finally:
            # Ensure other commands still work
            try:
                await bot.process_commands(message)
            except Exception:
                pass

    # Add a robust text command fallback for users typing '/autointel url:... depth:...'
    @bot.command(name="autointel")
    async def autointel_cmd(ctx, *, args: str = ""):
        # Parse from the full message content to support '/autointel url:... depth:...'
        text = getattr(ctx, "message", None)
        text = getattr(text, "content", "") if text else ""
        if not text:
            text = args or ""

        import re

        def _first_url(s: str) -> str | None:
            m = re.search(r"https?://\S+", s)
            return m.group(0) if m else None

        def _extract_depth(s: str) -> str | None:
            m = re.search(r"(?i)depth\s*:\s*([^\n]+)", s)
            return m.group(1).strip() if m else None

        def _normalize_depth(raw: str | None) -> str:
            if not raw:
                return "standard"
            v = raw.strip().lower()
            # Accept labels and synonyms
            if v.startswith("exp") or "experimental" in v:
                return "experimental"
            if v.startswith("comp") or "comprehensive" in v:
                return "comprehensive"
            if v.startswith("deep"):
                return "deep"
            return "standard"

        url = _first_url(text)
        depth = _normalize_depth(_extract_depth(text))

        if not url:
            await ctx.send(
                "❌ Could not parse URL. Usage examples:\n"
                "• /autointel url:https://youtu.be/VIDEO depth:Experimental - Cutting-Edge AI\n"
                "• !autointel https://youtu.be/VIDEO depth:experimental",
            )
            return

        # Build a minimal adapter exposing interaction-like API used by executor
        class _Response:
            async def defer(self):
                return None

            async def send_message(self, content: str | None = None, ephemeral: bool = False):  # noqa: ARG002
                if content:
                    await ctx.send(content)

        class _Followup:
            async def send(self, content: str | None = None, ephemeral: bool = False):  # noqa: ARG002
                if content:
                    await ctx.send(content)

        class _Adapter:
            def __init__(self, context):
                self._ctx = context
                self.response = _Response()
                self.followup = _Followup()
                self.guild_id = getattr(getattr(context, "guild", None), "id", None)
                self.channel = getattr(context, "channel", None)

        adapter = _Adapter(ctx)

        # Give quick feedback
        try:
            await ctx.send(f"🤖 Starting autointel for: {url} (depth: {depth})")
        except Exception:
            pass

        await _execute_autointel(adapter, url, depth)


async def _execute_autointel(interaction: Any, url: str, depth: str = "standard") -> None:
    """Shared autointel execution logic for slash and prefix commands."""
    try:
        # Validate inputs first
        if not url or not url.startswith(("http://", "https://")):
            try:
                await interaction.followup.send(
                    "❌ Invalid URL provided. Please provide a valid HTTP/HTTPS URL.",
                    ephemeral=True,
                )
            except Exception:
                pass
            return

        # Normalize depth strings coming from UI labels or free text
        def _normalize_depth(raw: str | None) -> str:
            if not raw:
                return "standard"
            v = str(raw).strip().lower()
            # Accept labels/synonyms like "Experimental - Cutting-Edge AI"
            if v.startswith("exp") or "experimental" in v:
                return "experimental"
            if v.startswith("comp") or "comprehensive" in v:
                return "comprehensive"
            if v.startswith("deep"):
                return "deep"
            return "standard"

        depth = _normalize_depth(depth)

        # Check if background worker is available
        background_worker = getattr(interaction.client, "background_worker", None)
        orchestrator = getattr(interaction.client, "orchestrator", None)

        # If background worker is available, use it for unlimited time processing
        if background_worker and orchestrator:
            print("🚀 Using background worker for unlimited analysis time")
            try:
                from ..background_autointel_handler import handle_autointel_background

                await handle_autointel_background(
                    interaction=interaction,
                    orchestrator=orchestrator,
                    background_worker=background_worker,
                    url=url,
                    depth=depth,
                )
                return
            except Exception as bg_error:
                print(f"⚠️ Background worker failed, falling back to synchronous: {bg_error}")
                # Fall through to synchronous execution

        print("🔄 Attempting to import autonomous orchestrator...")

        # Simplified robust orchestrator loading
        orchestrator = None
        orchestrator_type = "unknown"

        # Priority order: Try AutonomousIntelligenceOrchestrator first (most stable)
        import_attempts = [
            ("direct", "..autonomous_orchestrator", "AutonomousIntelligenceOrchestrator"),
            ("crew", "..crew", "UltimateDiscordIntelligenceBotCrew"),
        ]

        last_error = None
        for attempt_type, module_name, class_name in import_attempts:
            try:
                if attempt_type == "direct":
                    from ..autonomous_orchestrator import AutonomousIntelligenceOrchestrator

                    orchestrator = AutonomousIntelligenceOrchestrator()
                    orchestrator_type = "direct"
                    print("✅ Using AutonomousIntelligenceOrchestrator (direct)")
                    break
                elif attempt_type == "crew":
                    from ..crew import UltimateDiscordIntelligenceBotCrew

                    orchestrator = UltimateDiscordIntelligenceBotCrew().autonomous_orchestrator()
                    orchestrator_type = "crew"
                    print("✅ Using crew-based orchestrator")
                    break
            except Exception as e:
                print(f"⚠️ Failed to load {attempt_type} orchestrator: {e}")
                last_error = e
                continue

        # If all attempts failed, provide clear error message
        if orchestrator is None:
            error_msg = (
                f"❌ All orchestrator loading attempts failed.\n"
                f"Last error: {last_error}\n\n"
                f"This usually indicates:\n"
                f"• Missing dependencies (CrewAI, etc.)\n"
                f"• Configuration issues\n"
                f"• Import path problems\n\n"
                f"Please run 'python -m ultimate_discord_intelligence_bot.setup_cli doctor' to diagnose."
            )
            try:
                await interaction.followup.send(
                    error_msg,
                    ephemeral=True,
                )
            except Exception:
                pass
            return

        # Create tenant context for isolation. This is now done for all orchestrator types
        # to ensure consistent context propagation.
        tenant_ctx = None
        try:
            from ..tenancy import TenantContext

            guild_id = getattr(interaction, "guild_id", None)
            channel = getattr(interaction, "channel", None)
            workspace_name = getattr(channel, "name", "direct_message") if channel else "direct_message"
            tenant_ctx = TenantContext(
                tenant_id=f"guild_{guild_id or 'dm'}",
                workspace_id=workspace_name,
            )
            print(f"✅ Created tenant context: {tenant_ctx}")
        except ImportError as tenancy_error:
            print(f"⚠️ Tenancy system not available: {tenancy_error}. Proceeding without tenant context.")
            TenantContext = None
        except Exception as tenant_error:
            print(f"❌ Tenant context creation failed: {tenant_error}")
            try:
                await interaction.followup.send(
                    f"⚠️ Tenant context setup failed: {tenant_error}\nProceeding with basic execution.",
                    ephemeral=True,
                )
            except Exception:
                pass
            tenant_ctx = None

        if orchestrator_type in ("fallback", "enhanced", "direct", "crew"):
            # Enhanced diagnostic wrapper for orchestrator execution
            print(f"🚀 Running {orchestrator_type} orchestrator...")

            try:
                # Add comprehensive error tracking
                import time

                start_time = time.time()

                # Execute with detailed error context
                await orchestrator.execute_autonomous_intelligence_workflow(interaction, url, depth, tenant_ctx)

                execution_time = time.time() - start_time
                print(f"✅ Orchestrator completed successfully in {execution_time:.2f}s")

            except Exception as orchestrator_error:
                execution_time = time.time() - start_time
                error_context = {
                    "orchestrator_type": orchestrator_type,
                    "url": url,
                    "depth": depth,
                    "execution_time": execution_time,
                    "error": str(orchestrator_error),
                    "error_type": type(orchestrator_error).__name__,
                }

                print(f"❌ Orchestrator failed after {execution_time:.2f}s: {orchestrator_error}")
                print(f"📊 Error context: {error_context}")

                try:
                    error_msg = (
                        f"❌ Orchestrator execution failed:\n"
                        f"**Type:** {orchestrator_type}\n"
                        f"**URL:** {url}\n"
                        f"**Depth:** {depth}\n"
                        f"**Error:** {str(orchestrator_error)[:500]}...\n"
                        f"**Duration:** {execution_time:.2f}s\n\n"
                        f"This error has been logged for debugging."
                    )
                    await interaction.followup.send(error_msg, ephemeral=True)
                except Exception:
                    pass

                # Re-raise for higher-level handling if needed
                raise
            return

        # Full orchestrator mode - set up tenancy
        try:
            from ..tenancy import with_tenant

            print("✅ Successfully imported tenancy modules for 'with' statement")
        except ImportError as tenancy_error:
            print(f"❌ Import error for tenancy context manager: {tenancy_error}")
            try:
                await interaction.followup.send(
                    f"⚠️ Tenancy system import failed: {tenancy_error}\nRunning without tenant isolation.",
                    ephemeral=True,
                )
            except Exception:
                pass
            with_tenant = None

        print("🚀 Executing autonomous intelligence workflow...")

        # Initialize and execute autonomous workflow with enhanced error handling
        try:
            if tenant_ctx and orchestrator_type == "full" and with_tenant is not None:
                with with_tenant(tenant_ctx):
                    print("✅ Orchestrator executing with full tenant context")
                    await orchestrator.execute_autonomous_intelligence_workflow(interaction, url, depth, tenant_ctx)
            else:
                # Fallback execution without tenant context
                print(f"✅ Orchestrator executing in {orchestrator_type} mode without tenant context")
                await orchestrator.execute_autonomous_intelligence_workflow(interaction, url, depth, None)

        except Exception as orchestrator_error:
            print(f"❌ Orchestrator execution failed: {orchestrator_error}")
            import traceback

            traceback.print_exc()
            try:
                await interaction.followup.send(
                    (
                        f"❌ Autonomous intelligence workflow failed: {str(orchestrator_error)}\n\n"
                        f"**Error Details:**\n- URL: {url}\n- Analysis Depth: {depth}\n- Error Type: {type(orchestrator_error).__name__}\n\n"
                        "The system encountered an error during autonomous processing. This may be due to:\n"
                        "• Missing CrewAI dependencies\n• Network connectivity issues\n• Content access restrictions\n• System resource limitations\n\n"
                        "Please try again or contact support if the issue persists."
                    ),
                    ephemeral=True,
                )
            except Exception:
                pass
    except Exception as e:
        print(f"❌ Critical command failure: {e}")
        import traceback

        traceback.print_exc()
        try:
            await interaction.followup.send(
                (
                    f"❌ Critical system error: {str(e)}\n"
                    "The /autointel command encountered an unexpected error. Please try again or contact support."
                ),
                ephemeral=True,
            )
        except Exception:
            # Last resort - no available channel to notify
            pass


def _register_slash_commands(bot: Any) -> None:
    if LIGHTWEIGHT_IMPORT:
        return

    # Only register a minimal health/status set by default; rich commands can be migrated incrementally
    try:

        @bot.tree.command(name="health", description="Simple health check")
        async def _health(interaction):  # type: ignore
            try:
                await interaction.response.send_message("✅ Bot is alive", ephemeral=True)
            except Exception:
                try:
                    await interaction.followup.send("✅ Bot is alive", ephemeral=True)
                except Exception:
                    pass

        @bot.tree.command(
            name="autointel", description="Enhanced autonomous URL intelligence analysis with full AI agentic workflow"
        )
        @app_commands.describe(
            url="URL to analyze (YouTube, Twitter, TikTok, Instagram, Reddit, etc.)",
            depth="Analysis depth: standard (fast), deep (comprehensive), comprehensive (all features), experimental (cutting-edge AI)",
        )
        @app_commands.choices(
            depth=[
                app_commands.Choice(name="Standard - Fast Analysis", value="standard"),
                app_commands.Choice(name="Deep - Comprehensive Analysis", value="deep"),
                app_commands.Choice(name="Comprehensive - All Features", value="comprehensive"),
                app_commands.Choice(name="Experimental - Cutting-Edge AI", value="experimental"),
            ]
        )
        async def _autointel(interaction, url: str, depth: str = "standard"):  # type: ignore
            """Enhanced autonomous command that orchestrates ALL available AI capabilities.

            Features include:
            🎯 Mission Planning & Resource Allocation
            📥 Multi-Platform Content Acquisition
            📝 Advanced Transcription & Indexing
            🗺️ Comprehensive Linguistic Analysis
            🔍 Multi-Source Information Verification
            🛡️ Advanced Threat & Deception Analysis
            🌐 Cross-Platform Social Intelligence
            👤 Behavioral Profiling & Persona Analysis
            🧠 Multi-Layer Knowledge Integration
            📚 Research Synthesis & Context Building
            📊 Predictive Performance Analytics
            🤖 AI-Enhanced Quality Assessment
            📋 Intelligence Briefing Curation
            💬 Community Communication & Reporting
            """
            print(f"🤖 /autointel command started: URL={url}, Depth={depth}")
            await _execute_autointel(interaction, url, depth)

        @bot.tree.command(name="retrieve_results", description="Retrieve completed intelligence analysis results")
        @app_commands.describe(workflow_id="Workflow ID from the /autointel acknowledgment message")
        async def _retrieve_results(interaction, workflow_id: str):  # type: ignore
            """Retrieve results from a background intelligence analysis workflow."""
            try:
                await interaction.response.defer()
                print(f"🔍 /retrieve_results command started: workflow_id={workflow_id}")
            except Exception as defer_error:
                print(f"❌ Failed to defer response: {defer_error}")
                return

            # Get background worker
            background_worker = getattr(interaction.client, "background_worker", None)

            if not background_worker:
                try:
                    await interaction.followup.send(
                        "❌ **Background Worker Not Available**\n\n"
                        "The background processing system is not enabled. "
                        "Results retrieval is only available when background processing is active.",
                        ephemeral=True,
                    )
                except Exception:
                    pass
                return

            # Use the handler
            try:
                from ..background_autointel_handler import handle_retrieve_results

                await handle_retrieve_results(
                    interaction=interaction,
                    background_worker=background_worker,
                    workflow_id=workflow_id,
                )
            except Exception as e:
                print(f"❌ Result retrieval failed: {e}")
                try:
                    await interaction.followup.send(
                        f"❌ **Retrieval Error**\n\nFailed to retrieve results: {str(e)}",
                        ephemeral=True,
                    )
                except Exception:
                    pass

        if os.getenv("ENABLE_DISCORD_USER_COMMANDS", "0").lower() in {"1", "true", "yes"}:

            @bot.tree.command(name="status", description="Bot status overview")
            async def _status(interaction):  # type: ignore
                tool_count = len(getattr(bot, "get_all_tools", lambda: {})())
                msg = f"🟢 Status: OK — {tool_count} tools loaded"
                try:
                    await interaction.response.send_message(msg, ephemeral=True)
                except Exception:
                    try:
                        await interaction.followup.send(msg, ephemeral=True)
                    except Exception:
                        pass
    except Exception as e:  # pragma: no cover
        print(f"⚠️  Failed to register slash commands: {e}")


__all__ = [
    "_register_events",
    "_register_prefix_commands",
    "_register_slash_commands",
]
