"""
CrewAI agent for Episode Intelligence Pack generation and analysis.
Provides intelligent content analysis and recommendations for creators.
"""

import logging

from crewai import Agent, Crew, Task  # type: ignore[import-not-found]
from pydantic import BaseModel

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.features.intelligence_models import (
    EpisodeIntelligence,
)
from ultimate_discord_intelligence_bot.creator_ops.media.alignment import (
    AlignedTranscript,
)
from ultimate_discord_intelligence_bot.creator_ops.media.nlp import NLPResult
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class IntelligenceAnalysis(BaseModel):
    """Analysis result from intelligence agent."""

    episode_summary: str
    key_insights: list[str]
    content_recommendations: list[str]
    audience_engagement_predictions: dict[str, float]
    monetization_opportunities: list[str]
    risk_assessments: list[str]
    improvement_suggestions: list[str]


class EpisodeIntelligenceAgent:
    """CrewAI agent for episode intelligence analysis and recommendations."""

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
        """Create specialized agents for intelligence analysis."""
        agents = {}

        # Content Analyst Agent
        agents["content_analyst"] = Agent(
            role="Content Analyst",
            goal="Analyze episode content for quality, engagement, and audience appeal",
            backstory="""You are an expert content analyst with deep understanding of podcast and video content.
            You specialize in identifying what makes content engaging, valuable, and shareable.
            You understand audience psychology and can predict content performance.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

        # Risk Assessment Agent
        agents["risk_assessor"] = Agent(
            role="Risk Assessment Specialist",
            goal="Identify potential legal, brand safety, and reputation risks in content",
            backstory="""You are a legal and risk assessment expert specializing in content creation.
            You understand defamation law, brand safety guidelines, and platform policies.
            You help creators avoid content that could harm their reputation or lead to legal issues.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

        # Monetization Agent
        agents["monetization_expert"] = Agent(
            role="Monetization Strategist",
            goal="Identify revenue opportunities and optimization strategies for content",
            backstory="""You are a monetization expert who understands how to maximize revenue from content.
            You know about sponsorships, affiliate marketing, merchandise, and audience monetization.
            You help creators identify and capitalize on revenue opportunities.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

        # Audience Engagement Agent
        agents["audience_specialist"] = Agent(
            role="Audience Engagement Specialist",
            goal="Predict and optimize audience engagement and retention",
            backstory="""You are an audience engagement expert who understands what drives viewer retention and engagement.
            You analyze content patterns, audience behavior, and engagement metrics.
            You help creators optimize content for maximum audience engagement and growth.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

        return agents

    def _create_tasks(self) -> dict[str, Task]:
        """Create tasks for intelligence analysis."""
        tasks = {}

        # Content Analysis Task
        tasks["content_analysis"] = Task(
            description="""
            Analyze the episode content and provide insights on:
            1. Content quality and value proposition
            2. Key themes and topics covered
            3. Content structure and flow
            4. Audience appeal and engagement potential
            5. Content uniqueness and differentiation

            Provide specific, actionable insights that help creators understand their content better.
            """,
            agent=self.agents["content_analyst"],
            expected_output="Detailed content analysis with quality assessment and engagement predictions",
        )

        # Risk Assessment Task
        tasks["risk_assessment"] = Task(
            description="""
            Assess potential risks in the episode content:
            1. Defamation and legal risks
            2. Brand safety concerns
            3. Platform policy violations
            4. Reputation risks
            5. Controversy potential

            Provide specific risk factors and mitigation strategies.
            """,
            agent=self.agents["risk_assessor"],
            expected_output="Comprehensive risk assessment with specific concerns and mitigation recommendations",
        )

        # Monetization Analysis Task
        tasks["monetization_analysis"] = Task(
            description="""
            Identify monetization opportunities in the episode:
            1. Sponsorship opportunities
            2. Affiliate marketing potential
            3. Product placement opportunities
            4. Audience monetization strategies
            5. Revenue optimization recommendations

            Provide specific, actionable monetization strategies.
            """,
            agent=self.agents["monetization_expert"],
            expected_output="Detailed monetization analysis with specific opportunities and implementation strategies",
        )

        # Audience Engagement Task
        tasks["audience_engagement"] = Task(
            description="""
            Analyze audience engagement potential:
            1. Engagement prediction for different segments
            2. Retention optimization opportunities
            3. Shareability factors
            4. Audience growth potential
            5. Community building opportunities

            Provide specific recommendations for improving audience engagement.
            """,
            agent=self.agents["audience_specialist"],
            expected_output="Comprehensive audience engagement analysis with specific optimization recommendations",
        )

        return tasks

    def _create_crew(self) -> Crew:
        """Create the intelligence analysis crew."""
        return Crew(
            agents=list(self.agents.values()),
            tasks=list(self.tasks.values()),
            verbose=True,
            memory=True,
            planning=True,
            cache=True,
            max_rpm=10,
        )

    async def analyze_episode_intelligence(
        self,
        intelligence_pack: EpisodeIntelligence,
        transcript: AlignedTranscript,
        nlp_result: NLPResult | None = None,
    ) -> StepResult:
        """
        Analyze episode intelligence using CrewAI agents.

        Args:
            intelligence_pack: Generated intelligence pack
            transcript: Episode transcript
            nlp_result: Optional NLP analysis results

        Returns:
            StepResult with analysis results
        """
        try:
            logger.info(f"Starting intelligence analysis for episode {intelligence_pack.episode_id}")

            # Prepare inputs for agents
            inputs = {
                "episode_id": intelligence_pack.episode_id,
                "episode_title": intelligence_pack.episode_title,
                "episode_duration": intelligence_pack.episode_duration,
                "agenda": intelligence_pack.agenda,
                "guests": intelligence_pack.guests,
                "claims": intelligence_pack.claims,
                "quotations": intelligence_pack.quotations,
                "links": intelligence_pack.links,
                "brand_safety": intelligence_pack.brand_safety,
                "defamation_risk": intelligence_pack.defamation_risk,
                "transcript": transcript,
                "nlp_result": nlp_result,
            }

            # Execute crew analysis
            result = self.crew.kickoff(inputs=inputs)

            # Parse results
            analysis = self._parse_crew_results(result)

            # Generate recommendations
            recommendations = await self._generate_recommendations(intelligence_pack, analysis)

            # Create final analysis result
            intelligence_analysis = IntelligenceAnalysis(
                episode_summary=analysis.get("episode_summary", ""),
                key_insights=analysis.get("key_insights", []),
                content_recommendations=recommendations.get("content", []),
                audience_engagement_predictions=analysis.get("audience_engagement", {}),
                monetization_opportunities=recommendations.get("monetization", []),
                risk_assessments=recommendations.get("risks", []),
                improvement_suggestions=recommendations.get("improvements", []),
            )

            logger.info(f"Intelligence analysis completed for episode {intelligence_pack.episode_id}")
            return StepResult.ok(data={"analysis": intelligence_analysis})

        except Exception as e:
            logger.error(f"Intelligence analysis failed: {e!s}")
            return StepResult.fail(f"Intelligence analysis failed: {e!s}")

    def _parse_crew_results(self, result) -> dict:
        """Parse results from crew execution."""
        try:
            # Extract results from each task
            analysis = {
                "episode_summary": "",
                "key_insights": [],
                "content_analysis": "",
                "risk_assessment": "",
                "monetization_analysis": "",
                "audience_engagement": {},
                "overall_recommendations": [],
            }

            # Parse content analysis
            if "content_analysis" in result:
                analysis["content_analysis"] = result["content_analysis"]
                analysis["key_insights"].extend(self._extract_insights(result["content_analysis"]))

            # Parse risk assessment
            if "risk_assessment" in result:
                analysis["risk_assessment"] = result["risk_assessment"]
                analysis["key_insights"].extend(self._extract_insights(result["risk_assessment"]))

            # Parse monetization analysis
            if "monetization_analysis" in result:
                analysis["monetization_analysis"] = result["monetization_analysis"]
                analysis["key_insights"].extend(self._extract_insights(result["monetization_analysis"]))

            # Parse audience engagement
            if "audience_engagement" in result:
                analysis["audience_engagement"] = result["audience_engagement"]
                analysis["key_insights"].extend(self._extract_insights(result["audience_engagement"]))

            # Generate episode summary
            analysis["episode_summary"] = self._generate_episode_summary(analysis)

            return analysis

        except Exception as e:
            logger.error(f"Failed to parse crew results: {e!s}")
            return {"episode_summary": "Analysis parsing failed", "key_insights": []}

    def _extract_insights(self, text: str) -> list[str]:
        """Extract key insights from analysis text."""
        insights = []

        # Simple extraction - in production, you'd want more sophisticated parsing
        sentences = text.split(". ")
        for sentence in sentences:
            if len(sentence) > 20 and any(
                keyword in sentence.lower()
                for keyword in [
                    "insight",
                    "recommendation",
                    "suggestion",
                    "opportunity",
                ]
            ):
                insights.append(sentence.strip())

        return insights[:5]  # Limit to top 5 insights

    def _generate_episode_summary(self, analysis: dict) -> str:
        """Generate episode summary from analysis."""
        summary_parts = []

        if analysis.get("content_analysis"):
            summary_parts.append("Content Analysis: " + analysis["content_analysis"][:200] + "...")

        if analysis.get("risk_assessment"):
            summary_parts.append("Risk Assessment: " + analysis["risk_assessment"][:200] + "...")

        if analysis.get("monetization_analysis"):
            summary_parts.append("Monetization: " + analysis["monetization_analysis"][:200] + "...")

        return " | ".join(summary_parts)

    async def _generate_recommendations(
        self, intelligence_pack: EpisodeIntelligence, analysis: dict
    ) -> dict[str, list[str]]:
        """Generate specific recommendations based on analysis."""
        recommendations = {
            "content": [],
            "monetization": [],
            "risks": [],
            "improvements": [],
        }

        # Content recommendations
        if intelligence_pack.claims:
            recommendations["content"].append("Consider fact-checking unverified claims to improve credibility")

        if intelligence_pack.quotations:
            recommendations["content"].append("Highlight notable quotations for social media promotion")

        if intelligence_pack.agenda:
            recommendations["content"].append("Use agenda items to create chapter markers for better navigation")

        # Monetization recommendations
        if intelligence_pack.links:
            recommendations["monetization"].append("Review affiliate links for monetization opportunities")

        if intelligence_pack.guests:
            recommendations["monetization"].append("Consider guest appearances for cross-promotion opportunities")

        # Risk recommendations
        if intelligence_pack.defamation_risk and intelligence_pack.defamation_risk.risk_level.value == "high":
            recommendations["risks"].append("High defamation risk detected - review flagged statements")

        if intelligence_pack.brand_safety and intelligence_pack.brand_safety.overall_score < 3.0:
            recommendations["risks"].append("Brand safety concerns - review flagged content")

        # Improvement suggestions
        if intelligence_pack.average_sentiment < -0.3:
            recommendations["improvements"].append("Consider balancing negative sentiment with positive content")

        if intelligence_pack.total_speakers < 2:
            recommendations["improvements"].append("Consider adding guest speakers for more dynamic content")

        return recommendations

    async def generate_intelligence_report(
        self, intelligence_pack: EpisodeIntelligence, analysis: IntelligenceAnalysis
    ) -> StepResult:
        """Generate a comprehensive intelligence report."""
        try:
            report = {
                "episode_id": intelligence_pack.episode_id,
                "episode_title": intelligence_pack.episode_title,
                "generated_at": intelligence_pack.created_at.isoformat(),
                "summary": analysis.episode_summary,
                "key_insights": analysis.key_insights,
                "content_recommendations": analysis.content_recommendations,
                "monetization_opportunities": analysis.monetization_opportunities,
                "risk_assessments": analysis.risk_assessments,
                "improvement_suggestions": analysis.improvement_suggestions,
                "audience_engagement_predictions": analysis.audience_engagement_predictions,
                "intelligence_pack": intelligence_pack.dict(),
                "analysis_metadata": {
                    "total_speakers": intelligence_pack.total_speakers,
                    "total_segments": intelligence_pack.total_segments,
                    "episode_duration": intelligence_pack.episode_duration,
                    "average_sentiment": intelligence_pack.average_sentiment,
                    "top_topics": intelligence_pack.top_topics,
                },
            }

            return StepResult.ok(data={"report": report})

        except Exception as e:
            logger.error(f"Failed to generate intelligence report: {e!s}")
            return StepResult.fail(f"Failed to generate intelligence report: {e!s}")

    async def get_intelligence_dashboard_data(
        self, intelligence_pack: EpisodeIntelligence, analysis: IntelligenceAnalysis
    ) -> StepResult:
        """Generate dashboard data for intelligence visualization."""
        try:
            dashboard_data = {
                "episode_overview": {
                    "title": intelligence_pack.episode_title,
                    "duration": intelligence_pack.episode_duration,
                    "speakers": intelligence_pack.total_speakers,
                    "segments": intelligence_pack.total_segments,
                    "sentiment": intelligence_pack.average_sentiment,
                },
                "content_metrics": {
                    "agenda_items": len(intelligence_pack.agenda),
                    "guests": len(intelligence_pack.guests),
                    "claims": len(intelligence_pack.claims),
                    "quotations": len(intelligence_pack.quotations),
                    "links": len(intelligence_pack.links),
                },
                "safety_metrics": {
                    "brand_safety_score": intelligence_pack.brand_safety.overall_score
                    if intelligence_pack.brand_safety
                    else None,
                    "defamation_risk": intelligence_pack.defamation_risk.risk_level.value
                    if intelligence_pack.defamation_risk
                    else None,
                    "flagged_segments": len(intelligence_pack.brand_safety.flagged_segments)
                    if intelligence_pack.brand_safety
                    else 0,
                },
                "engagement_predictions": analysis.audience_engagement_predictions,
                "top_topics": intelligence_pack.top_topics,
                "key_insights": analysis.key_insights[:5],  # Top 5 insights
                "recommendations": {
                    "content": analysis.content_recommendations[:3],
                    "monetization": analysis.monetization_opportunities[:3],
                    "risks": analysis.risk_assessments[:3],
                    "improvements": analysis.improvement_suggestions[:3],
                },
            }

            return StepResult.ok(data={"dashboard": dashboard_data})

        except Exception as e:
            logger.error(f"Failed to generate dashboard data: {e!s}")
            return StepResult.fail(f"Failed to generate dashboard data: {e!s}")
