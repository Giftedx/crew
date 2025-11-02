"""Feature flag audit and simplification framework."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from platform.core.step_result import StepResult
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from pathlib import Path
logger = logging.getLogger(__name__)

@dataclass
class FeatureFlag:
    """Represents a feature flag definition."""
    name: str
    default_value: str
    description: str | None = None
    category: str | None = None
    usage_count: int = 0
    usage_locations: list[str] = field(default_factory=list)
    is_deprecated: bool = False
    deprecation_reason: str | None = None

@dataclass
class FeatureFlagAuditResult:
    """Result of feature flag audit."""
    flags: list[FeatureFlag]
    total_flags: int
    unused_flags: list[FeatureFlag]
    deprecated_flags: list[FeatureFlag]
    complex_flags: list[FeatureFlag]
    recommendations: list[str]
    audit_time: float

class FeatureFlagAuditor:
    """Comprehensive feature flag auditor and simplifier."""

    def __init__(self, project_root: Path):
        """Initialize feature flag auditor.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.flags: list[FeatureFlag] = []
        self.usage_map: dict[str, list[str]] = {}
        self.audit_start_time: float | None = None

    def discover_feature_flags(self) -> list[FeatureFlag]:
        """Discover all feature flags in the codebase."""
        flags = []
        settings_files = ['src/ultimate_discord_intelligence_bot/settings.py', 'src/core/settings.py']
        for settings_file in settings_files:
            file_path = self.project_root / settings_file
            if file_path.exists():
                flags.extend(self._parse_settings_file(file_path))
        self._scan_feature_flag_usage()
        for flag in flags:
            flag.usage_count = len(self.usage_map.get(flag.name, []))
            flag.usage_locations = self.usage_map.get(flag.name, [])
        self.flags = flags
        return flags

    def _parse_settings_file(self, file_path: Path) -> list[FeatureFlag]:
        """Parse settings file for feature flags."""
        flags = []
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
            enable_pattern = 'ENABLE_(\\w+)\\s*=\\s*str\\(_get_setting\\("([^"]+)",\\s*"([^"]+)"\\)\\)'
            matches = re.findall(enable_pattern, content)
            for match in matches:
                flag_name = f'ENABLE_{match[0]}'
                match[1]
                default_value = match[2]
                description = self._extract_flag_description(content, flag_name)
                category = self._determine_flag_category(flag_name)
                flags.append(FeatureFlag(name=flag_name, default_value=default_value, description=description, category=category))
        except Exception as e:
            logger.error(f'Failed to parse settings file {file_path}: {e}')
        return flags

    def _extract_flag_description(self, content: str, flag_name: str) -> str | None:
        """Extract description from comments near flag definition."""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if flag_name in line:
                for j in range(max(0, i - 5), i):
                    comment_line = lines[j].strip()
                    if comment_line.startswith('#') and 'description' in comment_line.lower():
                        return comment_line.replace('#', '').strip()
        return None

    def _determine_flag_category(self, flag_name: str) -> str:
        """Determine category based on flag name."""
        if 'UNIFIED' in flag_name:
            return 'unified_systems'
        elif 'CACHE' in flag_name:
            return 'caching'
        elif 'OBSERVABILITY' in flag_name or 'METRICS' in flag_name:
            return 'observability'
        elif 'ROUTER' in flag_name or 'ROUTING' in flag_name:
            return 'routing'
        elif 'ORCHESTRATION' in flag_name:
            return 'orchestration'
        elif 'AGENT' in flag_name:
            return 'agents'
        elif 'KNOWLEDGE' in flag_name:
            return 'knowledge'
        elif 'RATE_LIMIT' in flag_name:
            return 'rate_limiting'
        elif 'DISTRIBUTED' in flag_name:
            return 'distributed_systems'
        else:
            return 'core'

    def _scan_feature_flag_usage(self) -> None:
        """Scan codebase for feature flag usage."""
        python_files = list(self.project_root.rglob('*.py'))
        for file_path in python_files:
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()
                for flag in self.flags:
                    if flag.name in content:
                        if flag.name not in self.usage_map:
                            self.usage_map[flag.name] = []
                        self.usage_map[flag.name].append(str(file_path))
            except Exception as e:
                logger.warning(f'Failed to scan file {file_path}: {e}')

    def identify_unused_flags(self) -> list[FeatureFlag]:
        """Identify unused feature flags."""
        return [flag for flag in self.flags if flag.usage_count == 0]

    def identify_deprecated_flags(self) -> list[FeatureFlag]:
        """Identify deprecated feature flags."""
        deprecated = []
        for flag in self.flags:
            if any(keyword in flag.name.lower() for keyword in ['legacy', 'old', 'deprecated']):
                flag.is_deprecated = True
                flag.deprecation_reason = 'Flag name contains deprecation keywords'
                deprecated.append(flag)
            elif flag.usage_count <= 1 and flag.default_value == 'false':
                flag.is_deprecated = True
                flag.deprecation_reason = 'Low usage and disabled by default'
                deprecated.append(flag)
        return deprecated

    def identify_complex_flags(self) -> list[FeatureFlag]:
        """Identify complex feature flags that could be simplified."""
        complex_flags = []
        for flag in self.flags:
            complexity_score = 0
            if flag.usage_count > 10:
                complexity_score += 2
            if len(flag.name) > 30:
                complexity_score += 1
            if flag.name.count('_') > 3:
                complexity_score += 1
            if len(flag.usage_locations) > 5:
                complexity_score += 1
            if complexity_score >= 3:
                complex_flags.append(flag)
        return complex_flags

    def generate_simplification_recommendations(self) -> list[str]:
        """Generate recommendations for simplifying feature flags."""
        recommendations = []
        flag_names = [flag.name for flag in self.flags]
        redundant_groups = self._find_redundant_flag_groups(flag_names)
        for group in redundant_groups:
            recommendations.append(f'Consider consolidating redundant flags: {', '.join(group)}')
        overly_specific = [flag for flag in self.flags if len(flag.name.split('_')) > 4]
        if overly_specific:
            recommendations.append(f'Consider simplifying overly specific flags: {[f.name for f in overly_specific]}')
        grouped_flags = self._find_groupable_flags(flag_names)
        for group in grouped_flags:
            recommendations.append(f'Consider grouping related flags: {', '.join(group)}')
        inconsistent_naming = self._find_inconsistent_naming(flag_names)
        if inconsistent_naming:
            recommendations.append(f'Standardize flag naming conventions: {inconsistent_naming}')
        return recommendations

    def _find_redundant_flag_groups(self, flag_names: list[str]) -> list[list[str]]:
        """Find groups of redundant flags."""
        redundant_groups = []
        base_groups = {}
        for name in flag_names:
            base = name.replace('ENABLE_', '').split('_')[0]
            if base not in base_groups:
                base_groups[base] = []
            base_groups[base].append(name)
        for _base, flags in base_groups.items():
            if len(flags) > 1:
                redundant_groups.append(flags)
        return redundant_groups

    def _find_groupable_flags(self, flag_names: list[str]) -> list[list[str]]:
        """Find flags that could be grouped together."""
        groupable = []
        category_groups = {}
        for flag in self.flags:
            if flag.category not in category_groups:
                category_groups[flag.category] = []
            category_groups[flag.category].append(flag.name)
        for _category, flags in category_groups.items():
            if len(flags) > 2:
                groupable.append(flags)
        return groupable

    def _find_inconsistent_naming(self, flag_names: list[str]) -> list[str]:
        """Find flags with inconsistent naming patterns."""
        inconsistent = []
        patterns = {'ENABLE_': [name for name in flag_names if name.startswith('ENABLE_')], 'DISABLE_': [name for name in flag_names if name.startswith('DISABLE_')], 'ALLOW_': [name for name in flag_names if name.startswith('ALLOW_')]}
        for _pattern, flags in patterns.items():
            if len(flags) > 0 and len(flags) < len(flag_names) * 0.8:
                inconsistent.extend(flags)
        return inconsistent

    def run_comprehensive_audit(self) -> FeatureFlagAuditResult:
        """Run comprehensive feature flag audit."""
        import time
        self.audit_start_time = time.time()
        self.discover_feature_flags()
        unused_flags = self.identify_unused_flags()
        deprecated_flags = self.identify_deprecated_flags()
        complex_flags = self.identify_complex_flags()
        recommendations = self.generate_simplification_recommendations()
        if unused_flags:
            recommendations.append(f'Remove {len(unused_flags)} unused flags: {[f.name for f in unused_flags]}')
        if deprecated_flags:
            recommendations.append(f'Deprecate {len(deprecated_flags)} flags: {[f.name for f in deprecated_flags]}')
        if complex_flags:
            recommendations.append(f'Simplify {len(complex_flags)} complex flags: {[f.name for f in complex_flags]}')
        audit_time = time.time() - self.audit_start_time
        return FeatureFlagAuditResult(flags=self.flags, total_flags=len(self.flags), unused_flags=unused_flags, deprecated_flags=deprecated_flags, complex_flags=complex_flags, recommendations=recommendations, audit_time=audit_time)

    def generate_simplified_config(self) -> str:
        """Generate simplified configuration template."""
        config_lines = ['# ========================================', '# SIMPLIFIED FEATURE FLAGS', '# ========================================', '', '# Core Features', 'ENABLE_CORE_FEATURES=true', 'ENABLE_ADVANCED_FEATURES=false', '', '# System Components', 'ENABLE_CACHING=true', 'ENABLE_RATE_LIMITING=true', 'ENABLE_OBSERVABILITY=true', '', '# Performance Features', 'ENABLE_OPTIMIZATION=false', 'ENABLE_DISTRIBUTED_SYSTEMS=false', '', '# Development Features', 'ENABLE_DEBUG=false', 'ENABLE_PROFILING=false']
        return '\n'.join(config_lines)

    def get_audit_summary(self) -> dict[str, Any]:
        """Get audit summary statistics."""
        if not self.flags:
            return {'status': 'no_flags_found'}
        return {'status': 'audit_complete', 'total_flags': len(self.flags), 'unused_flags': len([f for f in self.flags if f.usage_count == 0]), 'deprecated_flags': len([f for f in self.flags if f.is_deprecated]), 'complex_flags': len([f for f in self.flags if f.usage_count > 10]), 'categories': list({f.category for f in self.flags if f.category}), 'most_used_flags': sorted(self.flags, key=lambda f: f.usage_count, reverse=True)[:5]}

def audit_feature_flags(project_root: Path) -> StepResult:
    """Convenience function for feature flag audit."""
    try:
        auditor = FeatureFlagAuditor(project_root)
        result = auditor.run_comprehensive_audit()
        if result.total_flags == 0:
            return StepResult.ok(data={'status': 'no_flags_found'})
        else:
            return StepResult.ok(data={'audit_result': result})
    except Exception as e:
        return StepResult.fail(f'Feature flag audit failed: {e}')

def simplify_feature_flags(project_root: Path) -> StepResult:
    """Convenience function for feature flag simplification."""
    try:
        auditor = FeatureFlagAuditor(project_root)
        result = auditor.run_comprehensive_audit()
        simplified_config = auditor.generate_simplified_config()
        return StepResult.ok(data={'audit_result': result, 'simplified_config': simplified_config, 'recommendations': result.recommendations})
    except Exception as e:
        return StepResult.fail(f'Feature flag simplification failed: {e}')
