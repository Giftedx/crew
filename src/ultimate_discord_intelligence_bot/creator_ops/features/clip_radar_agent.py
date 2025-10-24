"""
CrewAI agent for Live Clip Radar viral moment detection and clip generation.
Provides intelligent analysis and optimization for viral moment detection.
"""

import logging
from datetime import datetime

from crewai import Agent, Crew, Task  # type: ignore[import-not-found]
from pydantic import BaseModel

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.features.clip_radar_models import (
    ClipCandidate,
    ClipStatus,
    MonitoringConfig,
    ViralMoment,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class ViralMomentAnalysis(BaseModel):
    """Analysis result for viral moment detection."""

    moment_quality_score: float  # 0.0 to 1.0
    viral_potential: float  # 0.0 to 1.0
    engagement_prediction: dict[str, float]
    optimization_suggestions: list[str]
    clip_recommendations: list[str]
    risk_assessment: str
    target_audience: list[str]


class ClipOptimization(BaseModel):
    """Clip optimization recommendations."""

    title_optimization: str
    description_optimization: str
    timing_optimization: dict[str, float]
    platform_specific_hooks: dict[str, str]
    hashtag_recommendations: list[str]
    thumbnail_suggestions: list[str]
    engagement_strategies: list[str]


class LiveClipRadarAgent:
    """CrewAI agent for Live Clip Radar analysis and optimization."""

    def __init__(self, config: CreatorOpsConfig):
        self.config = config
        self.llm = self._get_llm()
        self.agents = self._create_agents()
        self.tasks = self._create_tasks()
        self.crew = self._create_crew()

    def _get_llm(self):
        """Get configured LLM for agent."""
        # Use OpenRouter or OpenAI based on configuration
        if hasattr(self.config, "openrouter_api_key") and self.config.openrouter_api_key:
            from langchain_openai import ChatOpenAI  # type: ignore[import-not-found]

            return ChatOpenAI(
                model="anthropic/claude-3-sonnet",
                api_key=self.config.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            )
        else:
            from langchain_openai import ChatOpenAI  # type: ignore[import-not-found]

            return ChatOpenAI(model="gpt-4", api_key=self.config.openai_api_key)

    def _create_agents(self) -> dict[str, Agent]:
        """Create specialized agents for viral moment analysis."""
        agents = {}

        # Viral Moment Analyst Agent
        agents["viral_analyst"] = Agent(
            role="Viral Moment Analyst",
            goal="Analyze viral moments for quality, potential, and optimization opportunities",
            backstory="""You are an expert in viral content analysis with deep understanding of what makes content go viral across different platforms.
            You specialize in identifying high-potential moments, predicting engagement, and optimizing content for maximum reach.
            You understand audience psychology, platform algorithms, and viral content patterns.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

        # Clip Optimization Agent
        agents["clip_optimizer"] = Agent(
            role="Clip Optimization Specialist",
            goal="Optimize clip candidates for maximum engagement and viral potential",
            backstory="""You are a clip optimization expert who understands how to make content perform better on different platforms.
            You know about platform-specific requirements, optimal timing, hooks, and engagement strategies.
            You help creators maximize the potential of their viral moments.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

        # Engagement Prediction Agent
        agents["engagement_predictor"] = Agent(
            role="Engagement Prediction Specialist",
            goal="Predict audience engagement and viral potential for clip candidates",
            backstory="""You are an engagement prediction expert with deep knowledge of audience behavior and viral content patterns.
            You analyze content characteristics, audience demographics, and platform trends to predict performance.
            You help creators understand what content will resonate with their audience.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

        # Platform Strategy Agent
        agents["platform_strategist"] = Agent(
            role="Platform Strategy Specialist",
            goal="Develop platform-specific strategies for clip distribution and optimization",
            backstory="""You are a platform strategy expert who understands the unique characteristics and requirements of each social media platform.
            You know about platform algorithms, audience preferences, and optimization strategies for YouTube, TikTok, Instagram, and Twitter.
            You help creators adapt content for maximum impact on each platform.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

        return agents

    def _create_tasks(self) -> dict[str, Task]:
        """Create tasks for viral moment analysis."""
        tasks = {}

        # Viral Moment Analysis Task
        tasks["viral_analysis"] = Task(
            description="""
            Analyze the viral moment and provide insights on:
            1. Moment quality and authenticity
            2. Viral potential and likelihood
            3. Audience engagement predictions
            4. Optimization opportunities
            5. Risk assessment and considerations

            Provide specific, actionable insights that help creators understand and optimize their viral moments.
            """,
            agent=self.agents["viral_analyst"],
            expected_output="Comprehensive viral moment analysis with quality scores and optimization recommendations",
        )

        # Clip Optimization Task
        tasks["clip_optimization"] = Task(
            description="""
            Optimize the clip candidate for maximum engagement:
            1. Title optimization for different platforms
            2. Description and hook optimization
            3. Timing and pacing recommendations
            4. Platform-specific adaptations
            5. Hashtag and metadata optimization

            Provide specific optimization strategies for each platform.
            """,
            agent=self.agents["clip_optimizer"],
            expected_output="Detailed clip optimization recommendations with platform-specific strategies",
        )

        # Engagement Prediction Task
        tasks["engagement_prediction"] = Task(
            description="""
            Predict audience engagement and viral potential:
            1. Engagement metrics predictions (views, likes, shares, comments)
            2. Viral potential assessment
            3. Target audience identification
            4. Performance timeline predictions
            5. Success probability analysis

            Provide data-driven predictions based on content characteristics and audience patterns.
            """,
            agent=self.agents["engagement_predictor"],
            expected_output="Engagement predictions with specific metrics and success probability",
        )

        # Platform Strategy Task
        tasks["platform_strategy"] = Task(
            description="""
            Develop platform-specific distribution strategies:
            1. YouTube optimization (SEO, thumbnails, descriptions)
            2. TikTok optimization (trends, sounds, hashtags)
            3. Instagram Reels optimization (hooks, captions, timing)
            4. Twitter/X optimization (threads, timing, engagement)
            5. Cross-platform coordination strategies

            Provide specific strategies for each platform to maximize reach and engagement.
            """,
            agent=self.agents["platform_strategist"],
            expected_output="Platform-specific strategies with actionable recommendations",
        )

        return tasks

    def _create_crew(self) -> Crew:
        """Create the viral moment analysis crew."""
        return Crew(
            agents=list(self.agents.values()),
            tasks=list(self.tasks.values()),
            verbose=True,
            memory=True,
            planning=True,
            cache=True,
            max_rpm=10,
        )

    async def analyze_viral_moment(
        self,
        viral_moment: ViralMoment,
        clip_candidate: ClipCandidate | None = None,
        monitoring_config: MonitoringConfig | None = None,
    ) -> StepResult:
        """
        Analyze a viral moment using CrewAI agents.

        Args:
            viral_moment: Detected viral moment
            clip_candidate: Optional clip candidate
            monitoring_config: Optional monitoring configuration

        Returns:
            StepResult with analysis results
        """
        try:
            logger.info(f"Starting viral moment analysis for {viral_moment.moment_id}")

            # Prepare inputs for agents
            inputs = {
                "viral_moment": viral_moment,
                "clip_candidate": clip_candidate,
                "monitoring_config": monitoring_config,
                "platform": viral_moment.platform.value,
                "moment_type": viral_moment.moment_type.value,
                "confidence": viral_moment.confidence,
                "description": viral_moment.description,
                "trigger_message": viral_moment.trigger_message.message if viral_moment.trigger_message else "",
                "context_messages": [msg.message for msg in viral_moment.context_messages],
                "metrics": viral_moment.metrics,
            }

            # Execute crew analysis
            result = self.crew.kickoff(inputs=inputs)

            # Parse results
            analysis = self._parse_crew_results(result)

            # Create analysis result
            viral_analysis = ViralMomentAnalysis(
                moment_quality_score=analysis.get("quality_score", 0.7),
                viral_potential=analysis.get("viral_potential", 0.6),
                engagement_prediction=analysis.get("engagement_prediction", {}),
                optimization_suggestions=analysis.get("optimization_suggestions", []),
                clip_recommendations=analysis.get("clip_recommendations", []),
                risk_assessment=analysis.get("risk_assessment", "Low risk"),
                target_audience=analysis.get("target_audience", []),
            )

            logger.info(f"Viral moment analysis completed for {viral_moment.moment_id}")
            return StepResult.ok(data={"analysis": viral_analysis})

        except Exception as e:
            logger.error(f"Viral moment analysis failed: {e!s}")
            return StepResult.fail(f"Viral moment analysis failed: {e!s}")

    async def optimize_clip_candidate(
        self,
        clip_candidate: ClipCandidate,
        viral_analysis: ViralMomentAnalysis | None = None,
    ) -> StepResult:
        """
        Optimize a clip candidate using CrewAI agents.

        Args:
            clip_candidate: Clip candidate to optimize
            viral_analysis: Optional viral moment analysis

        Returns:
            StepResult with optimization results
        """
        try:
            logger.info(f"Starting clip optimization for {clip_candidate.clip_id}")

            # Prepare inputs for agents
            inputs = {
                "clip_candidate": clip_candidate,
                "viral_analysis": viral_analysis,
                "title": clip_candidate.title,
                "description": clip_candidate.description,
                "duration": clip_candidate.duration,
                "platform": clip_candidate.platform.value,
                "viral_moment": clip_candidate.viral_moment,
                "moment_type": clip_candidate.viral_moment.moment_type.value,
                "confidence": clip_candidate.viral_moment.confidence,
            }

            # Execute crew analysis
            result = self.crew.kickoff(inputs=inputs)

            # Parse results
            optimization = self._parse_crew_results(result)

            # Create optimization result
            clip_optimization = ClipOptimization(
                title_optimization=optimization.get("title_optimization", clip_candidate.title),
                description_optimization=optimization.get("description_optimization", clip_candidate.description),
                timing_optimization=optimization.get("timing_optimization", {}),
                platform_specific_hooks=optimization.get("platform_hooks", {}),
                hashtag_recommendations=optimization.get("hashtags", []),
                thumbnail_suggestions=optimization.get("thumbnails", []),
                engagement_strategies=optimization.get("engagement_strategies", []),
            )

            logger.info(f"Clip optimization completed for {clip_candidate.clip_id}")
            return StepResult.ok(data={"optimization": clip_optimization})

        except Exception as e:
            logger.error(f"Clip optimization failed: {e!s}")
            return StepResult.fail(f"Clip optimization failed: {e!s}")

    def _parse_crew_results(self, result) -> dict:
        """Parse results from crew execution."""
        try:
            analysis = {
                "quality_score": 0.7,
                "viral_potential": 0.6,
                "engagement_prediction": {},
                "optimization_suggestions": [],
                "clip_recommendations": [],
                "risk_assessment": "Low risk",
                "target_audience": [],
                "title_optimization": "",
                "description_optimization": "",
                "timing_optimization": {},
                "platform_hooks": {},
                "hashtags": [],
                "thumbnails": [],
                "engagement_strategies": [],
            }

            # Parse viral analysis
            if "viral_analysis" in result:
                analysis.update(self._extract_viral_insights(result["viral_analysis"]))

            # Parse clip optimization
            if "clip_optimization" in result:
                analysis.update(self._extract_optimization_insights(result["clip_optimization"]))

            # Parse engagement prediction
            if "engagement_prediction" in result:
                analysis.update(self._extract_engagement_insights(result["engagement_prediction"]))

            # Parse platform strategy
            if "platform_strategy" in result:
                analysis.update(self._extract_platform_insights(result["platform_strategy"]))

            return analysis

        except Exception as e:
            logger.error(f"Failed to parse crew results: {e!s}")
            return {
                "quality_score": 0.7,
                "viral_potential": 0.6,
                "engagement_prediction": {},
                "optimization_suggestions": [],
                "clip_recommendations": [],
                "risk_assessment": "Low risk",
                "target_audience": [],
            }

    def _extract_viral_insights(self, text: str) -> dict:
        """Extract viral insights from analysis text."""
        insights = {}

        # Simple extraction - in production, you'd want more sophisticated parsing
        text_lower = text.lower()

        # Extract quality score
        if "quality" in text_lower:
            insights["quality_score"] = self._extract_score(text_lower, "quality")

        # Extract viral potential
        if "viral" in text_lower:
            insights["viral_potential"] = self._extract_score(text_lower, "viral")

        # Extract suggestions
        suggestions = []
        if "optimization" in text_lower:
            suggestions.append("Consider optimizing timing and pacing")
        if "engagement" in text_lower:
            suggestions.append("Focus on audience engagement strategies")

        insights["optimization_suggestions"] = suggestions

        return insights

    def _extract_optimization_insights(self, text: str) -> dict:
        """Extract optimization insights from analysis text."""
        insights = {}

        text_lower = text.lower()

        # Extract title optimization
        if "title" in text_lower:
            insights["title_optimization"] = self._extract_optimization(text_lower, "title")

        # Extract description optimization
        if "description" in text_lower:
            insights["description_optimization"] = self._extract_optimization(text_lower, "description")

        # Extract hashtags
        hashtags = []
        if "#" in text:
            hashtags = [tag.strip() for tag in text.split("#")[1:]]
        insights["hashtags"] = hashtags[:5]  # Limit to 5 hashtags

        return insights

    def _extract_engagement_insights(self, text: str) -> dict:
        """Extract engagement insights from analysis text."""
        insights = {}

        text_lower = text.lower()

        # Extract engagement predictions
        engagement_prediction = {}
        if "views" in text_lower:
            engagement_prediction["views"] = self._extract_number(text_lower, "views")
        if "likes" in text_lower:
            engagement_prediction["likes"] = self._extract_number(text_lower, "likes")
        if "shares" in text_lower:
            engagement_prediction["shares"] = self._extract_number(text_lower, "shares")

        insights["engagement_prediction"] = engagement_prediction

        return insights

    def _extract_platform_insights(self, text: str) -> dict:
        """Extract platform insights from analysis text."""
        insights = {}

        text_lower = text.lower()

        # Extract platform-specific hooks
        platform_hooks = {}
        if "youtube" in text_lower:
            platform_hooks["youtube"] = "Optimize for YouTube algorithm and SEO"
        if "tiktok" in text_lower:
            platform_hooks["tiktok"] = "Use trending sounds and hashtags"
        if "instagram" in text_lower:
            platform_hooks["instagram"] = "Focus on visual appeal and engagement"
        if "twitter" in text_lower or "x" in text_lower:
            platform_hooks["twitter"] = "Create engaging threads and use trending topics"

        insights["platform_hooks"] = platform_hooks

        return insights

    def _extract_score(self, text: str, keyword: str) -> float:
        """Extract a score from text."""
        try:
            # Look for patterns like "quality: 0.8" or "quality score: 85%"
            import re

            patterns = [
                rf"{keyword}.*?(\d+\.?\d*)",
                rf"{keyword}.*?(\d+)%",
                rf"(\d+\.?\d*).*?{keyword}",
            ]

            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    score = float(match.group(1))
                    if "%" in text or score > 1.0:
                        return score / 100.0
                    else:
                        return score

            return 0.7  # Default score

        except Exception:
            return 0.7

    def _extract_optimization(self, text: str, keyword: str) -> str:
        """Extract optimization suggestion from text."""
        try:
            # Simple extraction - in production, you'd want more sophisticated parsing
            sentences = text.split(".")
            for sentence in sentences:
                if keyword in sentence.lower():
                    return sentence.strip()

            return f"Optimize {keyword} for better engagement"

        except Exception:
            return f"Optimize {keyword} for better engagement"

    def _extract_number(self, text: str, keyword: str) -> int:
        """Extract a number from text."""
        try:
            import re

            pattern = rf"{keyword}.*?(\d+)"
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))

            return 1000  # Default number

        except Exception:
            return 1000

    async def generate_optimized_clip(
        self,
        clip_candidate: ClipCandidate,
        viral_analysis: ViralMomentAnalysis,
        clip_optimization: ClipOptimization,
    ) -> StepResult:
        """Generate an optimized clip based on analysis and optimization."""
        try:
            # Create optimized clip candidate
            optimized_clip = ClipCandidate(
                clip_id=clip_candidate.clip_id,
                moment_id=clip_candidate.moment_id,
                title=clip_optimization.title_optimization,
                description=clip_optimization.description_optimization,
                start_time=clip_candidate.start_time,
                end_time=clip_candidate.end_time,
                duration=clip_candidate.duration,
                platform=clip_candidate.platform,
                stream_id=clip_candidate.stream_id,
                channel_id=clip_candidate.channel_id,
                status=ClipStatus.PROCESSING,
                viral_moment=clip_candidate.viral_moment,
                metadata={
                    **clip_candidate.metadata,
                    "optimized": True,
                    "quality_score": viral_analysis.moment_quality_score,
                    "viral_potential": viral_analysis.viral_potential,
                    "platform_hooks": clip_optimization.platform_specific_hooks,
                    "hashtags": clip_optimization.hashtag_recommendations,
                    "engagement_strategies": clip_optimization.engagement_strategies,
                },
                created_at=clip_candidate.created_at,
                updated_at=datetime.now(),
            )

            logger.info(f"Generated optimized clip: {optimized_clip.title}")
            return StepResult.ok(data={"optimized_clip": optimized_clip})

        except Exception as e:
            logger.error(f"Failed to generate optimized clip: {e!s}")
            return StepResult.fail(f"Failed to generate optimized clip: {e!s}")

    async def get_analysis_summary(
        self, viral_analysis: ViralMomentAnalysis, clip_optimization: ClipOptimization
    ) -> StepResult:
        """Get a summary of the analysis and optimization."""
        try:
            summary = {
                "viral_moment_quality": viral_analysis.moment_quality_score,
                "viral_potential": viral_analysis.viral_potential,
                "engagement_predictions": viral_analysis.engagement_prediction,
                "optimization_highlights": {
                    "title": clip_optimization.title_optimization,
                    "description": clip_optimization.description_optimization,
                    "hashtags": clip_optimization.hashtag_recommendations[:3],  # Top 3
                    "platforms": list(clip_optimization.platform_specific_hooks.keys()),
                },
                "recommendations": {
                    "optimization": viral_analysis.optimization_suggestions[:3],  # Top 3
                    "engagement": clip_optimization.engagement_strategies[:3],  # Top 3
                    "clips": viral_analysis.clip_recommendations[:3],  # Top 3
                },
                "risk_assessment": viral_analysis.risk_assessment,
                "target_audience": viral_analysis.target_audience,
            }

            return StepResult.ok(data={"summary": summary})

        except Exception as e:
            logger.error(f"Failed to generate analysis summary: {e!s}")
            return StepResult.fail(f"Failed to generate analysis summary: {e!s}")
