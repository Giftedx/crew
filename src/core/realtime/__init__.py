"""
Real-time processing capabilities for the Ultimate Discord Intelligence Bot.

This module provides comprehensive real-time content processing including:
- Stream processing with concurrent multi-source analysis
- Live content monitoring with intelligent alerts
- Real-time fact-checking with automated verification
- Performance optimization and adaptive processing
"""

from .fact_checker import (
    ClaimType,
    ConfidenceLevel,
    FactCheckAlert,
    FactualClaim,
    RealTimeFactChecker,
    VerificationResult,
    VerificationSource,
    VerificationStatus,
    extract_claims,
    get_global_fact_checker,
    set_global_fact_checker,
    verify_claim,
    verify_content_stream,
)
from .live_monitor import (
    AlertLevel,
    LiveContentMetrics,
    LiveMonitor,
    MonitoringAlert,
    MonitoringRule,
    MonitorType,
    TrendData,
    TrendDirection,
    get_active_alerts,
    get_global_live_monitor,
    set_global_live_monitor,
    start_monitoring,
    update_metrics,
)
from .stream_processor import (
    ProcessingPriority,
    ProcessingResult,
    StreamChunk,
    StreamMetadata,
    StreamProcessor,
    StreamProcessorConfig,
    StreamStatus,
    StreamType,
    add_chunk,
    get_global_stream_processor,
    get_processing_results,
    set_global_stream_processor,
    start_stream,
    stop_stream,
)


__all__ = [
    "AlertLevel",
    "ClaimType",
    "ConfidenceLevel",
    "FactCheckAlert",
    "FactualClaim",
    "LiveContentMetrics",
    # Live monitoring
    "LiveMonitor",
    "MonitorType",
    "MonitoringAlert",
    "MonitoringRule",
    "ProcessingPriority",
    "ProcessingResult",
    # Fact checking
    "RealTimeFactChecker",
    "StreamChunk",
    "StreamMetadata",
    # Stream processing
    "StreamProcessor",
    "StreamProcessorConfig",
    "StreamStatus",
    "StreamType",
    "TrendData",
    "TrendDirection",
    "VerificationResult",
    "VerificationSource",
    "VerificationStatus",
    "add_chunk",
    "extract_claims",
    "get_active_alerts",
    "get_global_fact_checker",
    "get_global_live_monitor",
    "get_global_stream_processor",
    "get_processing_results",
    "set_global_fact_checker",
    "set_global_live_monitor",
    "set_global_stream_processor",
    "start_monitoring",
    "start_stream",
    "stop_stream",
    "update_metrics",
    "verify_claim",
    "verify_content_stream",
]
