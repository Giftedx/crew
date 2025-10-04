"""Crew building functions for CrewAI agent orchestration.

This module provides functions for building, caching, and configuring CrewAI agents
and crews for the autonomous intelligence workflow.
"""

import logging
from typing import Any

from crewai import Crew, Process, Task

from core.settings import get_settings

# Module-level logger
logger = logging.getLogger(__name__)


def populate_agent_tool_context(
    agent: Any,
    context_data: dict[str, Any],
    logger_instance: logging.Logger | None = None,
    metrics_instance: Any | None = None,
) -> None:
    """Populate shared context on all tool wrappers for an agent.

    This is CRITICAL for CrewAI agents to receive structured data. Without this,
    tools receive empty parameters and fail or return meaningless results.

    Args:
        agent: CrewAI Agent instance with tools attribute
        context_data: Dictionary of data to make available to all tools
        logger_instance: Optional logger instance
        metrics_instance: Optional metrics instance for tracking
    """
    _logger = logger_instance or logger

    if not hasattr(agent, "tools"):
        _logger.warning(f"Agent {getattr(agent, 'role', 'unknown')} has no tools attribute")
        return

    # ENHANCED CONTEXT PROPAGATION LOGGING
    # Show exactly what data is available and what format it's in
    context_summary = {}
    for k, v in context_data.items():
        if isinstance(v, str):
            context_summary[k] = f"str({len(v)} chars)"
        elif isinstance(v, (list, dict)):
            context_summary[k] = f"{type(v).__name__}({len(v)} items)"
        else:
            context_summary[k] = type(v).__name__

    _logger.warning(f"🔧 POPULATING CONTEXT for agent {getattr(agent, 'role', 'unknown')}")
    _logger.warning(f"   📦 Data summary: {context_summary}")

    # Show critical fields with previews
    if "transcript" in context_data:
        preview = str(context_data["transcript"])[:200]
        _logger.warning(f"   📝 Transcript preview: {preview}...")
    if "file_path" in context_data:
        _logger.warning(f"   📁 File path: {context_data['file_path']}")
    if "url" in context_data:
        _logger.warning(f"   🔗 URL: {context_data['url']}")

    populated_count = 0
    for tool in agent.tools:
        if hasattr(tool, "update_context"):
            tool.update_context(context_data)
            populated_count += 1
            _logger.debug(
                f"✅ Populated context for {getattr(tool, 'name', tool.__class__.__name__)}: "
                f"{list(context_data.keys())}"
            )

    if populated_count > 0:
        _logger.warning(
            f"✅ CONTEXT POPULATED on {populated_count} tools for agent {getattr(agent, 'role', 'unknown')}"
        )
        # Track context population for monitoring
        if metrics_instance:
            try:
                metrics_instance.counter(
                    "autointel_context_populated",
                    labels={
                        "agent": getattr(agent, "role", "unknown"),
                        "tools_count": populated_count,
                        "has_transcript": "transcript" in context_data or "text" in context_data,
                    },
                ).inc()
            except Exception:
                pass
    else:
        _logger.error(f"❌ CONTEXT POPULATION FAILED: 0 tools updated for agent {getattr(agent, 'role', 'unknown')}")


def get_or_create_agent(
    agent_name: str,
    agent_coordinators: dict[str, Any],
    crew_instance: Any,
    logger_instance: logging.Logger | None = None,
) -> Any:
    """Get agent from coordinators cache or create and cache it.

    CRITICAL: This ensures agents are created ONCE and reused across stages.
    Repeated calls to crew_instance.agent_method() create FRESH agents with
    EMPTY tools, bypassing context population. Always use this method.

    Args:
        agent_name: Name of agent method (e.g., 'analysis_cartographer')
        agent_coordinators: Dictionary to cache agents (will be mutated)
        crew_instance: UltimateDiscordIntelligenceBotCrew instance
        logger_instance: Optional logger instance

    Returns:
        Cached agent instance with persistent tool context

    Raises:
        ValueError: If agent_name doesn't exist in crew_instance
    """
    _logger = logger_instance or logger

    # Return cached agent if available
    if agent_name in agent_coordinators:
        _logger.debug(f"✅ Reusing cached agent: {agent_name}")
        return agent_coordinators[agent_name]

    # Create new agent and cache it
    agent_method = getattr(crew_instance, agent_name, None)
    if not agent_method:
        raise ValueError(f"Unknown agent: {agent_name}")

    agent = agent_method()
    agent_coordinators[agent_name] = agent

    _logger.info(f"✨ Created and cached new agent: {agent_name}")
    return agent


def build_intelligence_crew(
    url: str,
    depth: str,
    agent_getter_callback,
    task_completion_callback: Any | None = None,
    logger_instance: logging.Logger | None = None,
    enable_parallel_memory_ops: bool | None = None,
    enable_parallel_analysis: bool | None = None,
) -> Crew:
    """Build a single chained CrewAI crew for the complete intelligence workflow.

    This is the CORRECT CrewAI pattern: one crew with multiple chained tasks using
    the context parameter to pass data between stages. This replaces the previous
    broken pattern of creating 25 separate single-task crews with data embedded
    in task descriptions.

    Args:
        url: URL to analyze
        depth: Analysis depth (standard, deep, comprehensive, experimental)
        agent_getter_callback: Callable that takes agent_name and returns agent instance
        task_completion_callback: Optional callback for task completion
        logger_instance: Optional logger instance
        enable_parallel_memory_ops: Enable parallel memory operations (default: from settings)
        enable_parallel_analysis: Enable parallel analysis subtasks (default: from settings)

    Returns:
        Configured Crew with chained tasks
    """
    _logger = logger_instance or logger

    # Get feature flags from settings if not explicitly provided
    settings = get_settings()
    if enable_parallel_memory_ops is None:
        enable_parallel_memory_ops = settings.enable_parallel_memory_ops
    if enable_parallel_analysis is None:
        enable_parallel_analysis = settings.enable_parallel_analysis

    _logger.info(f"🏗️  Building chained intelligence crew for depth: {depth}")

    # Get or create all agents ONCE (they'll be cached and reused)
    acquisition_agent = agent_getter_callback("acquisition_specialist")
    transcription_agent = agent_getter_callback("transcription_engineer")
    analysis_agent = agent_getter_callback("analysis_cartographer")
    verification_agent = agent_getter_callback("verification_director")
    knowledge_agent = agent_getter_callback("knowledge_integrator")

    # Build chained tasks - each task receives output from previous via context
    # CRITICAL: Task descriptions must be EXPLICIT about data extraction!
    # CrewAI passes output TEXT to prompts, NOT structured data to tools.
    # LLM must parse previous output and extract required fields.

    # Stage 1: Content Acquisition
    acquisition_task = Task(
        description=(
            "Download and acquire media content from {url}. "
            "Use the appropriate download tool for the platform (YouTube, TikTok, Twitter, etc.). "
            "Extract metadata and obtain the raw media file. "
            "\n\nCRITICAL: Return your results as JSON with these exact keys: "
            "file_path, title, description, author, duration, platform. "
            "Wrap the JSON in ```json``` code blocks for easy parsing."
        ),
        expected_output="JSON with file_path, title, description, author, duration, platform",
        agent=acquisition_agent,
        callback=task_completion_callback,
    )

    # Stage 2: Transcription & Indexing (depends on acquisition)
    transcription_task = Task(
        description=(
            "STEP 1: Extract the 'file_path' field from the previous task's JSON output. "
            "STEP 2: YOU MUST CALL AudioTranscriptionTool(file_path=<extracted_path>). "
            "DO NOT generate placeholder text like 'Your transcribed text goes here'. "
            "DO NOT respond until the tool returns actual transcript data. "
            "STEP 3: Create timeline anchors for key moments using the real transcript. "
            "\n\nCRITICAL: Return your results as JSON with these exact keys: "
            "transcript, timeline_anchors, transcript_length, quality_score. "
            "Wrap the JSON in ```json``` code blocks."
        ),
        expected_output=(
            "JSON with transcript (min 1000 chars from AudioTranscriptionTool), "
            "timeline_anchors (list of dicts), transcript_length (int), quality_score (0.0-1.0). "
            "❌ REJECT: Placeholder text. ❌ REJECT: transcript_length < 100. "
            "✅ ACCEPT: Real transcript with actual spoken words from the media file."
        ),
        agent=transcription_agent,
        context=[acquisition_task],
        callback=task_completion_callback,
    )

    # Stage 3: Content Analysis (depends on transcription)
    # Can use parallel analysis subtasks if enabled
    if enable_parallel_analysis:
        _logger.info("⚡ Using PARALLEL analysis subtasks (async_execution=True)")

        # Parallel Stage 3a: Text Analysis (linguistic patterns, themes, insights)
        text_analysis_task = Task(
            description=(
                "STEP 1: Extract the 'transcript' field from the transcription task output. "
                "STEP 2: YOU MUST CALL TextAnalysisTool(text=<transcript>) to analyze insights and themes. "
                "DO NOT generate placeholder values. "
                "DO NOT respond until the tool returns actual results. "
                "\n\nReturn results as JSON with keys: insights (list), themes (list)."
            ),
            expected_output=(
                "JSON with insights (list from TextAnalysisTool), "
                "themes (list from TextAnalysisTool). "
                "❌ REJECT: Placeholder values. ✅ ACCEPT: Real analysis from tool."
            ),
            agent=analysis_agent,
            context=[transcription_task],
            callback=task_completion_callback,
            async_execution=True,  # ⚡ RUNS IN PARALLEL
        )

        # Parallel Stage 3b: Logical Fallacy Detection
        fallacy_detection_task = Task(
            description=(
                "STEP 1: Extract the 'transcript' field from the transcription task output. "
                "STEP 2: YOU MUST CALL LogicalFallacyTool(text=<transcript>) to detect fallacies. "
                "DO NOT generate placeholder values. "
                "DO NOT respond until the tool returns actual results. "
                "\n\nReturn results as JSON with key: fallacies (list)."
            ),
            expected_output=(
                "JSON with fallacies (list from LogicalFallacyTool). "
                "❌ REJECT: Placeholder values. ✅ ACCEPT: Real fallacies from tool."
            ),
            agent=analysis_agent,
            context=[transcription_task],
            callback=task_completion_callback,
            async_execution=True,  # ⚡ RUNS IN PARALLEL
        )

        # Parallel Stage 3c: Perspective Synthesis
        perspective_synthesis_task = Task(
            description=(
                "STEP 1: Extract the 'transcript' field from the transcription task output. "
                "STEP 2: YOU MUST CALL PerspectiveSynthesizerTool(text=<transcript>) for perspectives. "
                "DO NOT generate placeholder values. "
                "DO NOT respond until the tool returns actual results. "
                "\n\nReturn results as JSON with key: perspectives (list)."
            ),
            expected_output=(
                "JSON with perspectives (list from PerspectiveSynthesizerTool). "
                "❌ REJECT: Placeholder values. ✅ ACCEPT: Real perspectives from tool."
            ),
            agent=analysis_agent,
            context=[transcription_task],
            callback=task_completion_callback,
            async_execution=True,  # ⚡ RUNS IN PARALLEL
        )

        # Stage 3d: Analysis Integration (waits for all 3 parallel tasks)
        analysis_integration_task = Task(
            description=(
                "Combine analysis results from three parallel tasks into unified output.\n\n"
                "You will receive outputs from THREE parallel tasks:\n"
                "1. Text analysis task - insights and themes\n"
                "2. Fallacy detection task - logical fallacies\n"
                "3. Perspective synthesis task - multiple perspectives\n\n"
                "STEP 1: Extract insights and themes from text analysis output\n"
                "STEP 2: Extract fallacies from fallacy detection output\n"
                "STEP 3: Extract perspectives from perspective synthesis output\n"
                "STEP 4: Combine all into unified JSON\n\n"
                "Return JSON with ALL keys: insights, themes, fallacies, perspectives."
            ),
            expected_output=(
                "JSON with insights (list), themes (list), fallacies (list), "
                "perspectives (list). Combined from all 3 parallel analysis tasks."
            ),
            agent=analysis_agent,
            context=[text_analysis_task, fallacy_detection_task, perspective_synthesis_task],
            callback=task_completion_callback,
        )
    else:
        # Sequential analysis (original pattern)
        analysis_task = Task(
            description=(
                "STEP 1: Extract the 'transcript' field from the previous task's JSON output. "
                "STEP 2: YOU MUST CALL TextAnalysisTool(text=<transcript>) to analyze insights and themes. "
                "STEP 3: YOU MUST CALL LogicalFallacyTool(text=<transcript>) to detect fallacies. "
                "STEP 4: YOU MUST CALL PerspectiveSynthesizerTool(text=<transcript>) for perspectives. "
                "DO NOT generate placeholder values like '<extracted_insights>'. "
                "DO NOT respond until all tools return actual results. "
                "\n\nCRITICAL: Pass the FULL transcript as the 'text' parameter to these tools. "
                "Return results as JSON with keys: insights, themes, fallacies, perspectives."
            ),
            expected_output=(
                "JSON with insights (list from TextAnalysisTool), "
                "themes (list from TextAnalysisTool), fallacies (list from LogicalFallacyTool), "
                "perspectives (list from PerspectiveSynthesizerTool). "
                "❌ REJECT: Placeholder values. ❌ REJECT: Invalid JSON. "
                "✅ ACCEPT: Real analysis from actual tool executions."
            ),
            agent=analysis_agent,
            context=[transcription_task],
            callback=task_completion_callback,
        )

    # Stage 4: Verification (depends on analysis)
    # Determine which analysis task to reference based on parallel flag
    analysis_ref = analysis_integration_task if enable_parallel_analysis else analysis_task

    verification_task = Task(
        description=(
            "CRITICAL DATA EXTRACTION INSTRUCTIONS:\n"
            "You will receive TWO previous task outputs in your context:\n"
            "1. Transcription task output - a JSON containing the 'transcript' field\n"
            "2. Analysis task output - a JSON containing 'insights', 'themes', etc.\n"
            "\n"
            "STEP 1: MANDATORY - Locate and extract the FULL TRANSCRIPT from the transcription task output.\n"
            "The transcript field contains the ACTUAL SPOKEN WORDS from the video.\n"
            "This is typically a LONG text (1000+ characters) with real quotes and conversation.\n"
            "DO NOT use task descriptions, instructions, or any other text as the transcript!\n"
            "\n"
            "STEP 2: YOU MUST CALL ClaimExtractorTool(text=<full_transcript_text>, max_claims=10).\n"
            "   - DO NOT respond until the tool returns actual claims.\n"
            "   - DO NOT generate empty arrays or placeholder claims.\n"
            "   - The tool will return 3-10 claims extracted from the transcript\n"
            "   - Call this tool EXACTLY ONCE\n"
            "\n"
            "STEP 3: Select the 3-5 most significant claims from the extracted list.\n"
            "\n"
            "STEP 4: YOU MUST CALL FactCheckTool(claim=<claim_text>) for each selected claim.\n"
            "   - Call the tool ONCE PER CLAIM (3-5 calls total).\n"
            "   - DO NOT respond until all tools return verification results.\n"
            "\n"
            "STEP 5: Assess overall source trustworthiness based on verified facts.\n"
            "\n"
            "VALIDATION CHECK:\n"
            "- If you're analyzing a video about Twitch/streaming, claims should mention Twitch, streamers, platform issues\n"
            "- If claims are about 'methodologies' or 'environmental issues', you're using the WRONG TEXT!\n"
            "- Claims should reflect the ACTUAL content discussed in the video, not generic topics\n"
            "\n"
            "Return results as JSON with keys:\n"
            "verified_claims (array of claim texts),\n"
            "fact_check_results (array of verification outcomes),\n"
            "trustworthiness_score (0-100)."
        ),
        expected_output=(
            "JSON with verified_claims (non-empty array from ClaimExtractorTool), "
            "fact_check_results (non-empty array from FactCheckTool), "
            "trustworthiness_score (0-100). "
            "❌ REJECT: Empty arrays. ❌ REJECT: Placeholder claims. "
            "✅ ACCEPT: Real claims about actual video content."
        ),
        agent=verification_agent,
        context=[transcription_task, analysis_ref],  # Need both for comprehensive verification
        callback=task_completion_callback,
    )

    # Stage 5: Knowledge Integration (depends on ALL previous tasks)
    # Can use parallel memory operations if enabled
    if enable_parallel_memory_ops:
        _logger.info("⚡ Using PARALLEL memory operations (async_execution=True)")

        # Parallel Stage 5a: Vector Memory Storage (runs independently)
        memory_storage_task = Task(
            description=(
                "⚠️ CRITICAL TOOL EXECUTION REQUIREMENT ⚠️\n\n"
                "STEP 1: Extract the FULL transcript from the transcription task output.\n"
                "The transcript is typically 1000+ characters of actual spoken words.\n\n"
                "STEP 2: YOU MUST CALL MemoryStorageTool(text=<full_transcript>).\n"
                "→ DO NOT respond until the tool returns a result\n"
                "→ DO NOT claim success until the tool confirms storage\n\n"
                "Return JSON with: memory_stored (boolean), storage_details (dict)."
            ),
            expected_output=(
                "JSON with memory_stored: true/false, storage_details: {...}.\n"
                "You MUST call MemoryStorageTool before responding."
            ),
            agent=knowledge_agent,
            context=[transcription_task],  # Only needs transcript
            callback=task_completion_callback,
            async_execution=True,  # ⚡ RUNS IN PARALLEL
        )

        # Parallel Stage 5b: Knowledge Graph Creation (runs independently)
        graph_memory_task = Task(
            description=(
                "⚠️ CRITICAL TOOL EXECUTION REQUIREMENT ⚠️\n\n"
                "STEP 1: Extract insights, themes, and entities from the analysis task output.\n\n"
                "STEP 2: YOU MUST CALL GraphMemoryTool with entity-relationship data.\n"
                "→ Extract key entities (people, organizations, topics)\n"
                "→ Define relationships between entities\n"
                "→ DO NOT respond until the tool returns a result\n\n"
                "Return JSON with: graph_created (boolean), graph_details (dict)."
            ),
            expected_output=(
                "JSON with graph_created: true/false, graph_details: {...}.\n"
                "You MUST call GraphMemoryTool before responding."
            ),
            agent=knowledge_agent,
            context=[analysis_ref],  # Only needs analysis
            callback=task_completion_callback,
            async_execution=True,  # ⚡ RUNS IN PARALLEL
        )

        # Stage 5c: Briefing Generation (waits for both parallel tasks)
        integration_task = Task(
            description=(
                "Generate comprehensive intelligence briefing after memory and graph operations complete.\n\n"
                "You will receive outputs from TWO parallel tasks:\n"
                "1. Memory storage task - confirms vector memory storage\n"
                "2. Graph memory task - confirms knowledge graph creation\n\n"
                "STEP 1: Verify both operations completed successfully\n"
                "STEP 2: Synthesize ALL findings into a comprehensive briefing\n"
                "Include sections: Overview, Key Insights, Themes, Perspectives, Verified Claims, Conclusion\n"
                "Use specific quotes, insights, and claims from previous tasks.\n\n"
                "Return JSON with: memory_stored (boolean), graph_created (boolean), "
                "briefing (markdown string)."
            ),
            expected_output=(
                "Final JSON with memory_stored, graph_created (from parallel tasks), "
                "and briefing (comprehensive markdown analysis)."
            ),
            agent=knowledge_agent,
            context=[
                memory_storage_task,
                graph_memory_task,
                acquisition_task,
                transcription_task,
                analysis_ref,
                verification_task,
            ],
            callback=task_completion_callback,
        )
    else:
        # Sequential integration (original pattern)
        integration_task = Task(
            description=(
                "⚠️ CRITICAL TOOL EXECUTION REQUIREMENTS - READ CAREFULLY ⚠️\n\n"
                "This task requires you to CALL SPECIFIC TOOLS. You CANNOT complete this task by just "
                "writing JSON - you MUST execute the tools and wait for their responses.\n\n"
                "STEP 1: Store the full transcript in vector memory\n"
                "→ REQUIRED ACTION: Use MemoryStorageTool with the full transcript text\n"
                "→ You MUST wait for the tool to execute and return a result\n"
                "→ DO NOT claim 'memory_stored': true until the tool confirms success\n\n"
                "STEP 2: Create a knowledge graph from the analysis\n"
                "→ REQUIRED ACTION: Use GraphMemoryTool with entity-relationship data\n"
                "→ Extract key entities (people, organizations, topics) from the analysis\n"
                "→ Define relationships between entities\n"
                "→ You MUST wait for the tool to execute and return a result\n"
                "→ DO NOT claim 'graph_created': true until the tool confirms success\n\n"
                "STEP 3: Generate intelligence briefing\n"
                "→ After both tools succeed, synthesize ALL findings into a comprehensive briefing\n"
                "→ Include sections: Overview, Key Insights, Themes, Perspectives, Verified Claims, Conclusion\n"
                "→ Use specific quotes, insights, and claims from previous tasks\n\n"
                "⛔ FORBIDDEN: Generating the final JSON without calling the tools first\n"
                "✅ REQUIRED: Call MemoryStorageTool, wait for response, call GraphMemoryTool, "
                "wait for response, THEN provide final answer\n\n"
                "If a tool fails, set its flag to false and explain the error in your final answer."
            ),
            expected_output=(
                "Final JSON object containing:\n"
                "- memory_stored: boolean (true ONLY if MemoryStorageTool executed successfully)\n"
                "- graph_created: boolean (true ONLY if GraphMemoryTool executed successfully)\n"
                "- briefing: markdown string with comprehensive intelligence analysis\n\n"
                "You MUST call the tools before providing this answer."
            ),
            agent=knowledge_agent,
            context=[acquisition_task, transcription_task, analysis_ref, verification_task],
            callback=task_completion_callback,
        )

    # Determine which tasks to include based on depth
    # Handle combinations of parallel analysis and parallel memory operations
    if enable_parallel_analysis and enable_parallel_memory_ops:
        # Both parallelizations enabled
        base_tasks = [acquisition_task, transcription_task]
        analysis_tasks = [text_analysis_task, fallacy_detection_task, perspective_synthesis_task, analysis_integration_task]
        verification_tasks = [verification_task]
        memory_tasks = [memory_storage_task, graph_memory_task, integration_task]

        if depth == "standard":
            tasks = base_tasks + analysis_tasks  # Through analysis integration
        elif depth == "deep":
            tasks = base_tasks + analysis_tasks + verification_tasks
        else:  # comprehensive or experimental
            tasks = base_tasks + analysis_tasks + verification_tasks + memory_tasks
    elif enable_parallel_analysis:
        # Only analysis parallelization enabled
        base_tasks = [acquisition_task, transcription_task]
        analysis_tasks = [text_analysis_task, fallacy_detection_task, perspective_synthesis_task, analysis_integration_task]
        verification_tasks = [verification_task]
        integration_tasks = [integration_task]

        if depth == "standard":
            tasks = base_tasks + analysis_tasks
        elif depth == "deep":
            tasks = base_tasks + analysis_tasks + verification_tasks
        else:  # comprehensive or experimental
            tasks = base_tasks + analysis_tasks + verification_tasks + integration_tasks
    elif enable_parallel_memory_ops:
        # Only memory parallelization enabled
        base_tasks = [acquisition_task, transcription_task, analysis_task, verification_task]
        memory_tasks = [memory_storage_task, graph_memory_task, integration_task]

        if depth == "standard":
            tasks = base_tasks[:3]  # Through analysis
        elif depth == "deep":
            tasks = base_tasks[:4]  # Add verification
        else:  # comprehensive or experimental
            tasks = base_tasks + memory_tasks
    else:
        # Sequential pattern (original)
        all_tasks = [acquisition_task, transcription_task, analysis_task, verification_task, integration_task]

        if depth == "standard":
            tasks = all_tasks[:3]
        elif depth == "deep":
            tasks = all_tasks[:4]
        else:  # comprehensive or experimental
            tasks = all_tasks

    # Build single crew with all agents and chained tasks
    crew = Crew(
        agents=[
            acquisition_agent,
            transcription_agent,
            analysis_agent,
            verification_agent,
            knowledge_agent,
        ],
        tasks=tasks,
        process=Process.sequential,  # Tasks execute in order with context passing
        verbose=True,
        memory=True,  # Enable cross-task memory
    )

    # Build parallel status message
    parallel_features = []
    if enable_parallel_analysis and depth in ["standard", "deep", "comprehensive", "experimental"]:
        parallel_features.append("analysis")
    if enable_parallel_memory_ops and depth in ["comprehensive", "experimental"]:
        parallel_features.append("memory")

    parallel_status = f"PARALLEL {'+'.join(parallel_features)}" if parallel_features else "SEQUENTIAL"
    _logger.info(f"✅ Built crew with {len(tasks)} chained tasks for {depth} analysis ({parallel_status})")
    return crew


def task_completion_callback(
    task_output: Any,
    populate_agent_context_callback: Any | None = None,
    detect_placeholder_callback: Any | None = None,
    repair_json_callback: Any | None = None,
    extract_key_values_callback: Any | None = None,
    logger_instance: logging.Logger | None = None,
    metrics_instance: Any | None = None,
    agent_coordinators: dict[str, Any] | None = None,
) -> None:
    """Callback executed after each task to extract and propagate structured data.

    CRITICAL FIX: CrewAI task context passes TEXT to LLM prompts, NOT structured
    data to tools. This callback extracts tool results and updates global crew
    context so subsequent tasks can access the data.

    Now includes Pydantic validation to prevent invalid data propagation.

    Args:
        task_output: TaskOutput object from completed task
        populate_agent_context_callback: Optional callback to populate agent tool context
        detect_placeholder_callback: Optional callback to detect placeholder responses
        repair_json_callback: Optional callback to repair malformed JSON
        extract_key_values_callback: Optional callback to extract key-value pairs from text
        logger_instance: Optional logger instance
        metrics_instance: Optional metrics instance
        agent_coordinators: Optional dict of cached agents to update
    """
    _logger = logger_instance or logger

    # Import here to avoid circular dependency
    try:
        from pydantic import ValidationError

        from ..schemas.task_outputs import TASK_OUTPUT_SCHEMAS
    except ImportError:
        _logger.warning("Task output schemas not available - validation disabled")
        TASK_OUTPUT_SCHEMAS = {}
        ValidationError = Exception

    try:
        # Extract structured data from task output
        output_data = {}
        task_name = "unknown"

        # Try to get task name for schema lookup
        if hasattr(task_output, "task") and hasattr(task_output.task, "description"):
            desc = str(task_output.task.description).lower()
            # Infer task type from description keywords
            if "download" in desc or "acquire" in desc:
                task_name = "acquisition"
            elif "transcrib" in desc:
                task_name = "transcription"
            elif "analy" in desc or "map" in desc:
                task_name = "analysis"
            elif "verif" in desc or "fact" in desc:
                task_name = "verification"
            elif "integrat" in desc or "knowledge" in desc:
                task_name = "integration"

        if hasattr(task_output, "raw"):
            raw = task_output.raw
            raw_str = str(raw)

            # DEBUG: Log the raw output to help diagnose extraction failures
            _logger.debug(f"🔍 Raw task output ({len(raw_str)} chars): {raw_str[:500]}...")

            # Try to extract JSON from output
            import json
            import re

            # Try multiple extraction strategies in order of preference
            extraction_strategies = [
                # Strategy 1: JSON code block with ```json (non-greedy, handles nested braces)
                (r"```json\s*(\{(?:[^{}]|\{[^{}]*\})*\})\s*```", "json code block"),
                # Strategy 2: JSON code block without language specifier (non-greedy)
                (r"```\s*(\{(?:[^{}]|\{[^{}]*\})*\})\s*```", "generic code block"),
                # Strategy 3: Inline JSON object with balanced braces
                (r'(\{(?:[^{}"]*"[^"]*"[^{}]*|[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\})', "inline JSON"),
                # Strategy 4: Greedy multiline JSON (last resort)
                (r"(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})", "multiline JSON"),
            ]

            json_match = None
            extraction_method = None

            for pattern, method in extraction_strategies:
                json_match = re.search(pattern, raw_str, re.DOTALL)
                if json_match:
                    extraction_method = method
                    _logger.info(f"✅ Found JSON using strategy: {method}")
                    break

            if json_match:
                try:
                    json_text = json_match.group(1)

                    # Try parsing first without repairs
                    try:
                        output_data = json.loads(json_text)
                        _logger.info(f"📦 Extracted structured data from task output: {list(output_data.keys())}")
                    except json.JSONDecodeError:
                        # Attempt JSON repair for common issues
                        _logger.info("🔧 Attempting JSON repair...")
                        if repair_json_callback:
                            repaired_json = repair_json_callback(json_text)
                            output_data = json.loads(repaired_json)
                            _logger.info(f"✅ Repaired and parsed JSON: {list(output_data.keys())}")
                        else:
                            raise

                    # Validate that we got meaningful data
                    if not output_data or all(not v for v in output_data.values()):
                        _logger.warning("⚠️  Extracted JSON is empty or contains only null values")

                except json.JSONDecodeError as parse_error:
                    _logger.warning(f"❌ Failed to parse JSON from task output ({extraction_method}): {parse_error}")
                    _logger.debug(f"   Failed JSON text: {json_match.group(1)[:200]}...")

                    # FALLBACK: Try to extract key-value pairs from text
                    if extract_key_values_callback:
                        output_data = extract_key_values_callback(raw_str)
                        if output_data:
                            _logger.info(f"🔄 Fallback extraction succeeded: {list(output_data.keys())}")
            else:
                _logger.warning("⚠️  No JSON found in task output, attempting fallback extraction")
                # FALLBACK: Extract key information from plain text
                if extract_key_values_callback:
                    output_data = extract_key_values_callback(raw_str)
                    if output_data:
                        _logger.info(f"🔄 Fallback extraction found: {list(output_data.keys())}")

        # VALIDATION: Validate output against expected schema if available
        if output_data and task_name in TASK_OUTPUT_SCHEMAS:
            schema = TASK_OUTPUT_SCHEMAS[task_name]
            try:
                validated_output = schema(**output_data)
                # Convert back to dict for context propagation
                output_data = validated_output.model_dump()
                _logger.info(f"✅ Task output validated successfully against {schema.__name__} schema")
                # Track validation success
                if metrics_instance:
                    try:
                        metrics_instance.counter(
                            "autointel_task_validation", labels={"task": task_name, "outcome": "success"}
                        ).inc()
                    except Exception:
                        pass
            except ValidationError as val_error:
                _logger.warning(f"⚠️  Task output validation failed for {task_name}: {val_error}")
                _logger.warning(f"   Invalid data: {output_data}")
                # Track validation failure but allow data to propagate (graceful degradation)
                if metrics_instance:
                    try:
                        metrics_instance.counter(
                            "autointel_task_validation", labels={"task": task_name, "outcome": "failure"}
                        ).inc()
                    except Exception:
                        pass
        elif output_data:
            _logger.info(f"ℹ️  No validation schema for task '{task_name}' - skipping validation")

        # FIX #11: PLACEHOLDER DETECTION - Detect when agents generate mock data instead of calling tools
        if output_data and detect_placeholder_callback:
            detect_placeholder_callback(task_name, output_data)

        # Update global crew context with extracted data
        if output_data:
            from ..crewai_tool_wrappers import _GLOBAL_CREW_CONTEXT

            _GLOBAL_CREW_CONTEXT.update(output_data)

            # FIX #16: ENHANCED CONTEXT PROPAGATION LOGGING
            # Show exactly what data was extracted and is now available to subsequent tasks
            data_summary = {}
            for k, v in output_data.items():
                if isinstance(v, str):
                    data_summary[k] = f"str({len(v)} chars)"
                elif isinstance(v, (list, dict)):
                    data_summary[k] = f"{type(v).__name__}({len(v)} items)"
                else:
                    data_summary[k] = type(v).__name__

            _logger.warning(
                f"✅ UPDATED GLOBAL CREW CONTEXT after {task_name} task:\n"
                f"   📦 Keys added: {list(output_data.keys())}\n"
                f"   📊 Data summary: {data_summary}\n"
                f"   🔧 Total context keys: {list(_GLOBAL_CREW_CONTEXT.keys())}"
            )

            # Show critical data previews
            if "file_path" in output_data:
                _logger.warning(f"   📁 CRITICAL: file_path = {output_data['file_path']}")
            if "transcript" in output_data:
                preview = str(output_data["transcript"])[:200]
                _logger.warning(f"   📝 CRITICAL: transcript ({len(output_data['transcript'])} chars) = {preview}...")
            if "url" in output_data:
                _logger.warning(f"   🔗 CRITICAL: url = {output_data['url']}")

            _logger.info(f"✅ Updated global crew context with {len(output_data)} keys: {list(output_data.keys())}")

            # VALIDATION: Check if integration task completed required tool calls
            if task_name == "integration":
                # Integration task MUST use MemoryStorageTool and GraphMemoryTool
                memory_stored = output_data.get("memory_stored", False)
                graph_created = output_data.get("graph_created", False)

                if not memory_stored:
                    _logger.warning("⚠️  Integration task did not call MemoryStorageTool - data not persisted!")
                if not graph_created:
                    _logger.warning("⚠️  Integration task did not call GraphMemoryTool - knowledge graph not created!")

                # Track compliance
                if metrics_instance:
                    try:
                        metrics_instance.counter(
                            "autointel_tool_compliance",
                            labels={"task": "integration", "tool": "memory_storage", "used": str(memory_stored)},
                        ).inc()
                        metrics_instance.counter(
                            "autointel_tool_compliance",
                            labels={"task": "integration", "tool": "graph_memory", "used": str(graph_created)},
                        ).inc()
                    except Exception:
                        pass

            # Also update tools on all cached agents
            if populate_agent_context_callback and agent_coordinators:
                for agent in agent_coordinators.values():
                    populate_agent_context_callback(agent, output_data)
        else:
            _logger.warning("⚠️  No data extracted from task output - downstream tasks may lack context!")

    except Exception as callback_error:
        _logger.error(f"❌ Task completion callback failed: {callback_error}")
        import traceback

        _logger.error(traceback.format_exc())
