#!/usr/bin/env python3
"""
Agent Training Coordinator for CrewAI Agents

Enhances existing CrewAI agents with improved prompting, tool usage training,
and autonomous reasoning capabilities using synthetic training data.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from core.time import default_utc_now  # type: ignore[import-not-found]

from .synthetic_data_generator import SyntheticDataGenerator, ToolUsageExample


@dataclass
class AgentEnhancement:
    """Configuration for enhancing an existing agent."""

    agent_name: str
    current_config: dict[str, Any]
    enhanced_backstory: str
    tool_usage_guidelines: list[str]
    reasoning_framework: dict[str, Any]
    performance_metrics: dict[str, Any]
    training_examples: list[ToolUsageExample]


class AgentTrainingCoordinator:
    """Coordinates training and enhancement of CrewAI agents."""

    def __init__(self, agents_config_path: Path, tasks_config_path: Path):
        self.agents_config_path = agents_config_path
        self.tasks_config_path = tasks_config_path
        self.logger = logging.getLogger(__name__)

        # Load current configurations
        self.agents_config = self._load_yaml_config(agents_config_path)
        self.tasks_config = self._load_yaml_config(tasks_config_path)

        # Available tools mapping (from your project)
        self.available_tools = [
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
            "youtube_tool",
            "transcript_index_tool",
            "twitch_download_tool",
            "audio_transcription_tool",
            "trustworthiness_tracker_tool",
            "multi_platform_download_tool",
            "x_monitor_tool",
            "reddit_monitor_tool",
            "tiktok_monitor_tool",
            "instagram_monitor_tool",
            "telegram_monitor_tool",
            "discord_monitor_tool",
            "link_scraper_tool",
            "archive_tool",
            "search_engine_tool",
            "news_api_tool",
            "web_search_tool",
            "screenshot_tool",
            "video_download_tool",
            "audio_extraction_tool",
            "transcript_generation_tool",
            "content_analysis_tool",
            "sentiment_analysis_tool",
            "topic_modeling_tool",
            "named_entity_recognition_tool",
            "keyword_extraction_tool",
            "language_detection_tool",
            "text_classification_tool",
            "summarization_tool",
        ]

        self.training_generator = SyntheticDataGenerator(self.available_tools)

    def _load_yaml_config(self, config_path: Path) -> dict:
        """Load YAML configuration file."""
        with open(config_path) as f:
            return yaml.safe_load(f)

    def _save_yaml_config(self, config: dict, config_path: Path):
        """Save YAML configuration file."""
        with open(config_path, "w") as f:
            yaml.dump(config, f, indent=2, default_flow_style=False)

    def analyze_current_agents(self) -> dict[str, dict]:
        """Analyze current agent configurations and identify enhancement opportunities."""
        analysis = {}

        for agent_name, agent_config in self.agents_config.items():
            agent_analysis: dict[str, Any] = {
                "agent_name": agent_name,
                "configuration": {
                    "role": agent_config.get("role", ""),
                    "goal": agent_config.get("goal", ""),
                    "backstory": agent_config.get("backstory", ""),
                    "has_tools": len(agent_config.get("tools", [])) > 0,
                    "has_reasoning": agent_config.get("reasoning", False),
                    "has_memory": agent_config.get("memory", False),
                    "verbose": agent_config.get("verbose", False),
                    "allow_delegation": agent_config.get("allow_delegation", False),
                },
                "enhancement_opportunities": [],
                "tool_usage_potential": "unknown",
                "complexity_level": "basic",
            }

            # Analyze backstory for complexity
            backstory = agent_config.get("backstory", "")
            if len(backstory) > 500:
                agent_analysis["complexity_level"] = "advanced"
            elif len(backstory) > 200:
                agent_analysis["complexity_level"] = "intermediate"

            # Identify enhancement opportunities
            if not agent_config.get("reasoning", False):
                agent_analysis["enhancement_opportunities"].append("enable_reasoning")

            if not agent_config.get("memory", False):
                agent_analysis["enhancement_opportunities"].append("enable_memory")

            if "tool" not in backstory.lower() and "analysis" in backstory.lower():
                agent_analysis["enhancement_opportunities"].append("add_tool_usage_training")
                agent_analysis["tool_usage_potential"] = "high"

            # Determine agent role for training
            role = agent_config.get("role", "").lower()
            if "fact" in role or "truth" in role:
                agent_analysis["primary_function"] = "fact_checking"
            elif "intelligence" in role or "monitor" in role:
                agent_analysis["primary_function"] = "cross_platform_monitoring"
            elif "character" in role or "profile" in role:
                agent_analysis["primary_function"] = "character_profiling"
            else:
                agent_analysis["primary_function"] = "content_analysis"

            analysis[agent_name] = agent_analysis

        return analysis

    def generate_enhanced_prompts(
        self,
        agent_name: str,
        current_config: dict,
        training_examples: list[ToolUsageExample],
    ) -> dict[str, str]:
        """Generate enhanced prompts based on training examples."""

        # Extract patterns from training examples
        common_tools = []
        reasoning_patterns = []
        quality_patterns = []

        for example in training_examples[:10]:  # Use top 10 examples
            common_tools.extend(example.optimal_tools)
            reasoning_patterns.extend(example.reasoning_steps[:3])  # Top 3 reasoning steps
            if example.quality_score > 0.8:
                quality_patterns.append(example.expected_outcome)

        # Count tool usage frequency
        tool_frequency: dict[str, int] = {}
        for tool in common_tools:
            tool_frequency[tool] = tool_frequency.get(tool, 0) + 1

        top_tools = sorted(tool_frequency.items(), key=lambda x: x[1], reverse=True)[:5]

        # Enhanced backstory
        current_backstory = current_config.get("backstory", "")
        enhanced_backstory = f"""{current_backstory}

ENHANCED CAPABILITIES & TOOL USAGE TRAINING:

You are equipped with {len(self.available_tools)} sophisticated analysis tools. Your primary toolkit includes:
{", ".join([tool for tool, _ in top_tools])}.

TOOL USAGE PRINCIPLES:
1. ALWAYS consider which tools are most appropriate for each specific task
2. Use tools in logical sequence - gather data first, then analyze, then synthesize
3. Cross-verify findings using multiple tools when possible
4. Document your reasoning for tool selection in your responses

REASONING FRAMEWORK:
{chr(10).join([f"- {pattern}" for pattern in reasoning_patterns[:5]])}

QUALITY STANDARDS:
- Aim for high-confidence analysis backed by multiple sources
- Clearly distinguish between verified facts and informed speculation
- Provide uncertainty quantification when evidence is limited
- Always include relevant context and limitations in your analysis

AUTONOMOUS DECISION-MAKING:
- Proactively identify when additional tools could enhance your analysis
- Suggest alternative approaches when initial methods seem insufficient
- Continuously improve your tool selection based on task outcomes
"""

        # Enhanced goal
        current_goal = current_config.get("goal", "")
        enhanced_goal = f"""{current_goal}

ENHANCED OPERATIONAL OBJECTIVES:
- Maximize analytical accuracy through strategic tool utilization
- Provide comprehensive, multi-perspective analysis using appropriate tool sequences
- Maintain transparency about methodology and confidence levels
- Continuously refine approach based on task complexity and available evidence"""

        # Tool usage guidelines
        tool_guidelines = f"""TOOL SELECTION GUIDELINES for {agent_name.upper()}:

PRIMARY ANALYSIS TOOLS:
{chr(10).join([f"- {tool}: Use when {self._get_tool_usage_context(tool)}" for tool, _ in top_tools[:3]])}

VERIFICATION WORKFLOW:
1. Extract key claims using claim_extractor_tool
2. Verify facts using fact_check_tool with multiple sources
3. Cross-reference with vector_tool for historical context
4. Store findings using memory_storage_tool for future reference

QUALITY ASSURANCE:
- Use multiple independent sources for verification
- Apply fallacy_tool to identify logical errors
- Employ steelman_argument_tool for balanced analysis
- Document uncertainty and limitations clearly"""

        return {
            "enhanced_backstory": enhanced_backstory,
            "enhanced_goal": enhanced_goal,
            "tool_guidelines": tool_guidelines,
        }

    def _get_tool_usage_context(self, tool_name: str) -> str:
        """Get appropriate usage context for a tool."""
        tool_contexts = {
            "pipeline_tool": "comprehensive video/audio content analysis",
            "fact_check_tool": "verifying specific factual claims",
            "fallacy_tool": "identifying logical errors in arguments",
            "vector_tool": "finding related content and context",
            "claim_extractor_tool": "isolating testable factual statements",
            "context_verification_tool": "validating source authenticity",
            "memory_storage_tool": "preserving analysis for future reference",
            "sentiment_tool": "analyzing emotional tone and public opinion",
            "character_profile_tool": "building comprehensive personality assessments",
            "truth_scoring_tool": "quantifying credibility and trustworthiness",
            "steelman_argument_tool": "presenting strongest version of arguments",
            "debate_tool": "structured argumentation and counter-analysis",
        }
        return tool_contexts.get(tool_name, "specialized analysis tasks")

    def create_reasoning_framework(self, agent_role: str) -> dict[str, Any]:
        """Create enhanced reasoning framework for agent."""
        base_framework = {
            "reasoning_enabled": True,
            "reasoning_style": "analytical",
            "confidence_threshold": 0.75,
            "verification_requirements": "multiple_sources",
            "uncertainty_handling": "explicit_quantification",
        }

        # Role-specific enhancements
        if "fact" in agent_role.lower():
            base_framework.update(
                {
                    "reasoning_style": "verification_focused",
                    "confidence_threshold": 0.85,
                    "verification_requirements": "authoritative_sources",
                    "bias_detection": True,
                    "source_credibility_assessment": True,
                }
            )
        elif "intelligence" in agent_role.lower():
            base_framework.update(
                {
                    "reasoning_style": "investigative",
                    "pattern_recognition": True,
                    "cross_platform_correlation": True,
                    "temporal_analysis": True,
                }
            )
        elif "character" in agent_role.lower():
            base_framework.update(
                {
                    "reasoning_style": "psychological_analytical",
                    "longitudinal_tracking": True,
                    "behavioral_pattern_analysis": True,
                    "consistency_evaluation": True,
                }
            )
        elif "defender" in agent_role.lower():
            base_framework.update(
                {
                    "reasoning_style": "defensive_analytical",
                    "argument_strengthening": True,
                    "counter_argument_anticipation": True,
                    "evidence_prioritization": True,
                }
            )

        return base_framework

    def enhance_agent(self, agent_name: str) -> AgentEnhancement:
        """Create complete enhancement package for an agent."""
        current_config = self.agents_config.get(agent_name, {})
        agent_role = current_config.get("role", "")

        # Determine training focus based on agent role
        if "fact" in agent_role.lower() or "truth" in agent_role.lower():
            training_focus = "fact_checking"
        elif "intelligence" in agent_role.lower() or "monitor" in agent_role.lower():
            training_focus = "cross_platform_monitoring"
        elif "character" in agent_role.lower() or "profile" in agent_role.lower():
            training_focus = "character_profiling"
        else:
            training_focus = "content_analysis"

        # Generate training examples
        training_examples = self.training_generator.generate_training_batch(
            agent_role=training_focus,
            batch_size=50,
            complexity_distribution={
                "basic": 0.2,
                "intermediate": 0.3,
                "advanced": 0.3,
                "expert": 0.2,
            },
        )

        # Generate enhanced prompts
        enhanced_prompts = self.generate_enhanced_prompts(agent_name, current_config, training_examples)

        # Create reasoning framework
        reasoning_framework = self.create_reasoning_framework(agent_role)

        # Define performance metrics
        performance_metrics = {
            "accuracy_target": 0.90,
            "tool_usage_efficiency": 0.85,
            "response_completeness": 0.80,
            "reasoning_quality": 0.85,
            "source_verification_rate": 0.95,
        }

        # Tool usage guidelines
        tool_guidelines = [
            "Always identify the most appropriate tools for each specific analysis task",
            "Use tools in logical sequence to build comprehensive understanding",
            "Cross-verify important findings using multiple independent tools",
            "Document tool selection reasoning in your analysis",
            "Continuously evaluate tool effectiveness and adjust approach",
            "Leverage memory tools to build knowledge over time",
            "Apply quality checks and uncertainty quantification to all findings",
        ]

        return AgentEnhancement(
            agent_name=agent_name,
            current_config=current_config,
            enhanced_backstory=enhanced_prompts["enhanced_backstory"],
            tool_usage_guidelines=tool_guidelines,
            reasoning_framework=reasoning_framework,
            performance_metrics=performance_metrics,
            training_examples=training_examples,
        )

    def apply_enhancements(self, enhancement: AgentEnhancement, backup: bool = True) -> bool:
        """Apply enhancements to agent configuration."""
        try:
            if backup:
                # Create backup of current config
                backup_path = self.agents_config_path.with_suffix(".backup.yaml")
                self._save_yaml_config(self.agents_config, backup_path)
                self.logger.info(f"Created backup at {backup_path}")

            # Update agent configuration
            agent_config = self.agents_config[enhancement.agent_name]

            # Apply enhancements
            agent_config["backstory"] = enhancement.enhanced_backstory
            agent_config["reasoning"] = enhancement.reasoning_framework.get("reasoning_enabled", True)
            agent_config["memory"] = True  # Enable memory for all enhanced agents
            agent_config["verbose"] = True  # Enable verbose for better debugging

            # Add tool usage metadata
            agent_config["tool_guidelines"] = enhancement.tool_usage_guidelines
            agent_config["performance_metrics"] = enhancement.performance_metrics
            agent_config["reasoning_framework"] = enhancement.reasoning_framework
            agent_config["enhanced_at"] = default_utc_now().isoformat()

            # Save updated configuration
            self._save_yaml_config(self.agents_config, self.agents_config_path)

            # Save training examples
            training_path = Path(f"data/agent_training/{enhancement.agent_name}_training_examples.json")
            training_path.parent.mkdir(parents=True, exist_ok=True)

            training_data = {
                "agent_name": enhancement.agent_name,
                "enhanced_at": default_utc_now().isoformat(),
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
                    for ex in enhancement.training_examples
                ],
            }

            with open(training_path, "w") as f:
                json.dump(training_data, f, indent=2)

            self.logger.info(f"✅ Successfully enhanced agent {enhancement.agent_name}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to enhance agent {enhancement.agent_name}: {e}")
            return False

    def enhance_all_agents(self) -> dict[str, bool]:
        """Enhance all agents in the configuration."""
        results = {}

        for agent_name in self.agents_config:
            self.logger.info(f"Enhancing agent: {agent_name}")

            try:
                enhancement = self.enhance_agent(agent_name)
                success = self.apply_enhancements(enhancement)
                results[agent_name] = success

                if success:
                    self.logger.info(
                        f"✅ Enhanced {agent_name} - Training examples: {len(enhancement.training_examples)}"
                    )
                else:
                    self.logger.error(f"❌ Failed to enhance {agent_name}")

            except Exception as e:
                self.logger.error(f"❌ Error enhancing {agent_name}: {e}")
                results[agent_name] = False

        return results

    def generate_enhancement_report(self, results: dict[str, bool]) -> str:
        """Generate a comprehensive report of enhancements applied."""
        successful = sum(1 for success in results.values() if success)
        total = len(results)

        report = f"""
# CrewAI Agent Enhancement Report
Generated: {default_utc_now().isoformat()}

## Summary
- **Total Agents**: {total}
- **Successfully Enhanced**: {successful}
- **Enhancement Rate**: {(successful / total) * 100:.1f}%

## Enhanced Agents
"""

        for agent_name, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            report += f"- **{agent_name}**: {status}\n"

        report += f"""
## Enhancement Details
Each successfully enhanced agent now includes:
- **Enhanced Backstory**: Comprehensive tool usage training and reasoning frameworks
- **Tool Usage Guidelines**: 7 core principles for optimal tool selection and usage
- **Reasoning Framework**: Role-specific analytical approaches and quality standards
- **Performance Metrics**: Target benchmarks for accuracy, efficiency, and completeness
- **Training Examples**: 50 synthetic training examples with complexity distribution
- **Memory & Reasoning**: Enabled advanced capabilities for autonomous decision-making

## Training Data Generated
- **Synthetic Examples**: {successful * 50} total training examples
- **Complexity Levels**: Basic (20%), Intermediate (30%), Advanced (30%), Expert (20%)
- **Tool Coverage**: {len(self.available_tools)} available tools with usage patterns
- **Quality Assurance**: Anti-pattern identification and quality scoring

## Next Steps
1. Monitor agent performance using new metrics
2. Analyze tool usage patterns in real deployments
3. Refine training based on actual outcomes
4. Expand synthetic training data based on edge cases discovered
"""

        return report


def main():
    """Main function to enhance all CrewAI agents."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize coordinator
    agents_config_path = Path("/home/crew/src/ultimate_discord_intelligence_bot/config/agents.yaml")
    tasks_config_path = Path("/home/crew/src/ultimate_discord_intelligence_bot/config/tasks.yaml")

    coordinator = AgentTrainingCoordinator(agents_config_path, tasks_config_path)

    # Enhance all agents
    print("🚀 Starting CrewAI Agent Enhancement Process...")
    results = coordinator.enhance_all_agents()

    # Generate and save report
    report = coordinator.generate_enhancement_report(results)
    report_path = Path("reports/agent_enhancement_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        f.write(report)

    print("\n📊 Enhancement Complete!")
    print(f"📝 Report saved to: {report_path}")
    print(f"✅ Successfully enhanced: {sum(results.values())}/{len(results)} agents")


if __name__ == "__main__":
    main()
