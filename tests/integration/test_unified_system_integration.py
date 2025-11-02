"""Integration Tests for Unified System

This module provides comprehensive integration tests for the unified system,
testing all phases together to ensure proper functionality and performance.
"""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch
import pytest

class TestUnifiedSystemIntegration:
    """Integration tests for the unified system components"""

    @pytest.fixture
    def enable_all_features(self):
        """Enable all unified system features for testing"""
        with patch.multiple('ultimate_discord_intelligence_bot.settings', ENABLE_UNIFIED_KNOWLEDGE=True, ENABLE_UNIFIED_ROUTER=True, ENABLE_UNIFIED_CACHE=True, ENABLE_UNIFIED_ORCHESTRATION=True, ENABLE_AGENT_BRIDGE=True, ENABLE_UNIFIED_METRICS=True, ENABLE_INTELLIGENT_ALERTING=True, ENABLE_DASHBOARD_INTEGRATION=True):
            yield

    @pytest.fixture
    def mock_services(self):
        """Mock external services for testing"""
        with patch('ultimate_discord_intelligence_bot.knowledge.unified_memory.QdrantClient') as mock_qdrant, patch('ultimate_discord_intelligence_bot.knowledge.unified_memory.sqlite3.connect') as mock_sqlite, patch('ultimate_discord_intelligence_bot.observability.unified_metrics.prometheus_client') as mock_prometheus:
            mock_qdrant.return_value = AsyncMock()
            mock_qdrant.return_value.upsert = AsyncMock()
            mock_qdrant.return_value.search = AsyncMock(return_value=[])
            mock_sqlite.return_value = Mock()
            mock_sqlite.return_value.execute = Mock()
            mock_sqlite.return_value.commit = Mock()
            mock_prometheus.Counter = Mock()
            mock_prometheus.Gauge = Mock()
            mock_prometheus.Histogram = Mock()
            yield {'qdrant': mock_qdrant, 'sqlite': mock_sqlite, 'prometheus': mock_prometheus}

    @pytest.mark.asyncio
    async def test_unified_knowledge_layer_integration(self, enable_all_features, mock_services):
        """Test unified knowledge layer integration"""
        from ultimate_discord_intelligence_bot.knowledge import UnifiedContextBuilder, UnifiedMemoryService, UnifiedRetrievalEngine
        memory_service = UnifiedMemoryService()
        retrieval_engine = UnifiedRetrievalEngine()
        context_builder = UnifiedContextBuilder()
        test_content = {'text': 'Test content for integration testing', 'metadata': {'source': 'test', 'timestamp': datetime.now(UTC).isoformat()}, 'embeddings': [0.1, 0.2, 0.3]}
        result = await memory_service.store_content(content=test_content['text'], tenant_id='test_tenant', workspace_id='test_workspace', metadata=test_content['metadata'], embeddings=test_content['embeddings'])
        assert result.success
        assert 'content_id' in result.data
        retrieval_result = await retrieval_engine.retrieve_content(query='test content', tenant_id='test_tenant', workspace_id='test_workspace', limit=5)
        assert retrieval_result.success
        assert isinstance(retrieval_result.data, list)
        context_result = await context_builder.build_context(agent_id='test_agent', agent_type='test_type', query='test query', tenant_id='test_tenant', workspace_id='test_workspace', max_context_length=1000)
        assert context_result.success
        assert 'context' in context_result.data

    @pytest.mark.asyncio
    async def test_unified_router_integration(self, enable_all_features):
        """Test unified router system integration"""
        from ultimate_discord_intelligence_bot.routing import UnifiedCostTracker, UnifiedRouterService
        router_service = UnifiedRouterService()
        cost_tracker = UnifiedCostTracker()
        routing_result = await router_service.route_request(prompt='Test prompt for routing', tenant_id='test_tenant', workspace_id='test_workspace', max_tokens=100, temperature=0.7)
        assert routing_result.success
        assert 'model' in routing_result.data
        assert 'provider' in routing_result.data
        cost_result = await cost_tracker.record_usage(tenant_id='test_tenant', workspace_id='test_workspace', model='test-model', provider='test-provider', input_tokens=50, output_tokens=25, cost=0.001)
        assert cost_result.success

    @pytest.mark.asyncio
    async def test_unified_cache_integration(self, enable_all_features):
        """Test unified cache system integration"""
        from ultimate_discord_intelligence_bot.caching import CacheOptimizer, UnifiedCacheService
        cache_service = UnifiedCacheService()
        cache_optimizer = CacheOptimizer()
        cache_result = await cache_service.store(key='test_key', value='test_value', tenant_id='test_tenant', workspace_id='test_workspace', ttl=3600)
        assert cache_result.success
        retrieval_result = await cache_service.get(key='test_key', tenant_id='test_tenant', workspace_id='test_workspace')
        assert retrieval_result.success
        assert retrieval_result.data == 'test_value'
        optimization_result = await cache_optimizer.optimize_ttl(key='test_key', tenant_id='test_tenant', workspace_id='test_workspace', access_pattern='frequent')
        assert optimization_result.success

    @pytest.mark.asyncio
    async def test_unified_orchestration_integration(self, enable_all_features):
        """Test unified orchestration system integration"""
        from ultimate_discord_intelligence_bot.orchestration import TaskManager, UnifiedOrchestrationService
        orchestrator = UnifiedOrchestrationService()
        task_manager = TaskManager()
        task_result = await orchestrator.submit_task(task_type='test_task', payload={'test': 'data'}, tenant_id='test_tenant', workspace_id='test_workspace', priority='high')
        assert task_result.success
        assert 'task_id' in task_result.data
        management_result = await task_manager.get_task_status(task_id=task_result.data['task_id'], tenant_id='test_tenant', workspace_id='test_workspace')
        assert management_result.success

    @pytest.mark.asyncio
    async def test_agent_bridge_integration(self, enable_all_features):
        """Test agent bridge system integration"""
        from ultimate_discord_intelligence_bot.agent_bridge import AgentBridge, AgentKnowledgeBridge, CollectiveIntelligenceService, CrossAgentLearningService
        agent_bridge = AgentBridge()
        AgentKnowledgeBridge()
        learning_service = CrossAgentLearningService()
        collective_intelligence = CollectiveIntelligenceService()
        insight_result = await agent_bridge.share_insight(agent_id='test_agent_1', agent_type='test_type', insight_type='performance', title='Test Insight', description='Test insight description', context={'test': 'context'}, tags=['test', 'integration'], confidence_score=0.8, priority='medium')
        assert insight_result.success
        retrieval_result = await agent_bridge.request_insights(agent_id='test_agent_2', agent_type='test_type', insight_types=['performance'], limit=5)
        assert retrieval_result.success
        assert isinstance(retrieval_result.data, list)
        learning_result = await learning_service.learn_from_experience(agent_id='test_agent_1', experience_type='success', context={'task': 'test_task', 'outcome': 'success'}, metadata={'duration': 100, 'quality': 0.9})
        assert learning_result.success
        synthesis_result = await collective_intelligence.synthesize_collective_intelligence(synthesis_type='performance_optimization', agent_contributions=[{'agent_id': 'test_agent_1', 'contribution_type': 'insight', 'data': {'insight': 'test'}}], tenant_id='test_tenant', workspace_id='test_workspace')
        assert synthesis_result.success

    @pytest.mark.asyncio
    async def test_observability_integration(self, enable_all_features, mock_services):
        """Test observability system integration"""
        from ultimate_discord_intelligence_bot.observability import DashboardIntegrationService, IntelligentAlertingService, UnifiedMetricsCollector
        metrics_collector = UnifiedMetricsCollector()
        alerting_service = IntelligentAlertingService()
        dashboard_service = DashboardIntegrationService()
        metrics_result = await metrics_collector.collect_system_metric(name='test_metric', value=100.0, metric_type='gauge', category='system', labels={'test': 'integration'}, description='Test metric for integration')
        assert metrics_result.success
        agent_metrics_result = await metrics_collector.collect_agent_metric(agent_id='test_agent', agent_type='test_type', metric_name='task_completion_time', value=150.0, metric_type='histogram', category='agent', labels={'task_type': 'test'})
        assert agent_metrics_result.success
        from ultimate_discord_intelligence_bot.observability.intelligent_alerts import AlertCondition
        alert_result = await alerting_service.create_alert_rule(rule_id='test_rule', name='Test Alert Rule', description='Test alert rule for integration', alert_type='threshold', alert_level='warning', conditions=[AlertCondition(metric_name='test_metric', operator='>', threshold_value=50.0, time_window=300, evaluation_periods=1)], enabled=True)
        assert alert_result.success
        from ultimate_discord_intelligence_bot.observability.dashboard_integration import DashboardWidget, MetricsQuery
        dashboard_result = await dashboard_service.create_grafana_dashboard(dashboard_id='test_dashboard', title='Test Dashboard', description='Test dashboard for integration', dashboard_type='custom', widgets=[DashboardWidget(widget_id='test_widget', title='Test Widget', widget_type='graph', position={'x': 0, 'y': 0, 'width': 12, 'height': 8}, queries=[MetricsQuery(query='test_metric', legend='Test Metric', ref_id='A', interval='1m', range='1h', step='15s')], options={}, thresholds=[])], tags=['test', 'integration'])
        assert dashboard_result.success

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, enable_all_features, mock_services):
        """Test complete end-to-end workflow through all unified systems"""
        from ultimate_discord_intelligence_bot.agent_bridge import AgentBridge
        from ultimate_discord_intelligence_bot.caching import UnifiedCacheService
        from ultimate_discord_intelligence_bot.knowledge import UnifiedMemoryService
        from ultimate_discord_intelligence_bot.observability import UnifiedMetricsCollector
        from ultimate_discord_intelligence_bot.orchestration import UnifiedOrchestrationService
        from ultimate_discord_intelligence_bot.routing import UnifiedRouterService
        memory_service = UnifiedMemoryService()
        router_service = UnifiedRouterService()
        cache_service = UnifiedCacheService()
        orchestrator = UnifiedOrchestrationService()
        agent_bridge = AgentBridge()
        metrics_collector = UnifiedMetricsCollector()
        tenant_id = 'test_tenant'
        workspace_id = 'test_workspace'
        content_result = await memory_service.store_content(content='Test content for end-to-end workflow', tenant_id=tenant_id, workspace_id=workspace_id, metadata={'source': 'integration_test'}, embeddings=[0.1, 0.2, 0.3, 0.4, 0.5])
        assert content_result.success
        content_id = content_result.data['content_id']
        routing_result = await router_service.route_request(prompt='Process the stored content', tenant_id=tenant_id, workspace_id=workspace_id, max_tokens=100, temperature=0.7)
        assert routing_result.success
        cache_result = await cache_service.store(key=f'workflow_result_{content_id}', value=routing_result.data, tenant_id=tenant_id, workspace_id=workspace_id, ttl=3600)
        assert cache_result.success
        task_result = await orchestrator.submit_task(task_type='content_processing', payload={'content_id': content_id, 'routing_result': routing_result.data}, tenant_id=tenant_id, workspace_id=workspace_id, priority='medium')
        assert task_result.success
        insight_result = await agent_bridge.share_insight(agent_id='workflow_agent', agent_type='integration', insight_type='workflow', title='End-to-End Workflow Success', description='Successfully completed end-to-end workflow test', context={'content_id': content_id, 'task_id': task_result.data['task_id']}, tags=['integration', 'workflow', 'success'], confidence_score=1.0, priority='high')
        assert insight_result.success
        metrics_result = await metrics_collector.collect_system_metric(name='end_to_end_workflow_duration', value=1500.0, metric_type='histogram', category='workflow', labels={'workflow_type': 'integration_test'}, description='Duration of end-to-end workflow test')
        assert metrics_result.success
        assert all([content_result.success, routing_result.success, cache_result.success, task_result.success, insight_result.success, metrics_result.success])

    def test_crew_integration_with_unified_systems(self, enable_all_features):
        """Test CrewAI integration with all unified systems"""
        from domains.orchestration.crew import UltimateDiscordIntelligenceBotCrew
        crew = UltimateDiscordIntelligenceBotCrew()
        mission_orchestrator = crew.mission_orchestrator()
        tool_names = [tool.name for tool in mission_orchestrator.tools]
        unified_tools = [tool for tool in tool_names if any((keyword in tool.lower() for keyword in ['unified', 'metrics', 'alert', 'dashboard', 'bridge', 'orchestration', 'cache', 'router']))]
        assert len(unified_tools) > 0, 'Mission orchestrator should have unified system tools'
        executive_supervisor = crew.executive_supervisor()
        tool_names = [tool.name for tool in executive_supervisor.tools]
        unified_tools = [tool for tool in tool_names if any((keyword in tool.lower() for keyword in ['unified', 'metrics', 'alert', 'dashboard', 'bridge', 'orchestration', 'cache', 'router']))]
        assert len(unified_tools) > 0, 'Executive supervisor should have unified system tools'

    @pytest.mark.asyncio
    async def test_error_handling_across_systems(self, enable_all_features):
        """Test error handling across all unified systems"""
        from ultimate_discord_intelligence_bot.caching import UnifiedCacheService
        from ultimate_discord_intelligence_bot.knowledge import UnifiedMemoryService
        from ultimate_discord_intelligence_bot.routing import UnifiedRouterService
        memory_service = UnifiedMemoryService()
        router_service = UnifiedRouterService()
        cache_service = UnifiedCacheService()
        with patch.object(memory_service, '_vector_store') as mock_vector:
            mock_vector.upsert.side_effect = Exception('Vector store error')
            result = await memory_service.store_content(content='Test content', tenant_id='test_tenant', workspace_id='test_workspace')
            assert not result.success
            assert 'error' in result.error.lower()
        with patch.object(router_service, '_openrouter_service') as mock_router:
            mock_router.route.side_effect = Exception('Routing error')
            result = await router_service.route_request(prompt='Test prompt', tenant_id='test_tenant', workspace_id='test_workspace')
            assert not result.success
            assert 'error' in result.error.lower()
        with patch.object(cache_service, '_redis_client') as mock_redis:
            mock_redis.set.side_effect = Exception('Redis error')
            result = await cache_service.store(key='test_key', value='test_value', tenant_id='test_tenant', workspace_id='test_workspace')
            assert not result.success
            assert 'error' in result.error.lower()

    @pytest.mark.asyncio
    async def test_tenant_isolation_across_systems(self, enable_all_features):
        """Test tenant isolation across all unified systems"""
        from ultimate_discord_intelligence_bot.caching import UnifiedCacheService
        from ultimate_discord_intelligence_bot.knowledge import UnifiedMemoryService
        from ultimate_discord_intelligence_bot.routing import UnifiedRouterService
        memory_service = UnifiedMemoryService()
        UnifiedRouterService()
        UnifiedCacheService()
        result1 = await memory_service.store_content(content='Tenant 1 content', tenant_id='tenant_1', workspace_id='workspace_1', metadata={'tenant': '1'})
        assert result1.success
        result2 = await memory_service.store_content(content='Tenant 2 content', tenant_id='tenant_2', workspace_id='workspace_2', metadata={'tenant': '2'})
        assert result2.success
        from ultimate_discord_intelligence_bot.knowledge import UnifiedRetrievalEngine
        retrieval_engine = UnifiedRetrievalEngine()
        search_result1 = await retrieval_engine.retrieve_content(query='content', tenant_id='tenant_1', workspace_id='workspace_1', limit=10)
        assert search_result1.success
        search_result2 = await retrieval_engine.retrieve_content(query='content', tenant_id='tenant_2', workspace_id='workspace_2', limit=10)
        assert search_result2.success
        if search_result1.data and search_result2.data:
            assert search_result1.data != search_result2.data