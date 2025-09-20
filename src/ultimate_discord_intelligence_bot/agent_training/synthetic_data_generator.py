#!/usr/bin/env python3
"""
Synthetic Data Generator for CrewAI Agent Training

Generates high-quality synthetic training examples for agents to learn optimal
tool usage patterns, reasoning workflows, and autonomous decision-making.
"""

import json
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ToolUsageExample:
    """Represents a synthetic training example for tool usage."""

    scenario: str
    context: dict[str, Any]
    optimal_tools: list[str]
    tool_sequence: list[dict[str, Any]]
    reasoning_steps: list[str]
    expected_outcome: str
    anti_patterns: list[dict[str, str]]
    quality_score: float


class SyntheticDataGenerator:
    """Generates synthetic training data for CrewAI agents."""

    def __init__(self, tools_available: list[str]):
        self.tools_available = tools_available
        self.scenario_templates = self._load_scenario_templates()
        self.reasoning_patterns = self._load_reasoning_patterns()

    def _load_scenario_templates(self) -> dict[str, dict]:
        """Load scenario templates for different agent roles."""
        return {
            "content_analysis": {
                "scenarios": [
                    "YouTube video about political topic requires fact-checking",
                    "Twitch stream contains controversial claims needing verification",
                    "Social media post spreading misinformation requires debunking",
                    "Podcast episode makes historical claims needing context",
                    "News article requires cross-platform sentiment analysis",
                ],
                "complexity_levels": ["basic", "intermediate", "advanced", "expert"],
                "required_tools": ["pipeline_tool", "fact_check_tool", "fallacy_tool", "vector_tool"],
            },
            "fact_checking": {
                "scenarios": [
                    "Political claim requires multi-source verification",
                    "Scientific statement needs peer-reviewed source validation",
                    "Historical fact requires authoritative source confirmation",
                    "Statistical claim needs data source verification",
                    "Quote attribution requires original source finding",
                ],
                "complexity_levels": ["straightforward", "nuanced", "contested", "deeply_complex"],
                "required_tools": [
                    "fact_check_tool",
                    "context_verification_tool",
                    "vector_tool",
                    "claim_extractor_tool",
                ],
            },
            "cross_platform_monitoring": {
                "scenarios": [
                    "Track viral misinformation across multiple platforms",
                    "Monitor developing story sentiment evolution",
                    "Identify coordinated inauthentic behavior patterns",
                    "Track influencer narrative consistency",
                    "Monitor breaking news spread patterns",
                ],
                "complexity_levels": ["single_platform", "multi_platform", "cross_network", "ecosystem_wide"],
                "required_tools": [
                    "multi_platform_monitor_tool",
                    "social_media_monitor_tool",
                    "x_monitor_tool",
                    "sentiment_tool",
                ],
            },
            "character_profiling": {
                "scenarios": [
                    "Build comprehensive personality profile from content history",
                    "Track trustworthiness evolution over time",
                    "Identify behavioral pattern changes",
                    "Analyze rhetoric consistency across platforms",
                    "Evaluate credibility based on fact-check history",
                ],
                "complexity_levels": ["surface_level", "psychological", "longitudinal", "comprehensive"],
                "required_tools": ["character_profile_tool", "truth_scoring_tool", "timeline_tool", "sentiment_tool"],
            },
        }

    def _load_reasoning_patterns(self) -> dict[str, list[str]]:
        """Load reasoning step templates for different thinking patterns."""
        return {
            "analytical": [
                "Define the specific information need or question",
                "Identify the most appropriate tools for the task",
                "Plan the sequence of tool usage for optimal results",
                "Execute tools with careful parameter selection",
                "Validate results and cross-check with alternative methods",
                "Synthesize findings into coherent conclusion",
                "Identify limitations and areas for further investigation",
            ],
            "verification": [
                "Extract specific claims or statements to verify",
                "Determine verification criteria and evidence standards",
                "Search for authoritative sources using multiple methods",
                "Cross-reference findings across independent sources",
                "Evaluate source credibility and potential bias",
                "Assess confidence level based on evidence quality",
                "Document verification process for transparency",
            ],
            "investigative": [
                "Map the scope and boundaries of the investigation",
                "Identify key actors, events, and relationships",
                "Gather evidence systematically from multiple sources",
                "Build timeline of events and causal relationships",
                "Look for patterns, contradictions, or gaps",
                "Verify critical evidence through independent means",
                "Construct comprehensive narrative from findings",
            ],
            "defensive": [
                "Understand the position or claim being defended",
                "Identify the strongest supporting evidence available",
                "Anticipate potential counterarguments or criticisms",
                "Gather additional context that strengthens the position",
                "Frame arguments in the most compelling way",
                "Address weaknesses proactively and honestly",
                "Present defense with appropriate confidence level",
            ],
        }

    def generate_training_batch(
        self, agent_role: str, batch_size: int = 50, complexity_distribution: dict[str, float] | None = None
    ) -> list[ToolUsageExample]:
        """Generate a batch of synthetic training examples for an agent."""
        if complexity_distribution is None:
            complexity_distribution = {"basic": 0.3, "intermediate": 0.4, "advanced": 0.2, "expert": 0.1}

        examples = []
        scenario_config = self.scenario_templates.get(agent_role, self.scenario_templates["content_analysis"])

        for _ in range(batch_size):
            complexity = self._sample_complexity(complexity_distribution)
            example = self._generate_single_example(agent_role, scenario_config, complexity)
            examples.append(example)

        return examples

    def _sample_complexity(self, distribution: dict[str, float]) -> str:
        """Sample complexity level based on distribution."""
        levels = list(distribution.keys())
        weights = list(distribution.values())
        return random.choices(levels, weights=weights)[0]

    def _generate_single_example(self, agent_role: str, scenario_config: dict, complexity: str) -> ToolUsageExample:
        """Generate a single synthetic training example."""
        # Select scenario
        scenario = random.choice(scenario_config["scenarios"])

        # Generate context
        context = self._generate_context(agent_role, scenario, complexity)

        # Determine optimal tools
        optimal_tools = self._select_optimal_tools(agent_role, scenario_config, complexity, context)

        # Generate tool sequence
        tool_sequence = self._generate_tool_sequence(optimal_tools, context, complexity)

        # Generate reasoning steps
        reasoning_steps = self._generate_reasoning_steps(agent_role, scenario, complexity)

        # Generate expected outcome
        expected_outcome = self._generate_expected_outcome(scenario, tool_sequence, complexity)

        # Generate anti-patterns
        anti_patterns = self._generate_anti_patterns(optimal_tools, complexity)

        # Calculate quality score
        quality_score = self._calculate_quality_score(tool_sequence, reasoning_steps, complexity)

        return ToolUsageExample(
            scenario=scenario,
            context=context,
            optimal_tools=optimal_tools,
            tool_sequence=tool_sequence,
            reasoning_steps=reasoning_steps,
            expected_outcome=expected_outcome,
            anti_patterns=anti_patterns,
            quality_score=quality_score,
        )

    def _generate_context(self, agent_role: str, scenario: str, complexity: str) -> dict[str, Any]:
        """Generate realistic context for the scenario."""
        base_context = {
            "timestamp": datetime.now().isoformat(),
            "agent_role": agent_role,
            "complexity_level": complexity,
            "available_tools": self.tools_available,
            "confidence_threshold": 0.8 if complexity in ["advanced", "expert"] else 0.7,
        }

        # Add scenario-specific context
        if "youtube" in scenario.lower() or "video" in scenario.lower():
            base_context.update(
                {
                    "content_type": "video",
                    "platform": "youtube",
                    "duration": random.randint(300, 3600),  # 5min to 1hr
                    "view_count": random.randint(1000, 1000000),
                    "has_transcript": True,
                    "language": "english",
                }
            )
        elif "twitch" in scenario.lower() or "stream" in scenario.lower():
            base_context.update(
                {
                    "content_type": "livestream",
                    "platform": "twitch",
                    "duration": random.randint(1800, 14400),  # 30min to 4hr
                    "viewer_count": random.randint(100, 50000),
                    "is_live": random.choice([True, False]),
                    "language": "english",
                }
            )
        elif "social media" in scenario.lower() or "post" in scenario.lower():
            base_context.update(
                {
                    "content_type": "social_post",
                    "platform": random.choice(["twitter", "reddit", "instagram", "tiktok"]),
                    "engagement_score": random.uniform(0.1, 10.0),
                    "viral_potential": random.choice(["low", "medium", "high"]),
                    "language": "english",
                }
            )

        # Add complexity-specific context
        if complexity in ["advanced", "expert"]:
            base_context.update(
                {
                    "requires_deep_analysis": True,
                    "multiple_perspectives_needed": True,
                    "high_stakes": True,
                    "time_sensitive": random.choice([True, False]),
                }
            )

        return base_context

    def _select_optimal_tools(
        self, agent_role: str, scenario_config: dict, complexity: str, context: dict
    ) -> list[str]:
        """Select the optimal tools for the given scenario."""
        base_tools = scenario_config.get("required_tools", [])
        optimal_tools = base_tools.copy()

        # Add complexity-based tools
        if complexity in ["advanced", "expert"]:
            enhancement_tools = [
                "context_verification_tool",
                "steelman_argument_tool",
                "perspective_synthesizer_tool",
                "timeline_tool",
                "debate_tool",
            ]
            optimal_tools.extend([tool for tool in enhancement_tools if tool in self.tools_available])

        # Add context-based tools
        if context.get("platform") == "youtube":
            optimal_tools.extend(["youtube_tool", "transcript_index_tool"])
        elif context.get("platform") == "twitch":
            optimal_tools.extend(["twitch_download_tool", "audio_transcription_tool"])

        if context.get("requires_deep_analysis"):
            optimal_tools.extend(["memory_storage_tool", "trustworthiness_tracker_tool"])

        # Remove duplicates and filter available tools
        optimal_tools = list(set([tool for tool in optimal_tools if tool in self.tools_available]))

        return optimal_tools

    def _generate_tool_sequence(self, optimal_tools: list[str], context: dict, complexity: str) -> list[dict[str, Any]]:
        """Generate the optimal sequence of tool usage."""
        sequence = []

        # Phase 1: Content acquisition
        if context.get("content_type") == "video":
            sequence.append(
                {
                    "tool": "pipeline_tool",
                    "action": "download_and_transcribe",
                    "parameters": {"url": "{{content_url}}", "quality": "high"},
                    "reasoning": "Need full transcript and metadata for analysis",
                }
            )
        elif context.get("content_type") == "social_post":
            sequence.append(
                {
                    "tool": "multi_platform_download_tool",
                    "action": "fetch_content",
                    "parameters": {"url": "{{content_url}}", "include_context": True},
                    "reasoning": "Gather post content and surrounding discussion context",
                }
            )

        # Phase 2: Initial analysis
        if "claim_extractor_tool" in optimal_tools:
            sequence.append(
                {
                    "tool": "claim_extractor_tool",
                    "action": "extract_claims",
                    "parameters": {
                        "text": "{{transcript}}",
                        "confidence_threshold": context.get("confidence_threshold", 0.7),
                    },
                    "reasoning": "Identify specific factual claims that can be verified",
                }
            )

        # Phase 3: Verification and fact-checking
        if "fact_check_tool" in optimal_tools:
            sequence.append(
                {
                    "tool": "fact_check_tool",
                    "action": "verify_claims",
                    "parameters": {
                        "claims": "{{extracted_claims}}",
                        "search_depth": "thorough" if complexity in ["advanced", "expert"] else "standard",
                    },
                    "reasoning": "Verify factual accuracy using authoritative sources",
                }
            )

        # Phase 4: Context and perspective gathering
        if "vector_tool" in optimal_tools:
            sequence.append(
                {
                    "tool": "vector_tool",
                    "action": "semantic_search",
                    "parameters": {"query": "{{main_topic}}", "limit": 10},
                    "reasoning": "Find related content and historical context",
                }
            )

        # Phase 5: Advanced analysis (for complex scenarios)
        if complexity in ["advanced", "expert"]:
            if "fallacy_tool" in optimal_tools:
                sequence.append(
                    {
                        "tool": "fallacy_tool",
                        "action": "detect_fallacies",
                        "parameters": {"text": "{{transcript}}", "strictness": "high"},
                        "reasoning": "Identify logical errors and reasoning flaws",
                    }
                )

            if "steelman_argument_tool" in optimal_tools:
                sequence.append(
                    {
                        "tool": "steelman_argument_tool",
                        "action": "build_strongest_case",
                        "parameters": {"claim": "{{primary_claim}}", "evidence": "{{fact_check_results}}"},
                        "reasoning": "Present the strongest possible version of the argument",
                    }
                )

        # Phase 6: Synthesis and storage
        if "memory_storage_tool" in optimal_tools:
            sequence.append(
                {
                    "tool": "memory_storage_tool",
                    "action": "store_analysis",
                    "parameters": {"data": "{{analysis_results}}", "tags": ["{{content_type}}", "{{platform}}"]},
                    "reasoning": "Preserve findings for future reference and learning",
                }
            )

        return sequence

    def _generate_reasoning_steps(self, agent_role: str, scenario: str, complexity: str) -> list[str]:
        """Generate reasoning steps appropriate for the agent role and scenario."""
        # Select appropriate reasoning pattern
        if "fact" in agent_role.lower() or "verify" in scenario.lower():
            pattern = "verification"
        elif "character" in agent_role.lower() or "profile" in scenario.lower():
            pattern = "investigative"
        elif "defender" in agent_role.lower() or "defend" in scenario.lower():
            pattern = "defensive"
        else:
            pattern = "analytical"

        base_steps = self.reasoning_patterns[pattern].copy()

        # Add complexity-specific reasoning
        if complexity in ["advanced", "expert"]:
            base_steps.extend(
                [
                    "Consider alternative interpretations and edge cases",
                    "Evaluate potential biases in sources and methodology",
                    "Assess broader implications and downstream effects",
                    "Plan for uncertainty and incomplete information",
                ]
            )

        # Add scenario-specific reasoning
        if "misinformation" in scenario.lower():
            base_steps.extend(
                [
                    "Identify hallmarks of misinformation patterns",
                    "Trace potential origins and spread mechanisms",
                    "Assess harm potential and urgency of response",
                ]
            )

        return base_steps

    def _generate_expected_outcome(self, scenario: str, tool_sequence: list[dict], complexity: str) -> str:
        """Generate the expected outcome description."""
        outcome_templates = {
            "basic": "Clear {analysis_type} with {confidence}% confidence, supported by {source_count} sources",
            "intermediate": "Nuanced {analysis_type} addressing multiple perspectives, {confidence}% confidence with {caveat_count} caveats noted",
            "advanced": "Comprehensive {analysis_type} with {confidence}% confidence, {source_count} sources verified, {limitation_count} limitations identified",
            "expert": "Expert-level {analysis_type} with {confidence}% confidence, {source_count} cross-verified sources, full uncertainty quantification",
        }

        template = outcome_templates.get(complexity, outcome_templates["basic"])

        # Determine analysis type from scenario
        if "fact-check" in scenario.lower():
            analysis_type = "fact-check verdict"
        elif "sentiment" in scenario.lower():
            analysis_type = "sentiment analysis"
        elif "profile" in scenario.lower():
            analysis_type = "character profile"
        else:
            analysis_type = "content analysis"

        return template.format(
            analysis_type=analysis_type,
            confidence=random.randint(75, 95) if complexity in ["advanced", "expert"] else random.randint(60, 85),
            source_count=random.randint(3, 8) if complexity in ["advanced", "expert"] else random.randint(1, 4),
            caveat_count=random.randint(1, 3),
            limitation_count=random.randint(1, 4),
        )

    def _generate_anti_patterns(self, optimal_tools: list[str], complexity: str) -> list[dict[str, str]]:
        """Generate anti-patterns (what NOT to do) for learning."""
        anti_patterns = [
            {
                "pattern": "tool_overuse",
                "description": "Using every available tool regardless of relevance",
                "why_bad": "Wastes resources and introduces noise into analysis",
            },
            {
                "pattern": "insufficient_verification",
                "description": "Accepting first source found without cross-checking",
                "why_bad": "Leads to propagation of misinformation and low-quality analysis",
            },
            {
                "pattern": "circular_reasoning",
                "description": "Using the same source to verify itself",
                "why_bad": "Creates false confidence without independent validation",
            },
            {
                "pattern": "tool_sequence_chaos",
                "description": "Using tools in random order without logical progression",
                "why_bad": "Later tools cannot benefit from earlier analysis, reducing effectiveness",
            },
            {
                "pattern": "context_blindness",
                "description": "Ignoring relevant context and focusing only on isolated claims",
                "why_bad": "Misses important nuance and can lead to misleading conclusions",
            },
        ]

        # Add complexity-specific anti-patterns
        if complexity in ["advanced", "expert"]:
            anti_patterns.extend(
                [
                    {
                        "pattern": "overconfidence_bias",
                        "description": "Claiming high confidence without sufficient evidence",
                        "why_bad": "Misleads users about the reliability of analysis",
                    },
                    {
                        "pattern": "analysis_paralysis",
                        "description": "Getting stuck in endless verification loops",
                        "why_bad": "Prevents timely delivery of results",
                    },
                ]
            )

        return random.sample(anti_patterns, min(len(anti_patterns), 3))

    def _calculate_quality_score(self, tool_sequence: list[dict], reasoning_steps: list[str], complexity: str) -> float:
        """Calculate a quality score for the training example."""
        base_score = 0.7

        # Tool sequence quality
        if len(tool_sequence) >= 3:
            base_score += 0.1
        if any("reasoning" in step for step in tool_sequence):
            base_score += 0.1

        # Reasoning quality
        if len(reasoning_steps) >= 5:
            base_score += 0.1

        # Complexity bonus
        complexity_bonuses = {"basic": 0.0, "intermediate": 0.05, "advanced": 0.1, "expert": 0.15}
        base_score += complexity_bonuses.get(complexity, 0.0)

        return min(base_score, 1.0)

    def save_training_data(self, examples: list[ToolUsageExample], output_path: Path):
        """Save generated training examples to disk."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        training_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator_version": "1.0",
                "total_examples": len(examples),
                "tools_available": self.tools_available,
            },
            "examples": [
                {
                    "scenario": ex.scenario,
                    "context": ex.context,
                    "optimal_tools": ex.optimal_tools,
                    "tool_sequence": ex.tool_sequence,
                    "reasoning_steps": ex.reasoning_steps,
                    "expected_outcome": ex.expected_outcome,
                    "anti_patterns": ex.anti_patterns,
                    "quality_score": ex.quality_score,
                }
                for ex in examples
            ],
        }

        with open(output_path, "w") as f:
            json.dump(training_data, f, indent=2)

        print(f"✅ Saved {len(examples)} training examples to {output_path}")


def generate_training_data_for_all_agents(tools_available: list[str]) -> dict[str, list[ToolUsageExample]]:
    """Generate comprehensive training data for all agent roles."""
    generator = SyntheticDataGenerator(tools_available)

    agent_roles = ["content_analysis", "fact_checking", "cross_platform_monitoring", "character_profiling"]

    all_training_data = {}

    for role in agent_roles:
        print(f"Generating training data for {role}...")
        examples = generator.generate_training_batch(role, batch_size=100)
        all_training_data[role] = examples

        # Save individual agent training data
        output_path = Path(f"data/agent_training/{role}_synthetic_training.json")
        generator.save_training_data(examples, output_path)

    return all_training_data


if __name__ == "__main__":
    # Example usage
    available_tools = [
        "pipeline_tool",
        "fact_check_tool",
        "fallacy_tool",
        "vector_tool",
        "claim_extractor_tool",
        "context_verification_tool",
        "memory_storage_tool",
        "multi_platform_monitor_tool",
        "social_media_monitor_tool",
        "sentiment_tool",
        "character_profile_tool",
        "truth_scoring_tool",
        "timeline_tool",
        "steelman_argument_tool",
        "perspective_synthesizer_tool",
        "debate_tool",
    ]

    all_data = generate_training_data_for_all_agents(available_tools)
    print(f"Generated training data for {len(all_data)} agent roles")
