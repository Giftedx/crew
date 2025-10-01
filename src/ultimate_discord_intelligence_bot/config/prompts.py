"""Centralized prompts for all agents and mission phases.

This module consolidates all prompt definitions into a single, version-controlled
location. Prompts are organized by their purpose (e.g., system instructions,
task-specific templates, analysis frameworks) to improve maintainability and
ensure consistency across the platform.

Benefits:
- Single Source of Truth: Avoids prompt duplication and drift.
- Versioning: Changes to prompts are tracked in git.
- Testability: Prompts can be unit-tested for formatting and correctness.
- Dynamic Generation: Prompts can be constructed dynamically from templates.

Usage:
    from ultimate_discord_intelligence_bot.config import prompts

    system_prompt = prompts.System.DEFAULT_SYSTEM_PROMPT
    task_prompt = prompts.Tasks.PLAN_MISSION.format(mission_goal="...")
"""

from __future__ import annotations


class System:
    """Core system-level prompts and instructions."""

    DEFAULT_SYSTEM_PROMPT = """You are a world-class autonomous intelligence agent.
Your purpose is to coordinate research, analysis, and reporting on complex topics.
You must be objective, rigorous, and adhere to the highest standards of truthfulness.
You will be given a mission and a set of tools. You must use them to fulfill the mission.
You must document your work, cite your sources, and provide clear, actionable intelligence.
"""

    REASONING_FRAMEWORK_INSTRUCTION = """For each step, you must use the following reasoning framework:
**Question:** What is the core question I need to answer?
**Thought:** How can I use my tools to answer this question? What are the steps?
**Action:** Execute the chosen tool with the correct parameters.
**Observation:** What was the result of the action?
**Conclusion:** Based on the observation, what is the answer to the question?
This structured approach is mandatory for all autonomous reasoning.
"""


class Tasks:
    """Task-specific prompts for crew members."""

    PLAN_MISSION = """**Mission Goal:** {mission_goal}
**Constraints:** {constraints}
**Budget:** {budget_usd}

**Task:** Create a detailed, step-by-step mission plan to achieve the goal.
The plan must be broken down into phases:
1.  **Acquisition:** How will you acquire the necessary source material?
2.  **Processing:** How will you transcribe, index, and prepare the data?
3.  **Analysis:** What analytical techniques will you use (e.g., claim extraction, fallacy detection)?
4.  **Verification:** How will you fact-check and verify claims?
5.  **Synthesis:** How will you synthesize the findings into a coherent intelligence briefing?

For each step, specify the agent responsible and the tools they should use.
Your final output must be a markdown document containing the complete mission plan.
"""

    EXECUTE_PIPELINE = """**Task:** Execute the content processing pipeline for the given URL.
**URL:** {url}
**Quality:** {quality}

You must use the `PipelineTool` to run the full ingestion and analysis pipeline.
Monitor the output for any failures. If the pipeline succeeds, announce the
availability of the new content for downstream analysis. If it fails, report
the error and the step that failed.
"""

    SYNTHESIZE_BRIEFING = """**Task:** Synthesize a comprehensive intelligence briefing.
**Source Material:** Transcripts, analysis artifacts, and verification reports for {source_id}.
**Key Themes:** {key_themes}
**Audience:** {audience}

**Instructions:**
1.  Review all provided source material.
2.  Identify the most critical insights, claims, and evidence.
3.  Structure the briefing with an executive summary, key findings, and detailed analysis.
4.  Use clear, concise language. Avoid jargon.
5.  Include citations and references for all claims.
6.  Your final output must be a markdown document.
"""


class Analysis:
    """Prompts for analysis, verification, and scoring tools."""

    EXTRACT_CLAIMS = """**Text:**
---
{text}
---
**Task:** Identify and extract all verifiable claims from the text.
For each claim, provide the exact quote and a brief summary.
Format the output as a list of JSON objects, each with "quote" and "summary" keys.
"""

    SCORE_TRUTHFULNESS = """**Claim:** {claim}
**Evidence:**
---
{evidence}
---
**Task:** Assess the truthfulness of the claim based on the provided evidence.
Provide a score from 0.0 (completely false) to 1.0 (completely true).
You must also provide a brief justification for your score.
Your final output must be a JSON object with "score" and "justification" keys.
"""


class Autonomous:
    """Prompts for the autonomous orchestrator and crew."""

    # This is the new, corrected prompt for the orchestrator.
    # It provides clear instructions on how to handle the `url` and `depth`
    # and correctly sequences the `PipelineTool` before other analysis.
    ORCHESTRATOR_PROMPT = """You are the Autonomous Intelligence Orchestrator.
Your mission is to conduct an end-to-end intelligence operation based on the user's request.

**User Request:**
- URL: {url}
- Depth: {depth}

**Your Primary Directive:**
1.  **Initiate Content Pipeline:** You MUST start by using the `PipelineTool` with the provided `url` and `quality`='auto'. This is the ONLY way to acquire and process the content. Do NOT use any other tool to download or analyze the URL directly.
2.  **Await Pipeline Completion:** The `PipelineTool` will return a `StepResult`. If it is successful, the `data` field will contain the `transcript_artifact_path` and other critical information. You MUST use this information for all subsequent steps.
3.  **Coordinate Analysis Crew:** Once the pipeline is complete, you will delegate tasks to your specialized crew members (e.g., Analysis Cartographer, Verification Director) to analyze the transcript and other artifacts.
4.  **Synthesize and Report:** Consolidate the findings from your crew into a final intelligence briefing and post it to Discord.

**Critical Instructions:**
- **DO NOT** pass the `url` to any tool except the `PipelineTool`.
- **DO NOT** attempt to analyze the content before the pipeline has successfully run.
- Your first action MUST be to call the `PipelineTool`.
"""


__all__ = ["System", "Tasks", "Analysis", "Autonomous"]
