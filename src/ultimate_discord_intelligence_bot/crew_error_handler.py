"""
DEPRECATED: This file is deprecated and will be removed in a future version.
Please use ultimate_discord_intelligence_bot.crew_core instead.

Migration guide:
- Import from crew_core instead of this module
- Use UnifiedCrewExecutor for crew execution
- Use CrewErrorHandler for error handling
- Use CrewInsightGenerator for insight generation

Example:
    from ultimate_discord_intelligence_bot.crew_core import (
        UnifiedCrewExecutor,
        CrewConfig,
        CrewTask,
    )
"""

import warnings


warnings.warn(
    "This module is deprecated. Use ultimate_discord_intelligence_bot.crew_core instead.",
    DeprecationWarning,
    stacklevel=2,
)


"""Advanced error handling and recovery system for autonomous intelligence workflows.

This module provides context-aware error handling, crew-level failure recovery,
graceful degradation strategies, and intelligent retry mechanisms for the
multi-agent intelligence orchestration system.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .step_result import StepResult


class ErrorSeverity(Enum):
    """Error severity levels for intelligent error handling."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """Recovery strategies for different types of errors."""

    RETRY = "retry"
    FALLBACK_AGENT = "fallback_agent"
    SIMPLIFIED_EXECUTION = "simplified_execution"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    ABORT_WORKFLOW = "abort_workflow"


@dataclass
class ErrorContext:
    """Context information for error analysis and recovery."""

    stage_name: str
    agent_name: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    retry_count: int
    workflow_depth: str
    preceding_stage_results: dict[str, Any]
    system_health: dict[str, Any]


@dataclass
class RecoveryPlan:
    """Recovery plan for error handling."""

    strategy: RecoveryStrategy
    fallback_agent: str | None
    simplified_parameters: dict[str, Any] | None
    max_retries: int
    degradation_level: str
    continue_workflow: bool
    reason: str


class CrewErrorHandler:
    """Advanced error handler for CrewAI multi-agent workflows."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_history: list[ErrorContext] = []
        self.recovery_metrics = {
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "degraded_executions": 0,
        }

    async def handle_crew_error(
        self,
        error: Exception,
        stage_name: str,
        agent_name: str,
        workflow_depth: str,
        retry_count: int = 0,
        preceding_results: dict[str, Any] | None = None,
        system_health: dict[str, Any] | None = None,
    ) -> tuple[RecoveryPlan, StepResult]:
        """
        Handle crew-level errors with intelligent recovery strategies.

        Args:
            error: The exception that occurred
            stage_name: Name of the workflow stage that failed
            agent_name: Name of the agent that failed
            workflow_depth: Analysis depth (standard, deep, comprehensive, experimental)
            retry_count: Number of retries already attempted
            preceding_results: Results from previous stages
            system_health: Current system health metrics

        Returns:
            Tuple of recovery plan and interim step result
        """
        try:
            # Analyze error context
            error_context = self._analyze_error_context(
                error,
                stage_name,
                agent_name,
                workflow_depth,
                retry_count,
                preceding_results or {},
                system_health or {},
            )

            # Generate recovery plan
            recovery_plan = self._generate_recovery_plan(error_context)

            # Log error and recovery plan
            self._log_error_and_recovery(error_context, recovery_plan)

            # Update error history
            self.error_history.append(error_context)

            # Execute recovery strategy
            interim_result = await self._execute_recovery_strategy(error_context, recovery_plan)

            return recovery_plan, interim_result

        except Exception as recovery_error:
            # Ultimate fallback if recovery itself fails
            self.logger.critical(f"Recovery system failure: {recovery_error}")
            critical_plan = RecoveryPlan(
                strategy=RecoveryStrategy.ABORT_WORKFLOW,
                fallback_agent=None,
                simplified_parameters=None,
                max_retries=0,
                degradation_level="critical",
                continue_workflow=False,
                reason=f"Recovery system failure: {recovery_error}",
            )
            critical_result = StepResult.fail(
                f"Critical system failure in error recovery: {recovery_error}",
                step=f"{stage_name}_critical_failure",
            )
            return critical_plan, critical_result

    def _analyze_error_context(
        self,
        error: Exception,
        stage_name: str,
        agent_name: str,
        workflow_depth: str,
        retry_count: int,
        preceding_results: dict[str, Any],
        system_health: dict[str, Any],
    ) -> ErrorContext:
        """Analyze error context to determine appropriate recovery strategy."""

        # Determine error type and severity
        error_type = type(error).__name__
        error_message = str(error)

        severity = self._assess_error_severity(error, stage_name, retry_count, workflow_depth)

        return ErrorContext(
            stage_name=stage_name,
            agent_name=agent_name,
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            retry_count=retry_count,
            workflow_depth=workflow_depth,
            preceding_stage_results=preceding_results,
            system_health=system_health,
        )

    def _assess_error_severity(
        self,
        error: Exception,
        stage_name: str,
        retry_count: int,
        workflow_depth: str,
    ) -> ErrorSeverity:
        """Assess the severity of the error for recovery planning."""

        # Critical errors that should abort workflow
        if isinstance(error, (MemoryError, SystemError)):
            return ErrorSeverity.CRITICAL

        # High severity for core stages or repeated failures
        if stage_name in ["content_acquisition", "mission_coordination"] or retry_count >= 3:
            return ErrorSeverity.HIGH

        # Medium severity for analysis stages
        if stage_name in ["content_analysis", "information_verification", "threat_analysis"] or retry_count >= 2:
            return ErrorSeverity.MEDIUM

        # Low severity for enhancement stages
        if workflow_depth in ["experimental"] and stage_name in [
            "ai_enhanced_quality_assessment",
            "advanced_pattern_recognition",
        ]:
            return ErrorSeverity.LOW

        return ErrorSeverity.MEDIUM

    def _generate_recovery_plan(self, error_context: ErrorContext) -> RecoveryPlan:
        """Generate intelligent recovery plan based on error context."""

        if error_context.severity == ErrorSeverity.CRITICAL:
            return RecoveryPlan(
                strategy=RecoveryStrategy.ABORT_WORKFLOW,
                fallback_agent=None,
                simplified_parameters=None,
                max_retries=0,
                degradation_level="critical",
                continue_workflow=False,
                reason=f"Critical error in {error_context.stage_name}: {error_context.error_message}",
            )

        if error_context.severity == ErrorSeverity.HIGH:
            if error_context.retry_count < 2:
                return RecoveryPlan(
                    strategy=RecoveryStrategy.RETRY,
                    fallback_agent=None,
                    simplified_parameters=self._get_simplified_parameters(error_context),
                    max_retries=2,
                    degradation_level="minimal",
                    continue_workflow=True,
                    reason="High severity error - attempting retry with simplified parameters",
                )
            else:
                return RecoveryPlan(
                    strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
                    fallback_agent=self._get_fallback_agent(error_context),
                    simplified_parameters=None,
                    max_retries=0,
                    degradation_level="significant",
                    continue_workflow=True,
                    reason="High severity error after retries - graceful degradation",
                )

        if error_context.severity == ErrorSeverity.MEDIUM:
            if error_context.retry_count < 3:
                return RecoveryPlan(
                    strategy=RecoveryStrategy.FALLBACK_AGENT,
                    fallback_agent=self._get_fallback_agent(error_context),
                    simplified_parameters=None,
                    max_retries=1,
                    degradation_level="moderate",
                    continue_workflow=True,
                    reason="Medium severity error - using fallback agent",
                )
            else:
                return RecoveryPlan(
                    strategy=RecoveryStrategy.SIMPLIFIED_EXECUTION,
                    fallback_agent=None,
                    simplified_parameters=self._get_simplified_parameters(error_context),
                    max_retries=1,
                    degradation_level="moderate",
                    continue_workflow=True,
                    reason="Medium severity error after retries - simplified execution",
                )

        # Low severity
        return RecoveryPlan(
            strategy=RecoveryStrategy.SIMPLIFIED_EXECUTION,
            fallback_agent=None,
            simplified_parameters=self._get_simplified_parameters(error_context),
            max_retries=1,
            degradation_level="minimal",
            continue_workflow=True,
            reason="Low severity error - simplified execution",
        )

    def _get_fallback_agent(self, error_context: ErrorContext) -> str | None:
        """Get fallback agent for failed stage."""

        fallback_mapping = {
            "multi_platform_acquisition_specialist": "pipeline_tool",
            "comprehensive_linguistic_analyst": "text_analysis_tool",
            "information_verification_director": "fact_check_tool",
            "threat_intelligence_analyst": "deception_scoring_tool",
            "behavioral_profiling_specialist": "character_profile_tool",
            "social_intelligence_coordinator": "social_media_monitor_tool",
            "trend_analysis_scout": "multi_platform_monitor_tool",
            "knowledge_integration_architect": "memory_storage_tool",
            "research_synthesis_specialist": "research_and_brief_tool",
            "intelligence_briefing_director": "perspective_synthesizer_tool",
        }

        return fallback_mapping.get(error_context.agent_name)

    def _get_simplified_parameters(self, error_context: ErrorContext) -> dict[str, Any]:
        """Get simplified parameters for recovery execution."""

        simplified = {
            "reduced_complexity": True,
            "skip_optional_analysis": True,
            "use_cached_results": True,
            "minimal_validation": True,
        }

        if error_context.workflow_depth == "experimental":
            simplified.update(
                {
                    "fallback_to_comprehensive": True,
                    "skip_experimental_features": True,
                }
            )

        if error_context.workflow_depth == "comprehensive":
            simplified.update(
                {
                    "fallback_to_deep": True,
                    "skip_advanced_features": True,
                }
            )

        return simplified

    async def _execute_recovery_strategy(self, error_context: ErrorContext, recovery_plan: RecoveryPlan) -> StepResult:
        """Execute the recovery strategy and return interim result."""

        try:
            if recovery_plan.strategy == RecoveryStrategy.ABORT_WORKFLOW:
                self.recovery_metrics["failed_recoveries"] += 1
                return StepResult.fail(
                    f"Workflow aborted due to critical error: {recovery_plan.reason}",
                    step=f"{error_context.stage_name}_aborted",
                )

            elif recovery_plan.strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
                self.recovery_metrics["degraded_executions"] += 1
                return StepResult.ok(
                    message=f"Stage completed with graceful degradation: {recovery_plan.reason}",
                    degraded_execution=True,
                    degradation_level=recovery_plan.degradation_level,
                    original_error=error_context.error_message,
                    fallback_data=self._generate_fallback_data(error_context),
                )

            elif recovery_plan.strategy in [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.FALLBACK_AGENT,
                RecoveryStrategy.SIMPLIFIED_EXECUTION,
            ]:
                self.recovery_metrics["successful_recoveries"] += 1
                return StepResult.ok(
                    message=f"Recovery strategy applied: {recovery_plan.reason}",
                    recovery_applied=True,
                    recovery_strategy=recovery_plan.strategy.value,
                    fallback_agent=recovery_plan.fallback_agent,
                    simplified_parameters=recovery_plan.simplified_parameters,
                    continue_workflow=recovery_plan.continue_workflow,
                )

            else:
                return StepResult.fail(
                    f"Unknown recovery strategy: {recovery_plan.strategy}",
                    step=f"{error_context.stage_name}_recovery_error",
                )

        except Exception as recovery_execution_error:
            self.recovery_metrics["failed_recoveries"] += 1
            return StepResult.fail(
                f"Recovery execution failed: {recovery_execution_error}",
                step=f"{error_context.stage_name}_recovery_failure",
            )

    def _generate_fallback_data(self, error_context: ErrorContext) -> dict[str, Any]:
        """Generate fallback data when graceful degradation is needed."""

        fallback = {
            "fallback_reason": f"Error in {error_context.stage_name}",
            "error_context": {
                "stage": error_context.stage_name,
                "agent": error_context.agent_name,
                "error_type": error_context.error_type,
            },
            "reduced_confidence": True,
            "requires_manual_review": error_context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL],
        }

        # Stage-specific fallback data
        if error_context.stage_name == "content_analysis":
            fallback.update(
                {
                    "basic_analysis": "Content analysis failed - manual review required",
                    "sentiment": "neutral",
                    "key_topics": ["analysis_failed"],
                }
            )

        elif error_context.stage_name == "information_verification":
            fallback.update(
                {
                    "verification_status": "inconclusive",
                    "confidence_level": 0.1,
                    "requires_verification": True,
                }
            )

        elif error_context.stage_name == "threat_analysis":
            fallback.update(
                {
                    "threat_level": "unknown",
                    "deception_score": 0.5,
                    "requires_assessment": True,
                }
            )

        return fallback

    def _log_error_and_recovery(self, error_context: ErrorContext, recovery_plan: RecoveryPlan) -> None:
        """Log error details and recovery plan for monitoring and debugging."""

        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }[error_context.severity]

        self.logger.log(
            log_level,
            f"Crew Error Handler: Stage={error_context.stage_name}, "
            f"Agent={error_context.agent_name}, Error={error_context.error_type}, "
            f"Severity={error_context.severity.value}, Retry={error_context.retry_count}, "
            f"Recovery={recovery_plan.strategy.value}, Continue={recovery_plan.continue_workflow}",
        )

    def get_recovery_metrics(self) -> dict[str, Any]:
        """Get recovery system performance metrics."""
        total_recoveries = self.recovery_metrics["successful_recoveries"] + self.recovery_metrics["failed_recoveries"]

        return {
            **self.recovery_metrics,
            "total_recoveries": total_recoveries,
            "success_rate": (self.recovery_metrics["successful_recoveries"] / max(total_recoveries, 1)),
            "error_history_count": len(self.error_history),
        }

    def reset_metrics(self) -> None:
        """Reset recovery metrics for fresh tracking."""
        self.recovery_metrics = {
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "degraded_executions": 0,
        }
        self.error_history.clear()
