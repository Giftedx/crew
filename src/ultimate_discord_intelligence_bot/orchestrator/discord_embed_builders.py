"""Discord Embed Builders - Discord embed creation utilities.

This module contains Discord embed creation logic extracted from discord_helpers.py,
providing utilities to create rich Discord embeds for analysis results and error messages.
"""

from __future__ import annotations

from typing import Any


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
                fact_line = f"**Fact Checks:** {int(claim_count or 0)} claims, {int(evidence_count or 0)} evidence\n"
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
