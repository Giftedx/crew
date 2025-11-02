"""
Live stream analysis tool for real-time content processing.

This tool provides comprehensive live stream analysis including:
- Real-time chat sentiment monitoring
- Live content moderation
- Dynamic fact-checking alerts
- Stream health monitoring
- Audience engagement tracking
- Content trend detection in real-time
"""
from __future__ import annotations
import logging
import time
from typing import Any, TypedDict
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
from ._base import BaseTool

class ChatMessage(TypedDict, total=False):
    """Live chat message structure."""
    timestamp: float
    user_id: str
    username: str
    message: str
    platform: str
    channel_id: str
    message_id: str
    is_moderator: bool
    is_subscriber: bool
    is_vip: bool

class StreamMetrics(TypedDict, total=False):
    """Live stream metrics."""
    viewer_count: int
    chat_rate: float
    engagement_score: float
    sentiment_trend: str
    moderation_alerts: int
    fact_check_alerts: int
    stream_health: float

class TrendAlert(TypedDict, total=False):
    """Real-time trend alert."""
    trend_type: str
    confidence: float
    description: str
    timestamp: float
    related_messages: list[ChatMessage]
    impact_score: float

class ModerationAlert(TypedDict, total=False):
    """Content moderation alert."""
    alert_type: str
    severity: str
    message: ChatMessage
    reason: str
    confidence: float
    action_required: str

class FactCheckAlert(TypedDict, total=False):
    """Real-time fact-checking alert."""
    claim: str
    confidence: float
    source_message: ChatMessage
    verification_status: str
    suggested_response: str
    priority: str

class LiveStreamAnalysisResult(TypedDict, total=False):
    """Complete live stream analysis result."""
    stream_metrics: StreamMetrics
    chat_analysis: dict[str, Any]
    trend_alerts: list[TrendAlert]
    moderation_alerts: list[ModerationAlert]
    fact_check_alerts: list[FactCheckAlert]
    engagement_insights: dict[str, Any]
    content_health: dict[str, Any]
    processing_time: float
    metadata: dict[str, Any]

class LiveStreamAnalysisTool(BaseTool[StepResult]):
    """Real-time live stream analysis with comprehensive monitoring capabilities."""
    name: str = 'Live Stream Analysis Tool'
    description: str = 'Analyzes live streams in real-time for chat sentiment, content moderation, fact-checking, and trend detection.'

    def __init__(self, enable_chat_analysis: bool=True, enable_moderation: bool=True, enable_fact_checking: bool=True, enable_trend_detection: bool=True, chat_window_minutes: int=5, max_messages_per_analysis: int=1000, sentiment_threshold: float=0.7, moderation_threshold: float=0.8):
        super().__init__()
        self._enable_chat_analysis = enable_chat_analysis
        self._enable_moderation = enable_moderation
        self._enable_fact_checking = enable_fact_checking
        self._enable_trend_detection = enable_trend_detection
        self._chat_window_minutes = chat_window_minutes
        self._max_messages_per_analysis = max_messages_per_analysis
        self._sentiment_threshold = sentiment_threshold
        self._moderation_threshold = moderation_threshold
        self._metrics = get_metrics()
        self._chat_buffer: list[ChatMessage] = []
        self._trend_history: list[TrendAlert] = []
        self._moderation_history: list[ModerationAlert] = []

    def _run(self, stream_data: dict[str, Any], chat_messages: list[ChatMessage] | None=None, stream_metadata: dict[str, Any] | None=None, tenant: str='default', workspace: str='default', analysis_mode: str='comprehensive') -> StepResult:
        """
        Perform real-time live stream analysis.

        Args:
            stream_data: Live stream information (viewer count, platform, etc.)
            chat_messages: Recent chat messages for analysis
            stream_metadata: Additional stream metadata
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier
            analysis_mode: Analysis mode (basic, comprehensive, monitoring)

        Returns:
            StepResult with comprehensive live stream analysis
        """
        start_time = time.monotonic()
        try:
            if not stream_data:
                return StepResult.fail('Stream data cannot be empty')
            if tenant and workspace:
                self.note('Starting live stream analysis')
            if chat_messages:
                self._update_chat_buffer(chat_messages)
            stream_metrics = self._analyze_stream_metrics(stream_data, stream_metadata)
            chat_analysis = self._analyze_chat_sentiment() if self._enable_chat_analysis else {}
            trend_alerts = self._detect_trends() if self._enable_trend_detection else []
            moderation_alerts = self._analyze_moderation() if self._enable_moderation else []
            fact_check_alerts = self._analyze_fact_checking() if self._enable_fact_checking else []
            engagement_insights = self._analyze_engagement(stream_data, stream_metrics)
            content_health = self._assess_content_health(stream_metrics, moderation_alerts, fact_check_alerts)
            processing_time = time.monotonic() - start_time
            result: LiveStreamAnalysisResult = {'stream_metrics': stream_metrics, 'chat_analysis': chat_analysis, 'trend_alerts': trend_alerts, 'moderation_alerts': moderation_alerts, 'fact_check_alerts': fact_check_alerts, 'engagement_insights': engagement_insights, 'content_health': content_health, 'processing_time': processing_time, 'metadata': {'analysis_mode': analysis_mode, 'chat_messages_analyzed': len(self._chat_buffer), 'tenant': tenant, 'workspace': workspace, 'timestamp': time.time()}}
            self._metrics.counter('tool_runs_total', labels={'tool': self.name, 'outcome': 'success'}).inc()
            self._metrics.histogram('tool_run_seconds', processing_time, labels={'tool': self.name})
            return StepResult.ok(data=result)
        except Exception as e:
            processing_time = time.monotonic() - start_time
            self._metrics.counter('tool_runs_total', labels={'tool': self.name, 'outcome': 'error'}).inc()
            logging.exception('Live stream analysis failed')
            return StepResult.fail(f'Live stream analysis failed: {e!s}')

    def _update_chat_buffer(self, new_messages: list[ChatMessage]) -> None:
        """Update the chat message buffer with new messages."""
        current_time = time.time()
        cutoff_time = current_time - self._chat_window_minutes * 60
        self._chat_buffer.extend(new_messages)
        self._chat_buffer = [msg for msg in self._chat_buffer if msg.get('timestamp', 0) > cutoff_time]
        if len(self._chat_buffer) > self._max_messages_per_analysis:
            self._chat_buffer = self._chat_buffer[-self._max_messages_per_analysis:]

    def _analyze_stream_metrics(self, stream_data: dict[str, Any], stream_metadata: dict[str, Any] | None) -> StreamMetrics:
        """Analyze live stream metrics."""
        viewer_count = stream_data.get('viewer_count', 0)
        current_time = time.time()
        recent_messages = [msg for msg in self._chat_buffer if current_time - msg.get('timestamp', 0) <= 60]
        chat_rate = len(recent_messages)
        engagement_score = self._calculate_engagement_score(viewer_count, chat_rate, recent_messages)
        sentiment_trend = self._analyze_sentiment_trend()
        moderation_alerts = len([alert for alert in self._moderation_history if current_time - alert.get('timestamp', 0.0) <= 300])
        fact_check_alerts = 0
        stream_health = self._calculate_stream_health(viewer_count, chat_rate, engagement_score)
        return {'viewer_count': viewer_count, 'chat_rate': float(chat_rate), 'engagement_score': engagement_score, 'sentiment_trend': sentiment_trend, 'moderation_alerts': moderation_alerts, 'fact_check_alerts': fact_check_alerts, 'stream_health': stream_health}

    def _analyze_chat_sentiment(self) -> dict[str, Any]:
        """Analyze chat sentiment in real-time."""
        if not self._chat_buffer:
            return {'sentiment': 'neutral', 'confidence': 0.0, 'message_count': 0}
        positive_keywords = ['good', 'great', 'awesome', 'love', 'amazing', 'best', 'excellent', 'fantastic']
        negative_keywords = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'disgusting', 'stupid']
        positive_count = 0
        negative_count = 0
        total_messages = len(self._chat_buffer)
        for message in self._chat_buffer:
            msg_text = message.get('message', '').lower()
            positive_count += sum((1 for keyword in positive_keywords if keyword in msg_text))
            negative_count += sum((1 for keyword in negative_keywords if keyword in msg_text))
        if positive_count > negative_count:
            sentiment = 'positive'
            confidence = min(0.9, positive_count / max(1, total_messages))
        elif negative_count > positive_count:
            sentiment = 'negative'
            confidence = min(0.9, negative_count / max(1, total_messages))
        else:
            sentiment = 'neutral'
            confidence = 0.5
        sentiment_timeline = self._create_sentiment_timeline()
        return {'sentiment': sentiment, 'confidence': confidence, 'message_count': total_messages, 'positive_indicators': positive_count, 'negative_indicators': negative_count, 'sentiment_timeline': sentiment_timeline}

    def _detect_trends(self) -> list[TrendAlert]:
        """Detect emerging trends in chat."""
        if not self._chat_buffer:
            return []
        trends: list[TrendAlert] = []
        current_time = time.time()
        recent_messages = [msg for msg in self._chat_buffer if current_time - msg.get('timestamp', 0) <= 300]
        if len(recent_messages) < 10:
            return trends
        trending_topics = self._detect_trending_topics(recent_messages)
        for topic, confidence in trending_topics.items():
            if confidence > 0.6:
                trend_alert: TrendAlert = {'trend_type': 'topic_trend', 'confidence': confidence, 'description': f'Trending topic: {topic}', 'timestamp': current_time, 'related_messages': [msg for msg in recent_messages if topic.lower() in msg.get('message', '').lower()][:5], 'impact_score': confidence * len([msg for msg in recent_messages if topic.lower() in msg.get('message', '').lower()])}
                trends.append(trend_alert)
        engagement_spike = self._detect_engagement_spike(recent_messages)
        if engagement_spike:
            trends.append(engagement_spike)
        return trends

    def _analyze_moderation(self) -> list[ModerationAlert]:
        """Analyze chat for moderation needs."""
        if not self._chat_buffer:
            return []
        alerts = []
        current_time = time.time()
        recent_messages = [msg for msg in self._chat_buffer if current_time - msg.get('timestamp', 0) <= 60]
        for message in recent_messages:
            alert = self._check_message_moderation(message)
            if alert:
                alerts.append(alert)
        return alerts

    def _analyze_fact_checking(self) -> list[FactCheckAlert]:
        """Analyze chat for fact-checking opportunities."""
        if not self._chat_buffer:
            return []
        alerts = []
        current_time = time.time()
        recent_messages = [msg for msg in self._chat_buffer if current_time - msg.get('timestamp', 0) <= 300]
        for message in recent_messages:
            claim = self._extract_factual_claim(message)
            if claim:
                alert: FactCheckAlert = {'claim': claim, 'confidence': 0.7, 'source_message': message, 'verification_status': 'pending', 'suggested_response': f'Fact-checking claim: {claim}', 'priority': 'medium'}
                alerts.append(alert)
        return alerts

    def _analyze_engagement(self, stream_data: dict[str, Any], stream_metrics: StreamMetrics) -> dict[str, Any]:
        """Analyze audience engagement patterns."""
        viewer_count = stream_data.get('viewer_count', 0)
        chat_rate = stream_metrics.get('chat_rate', 0.0)
        engagement_score = stream_metrics.get('engagement_score', 0.0)
        engagement_ratio = chat_rate / max(1, viewer_count) if viewer_count > 0 else 0.0
        if engagement_ratio > 0.1:
            engagement_level = 'high'
        elif engagement_ratio > 0.05:
            engagement_level = 'medium'
        else:
            engagement_level = 'low'
        engagement_trend = self._analyze_engagement_trend()
        return {'engagement_level': engagement_level, 'engagement_ratio': engagement_ratio, 'engagement_score': engagement_score, 'engagement_trend': engagement_trend, 'viewer_participation': min(1.0, chat_rate / max(1, viewer_count * 0.1))}

    def _assess_content_health(self, stream_metrics: StreamMetrics, moderation_alerts: list[ModerationAlert], fact_check_alerts: list[FactCheckAlert]) -> dict[str, Any]:
        """Assess overall content health of the stream."""
        health_score = 1.0
        moderation_penalty = len(moderation_alerts) * 0.1
        health_score -= moderation_penalty
        fact_check_penalty = len(fact_check_alerts) * 0.05
        health_score -= fact_check_penalty
        sentiment_trend = stream_metrics.get('sentiment_trend', 'neutral')
        if sentiment_trend == 'negative':
            health_score -= 0.2
        elif sentiment_trend == 'positive':
            health_score += 0.1
        engagement_score = stream_metrics.get('engagement_score', 0.5)
        health_score = (health_score + engagement_score) / 2
        health_score = max(0.0, min(1.0, health_score))
        if health_score > 0.8:
            health_status = 'excellent'
        elif health_score > 0.6:
            health_status = 'good'
        elif health_score > 0.4:
            health_status = 'fair'
        else:
            health_status = 'poor'
        return {'health_score': health_score, 'health_status': health_status, 'moderation_issues': len(moderation_alerts), 'fact_check_issues': len(fact_check_alerts), 'recommendations': self._generate_health_recommendations(health_score, moderation_alerts, fact_check_alerts)}

    def _calculate_engagement_score(self, viewer_count: int, chat_rate: float, recent_messages: list[ChatMessage]) -> float:
        """Calculate engagement score based on various factors."""
        if viewer_count == 0:
            return 0.0
        base_engagement = min(1.0, chat_rate / max(1, viewer_count * 0.1))
        unique_users = len({msg.get('user_id', '') for msg in recent_messages})
        user_diversity = unique_users / max(1, len(recent_messages))
        special_users = sum((1 for msg in recent_messages if any([msg.get('is_moderator', False), msg.get('is_subscriber', False), msg.get('is_vip', False)])))
        special_user_bonus = special_users / max(1, len(recent_messages))
        engagement_score = (base_engagement + user_diversity + special_user_bonus) / 3
        return min(1.0, engagement_score)

    def _analyze_sentiment_trend(self) -> str:
        """Analyze sentiment trend over time."""
        if len(self._chat_buffer) < 10:
            return 'neutral'
        current_time = time.time()
        windows = [(current_time - 60, current_time), (current_time - 300, current_time - 60)]
        window_sentiments = []
        for start_time, end_time in windows:
            window_messages = [msg for msg in self._chat_buffer if start_time <= msg.get('timestamp', 0) <= end_time]
            if window_messages:
                sentiment = self._calculate_window_sentiment(window_messages)
                window_sentiments.append(sentiment)
        if len(window_sentiments) < 2:
            return 'neutral'
        recent_sentiment = window_sentiments[0]
        previous_sentiment = window_sentiments[1]
        if recent_sentiment > previous_sentiment + 0.2:
            return 'improving'
        elif recent_sentiment < previous_sentiment - 0.2:
            return 'declining'
        else:
            return 'stable'

    def _calculate_stream_health(self, viewer_count: int, chat_rate: float, engagement_score: float) -> float:
        """Calculate overall stream health score."""
        viewer_health = min(1.0, viewer_count / 1000)
        chat_health = min(1.0, chat_rate / 10)
        engagement_health = engagement_score
        health_score = (viewer_health + chat_health + engagement_health) / 3
        return min(1.0, health_score)

    def _create_sentiment_timeline(self) -> list[dict[str, Any]]:
        """Create sentiment timeline for the chat."""
        if not self._chat_buffer:
            return []
        timeline = []
        current_time = time.time()
        for i in range(5):
            window_start = current_time - (i + 1) * 60
            window_end = current_time - i * 60
            window_messages = [msg for msg in self._chat_buffer if window_start <= msg.get('timestamp', 0) <= window_end]
            if window_messages:
                sentiment = self._calculate_window_sentiment(window_messages)
                timeline.append({'timestamp': window_start, 'sentiment': sentiment, 'message_count': len(window_messages)})
        return timeline

    def _calculate_window_sentiment(self, messages: list[ChatMessage]) -> float:
        """Calculate sentiment for a time window."""
        if not messages:
            return 0.5
        positive_keywords = ['good', 'great', 'awesome', 'love', 'amazing', 'best', 'excellent', 'fantastic']
        negative_keywords = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'disgusting', 'stupid']
        positive_count = 0
        negative_count = 0
        for message in messages:
            msg_text = message.get('message', '').lower()
            positive_count += sum((1 for keyword in positive_keywords if keyword in msg_text))
            negative_count += sum((1 for keyword in negative_keywords if keyword in msg_text))
        total_indicators = positive_count + negative_count
        if total_indicators == 0:
            return 0.5
        return positive_count / total_indicators

    def _detect_trending_topics(self, messages: list[ChatMessage]) -> dict[str, float]:
        """Detect trending topics in chat messages."""
        word_counts: dict[str, int] = {}
        total_messages = len(messages)
        for message in messages:
            msg_text = message.get('message', '').lower()
            words = msg_text.split()
            for word in words:
                if len(word) > 3:
                    word_counts[word] = word_counts.get(word, 0) + 1
        trending_topics = {}
        for word, count in word_counts.items():
            if count >= 3:
                trending_score = count / total_messages
                trending_topics[word] = trending_score
        return trending_topics

    def _detect_engagement_spike(self, messages: list[ChatMessage]) -> TrendAlert | None:
        """Detect engagement spikes in chat."""
        if len(messages) < 20:
            return None
        current_time = time.time()
        messages_per_minute = len(messages) / 5
        if messages_per_minute > 20:
            return {'trend_type': 'engagement_spike', 'confidence': min(1.0, messages_per_minute / 50), 'description': f'High engagement detected: {messages_per_minute:.1f} messages/minute', 'timestamp': current_time, 'related_messages': messages[-10:], 'impact_score': messages_per_minute}
        return None

    def _check_message_moderation(self, message: ChatMessage) -> ModerationAlert | None:
        """Check if a message needs moderation."""
        msg_text = message.get('message', '').lower()
        inappropriate_keywords = ['spam', 'scam', 'fake', 'hate', 'harassment']
        for keyword in inappropriate_keywords:
            if keyword in msg_text:
                return {'alert_type': 'inappropriate_content', 'severity': 'medium', 'message': message, 'reason': f'Contains potentially inappropriate content: {keyword}', 'confidence': 0.8, 'action_required': 'review'}
        if len(msg_text) > 200:
            return {'alert_type': 'potential_spam', 'severity': 'low', 'message': message, 'reason': 'Unusually long message', 'confidence': 0.6, 'action_required': 'monitor'}
        return None

    def _extract_factual_claim(self, message: ChatMessage) -> str | None:
        """Extract factual claims from a message."""
        msg_text = message.get('message', '')
        claim_indicators = ['is', 'are', 'was', 'were', 'will be', 'has been', 'have been']
        factual_indicators = ['fact', 'truth', 'proven', 'confirmed', 'verified']
        for indicator in claim_indicators:
            if indicator in msg_text.lower():
                for fact_indicator in factual_indicators:
                    if fact_indicator in msg_text.lower():
                        return msg_text
        if any((char.isdigit() for char in msg_text)) and len(msg_text) > 20:
            return msg_text
        return None

    def _analyze_engagement_trend(self) -> str:
        """Analyze engagement trend over time."""
        if len(self._chat_buffer) < 20:
            return 'insufficient_data'
        current_time = time.time()
        recent_window = [msg for msg in self._chat_buffer if current_time - msg.get('timestamp', 0) <= 60]
        previous_window = [msg for msg in self._chat_buffer if 60 < current_time - msg.get('timestamp', 0) <= 120]
        if len(recent_window) > len(previous_window) * 1.5:
            return 'increasing'
        elif len(recent_window) < len(previous_window) * 0.5:
            return 'decreasing'
        else:
            return 'stable'

    def _generate_health_recommendations(self, health_score: float, moderation_alerts: list[ModerationAlert], fact_check_alerts: list[FactCheckAlert]) -> list[str]:
        """Generate recommendations for improving stream health."""
        recommendations = []
        if health_score < 0.6:
            recommendations.append('Consider increasing audience engagement through interactive content')
        if len(moderation_alerts) > 5:
            recommendations.append('High moderation activity - consider additional moderators')
        if len(fact_check_alerts) > 3:
            recommendations.append('Multiple fact-checking opportunities - consider addressing misinformation')
        if health_score < 0.4:
            recommendations.append('Stream health is low - review content strategy and audience engagement')
        return recommendations

    def run(self, stream_data: dict[str, Any], chat_messages: list[ChatMessage] | None=None, stream_metadata: dict[str, Any] | None=None, tenant: str='default', workspace: str='default', analysis_mode: str='comprehensive') -> StepResult:
        """Public interface for live stream analysis."""
        return self._run(stream_data, chat_messages, stream_metadata, tenant, workspace, analysis_mode)