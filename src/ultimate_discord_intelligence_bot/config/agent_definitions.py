"""Agent definitions separated from tool wiring for better maintainability.

This module defines agent configurations as structured data, making them easier to
test, modify, and maintain without the complexity of the full crew.py file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentDefinition:
    """Structured definition of an agent."""

    name: str
    role: str
    goal: str
    backstory: str
    tools: list[str] = field(default_factory=list)
    verbose: bool = True
    allow_delegation: bool = False
    max_iter: int = 3
    memory: bool = True
    max_rpm: int = 10
    max_execution_time: int = 600
    step_callback: str | None = None
    planning: bool = True
    max_retry_limit: int = 3
    max_prompt_tokens: int = 4000
    max_completion_tokens: int = 1000
    temperature: float = 0.1
    top_p: float = 0.9
    metadata: dict[str, Any] = field(default_factory=dict)


# Core agent definitions
AGENT_DEFINITIONS = {
    "mission_orchestrator": AgentDefinition(
        name="mission_orchestrator",
        role="Autonomy Mission Orchestrator",
        goal="Coordinate end-to-end missions, sequencing depth, specialists, and budgets.",
        backstory="Mission orchestration and strategic control with multimodal planning capabilities.",
        tools=[
            "PipelineTool",
            "AdvancedPerformanceAnalyticsTool",
            "EnhancedContentAnalysisTool",
            "MemoryStorageTool",
            "DiscordPostTool",
            "DiscordPrivateAlertTool",
        ],
        allow_delegation=True,
        max_iter=5,
        max_execution_time=1800,
        planning=True,
    ),
    "executive_supervisor": AgentDefinition(
        name="executive_supervisor",
        role="Executive Supervisor",
        goal="Oversee mission execution, quality control, and strategic decision-making.",
        backstory="Executive oversight with deep understanding of content analysis and quality assurance.",
        tools=[
            "EnhancedContentAnalysisTool",
            "AdvancedPerformanceAnalyticsTool",
            "MemoryStorageTool",
            "DiscordPrivateAlertTool",
        ],
        allow_delegation=True,
        max_iter=3,
        max_execution_time=1200,
    ),
    "acquisition_specialist": AgentDefinition(
        name="acquisition_specialist",
        role="Content Acquisition Specialist",
        goal="Download and acquire content from multiple platforms efficiently.",
        backstory="Expert in content acquisition from YouTube, TikTok, Twitter, and other platforms.",
        tools=[
            "MultiPlatformDownloadTool",
            "EnhancedYouTubeTool",
            "TikTokEnhancedDownloadTool",
            "AudioTranscriptionTool",
            "TranscriptIndexTool",
        ],
        max_iter=3,
        max_execution_time=900,
    ),
    "content_analyst": AgentDefinition(
        name="content_analyst",
        role="Content Analysis Specialist",
        goal="Analyze content for political topics, sentiment, and claims.",
        backstory="Expert in content analysis with focus on political content and bias detection.",
        tools=[
            "EnhancedContentAnalysisTool",
            "ClaimExtractorTool",
            "SentimentAnalysisTool",
            "PoliticalTopicDetectionTool",
            "BiasDetectionTool",
        ],
        max_iter=3,
        max_execution_time=600,
    ),
    "fact_checker": AgentDefinition(
        name="fact_checker",
        role="Fact-Checking Specialist",
        goal="Verify claims and provide accurate fact-checking results.",
        backstory="Expert in fact-checking with access to reliable sources and verification tools.",
        tools=[
            "ClaimExtractorTool",
            "FactCheckingTool",
            "SourceVerificationTool",
            "MemoryStorageTool",
        ],
        max_iter=3,
        max_execution_time=600,
    ),
    "knowledge_integrator": AgentDefinition(
        name="knowledge_integrator",
        role="Knowledge Integration Specialist",
        goal="Integrate and synthesize knowledge from multiple sources.",
        backstory="Expert in knowledge synthesis and integration across different content types.",
        tools=[
            "MemoryStorageTool",
            "GraphMemoryTool",
            "HippoRAGTool",
            "KnowledgeSynthesisTool",
        ],
        max_iter=3,
        max_execution_time=600,
    ),
    "quality_assurance_specialist": AgentDefinition(
        name="quality_assurance_specialist",
        role="Quality Assurance Specialist",
        goal="Ensure high quality standards across all analysis outputs.",
        backstory="Expert in quality assurance with focus on accuracy and reliability.",
        tools=[
            "EnhancedContentAnalysisTool",
            "QualityAssessmentTool",
            "AdvancedPerformanceAnalyticsTool",
            "DiscordPrivateAlertTool",
        ],
        max_iter=3,
        max_execution_time=600,
    ),
    "system_reliability_officer": AgentDefinition(
        name="system_reliability_officer",
        role="System Reliability Officer",
        goal="Monitor system health and ensure reliable operation.",
        backstory="Expert in system monitoring and reliability engineering.",
        tools=[
            "AdvancedPerformanceAnalyticsTool",
            "SystemHealthMonitorTool",
            "DiscordPrivateAlertTool",
        ],
        max_iter=2,
        max_execution_time=300,
    ),
    "compliance_regulatory_officer": AgentDefinition(
        name="compliance_regulatory_officer",
        role="Compliance & Regulatory Officer",
        goal="Ensure compliance with regulations and content policies.",
        backstory="Expert in regulatory compliance and content policy enforcement.",
        tools=[
            "ContentPolicyCheckTool",
            "ComplianceMonitorTool",
            "DiscordPrivateAlertTool",
        ],
        max_iter=2,
        max_execution_time=300,
    ),
    "visual_intelligence_specialist": AgentDefinition(
        name="visual_intelligence_specialist",
        role="Visual Intelligence Specialist",
        goal="Analyze visual content including images and videos.",
        backstory="Expert in visual content analysis and computer vision.",
        tools=[
            "ImageAnalysisTool",
            "VideoFrameAnalysisTool",
            "VisualSummaryTool",
            "MultimodalAnalysisTool",
        ],
        max_iter=3,
        max_execution_time=600,
    ),
}


# Agent groups for different workflows
AGENT_GROUPS = {
    "content_pipeline": [
        "acquisition_specialist",
        "content_analyst",
        "fact_checker",
        "knowledge_integrator",
    ],
    "quality_control": [
        "quality_assurance_specialist",
        "system_reliability_officer",
        "compliance_regulatory_officer",
    ],
    "multimodal_analysis": [
        "visual_intelligence_specialist",
        "content_analyst",
        "knowledge_integrator",
    ],
    "mission_control": [
        "mission_orchestrator",
        "executive_supervisor",
        "system_reliability_officer",
    ],
}


def get_agent_definition(name: str) -> AgentDefinition | None:
    """Get an agent definition by name."""
    return AGENT_DEFINITIONS.get(name)


def get_agent_group(group_name: str) -> list[str]:
    """Get a list of agent names for a specific group."""
    return AGENT_GROUPS.get(group_name, [])


def get_all_agent_names() -> list[str]:
    """Get all agent names."""
    return list(AGENT_DEFINITIONS.keys())


def get_agents_by_tool(tool_name: str) -> list[str]:
    """Get agents that use a specific tool."""
    agents = []
    for name, definition in AGENT_DEFINITIONS.items():
        if tool_name in definition.tools:
            agents.append(name)
    return agents


def validate_agent_definitions() -> list[str]:
    """Validate agent definitions and return any issues."""
    issues = []

    for name, definition in AGENT_DEFINITIONS.items():
        if not definition.name:
            issues.append(f"Agent {name} has no name")

        if not definition.role:
            issues.append(f"Agent {name} has no role")

        if not definition.goal:
            issues.append(f"Agent {name} has no goal")

        if not definition.backstory:
            issues.append(f"Agent {name} has no backstory")

        if definition.max_iter < 1:
            issues.append(f"Agent {name} has invalid max_iter: {definition.max_iter}")

        if definition.max_execution_time < 1:
            issues.append(f"Agent {name} has invalid max_execution_time: {definition.max_execution_time}")

        if definition.temperature < 0 or definition.temperature > 2:
            issues.append(f"Agent {name} has invalid temperature: {definition.temperature}")

    return issues
