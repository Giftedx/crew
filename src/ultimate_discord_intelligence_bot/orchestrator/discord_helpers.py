"""Discord Integration Helpers - Isolated Discord-specific functionality.

This module contains all Discord-specific integration logic extracted from the
autonomous orchestrator, including progress updates, session validation, error
handling, result delivery, and embed creation.

All functions are stateless and accept Discord interaction objects + necessary
data as parameters. This design enables:
- Easy testing with mocked Discord interactions
- Clear separation of concerns (Discord I/O vs business logic)
- Reusability across different orchestrators or Discord commands
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.step_result import StepResult

if TYPE_CHECKING:
    pass  # Discord types imported dynamically at runtime

logger = logging.getLogger(__name__)


def _get_metrics():
    """Lazy import of metrics to avoid circular dependencies."""
    try:
        from obs.metrics import get_metrics

        return get_metrics()
    except ImportError:
        # Return a no-op metrics object if metrics module not available
        class NoOpMetrics:
            def counter(self, *args, **kwargs):
                pass

            def histogram(self, *args, **kwargs):
                pass

        return NoOpMetrics()


# ============================================================================
# Session Validation
# ============================================================================


def is_session_valid(interaction: Any, log: logging.Logger | None = None) -> bool:
    """Check if Discord session is still valid for sending messages.

    Args:
        interaction: Discord interaction object
        log: Optional logger instance (defaults to module logger)

    Returns:
        True if session is valid and can receive messages
        False if session is closed or invalid

    Examples:
        >>> if is_session_valid(interaction):
        ...     await send_progress_update(interaction, "Processing...", 1, 5)
    """
    _logger = log or logger

    try:
        # Check if interaction has a webhook and if the session is open
        if not hasattr(interaction, "followup"):
            _logger.debug("Interaction missing 'followup' attribute")
            return False

        # Check if the underlying webhook has a valid session
        if hasattr(interaction.followup, "_adapter"):
            adapter = interaction.followup._adapter
            if hasattr(adapter, "_session") and adapter._session:
                session = adapter._session
                # aiohttp session has a 'closed' property
                if hasattr(session, "closed"):
                    is_open = not session.closed
                    if not is_open:
                        _logger.warning("Discord aiohttp session detected as closed")
                    return is_open

        # Additional validation: try to access interaction properties
        try:
            _ = interaction.id  # Will fail if interaction is invalid
        except Exception as e:
            _logger.debug(f"Interaction ID access failed: {e}")
            return False

        # If we can't determine session state definitively, assume it might work
        return True
    except Exception as e:
        # If any check fails, assume session is invalid
        _logger.debug(f"Session validation failed with exception: {e}")
        return False


# ============================================================================
# Progress Updates
# ============================================================================


async def send_progress_update(
    interaction: Any,
    message: str,
    current: int,
    total: int,
    log: logging.Logger | None = None,
) -> None:
    """Send real-time progress updates to Discord.

    Displays a visual progress bar with emoji indicators and percentage.
    Automatically checks session validity before sending.

    Args:
        interaction: Discord interaction object
        message: Progress message to display
        current: Current step number
        total: Total number of steps
        log: Optional logger instance

    Examples:
        >>> await send_progress_update(interaction, "Downloading media", 2, 5)
        # Output: "Downloading media
        #          🟢🟢⚪⚪⚪ 2/5 (40%)"
    """
    _logger = log or logger

    try:
        # Check if session is still valid before attempting to send
        if not is_session_valid(interaction, _logger):
            _logger.warning(f"Session closed, cannot send progress update: {message}")
            return

        # Prevent division by zero
        if total <= 0:
            total = 1

        progress_bar = "🟢" * current + "⚪" * max(0, total - current)
        progress_percentage = int((current / total) * 100) if total > 0 else 0
        progress_text = f"{message}\n{progress_bar} {current}/{total} ({progress_percentage}%)"

        # Always use followup.send for progress updates since interaction.response.defer() was called
        try:
            await interaction.followup.send(progress_text, ephemeral=False)
        except RuntimeError as e:
            if "Session is closed" in str(e):
                _logger.warning(f"Session closed during progress update: {message}")
            else:
                raise

    except Exception as e:
        # Only log if it's not a session closed error (already handled above)
        if "Session is closed" not in str(e):
            _logger.error(f"Progress update failed: {e}", exc_info=True)


# ============================================================================
# Result Persistence (Orphaned Results)
# ============================================================================


async def persist_workflow_results(
    workflow_id: str,
    results: dict[str, Any],
    url: str,
    depth: str,
    log: logging.Logger | None = None,
) -> str:
    """Persist workflow results to disk when Discord session closes.

    This allows users to retrieve results even after the interaction timeout.
    Results are stored in data/orphaned_results/ with workflow_id as filename.

    Args:
        workflow_id: Unique identifier for the workflow
        results: Complete workflow results dictionary
        url: Original URL that was analyzed
        depth: Analysis depth used
        log: Optional logger instance

    Returns:
        Path to the persisted result file, or empty string on failure

    Examples:
        >>> path = await persist_workflow_results(
        ...     "abc123", results, "https://example.com", "experimental"
        ... )
        >>> print(path)
        "data/orphaned_results/abc123.json"
    """
    _logger = log or logger

    try:
        import json
        from pathlib import Path

        results_dir = Path("data/orphaned_results")
        results_dir.mkdir(parents=True, exist_ok=True)

        result_file = results_dir / f"{workflow_id}.json"

        result_data = {
            "workflow_id": workflow_id,
            "timestamp": time.time(),
            "url": url,
            "depth": depth,
            "results": results,
            "retrieval_info": {
                "command": f"/retrieve_results workflow_id:{workflow_id}",
                "file_path": str(result_file),
                "status": "session_closed_during_workflow",
            },
        }

        with open(result_file, "w") as f:
            json.dump(result_data, f, indent=2, default=str)

        _logger.info(f"✅ Workflow results persisted to {result_file} (workflow_id={workflow_id})")

        # Track metric
        _get_metrics().counter("workflow_results_persisted_total", labels={"reason": "session_closed", "depth": depth})

        return str(result_file)
    except Exception as e:
        _logger.error(f"❌ Failed to persist workflow results: {e}", exc_info=True)
        return ""


# ============================================================================
# Error Handling & Reporting
# ============================================================================


async def handle_acquisition_failure(
    interaction: Any,
    acquisition_result: StepResult,
    url: str,
    log: logging.Logger | None = None,
) -> None:
    """Handle content acquisition failures with specialized guidance.

    Provides user-friendly error messages with actionable guidance based on
    error type (missing dependencies, YouTube protection, etc.).

    Args:
        interaction: Discord interaction object
        acquisition_result: Failed acquisition StepResult
        url: URL that failed to be acquired
        log: Optional logger instance
    """
    _logger = log or logger

    try:
        error_data = acquisition_result.data or {}
        error_type = error_data.get("error_type", "general")

        # Recognize missing dependency surfaced by YtDlpDownloadTool
        if error_type == "dependency_missing" or (
            isinstance(acquisition_result.error, str) and "yt-dlp" in acquisition_result.error.lower()
        ):
            guidance = error_data.get(
                "guidance",
                (
                    "yt-dlp is missing on this system. Install it with 'pip install yt-dlp' or run 'make first-run' "
                    "to set up the environment. You can also run 'make doctor' to verify binaries."
                ),
            )
            enhanced_error = (
                "🔧 Missing Dependency Detected: yt-dlp\n\n"
                "The downloader requires yt-dlp to fetch media.\n\n"
                f"Guidance: {guidance}"
            )
            await send_enhanced_error_response(interaction, "Content Acquisition", enhanced_error, _logger)
            return

        if error_type == "youtube_protection":
            enhanced_error = (
                "🎬 **YouTube Download Issue Detected**\n\n"
                "The video appears to have YouTube's enhanced protection enabled. This is common for:\n"
                "• Popular or trending videos\n"
                "• Videos with restricted access\n"
                "• Content with digital rights management\n\n"
                "**Suggestions:**\n"
                "• Try a different YouTube video\n"
                "• Use a direct video file URL instead\n"
                "• The autonomous system attempted multiple quality fallbacks but YouTube blocked all formats\n\n"
                f"**Technical Details:** {acquisition_result.error or 'Unknown error'}..."
            )
            await send_enhanced_error_response(interaction, "Content Acquisition", enhanced_error, _logger)
        else:
            # General acquisition failure
            error_msg = acquisition_result.error or "Content acquisition failed"
            await send_error_response(interaction, "Content Acquisition", error_msg, _logger)

    except Exception as e:
        # Fallback error handling
        await send_error_response(
            interaction, "Content Acquisition", f"Failed to acquire content from {url}: {e}", _logger
        )


async def send_error_response(
    interaction: Any,
    stage: str,
    error: str,
    log: logging.Logger | None = None,
) -> None:
    """Send error response to Discord with session resilience.

    Args:
        interaction: Discord interaction object
        stage: Stage name where error occurred
        error: Error message to send
        log: Optional logger instance

    Note:
        If session is closed, error is logged instead of sent.
        This prevents cascading RuntimeError exceptions.
    """
    _logger = log or logger

    try:
        # Check if session is still valid
        if not is_session_valid(interaction, _logger):
            _logger.error(f"❌ Session closed, cannot send error response to Discord.\nStage: {stage}\nError: {error}")
            # Track metric for session closure during error handling
            _get_metrics().counter(
                "discord_session_closed_total",
                labels={"stage": f"error_response_{stage.lower().replace(' ', '_')}"},
            )
            return

        error_embed = await create_error_embed(stage, error)
        try:
            await interaction.followup.send(embed=error_embed, ephemeral=False)
        except RuntimeError as e:
            if "Session is closed" in str(e):
                _logger.error(f"❌ Session closed while sending error embed.\nStage: {stage}\nError: {error}")
                # Track metric
                _get_metrics().counter(
                    "discord_session_closed_total",
                    labels={"stage": f"error_response_send_{stage.lower().replace(' ', '_')}"},
                )
                return
            else:
                raise
    except Exception as e:
        # Don't log session closed errors (already handled)
        if "Session is closed" in str(e):
            _logger.error(f"Session closed during error response for {stage}: {error}")
            return

        # Fallback to text response for other errors
        try:
            if is_session_valid(interaction, _logger):
                await interaction.followup.send(
                    f"❌ Autonomous Intelligence Error\n"
                    f"**Stage:** {stage}\n"
                    f"**Error:** {error}\n\n"
                    f"The autonomous workflow encountered an issue during processing.",
                    ephemeral=False,
                )
            else:
                _logger.error(f"Session closed during error fallback for {stage}: {error}")
        except Exception as fallback_error:
            if "Session is closed" not in str(fallback_error):
                _logger.error(f"All error reporting failed for {stage}: {error}")


async def send_enhanced_error_response(
    interaction: Any,
    stage: str,
    enhanced_message: str,
    log: logging.Logger | None = None,
) -> None:
    """Send enhanced user-friendly error response to Discord.

    Args:
        interaction: Discord interaction object
        stage: Stage name where error occurred
        enhanced_message: Pre-formatted error message with guidance
        log: Optional logger instance
    """
    _logger = log or logger

    try:
        await interaction.followup.send(
            f"❌ **Autonomous Intelligence - {stage}**\n\n{enhanced_message}",
            ephemeral=False,
        )
    except Exception:
        # Fallback to basic error response
        await send_error_response(interaction, stage, "Enhanced error details unavailable", _logger)


# ============================================================================
# Result Delivery
# ============================================================================


async def deliver_autonomous_results(
    interaction: Any,
    results: dict[str, Any],
    depth: str,
    log: logging.Logger | None = None,
) -> None:
    """Deliver comprehensive autonomous analysis results to Discord.

    Creates and sends multiple embeds with analysis summary, detailed results,
    and knowledge base integration status.

    Args:
        interaction: Discord interaction object
        results: Complete workflow results dictionary
        depth: Analysis depth used (e.g., "experimental", "moderate")
        log: Optional logger instance
    """
    _logger = log or logger

    try:
        # Create comprehensive result embeds
        main_embed = await create_main_results_embed(results, depth)
        details_embed = await create_details_embed(results)

        await interaction.followup.send(embeds=[main_embed, details_embed], ephemeral=False)

        # Send knowledge base update notification
        knowledge_data = results.get("detailed_results", {}).get("knowledge_base_integration", {})
        if knowledge_data.get("knowledge_storage"):
            kb_embed = await create_knowledge_base_embed(knowledge_data)
            await interaction.followup.send(embed=kb_embed, ephemeral=True)

    except Exception as e:
        _logger.error(f"Results delivery failed: {e}", exc_info=True)
        # Fallback to text response
        summary = results.get("autonomous_analysis_summary", {})
        await interaction.followup.send(
            f"✅ **Autonomous Intelligence Analysis Complete**\n\n"
            f"**URL:** {summary.get('url', 'N/A')}\n"
            f"**Deception Score:** {summary.get('deception_score', 0.0):.2f}/1.00\n"
            f"**Processing Time:** {summary.get('processing_time', 0.0):.1f}s\n"
            f"**Analysis Depth:** {depth}\n\n"
            f"*Full results available but embed generation failed.*",
            ephemeral=False,
        )


# ============================================================================
# Discord Embed Builders
# ============================================================================


async def create_main_results_embed(results: dict[str, Any], depth: str) -> Any:
    """Create the main results embed for Discord.

    Args:
        results: Complete workflow results dictionary
        depth: Analysis depth used

    Returns:
        Discord Embed object with main results summary
    """
    try:
        from ..discord_bot.discord_env import discord

        summary = results.get("autonomous_analysis_summary", {})
        stats = summary.get("summary_statistics", {})
        insights = summary.get("autonomous_insights", [])

        deception_score = summary.get("deception_score", 0.0)
        color = 0x00FF00 if deception_score < 0.3 else 0xFF6600 if deception_score < 0.7 else 0xFF0000
        score_emoji = "🟢" if deception_score < 0.3 else "🟡" if deception_score < 0.7 else "🔴"

        embed = discord.Embed(
            title="🤖 Autonomous Intelligence Analysis Complete",
            description=f"**URL:** {summary.get('url', 'N/A')}",
            color=color,
        )

        # Deception score (primary metric)
        embed.add_field(name="🎯 Deception Score", value=f"{score_emoji} {deception_score:.2f}/1.00", inline=True)

        # Processing stats
        embed.add_field(name="⚡ Processing Time", value=f"{summary.get('processing_time', 0.0):.1f}s", inline=True)

        embed.add_field(name="📊 Analysis Depth", value=depth.title(), inline=True)

        # Fact-checking summary
        if stats.get("fact_checks_performed", 0) > 0:
            embed.add_field(name="✅ Fact Checks", value=f"{stats['fact_checks_performed']} performed", inline=True)

        # Fallacy detection
        if stats.get("fallacies_detected", 0) > 0:
            embed.add_field(name="⚠️ Logical Fallacies", value=f"{stats['fallacies_detected']} detected", inline=True)

        # Cross-platform intelligence
        if stats.get("cross_platform_sources", 0) > 0:
            embed.add_field(
                name="🌐 Cross-Platform Intel", value=f"{stats['cross_platform_sources']} sources", inline=True
            )

        # Autonomous insights
        if insights:
            embed.add_field(
                name="🧠 Autonomous Insights",
                value="\n".join(insights[:3]),  # Show top 3 insights
                inline=False,
            )

        # Footer with workflow metadata
        embed.set_footer(text=f"Workflow ID: {summary.get('workflow_id', 'N/A')} | Autonomous Intelligence System v2.0")

        return embed

    except Exception as e:
        # Return a minimal embed on error
        return {"title": "Results Available", "description": f"Results generated but embed creation failed: {e}"}


async def create_details_embed(results: dict[str, Any]) -> Any:
    """Create detailed results embed.

    Args:
        results: Complete workflow results dictionary

    Returns:
        Discord Embed object with detailed analysis results
    """
    try:
        from ..discord_bot.discord_env import discord

        detailed = results.get("detailed_results", {})
        content_data = detailed.get("content_analysis", {})
        fact_data = detailed.get("fact_checking", {})

        embed = discord.Embed(title="📋 Detailed Analysis Results", color=0x0099FF)

        # Content analysis details
        download_info = content_data.get("download", {})
        if download_info:
            embed.add_field(
                name="📺 Content Details",
                value=f"**Title:** {download_info.get('title', 'N/A')[:100]}...\n"
                f"**Platform:** {download_info.get('platform', 'Unknown')}\n"
                f"**Duration:** {download_info.get('duration', 'N/A')}",
                inline=False,
            )

        # Analysis results
        analysis_data = content_data.get("analysis", {})
        if analysis_data:
            sentiment = analysis_data.get("sentiment", "Unknown")
            keywords = analysis_data.get("keywords", [])
            embed.add_field(
                name="🔍 Content Analysis",
                value=f"**Sentiment:** {sentiment}\n"
                f"**Key Topics:** {', '.join(keywords[:5]) if keywords else 'None identified'}",
                inline=False,
            )

        # Fact-checking details
        if fact_data.get("fact_checks"):
            fact_summary = fact_data["fact_checks"]
            embed.add_field(
                name="🔬 Fact-Check Summary",
                value=f"**Verified Claims:** {fact_summary.get('verified_claims', 0)}\n"
                f"**Disputed Claims:** {fact_summary.get('disputed_claims', 0)}\n"
                f"**Confidence:** {fact_summary.get('confidence', 'N/A')}",
                inline=True,
            )

            # Add a compact list of top claims with verdicts for transparency
            try:
                items = fact_summary.get("items")
                if isinstance(items, list) and items:
                    lines: list[str] = []
                    # Show up to 3 most salient claims (default ordering preserved)
                    for it in items[:3]:
                        if not isinstance(it, dict):
                            continue
                        claim_txt = str(it.get("claim", "")).strip()
                        verdict = str(it.get("verdict", "")).strip().lower()
                        conf = it.get("confidence", None)
                        if isinstance(conf, (int, float, str)):
                            try:
                                conf_f = float(conf)  # type: ignore[arg-type]
                            except Exception:
                                conf_f = 0.0
                        else:
                            conf_f = 0.0
                        # Truncate long claims for embed readability
                        display_claim = (claim_txt[:120] + "...") if len(claim_txt) > 120 else claim_txt
                        if display_claim:
                            lines.append(f"• {display_claim}\n  → {verdict or 'unknown'} ({conf_f:.2f})")
                    if lines:
                        embed.add_field(
                            name="🧾 Top Claims & Verdicts",
                            value="\n".join(lines),
                            inline=False,
                        )
            except Exception:
                # Non-fatal: skip details if any formatting error occurs
                pass

        # Fallacy detection details
        if fact_data.get("logical_fallacies"):
            fallacies = fact_data["logical_fallacies"].get("fallacies_detected", [])
            if fallacies:
                embed.add_field(
                    name="⚠️ Detected Fallacies",
                    value="\n".join([f"• {fallacy}" for fallacy in fallacies[:5]]),
                    inline=True,
                )

        return embed

    except Exception:
        return {"title": "Details", "description": "Detailed results available in logs"}


async def create_knowledge_base_embed(knowledge_data: dict[str, Any]) -> Any:
    """Create knowledge base integration embed.

    Args:
        knowledge_data: Knowledge base integration results

    Returns:
        Discord Embed object with KB integration status
    """
    try:
        from ..discord_bot.discord_env import discord

        storage = knowledge_data.get("knowledge_storage", {})
        stored_payload = knowledge_data.get("stored_payload", {})

        embed = discord.Embed(
            title="💾 Knowledge Base Integration",
            description="Analysis results have been integrated into the knowledge base",
            color=0x00FF99,
        )

        # Storage details
        storage_types = []
        if storage.get("memory_storage"):
            storage_types.append("Vector Memory")
        if storage.get("graph_memory"):
            storage_types.append("Graph Memory")
        if storage.get("hipporag_memory"):
            storage_types.append("Continual Memory")

        if storage_types:
            embed.add_field(
                name="📊 Storage Systems",
                value="\n".join([f"✅ {storage_type}" for storage_type in storage_types]),
                inline=True,
            )

        # Stored content summary
        embed.add_field(
            name="📝 Stored Content",
            value=f"**Title:** {stored_payload.get('title', 'N/A')[:50]}...\n"
            f"**Platform:** {stored_payload.get('platform', 'Unknown')}\n"
            f"**Deception Score:** {stored_payload.get('deception_score', 0.0):.2f}",
            inline=True,
        )

        embed.set_footer(text="This data is now available for future queries and analysis")

        return embed

    except Exception:
        return {"title": "Knowledge Base", "description": "Integration completed successfully"}


async def create_error_embed(stage: str, error: str) -> Any:
    """Create error embed for Discord.

    Args:
        stage: Stage name where error occurred
        error: Error message to display

    Returns:
        Discord Embed object with error details
    """
    try:
        from ..discord_bot.discord_env import discord

        embed = discord.Embed(
            title="❌ Autonomous Intelligence Error",
            description="The autonomous workflow encountered an error during processing.",
            color=0xFF0000,
        )

        embed.add_field(name="🔧 Failed Stage", value=stage, inline=True)

        embed.add_field(name="⚠️ Error Details", value=error[:500] + ("..." if len(error) > 500 else ""), inline=False)

        embed.set_footer(text="Please try again or contact support if the issue persists")

        return embed

    except Exception:
        # Fallback to minimal embed on error
        return {"title": "Error", "description": f"Error in stage: {stage}. Details: {error[:100]}"}


async def create_specialized_main_results_embed(results: dict[str, Any], depth: str) -> Any:
    """Create specialized main results embed for Discord.

    Args:
        results: Analysis results dictionary
        depth: Analysis depth level

    Returns:
        Discord Embed object with specialized analysis summary
    """
    try:
        from ..discord_bot.discord_env import discord

        summary = results.get("specialized_analysis_summary", {})
        stats = summary.get("summary_statistics", {})
        insights = summary.get("specialized_insights", [])

        threat_score = summary.get("threat_score", 0.0)
        threat_level = summary.get("threat_level", "unknown")

        # Color coding based on threat level
        color = 0x00FF00 if threat_level == "low" else 0xFF6600 if threat_level == "medium" else 0xFF0000
        threat_emoji = "🟢" if threat_level == "low" else "🟡" if threat_level == "medium" else "🔴"

        embed = discord.Embed(
            title="🤖 Specialized Autonomous Intelligence Analysis",
            description=f"**URL:** {summary.get('url', 'N/A')}",
            color=color,
        )

        # Threat assessment (primary metric)
        embed.add_field(
            name="🎯 Threat Assessment",
            value=f"{threat_emoji} {threat_score:.2f}/1.00 ({threat_level.upper()})",
            inline=True,
        )

        # Processing performance
        embed.add_field(name="⚡ Processing Time", value=f"{summary.get('processing_time', 0.0):.1f}s", inline=True)

        embed.add_field(name="🧠 Analysis Method", value="Specialized Agents", inline=True)

        # Verification status
        if stats.get("verification_completed"):
            embed.add_field(name="✅ Information Verification", value="Completed by Specialist", inline=True)

        # Behavioral analysis
        if stats.get("behavioral_analysis_done"):
            embed.add_field(name="📊 Behavioral Analysis", value="Pattern Analysis Complete", inline=True)

        # Knowledge integration
        if stats.get("knowledge_integrated"):
            embed.add_field(name="💾 Knowledge Integration", value="Multi-System Storage", inline=True)

        # Specialized insights
        if insights:
            embed.add_field(
                name="🧠 Specialized Intelligence Insights",
                value="\n".join(insights[:4]),  # Show top 4 insights
                inline=False,
            )

        # Footer with specialized workflow info
        embed.set_footer(
            text=f"Analysis: {summary.get('workflow_id', 'N/A')} | Specialized Autonomous Intelligence v2.0"
        )

        return embed

    except Exception as e:
        # Fallback embed
        return {"title": "Specialized Analysis Complete", "description": f"Results available (embed error: {e})"}


async def create_specialized_details_embed(results: dict[str, Any]) -> Any:
    """Create specialized detailed results embed.

    Args:
        results: Analysis results dictionary

    Returns:
        Discord Embed object with detailed analysis information
    """
    try:
        from ..discord_bot.discord_env import discord

        detailed = results.get("detailed_results", {})
        intelligence_data = detailed.get("intelligence", {})
        verification_data = detailed.get("verification", {})
        deception_data = detailed.get("deception", {})

        embed = discord.Embed(title="📋 Specialized Analysis Details", color=0x0099FF)

        # Content intelligence details
        content_metadata = intelligence_data.get("content_metadata", {})
        if content_metadata:
            embed.add_field(
                name="📺 Content Intelligence",
                value=f"**Platform:** {content_metadata.get('platform', 'Unknown')}\n"
                f"**Title:** {content_metadata.get('title', 'N/A')[:50]}...\n"
                f"**Duration:** {content_metadata.get('duration', 'N/A')}",
                inline=False,
            )

        # Verification details (support both 'fact_checks' and legacy 'fact_verification')
        fact_checks = None
        if isinstance(verification_data.get("fact_checks"), dict):
            fact_checks = verification_data["fact_checks"]
        elif isinstance(verification_data.get("fact_verification"), dict):
            fact_checks = verification_data["fact_verification"]
        if isinstance(fact_checks, dict):
            verified = fact_checks.get("verified_claims")
            disputed = fact_checks.get("disputed_claims")
            evidence_count = fact_checks.get("evidence_count")
            claims = fact_checks.get("claims")
            claim_count = len(claims) if isinstance(claims, list) else fact_checks.get("claims_count")
            if isinstance(verified, int) or isinstance(disputed, int):
                fact_line = f"**Fact Checks:** {int(verified or 0)} verified, {int(disputed or 0)} disputed\n"
            else:
                fact_line = (
                    f"**Fact Checks:** {int(claim_count or 0)} claims, {int(evidence_count or 0)} evidence\n"
                )
            embed.add_field(
                name="🔬 Information Verification",
                value=fact_line + f"**Confidence:** {verification_data.get('verification_confidence', 0.0):.2f}",
                inline=True,
            )

        # Threat analysis details
        if deception_data.get("deception_analysis"):
            embed.add_field(
                name="⚖️ Threat Analysis",
                value=f"**Threat Level:** {deception_data.get('threat_level', 'unknown').upper()}\n"
                f"**Score:** {deception_data.get('threat_score', 0.0):.2f}/1.00\n"
                f"**Assessment:** Specialized Analysis",
                inline=True,
            )

        # Logical analysis
        logical_analysis = verification_data.get("logical_analysis", {})
        if logical_analysis.get("fallacies_detected"):
            fallacies = logical_analysis["fallacies_detected"]
            embed.add_field(
                name="⚠️ Logical Analysis",
                value="\n".join([f"• {fallacy}" for fallacy in fallacies[:3]]),
                inline=False,
            )

        return embed

    except Exception:
        return {"title": "Analysis Details", "description": "Specialized analysis details available"}


async def create_specialized_knowledge_embed(knowledge_data: dict[str, Any]) -> Any:
    """Create specialized knowledge integration embed.

    Args:
        knowledge_data: Knowledge integration data

    Returns:
        Discord Embed object with knowledge integration status
    """
    try:
        from ..discord_bot.discord_env import discord

        systems = knowledge_data.get("knowledge_systems", {})

        embed = discord.Embed(
            title="💾 Specialized Knowledge Integration",
            description="Intelligence integrated by Knowledge Integration Manager",
            color=0x00FF99,
        )

        # Integration systems
        integrated_systems = []
        if systems.get("vector_memory"):
            integrated_systems.append("✅ Vector Memory System")
        if systems.get("graph_memory"):
            integrated_systems.append("✅ Graph Memory System")
        if systems.get("continual_memory"):
            integrated_systems.append("✅ Continual Learning System")

        if integrated_systems:
            embed.add_field(name="🔧 Integrated Systems", value="\n".join(integrated_systems), inline=True)

        embed.add_field(
            name="📊 Integration Status",
            value=f"**Method:** Specialized Agent\n**Status:** {knowledge_data.get('integration_status', 'unknown').title()}\n**Approach:** Multi-System",
            inline=True,
        )

        embed.set_footer(text="Specialized intelligence available for future queries and analysis")

        return embed

    except Exception:
        return {"title": "Knowledge Integration", "description": "Specialized integration completed successfully"}
