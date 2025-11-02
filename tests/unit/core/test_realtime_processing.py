"""
Comprehensive test suite for real-time processing capabilities.

Tests stream processing, live content monitoring, and real-time fact-checking functionality.
"""
import pytest
from platform.core.realtime import AlertLevel, ClaimType, ConfidenceLevel, FactualClaim, LiveContentMetrics, LiveMonitor, MonitoringAlert, MonitoringRule, MonitorType, ProcessingResult, RealTimeFactChecker, StreamChunk, StreamProcessor, StreamStatus, StreamType, TrendData, TrendDirection, VerificationResult, VerificationSource, VerificationStatus, get_global_fact_checker, get_global_live_monitor, get_global_stream_processor, set_global_fact_checker, set_global_live_monitor, set_global_stream_processor

class TestStreamChunk:
    """Test StreamChunk dataclass."""

    def test_stream_chunk_creation(self) -> None:
        """Test StreamChunk creation and properties."""
        chunk = StreamChunk(stream_id='test_stream', chunk_id='chunk_001', content_type='audio', data=b'test audio data', timestamp=1234567890.0)
        assert chunk.stream_id == 'test_stream'
        assert chunk.chunk_id == 'chunk_001'
        assert chunk.content_type == 'audio'
        assert chunk.data == b'test audio data'
        assert chunk.timestamp == 1234567890.0
        assert chunk.is_audio is True
        assert chunk.is_video is False
        assert chunk.is_text is False

    def test_stream_chunk_properties(self) -> None:
        """Test StreamChunk property methods."""
        chunk = StreamChunk(stream_id='test_stream', chunk_id='chunk_001', content_type='video', data=b'test video data', timestamp=1234567890.0)
        assert chunk.is_video is True
        assert chunk.size_bytes == len(b'test video data')

class TestStreamStatus:
    """Test StreamStatus enum."""

    def test_stream_status_values(self) -> None:
        """Test StreamStatus enum values."""
        assert StreamStatus.PROCESSING.value == 'processing'
        assert StreamStatus.CONNECTED.value == 'connected'
        assert StreamStatus.ERROR.value == 'error'

class TestProcessingResult:
    """Test ProcessingResult dataclass."""

    def test_processing_result_creation(self) -> None:
        """Test ProcessingResult creation and properties."""
        result = ProcessingResult(chunk_id='chunk_001', stream_id='test_stream', processing_time=1.5, success=True, confidence=0.95)
        assert result.chunk_id == 'chunk_001'
        assert result.stream_id == 'test_stream'
        assert result.processing_time == 1.5
        assert result.success is True
        assert result.confidence == 0.95
        assert result.is_successful is True
        assert result.has_high_confidence is True

    def test_processing_result_confidence_threshold(self) -> None:
        """Test ProcessingResult confidence threshold logic."""
        high_confidence = ProcessingResult(chunk_id='chunk_001', stream_id='test_stream', processing_time=1.0, success=True, confidence=0.95)
        low_confidence = ProcessingResult(chunk_id='chunk_001', stream_id='test_stream', processing_time=1.0, success=True, confidence=0.5)
        assert high_confidence.has_high_confidence is True
        assert low_confidence.has_high_confidence is False

class TestStreamProcessor:
    """Test StreamProcessor functionality."""

    @pytest.fixture
    def processor(self) -> StreamProcessor:
        """Create StreamProcessor instance for testing."""
        return StreamProcessor()

    def test_processor_initialization(self, processor: StreamProcessor) -> None:
        """Test StreamProcessor initialization."""
        assert len(processor.active_streams) == 0
        assert processor.performance_metrics['total_chunks_processed'] == 0

    @pytest.mark.asyncio
    async def test_start_stream(self, processor: StreamProcessor) -> None:
        """Test starting a stream."""
        result = await processor.start_stream('test_stream', StreamType.GENERIC_AUDIO, 'https://example.com/stream', 'Test Stream')
        assert result.stream_id == 'test_stream'
        assert 'test_stream' in processor.active_streams

    @pytest.mark.asyncio
    async def test_add_chunk(self, processor: StreamProcessor) -> None:
        """Test adding a chunk to a stream."""
        await processor.start_stream('test_stream', StreamType.GENERIC_AUDIO, 'https://example.com/stream', 'Test Stream')
        chunk = StreamChunk(stream_id='test_stream', chunk_id='chunk_001', content_type='audio', data=b'test audio data', timestamp=1234567890.0)
        result = await processor.add_chunk('test_stream', chunk)
        assert result is True

    @pytest.mark.asyncio
    async def test_stop_stream(self, processor: StreamProcessor) -> None:
        """Test stopping a stream."""
        await processor.start_stream('test_stream', StreamType.GENERIC_AUDIO, 'https://example.com/stream', 'Test Stream')
        result = await processor.stop_stream('test_stream')
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_stream_status(self, processor: StreamProcessor) -> None:
        """Test getting stream status."""
        await processor.start_stream('test_stream', StreamType.GENERIC_AUDIO, 'https://example.com/stream', 'Test Stream')
        status = await processor.get_stream_status('test_stream')
        assert status is not None

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, processor: StreamProcessor) -> None:
        """Test getting performance metrics."""
        metrics = await processor.get_performance_metrics()
        assert 'throughput_chunks_per_second' in metrics

    @pytest.mark.asyncio
    async def test_get_processing_results(self, processor: StreamProcessor) -> None:
        """Test getting processing results."""
        await processor.start_stream('test_stream', StreamType.GENERIC_AUDIO, 'https://example.com/stream', 'Test Stream')
        results = await processor.get_processing_results('test_stream')
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_context_manager(self, processor: StreamProcessor) -> None:
        """Test StreamProcessor as context manager."""
        async with processor:
            await processor.start_stream('test_stream', StreamType.GENERIC_AUDIO, 'https://example.com/stream', 'Test Stream')
            assert 'test_stream' in processor.active_streams

    @pytest.mark.asyncio
    async def test_error_handling(self, processor: StreamProcessor) -> None:
        """Test error handling in stream processing."""
        await processor.start_stream('test_stream', StreamType.GENERIC_AUDIO, 'https://example.com/stream', 'Test Stream')
        invalid_chunk = StreamChunk(stream_id='nonexistent_stream', chunk_id='chunk_001', content_type='audio', data=b'test data', timestamp=1234567890.0)
        result = await processor.add_chunk('nonexistent_stream', invalid_chunk)
        assert result is False

class TestMonitoringRule:
    """Test MonitoringRule dataclass."""

    def test_monitoring_rule_creation(self) -> None:
        """Test MonitoringRule creation and properties."""
        rule = MonitoringRule(rule_id='test_rule', monitor_type=MonitorType.SENTIMENT_MONITORING, name='Test Rule', description='Test monitoring rule', condition='sentiment_score < 0.3', threshold=0.8, alert_level=AlertLevel.WARNING)
        assert rule.rule_id == 'test_rule'
        assert rule.monitor_type == MonitorType.SENTIMENT_MONITORING
        assert rule.name == 'Test Rule'
        assert rule.description == 'Test monitoring rule'
        assert rule.condition == 'sentiment_score < 0.3'
        assert rule.threshold == 0.8
        assert rule.alert_level == AlertLevel.WARNING
        assert rule.is_active is True
        assert rule.is_critical_alert is False

    def test_critical_alert_detection(self) -> None:
        """Test critical alert detection."""
        critical_rule = MonitoringRule(rule_id='critical_rule', monitor_type=MonitorType.CONTENT_MODERATION, name='Critical Rule', description='Critical monitoring rule', condition='moderation_flags > 5', threshold=0.9, alert_level=AlertLevel.CRITICAL)
        assert critical_rule.is_critical_alert is True

class TestLiveContentMetrics:
    """Test LiveContentMetrics dataclass."""

    def test_live_content_metrics_creation(self) -> None:
        """Test LiveContentMetrics creation and properties."""
        metrics = LiveContentMetrics(stream_id='test_stream', timestamp=1234567890.0, viewer_count=1000, engagement_rate=0.8, sentiment_score=0.6)
        assert metrics.stream_id == 'test_stream'
        assert metrics.timestamp == 1234567890.0
        assert metrics.viewer_count == 1000
        assert metrics.engagement_rate == 0.8
        assert metrics.sentiment_score == 0.6

class TestMonitoringAlert:
    """Test MonitoringAlert dataclass."""

    def test_monitoring_alert_creation(self) -> None:
        """Test MonitoringAlert creation and properties."""
        alert = MonitoringAlert(alert_id='test_alert', rule_id='test_rule', stream_id='test_stream', alert_level=AlertLevel.WARNING, message='Test alert message', timestamp=1234567890.0, value=0.9, threshold=0.8)
        assert alert.alert_id == 'test_alert'
        assert alert.rule_id == 'test_rule'
        assert alert.stream_id == 'test_stream'
        assert alert.alert_level == AlertLevel.WARNING
        assert alert.message == 'Test alert message'
        assert alert.timestamp == 1234567890.0
        assert alert.value == 0.9
        assert alert.threshold == 0.8
        assert alert.is_active is True
        assert alert.is_stale is False

class TestTrendData:
    """Test TrendData dataclass."""

    def test_trend_data_creation(self) -> None:
        """Test TrendData creation and properties."""
        trend = TrendData(metric_name='engagement', current_value=0.8, previous_value=0.6, trend_direction=TrendDirection.RISING, change_percentage=33.33, confidence=0.9)
        assert trend.metric_name == 'engagement'
        assert trend.current_value == 0.8
        assert trend.previous_value == 0.6
        assert trend.trend_direction == TrendDirection.RISING
        assert trend.change_percentage == 33.33
        assert trend.confidence == 0.9
        assert trend.is_significant_change is True
        assert trend.is_rising_trend is True
        assert trend.is_falling_trend is False

class TestLiveMonitor:
    """Test LiveMonitor functionality."""

    @pytest.fixture
    def monitor(self) -> LiveMonitor:
        """Create LiveMonitor instance for testing."""
        return LiveMonitor()

    def test_monitor_initialization(self, monitor: LiveMonitor) -> None:
        """Test LiveMonitor initialization."""
        assert len(monitor.monitoring_rules) == 0
        assert len(monitor.content_metrics) == 0

    @pytest.mark.asyncio
    async def test_add_monitoring_rule(self, monitor: LiveMonitor) -> None:
        """Test adding a monitoring rule."""
        sample_rule = MonitoringRule(rule_id='test_rule', monitor_type=MonitorType.SENTIMENT_MONITORING, name='Test Rule', description='Test monitoring rule', condition='sentiment_score < 0.3', threshold=0.8, alert_level=AlertLevel.WARNING)
        monitor.add_monitoring_rule(sample_rule)
        assert 'test_rule' in monitor.monitoring_rules
        assert monitor.monitoring_rules['test_rule'] == sample_rule

    @pytest.mark.asyncio
    async def test_start_monitoring(self, monitor: LiveMonitor) -> None:
        """Test starting monitoring for a stream."""
        await monitor.start_monitoring('test_stream')
        assert 'test_stream' in monitor.monitoring_tasks

    @pytest.mark.asyncio
    async def test_stop_monitoring(self, monitor: LiveMonitor) -> None:
        """Test stopping monitoring for a stream."""
        await monitor.start_monitoring('test_stream')
        await monitor.stop_monitoring('test_stream')
        assert 'test_stream' not in monitor.monitoring_tasks

    @pytest.mark.asyncio
    async def test_update_metrics(self, monitor: LiveMonitor) -> None:
        """Test updating content metrics."""
        sample_metrics = LiveContentMetrics(stream_id='test_stream', timestamp=1234567890.0, viewer_count=1000, engagement_rate=0.8, sentiment_score=0.6)
        await monitor.update_metrics('test_stream', sample_metrics)
        assert 'test_stream' in monitor.content_metrics

    @pytest.mark.asyncio
    async def test_get_active_alerts(self, monitor: LiveMonitor) -> None:
        """Test getting active alerts."""
        alerts = await monitor.get_active_alerts('test_stream')
        assert isinstance(alerts, list)

    @pytest.mark.asyncio
    async def test_get_monitoring_statistics(self, monitor: LiveMonitor) -> None:
        """Test getting monitoring statistics."""
        stats = await monitor.get_monitoring_statistics()
        assert isinstance(stats, dict)

    @pytest.mark.asyncio
    async def test_context_manager(self, monitor: LiveMonitor) -> None:
        """Test LiveMonitor as context manager."""
        async with monitor:
            await monitor.start_monitoring('test_stream')

class TestFactualClaim:
    """Test FactualClaim dataclass."""

    def test_factual_claim_creation(self) -> None:
        """Test FactualClaim creation and properties."""
        claim = FactualClaim(claim_id='test_claim', text='The sky is blue', claim_type=ClaimType.SCIENTIFIC, timestamp=1234567890.0, speaker='Test Speaker', context='meteorology discussion')
        assert claim.claim_id == 'test_claim'
        assert claim.text == 'The sky is blue'
        assert claim.claim_type == ClaimType.SCIENTIFIC
        assert claim.timestamp == 1234567890.0
        assert claim.speaker == 'Test Speaker'
        assert claim.context == 'meteorology discussion'
        assert claim.is_scientific is True
        assert claim.is_political is False

class TestVerificationResult:
    """Test VerificationResult dataclass."""

    def test_verification_result_creation(self) -> None:
        """Test VerificationResult creation and properties."""
        result = VerificationResult(claim_id='test_claim', verification_status=VerificationStatus.VERIFIED, confidence_level=ConfidenceLevel.HIGH, confidence_score=0.95, verification_time=2.5, sources_checked=5, sources_agreeing=4, sources_disputing=1, summary='Claim verified by multiple sources')
        assert result.claim_id == 'test_claim'
        assert result.verification_status == VerificationStatus.VERIFIED
        assert result.confidence_level == ConfidenceLevel.HIGH
        assert result.confidence_score == 0.95
        assert result.verification_time == 2.5
        assert result.sources_checked == 5
        assert result.sources_agreeing == 4
        assert result.sources_disputing == 1
        assert result.summary == 'Claim verified by multiple sources'
        assert result.is_verified is True
        assert result.is_disputed is False
        assert result.has_high_confidence is True

class TestVerificationSource:
    """Test VerificationSource dataclass."""

    def test_verification_source_creation(self) -> None:
        """Test VerificationSource creation and properties."""
        source = VerificationSource(source_id='test_source', name='Wikipedia', url='https://en.wikipedia.org', authority_score=0.9, reliability_score=0.85, last_updated=1234567890.0)
        assert source.source_id == 'test_source'
        assert source.name == 'Wikipedia'
        assert source.url == 'https://en.wikipedia.org'
        assert source.authority_score == 0.9
        assert source.reliability_score == 0.85
        assert source.last_updated == 1234567890.0
        assert source.is_authoritative is True
        assert source.is_reliable is True
        assert source.is_high_quality is True

class TestRealTimeFactChecker:
    """Test RealTimeFactChecker functionality."""

    @pytest.fixture
    def fact_checker(self) -> RealTimeFactChecker:
        """Create RealTimeFactChecker instance for testing."""
        return RealTimeFactChecker()

    def test_fact_checker_initialization(self, fact_checker: RealTimeFactChecker) -> None:
        """Test RealTimeFactChecker initialization."""
        assert len(fact_checker.verification_tasks) == 0
        assert len(fact_checker.verification_sources) == 0

    @pytest.mark.asyncio
    async def test_context_manager(self, fact_checker: RealTimeFactChecker) -> None:
        """Test RealTimeFactChecker as context manager."""
        async with fact_checker:
            pass

class TestGlobalStateManagement:
    """Test global state management functions."""

    @pytest.mark.asyncio
    async def test_global_stream_processor(self) -> None:
        """Test global stream processor state management."""
        processor1 = get_global_stream_processor()
        assert processor1 is not None
        new_processor = StreamProcessor()
        set_global_stream_processor(new_processor)
        processor2 = get_global_stream_processor()
        assert processor2 is new_processor

    @pytest.mark.asyncio
    async def test_global_live_monitor(self) -> None:
        """Test global live monitor state management."""
        monitor1 = get_global_live_monitor()
        assert monitor1 is not None
        new_monitor = LiveMonitor()
        set_global_live_monitor(new_monitor)
        monitor2 = get_global_live_monitor()
        assert monitor2 is new_monitor

    @pytest.mark.asyncio
    async def test_global_fact_checker(self) -> None:
        """Test global fact checker state management."""
        fact_checker1 = get_global_fact_checker()
        assert fact_checker1 is not None
        new_fact_checker = RealTimeFactChecker()
        set_global_fact_checker(new_fact_checker)
        fact_checker2 = get_global_fact_checker()
        assert fact_checker2 is new_fact_checker

@pytest.fixture
def sample_claim() -> FactualClaim:
    """Create sample FactualClaim for testing."""
    return FactualClaim(claim_id='sample_claim', text='Sample claim text', claim_type=ClaimType.GENERAL, timestamp=1234567890.0, speaker='Test Speaker', context='test context')

@pytest.fixture
def sample_source() -> VerificationSource:
    """Create sample VerificationSource for testing."""
    return VerificationSource(source_id='sample_source', name='Sample Source', url='https://example.com', authority_score=0.9, reliability_score=0.85, last_updated=1234567890.0)