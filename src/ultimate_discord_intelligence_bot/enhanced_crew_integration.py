"""Enhanced crew integration with comprehensive performance monitoring.

This module provides a seamless integration layer between the existing crew system
and the enhanced performance monitoring capabilities, extending the current tracking
with real-time quality assessment, alerting, and advanced analytics.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

from .crew import UltimateDiscordIntelligenceBotCrew
from .enhanced_performance_monitor import EnhancedPerformanceMonitor
from .performance_integration import PerformanceIntegrationManager
from .services.enterprise_auth_service import get_auth_service
from .services.enterprise_tenant_manager import ResourceType, get_tenant_manager
from .services.hierarchical_orchestrator import HierarchicalOrchestrator
from .services.websocket_integration import get_websocket_integration
from .settings import (
    ENABLE_ENTERPRISE_TENANT_MANAGEMENT,
    ENABLE_HIERARCHICAL_ORCHESTRATION,
    ENABLE_WEBSOCKET_UPDATES,
)

logger = logging.getLogger(__name__)


class EnhancedCrewExecutor:
    """Enhanced crew executor with comprehensive monitoring and quality assessment."""

    def __init__(self, crew_instance: UltimateDiscordIntelligenceBotCrew | None = None):
        """Initialize enhanced crew executor.

        Args:
            crew_instance: Optional existing crew instance. If None, creates new one.
        """
        self.crew_instance = crew_instance or UltimateDiscordIntelligenceBotCrew()
        self.enhanced_monitor = EnhancedPerformanceMonitor()
        self.integration_manager = PerformanceIntegrationManager()

        # Initialize hierarchical orchestrator if enabled
        self.orchestrator = None
        if ENABLE_HIERARCHICAL_ORCHESTRATION:
            self.orchestrator = HierarchicalOrchestrator()
            logger.info(
                "Hierarchical Orchestrator enabled - Phase 2 agent coordination active"
            )

        # Initialize WebSocket integration if enabled
        self.websocket_integration = None
        if ENABLE_WEBSOCKET_UPDATES:
            self.websocket_integration = get_websocket_integration()
            logger.info("WebSocket integration enabled - real-time updates active")

        # Initialize Enterprise services if enabled
        self.tenant_manager = None
        self.auth_service = None
        if ENABLE_ENTERPRISE_TENANT_MANAGEMENT:
            self.tenant_manager = get_tenant_manager()
            self.auth_service = get_auth_service()
            logger.info("Enterprise services enabled - multi-tenant operations active")

        self._execution_context: dict[str, Any] = {}

    async def execute_with_comprehensive_monitoring(
        self,
        inputs: dict[str, Any] | None = None,
        enable_real_time_alerts: bool = True,
        quality_threshold: float = 0.7,
        max_execution_time: float = 300.0,  # 5 minutes
    ) -> dict[str, Any]:
        """Execute crew with comprehensive monitoring and quality assessment.

        Args:
            inputs: Input parameters for crew execution
            enable_real_time_alerts: Whether to enable real-time quality alerts
            quality_threshold: Minimum quality threshold for alerts
            max_execution_time: Maximum execution time before timeout alert

        Returns:
            Dict containing execution results and comprehensive metrics
        """
        execution_id = f"crew_exec_{int(time.time() * 1000)}"
        start_time = time.time()

        try:
            # Initialize execution context
            self._execution_context = {
                "execution_id": execution_id,
                "start_time": start_time,
                "inputs": inputs or {},
                "agents_executed": [],
                "tools_used": [],
                "quality_checkpoints": [],
                "performance_alerts": [],
            }

            # Extract tenant information from inputs
            tenant_id = inputs.get("tenant_id", "default") if inputs else "default"
            workspace_id = inputs.get("workspace_id", "main") if inputs else "main"
            user_id = inputs.get("user_id") if inputs else None

            # Track tenant resource usage
            if self.tenant_manager and tenant_id != "default":
                # Check quota before execution
                quota_check = self.tenant_manager.check_tenant_quota(
                    tenant_id, ResourceType.AGENT_EXECUTIONS, 1.0
                )
                if not quota_check.success or not quota_check.data.get(
                    "sufficient", True
                ):
                    return {
                        "result": None,
                        "execution_summary": "Quota exceeded",
                        "quality_score": 0.0,
                        "execution_time": 0.0,
                        "performance_alerts": ["Tenant quota exceeded"],
                        "error": "Insufficient quota for agent execution",
                    }

                # Update usage
                self.tenant_manager.update_tenant_usage(
                    tenant_id, ResourceType.AGENT_EXECUTIONS, 1.0
                )

            # Notify WebSocket clients about execution start
            if self.websocket_integration:
                await self.websocket_integration.notify_agent_status_change(
                    agent_id="crew_executor",
                    status="starting",
                    details={
                        "execution_id": execution_id,
                        "inputs": inputs or {},
                        "timestamp": start_time,
                    },
                    tenant_id="default",
                    workspace_id="main",
                )

            # Start real-time monitoring
            if enable_real_time_alerts:
                monitor_task = asyncio.create_task(
                    self._real_time_monitoring_loop(
                        execution_id, quality_threshold, max_execution_time
                    )
                )

            # Execute crew with enhanced tracking
            logger.info(f"Starting enhanced crew execution {execution_id}")

            # Override the crew's step callback for enhanced tracking
            original_log_step = self.crew_instance._log_step
            # Store the original method for restoration later
            setattr(self.crew_instance, "_original_log_step", original_log_step)
            # Replace with enhanced callback
            setattr(
                self.crew_instance,
                "_log_step",
                lambda step: self._enhanced_step_callback(step, original_log_step),
            )

            # Execute the crew with optional hierarchical orchestration
            if self.orchestrator:
                # Create orchestration session for hierarchical coordination
                session = await self.orchestrator.create_orchestration_session(
                    mission_context=f"Enhanced crew execution {execution_id}",
                    tenant="default",
                    workspace="main",
                )

                # Register agents in the orchestrator
                await self._register_crew_agents_in_orchestrator(session)

                # Execute with hierarchical coordination
                result = await self._execute_with_hierarchical_orchestration(
                    session, inputs
                )

                # Complete the orchestration session
                await self.orchestrator.complete_orchestration_session(
                    session.session_id
                )
                logger.info(
                    f"Hierarchical orchestration session {session.session_id} completed"
                )
            else:
                # Standard crew execution without orchestration
                result = self.crew_instance.kickoff_with_performance_tracking(inputs)

            end_time = time.time()
            total_execution_time = end_time - start_time

            # Assess overall execution quality
            execution_quality = await self._assess_comprehensive_execution_quality(
                result, total_execution_time
            )

            # Record comprehensive performance data
            await self._record_comprehensive_performance(
                execution_id, result, execution_quality, total_execution_time
            )

            # Generate execution summary
            execution_summary = self._generate_execution_summary(
                execution_id, result, execution_quality, total_execution_time
            )

            # Stop real-time monitoring
            if enable_real_time_alerts:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass

            logger.info(
                f"Enhanced crew execution {execution_id} completed successfully"
            )

            # Notify WebSocket clients about execution completion
            if self.websocket_integration:
                await self.websocket_integration.notify_agent_status_change(
                    agent_id="crew_executor",
                    status="completed",
                    details={
                        "execution_id": execution_id,
                        "execution_time": total_execution_time,
                        "quality_score": execution_quality,
                        "summary": execution_summary,
                    },
                    tenant_id="default",
                    workspace_id="main",
                )

            return {
                "result": result,
                "execution_summary": execution_summary,
                "quality_score": execution_quality,
                "execution_time": total_execution_time,
                "performance_alerts": self._execution_context.get(
                    "performance_alerts", []
                ),
                "quality_checkpoints": self._execution_context.get(
                    "quality_checkpoints", []
                ),
            }

        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time

            # Record failure
            await self._record_execution_failure(execution_id, str(e), execution_time)

            logger.error(f"Enhanced crew execution {execution_id} failed: {e}")

            return {
                "result": None,
                "error": str(e),
                "execution_summary": self._generate_failure_summary(
                    execution_id, str(e), execution_time
                ),
                "quality_score": 0.0,
                "execution_time": execution_time,
                "performance_alerts": self._execution_context.get(
                    "performance_alerts", []
                ),
            }

    def _enhanced_step_callback(
        self, step: Any, original_callback: Callable[[Any], None]
    ) -> None:
        """Enhanced step callback with real-time quality assessment."""
        # Call original callback first
        original_callback(step)

        try:
            # Extract step information
            step_info = self._extract_step_information(step)

            # Record step in execution context
            self._execution_context["agents_executed"].append(step_info["agent_role"])
            if step_info["tool_used"]:
                self._execution_context["tools_used"].append(step_info["tool_used"])

            # Assess step quality
            step_quality = self._assess_step_quality(step_info)

            # Record quality checkpoint
            checkpoint = {
                "timestamp": time.time(),
                "agent": step_info["agent_role"],
                "tool": step_info["tool_used"],
                "quality": step_quality,
                "output_length": len(step_info["output"]) if step_info["output"] else 0,
            }
            self._execution_context["quality_checkpoints"].append(checkpoint)

            # Check for quality alerts
            if step_quality < 0.5:  # Low quality threshold
                alert = {
                    "timestamp": time.time(),
                    "type": "low_step_quality",
                    "agent": step_info["agent_role"],
                    "quality": step_quality,
                    "message": f"Low quality step detected for agent {step_info['agent_role']}",
                }
                self._execution_context["performance_alerts"].append(alert)
                logger.warning(f"Quality alert: {alert['message']}")

        except Exception as e:
            logger.debug(f"Enhanced step callback error: {e}")

    def _extract_step_information(self, step: Any) -> dict[str, Any]:
        """Extract information from a crew execution step."""
        try:
            agent_role = getattr(getattr(step, "agent", None), "role", "unknown")
            tool_used = getattr(step, "tool", None)
            raw_output = getattr(step, "raw", None) or getattr(
                getattr(step, "output", None), "raw", None
            )

            return {
                "agent_role": agent_role,
                "tool_used": str(tool_used) if tool_used else None,
                "output": raw_output if isinstance(raw_output, str) else "",
                "step_object": step,
            }
        except Exception as e:
            logger.debug(f"Step information extraction error: {e}")
            return {
                "agent_role": "unknown",
                "tool_used": None,
                "output": "",
                "step_object": step,
            }

    def _assess_step_quality(self, step_info: dict[str, Any]) -> float:
        """Assess the quality of an individual step."""
        quality_score = 0.5  # Base score

        output = step_info.get("output", "")
        tool_used = step_info.get("tool_used")

        # Content quality assessment
        if output:
            # Length factor
            if len(output) > 100:
                quality_score += 0.1
            elif len(output) > 50:
                quality_score += 0.05

            # Quality indicators
            quality_indicators = [
                "analysis",
                "evidence",
                "conclusion",
                "recommendation",
                "verified",
                "confirmed",
                "research",
                "assessment",
                "because",
                "therefore",
                "indicates",
                "suggests",
            ]

            indicator_count = sum(
                1
                for indicator in quality_indicators
                if indicator.lower() in output.lower()
            )
            quality_score += min(0.2, indicator_count * 0.05)

            # Coherence check (basic)
            sentences = output.split(".")
            if len(sentences) > 1:
                quality_score += 0.1

        # Tool usage factor
        if tool_used:
            quality_score += 0.1
            # Specific tool quality bonuses
            high_quality_tools = [
                "FactCheckTool",
                "LogicalFallacyTool",
                "TruthScoringTool",
                "PerspectiveSynthesizerTool",
                "TextAnalysisTool",
            ]
            if any(tool in tool_used for tool in high_quality_tools):
                quality_score += 0.05

        return min(1.0, quality_score)

    async def _real_time_monitoring_loop(
        self, execution_id: str, quality_threshold: float, max_execution_time: float
    ) -> None:
        """Real-time monitoring loop for execution alerts."""
        start_time = self._execution_context["start_time"]

        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds

                current_time = time.time()
                elapsed_time = current_time - start_time

                # Check execution time
                if elapsed_time > max_execution_time:
                    alert = {
                        "timestamp": current_time,
                        "type": "execution_timeout",
                        "execution_id": execution_id,
                        "elapsed_time": elapsed_time,
                        "message": f"Execution {execution_id} exceeded maximum time ({max_execution_time}s)",
                    }
                    self._execution_context["performance_alerts"].append(alert)
                    logger.warning(f"Timeout alert: {alert['message']}")

                # Check overall quality trend
                checkpoints = self._execution_context.get("quality_checkpoints", [])
                if len(checkpoints) >= 3:
                    recent_quality = sum(cp["quality"] for cp in checkpoints[-3:]) / 3
                    if recent_quality < quality_threshold:
                        alert = {
                            "timestamp": current_time,
                            "type": "quality_decline",
                            "execution_id": execution_id,
                            "recent_quality": recent_quality,
                            "threshold": quality_threshold,
                            "message": f"Quality decline detected: {recent_quality:.2f} < {quality_threshold}",
                        }
                        self._execution_context["performance_alerts"].append(alert)
                        logger.warning(f"Quality alert: {alert['message']}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Real-time monitoring error: {e}")

    async def _assess_comprehensive_execution_quality(
        self, result: Any, execution_time: float
    ) -> float:
        """Assess comprehensive execution quality using enhanced monitoring."""
        try:
            # Base quality from result content
            result_str = str(result) if result else ""
            content_quality = self._assess_result_content_quality(result_str)

            # Quality from execution process
            process_quality = self._assess_execution_process_quality()

            # Time efficiency factor
            time_efficiency = self._assess_time_efficiency(execution_time)

            # Tool usage effectiveness
            tool_effectiveness = self._assess_tool_usage_effectiveness()

            # Weighted combination
            comprehensive_quality = (
                content_quality * 0.4
                + process_quality * 0.3
                + time_efficiency * 0.2
                + tool_effectiveness * 0.1
            )

            return min(1.0, comprehensive_quality)

        except Exception as e:
            logger.debug(f"Comprehensive quality assessment error: {e}")
            return 0.5

    def _assess_result_content_quality(self, result_str: str) -> float:
        """Assess quality of the final result content."""
        if not result_str:
            return 0.0

        quality_score = 0.3  # Base score

        # Length and substance
        if len(result_str) > 500:
            quality_score += 0.3
        elif len(result_str) > 200:
            quality_score += 0.2
        elif len(result_str) > 100:
            quality_score += 0.1

        # Quality indicators
        high_quality_indicators = [
            "analysis",
            "evidence",
            "conclusion",
            "recommendation",
            "verified",
            "confirmed",
            "research",
            "assessment",
            "comprehensive",
            "detailed",
            "thorough",
        ]

        indicator_count = sum(
            1
            for indicator in high_quality_indicators
            if indicator.lower() in result_str.lower()
        )
        quality_score += min(0.3, indicator_count * 0.05)

        # Structure indicators
        structure_indicators = ["introduction", "summary", "conclusion", "findings"]
        structure_count = sum(
            1
            for indicator in structure_indicators
            if indicator.lower() in result_str.lower()
        )
        quality_score += min(0.1, structure_count * 0.03)

        return min(1.0, quality_score)

    def _assess_execution_process_quality(self) -> float:
        """Assess quality of the execution process."""
        checkpoints = self._execution_context.get("quality_checkpoints", [])

        if not checkpoints:
            return 0.5

        # Average step quality
        avg_quality = sum(cp["quality"] for cp in checkpoints) / len(checkpoints)

        # Quality consistency (lower variance is better)
        qualities = [cp["quality"] for cp in checkpoints]
        if len(qualities) > 1:
            variance = sum((q - avg_quality) ** 2 for q in qualities) / len(qualities)
            consistency_bonus = max(0, 0.2 - variance)
        else:
            consistency_bonus = 0.1

        return min(1.0, avg_quality + consistency_bonus)

    def _assess_time_efficiency(self, execution_time: float) -> float:
        """Assess time efficiency of execution."""
        # Efficiency based on reasonable execution time expectations
        if execution_time < 30:  # Very fast
            return 1.0
        elif execution_time < 60:  # Fast
            return 0.9
        elif execution_time < 120:  # Reasonable
            return 0.8
        elif execution_time < 300:  # Acceptable
            return 0.6
        else:  # Slow
            return 0.4

    def _assess_tool_usage_effectiveness(self) -> float:
        """Assess effectiveness of tool usage during execution."""
        tools_used = self._execution_context.get("tools_used", [])

        if not tools_used:
            return 0.5  # No tools used

        # Unique tools diversity bonus
        unique_tools = set(tools_used)
        diversity_score = min(0.3, len(unique_tools) * 0.1)

        # High-value tools bonus
        high_value_tools = [
            "FactCheckTool",
            "LogicalFallacyTool",
            "TruthScoringTool",
            "PerspectiveSynthesizerTool",
            "TextAnalysisTool",
            "PipelineTool",
        ]

        high_value_count = sum(
            1 for tool in tools_used if any(hv in tool for hv in high_value_tools)
        )
        value_score = min(0.4, high_value_count * 0.1)

        return min(1.0, 0.3 + diversity_score + value_score)

    async def _record_comprehensive_performance(
        self,
        execution_id: str,
        result: Any,
        quality_score: float,
        execution_time: float,
    ) -> None:
        """Record comprehensive performance data."""
        try:
            # Record in enhanced monitor
            await self.enhanced_monitor.monitor_real_time_performance(
                agent_name="crew_orchestrator",
                interaction_data={
                    "interaction_type": "comprehensive_execution",
                    "quality_score": quality_score,
                    "response_time": execution_time,
                    "execution_id": execution_id,
                    "agents_count": len(
                        set(self._execution_context.get("agents_executed", []))
                    ),
                    "tools_count": len(
                        set(self._execution_context.get("tools_used", []))
                    ),
                    "quality_checkpoints": len(
                        self._execution_context.get("quality_checkpoints", [])
                    ),
                    "performance_alerts": len(
                        self._execution_context.get("performance_alerts", [])
                    ),
                    "result_length": len(str(result)) if result else 0,
                    "execution_context": self._execution_context,
                },
            )

            # Record in integration manager (method not yet implemented)
            # await self.integration_manager.track_crew_execution(
            #     execution_id=execution_id,
            #     agents_used=list(set(self._execution_context.get("agents_executed", []))),
            #     tools_used=list(set(self._execution_context.get("tools_used", []))),
            #     quality_score=quality_score,
            #     execution_time=execution_time,
            #     result=result,
            # )

        except Exception as e:
            logger.debug(f"Performance recording error: {e}")

    async def _record_execution_failure(
        self, execution_id: str, error_message: str, execution_time: float
    ) -> None:
        """Record execution failure data."""
        try:
            await self.enhanced_monitor.record_interaction_async(
                agent_name="crew_orchestrator",
                interaction_type="failed_execution",
                quality_score=0.0,
                response_time=execution_time,
                context={
                    "execution_id": execution_id,
                    "error": error_message,
                    "execution_context": self._execution_context,
                },
            )
        except Exception as e:
            logger.debug(f"Failure recording error: {e}")

    def _generate_execution_summary(
        self,
        execution_id: str,
        result: Any,
        quality_score: float,
        execution_time: float,
    ) -> dict[str, Any]:
        """Generate comprehensive execution summary."""
        return {
            "execution_id": execution_id,
            "execution_time": execution_time,
            "quality_score": quality_score,
            "agents_executed": list(
                set(self._execution_context.get("agents_executed", []))
            ),
            "tools_used": list(set(self._execution_context.get("tools_used", []))),
            "quality_checkpoints_count": len(
                self._execution_context.get("quality_checkpoints", [])
            ),
            "performance_alerts_count": len(
                self._execution_context.get("performance_alerts", [])
            ),
            "result_summary": {
                "has_result": result is not None,
                "result_length": len(str(result)) if result else 0,
                "result_type": type(result).__name__ if result else "None",
            },
            "performance_insights": self._generate_performance_insights(),
        }

    def _generate_failure_summary(
        self, execution_id: str, error_message: str, execution_time: float
    ) -> dict[str, Any]:
        """Generate summary for failed execution."""
        return {
            "execution_id": execution_id,
            "execution_time": execution_time,
            "error": error_message,
            "agents_attempted": list(
                set(self._execution_context.get("agents_executed", []))
            ),
            "tools_attempted": list(set(self._execution_context.get("tools_used", []))),
            "failure_analysis": self._analyze_failure_context(),
        }

    def _generate_performance_insights(self) -> dict[str, Any]:
        """Generate insights from execution performance data."""
        checkpoints = self._execution_context.get("quality_checkpoints", [])
        alerts = self._execution_context.get("performance_alerts", [])

        insights = {
            "quality_trend": "stable",
            "efficiency_rating": "good",
            "tool_usage_pattern": "balanced",
            "recommendations": [],
        }

        if checkpoints:
            qualities = [cp["quality"] for cp in checkpoints]
            if len(qualities) > 2:
                if qualities[-1] > qualities[0]:
                    insights["quality_trend"] = "improving"
                elif qualities[-1] < qualities[0]:
                    insights["quality_trend"] = "declining"

        if alerts:
            if any(alert["type"] == "execution_timeout" for alert in alerts):
                insights["efficiency_rating"] = "poor"
                insights["recommendations"].append(
                    "Consider optimizing agent workflows to reduce execution time"
                )
            elif any(alert["type"] == "quality_decline" for alert in alerts):
                insights["efficiency_rating"] = "fair"
                insights["recommendations"].append(
                    "Monitor agent performance for quality consistency"
                )

        return insights

    def _analyze_failure_context(self) -> dict[str, Any]:
        """Analyze context around execution failure."""
        return {
            "checkpoints_before_failure": len(
                self._execution_context.get("quality_checkpoints", [])
            ),
            "alerts_before_failure": len(
                self._execution_context.get("performance_alerts", [])
            ),
            "last_successful_agent": (
                self._execution_context.get("agents_executed", [])[-1]
                if self._execution_context.get("agents_executed")
                else None
            ),
            "failure_stage": self._determine_failure_stage(),
        }

    def _determine_failure_stage(self) -> str:
        """Determine at what stage the execution failed."""
        agents_count = len(self._execution_context.get("agents_executed", []))
        tools_count = len(self._execution_context.get("tools_used", []))

        if agents_count == 0:
            return "initialization"
        elif tools_count == 0:
            return "agent_setup"
        elif agents_count < 3:
            return "early_execution"
        else:
            return "mid_execution"

    async def _register_crew_agents_in_orchestrator(self, session) -> None:
        """Register crew agents in the hierarchical orchestrator."""
        if not self.orchestrator:
            return

        logger.info(
            f"Registering crew agents in orchestrator session {session.session_id}"
        )

        # Get crew agents and register them
        crew_agents = self.crew_instance.crew().agents

        for agent in crew_agents:
            await self.orchestrator.register_agent(
                session.session_id,
                agent_id=agent.role.lower().replace(" ", "_"),
                role=agent.role,
                capabilities=[tool.name for tool in agent.tools],
                max_concurrent_tasks=3,
            )

        logger.info(f"Registered {len(crew_agents)} agents in orchestrator")

    async def _execute_with_hierarchical_orchestration(
        self, session, inputs: dict[str, Any]
    ) -> Any:
        """Execute crew with hierarchical orchestration coordination."""
        if not self.orchestrator:
            return self.crew_instance.kickoff_with_performance_tracking(inputs)

        logger.info(
            f"Executing crew with hierarchical orchestration - session {session.session_id}"
        )

        try:
            # Create orchestration tasks based on inputs
            orchestration_tasks = []

            # Create main execution task
            main_task = await self.orchestrator.create_orchestration_task(
                session.session_id,
                task_id="main_execution",
                description=f"Execute crew with inputs: {inputs}",
                priority=1,
                estimated_duration=300,  # 5 minutes
                dependencies=[],
            )
            orchestration_tasks.append(main_task)

            # Execute tasks through orchestrator
            results = []
            for task in orchestration_tasks:
                result = await self.orchestrator.execute_orchestration_task(
                    session.session_id, task.task_id
                )
                results.append(result)

            # For now, fall back to standard crew execution
            # TODO: Implement full hierarchical task execution
            return self.crew_instance.kickoff_with_performance_tracking(inputs)

        except Exception as e:
            logger.error(f"Hierarchical orchestration execution failed: {e}")
            # Fall back to standard execution
            return self.crew_instance.kickoff_with_performance_tracking(inputs)


@contextmanager
def enhanced_crew_execution(
    crew_instance: UltimateDiscordIntelligenceBotCrew | None = None,
    **monitoring_options,
):
    """Context manager for enhanced crew execution with comprehensive monitoring.

    Args:
        crew_instance: Optional crew instance
        **monitoring_options: Additional monitoring configuration options

    Usage:
        with enhanced_crew_execution() as executor:
            result = await executor.execute_with_comprehensive_monitoring(inputs)
    """
    executor = EnhancedCrewExecutor(crew_instance)
    try:
        yield executor
    finally:
        # Cleanup if needed
        pass


# Convenience functions for common use cases
async def execute_crew_with_quality_monitoring(
    inputs: dict[str, Any] | None = None,
    quality_threshold: float = 0.7,
    enable_alerts: bool = True,
) -> dict[str, Any]:
    """Convenience function for executing crew with quality monitoring.

    Args:
        inputs: Input parameters for crew execution
        quality_threshold: Minimum quality threshold for alerts
        enable_alerts: Whether to enable real-time alerts

    Returns:
        Dict containing execution results and comprehensive metrics
    """
    executor = EnhancedCrewExecutor()
    return await executor.execute_with_comprehensive_monitoring(
        inputs=inputs,
        enable_real_time_alerts=enable_alerts,
        quality_threshold=quality_threshold,
    )


def create_enhanced_crew_executor() -> EnhancedCrewExecutor:
    """Create a new enhanced crew executor instance.

    Returns:
        Configured EnhancedCrewExecutor instance
    """
    return EnhancedCrewExecutor()
