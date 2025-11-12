"""Tests for feature flag audit and simplification framework."""

from pathlib import Path
from platform.config.configuration.feature_flag_audit import (
    FeatureFlag,
    FeatureFlagAuditor,
    FeatureFlagAuditResult,
    audit_feature_flags,
    simplify_feature_flags,
)
from unittest.mock import Mock, patch


class TestFeatureFlagAuditor:
    """Test feature flag auditor functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.project_root = Path("/tmp/test_project")
        self.auditor = FeatureFlagAuditor(self.project_root)

    def test_feature_flag_creation(self):
        """Test feature flag creation."""
        flag = FeatureFlag(
            name="ENABLE_TEST_FEATURE",
            default_value="false",
            description="Test feature flag",
            category="test",
            usage_count=5,
            usage_locations=["file1.py", "file2.py"],
        )
        assert flag.name == "ENABLE_TEST_FEATURE"
        assert flag.default_value == "false"
        assert flag.description == "Test feature flag"
        assert flag.category == "test"
        assert flag.usage_count == 5
        assert len(flag.usage_locations) == 2

    def test_discover_feature_flags(self):
        """Test feature flag discovery."""
        with patch.object(self.auditor, "_parse_settings_file") as mock_parse:
            mock_parse.return_value = [
                FeatureFlag(
                    name="ENABLE_TEST_FEATURE", default_value="false", description="Test feature", category="test"
                )
            ]
            flags = self.auditor.discover_feature_flags()
            assert len(flags) == 1
            assert flags[0].name == "ENABLE_TEST_FEATURE"

    def test_identify_unused_flags(self):
        """Test identification of unused flags."""
        self.auditor.flags = [
            FeatureFlag(name="ENABLE_USED_FEATURE", default_value="false", usage_count=5),
            FeatureFlag(name="ENABLE_UNUSED_FEATURE", default_value="false", usage_count=0),
        ]
        unused_flags = self.auditor.identify_unused_flags()
        assert len(unused_flags) == 1
        assert unused_flags[0].name == "ENABLE_UNUSED_FEATURE"

    def test_identify_deprecated_flags(self):
        """Test identification of deprecated flags."""
        self.auditor.flags = [
            FeatureFlag(name="ENABLE_LEGACY_FEATURE", default_value="false", usage_count=1),
            FeatureFlag(name="ENABLE_NEW_FEATURE", default_value="true", usage_count=10),
        ]
        deprecated_flags = self.auditor.identify_deprecated_flags()
        assert len(deprecated_flags) == 1
        assert deprecated_flags[0].name == "ENABLE_LEGACY_FEATURE"
        assert deprecated_flags[0].is_deprecated

    def test_identify_complex_flags(self):
        """Test identification of complex flags."""
        self.auditor.flags = [
            FeatureFlag(
                name="ENABLE_VERY_COMPLEX_FEATURE_WITH_LONG_NAME",
                default_value="false",
                usage_count=15,
                usage_locations=["file1.py", "file2.py", "file3.py", "file4.py", "file5.py", "file6.py"],
            ),
            FeatureFlag(
                name="ENABLE_SIMPLE_FEATURE", default_value="false", usage_count=2, usage_locations=["file1.py"]
            ),
        ]
        complex_flags = self.auditor.identify_complex_flags()
        assert len(complex_flags) == 1
        assert complex_flags[0].name == "ENABLE_VERY_COMPLEX_FEATURE_WITH_LONG_NAME"

    def test_generate_simplification_recommendations(self):
        """Test generation of simplification recommendations."""
        self.auditor.flags = [
            FeatureFlag(name="ENABLE_CACHE_OPTIMIZATION", default_value="false", category="caching", usage_count=5),
            FeatureFlag(name="ENABLE_CACHE_PRELOADING", default_value="false", category="caching", usage_count=3),
            FeatureFlag(name="ENABLE_UNUSED_FEATURE", default_value="false", usage_count=0),
        ]
        recommendations = self.auditor.generate_simplification_recommendations()
        assert len(recommendations) > 0, "Should generate recommendations"
        assert any("unused" in rec.lower() for rec in recommendations), "Should recommend removing unused flags"

    def test_run_comprehensive_audit(self):
        """Test comprehensive audit execution."""
        with patch.object(self.auditor, "discover_feature_flags") as mock_discover:
            mock_discover.return_value = [
                FeatureFlag(name="ENABLE_TEST_FEATURE", default_value="false", category="test", usage_count=5)
            ]
            result = self.auditor.run_comprehensive_audit()
            assert isinstance(result, FeatureFlagAuditResult)
            assert result.total_flags == 1
            assert result.audit_time > 0

    def test_generate_simplified_config(self):
        """Test generation of simplified configuration."""
        config = self.auditor.generate_simplified_config()
        assert isinstance(config, str)
        assert "ENABLE_CORE_FEATURES" in config
        assert "ENABLE_ADVANCED_FEATURES" in config
        assert "ENABLE_CACHING" in config
        assert "ENABLE_RATE_LIMITING" in config

    def test_get_audit_summary(self):
        """Test audit summary generation."""
        self.auditor.flags = [
            FeatureFlag(name="ENABLE_USED_FEATURE", default_value="false", category="core", usage_count=10),
            FeatureFlag(name="ENABLE_UNUSED_FEATURE", default_value="false", category="core", usage_count=0),
        ]
        summary = self.auditor.get_audit_summary()
        assert summary["status"] == "audit_complete"
        assert summary["total_flags"] == 2
        assert summary["unused_flags"] == 1
        assert "categories" in summary
        assert "most_used_flags" in summary

    def test_get_audit_summary_no_flags(self):
        """Test audit summary with no flags."""
        self.auditor.flags = []
        summary = self.auditor.get_audit_summary()
        assert summary["status"] == "no_flags_found"

    def test_find_redundant_flag_groups(self):
        """Test finding redundant flag groups."""
        flag_names = [
            "ENABLE_CACHE_OPTIMIZATION",
            "ENABLE_CACHE_PRELOADING",
            "ENABLE_CACHE_CLEANUP",
            "ENABLE_ROUTER_OPTIMIZATION",
        ]
        redundant_groups = self.auditor._find_redundant_flag_groups(flag_names)
        assert len(redundant_groups) > 0, "Should find redundant groups"
        assert any("CACHE" in group[0] for group in redundant_groups), "Should find cache-related groups"

    def test_find_groupable_flags(self):
        """Test finding groupable flags."""
        flag_names = [
            "ENABLE_CACHE_OPTIMIZATION",
            "ENABLE_CACHE_PRELOADING",
            "ENABLE_CACHE_CLEANUP",
            "ENABLE_ROUTER_OPTIMIZATION",
        ]
        groupable = self.auditor._find_groupable_flags(flag_names)
        assert len(groupable) > 0, "Should find groupable flags"

    def test_find_inconsistent_naming(self):
        """Test finding inconsistent naming patterns."""
        flag_names = ["ENABLE_FEATURE_1", "ENABLE_FEATURE_2", "DISABLE_FEATURE_3", "ALLOW_FEATURE_4"]
        inconsistent = self.auditor._find_inconsistent_naming(flag_names)
        assert len(inconsistent) > 0, "Should find inconsistent naming"

    def test_determine_flag_category(self):
        """Test flag category determination."""
        test_cases = [
            ("ENABLE_UNIFIED_CACHE", "unified_systems"),
            ("ENABLE_CACHE_OPTIMIZATION", "caching"),
            ("ENABLE_OBSERVABILITY_METRICS", "observability"),
            ("ENABLE_ROUTER_OPTIMIZATION", "routing"),
            ("ENABLE_ORCHESTRATION", "orchestration"),
            ("ENABLE_AGENT_BRIDGE", "agents"),
            ("ENABLE_KNOWLEDGE_SHARING", "knowledge"),
            ("ENABLE_RATE_LIMITING", "rate_limiting"),
            ("ENABLE_DISTRIBUTED_CACHE", "distributed_systems"),
            ("ENABLE_UNKNOWN_FEATURE", "core"),
        ]
        for flag_name, expected_category in test_cases:
            category = self.auditor._determine_flag_category(flag_name)
            assert category == expected_category, f"Wrong category for {flag_name}"

    def test_extract_flag_description(self):
        """Test flag description extraction."""
        content = '\n        # This is a description for the flag\n        ENABLE_TEST_FEATURE = str(_get_setting("ENABLE_TEST_FEATURE", "false"))\n        '
        description = self.auditor._extract_flag_description(content, "ENABLE_TEST_FEATURE")
        assert description is not None
        assert "description" in description.lower()

    def test_parse_settings_file(self):
        """Test parsing settings file."""
        settings_content = '\n        # Test feature flag\n        ENABLE_TEST_FEATURE = str(_get_setting("ENABLE_TEST_FEATURE", "false"))\n        '
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = settings_content
            flags = self.auditor._parse_settings_file(Path("test_settings.py"))
            assert len(flags) == 1
            assert flags[0].name == "ENABLE_TEST_FEATURE"
            assert flags[0].default_value == "false"


class TestConvenienceFunctions:
    """Test convenience functions for feature flag audit."""

    def setup_method(self):
        """Set up test fixtures."""
        self.project_root = Path("/tmp/test_project")

    def test_audit_feature_flags_success(self):
        """Test audit_feature_flags with success."""
        with patch("src.core.configuration.feature_flag_audit.FeatureFlagAuditor") as mock_auditor_class:
            mock_auditor = Mock()
            mock_auditor.run_comprehensive_audit.return_value = Mock(
                total_flags=5,
                unused_flags=[],
                deprecated_flags=[],
                complex_flags=[],
                recommendations=[],
                audit_time=0.1,
            )
            mock_auditor_class.return_value = mock_auditor
            result = audit_feature_flags(self.project_root)
            assert result.success, "Should succeed with valid audit"
            assert "audit_result" in result.data

    def test_audit_feature_flags_no_flags(self):
        """Test audit_feature_flags with no flags."""
        with patch("src.core.configuration.feature_flag_audit.FeatureFlagAuditor") as mock_auditor_class:
            mock_auditor = Mock()
            mock_auditor.run_comprehensive_audit.return_value = Mock(
                total_flags=0,
                unused_flags=[],
                deprecated_flags=[],
                complex_flags=[],
                recommendations=[],
                audit_time=0.1,
            )
            mock_auditor_class.return_value = mock_auditor
            result = audit_feature_flags(self.project_root)
            assert result.success, "Should succeed with no flags"
            assert result.data["status"] == "no_flags_found"

    def test_audit_feature_flags_exception(self):
        """Test audit_feature_flags with exception."""
        with patch("src.core.configuration.feature_flag_audit.FeatureFlagAuditor") as mock_auditor_class:
            mock_auditor_class.side_effect = Exception("Test exception")
            result = audit_feature_flags(self.project_root)
            assert not result.success, "Should fail with exception"
            assert "Test exception" in result.error

    def test_simplify_feature_flags_success(self):
        """Test simplify_feature_flags with success."""
        with patch("src.core.configuration.feature_flag_audit.FeatureFlagAuditor") as mock_auditor_class:
            mock_auditor = Mock()
            mock_auditor.run_comprehensive_audit.return_value = Mock(
                total_flags=5,
                unused_flags=[],
                deprecated_flags=[],
                complex_flags=[],
                recommendations=["Test recommendation"],
                audit_time=0.1,
            )
            mock_auditor.generate_simplified_config.return_value = "simplified_config_content"
            mock_auditor_class.return_value = mock_auditor
            result = simplify_feature_flags(self.project_root)
            assert result.success, "Should succeed with simplification"
            assert "audit_result" in result.data
            assert "simplified_config" in result.data
            assert "recommendations" in result.data

    def test_simplify_feature_flags_exception(self):
        """Test simplify_feature_flags with exception."""
        with patch("src.core.configuration.feature_flag_audit.FeatureFlagAuditor") as mock_auditor_class:
            mock_auditor_class.side_effect = Exception("Test exception")
            result = simplify_feature_flags(self.project_root)
            assert not result.success, "Should fail with exception"
            assert "Test exception" in result.error
