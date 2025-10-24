"""
CrewAI agent for the Repurposing Studio.
Handles intelligent clip selection and platform optimization.
"""

import logging

from crewai import Agent, Task  # type: ignore[import-not-found]

from ultimate_discord_intelligence_bot.creator_ops.features.repurposing_models import (
    ClipCandidate,
    PlatformType,
    RepurposingConfig,
)
from ultimate_discord_intelligence_bot.creator_ops.features.repurposing_studio import (
    RepurposingStudio,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class RepurposingAgent:
    """CrewAI agent for intelligent repurposing decisions."""

    def __init__(self, repurposing_studio: RepurposingStudio):
        self.repurposing_studio = repurposing_studio
        self.agent = self._create_agent()

    def _create_agent(self) -> Agent:
        """Create the CrewAI agent for repurposing."""
        return Agent(
            role="Content Repurposing Specialist",
            goal="Transform long-form content into engaging, platform-optimized shorts that maximize reach and engagement",
            backstory="""You are an expert content strategist with deep knowledge of social media algorithms
            and platform-specific best practices. You specialize in identifying the most engaging moments
            from long-form content and repurposing them into viral-worthy shorts. You understand the unique
            characteristics of each platform and know how to optimize content for maximum impact.""",
            verbose=True,
            allow_delegation=False,
            tools=[],  # Add tools as needed
        )

    async def analyze_content_for_repurposing(
        self,
        episode_title: str,
        transcript_text: str,
        target_platforms: list[PlatformType],
        config: RepurposingConfig | None = None,
    ) -> StepResult:
        """
        Analyze content and provide repurposing recommendations.

        Args:
            episode_title: Title of the episode
            transcript_text: Full transcript text
            target_platforms: List of target platforms
            config: Repurposing configuration

        Returns:
            StepResult with analysis and recommendations
        """
        try:
            # Create analysis task
            task = Task(
                description=f"""
                Analyze the following content for repurposing opportunities:

                Episode Title: {episode_title}
                Target Platforms: {[p.value for p in target_platforms]}
                Transcript: {transcript_text[:2000]}...

                Provide:
                1. Key themes and topics
                2. Most engaging segments
                3. Platform-specific optimization recommendations
                4. Viral potential assessment
                5. Content strategy suggestions
                """,
                agent=self.agent,
                expected_output="""Detailed analysis including:
                - Key themes and topics identified
                - Top 5 most engaging segments with timestamps
                - Platform-specific optimization recommendations
                - Viral potential assessment (1-10 scale)
                - Content strategy suggestions for each platform""",
            )

            # Execute task
            result = await self.agent.execute_task(task)

            # Parse and structure the result
            analysis = self._parse_analysis_result(result)

            return StepResult.ok(
                data={
                    "analysis": analysis,
                    "recommendations": self._generate_recommendations(analysis, target_platforms),
                    "viral_potential": analysis.get("viral_potential", 5),
                    "platform_optimizations": analysis.get("platform_optimizations", {}),
                }
            )

        except Exception as e:
            logger.error(f"Content analysis failed: {e!s}")
            return StepResult.fail(f"Content analysis failed: {e!s}")

    def _parse_analysis_result(self, result: str) -> dict:
        """Parse the agent's analysis result into structured data."""
        analysis = {
            "themes": [],
            "engaging_segments": [],
            "platform_optimizations": {},
            "viral_potential": 5,
            "strategy_suggestions": [],
        }

        # Simple parsing - in production, you'd want more sophisticated parsing
        lines = result.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if "themes" in line.lower() or "topics" in line.lower():
                current_section = "themes"
            elif "engaging" in line.lower() or "segments" in line.lower():
                current_section = "engaging_segments"
            elif "platform" in line.lower() or "optimization" in line.lower():
                current_section = "platform_optimizations"
            elif "viral" in line.lower() or "potential" in line.lower():
                current_section = "viral_potential"
            elif "strategy" in line.lower() or "suggestions" in line.lower():
                current_section = "strategy_suggestions"
            else:
                if current_section == "themes":
                    analysis["themes"].append(line)
                elif current_section == "engaging_segments":
                    analysis["engaging_segments"].append(line)
                elif current_section == "platform_optimizations":
                    analysis["platform_optimizations"][line] = line
                elif current_section == "viral_potential":
                    # Extract numeric value
                    import re

                    numbers = re.findall(r"\d+", line)
                    if numbers:
                        analysis["viral_potential"] = int(numbers[0])
                elif current_section == "strategy_suggestions":
                    analysis["strategy_suggestions"].append(line)

        return analysis

    def _generate_recommendations(self, analysis: dict, target_platforms: list[PlatformType]) -> dict[str, list[str]]:
        """Generate platform-specific recommendations."""
        recommendations = {}

        for platform in target_platforms:
            platform_recs = []

            if platform == PlatformType.YOUTUBE_SHORTS:
                platform_recs.extend(
                    [
                        "Keep clips under 60 seconds for maximum engagement",
                        "Use trending audio and music",
                        "Add captions for accessibility",
                        "Post during peak hours (6-9 PM)",
                        "Use #shorts hashtag for algorithm boost",
                    ]
                )
            elif platform == PlatformType.TIKTOK:
                platform_recs.extend(
                    [
                        "Keep clips under 60 seconds",
                        "Use trending hashtags (#fyp, #viral)",
                        "Post during peak hours (6-9 PM)",
                        "Use trending audio",
                        "Engage with comments quickly",
                    ]
                )
            elif platform == PlatformType.INSTAGRAM_REELS:
                platform_recs.extend(
                    [
                        "Keep clips under 90 seconds",
                        "Use trending audio and music",
                        "Post during peak hours (6-9 PM)",
                        "Use #reels hashtag",
                        "Cross-post to Stories",
                    ]
                )
            elif platform == PlatformType.X:
                platform_recs.extend(
                    [
                        "Keep clips under 2 minutes",
                        "Use trending hashtags",
                        "Post during peak hours (9-11 AM, 1-3 PM)",
                        "Add compelling captions",
                        "Engage with replies",
                    ]
                )

            # Add analysis-based recommendations
            if analysis.get("viral_potential", 5) > 7:
                platform_recs.append("High viral potential - consider boosting/promoting")

            if analysis.get("themes"):
                platform_recs.append(f"Focus on themes: {', '.join(analysis['themes'][:3])}")

            recommendations[platform.value] = platform_recs

        return recommendations

    async def optimize_clip_selection(
        self,
        candidates: list[ClipCandidate],
        target_platforms: list[PlatformType],
        max_clips: int = 5,
    ) -> StepResult:
        """
        Use AI to optimize clip selection for maximum impact.

        Args:
            candidates: List of clip candidates
            target_platforms: Target platforms
            max_clips: Maximum number of clips to select

        Returns:
            StepResult with optimized clip selection
        """
        try:
            # Create optimization task
            task = Task(
                description=f"""
                Optimize clip selection from {len(candidates)} candidates for {len(target_platforms)} platforms.

                Candidates:
                {self._format_candidates_for_agent(candidates)}

                Target Platforms: {[p.value for p in target_platforms]}
                Max Clips: {max_clips}

                Select the best clips that will:
                1. Maximize engagement across all platforms
                2. Provide variety in content
                3. Cover different themes/topics
                4. Have high viral potential
                5. Work well for each platform's format
                """,
                agent=self.agent,
                expected_output=f"""Optimized clip selection with:
                - Top {max_clips} clips selected
                - Reasoning for each selection
                - Platform-specific optimization notes
                - Expected performance metrics""",
            )

            # Execute task
            result = await self.agent.execute_task(task)

            # Parse result and select clips
            selected_clips = self._parse_clip_selection(result, candidates, max_clips)

            return StepResult.ok(
                data={
                    "selected_clips": selected_clips,
                    "selection_reasoning": result,
                    "optimization_notes": self._extract_optimization_notes(result),
                }
            )

        except Exception as e:
            logger.error(f"Clip optimization failed: {e!s}")
            return StepResult.fail(f"Clip optimization failed: {e!s}")

    def _format_candidates_for_agent(self, candidates: list[ClipCandidate]) -> str:
        """Format candidates for agent analysis."""
        formatted = []
        for i, candidate in enumerate(candidates):
            formatted.append(f"""
            Candidate {i + 1}:
            - Duration: {candidate.duration:.1f}s
            - Content: {candidate.transcript_segment[:200]}...
            - Speakers: {", ".join(candidate.speakers)}
            - Topics: {", ".join(candidate.topics)}
            - Engagement Score: {candidate.engagement_score:.2f}
            - Viral Potential: {candidate.viral_potential:.2f}
            - Reason: {candidate.reason}
            """)
        return "\n".join(formatted)

    def _parse_clip_selection(
        self, result: str, candidates: list[ClipCandidate], max_clips: int
    ) -> list[ClipCandidate]:
        """Parse the agent's clip selection result."""

        # Simple selection logic - in production, you'd want more sophisticated parsing
        # For now, select top candidates by combined score
        sorted_candidates = sorted(
            candidates,
            key=lambda c: c.engagement_score + c.viral_potential,
            reverse=True,
        )

        return sorted_candidates[:max_clips]

    def _extract_optimization_notes(self, result: str) -> dict[str, str]:
        """Extract optimization notes from agent result."""
        notes = {}

        # Simple extraction - in production, you'd want more sophisticated parsing
        lines = result.split("\n")
        current_platform = None

        for line in lines:
            line = line.strip()
            if any(platform in line.lower() for platform in ["youtube", "tiktok", "instagram", "x", "twitter"]):
                current_platform = line
            elif current_platform and line:
                notes[current_platform] = line

        return notes

    async def generate_content_strategy(
        self,
        episode_title: str,
        target_platforms: list[PlatformType],
        clips_created: int,
    ) -> StepResult:
        """
        Generate a comprehensive content strategy for repurposed content.

        Args:
            episode_title: Title of the episode
            target_platforms: Target platforms
            clips_created: Number of clips created

        Returns:
            StepResult with content strategy
        """
        try:
            # Create strategy task
            task = Task(
                description=f"""
                Generate a comprehensive content strategy for repurposed content:

                Episode: {episode_title}
                Clips Created: {clips_created}
                Target Platforms: {[p.value for p in target_platforms]}

                Provide:
                1. Posting schedule recommendations
                2. Cross-platform promotion strategy
                3. Engagement tactics
                4. Performance tracking suggestions
                5. Content calendar ideas
                """,
                agent=self.agent,
                expected_output="""Comprehensive content strategy including:
                - Optimal posting schedule for each platform
                - Cross-platform promotion tactics
                - Engagement strategies
                - Performance metrics to track
                - Content calendar recommendations""",
            )

            # Execute task
            result = await self.agent.execute_task(task)

            # Parse and structure the strategy
            strategy = self._parse_strategy_result(result)

            return StepResult.ok(
                data={
                    "strategy": strategy,
                    "posting_schedule": strategy.get("posting_schedule", {}),
                    "promotion_tactics": strategy.get("promotion_tactics", []),
                    "engagement_strategies": strategy.get("engagement_strategies", []),
                    "performance_metrics": strategy.get("performance_metrics", []),
                    "content_calendar": strategy.get("content_calendar", []),
                }
            )

        except Exception as e:
            logger.error(f"Strategy generation failed: {e!s}")
            return StepResult.fail(f"Strategy generation failed: {e!s}")

    def _parse_strategy_result(self, result: str) -> dict:
        """Parse the agent's strategy result into structured data."""
        strategy = {
            "posting_schedule": {},
            "promotion_tactics": [],
            "engagement_strategies": [],
            "performance_metrics": [],
            "content_calendar": [],
        }

        # Simple parsing - in production, you'd want more sophisticated parsing
        lines = result.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if "posting" in line.lower() or "schedule" in line.lower():
                current_section = "posting_schedule"
            elif "promotion" in line.lower() or "cross-platform" in line.lower():
                current_section = "promotion_tactics"
            elif "engagement" in line.lower():
                current_section = "engagement_strategies"
            elif "performance" in line.lower() or "metrics" in line.lower():
                current_section = "performance_metrics"
            elif "calendar" in line.lower():
                current_section = "content_calendar"
            else:
                if current_section == "posting_schedule":
                    strategy["posting_schedule"][line] = line
                elif current_section == "promotion_tactics":
                    strategy["promotion_tactics"].append(line)
                elif current_section == "engagement_strategies":
                    strategy["engagement_strategies"].append(line)
                elif current_section == "performance_metrics":
                    strategy["performance_metrics"].append(line)
                elif current_section == "content_calendar":
                    strategy["content_calendar"].append(line)

        return strategy
