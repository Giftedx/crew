"""
Live Monitoring Agent for Real-Time Trend Detection and Fact-Checking

This agent coordinates real-time monitoring of live content streams, providing
intelligent trend detection, fact-checking alerts, and automated response capabilities.
It integrates with the live monitor, stream processor, and analysis tools to provide
comprehensive real-time intelligence.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)
from platform.core.step_result import StepResult
from platform.realtime.live_monitor import (
    AlertLevel,
    LiveContentMetrics,
    LiveMonitor,
    MonitoringAlert,
    MonitoringRule,
    MonitorType,
    TrendData,
)
from platform.realtime.stream_processor import (
    ProcessingPriority,
    ProcessingResult,
    StreamChunk,
    StreamProcessor,
    StreamType,
)

from domains.intelligence.analysis.live_stream_analysis_tool import LiveStreamAnalysisTool


class MonitoringMode(Enum):
    """Monitoring mode enumeration."""

    PASSIVE = "passive"
    ACTIVE = "active"
    INTELLIGENT = "intelligent"


class TrendCategory(Enum):
    """Trend category enumeration."""

    VIRAL_CONTENT = "viral_content"
    CONTROVERSIAL_TOPIC = "controversial_topic"
    FACT_CHECK_OPPORTUNITY = "fact_check_opportunity"
    ENGAGEMENT_SPIKE = "engagement_spike"
    SENTIMENT_SHIFT = "sentiment_shift"
    QUALITY_DEGRADATION = "quality_degradation"


@dataclass
class LiveMonitoringSession:
    """Live monitoring session with configuration and state."""

    session_id: str
    stream_id: str
    stream_type: StreamType
    monitoring_mode: MonitoringMode
    start_time: float
    end_time: float | None = None
    status: str = "active"
    configuration: dict[str, Any] = field(default_factory=dict)
    metrics: list[LiveContentMetrics] = field(default_factory=list)
    alerts: list[MonitoringAlert] = field(default_factory=list)
    trends: list[TrendData] = field(default_factory=list)
    tenant: str = "default"
    workspace: str = "default"

    @property
    def is_active(self) -> bool:
        """Check if session is active."""
        return self.status == "active" and self.end_time is None

    @property
    def duration_seconds(self) -> float:
        """Get session duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time


@dataclass
class TrendAlert:
    """Trend alert with detailed information."""

    alert_id: str
    trend_category: TrendCategory
    confidence: float
    description: str
    timestamp: float
    stream_id: str
    impact_score: float
    recommended_actions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FactCheckAlert:
    """Fact-checking alert with verification details."""

    alert_id: str
    claim: str
    confidence: float
    source_context: str
    timestamp: float
    stream_id: str
    verification_status: str = "pending"
    suggested_response: str = ""
    priority: str = "medium"
    metadata: dict[str, Any] = field(default_factory=dict)


class LiveMonitoringAgent:
    """
    Live Monitoring Agent for real-time trend detection and fact-checking.

    This agent provides comprehensive real-time monitoring capabilities including:
    - Intelligent trend detection and analysis
    - Real-time fact-checking alerts
    - Automated response recommendations
    - Multi-stream monitoring coordination
    - Performance optimization and learning
    """

    def __init__(self):
        """Initialize the Live Monitoring Agent."""
        self.live_monitor = LiveMonitor()
        self.stream_processor = StreamProcessor()
        self.live_stream_analysis_tool = LiveStreamAnalysisTool()
        self.active_sessions: dict[str, LiveMonitoringSession] = {}
        self.trend_alerts: list[TrendAlert] = []
        self.fact_check_alerts: list[FactCheckAlert] = []
        self.performance_metrics = {
            "total_sessions": 0,
            "active_sessions": 0,
            "trends_detected": 0,
            "fact_checks_triggered": 0,
            "average_response_time": 0.0,
        }
        self.agent = None
        logger.info("Live Monitoring Agent initialized")

    async def start_monitoring_session(
        self,
        stream_id: str,
        stream_type: StreamType,
        monitoring_mode: MonitoringMode = MonitoringMode.INTELLIGENT,
        configuration: dict[str, Any] | None = None,
        tenant: str = "default",
        workspace: str = "default",
    ) -> StepResult:
        """
        Start a new live monitoring session.

        Args:
            stream_id: Unique identifier for the stream
            stream_type: Type of content stream
            monitoring_mode: Monitoring mode (passive, active, intelligent)
            configuration: Session configuration
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with session information
        """
        try:
            session_id = str(uuid.uuid4())
            session = LiveMonitoringSession(
                session_id=session_id,
                stream_id=stream_id,
                stream_type=stream_type,
                monitoring_mode=monitoring_mode,
                start_time=time.time(),
                configuration=configuration or {},
                tenant=tenant,
                workspace=workspace,
            )
            stream_metadata = await self.stream_processor.start_stream(
                stream_id=stream_id,
                stream_type=stream_type,
                source_url=configuration.get("source_url", ""),
                title=configuration.get("title", f"Stream {stream_id}"),
                description=configuration.get("description", ""),
                priority=ProcessingPriority.HIGH
                if monitoring_mode == MonitoringMode.INTELLIGENT
                else ProcessingPriority.NORMAL,
            )
            await self.live_monitor.start_monitoring(stream_id)
            await self._setup_monitoring_rules(session)
            self.active_sessions[session_id] = session
            self.performance_metrics["total_sessions"] += 1
            self.performance_metrics["active_sessions"] += 1
            logger.info(f"Started monitoring session {session_id} for stream {stream_id}")
            return StepResult.success(
                {
                    "session_id": session_id,
                    "stream_id": stream_id,
                    "monitoring_mode": monitoring_mode.value,
                    "status": "active",
                    "stream_metadata": stream_metadata.__dict__,
                    "tenant": tenant,
                    "workspace": workspace,
                }
            )
        except Exception as e:
            logger.error(f"Failed to start monitoring session: {e!s}")
            return StepResult.fail(f"Failed to start monitoring session: {e!s}")

    async def stop_monitoring_session(self, session_id: str) -> StepResult:
        """
        Stop a monitoring session.

        Args:
            session_id: Session identifier

        Returns:
            StepResult with session summary
        """
        try:
            if session_id not in self.active_sessions:
                return StepResult.fail(f"Session {session_id} not found")
            session = self.active_sessions[session_id]
            session.end_time = time.time()
            session.status = "completed"
            await self.stream_processor.stop_stream(session.stream_id)
            await self.live_monitor.stop_monitoring(session.stream_id)
            summary = await self._generate_session_summary(session)
            self.performance_metrics["active_sessions"] -= 1
            logger.info(f"Stopped monitoring session {session_id}")
            return StepResult.success(
                {
                    "session_id": session_id,
                    "status": "completed",
                    "duration_seconds": session.duration_seconds,
                    "summary": summary,
                }
            )
        except Exception as e:
            logger.error(f"Failed to stop monitoring session: {e!s}")
            return StepResult.fail(f"Failed to stop monitoring session: {e!s}")

    async def process_stream_chunk(self, session_id: str, chunk: StreamChunk) -> StepResult:
        """
        Process a stream chunk for real-time analysis.

        Args:
            session_id: Session identifier
            chunk: Stream chunk to process

        Returns:
            StepResult with processing results
        """
        try:
            if session_id not in self.active_sessions:
                return StepResult.fail(f"Session {session_id} not found")
            session = self.active_sessions[session_id]
            if not session.is_active:
                return StepResult.fail(f"Session {session_id} is not active")
            await self.stream_processor.add_chunk(session.stream_id, chunk)
            results = await self.stream_processor.get_processing_results(session.stream_id)
            latest_result = results[-1] if results else None
            if latest_result:
                metrics = self._create_metrics_from_result(latest_result, session)
                session.metrics.append(metrics)
                await self.live_monitor.update_metrics(session.stream_id, metrics)
                await self._check_for_trends_and_alerts(session, latest_result)
            return StepResult.success(
                {
                    "session_id": session_id,
                    "chunk_processed": True,
                    "processing_result": latest_result.__dict__ if latest_result else None,
                }
            )
        except Exception as e:
            logger.error(f"Failed to process stream chunk: {e!s}")
            return StepResult.fail(f"Failed to process stream chunk: {e!s}")

    async def get_trend_analysis(self, session_id: str, metric_name: str | None = None) -> StepResult:
        """
        Get trend analysis for a monitoring session.

        Args:
            session_id: Session identifier
            metric_name: Specific metric to analyze (optional)

        Returns:
            StepResult with trend analysis
        """
        try:
            if session_id not in self.active_sessions:
                return StepResult.fail(f"Session {session_id} not found")
            session = self.active_sessions[session_id]
            if metric_name:
                trend_data = await self.live_monitor.get_trend_analysis(session.stream_id, metric_name)
                trends = [trend_data] if trend_data else []
            else:
                trends = []
                for metric in ["viewer_count", "engagement_rate", "sentiment_score", "content_quality"]:
                    trend = await self.live_monitor.get_trend_analysis(session.stream_id, metric)
                    if trend:
                        trends.append(trend)
            return StepResult.success(
                {
                    "session_id": session_id,
                    "trends": [trend.__dict__ for trend in trends],
                    "analysis_timestamp": time.time(),
                }
            )
        except Exception as e:
            logger.error(f"Failed to get trend analysis: {e!s}")
            return StepResult.fail(f"Failed to get trend analysis: {e!s}")

    async def get_active_alerts(self, session_id: str | None = None, alert_type: str | None = None) -> StepResult:
        """
        Get active alerts for monitoring sessions.

        Args:
            session_id: Specific session (optional)
            alert_type: Type of alerts to filter (optional)

        Returns:
            StepResult with active alerts
        """
        try:
            alerts = []
            if session_id:
                if session_id not in self.active_sessions:
                    return StepResult.fail(f"Session {session_id} not found")
                session = self.active_sessions[session_id]
                monitoring_alerts = await self.live_monitor.get_active_alerts(session.stream_id)
                alerts.extend([alert.__dict__ for alert in monitoring_alerts])
                if not alert_type or alert_type == "trend":
                    trend_alerts = [alert for alert in self.trend_alerts if alert.stream_id == session.stream_id]
                    alerts.extend([alert.__dict__ for alert in trend_alerts])
                if not alert_type or alert_type == "fact_check":
                    fact_alerts = [alert for alert in self.fact_check_alerts if alert.stream_id == session.stream_id]
                    alerts.extend([alert.__dict__ for alert in fact_alerts])
            else:
                monitoring_alerts = await self.live_monitor.get_active_alerts()
                alerts.extend([alert.__dict__ for alert in monitoring_alerts])
                alerts.extend([alert.__dict__ for alert in self.trend_alerts])
                alerts.extend([alert.__dict__ for alert in self.fact_check_alerts])
            return StepResult.success({"alerts": alerts, "total_count": len(alerts), "timestamp": time.time()})
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e!s}")
            return StepResult.fail(f"Failed to get active alerts: {e!s}")

    async def _setup_monitoring_rules(self, session: LiveMonitoringSession) -> None:
        """Set up monitoring rules for a session."""
        rules = []
        rules.append(
            MonitoringRule(
                rule_id=f"{session.session_id}_sentiment",
                monitor_type=MonitorType.SENTIMENT_MONITORING,
                name="Sentiment Monitoring",
                description="Monitor sentiment trends",
                condition="sentiment_score < 0.3",
                threshold=0.3,
                alert_level=AlertLevel.WARNING,
            )
        )
        rules.append(
            MonitoringRule(
                rule_id=f"{session.session_id}_quality",
                monitor_type=MonitorType.QUALITY_MONITORING,
                name="Content Quality Monitoring",
                description="Monitor content quality",
                condition="content_quality < 0.6",
                threshold=0.6,
                alert_level=AlertLevel.WARNING,
            )
        )
        rules.append(
            MonitoringRule(
                rule_id=f"{session.session_id}_engagement",
                monitor_type=MonitorType.AUDIENCE_ENGAGEMENT,
                name="Engagement Monitoring",
                description="Monitor audience engagement",
                condition="engagement_rate < 0.2",
                threshold=0.2,
                alert_level=AlertLevel.INFO,
            )
        )
        for rule in rules:
            self.live_monitor.add_monitoring_rule(rule)

    def _create_metrics_from_result(
        self, result: ProcessingResult, session: LiveMonitoringSession
    ) -> LiveContentMetrics:
        """Create metrics from processing result."""
        result_data = result.result_data
        return LiveContentMetrics(
            stream_id=session.stream_id,
            timestamp=time.time(),
            viewer_count=result_data.get("viewer_count", 0),
            engagement_rate=result_data.get("engagement_rate", 0.0),
            sentiment_score=result_data.get("sentiment_score", 0.5),
            content_quality=result_data.get("content_quality", 0.8),
            fact_check_accuracy=result_data.get("fact_check_accuracy", 0.9),
            moderation_flags=result_data.get("moderation_flags", 0),
            performance_score=result_data.get("performance_score", 0.8),
            metadata=result_data.get("metadata", {}),
        )

    async def _check_for_trends_and_alerts(self, session: LiveMonitoringSession, result: ProcessingResult) -> None:
        """Check for trends and generate alerts."""
        if result.result_data.get("engagement_rate", 0) > 0.8:
            trend_alert = TrendAlert(
                alert_id=str(uuid.uuid4()),
                trend_category=TrendCategory.VIRAL_CONTENT,
                confidence=0.9,
                description="High engagement detected - potential viral content",
                timestamp=time.time(),
                stream_id=session.stream_id,
                impact_score=0.8,
                recommended_actions=["Monitor closely", "Prepare response strategy"],
            )
            self.trend_alerts.append(trend_alert)
            self.performance_metrics["trends_detected"] += 1
        if result.result_data.get("fact_check_opportunity", False):
            fact_alert = FactCheckAlert(
                alert_id=str(uuid.uuid4()),
                claim=result.result_data.get("claim", ""),
                confidence=0.7,
                source_context=result.result_data.get("context", ""),
                timestamp=time.time(),
                stream_id=session.stream_id,
                verification_status="pending",
                suggested_response="Verify claim with reliable sources",
                priority="high",
            )
            self.fact_check_alerts.append(fact_alert)
            self.performance_metrics["fact_checks_triggered"] += 1

    async def _generate_session_summary(self, session: LiveMonitoringSession) -> dict[str, Any]:
        """Generate a summary of the monitoring session."""
        return {
            "session_id": session.session_id,
            "stream_id": session.stream_id,
            "duration_seconds": session.duration_seconds,
            "total_metrics": len(session.metrics),
            "total_alerts": len(session.alerts),
            "trends_detected": len([a for a in self.trend_alerts if a.stream_id == session.stream_id]),
            "fact_checks_triggered": len([a for a in self.fact_check_alerts if a.stream_id == session.stream_id]),
            "monitoring_mode": session.monitoring_mode.value,
            "performance_summary": {
                "average_engagement": sum(m.engagement_rate for m in session.metrics) / max(1, len(session.metrics)),
                "average_sentiment": sum(m.sentiment_score for m in session.metrics) / max(1, len(session.metrics)),
                "average_quality": sum(m.content_quality for m in session.metrics) / max(1, len(session.metrics)),
            },
        }

    async def get_agent_status(self) -> StepResult:
        """Get the current status of the live monitoring agent."""
        try:
            return StepResult.success(
                {
                    "agent_type": "LiveMonitoringAgent",
                    "status": "active",
                    "active_sessions": len(self.active_sessions),
                    "performance_metrics": self.performance_metrics,
                    "monitoring_statistics": await self.live_monitor.get_monitoring_statistics(),
                    "stream_statistics": await self.stream_processor.get_stream_statistics(),
                }
            )
        except Exception as e:
            logger.error(f"Failed to get agent status: {e!s}")
            return StepResult.fail(f"Failed to get agent status: {e!s}")
