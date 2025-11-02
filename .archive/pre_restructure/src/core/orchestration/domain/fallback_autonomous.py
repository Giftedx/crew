"""Fallback autonomous intelligence orchestrator.

This provides basic autonomous intelligence functionality when CrewAI is not available,
ensuring the /autointel command can still provide some level of analysis.

Migrated from: ultimate_discord_intelligence_bot/fallback_orchestrator.py
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

import structlog

from core.orchestration.protocols import (
    BaseOrchestrator,
    OrchestrationLayer,
    OrchestrationType,
)


if TYPE_CHECKING:
    from core.orchestration.protocols import OrchestrationContext
    from ultimate_discord_intelligence_bot.step_result import StepResult

logger = structlog.get_logger(__name__)


class FallbackAutonomousOrchestrator(BaseOrchestrator):
    """Fallback orchestrator for autonomous intelligence when CrewAI is not available.

    This orchestrator provides basic content analysis functionality without CrewAI dependencies,
    ensuring graceful degradation of the autonomous intelligence features.
    """

    def __init__(self) -> None:
        """Initialize the fallback autonomous orchestrator."""
        super().__init__(
            layer=OrchestrationLayer.DOMAIN,
            name="fallback_autonomous",
            orchestration_type=OrchestrationType.SEQUENTIAL,
        )

    async def orchestrate(
        self,
        context: OrchestrationContext,
        **kwargs: Any,
    ) -> StepResult:
        """Execute fallback autonomous intelligence workflow.

        Args:
            context: Orchestration context with tenant and request information
            **kwargs: Additional parameters:
                - interaction: Discord interaction object for progress updates
                - url: URL to analyze
                - depth: Analysis depth (default: "standard")

        Returns:
            StepResult with analysis results or error information
        """
        # Import here to avoid circular dependencies
        from ultimate_discord_intelligence_bot.step_result import (
            ErrorCategory,
            StepResult,
        )

        self._log_orchestration_start(context, **kwargs)

        # Extract parameters
        interaction = kwargs.get("interaction")
        url = kwargs.get("url")
        depth = kwargs.get("depth", "standard")

        if not url:
            result = StepResult.fail(
                "URL parameter is required",
                error_category=ErrorCategory.PROCESSING,
            )
            self._log_orchestration_end(context, result)
            return result

        start_time = time.time()

        try:
            # Stage 1: Progress notification
            if interaction:
                await self._send_progress_update(
                    interaction,
                    "🔄 Starting basic intelligence analysis (CrewAI unavailable)...",
                    1,
                    5,
                )

            # Stage 2: Basic Content Pipeline
            if interaction:
                await self._send_progress_update(
                    interaction,
                    "📥 Running basic content pipeline...",
                    2,
                    5,
                )

            pipeline_result = await self._execute_basic_pipeline(url)

            if not pipeline_result.success:
                if interaction:
                    await interaction.followup.send(
                        f"❌ Content acquisition failed: {pipeline_result.error}\n\n"
                        f"**Fallback Mode Active** (CrewAI unavailable)\n"
                        f"- URL: {url}\n"
                        f"- Attempted basic content processing\n"
                        f"- Consider installing CrewAI for full autonomous intelligence capabilities",
                        ephemeral=False,
                    )

                result = StepResult.fail(
                    f"Content acquisition failed: {pipeline_result.error}",
                    error_category=ErrorCategory.PROCESSING,
                    retryable=True,
                )
                self._log_orchestration_end(context, result)
                return result

            # Stage 3: Basic Analysis
            if interaction:
                await self._send_progress_update(
                    interaction,
                    "🔍 Performing basic content analysis...",
                    3,
                    5,
                )

            pipeline_payload = pipeline_result.data.get("data", pipeline_result.data)
            analysis_result = await self._execute_basic_analysis(pipeline_payload)

            # Stage 4: Basic Fact Checking
            if interaction:
                await self._send_progress_update(
                    interaction,
                    "✅ Running basic fact verification...",
                    4,
                    5,
                )

            fact_result = await self._execute_basic_fact_check(pipeline_payload)

            # Stage 5: Generate Report
            if interaction:
                await self._send_progress_update(
                    interaction,
                    "📋 Generating intelligence report...",
                    5,
                    5,
                )

            processing_time = time.time() - start_time

            # Create fallback report
            report = await self._generate_fallback_report(
                url,
                depth,
                pipeline_payload,
                analysis_result.data,
                fact_result.data,
                processing_time,
            )

            # Send report to Discord if interaction available
            if interaction:
                await interaction.followup.send(report, ephemeral=False)

            result = StepResult.ok(
                result={
                    "report": report,
                    "url": url,
                    "depth": depth,
                    "processing_time": processing_time,
                    "pipeline_data": pipeline_payload,
                    "analysis_data": analysis_result.data,
                    "fact_data": fact_result.data,
                }
            )

            self._log_orchestration_end(context, result)
            return result

        except Exception as e:
            logger.exception(
                "fallback_orchestration_failed",
                error=str(e),
                tenant_id=context.tenant_id,
                request_id=context.request_id,
            )

            if interaction:
                await interaction.followup.send(
                    f"❌ Even fallback processing failed: {e}\n\n"
                    f"**System Status**: CrewAI dependencies not available\n"
                    f"**URL**: {url}\n"
                    f"**Recommendation**: Please install CrewAI for full functionality:\n"
                    f"```\npip install crewai\n```",
                    ephemeral=True,
                )

            result = StepResult.fail(
                f"Fallback orchestration failed: {e}",
                error_category=ErrorCategory.PROCESSING,
                retryable=True,
            )
            self._log_orchestration_end(context, result)
            return result

    async def _send_progress_update(
        self,
        interaction: Any,
        message: str,
        current: int,
        total: int,
    ) -> None:
        """Send progress update to Discord.

        Args:
            interaction: Discord interaction object
            message: Progress message
            current: Current step number
            total: Total number of steps
        """
        progress_bar = "█" * (current * 10 // total) + "░" * (10 - current * 10 // total)

        try:
            if current == 1:
                await interaction.followup.send(
                    f"{message}\n`{progress_bar}` {current}/{total}",
                    ephemeral=False,
                )
            else:
                # Try to edit the previous message, but don't fail if we can't
                try:
                    await interaction.edit_original_response(content=f"{message}\n`{progress_bar}` {current}/{total}")
                except Exception:
                    # If edit fails, send a new message
                    await interaction.followup.send(
                        f"{message}\n`{progress_bar}` {current}/{total}",
                        ephemeral=False,
                    )
        except Exception as e:
            logger.warning(
                "progress_update_failed",
                error=str(e),
                current=current,
                total=total,
            )

    async def _execute_basic_pipeline(self, url: str) -> StepResult:
        """Execute basic content pipeline using available tools.

        Args:
            url: URL to process

        Returns:
            StepResult with pipeline data or error
        """
        from ultimate_discord_intelligence_bot.step_result import StepResult

        try:
            from ultimate_discord_intelligence_bot.tools import PipelineTool

            pipeline_tool = PipelineTool()

            # Try different quality levels
            for quality in ["720p", "audio", "worst"]:
                try:
                    result = await pipeline_tool._run_async(url, quality=quality)
                    if result.success:
                        return result
                except Exception as e:
                    logger.warning(
                        "pipeline_quality_attempt_failed",
                        quality=quality,
                        error=str(e),
                    )
                    continue

            return StepResult.fail("All pipeline attempts failed")

        except ImportError:
            return StepResult.fail("PipelineTool not available")
        except Exception as e:
            return StepResult.fail(f"Pipeline execution failed: {e}")

    async def _execute_basic_analysis(
        self,
        pipeline_data: dict[str, Any],
    ) -> StepResult:
        """Execute basic analysis using available tools.

        Args:
            pipeline_data: Pipeline output data

        Returns:
            StepResult with analysis data
        """
        from ultimate_discord_intelligence_bot.step_result import StepResult

        try:
            from ultimate_discord_intelligence_bot.tools import (
                SentimentTool,
                TextAnalysisTool,
            )

            # ContentPipeline returns a top-level 'transcription' mapping
            transcription_block = pipeline_data.get("transcription", {}) if isinstance(pipeline_data, dict) else {}
            transcript = transcription_block.get("transcript", "")

            if not transcript:
                return StepResult.skip(reason="No transcript available")

            # Basic text analysis
            text_tool = TextAnalysisTool()
            sentiment_tool = SentimentTool()

            text_result = await asyncio.to_thread(text_tool.run, transcript)
            sentiment_result = await asyncio.to_thread(sentiment_tool.run, transcript)

            return StepResult.ok(
                message="Basic analysis completed",
                text_analysis=text_result.data if text_result.success else {},
                sentiment_analysis=sentiment_result.data if sentiment_result.success else {},
            )

        except ImportError:
            return StepResult.skip(reason="Analysis tools not available")
        except Exception as e:
            return StepResult.fail(f"Basic analysis failed: {e}")

    async def _execute_basic_fact_check(
        self,
        pipeline_data: dict[str, Any],
    ) -> StepResult:
        """Execute basic fact checking using available tools.

        Args:
            pipeline_data: Pipeline output data

        Returns:
            StepResult with fact check data
        """
        from ultimate_discord_intelligence_bot.step_result import StepResult

        try:
            from ultimate_discord_intelligence_bot.tools import (
                FactCheckTool,
                LogicalFallacyTool,
            )

            transcription_block = pipeline_data.get("transcription", {}) if isinstance(pipeline_data, dict) else {}
            transcript = transcription_block.get("transcript", "")

            if not transcript:
                return StepResult.skip(reason="No transcript available")

            fact_tool = FactCheckTool()
            fallacy_tool = LogicalFallacyTool()

            fact_result = await asyncio.to_thread(fact_tool.run, transcript)
            fallacy_result = await asyncio.to_thread(fallacy_tool.run, transcript)

            return StepResult.ok(
                message="Basic fact checking completed",
                fact_checks=fact_result.data if fact_result.success else {},
                logical_fallacies=fallacy_result.data if fallacy_result.success else {},
            )

        except ImportError:
            return StepResult.skip(reason="Fact checking tools not available")
        except Exception as e:
            return StepResult.fail(f"Basic fact check failed: {e}")

    async def _generate_fallback_report(
        self,
        url: str,
        depth: str,
        pipeline_data: dict[str, Any],
        analysis_data: dict[str, Any],
        fact_data: dict[str, Any],
        processing_time: float,
    ) -> str:
        """Generate fallback intelligence report.

        Args:
            url: Analyzed URL
            depth: Analysis depth
            pipeline_data: Pipeline output
            analysis_data: Analysis results
            fact_data: Fact check results
            processing_time: Processing time in seconds

        Returns:
            Formatted report string
        """
        # Extract basic information
        download_info = pipeline_data.get("download", {})
        title = download_info.get("title", "Unknown Title")
        platform = download_info.get("platform", "Unknown Platform")
        duration = download_info.get("duration", "Unknown Duration")

        # Transcript lives under the 'transcription' block
        transcription_block = pipeline_data.get("transcription", {}) if isinstance(pipeline_data, dict) else {}
        transcript = transcription_block.get("transcript", "")
        transcript_length = len(transcript.split()) if transcript else 0

        # Basic sentiment analysis
        sentiment_data = analysis_data.get("sentiment_analysis", {})
        sentiment_score = sentiment_data.get("sentiment_score", 0.0)
        sentiment_label = "Positive" if sentiment_score > 0.1 else "Negative" if sentiment_score < -0.1 else "Neutral"

        # Basic fact check results
        fact_checks = fact_data.get("fact_checks", {})
        fact_check_summary = "Completed" if fact_checks else "Limited"

        report = f"""# 🤖 Autonomous Intelligence Report (Fallback Mode)

**⚠️ Notice**: CrewAI dependencies not available - running in basic fallback mode

## 📊 Content Summary
- **URL**: {url}
- **Title**: {title}
- **Platform**: {platform}
- **Duration**: {duration}
- **Analysis Depth**: {depth}
- **Processing Time**: {processing_time:.1f} seconds

## 📝 Transcript Analysis
- **Word Count**: {transcript_length:,} words
- **Content Available**: {"✅ Yes" if transcript else "❌ No"}

## 🎭 Sentiment Analysis
- **Overall Sentiment**: {sentiment_label}
- **Sentiment Score**: {sentiment_score:.2f}

## ✅ Fact Verification
- **Status**: {fact_check_summary}
- **Verification Tools**: {"Available" if fact_checks else "Limited"}

## 🔄 System Status
- **Mode**: Fallback (Basic Processing)
- **CrewAI Status**: ❌ Not Available
- **Multi-Agent Orchestration**: ❌ Disabled
- **Advanced AI Features**: ❌ Disabled

## 💡 Recommendations
To unlock full autonomous intelligence capabilities:

1. **Install CrewAI**: `pip install crewai`
2. **Configure Dependencies**: Ensure all AI tools are properly configured
3. **Retry Analysis**: Re-run `/autointel` after installation for full multi-agent analysis

## 📋 Available Analysis Types
When CrewAI is installed, you'll have access to:
- 🎯 15 Specialized AI Agents
- 🔍 25-Stage Analysis Pipeline
- 🛡️ Advanced Threat Detection
- 👤 Behavioral Profiling
- 🌐 Social Intelligence Monitoring
- 📚 Research Synthesis
- 🤖 AI-Enhanced Quality Assessment

---
*Report generated by Ultimate Discord Intelligence Bot - Fallback Mode*
*Timestamp: {time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}*"""

        return report
