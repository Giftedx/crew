"""
Unit tests for orchestrator/workflow_planners module.

Tests all workflow planning functions in isolation:
- get_available_capabilities
- estimate_workflow_duration
- get_planned_stages
- get_capabilities_summary
"""

from ultimate_discord_intelligence_bot.orchestrator import workflow_planners


class TestGetAvailableCapabilities:
    """Test get_available_capabilities function."""

    def test_returns_list_of_capabilities(self):
        """Test that function returns a list."""
        capabilities = workflow_planners.get_available_capabilities()

        assert isinstance(capabilities, list)

    def test_returns_15_capabilities(self):
        """Test that exactly 15 capabilities are returned."""
        capabilities = workflow_planners.get_available_capabilities()

        assert len(capabilities) == 15

    def test_all_capabilities_are_strings(self):
        """Test that all capabilities are string identifiers."""
        capabilities = workflow_planners.get_available_capabilities()

        assert all(isinstance(cap, str) for cap in capabilities)

    def test_all_capabilities_are_non_empty(self):
        """Test that no capability is an empty string."""
        capabilities = workflow_planners.get_available_capabilities()

        assert all(len(cap) > 0 for cap in capabilities)

    def test_contains_multi_platform_content_acquisition(self):
        """Test that core acquisition capability is present."""
        capabilities = workflow_planners.get_available_capabilities()

        assert "multi_platform_content_acquisition" in capabilities

    def test_contains_advanced_transcription_indexing(self):
        """Test that transcription capability is present."""
        capabilities = workflow_planners.get_available_capabilities()

        assert "advanced_transcription_indexing" in capabilities

    def test_contains_comprehensive_linguistic_analysis(self):
        """Test that linguistic analysis capability is present."""
        capabilities = workflow_planners.get_available_capabilities()

        assert "comprehensive_linguistic_analysis" in capabilities

    def test_contains_multi_source_fact_verification(self):
        """Test that fact verification capability is present."""
        capabilities = workflow_planners.get_available_capabilities()

        assert "multi_source_fact_verification" in capabilities

    def test_contains_advanced_threat_deception_analysis(self):
        """Test that threat analysis capability is present."""
        capabilities = workflow_planners.get_available_capabilities()

        assert "advanced_threat_deception_analysis" in capabilities

    def test_contains_cross_platform_social_intelligence(self):
        """Test that social intelligence capability is present."""
        capabilities = workflow_planners.get_available_capabilities()

        assert "cross_platform_social_intelligence" in capabilities

    def test_contains_behavioral_profiling_persona_analysis(self):
        """Test that behavioral profiling capability is present."""
        capabilities = workflow_planners.get_available_capabilities()

        assert "behavioral_profiling_persona_analysis" in capabilities

    def test_contains_multi_layer_knowledge_integration(self):
        """Test that knowledge integration capability is present."""
        capabilities = workflow_planners.get_available_capabilities()

        assert "multi_layer_knowledge_integration" in capabilities

    def test_contains_research_synthesis_context_building(self):
        """Test that research synthesis capability is present."""
        capabilities = workflow_planners.get_available_capabilities()

        assert "research_synthesis_context_building" in capabilities

    def test_contains_predictive_performance_analytics(self):
        """Test that performance analytics capability is present."""
        capabilities = workflow_planners.get_available_capabilities()

        assert "predictive_performance_analytics" in capabilities

    def test_contains_ai_enhanced_quality_assessment(self):
        """Test that quality assessment capability is present."""
        capabilities = workflow_planners.get_available_capabilities()

        assert "ai_enhanced_quality_assessment" in capabilities

    def test_contains_intelligence_briefing_curation(self):
        """Test that briefing curation capability is present."""
        capabilities = workflow_planners.get_available_capabilities()

        assert "intelligence_briefing_curation" in capabilities

    def test_contains_autonomous_learning_adaptation(self):
        """Test that autonomous learning capability is present."""
        capabilities = workflow_planners.get_available_capabilities()

        assert "autonomous_learning_adaptation" in capabilities

    def test_contains_real_time_monitoring_alerts(self):
        """Test that real-time monitoring capability is present."""
        capabilities = workflow_planners.get_available_capabilities()

        assert "real_time_monitoring_alerts" in capabilities

    def test_contains_community_liaison_communication(self):
        """Test that community liaison capability is present."""
        capabilities = workflow_planners.get_available_capabilities()

        assert "community_liaison_communication" in capabilities

    def test_no_duplicate_capabilities(self):
        """Test that all capabilities are unique."""
        capabilities = workflow_planners.get_available_capabilities()

        assert len(capabilities) == len(set(capabilities))

    def test_consistent_results_across_calls(self):
        """Test that function returns identical results on multiple calls."""
        capabilities1 = workflow_planners.get_available_capabilities()
        capabilities2 = workflow_planners.get_available_capabilities()

        assert capabilities1 == capabilities2


class TestEstimateWorkflowDuration:
    """Test estimate_workflow_duration function."""

    def test_returns_dict_for_standard_depth(self):
        """Test that function returns a dictionary for standard depth."""
        duration = workflow_planners.estimate_workflow_duration("standard")

        assert isinstance(duration, dict)

    def test_standard_depth_has_3_minutes(self):
        """Test that standard depth estimates 3 minutes."""
        duration = workflow_planners.estimate_workflow_duration("standard")

        assert duration["estimated_minutes"] == 3

    def test_deep_depth_has_8_minutes(self):
        """Test that deep depth estimates 8 minutes."""
        duration = workflow_planners.estimate_workflow_duration("deep")

        assert duration["estimated_minutes"] == 8

    def test_comprehensive_depth_has_15_minutes(self):
        """Test that comprehensive depth estimates 15 minutes."""
        duration = workflow_planners.estimate_workflow_duration("comprehensive")

        assert duration["estimated_minutes"] == 15

    def test_experimental_depth_has_25_minutes(self):
        """Test that experimental depth estimates 25 minutes."""
        duration = workflow_planners.estimate_workflow_duration("experimental")

        assert duration["estimated_minutes"] == 25

    def test_unknown_depth_defaults_to_5_minutes(self):
        """Test that unknown depth levels default to 5 minutes."""
        duration = workflow_planners.estimate_workflow_duration("unknown_level")

        assert duration["estimated_minutes"] == 5

    def test_contains_confidence_interval(self):
        """Test that result contains confidence interval."""
        duration = workflow_planners.estimate_workflow_duration("standard")

        assert "confidence_interval" in duration
        assert duration["confidence_interval"] == "±20%"

    def test_contains_factors_list(self):
        """Test that result contains factors affecting duration."""
        duration = workflow_planners.estimate_workflow_duration("standard")

        assert "factors" in duration
        assert isinstance(duration["factors"], list)

    def test_factors_include_content_complexity(self):
        """Test that content complexity is a duration factor."""
        duration = workflow_planners.estimate_workflow_duration("standard")

        assert "content_complexity" in duration["factors"]

    def test_factors_include_network_latency(self):
        """Test that network latency is a duration factor."""
        duration = workflow_planners.estimate_workflow_duration("standard")

        assert "network_latency" in duration["factors"]

    def test_factors_include_ai_model_response_times(self):
        """Test that AI model response times are a duration factor."""
        duration = workflow_planners.estimate_workflow_duration("standard")

        assert "ai_model_response_times" in duration["factors"]

    def test_experimental_is_longest_duration(self):
        """Test that experimental depth has the longest estimated duration."""
        depths = ["standard", "deep", "comprehensive", "experimental"]
        durations = [workflow_planners.estimate_workflow_duration(d)["estimated_minutes"] for d in depths]

        assert max(durations) == workflow_planners.estimate_workflow_duration("experimental")["estimated_minutes"]

    def test_standard_is_shortest_duration(self):
        """Test that standard depth has the shortest estimated duration."""
        depths = ["standard", "deep", "comprehensive", "experimental"]
        durations = [workflow_planners.estimate_workflow_duration(d)["estimated_minutes"] for d in depths]

        assert min(durations) == workflow_planners.estimate_workflow_duration("standard")["estimated_minutes"]

    def test_durations_are_monotonically_increasing(self):
        """Test that durations increase as depth increases."""
        standard = workflow_planners.estimate_workflow_duration("standard")["estimated_minutes"]
        deep = workflow_planners.estimate_workflow_duration("deep")["estimated_minutes"]
        comprehensive = workflow_planners.estimate_workflow_duration("comprehensive")["estimated_minutes"]
        experimental = workflow_planners.estimate_workflow_duration("experimental")["estimated_minutes"]

        assert standard < deep < comprehensive < experimental


class TestGetPlannedStages:
    """Test get_planned_stages function."""

    def test_returns_list_for_standard_depth(self):
        """Test that function returns a list for standard depth."""
        stages = workflow_planners.get_planned_stages("standard")

        assert isinstance(stages, list)

    def test_all_stages_are_dicts(self):
        """Test that all stages are dictionary objects."""
        stages = workflow_planners.get_planned_stages("comprehensive")

        assert all(isinstance(stage, dict) for stage in stages)

    def test_standard_depth_has_8_stages(self):
        """Test that standard depth includes 8 stages (critical + high)."""
        stages = workflow_planners.get_planned_stages("standard")

        assert len(stages) == 8

    def test_deep_depth_has_12_stages(self):
        """Test that deep depth includes 12 stages (critical + high + medium)."""
        stages = workflow_planners.get_planned_stages("deep")

        assert len(stages) == 12

    def test_comprehensive_depth_has_14_stages(self):
        """Test that comprehensive depth includes all 14 stages."""
        stages = workflow_planners.get_planned_stages("comprehensive")

        assert len(stages) == 14

    def test_experimental_depth_has_14_stages(self):
        """Test that experimental depth includes all 14 stages."""
        stages = workflow_planners.get_planned_stages("experimental")

        assert len(stages) == 14

    def test_standard_only_includes_critical_and_high(self):
        """Test that standard depth only includes critical and high priority stages."""
        stages = workflow_planners.get_planned_stages("standard")

        priorities = {stage["priority"] for stage in stages}
        assert priorities == {"critical", "high"}

    def test_deep_includes_critical_high_medium(self):
        """Test that deep depth includes critical, high, and medium priority stages."""
        stages = workflow_planners.get_planned_stages("deep")

        priorities = {stage["priority"] for stage in stages}
        assert priorities == {"critical", "high", "medium"}

    def test_comprehensive_includes_all_priorities(self):
        """Test that comprehensive depth includes all priority levels."""
        stages = workflow_planners.get_planned_stages("comprehensive")

        priorities = {stage["priority"] for stage in stages}
        assert "critical" in priorities
        assert "high" in priorities
        assert "medium" in priorities
        assert "low" in priorities

    def test_all_stages_have_name(self):
        """Test that all stages have a name field."""
        stages = workflow_planners.get_planned_stages("comprehensive")

        assert all("name" in stage for stage in stages)
        assert all(isinstance(stage["name"], str) for stage in stages)

    def test_all_stages_have_agent(self):
        """Test that all stages have an agent field."""
        stages = workflow_planners.get_planned_stages("comprehensive")

        assert all("agent" in stage for stage in stages)
        assert all(isinstance(stage["agent"], str) for stage in stages)

    def test_all_stages_have_priority(self):
        """Test that all stages have a priority field."""
        stages = workflow_planners.get_planned_stages("comprehensive")

        assert all("priority" in stage for stage in stages)
        assert all(stage["priority"] in ["critical", "high", "medium", "low"] for stage in stages)

    def test_mission_planning_stage_present(self):
        """Test that Mission Planning stage is present."""
        stages = workflow_planners.get_planned_stages("comprehensive")

        stage_names = [stage["name"] for stage in stages]
        assert "Mission Planning" in stage_names

    def test_content_acquisition_stage_present(self):
        """Test that Content Acquisition stage is present."""
        stages = workflow_planners.get_planned_stages("comprehensive")

        stage_names = [stage["name"] for stage in stages]
        assert "Content Acquisition" in stage_names

    def test_transcription_analysis_stage_present(self):
        """Test that Transcription Analysis stage is present."""
        stages = workflow_planners.get_planned_stages("comprehensive")

        stage_names = [stage["name"] for stage in stages]
        assert "Transcription Analysis" in stage_names

    def test_content_analysis_stage_present(self):
        """Test that Content Analysis stage is present."""
        stages = workflow_planners.get_planned_stages("comprehensive")

        stage_names = [stage["name"] for stage in stages]
        assert "Content Analysis" in stage_names

    def test_information_verification_stage_present(self):
        """Test that Information Verification stage is present."""
        stages = workflow_planners.get_planned_stages("comprehensive")

        stage_names = [stage["name"] for stage in stages]
        assert "Information Verification" in stage_names

    def test_threat_analysis_stage_present(self):
        """Test that Threat Analysis stage is present."""
        stages = workflow_planners.get_planned_stages("comprehensive")

        stage_names = [stage["name"] for stage in stages]
        assert "Threat Analysis" in stage_names

    def test_critical_stages_in_standard(self):
        """Test that all critical stages are included in standard depth."""
        stages = workflow_planners.get_planned_stages("standard")

        critical_stage_names = [stage["name"] for stage in stages if stage["priority"] == "critical"]
        assert "Mission Planning" in critical_stage_names
        assert "Content Acquisition" in critical_stage_names
        assert "Content Analysis" in critical_stage_names

    def test_unknown_depth_defaults_to_standard(self):
        """Test that unknown depth levels default to standard filtering."""
        stages = workflow_planners.get_planned_stages("unknown_level")
        standard_stages = workflow_planners.get_planned_stages("standard")

        assert len(stages) == len(standard_stages)

    def test_stages_increase_with_depth(self):
        """Test that number of stages increases as depth increases."""
        standard = len(workflow_planners.get_planned_stages("standard"))
        deep = len(workflow_planners.get_planned_stages("deep"))
        comprehensive = len(workflow_planners.get_planned_stages("comprehensive"))

        assert standard < deep <= comprehensive


class TestGetCapabilitiesSummary:
    """Test get_capabilities_summary function."""

    def test_returns_dict_for_standard_depth(self):
        """Test that function returns a dictionary."""
        summary = workflow_planners.get_capabilities_summary("standard")

        assert isinstance(summary, dict)

    def test_contains_total_agents(self):
        """Test that summary contains total_agents field."""
        summary = workflow_planners.get_capabilities_summary("standard")

        assert "total_agents" in summary
        assert isinstance(summary["total_agents"], int)

    def test_contains_total_tools(self):
        """Test that summary contains total_tools field."""
        summary = workflow_planners.get_capabilities_summary("standard")

        assert "total_tools" in summary
        assert isinstance(summary["total_tools"], int)

    def test_contains_ai_enhancement_features(self):
        """Test that summary contains ai_enhancement_features list."""
        summary = workflow_planners.get_capabilities_summary("standard")

        assert "ai_enhancement_features" in summary
        assert isinstance(summary["ai_enhancement_features"], list)

    def test_contains_depth_level(self):
        """Test that summary contains depth_level field."""
        summary = workflow_planners.get_capabilities_summary("standard")

        assert "depth_level" in summary
        assert summary["depth_level"] == "standard"

    def test_contains_experimental_features_enabled(self):
        """Test that summary contains experimental_features_enabled field."""
        summary = workflow_planners.get_capabilities_summary("standard")

        assert "experimental_features_enabled" in summary
        assert isinstance(summary["experimental_features_enabled"], bool)

    def test_total_tools_is_15(self):
        """Test that total_tools matches number of available capabilities (15)."""
        summary = workflow_planners.get_capabilities_summary("standard")

        assert summary["total_tools"] == 15

    def test_total_agents_matches_stage_count(self):
        """Test that total_agents matches number of planned stages for depth."""
        summary = workflow_planners.get_capabilities_summary("standard")
        stages = workflow_planners.get_planned_stages("standard")

        assert summary["total_agents"] == len(stages)

    def test_standard_depth_has_8_agents(self):
        """Test that standard depth summary shows 8 agents."""
        summary = workflow_planners.get_capabilities_summary("standard")

        assert summary["total_agents"] == 8

    def test_deep_depth_has_12_agents(self):
        """Test that deep depth summary shows 12 agents."""
        summary = workflow_planners.get_capabilities_summary("deep")

        assert summary["total_agents"] == 12

    def test_comprehensive_depth_has_14_agents(self):
        """Test that comprehensive depth summary shows 14 agents."""
        summary = workflow_planners.get_capabilities_summary("comprehensive")

        assert summary["total_agents"] == 14

    def test_experimental_depth_has_14_agents(self):
        """Test that experimental depth summary shows 14 agents."""
        summary = workflow_planners.get_capabilities_summary("experimental")

        assert summary["total_agents"] == 14

    def test_experimental_features_enabled_for_experimental(self):
        """Test that experimental features are enabled for experimental depth."""
        summary = workflow_planners.get_capabilities_summary("experimental")

        assert summary["experimental_features_enabled"] is True

    def test_experimental_features_disabled_for_standard(self):
        """Test that experimental features are disabled for standard depth."""
        summary = workflow_planners.get_capabilities_summary("standard")

        assert summary["experimental_features_enabled"] is False

    def test_experimental_features_disabled_for_deep(self):
        """Test that experimental features are disabled for deep depth."""
        summary = workflow_planners.get_capabilities_summary("deep")

        assert summary["experimental_features_enabled"] is False

    def test_experimental_features_disabled_for_comprehensive(self):
        """Test that experimental features are disabled for comprehensive depth."""
        summary = workflow_planners.get_capabilities_summary("comprehensive")

        assert summary["experimental_features_enabled"] is False

    def test_ai_features_include_adaptive_workflow_planning(self):
        """Test that adaptive workflow planning is an AI enhancement feature."""
        summary = workflow_planners.get_capabilities_summary("standard")

        assert "adaptive_workflow_planning" in summary["ai_enhancement_features"]

    def test_ai_features_include_real_time_performance_monitoring(self):
        """Test that real-time performance monitoring is an AI enhancement feature."""
        summary = workflow_planners.get_capabilities_summary("standard")

        assert "real_time_performance_monitoring" in summary["ai_enhancement_features"]

    def test_ai_features_include_multi_agent_coordination(self):
        """Test that multi-agent coordination is an AI enhancement feature."""
        summary = workflow_planners.get_capabilities_summary("standard")

        assert "multi_agent_coordination" in summary["ai_enhancement_features"]

    def test_ai_features_include_predictive_analytics(self):
        """Test that predictive analytics is an AI enhancement feature."""
        summary = workflow_planners.get_capabilities_summary("standard")

        assert "predictive_analytics" in summary["ai_enhancement_features"]

    def test_ai_features_include_autonomous_learning(self):
        """Test that autonomous learning is an AI enhancement feature."""
        summary = workflow_planners.get_capabilities_summary("standard")

        assert "autonomous_learning" in summary["ai_enhancement_features"]

    def test_ai_features_has_5_items(self):
        """Test that exactly 5 AI enhancement features are listed."""
        summary = workflow_planners.get_capabilities_summary("standard")

        assert len(summary["ai_enhancement_features"]) == 5

    def test_depth_level_preserved_in_summary(self):
        """Test that depth level is correctly preserved in summary."""
        for depth in ["standard", "deep", "comprehensive", "experimental"]:
            summary = workflow_planners.get_capabilities_summary(depth)
            assert summary["depth_level"] == depth
