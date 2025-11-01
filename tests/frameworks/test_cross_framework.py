"""Cross-framework compatibility tests.

This module validates that the universal FrameworkAdapter interface works consistently
across all registered frameworks (CrewAI, LangGraph, AutoGen, LlamaIndex).
"""

from __future__ import annotations

import pytest

from ai.frameworks import get_framework_adapter, list_available_frameworks
from ai.frameworks.protocols import FrameworkFeature
from ultimate_discord_intelligence_bot.crew_core.interfaces import CrewConfig, CrewTask
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestCrossFrameworkCompatibility:
    """Test that all frameworks handle standard tasks consistently."""

    def test_all_frameworks_registered(self) -> None:
        """Test that all 4 framework adapters are registered."""
        frameworks = list_available_frameworks()
        
        # All 4 frameworks should be available
        assert "crewai" in frameworks
        assert "langgraph" in frameworks
        assert "autogen" in frameworks
        assert "llamaindex" in frameworks
        assert len(frameworks) == 4

    def test_adapter_retrieval_consistency(self) -> None:
        """Test that get_framework_adapter returns valid adapters for all frameworks."""
        for framework_name in ["crewai", "langgraph", "autogen", "llamaindex"]:
            adapter = get_framework_adapter(framework_name)
            
            # All adapters should have required properties
            assert adapter.framework_name == framework_name
            assert isinstance(adapter.framework_version, str)
            assert len(adapter.framework_version) > 0

    def test_feature_support_matrix(self) -> None:
        """Test feature support across all frameworks and build comparison matrix."""
        frameworks = ["crewai", "langgraph", "autogen", "llamaindex"]
        
        # Key features to compare
        features_to_check = [
            FrameworkFeature.SEQUENTIAL_EXECUTION,
            FrameworkFeature.PARALLEL_EXECUTION,
            FrameworkFeature.ASYNC_EXECUTION,
            FrameworkFeature.STATE_PERSISTENCE,
            FrameworkFeature.MULTI_AGENT_COLLABORATION,
            FrameworkFeature.CUSTOM_TOOLS,
            FrameworkFeature.STREAMING,
        ]
        
        feature_matrix = {}
        
        for framework_name in frameworks:
            adapter = get_framework_adapter(framework_name)
            feature_matrix[framework_name] = {
                feature: adapter.supports_feature(feature)
                for feature in features_to_check
            }
        
        # Verify expected feature support patterns
        # All frameworks should support sequential execution
        assert all(
            feature_matrix[fw][FrameworkFeature.SEQUENTIAL_EXECUTION]
            for fw in frameworks
        )
        
        # All frameworks should support custom tools
        assert all(
            feature_matrix[fw][FrameworkFeature.CUSTOM_TOOLS]
            for fw in frameworks
        )
        
        # Only LangGraph should support state persistence
        assert feature_matrix["langgraph"][FrameworkFeature.STATE_PERSISTENCE]
        assert not feature_matrix["crewai"][FrameworkFeature.STATE_PERSISTENCE]
        assert not feature_matrix["autogen"][FrameworkFeature.STATE_PERSISTENCE]
        assert not feature_matrix["llamaindex"][FrameworkFeature.STATE_PERSISTENCE]
        
        # Only CrewAI and LangGraph should support parallel execution
        assert feature_matrix["crewai"][FrameworkFeature.PARALLEL_EXECUTION]
        assert feature_matrix["langgraph"][FrameworkFeature.PARALLEL_EXECUTION]
        assert not feature_matrix["autogen"][FrameworkFeature.PARALLEL_EXECUTION]
        assert not feature_matrix["llamaindex"][FrameworkFeature.PARALLEL_EXECUTION]

    def test_capabilities_structure_consistency(self) -> None:
        """Test that all frameworks return consistent capabilities structure."""
        frameworks = ["crewai", "langgraph", "autogen", "llamaindex"]
        
        for framework_name in frameworks:
            adapter = get_framework_adapter(framework_name)
            caps = adapter.get_capabilities()
            
            # All capabilities should have these required fields
            assert "supported_features" in caps
            assert "metadata" in caps
            assert isinstance(caps["supported_features"], list)
            assert isinstance(caps["metadata"], dict)
            
            # Metadata should contain framework name
            assert caps["metadata"]["framework"] == framework_name

    @pytest.mark.asyncio
    async def test_execute_task_interface_consistency(self) -> None:
        """Test that all frameworks accept and execute tasks with consistent interface."""
        # Create a simple test task
        task = CrewTask(
            task_id="cross_framework_test",
            task_type="general",
            description="Simple test task for cross-framework compatibility",
            inputs={"message": "hello world"},
        )
        config = CrewConfig(tenant_id="test")
        
        # Each framework should accept the task and return a StepResult
        frameworks_to_test = ["crewai"]  # Start with CrewAI only for basic validation
        
        for framework_name in frameworks_to_test:
            adapter = get_framework_adapter(framework_name)
            result = await adapter.execute_task(task, config)
            
            # Result should be a StepResult
            assert isinstance(result, StepResult)
            
            # StepResult should have required fields
            assert hasattr(result, "success")
            assert hasattr(result, "data")
            
            # If successful, data should contain ExecutionResult
            if result.success:
                execution_result = result.data
                assert hasattr(execution_result, "success")
                assert hasattr(execution_result, "execution_time_ms")
                assert execution_result.execution_time_ms >= 0

    def test_framework_unique_strengths(self) -> None:
        """Document each framework's unique strengths via feature flags."""
        # CrewAI: Hierarchical orchestration
        crewai = get_framework_adapter("crewai")
        assert crewai.supports_feature(FrameworkFeature.HIERARCHICAL_EXECUTION)
        assert crewai.supports_feature(FrameworkFeature.DYNAMIC_AGENT_CREATION)
        
        # LangGraph: State management
        langgraph = get_framework_adapter("langgraph")
        assert langgraph.supports_feature(FrameworkFeature.STATE_PERSISTENCE)
        assert langgraph.supports_feature(FrameworkFeature.STATE_CHECKPOINTING)
        assert langgraph.supports_feature(FrameworkFeature.STATE_BRANCHING)
        
        # AutoGen: Conversation and human-in-the-loop
        autogen = get_framework_adapter("autogen")
        assert autogen.supports_feature(FrameworkFeature.MULTI_AGENT_COLLABORATION)
        assert autogen.supports_feature(FrameworkFeature.HUMAN_IN_LOOP)
        
        # LlamaIndex: RAG and streaming
        llamaindex = get_framework_adapter("llamaindex")
        assert llamaindex.supports_feature(FrameworkFeature.STREAMING)
        assert llamaindex.supports_feature(FrameworkFeature.TOOL_CHAINING)

    def test_adapter_isolation(self) -> None:
        """Test that framework adapters are properly isolated from each other."""
        # Getting different adapters should return different instances
        crewai_1 = get_framework_adapter("crewai")
        crewai_2 = get_framework_adapter("crewai")
        langgraph = get_framework_adapter("langgraph")
        
        # Same framework should return same adapter class (singleton pattern)
        assert type(crewai_1) is type(crewai_2)
        
        # Different frameworks should return different adapter classes
        assert type(crewai_1) is not type(langgraph)

    def test_error_handling_consistency(self) -> None:
        """Test that all frameworks handle errors consistently."""
        # Invalid framework name should raise ValueError
        with pytest.raises(ValueError, match="Unknown framework"):
            get_framework_adapter("invalid_framework")
        
        # Empty framework name should raise ValueError
        with pytest.raises(ValueError):
            get_framework_adapter("")


class TestFrameworkPerformanceBaseline:
    """Baseline performance tests (no actual execution, just initialization)."""

    def test_adapter_initialization_performance(self) -> None:
        """Test that adapter initialization is fast."""
        import time
        
        frameworks = ["crewai", "langgraph", "autogen", "llamaindex"]
        
        for framework_name in frameworks:
            start = time.time()
            adapter = get_framework_adapter(framework_name)
            end = time.time()
            
            # Adapter initialization should be < 100ms
            init_time_ms = (end - start) * 1000
            assert init_time_ms < 100, f"{framework_name} initialization took {init_time_ms:.2f}ms"
            
            # Adapter should be usable immediately
            assert adapter.framework_name == framework_name

    def test_capabilities_query_performance(self) -> None:
        """Test that capabilities queries are fast."""
        import time
        
        frameworks = ["crewai", "langgraph", "autogen", "llamaindex"]
        
        for framework_name in frameworks:
            adapter = get_framework_adapter(framework_name)
            
            start = time.time()
            caps = adapter.get_capabilities()
            end = time.time()
            
            # Capabilities query should be < 10ms
            query_time_ms = (end - start) * 1000
            assert query_time_ms < 10, f"{framework_name} capabilities query took {query_time_ms:.2f}ms"
            
            # Capabilities should be complete
            assert len(caps["supported_features"]) > 0


class TestFrameworkDocumentation:
    """Test that frameworks provide adequate documentation metadata."""

    def test_all_frameworks_have_metadata(self) -> None:
        """Test that all frameworks provide comprehensive metadata."""
        frameworks = ["crewai", "langgraph", "autogen", "llamaindex"]
        
        for framework_name in frameworks:
            adapter = get_framework_adapter(framework_name)
            caps = adapter.get_capabilities()
            
            # All frameworks should document their limitations
            assert "limitations" in caps
            assert isinstance(caps["limitations"], list)
            
            # All frameworks should declare their state backends
            assert "state_backends" in caps
            assert isinstance(caps["state_backends"], list)

    def test_framework_version_availability(self) -> None:
        """Test that all frameworks report version information."""
        frameworks = ["crewai", "langgraph", "autogen", "llamaindex"]
        
        for framework_name in frameworks:
            adapter = get_framework_adapter(framework_name)
            
            # Version should be available (even if "unknown")
            assert adapter.framework_version is not None
            assert isinstance(adapter.framework_version, str)
            assert len(adapter.framework_version) > 0
