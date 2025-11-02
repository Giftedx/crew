"""
Tests for Live Clip Radar feature.
"""
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import pytest
from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.features.clip_radar_agent import LiveClipRadarAgent
from ultimate_discord_intelligence_bot.creator_ops.features.clip_radar_models import ChatMessage, ClipCandidate, ClipStatus, MomentType, MonitoringConfig, PlatformType, SentimentScore, StreamInfo, StreamStatus, ViralMoment
from ultimate_discord_intelligence_bot.creator_ops.features.live_clip_radar import LiveClipRadar
from platform.core.step_result import StepResult

class TestLiveClipRadar:
    """Test suite for LiveClipRadar."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=CreatorOpsConfig)
        self.clip_radar = LiveClipRadar(self.config)
        self.monitoring_config = MonitoringConfig(platform=PlatformType.YOUTUBE, channel_id='test_channel', enabled=True, detection_sensitivity=0.7, chat_velocity_threshold=3.0, sentiment_flip_threshold=0.5, laughter_keywords=['lol', 'haha', '😂'], min_clip_duration=30.0, max_clip_duration=90.0, auto_generate_clips=True, auto_create_markers=True)
        self.stream_info = StreamInfo(stream_id='test_stream', channel_id='test_channel', platform=PlatformType.YOUTUBE, title='Test Stream', description='Test stream description', status=StreamStatus.ONLINE, started_at=datetime.now(), viewer_count=1000, language='en', category='Gaming')
        self.chat_message = ChatMessage(message_id='msg_1', user_id='user_1', username='test_user', message='This is amazing! 😂😂😂', timestamp=datetime.now(), platform=PlatformType.YOUTUBE, channel_id='test_channel', stream_id='test_stream', emotes=['😂'])

    def test_init(self):
        """Test LiveClipRadar initialization."""
        assert self.clip_radar.config == self.config
        assert self.clip_radar.youtube_client is not None
        assert self.clip_radar.twitch_client is not None
        assert len(self.clip_radar.monitoring_configs) == 0
        assert len(self.clip_radar.active_streams) == 0

    @pytest.mark.asyncio
    async def test_start_monitoring_success(self):
        """Test successful monitoring start."""
        with patch.object(self.clip_radar, '_get_stream_info') as mock_get_info:
            mock_get_info.return_value = StepResult.ok(data={'stream_info': self.stream_info})
            with patch.object(self.clip_radar, '_monitor_stream') as mock_monitor:
                mock_monitor.return_value = None
                result = await self.clip_radar.start_monitoring(self.monitoring_config)
                assert result.success
                assert 'stream_key' in result.data
                assert 'stream_info' in result.data
                assert len(self.clip_radar.monitoring_configs) == 1
                assert len(self.clip_radar.active_streams) == 1

    @pytest.mark.asyncio
    async def test_start_monitoring_already_monitoring(self):
        """Test starting monitoring when already monitoring."""
        stream_key = 'youtube_test_channel'
        self.clip_radar.monitoring_configs[stream_key] = self.monitoring_config
        result = await self.clip_radar.start_monitoring(self.monitoring_config)
        assert not result.success
        assert 'Already monitoring' in result.error

    @pytest.mark.asyncio
    async def test_stop_monitoring_success(self):
        """Test successful monitoring stop."""
        stream_key = 'youtube_test_channel'
        self.clip_radar.monitoring_configs[stream_key] = self.monitoring_config
        self.clip_radar.active_streams[stream_key] = self.stream_info
        mock_task = Mock()
        mock_task.cancel = Mock()
        self.clip_radar.monitoring_tasks[stream_key] = mock_task
        result = await self.clip_radar.stop_monitoring(stream_key)
        assert result.success
        assert stream_key not in self.clip_radar.monitoring_configs
        assert stream_key not in self.clip_radar.active_streams
        assert stream_key not in self.clip_radar.monitoring_tasks

    @pytest.mark.asyncio
    async def test_stop_monitoring_not_monitoring(self):
        """Test stopping monitoring when not monitoring."""
        stream_key = 'youtube_test_channel'
        result = await self.clip_radar.stop_monitoring(stream_key)
        assert not result.success
        assert 'Not monitoring' in result.error

    @pytest.mark.asyncio
    async def test_process_chat_message(self):
        """Test chat message processing."""
        stream_key = 'youtube_test_channel'
        with patch.object(self.clip_radar, '_analyze_sentiment') as mock_sentiment:
            mock_sentiment.return_value = SentimentScore(score=0.8, confidence=0.9, label='positive', keywords=['amazing', 'great'])
            with patch.object(self.clip_radar, '_check_viral_moments') as mock_check:
                mock_check.return_value = None
                await self.clip_radar._process_chat_message(stream_key, self.chat_message, self.monitoring_config)
                assert len(self.clip_radar.chat_queues[stream_key]) == 1
                assert len(self.clip_radar.sentiment_history[stream_key]) == 1

    @pytest.mark.asyncio
    async def test_check_chat_velocity_high_velocity(self):
        """Test chat velocity detection with high velocity."""
        stream_key = 'youtube_test_channel'
        now = datetime.now()
        for i in range(50):
            msg = ChatMessage(message_id=f'msg_{i}', user_id=f'user_{i}', username=f'user_{i}', message=f'Message {i}', timestamp=now - timedelta(seconds=i), platform=PlatformType.YOUTUBE, channel_id='test_channel', stream_id='test_stream')
            self.clip_radar.chat_queues[stream_key].append(msg)
        with patch.object(self.clip_radar, '_calculate_baseline_velocity') as mock_baseline:
            mock_baseline.return_value = 10.0
            result = await self.clip_radar._check_chat_velocity(stream_key, self.chat_message, self.monitoring_config)
            assert result is not None
            assert result.moment_type == MomentType.CHAT_VELOCITY
            assert result.confidence > 0.5

    @pytest.mark.asyncio
    async def test_check_chat_velocity_low_velocity(self):
        """Test chat velocity detection with low velocity."""
        stream_key = 'youtube_test_channel'
        now = datetime.now()
        for i in range(5):
            msg = ChatMessage(message_id=f'msg_{i}', user_id=f'user_{i}', username=f'user_{i}', message=f'Message {i}', timestamp=now - timedelta(seconds=i), platform=PlatformType.YOUTUBE, channel_id='test_channel', stream_id='test_stream')
            self.clip_radar.chat_queues[stream_key].append(msg)
        with patch.object(self.clip_radar, '_calculate_baseline_velocity') as mock_baseline:
            mock_baseline.return_value = 10.0
            result = await self.clip_radar._check_chat_velocity(stream_key, self.chat_message, self.monitoring_config)
            assert result is None

    @pytest.mark.asyncio
    async def test_check_sentiment_flip_positive_flip(self):
        """Test sentiment flip detection with positive flip."""
        stream_key = 'youtube_test_channel'
        now = datetime.now()
        for i in range(10):
            self.clip_radar.sentiment_history[stream_key].append({'timestamp': now - timedelta(minutes=15, seconds=i), 'sentiment': -0.8, 'message': f'Bad message {i}'})
        for i in range(10):
            self.clip_radar.sentiment_history[stream_key].append({'timestamp': now - timedelta(seconds=i), 'sentiment': 0.8, 'message': f'Good message {i}'})
        sentiment = SentimentScore(score=0.8, confidence=0.9, label='positive')
        result = await self.clip_radar._check_sentiment_flip(stream_key, self.chat_message, sentiment, self.monitoring_config)
        assert result is not None
        assert result.moment_type == MomentType.SENTIMENT_FLIP
        assert 'positive_surge' in result.metrics.get('flip_type', '')

    @pytest.mark.asyncio
    async def test_check_laughter_detection(self):
        """Test laughter detection."""
        stream_key = 'youtube_test_channel'
        laughter_message = ChatMessage(message_id='msg_laughter', user_id='user_1', username='test_user', message="That's hilarious! 😂😂😂 haha", timestamp=datetime.now(), platform=PlatformType.YOUTUBE, channel_id='test_channel', stream_id='test_stream', emotes=['😂'])
        self.clip_radar.chat_queues[stream_key].append(laughter_message)
        result = await self.clip_radar._check_laughter(stream_key, laughter_message, self.monitoring_config)
        assert result is not None
        assert result.moment_type == MomentType.LAUGHTER
        assert result.confidence > 0.5

    @pytest.mark.asyncio
    async def test_generate_clip_candidate(self):
        """Test clip candidate generation."""
        viral_moment = ViralMoment(moment_id='moment_1', moment_type=MomentType.LAUGHTER, timestamp=datetime.now(), platform=PlatformType.YOUTUBE, channel_id='test_channel', stream_id='test_stream', confidence=0.8, trigger_message=self.chat_message, description='Laughter detected')
        with patch.object(self.clip_radar, '_generate_clip_title') as mock_title, patch.object(self.clip_radar, '_generate_clip_description') as mock_desc:
            mock_title.return_value = 'Hilarious Moment'
            mock_desc.return_value = 'Funny clip from live stream'
            result = await self.clip_radar._generate_clip_candidate(viral_moment, self.monitoring_config)
            assert result is not None
            assert result.title == 'Hilarious Moment'
            assert result.description == 'Funny clip from live stream'
            assert result.duration == 30.0
            assert result.status == ClipStatus.DETECTED

    def test_analyze_sentiment_positive(self):
        """Test sentiment analysis for positive text."""
        result = self.clip_radar._analyze_sentiment('This is amazing and great!')
        assert result.score > 0
        assert result.label == 'positive'
        assert result.confidence > 0

    def test_analyze_sentiment_negative(self):
        """Test sentiment analysis for negative text."""
        result = self.clip_radar._analyze_sentiment('This is terrible and awful!')
        assert result.score < 0
        assert result.label == 'negative'
        assert result.confidence > 0

    def test_analyze_sentiment_neutral(self):
        """Test sentiment analysis for neutral text."""
        result = self.clip_radar._analyze_sentiment('This is just a regular message.')
        assert result.score == 0
        assert result.label == 'neutral'
        assert result.confidence == 0

    def test_extract_emotes(self):
        """Test emote extraction."""
        message = "That's funny! 😂😂😂 Great job! 👏"
        emotes = self.clip_radar._extract_emotes(message)
        assert '😂' in emotes
        assert '👏' in emotes

    def test_calculate_baseline_velocity(self):
        """Test baseline velocity calculation."""
        stream_key = 'youtube_test_channel'
        now = datetime.now()
        for i in range(20):
            msg = ChatMessage(message_id=f'msg_{i}', user_id=f'user_{i}', username=f'user_{i}', message=f'Message {i}', timestamp=now - timedelta(minutes=i // 2), platform=PlatformType.YOUTUBE, channel_id='test_channel', stream_id='test_stream')
            self.clip_radar.chat_queues[stream_key].append(msg)
        baseline = self.clip_radar._calculate_baseline_velocity(stream_key)
        assert baseline > 0
        assert baseline >= 1.0

    @pytest.mark.asyncio
    async def test_get_monitoring_status(self):
        """Test monitoring status retrieval."""
        stream_key = 'youtube_test_channel'
        self.clip_radar.active_streams[stream_key] = self.stream_info
        self.clip_radar.monitoring_configs[stream_key] = self.monitoring_config
        viral_moment = ViralMoment(moment_id='moment_1', moment_type=MomentType.LAUGHTER, timestamp=datetime.now(), platform=PlatformType.YOUTUBE, channel_id='test_channel', stream_id='test_stream', confidence=0.8, description='Test moment')
        self.clip_radar.viral_moments.append(viral_moment)
        result = await self.clip_radar.get_monitoring_status()
        assert result.success
        assert result.data['status']['active_streams'] == 1
        assert result.data['status']['viral_moments_detected'] == 1
        assert result.data['status']['streams'] == [stream_key]

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup functionality."""
        stream_key = 'youtube_test_channel'
        self.clip_radar.monitoring_configs[stream_key] = self.monitoring_config
        self.clip_radar.active_streams[stream_key] = self.stream_info
        self.clip_radar.viral_moments.append(Mock())
        self.clip_radar.clip_candidates.append(Mock())
        with patch.object(self.clip_radar, 'stop_monitoring') as mock_stop:
            mock_stop.return_value = StepResult.ok(data={'stream_key': stream_key})
            await self.clip_radar.cleanup()
            assert len(self.clip_radar.viral_moments) == 0
            assert len(self.clip_radar.clip_candidates) == 0
            assert len(self.clip_radar.chat_queues) == 0
            assert len(self.clip_radar.sentiment_history) == 0

class TestLiveClipRadarAgent:
    """Test suite for LiveClipRadarAgent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=CreatorOpsConfig)
        self.config.openrouter_api_key = 'test_key'
        self.agent = LiveClipRadarAgent(self.config)

    def test_init(self):
        """Test LiveClipRadarAgent initialization."""
        assert self.agent.config == self.config
        assert self.agent.agents is not None
        assert self.agent.tasks is not None
        assert self.agent.crew is not None

    def test_create_agents(self):
        """Test agent creation."""
        agents = self.agent._create_agents()
        expected_roles = ['viral_analyst', 'clip_optimizer', 'engagement_predictor', 'platform_strategist']
        for role in expected_roles:
            assert role in agents
            assert agents[role].role == role.replace('_', ' ').title()

    def test_create_tasks(self):
        """Test task creation."""
        tasks = self.agent._create_tasks()
        expected_tasks = ['viral_analysis', 'clip_optimization', 'engagement_prediction', 'platform_strategy']
        for task in expected_tasks:
            assert task in tasks
            assert tasks[task].description is not None

    @pytest.mark.asyncio
    async def test_analyze_viral_moment(self):
        """Test viral moment analysis."""
        viral_moment = ViralMoment(moment_id='moment_1', moment_type=MomentType.LAUGHTER, timestamp=datetime.now(), platform=PlatformType.YOUTUBE, channel_id='test_channel', stream_id='test_stream', confidence=0.8, description='Laughter detected')
        with patch.object(self.agent.crew, 'kickoff') as mock_kickoff:
            mock_kickoff.return_value = {'viral_analysis': 'High quality viral moment with strong engagement potential', 'clip_optimization': 'Optimize title and description for better reach', 'engagement_prediction': 'Predicted high engagement based on content characteristics', 'platform_strategy': 'Platform-specific optimization strategies'}
            result = await self.agent.analyze_viral_moment(viral_moment)
            assert result.success
            assert 'analysis' in result.data

    @pytest.mark.asyncio
    async def test_optimize_clip_candidate(self):
        """Test clip candidate optimization."""
        clip_candidate = ClipCandidate(clip_id='clip_1', moment_id='moment_1', title='Original Title', description='Original description', start_time=100.0, end_time=130.0, duration=30.0, platform=PlatformType.YOUTUBE, stream_id='test_stream', channel_id='test_channel', status=ClipStatus.DETECTED, viral_moment=Mock())
        with patch.object(self.agent.crew, 'kickoff') as mock_kickoff:
            mock_kickoff.return_value = {'clip_optimization': 'Optimized title and description', 'engagement_prediction': 'High engagement potential', 'platform_strategy': 'Platform-specific optimizations'}
            result = await self.agent.optimize_clip_candidate(clip_candidate)
            assert result.success
            assert 'optimization' in result.data

    def test_parse_crew_results(self):
        """Test crew results parsing."""
        mock_result = {'viral_analysis': 'High quality moment with 0.8 quality score and strong viral potential', 'clip_optimization': 'Optimize title for better engagement and add relevant hashtags', 'engagement_prediction': 'Predicted 10k views, 1k likes, 500 shares', 'platform_strategy': 'YouTube optimization with SEO focus, TikTok with trending sounds'}
        result = self.agent._parse_crew_results(mock_result)
        assert 'quality_score' in result
        assert 'viral_potential' in result
        assert 'optimization_suggestions' in result
        assert 'engagement_prediction' in result

    def test_extract_viral_insights(self):
        """Test viral insights extraction."""
        text = 'High quality moment with 0.8 quality score and strong viral potential. Consider optimization strategies.'
        insights = self.agent._extract_viral_insights(text)
        assert 'quality_score' in insights
        assert 'viral_potential' in insights
        assert 'optimization_suggestions' in insights

    def test_extract_score(self):
        """Test score extraction."""
        text = 'quality score: 0.85'
        score = self.agent._extract_score(text, 'quality')
        assert 0.0 <= score <= 1.0

    def test_extract_optimization(self):
        """Test optimization extraction."""
        text = 'title optimization: Use engaging hooks and trending keywords.'
        optimization = self.agent._extract_optimization(text, 'title')
        assert 'title' in optimization.lower()

    @pytest.mark.asyncio
    async def test_generate_optimized_clip(self):
        """Test optimized clip generation."""
        clip_candidate = ClipCandidate(clip_id='clip_1', moment_id='moment_1', title='Original Title', description='Original description', start_time=100.0, end_time=130.0, duration=30.0, platform=PlatformType.YOUTUBE, stream_id='test_stream', channel_id='test_channel', status=ClipStatus.DETECTED, viral_moment=Mock())
        viral_analysis = Mock()
        viral_analysis.moment_quality_score = 0.8
        viral_analysis.viral_potential = 0.7
        clip_optimization = Mock()
        clip_optimization.title_optimization = 'Optimized Title'
        clip_optimization.description_optimization = 'Optimized description'
        clip_optimization.platform_specific_hooks = {'youtube': 'SEO optimized'}
        clip_optimization.hashtag_recommendations = ['#viral', '#funny']
        clip_optimization.engagement_strategies = ['Use trending hashtags']
        result = await self.agent.generate_optimized_clip(clip_candidate, viral_analysis, clip_optimization)
        assert result.success
        assert 'optimized_clip' in result.data
        optimized_clip = result.data['optimized_clip']
        assert optimized_clip.title == 'Optimized Title'
        assert optimized_clip.description == 'Optimized description'
        assert optimized_clip.status == ClipStatus.PROCESSING

    @pytest.mark.asyncio
    async def test_get_analysis_summary(self):
        """Test analysis summary generation."""
        viral_analysis = Mock()
        viral_analysis.moment_quality_score = 0.8
        viral_analysis.viral_potential = 0.7
        viral_analysis.engagement_prediction = {'views': 10000, 'likes': 1000}
        viral_analysis.optimization_suggestions = ['Optimize timing', 'Improve hooks']
        viral_analysis.clip_recommendations = ['Add captions', 'Use trending music']
        viral_analysis.risk_assessment = 'Low risk'
        viral_analysis.target_audience = ['Gaming', 'Comedy']
        clip_optimization = Mock()
        clip_optimization.title_optimization = 'Optimized Title'
        clip_optimization.description_optimization = 'Optimized description'
        clip_optimization.hashtag_recommendations = ['#viral', '#funny', '#gaming']
        clip_optimization.platform_specific_hooks = {'youtube': 'SEO', 'tiktok': 'Trending'}
        clip_optimization.engagement_strategies = ['Hashtags', 'Timing', 'Hooks']
        result = await self.agent.get_analysis_summary(viral_analysis, clip_optimization)
        assert result.success
        assert 'summary' in result.data
        summary = result.data['summary']
        assert summary['viral_moment_quality'] == 0.8
        assert summary['viral_potential'] == 0.7
        assert 'optimization_highlights' in summary
        assert 'recommendations' in summary