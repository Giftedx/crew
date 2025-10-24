#!/usr/bin/env python3
"""Categorize and move tools into hierarchical domain structure.

This script categorizes tools based on their functionality and moves them
into appropriate domain directories for better organization.
"""

import shutil
from pathlib import Path


# Tool categorization mapping
TOOL_CATEGORIES = {
    # Acquisition tools - content download and ingestion
    "acquisition": [
        "multi_platform_download_tool.py",
        "yt_dlp_download_tool.py",
        "youtube_download_tool.py",
        "enhanced_youtube_tool.py",
        "discord_download_tool.py",
        "instagram_stories_archiver_tool.py",
        "tiktok_enhanced_download_tool.py",
        "audio_transcription_tool.py",
        "transcript_index_tool.py",
    ],
    # Analysis tools - content analysis and processing
    "analysis": [
        "enhanced_analysis_tool.py",
        "text_analysis_tool.py",
        "sentiment_tool.py",
        "logical_fallacy_tool.py",
        "claim_extractor_tool.py",
        "trend_analysis_tool.py",
        "trend_forecasting_tool.py",
        "multimodal_analysis_tool.py",
        "image_analysis_tool.py",
        "video_frame_analysis_tool.py",
        "social_graph_analysis_tool.py",
        "live_stream_analysis_tool.py",
        "advanced_audio_analysis_tool.py",
        "reanalysis_trigger_tool.py",
        "content_quality_assessment_tool.py",
        "content_recommendation_tool.py",
        "engagement_prediction_tool.py",
        "virality_prediction_tool.py",
        "visual_summary_tool.py",
        "smart_clip_composer_tool.py",
        "cross_platform_narrative_tool.py",
        "narrative_tracker_tool.py",
        "timeline_tool.py",
        "character_profile_tool.py",
        "perspective_synthesizer_tool.py",
        "steelman_argument_tool.py",
    ],
    # Verification tools - fact-checking and verification
    "verification": [
        "fact_check_tool.py",
        "claim_verifier_tool.py",
        "truth_scoring_tool.py",
        "deception_scoring_tool.py",
        "context_verification_tool.py",
        "consistency_check_tool.py",
        "output_validation_tool.py",
        "trustworthiness_tracker_tool.py",
        "confidence_scoring_tool.py",
        "sponsor_compliance_tool.py",
        "compliance_executive_summary.py",
        "compliance_summary.py",
    ],
    # Memory tools - storage and retrieval
    "memory": [
        "memory_storage_tool.py",
        "memory_v2_tool.py",
        "memory_compaction_tool.py",
        "unified_memory_tool.py",
        "mem0_memory_tool.py",
        "graph_memory_tool.py",
        "hipporag_continual_memory_tool.py",
        "vector_search_tool.py",
        "rag_hybrid_tool.py",
        "rag_ingest_tool.py",
        "rag_ingest_url_tool.py",
        "rag_query_vs_tool.py",
        "offline_rag_tool.py",
        "mock_vector_tool.py",
        "research_and_brief_tool.py",
        "research_and_brief_multi_tool.py",
        "knowledge_ops_tool.py",
        "insight_sharing_tool.py",
        "collective_intelligence_tool.py",
        "strategic_planning_tool.py",
        "lc_summarize_tool.py",
        "prompt_compression_tool.py",
        "dspy_optimization_tool.py",
        "vowpal_wabbit_bandit_tool.py",
    ],
    # Observability tools - monitoring and system health
    "observability": [
        "system_status_tool.py",
        "advanced_performance_analytics_tool.py",
        "unified_metrics_tool.py",
        "orchestration_status_tool.py",
        "router_status_tool.py",
        "cost_tracking_tool.py",
        "resource_allocation_tool.py",
        "escalation_management_tool.py",
        "quality_assurance_tool.py",
        "performance_optimization_tool.py",
        "cache_optimization_tool.py",
        "workflow_optimization_tool.py",
        "early_exit_conditions_tool.py",
        "checkpoint_management_tool.py",
        "unified_cache_tool.py",
        "unified_router_tool.py",
        "unified_orchestration_tool.py",
        "task_routing_tool.py",
        "content_type_routing_tool.py",
        "agent_bridge_tool.py",
        "pipeline_tool.py",
        "mcp_call_tool.py",
        "fastmcp_client_tool.py",
        "dependency_resolver_tool.py",
        "step_result_auditor.py",
        "observability_tool.py",
    ],
}

# Tools that should remain in the root tools directory
ROOT_TOOLS = [
    "_base.py",
    "__init__.py",
    "__pycache__",
    "golden",
    "platform_resolver",
    "batch_stepresult_migration.py",
    "enhanced_error_handling_example.py",
    "multimodal_analysis_tool_old.py",
    "cache_v2_tool.py",
    "drive_upload_tool.py",
    "drive_upload_tool_bypass.py",
    "discord_monitor_tool.py",
    "discord_post_tool.py",
    "discord_private_alert_tool.py",
    "discord_qa_tool.py",
    "multi_platform_monitor_tool.py",
    "social_media_monitor_tool.py",
    "x_monitor_tool.py",
    "twitter_thread_reconstructor_tool.py",
    "debate_command_tool.py",
    "leaderboard_tool.py",
]


def categorize_tools():
    """Categorize and move tools into domain directories."""
    tools_dir = Path("/home/crew/src/ultimate_discord_intelligence_bot/tools")

    # Create domain directories
    for domain in TOOL_CATEGORIES:
        domain_dir = tools_dir / domain
        domain_dir.mkdir(exist_ok=True)

        # Create __init__.py for each domain
        init_file = domain_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text(f'"""Tools for {domain} domain."""\n')

    # Move tools to their respective domains
    moved_count = 0
    for domain, tools in TOOL_CATEGORIES.items():
        domain_dir = tools_dir / domain
        print(f"Processing {domain} domain...")

        for tool_file in tools:
            source_path = tools_dir / tool_file
            if source_path.exists():
                dest_path = domain_dir / tool_file
                if not dest_path.exists():
                    shutil.move(str(source_path), str(dest_path))
                    moved_count += 1
                    print(f"  Moved {tool_file} to {domain}/")
                else:
                    print(f"  Warning: {tool_file} already exists in {domain}/")
            else:
                print(f"  Warning: {tool_file} not found")

    print(f"\nMoved {moved_count} tools to domain directories")

    # List remaining tools in root
    remaining_tools = []
    for item in tools_dir.iterdir():
        if item.is_file() and item.name not in ROOT_TOOLS:
            remaining_tools.append(item.name)

    if remaining_tools:
        print(f"\nRemaining tools in root directory: {remaining_tools}")
    else:
        print("\nAll tools have been categorized!")


if __name__ == "__main__":
    categorize_tools()
