"""Unit tests for orchestrator_utilities module.

Tests all utility functions extracted from autonomous_orchestrator.py:
- get_budget_limits()
- to_thread_with_tenant()
- initialize_agent_workflow_map()
- initialize_workflow_dependencies()
"""

import pytest

from ultimate_discord_intelligence_bot.orchestrator import orchestrator_utilities


# ===================================
# get_budget_limits() Tests
# ===================================


class TestGetBudgetLimits:
    """Tests for depth-based budget calculations."""

    def test_returns_dict_for_standard_depth(self):
        """Should return a dictionary with budget configuration."""
        result = orchestrator_utilities.get_budget_limits("standard")
        assert isinstance(result, dict)

    def test_contains_total_and_per_task_keys(self):
        """Should have 'total' and 'per_task' keys."""
        result = orchestrator_utilities.get_budget_limits("standard")
        assert "total" in result
        assert "per_task" in result

    def test_per_task_is_dict(self):
        """Per-task budgets should be a dictionary."""
        result = orchestrator_utilities.get_budget_limits("standard")
        assert isinstance(result["per_task"], dict)

    # Budget amounts for each depth
    def test_quick_depth_has_050_total(self):
        """Quick depth should have $0.50 total budget."""
        result = orchestrator_utilities.get_budget_limits("quick")
        assert result["total"] == 0.50

    def test_standard_depth_has_150_total(self):
        """Standard depth should have $1.50 total budget."""
        result = orchestrator_utilities.get_budget_limits("standard")
        assert result["total"] == 1.50

    def test_deep_depth_has_300_total(self):
        """Deep depth should have $3.00 total budget."""
        result = orchestrator_utilities.get_budget_limits("deep")
        assert result["total"] == 3.00

    def test_comprehensive_depth_has_500_total(self):
        """Comprehensive depth should have $5.00 total budget."""
        result = orchestrator_utilities.get_budget_limits("comprehensive")
        assert result["total"] == 5.00

    def test_experimental_depth_has_1000_total(self):
        """Experimental depth should have $10.00 total budget."""
        result = orchestrator_utilities.get_budget_limits("experimental")
        assert result["total"] == 10.00

    # Per-task budget structure
    def test_quick_has_3_task_budgets(self):
        """Quick depth should have 3 task budgets (acquisition, transcription, analysis)."""
        result = orchestrator_utilities.get_budget_limits("quick")
        assert len(result["per_task"]) == 3
        assert "acquisition" in result["per_task"]
        assert "transcription" in result["per_task"]
        assert "analysis" in result["per_task"]

    def test_standard_has_4_task_budgets(self):
        """Standard depth should have 4 task budgets (+verification)."""
        result = orchestrator_utilities.get_budget_limits("standard")
        assert len(result["per_task"]) == 4
        assert "verification" in result["per_task"]

    def test_deep_has_5_task_budgets(self):
        """Deep depth should have 5 task budgets (+knowledge)."""
        result = orchestrator_utilities.get_budget_limits("deep")
        assert len(result["per_task"]) == 5
        assert "knowledge" in result["per_task"]

    def test_comprehensive_has_5_task_budgets(self):
        """Comprehensive depth should have 5 task budgets."""
        result = orchestrator_utilities.get_budget_limits("comprehensive")
        assert len(result["per_task"]) == 5

    def test_experimental_has_5_task_budgets(self):
        """Experimental depth should have 5 task budgets."""
        result = orchestrator_utilities.get_budget_limits("experimental")
        assert len(result["per_task"]) == 5

    # Budget monotonicity (higher depths = higher budgets)
    def test_budgets_increase_with_depth(self):
        """Total budgets should increase with depth level."""
        quick = orchestrator_utilities.get_budget_limits("quick")["total"]
        standard = orchestrator_utilities.get_budget_limits("standard")["total"]
        deep = orchestrator_utilities.get_budget_limits("deep")["total"]
        comprehensive = orchestrator_utilities.get_budget_limits("comprehensive")["total"]
        experimental = orchestrator_utilities.get_budget_limits("experimental")["total"]

        assert quick < standard < deep < comprehensive < experimental

    def test_analysis_budget_increases_with_depth(self):
        """Analysis task budget should increase with depth."""
        quick = orchestrator_utilities.get_budget_limits("quick")["per_task"]["analysis"]
        standard = orchestrator_utilities.get_budget_limits("standard")["per_task"]["analysis"]
        deep = orchestrator_utilities.get_budget_limits("deep")["per_task"]["analysis"]
        comprehensive = orchestrator_utilities.get_budget_limits("comprehensive")["per_task"]["analysis"]
        experimental = orchestrator_utilities.get_budget_limits("experimental")["per_task"]["analysis"]

        assert quick < standard < deep < comprehensive < experimental

    # Unknown depth fallback
    def test_unknown_depth_defaults_to_standard(self):
        """Unknown depth should fall back to standard budget."""
        result = orchestrator_utilities.get_budget_limits("unknown_depth")
        standard = orchestrator_utilities.get_budget_limits("standard")
        assert result == standard

    def test_empty_string_defaults_to_standard(self):
        """Empty string should fall back to standard budget."""
        result = orchestrator_utilities.get_budget_limits("")
        standard = orchestrator_utilities.get_budget_limits("standard")
        assert result == standard

    # Consistency checks
    def test_same_depth_returns_same_budget(self):
        """Calling with same depth should return identical results."""
        result1 = orchestrator_utilities.get_budget_limits("deep")
        result2 = orchestrator_utilities.get_budget_limits("deep")
        assert result1 == result2

    def test_all_per_task_budgets_are_positive(self):
        """All per-task budgets should be positive numbers."""
        for depth in ["quick", "standard", "deep", "comprehensive", "experimental"]:
            result = orchestrator_utilities.get_budget_limits(depth)
            for task, budget in result["per_task"].items():
                assert budget > 0, f"{depth}/{task} budget should be positive"


# ===================================
# to_thread_with_tenant() Tests
# ===================================


class TestToThreadWithTenant:
    """Tests for tenant-aware thread execution."""

    @pytest.mark.asyncio
    async def test_executes_sync_function_in_thread(self):
        """Should execute synchronous function in a thread."""

        def sync_func():
            return "result"

        result = await orchestrator_utilities.to_thread_with_tenant(sync_func)
        assert result == "result"

    @pytest.mark.asyncio
    async def test_passes_positional_arguments(self):
        """Should pass positional arguments to the function."""

        def sync_func(a, b):
            return a + b

        result = await orchestrator_utilities.to_thread_with_tenant(sync_func, 5, 3)
        assert result == 8

    @pytest.mark.asyncio
    async def test_passes_keyword_arguments(self):
        """Should pass keyword arguments to the function."""

        def sync_func(x=0, y=0):
            return x * y

        result = await orchestrator_utilities.to_thread_with_tenant(sync_func, x=4, y=5)
        assert result == 20

    @pytest.mark.asyncio
    async def test_passes_mixed_arguments(self):
        """Should pass both positional and keyword arguments."""

        def sync_func(a, b, c=10):
            return a + b + c

        result = await orchestrator_utilities.to_thread_with_tenant(sync_func, 1, 2, c=3)
        assert result == 6

    @pytest.mark.asyncio
    async def test_handles_function_exceptions(self):
        """Should propagate exceptions from the executed function."""

        def failing_func():
            raise ValueError("test error")

        try:
            await orchestrator_utilities.to_thread_with_tenant(failing_func)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert str(e) == "test error"

    @pytest.mark.asyncio
    async def test_returns_none_when_function_returns_none(self):
        """Should return None when function returns None."""

        def none_func():
            return None

        result = await orchestrator_utilities.to_thread_with_tenant(none_func)
        assert result is None

    @pytest.mark.asyncio
    async def test_handles_complex_return_types(self):
        """Should handle complex return types (dicts, lists, etc.)."""

        def complex_func():
            return {"key": "value", "list": [1, 2, 3]}

        result = await orchestrator_utilities.to_thread_with_tenant(complex_func)
        assert result == {"key": "value", "list": [1, 2, 3]}


# ===================================
# initialize_agent_workflow_map() Tests
# ===================================


class TestInitializeAgentWorkflowMap:
    """Tests for agent workflow mapping initialization."""

    def test_returns_dict(self):
        """Should return a dictionary."""
        result = orchestrator_utilities.initialize_agent_workflow_map()
        assert isinstance(result, dict)

    def test_has_15_workflow_mappings(self):
        """Should have 15 workflow-to-agent mappings."""
        result = orchestrator_utilities.initialize_agent_workflow_map()
        assert len(result) == 15

    def test_all_keys_are_strings(self):
        """All workflow names should be strings."""
        result = orchestrator_utilities.initialize_agent_workflow_map()
        assert all(isinstance(k, str) for k in result.keys())

    def test_all_values_are_strings(self):
        """All agent method names should be strings."""
        result = orchestrator_utilities.initialize_agent_workflow_map()
        assert all(isinstance(v, str) for v in result.values())

    # Key workflow mappings
    def test_mission_coordination_maps_to_coordinator(self):
        """Mission coordination should map to autonomous_mission_coordinator."""
        result = orchestrator_utilities.initialize_agent_workflow_map()
        assert result["mission_coordination"] == "autonomous_mission_coordinator"

    def test_content_acquisition_maps_to_specialist(self):
        """Content acquisition should map to multi_platform_acquisition_specialist."""
        result = orchestrator_utilities.initialize_agent_workflow_map()
        assert result["content_acquisition"] == "multi_platform_acquisition_specialist"

    def test_transcription_maps_to_engineer(self):
        """Transcription processing should map to advanced_transcription_engineer."""
        result = orchestrator_utilities.initialize_agent_workflow_map()
        assert result["transcription_processing"] == "advanced_transcription_engineer"

    def test_content_analysis_maps_to_analyst(self):
        """Content analysis should map to comprehensive_linguistic_analyst."""
        result = orchestrator_utilities.initialize_agent_workflow_map()
        assert result["content_analysis"] == "comprehensive_linguistic_analyst"

    def test_verification_maps_to_director(self):
        """Information verification should map to information_verification_director."""
        result = orchestrator_utilities.initialize_agent_workflow_map()
        assert result["information_verification"] == "information_verification_director"

    def test_threat_analysis_maps_to_analyst(self):
        """Threat analysis should map to threat_intelligence_analyst."""
        result = orchestrator_utilities.initialize_agent_workflow_map()
        assert result["threat_analysis"] == "threat_intelligence_analyst"

    def test_knowledge_integration_maps_to_architect(self):
        """Knowledge integration should map to knowledge_integration_architect."""
        result = orchestrator_utilities.initialize_agent_workflow_map()
        assert result["knowledge_integration"] == "knowledge_integration_architect"

    def test_intelligence_briefing_maps_to_director(self):
        """Intelligence briefing should map to intelligence_briefing_director."""
        result = orchestrator_utilities.initialize_agent_workflow_map()
        assert result["intelligence_briefing"] == "intelligence_briefing_director"

    # Consistency checks
    def test_no_duplicate_agent_names(self):
        """Each agent method should be used only once."""
        result = orchestrator_utilities.initialize_agent_workflow_map()
        values = list(result.values())
        assert len(values) == len(set(values)), "Agent methods should be unique"

    def test_consistent_results_across_calls(self):
        """Multiple calls should return identical mappings."""
        result1 = orchestrator_utilities.initialize_agent_workflow_map()
        result2 = orchestrator_utilities.initialize_agent_workflow_map()
        assert result1 == result2


# ===================================
# initialize_workflow_dependencies() Tests
# ===================================


class TestInitializeWorkflowDependencies:
    """Tests for workflow dependency graph initialization."""

    def test_returns_dict(self):
        """Should return a dictionary."""
        result = orchestrator_utilities.initialize_workflow_dependencies()
        assert isinstance(result, dict)

    def test_has_15_workflow_dependencies(self):
        """Should have dependencies for all 15 workflows."""
        result = orchestrator_utilities.initialize_workflow_dependencies()
        assert len(result) == 15

    def test_all_keys_are_strings(self):
        """All workflow names should be strings."""
        result = orchestrator_utilities.initialize_workflow_dependencies()
        assert all(isinstance(k, str) for k in result.keys())

    def test_all_values_are_lists(self):
        """All dependencies should be lists."""
        result = orchestrator_utilities.initialize_workflow_dependencies()
        assert all(isinstance(v, list) for v in result.values())

    def test_all_dependency_items_are_strings(self):
        """All items in dependency lists should be strings."""
        result = orchestrator_utilities.initialize_workflow_dependencies()
        for deps in result.values():
            assert all(isinstance(dep, str) for dep in deps)

    # Entry points (no dependencies)
    def test_mission_coordination_has_no_dependencies(self):
        """Mission coordination should be an entry point (no dependencies)."""
        result = orchestrator_utilities.initialize_workflow_dependencies()
        assert result["mission_coordination"] == []

    def test_system_operations_has_no_dependencies(self):
        """System operations should be independent (no dependencies)."""
        result = orchestrator_utilities.initialize_workflow_dependencies()
        assert result["system_operations"] == []

    # Linear dependencies
    def test_content_acquisition_depends_on_mission(self):
        """Content acquisition should depend on mission coordination."""
        result = orchestrator_utilities.initialize_workflow_dependencies()
        assert result["content_acquisition"] == ["mission_coordination"]

    def test_transcription_depends_on_acquisition(self):
        """Transcription should depend on content acquisition."""
        result = orchestrator_utilities.initialize_workflow_dependencies()
        assert result["transcription_processing"] == ["content_acquisition"]

    def test_content_analysis_depends_on_transcription(self):
        """Content analysis should depend on transcription."""
        result = orchestrator_utilities.initialize_workflow_dependencies()
        assert result["content_analysis"] == ["transcription_processing"]

    # Multi-dependency workflows
    def test_knowledge_integration_has_3_dependencies(self):
        """Knowledge integration should depend on 3 workflows."""
        result = orchestrator_utilities.initialize_workflow_dependencies()
        deps = result["knowledge_integration"]
        assert len(deps) == 3
        assert "information_verification" in deps
        assert "threat_analysis" in deps
        assert "behavioral_profiling" in deps

    def test_intelligence_briefing_has_2_dependencies(self):
        """Intelligence briefing should depend on 2 workflows."""
        result = orchestrator_utilities.initialize_workflow_dependencies()
        deps = result["intelligence_briefing"]
        assert len(deps) == 2
        assert "knowledge_integration" in deps
        assert "research_synthesis" in deps

    # Parallel execution candidates
    def test_social_intelligence_can_run_parallel_with_verification(self):
        """Social intelligence only depends on content analysis (can run parallel with verification)."""
        result = orchestrator_utilities.initialize_workflow_dependencies()
        assert result["social_intelligence"] == ["content_analysis"]

    # No circular dependencies
    def test_no_self_dependencies(self):
        """No workflow should depend on itself."""
        result = orchestrator_utilities.initialize_workflow_dependencies()
        for workflow, deps in result.items():
            assert workflow not in deps, f"{workflow} should not depend on itself"

    # Consistency checks
    def test_all_dependencies_exist_as_workflows(self):
        """All dependency references should point to valid workflows."""
        result = orchestrator_utilities.initialize_workflow_dependencies()
        all_workflows = set(result.keys())
        for deps in result.values():
            for dep in deps:
                assert dep in all_workflows, f"Dependency '{dep}' should be a valid workflow"

    def test_consistent_results_across_calls(self):
        """Multiple calls should return identical dependency graphs."""
        result1 = orchestrator_utilities.initialize_workflow_dependencies()
        result2 = orchestrator_utilities.initialize_workflow_dependencies()
        assert result1 == result2

    # Workflow count validation
    def test_matches_agent_workflow_map_size(self):
        """Should have same number of workflows as agent map."""
        deps = orchestrator_utilities.initialize_workflow_dependencies()
        agent_map = orchestrator_utilities.initialize_agent_workflow_map()
        assert len(deps) == len(agent_map)

    def test_workflow_names_match_agent_map_keys(self):
        """Workflow names should match agent map keys."""
        deps = orchestrator_utilities.initialize_workflow_dependencies()
        agent_map = orchestrator_utilities.initialize_agent_workflow_map()
        assert set(deps.keys()) == set(agent_map.keys())
