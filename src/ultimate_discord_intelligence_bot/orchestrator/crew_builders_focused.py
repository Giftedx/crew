"""Focused crew building utilities for CrewAI orchestration.

This module provides the core crew building logic extracted from the large
build_intelligence_crew function to improve maintainability.

Extracted from crew_builders.py to improve maintainability and organization.
"""
import logging
from typing import Any
from urllib.parse import urlparse
from crewai import Crew, Process, Task
from ultimate_discord_intelligence_bot.settings import Settings
logger = logging.getLogger(__name__)

def create_acquisition_task(agent: Any, callback: Any | None=None, content_url: str | None=None) -> Task:
    """Create the content acquisition task.

    Args:
        agent: Acquisition agent instance
        callback: Optional task completion callback

    Returns:
        Configured acquisition task
    """
    description_template = 'Download and acquire media content from {url}. Use the appropriate download tool for the platform (YouTube, TikTok, Twitter, etc.). Extract metadata and obtain the raw media file. \n\nCRITICAL: Return your results as JSON with these exact keys: url, video_id, file_path, title, description, author, duration, platform. The url field MUST contain {url}. The video_id can be extracted from the URL or set to the URL itself. Wrap the JSON in ```json``` code blocks for easy parsing.'
    formatted_url = content_url or '{url}'
    return Task(description=description_template.format(url=formatted_url), expected_output='JSON with url, video_id, file_path, title, description, author, duration, platform', agent=agent, callback=callback)

def create_transcription_task(agent: Any, acquisition_task: Task, callback: Any | None=None) -> Task:
    """Create the transcription task.

    Args:
        agent: Transcription agent instance
        acquisition_task: Previous acquisition task for context
        callback: Optional task completion callback

    Returns:
        Configured transcription task
    """
    return Task(description="STEP 1: Extract the 'file_path' field from the previous task's JSON output. STEP 2: YOU MUST CALL AudioTranscriptionTool(file_path=<extracted_path>). DO NOT generate placeholder text like 'Your transcribed text goes here'. DO NOT respond until the tool returns actual transcript data. STEP 3: Create timeline anchors for key moments using the real transcript. \n\nCRITICAL: Return your results as JSON with these exact keys: transcript, timeline_anchors, transcript_length, quality_score. Wrap the JSON in ```json``` code blocks.", expected_output='JSON with transcript (min 1000 chars from AudioTranscriptionTool), timeline_anchors (list of dicts), transcript_length (int), quality_score (0.0-1.0). ❌ REJECT: Placeholder text. ❌ REJECT: transcript_length < 100. ✅ ACCEPT: Real transcript with actual spoken words from the media file.', agent=agent, context=[acquisition_task], callback=callback)

def create_analysis_tasks(agents: dict[str, Any], transcription_task: Task, depth: str, enable_parallel: bool, callback: Any | None=None, logger_instance: logging.Logger | None=None) -> list[Task]:
    """Create analysis tasks based on configuration.

    Args:
        agents: Dictionary of analysis agents
        transcription_task: Previous transcription task for context
        depth: Analysis depth level
        enable_parallel: Whether to use parallel analysis subtasks
        callback: Optional task completion callback
        logger_instance: Optional logger instance

    Returns:
        List of configured analysis tasks
    """
    _logger = logger_instance or logger
    if enable_parallel:
        _logger.info('⚡ Using PARALLEL analysis subtasks (async_execution=True)')
        text_analysis_task = Task(description="STEP 1: Extract 'transcript' field from previous task's JSON output. STEP 2: Perform comprehensive text analysis including: - Linguistic patterns and readability analysis - Theme extraction and topic modeling - Sentiment analysis and emotional indicators - Keyword extraction and frequency analysis - Content structure and organization analysis \n\nCRITICAL: Return your results as JSON with these exact keys: linguistic_patterns, themes, sentiment_analysis, keywords, content_structure. Wrap the JSON in ```json``` code blocks.", expected_output='JSON with linguistic_patterns, themes, sentiment_analysis, keywords, content_structure', agent=agents['analysis_cartographer'], context=[transcription_task], callback=callback)
        fact_checking_task = Task(description="STEP 1: Extract 'transcript' field from previous task's JSON output. STEP 2: Perform comprehensive fact-checking analysis including: - Claim identification and extraction - Source verification and credibility assessment - Logical fallacy detection - Evidence quality evaluation - Truth assessment and confidence scoring \n\nCRITICAL: Return your results as JSON with these exact keys: claims, source_verification, logical_analysis, evidence_quality, truth_assessment. Wrap the JSON in ```json``` code blocks.", expected_output='JSON with claims, source_verification, logical_analysis, evidence_quality, truth_assessment', agent=agents['verification_director'], context=[transcription_task], callback=callback)
        bias_analysis_task = Task(description="STEP 1: Extract 'transcript' field from previous task's JSON output. STEP 2: Perform comprehensive bias and manipulation analysis including: - Bias indicators and type classification - Deception detection and manipulation techniques - Narrative integrity assessment - Psychological threat evaluation - Trustworthiness scoring \n\nCRITICAL: Return your results as JSON with these exact keys: bias_indicators, deception_analysis, narrative_integrity, psychological_threats, trustworthiness. Wrap the JSON in ```json``` code blocks.", expected_output='JSON with bias_indicators, deception_analysis, narrative_integrity, psychological_threats, trustworthiness', agent=agents['verification_director'], context=[transcription_task], callback=callback)
        return [text_analysis_task, fact_checking_task, bias_analysis_task]
    else:
        analysis_task = Task(description=f"STEP 1: Extract 'transcript' field from previous task's JSON output. STEP 2: Perform comprehensive content analysis including: - Linguistic patterns and readability analysis - Theme extraction and topic modeling - Sentiment analysis and emotional indicators - Fact-checking and claim verification - Bias detection and manipulation analysis - Source credibility assessment \n\nDepth level: {depth} - adjust analysis thoroughness accordingly. \n\nCRITICAL: Return your results as JSON with these exact keys: linguistic_patterns, themes, sentiment_analysis, fact_checking, bias_analysis, credibility. Wrap the JSON in ```json``` code blocks.", expected_output='JSON with linguistic_patterns, themes, sentiment_analysis, fact_checking, bias_analysis, credibility', agent=agents['analysis_cartographer'], context=[transcription_task], callback=callback)
        return [analysis_task]

def create_knowledge_integration_task(agent: Any, previous_tasks: list[Task], depth: str, callback: Any | None=None) -> Task:
    """Create the knowledge integration task.

    Args:
        agent: Knowledge integration agent instance
        previous_tasks: List of previous tasks for context
        depth: Analysis depth level
        callback: Optional task completion callback

    Returns:
        Configured knowledge integration task
    """
    return Task(description=f'STEP 1: Extract and synthesize data from ALL previous task outputs. STEP 2: Perform comprehensive knowledge integration including: - Cross-reference findings from all analysis stages - Identify patterns and correlations across data sources - Generate actionable insights and recommendations - Create comprehensive summary with key findings - Assess overall content quality and reliability \n\nDepth level: {depth} - adjust integration thoroughness accordingly. \n\nCRITICAL: Return your results as JSON with these exact keys: synthesis_analysis, key_insights, recommendations, quality_assessment, summary. Wrap the JSON in ```json``` code blocks.', expected_output='JSON with synthesis_analysis, key_insights, recommendations, quality_assessment, summary', agent=agent, context=previous_tasks, callback=callback)

def build_crew_with_tasks(tasks: list[Task], process_type: Process=Process.sequential, logger_instance: logging.Logger | None=None) -> Crew:
    """Build a CrewAI crew with the provided tasks.

    Args:
        tasks: List of configured tasks
        process_type: CrewAI process type (sequential or hierarchical)
        logger_instance: Optional logger instance

    Returns:
        Configured Crew instance
    """
    _logger = logger_instance or logger
    settings = Settings()
    crew = Crew(tasks=tasks, process=process_type, memory=getattr(settings, 'enable_crew_memory', True), planning=getattr(settings, 'enable_crew_planning', True), cache=getattr(settings, 'enable_crew_cache', True), max_rpm=getattr(settings, 'crew_max_rpm', 10), max_execution_time=getattr(settings, 'crew_max_execution_time', 300), verbose=getattr(settings, 'crew_verbose', True))
    _logger.info(f'🏗️  Built crew with {len(tasks)} tasks using {process_type} process')
    return crew

def build_intelligence_crew(url: str, depth: str, agent_getter_callback: Any | None=None, task_completion_callback: Any | None=None, logger_instance: logging.Logger | None=None, enable_parallel_memory_ops: bool=False, enable_parallel_analysis: bool=False, enable_parallel_fact_checking: bool=False) -> Crew:
    """Build a complete intelligence crew with optimized parallel execution.

    This function creates a CrewAI crew with tasks that can execute in parallel
    where dependencies allow, significantly improving performance.

    Args:
        url: URL to analyze
        depth: Analysis depth (standard, deep, comprehensive, experimental)
        agent_getter_callback: Function to get or create agents
        task_completion_callback: Callback for task completion events
        logger_instance: Optional logger instance
        enable_parallel_memory_ops: Enable parallel memory operations
        enable_parallel_analysis: Enable parallel analysis tasks
        enable_parallel_fact_checking: Enable parallel fact checking

    Returns:
        Configured Crew instance with optimized task execution
    """
    _logger = logger_instance or logger
    from .parallel_config import estimate_performance_improvement, get_parallel_execution_config
    parallel_config = get_parallel_execution_config()
    parsed_url = urlparse(url)
    content_domain = parsed_url.netloc or parsed_url.path or 'unknown'
    parallel_config.setdefault('target_domain', content_domain)
    _logger.info(f'🌐 Target content domain: {content_domain}')
    if enable_parallel_analysis is not None:
        parallel_config['enable_parallel_analysis'] = enable_parallel_analysis
    if enable_parallel_fact_checking is not None:
        parallel_config['enable_parallel_fact_checking'] = enable_parallel_fact_checking
    if enable_parallel_memory_ops is not None:
        parallel_config['enable_parallel_memory_ops'] = enable_parallel_memory_ops
    _logger.info(f'🏗️  Building intelligence crew for depth: {depth}')
    _logger.info(f'⚡ Parallel execution: analysis={parallel_config['enable_parallel_analysis']}, fact_checking={parallel_config['enable_parallel_fact_checking']}, memory={parallel_config['enable_parallel_memory_ops']}')
    estimated_tasks = 3 + (2 if depth in ['deep', 'comprehensive', 'experimental'] else 0)
    if parallel_config['enable_parallel_analysis']:
        estimated_tasks += 2
    if depth in ['comprehensive', 'experimental']:
        estimated_tasks += 2
    perf_estimate = estimate_performance_improvement(estimated_tasks, parallel_config)
    if perf_estimate['parallelization_feasible']:
        _logger.info(f'📈 Expected performance improvement: {perf_estimate['estimated_time_savings_percent']:.1f}% time savings')
    if agent_getter_callback:
        agents = {'acquisition_specialist': agent_getter_callback('acquisition_specialist'), 'transcription_engineer': agent_getter_callback('transcription_engineer'), 'analysis_cartographer': agent_getter_callback('analysis_cartographer'), 'verification_director': agent_getter_callback('verification_director'), 'knowledge_integrator': agent_getter_callback('knowledge_integrator')}
    else:
        from ..crew_core import UltimateDiscordIntelligenceBotCrew
        crew_instance = UltimateDiscordIntelligenceBotCrew()
        agents = {'acquisition_specialist': crew_instance.acquisition_specialist(), 'transcription_engineer': crew_instance.transcription_engineer(), 'analysis_cartographer': crew_instance.analysis_cartographer(), 'verification_director': crew_instance.verification_director(), 'knowledge_integrator': crew_instance.knowledge_integrator()}
    tasks = []
    acquisition_task = create_acquisition_task(agent=agents['acquisition_specialist'], callback=task_completion_callback, content_url=url)
    tasks.append(acquisition_task)
    transcription_task = create_transcription_task(agent=agents['transcription_engineer'], acquisition_task=acquisition_task, callback=task_completion_callback)
    tasks.append(transcription_task)
    if parallel_config['enable_parallel_analysis']:
        from .parallel_execution_engine import create_enhanced_parallel_analysis_tasks
        analysis_tasks = create_enhanced_parallel_analysis_tasks(agents=agents, transcription_task=transcription_task, depth=depth, enable_parallel=True, callback=task_completion_callback, logger_instance=_logger)
    else:
        analysis_tasks = create_analysis_tasks(agents=agents, transcription_task=transcription_task, depth=depth, enable_parallel=False, callback=task_completion_callback, logger_instance=_logger)
    tasks.extend(analysis_tasks)
    if depth in ['deep', 'comprehensive', 'experimental']:
        knowledge_task = create_knowledge_integration_task(agent=agents['knowledge_integrator'], previous_tasks=analysis_tasks, depth=depth, callback=task_completion_callback)
        tasks.append(knowledge_task)
    from .parallel_config import get_optimal_crew_process_type
    process_type = get_optimal_crew_process_type(len(tasks), parallel_config)
    if process_type == 'hierarchical':
        _logger.info('⚡ Using hierarchical process for parallel task execution')
    else:
        _logger.info('🔄 Using sequential process for traditional execution')
    crew = build_crew_with_tasks(tasks=tasks, process_type=process_type, logger_instance=_logger)
    _logger.info(f'✅ Built intelligence crew with {len(tasks)} tasks for {depth} analysis')
    return crew