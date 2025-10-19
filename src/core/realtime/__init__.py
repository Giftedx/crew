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
    # Stream processing
    "StreamProcessor",
    "StreamProcessorConfig",
    "StreamMetadata",
    "StreamChunk",
    "StreamType",
    "StreamStatus",
    "ProcessingPriority",
    "ProcessingResult",
    "start_stream",
    "add_chunk",
    "stop_stream",
    "get_processing_results",
    "get_global_stream_processor",
    "set_global_stream_processor",
    # Live monitoring
    "LiveMonitor",
    "MonitoringRule",
    "MonitoringAlert",
    "MonitorType",
    "AlertLevel",
    "LiveContentMetrics",
    "TrendData",
    "TrendDirection",
    "start_monitoring",
    "update_metrics",
    "get_active_alerts",
    "get_global_live_monitor",
    "set_global_live_monitor",
    # Fact checking
    "RealTimeFactChecker",
    "FactualClaim",
    "VerificationResult",
    "VerificationSource",
    "ClaimType",
    "VerificationStatus",
    "ConfidenceLevel",
    "FactCheckAlert",
    "verify_content_stream",
    "extract_claims",
    "verify_claim",
    "get_global_fact_checker",
    "set_global_fact_checker",
]
