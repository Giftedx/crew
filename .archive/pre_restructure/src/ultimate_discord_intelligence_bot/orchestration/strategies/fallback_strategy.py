"""Fallback orchestration strategy for degraded mode operation.

Provides basic intelligence workflow when CrewAI dependencies are unavailable,
ensuring the /autointel command can still function with reduced capabilities.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from core.orchestration import OrchestrationContext, get_orchestration_facade
from core.orchestration.domain import FallbackAutonomousOrchestrator
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class FallbackStrategy:
    """Fallback orchestration strategy for degraded mode.

    Provides basic content processing without CrewAI multi-agent workflows.
    Uses simple tool chains for pipeline → analysis → fact-checking → report.
    """

    name: str = "fallback"
    description: str = "Degraded mode for basic intelligence when CrewAI unavailable"

    def __init__(self):
        """Initialize fallback strategy."""
        # Register fallback orchestrator with the global facade
        self._orchestrator = FallbackAutonomousOrchestrator()
        facade = get_orchestration_facade()
        facade.register(self._orchestrator)

        logger.info("FallbackStrategy initialized with orchestration facade")

    async def execute_workflow(
        self,
        url: str,
        depth: str = "standard",
        tenant: str = "default",
        workspace: str = "main",
        **kwargs: Any,
    ) -> StepResult:
        """Execute fallback intelligence workflow.

        Args:
            url: Content URL to process
            depth: Analysis depth (ignored in fallback mode)
            tenant: Tenant identifier
            workspace: Workspace identifier
            **kwargs: Additional parameters (interaction for Discord updates)

        Returns:
            StepResult with workflow execution outcome
        """
        from obs.metrics import get_metrics

        metrics = get_metrics()
        metrics.counter(
            "orchestration_strategy_executions_total",
            labels={"strategy": self.name, "outcome": "started"},
        )

        try:
            logger.info(f"Executing fallback workflow: url={url}, tenant={tenant}, workspace={workspace}")

            # Check if interaction was provided for Discord updates
            interaction = kwargs.get("interaction")

            if interaction:
                # Create orchestration context
                context = OrchestrationContext(
                    tenant_id=tenant,
                    request_id=str(uuid.uuid4()),
                    metadata={"url": url, "depth": depth, "workspace": workspace},
                )

                # Execute via orchestration facade
                facade = get_orchestration_facade()
                result = await facade.orchestrate(
                    "fallback_autonomous",
                    context,
                    interaction=interaction,
                    url=url,
                    depth=depth,
                )

                # The orchestrator sends Discord messages directly
                metrics.counter(
                    "orchestration_strategy_executions_total",
                    labels={"strategy": self.name, "outcome": "success" if result.success else "failure"},
                )

                if result.success:
                    return StepResult.ok(
                        message="Fallback workflow completed",
                        mode="fallback",
                        url=url,
                        tenant=tenant,
                        workspace=workspace,
                    )
                else:
                    return result
            else:
                # Execute without Discord interaction (testing/API mode)
                result = await self._execute_pipeline_only(url)
                return result

        except Exception as exc:
            logger.error(f"Fallback workflow failed: {exc}", exc_info=True)
            metrics.counter(
                "orchestration_strategy_executions_total",
                labels={"strategy": self.name, "outcome": "failure"},
            )
            return StepResult.fail(
                f"Fallback orchestration failed: {exc}",
                step="fallback_workflow",
            )

    async def _execute_pipeline_only(self, url: str) -> StepResult:
        """Execute basic pipeline without Discord interaction.

        Args:
            url: Content URL to process

        Returns:
            StepResult with pipeline outcome
        """
        try:
            # Execute basic pipeline
            pipeline_result = await self._orchestrator._execute_basic_pipeline(url)

            if not pipeline_result.success:
                return StepResult.fail(
                    f"Pipeline failed: {pipeline_result.error}",
                    step="fallback_pipeline",
                )

            # Execute basic analysis
            pipeline_data = pipeline_result.data.get("data", pipeline_result.data)
            analysis_result = await self._orchestrator._execute_basic_analysis(pipeline_data)

            # Execute basic fact check
            fact_result = await self._orchestrator._execute_basic_fact_check(pipeline_data)

            # Combine results
            return StepResult.ok(
                pipeline=pipeline_data,
                analysis=analysis_result.data if analysis_result.success else {},
                fact_check=fact_result.data if fact_result.success else {},
                mode="fallback",
                message="Fallback workflow completed without Discord interaction",
            )

        except Exception as exc:
            return StepResult.fail(f"Pipeline execution failed: {exc}", step="fallback_pipeline")

    async def initialize(self) -> None:
        """Initialize strategy resources."""
        logger.info("FallbackStrategy resources initialized")

    async def cleanup(self) -> None:
        """Cleanup strategy resources."""
        logger.info("FallbackStrategy resources cleaned up")


__all__ = ["FallbackStrategy"]
