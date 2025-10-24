"""Discord Result Delivery - Result delivery and presentation utilities.

This module contains Discord result delivery logic extracted from discord_helpers.py,
providing utilities to deliver comprehensive analysis results to Discord.
"""

from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)


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
        # Import here to avoid circular dependency
        from .discord_embed_builders import (
            create_details_embed,
            create_knowledge_base_embed,
            create_main_results_embed,
        )

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
