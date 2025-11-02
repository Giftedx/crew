"""
Comprehensive test suite for Platform Expansion components.

Tests social media monitoring, content discovery, cross-platform analytics,
and platform integration capabilities.
"""
import asyncio
import time
import pytest
from platform.core.platform.analytics_query import AnalyticsMetric, AnalyticsQuery, TimeGranularity
from platform.core.platform.content_discovery import ContentDiscovery, DiscoveryQuery
from platform.core.platform.platform_integration import AuthType, PlatformConfig, PlatformIntegration, SyncMode
from platform.core.platform.social_content import ContentType, PlatformType, SocialContent
from platform.core.platform.social_monitor import SocialMonitor
try:
    from platform.core.platform.cross_platform_analytics import CrossPlatformAnalytics
except Exception:
    CrossPlatformAnalytics = None

class TestSocialMonitor:
    """Test social media monitoring capabilities."""

    @pytest.fixture
    def social_monitor(self):
        """Create social monitor instance."""
        return SocialMonitor()

    @pytest.fixture
    def sample_content(self):
        """Create sample social content."""
        return SocialContent(content_id='test_content_1', platform=PlatformType.TWITTER, content_type=ContentType.TEXT, author_id='user_123', author_name='Test User', text_content='This is a test post about AI and technology', hashtags=['#AI', '#technology'], engagement_metrics={'likes': 150, 'shares': 25, 'comments': 10}, timestamp=time.time(), language='en')

    @pytest.mark.asyncio
    async def test_social_monitor_initialization(self, social_monitor):
        """Test social monitor initialization."""
        assert social_monitor is not None
        assert social_monitor.monitoring_configs == {}
        assert social_monitor.content_cache == {}
        assert social_monitor.alert_rules == []

    @pytest.mark.asyncio
    async def test_start_monitoring(self, social_monitor):
        """Test starting monitoring."""
        config_id = 'test_config'
        result = await social_monitor.start_monitoring(config_id)
        assert result is not None
        assert config_id in social_monitor.monitoring_configs

    @pytest.mark.asyncio
    async def test_stop_monitoring(self, social_monitor):
        """Test stopping monitoring."""
        config_id = 'test_config'
        await social_monitor.start_monitoring(config_id)
        result = await social_monitor.stop_monitoring(config_id)
        assert result is True
        assert config_id not in social_monitor.monitoring_configs

    @pytest.mark.asyncio
    async def test_monitor_content(self, social_monitor, sample_content):
        """Test content monitoring."""
        config_id = 'test_config'
        await social_monitor.start_monitoring(config_id)
        result = await social_monitor.monitor_content(sample_content)
        assert result is not None
        assert result.monitored_content == 1
        assert result.alerts_triggered == 0

    @pytest.mark.asyncio
    async def test_add_alert_rule(self, social_monitor):
        """Test adding alert rule."""
        rule_id = 'test_rule'
        keywords = ['AI', 'technology']
        result = await social_monitor.add_alert_rule(rule_id, keywords)
        assert result is True
        assert len(social_monitor.alert_rules) == 1

    @pytest.mark.asyncio
    async def test_analyze_trends(self, social_monitor):
        """Test trend analysis."""
        for i in range(5):
            content = SocialContent(content_id=f'trend_content_{i}', platform=PlatformType.TWITTER, content_type=ContentType.TEXT, author_id=f'user_{i}', author_name=f'User {i}', text_content=f'Trending content about AI {i}', hashtags=['#AI'], engagement_metrics={'likes': 100 + i * 10, 'shares': 10 + i}, timestamp=time.time() - i * 3600, language='en')
            social_monitor.content_cache[content.content_id] = content
        result = await social_monitor.analyze_trends(24)
        assert result is not None
        assert 'trending_keywords' in result
        assert 'trend_velocity' in result

    @pytest.mark.asyncio
    async def test_get_monitoring_statistics(self, social_monitor):
        """Test getting monitoring statistics."""
        stats = await social_monitor.get_monitoring_statistics()
        assert stats is not None
        assert 'total_content_monitored' in stats
        assert 'active_monitoring_configs' in stats

class TestContentDiscovery:
    """Test content discovery capabilities."""

    @pytest.fixture
    def content_discovery(self):
        """Create content discovery instance."""
        return ContentDiscovery()

    @pytest.fixture
    def sample_discovery_query(self):
        """Create sample discovery query."""
        return DiscoveryQuery(query_id='test_query', keywords=['AI', 'technology'], platforms=[PlatformType.TWITTER, PlatformType.FACEBOOK], content_types=[ContentType.TEXT], max_results=50)

    @pytest.mark.asyncio
    async def test_content_discovery_initialization(self, content_discovery):
        """Test content discovery initialization."""
        assert content_discovery is not None
        assert content_discovery.active_queries == {}
        assert content_discovery.content_index == {}
        assert content_discovery.cluster_cache == {}

    @pytest.mark.asyncio
    async def test_discover_content(self, content_discovery, sample_discovery_query):
        """Test content discovery."""
        result = await content_discovery.discover_content(sample_discovery_query)
        assert result is not None
        assert result.query_id == sample_discovery_query.query_id
        assert result.total_matches >= 0
        assert result.filtered_matches >= 0

    @pytest.mark.asyncio
    async def test_get_content_recommendations(self, content_discovery):
        """Test content recommendations."""
        user_profile = {'interests': ['AI', 'technology']}
        recommendations = await content_discovery.get_content_recommendations(user_profile, 10)
        assert isinstance(recommendations, list)

    @pytest.mark.asyncio
    async def test_track_content_performance(self, content_discovery):
        """Test content performance tracking."""
        content_id = 'test_content'
        content = SocialContent(content_id=content_id, platform=PlatformType.TWITTER, content_type=ContentType.TEXT, author_id='user_123', author_name='Test User', text_content='Test content', hashtags=[], engagement_metrics={'likes': 100, 'shares': 10}, timestamp=time.time(), language='en')
        content_discovery.content_index[content_id] = content
        result = await content_discovery.track_content_performance(content_id, 24)
        assert result is not None
        assert 'content_id' in result
        assert 'engagement_growth' in result

    @pytest.mark.asyncio
    async def test_analyze_content_trends(self, content_discovery):
        """Test content trend analysis."""
        for i in range(10):
            content = SocialContent(content_id=f'trend_content_{i}', platform=PlatformType.TWITTER, content_type=ContentType.TEXT, author_id=f'user_{i}', author_name=f'User {i}', text_content=f'Content about AI and machine learning {i}', hashtags=['#AI', '#ML'], engagement_metrics={'likes': 50 + i * 5, 'shares': 5 + i}, timestamp=time.time() - i * 3600, language='en')
            content_discovery.content_index[content.content_id] = content
        result = await content_discovery.analyze_content_trends(24)
        assert result is not None
        assert 'total_content' in result
        assert 'platform_distribution' in result

    @pytest.mark.asyncio
    async def test_get_discovery_statistics(self, content_discovery):
        """Test getting discovery statistics."""
        stats = await content_discovery.get_discovery_statistics()
        assert stats is not None
        assert 'total_queries' in stats
        assert 'successful_queries' in stats

class TestCrossPlatformAnalytics:
    """Test cross-platform analytics capabilities."""

    @pytest.fixture
    def cross_platform_analytics(self):
        """Create cross-platform analytics instance."""
        if CrossPlatformAnalytics is None:
            pytest.skip('CrossPlatformAnalytics not available in this environment')
        return CrossPlatformAnalytics()

    @pytest.fixture
    def sample_analytics_query(self):
        """Create sample analytics query."""
        return AnalyticsQuery(query_id='test_analytics', metrics=[AnalyticsMetric.ENGAGEMENT_RATE, AnalyticsMetric.REACH], platforms=[PlatformType.TWITTER, PlatformType.FACEBOOK], time_range=(time.time() - 86400, time.time()), time_granularity=TimeGranularity.DAILY)

    @pytest.mark.asyncio
    async def test_cross_platform_analytics_initialization(self, cross_platform_analytics):
        """Test cross-platform analytics initialization."""
        assert cross_platform_analytics is not None
        assert cross_platform_analytics.content_data == {}
        assert cross_platform_analytics.analytics_cache == {}
        assert cross_platform_analytics.insights_history == []

    @pytest.mark.asyncio
    async def test_analyze_cross_platform_performance(self, cross_platform_analytics, sample_analytics_query):
        """Test cross-platform performance analysis."""
        for i in range(10):
            content = SocialContent(content_id=f'analytics_content_{i}', platform=PlatformType.TWITTER if i % 2 == 0 else PlatformType.FACEBOOK, content_type=ContentType.TEXT, author_id=f'user_{i}', author_name=f'User {i}', text_content=f'Analytics test content {i}', hashtags=['#analytics'], engagement_metrics={'likes': 100 + i * 10, 'shares': 10 + i}, timestamp=time.time() - i * 3600, language='en')
            cross_platform_analytics.content_data[content.content_id] = content
        result = await cross_platform_analytics.analyze_cross_platform_performance(sample_analytics_query)
        assert result is not None
        assert result.query_id == sample_analytics_query.query_id
        assert result.total_data_points >= 0

    @pytest.mark.asyncio
    async def test_compare_platform_performance(self, cross_platform_analytics):
        """Test platform performance comparison."""
        platforms = [PlatformType.TWITTER, PlatformType.FACEBOOK]
        time_range = (time.time() - 86400, time.time())
        result = await cross_platform_analytics.compare_platform_performance(platforms, time_range)
        assert result is not None
        assert 'platforms' in result
        assert 'insights' in result

    @pytest.mark.asyncio
    async def test_analyze_content_virality(self, cross_platform_analytics):
        """Test content virality analysis."""
        content = []
        for i in range(20):
            viral_content = SocialContent(content_id=f'viral_content_{i}', platform=PlatformType.TWITTER, content_type=ContentType.TEXT, author_id=f'user_{i}', author_name=f'User {i}', text_content=f'Viral content about trending topic {i}', hashtags=['#viral', '#trending'], engagement_metrics={'likes': 1000 + i * 100, 'shares': 100 + i * 10}, timestamp=time.time() - i * 1800, language='en')
            content.append(viral_content)
        result = await cross_platform_analytics.analyze_content_virality(content, 24)
        assert result is not None
        assert 'total_content' in result
        assert 'viral_content' in result

    @pytest.mark.asyncio
    async def test_track_campaign_performance(self, cross_platform_analytics):
        """Test campaign performance tracking."""
        campaign_id = 'test_campaign'
        platforms = [PlatformType.TWITTER, PlatformType.FACEBOOK]
        result = await cross_platform_analytics.track_campaign_performance(campaign_id, platforms)
        assert result is not None
        assert result['campaign_id'] == campaign_id
        assert 'platforms' in result

    @pytest.mark.asyncio
    async def test_generate_executive_dashboard(self, cross_platform_analytics):
        """Test executive dashboard generation."""
        time_range = (time.time() - 86400, time.time())
        platforms = [PlatformType.TWITTER, PlatformType.FACEBOOK]
        result = await cross_platform_analytics.generate_executive_dashboard(time_range, platforms)
        assert result is not None
        assert 'time_range' in result
        assert 'key_metrics' in result

    @pytest.mark.asyncio
    async def test_get_analytics_statistics(self, cross_platform_analytics):
        """Test getting analytics statistics."""
        stats = await cross_platform_analytics.get_analytics_statistics()
        assert stats is not None
        assert 'total_queries' in stats
        assert 'successful_queries' in stats

class TestPlatformIntegration:
    """Test platform integration capabilities."""

    @pytest.fixture
    def platform_integration(self):
        """Create platform integration instance."""
        return PlatformIntegration()

    @pytest.fixture
    def sample_platform_config(self):
        """Create sample platform config."""
        return PlatformConfig(platform=PlatformType.TWITTER, api_endpoint='https://api.twitter.com/2', auth_type=AuthType.OAUTH2, credentials={'client_id': 'test_id', 'client_secret': 'test_secret'}, rate_limits={'requests': 1000, 'content_fetch': 100}, sync_mode=SyncMode.REAL_TIME, enabled=True)

    @pytest.mark.asyncio
    async def test_platform_integration_initialization(self, platform_integration):
        """Test platform integration initialization."""
        assert platform_integration is not None
        assert platform_integration.platform_configs == {}
        assert platform_integration.integration_metrics == {}
        assert platform_integration.active_syncs == {}

    @pytest.mark.asyncio
    async def test_register_platform(self, platform_integration, sample_platform_config):
        """Test platform registration."""
        result = await platform_integration.register_platform(sample_platform_config)
        assert result is True
        assert PlatformType.TWITTER in platform_integration.platform_configs

    @pytest.mark.asyncio
    async def test_authenticate_platform(self, platform_integration, sample_platform_config):
        """Test platform authentication."""
        await platform_integration.register_platform(sample_platform_config)
        credentials = {'access_token': 'test_token'}
        result = await platform_integration.authenticate_platform(PlatformType.TWITTER, credentials)
        assert result is True

    @pytest.mark.asyncio
    async def test_start_sync(self, platform_integration, sample_platform_config):
        """Test starting sync."""
        await platform_integration.register_platform(sample_platform_config)
        result = await platform_integration.start_sync(PlatformType.TWITTER)
        assert result is True
        assert PlatformType.TWITTER in platform_integration.active_syncs

    @pytest.mark.asyncio
    async def test_stop_sync(self, platform_integration, sample_platform_config):
        """Test stopping sync."""
        await platform_integration.register_platform(sample_platform_config)
        await platform_integration.start_sync(PlatformType.TWITTER)
        result = await platform_integration.stop_sync(PlatformType.TWITTER)
        assert result is True
        assert PlatformType.TWITTER not in platform_integration.active_syncs

    @pytest.mark.asyncio
    async def test_sync_content(self, platform_integration, sample_platform_config):
        """Test content synchronization."""
        await platform_integration.register_platform(sample_platform_config)
        result = await platform_integration.sync_content(PlatformType.TWITTER)
        assert result is not None
        assert result.platform == PlatformType.TWITTER
        assert result.content_synced >= 0

    @pytest.mark.asyncio
    async def test_post_content(self, platform_integration, sample_platform_config):
        """Test posting content."""
        await platform_integration.register_platform(sample_platform_config)
        content = SocialContent(content_id='test_post', platform=PlatformType.TWITTER, content_type=ContentType.TEXT, author_id='user_123', author_name='Test User', text_content='Test post content', hashtags=['#test'], engagement_metrics={}, timestamp=time.time(), language='en')
        result = await platform_integration.post_content(PlatformType.TWITTER, content)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_get_platform_status(self, platform_integration, sample_platform_config):
        """Test getting platform status."""
        await platform_integration.register_platform(sample_platform_config)
        result = await platform_integration.get_platform_status(PlatformType.TWITTER)
        assert result is not None
        assert 'platform' in result
        assert 'status' in result

    @pytest.mark.asyncio
    async def test_get_all_platforms_status(self, platform_integration, sample_platform_config):
        """Test getting all platforms status."""
        await platform_integration.register_platform(sample_platform_config)
        result = await platform_integration.get_all_platforms_status()
        assert result is not None
        assert 'platforms' in result
        assert 'total_platforms' in result

    @pytest.mark.asyncio
    async def test_update_platform_config(self, platform_integration, sample_platform_config):
        """Test updating platform configuration."""
        await platform_integration.register_platform(sample_platform_config)
        updates = {'sync_interval': 600, 'enabled': False}
        result = await platform_integration.update_platform_config(PlatformType.TWITTER, updates)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_integration_statistics(self, platform_integration):
        """Test getting integration statistics."""
        stats = await platform_integration.get_integration_statistics()
        assert stats is not None
        assert 'total_platforms' in stats
        assert 'active_platforms' in stats

class TestPlatformExpansionIntegration:
    """Integration tests for platform expansion components."""

    @pytest.mark.asyncio
    async def test_end_to_end_platform_monitoring(self):
        """Test end-to-end platform monitoring workflow."""
        social_monitor = SocialMonitor()
        platform_integration = PlatformIntegration()
        config = PlatformConfig(platform=PlatformType.TWITTER, api_endpoint='https://api.twitter.com/2', auth_type=AuthType.OAUTH2, credentials={'client_id': 'test', 'client_secret': 'test'}, sync_mode=SyncMode.REAL_TIME)
        await platform_integration.register_platform(config)
        await platform_integration.authenticate_platform(PlatformType.TWITTER, {'access_token': 'test'})
        await social_monitor.start_monitoring('test_config')
        sync_result = await platform_integration.sync_content(PlatformType.TWITTER)
        assert sync_result is not None
        assert sync_result.success is True
        monitor_stats = await social_monitor.get_monitoring_statistics()
        integration_stats = await platform_integration.get_integration_statistics()
        assert monitor_stats is not None
        assert integration_stats is not None

    @pytest.mark.asyncio
    async def test_cross_platform_analytics_workflow(self):
        """Test cross-platform analytics workflow."""
        analytics = CrossPlatformAnalytics()
        discovery = ContentDiscovery()
        query = AnalyticsQuery(query_id='integration_test', metrics=[AnalyticsMetric.ENGAGEMENT_RATE, AnalyticsMetric.REACH], platforms=[PlatformType.TWITTER, PlatformType.FACEBOOK], time_range=(time.time() - 3600, time.time()))
        result = await analytics.analyze_cross_platform_performance(query)
        assert result is not None
        assert result.query_id == query.query_id
        discovery_query = DiscoveryQuery(query_id='discovery_test', keywords=['AI', 'technology'], platforms=[PlatformType.TWITTER], max_results=20)
        discovery_result = await discovery.discover_content(discovery_query)
        assert discovery_result is not None
        assert discovery_result.query_id == discovery_query.query_id

    @pytest.mark.asyncio
    async def test_platform_expansion_performance(self):
        """Test platform expansion performance."""
        social_monitor = SocialMonitor()
        content_discovery = ContentDiscovery()
        tasks = []
        for i in range(5):
            task = social_monitor.start_monitoring(f'config_{i}')
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        assert all(results)
        assert len(social_monitor.monitoring_configs) == 5
        discovery_tasks = []
        for i in range(3):
            query = DiscoveryQuery(query_id=f'discovery_{i}', keywords=['test'], platforms=[PlatformType.TWITTER])
            task = content_discovery.discover_content(query)
            discovery_tasks.append(task)
        discovery_results = await asyncio.gather(*discovery_tasks)
        assert len(discovery_results) == 3
        assert all((result.query_id.startswith('discovery_') for result in discovery_results))
if __name__ == '__main__':
    pytest.main([__file__])