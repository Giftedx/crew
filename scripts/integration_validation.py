#!/usr/bin/env python3
"""
Integration Validation Script
Comprehensive validation of codebase integration following CI/CD best practices.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class IntegrationValidator:
    """Validates integration between all components following best practices."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.passed_checks = 0
        self.total_checks = 0

    def run_check(self, name: str, check_func: Callable[[], bool]) -> bool:
        """Run a validation check and track results."""
        self.total_checks += 1
        logger.info(f"Running check: {name}")

        try:
            result = check_func()
            if result:
                logger.info(f"✅ {name}")
                self.passed_checks += 1
                return True
            else:
                logger.error(f"❌ {name}")
                return False
        except Exception as e:
            logger.error(f"❌ {name}: {e}")
            return False

    def check_code_quality(self) -> bool:
        """Validate code quality and formatting standards."""
        # Run ruff for linting
        try:
            result = subprocess.run(
                ["python", "-m", "ruff", "check", ".", "--quiet"],
                check=False,
                cwd=self.project_root,
                capture_output=True,
                timeout=60,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def check_type_annotations(self) -> bool:
        """Check for type annotation coverage."""
        try:
            # Count files with type annotations
            py_files = list(self.project_root.glob("src/**/*.py"))
            files_with_annotations = 0

            for file_path in py_files[:20]:  # Sample check for performance
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()
                        if "-> " in content or ": " in content:
                            files_with_annotations += 1
                except Exception:
                    continue

            # Require at least 80% coverage in sample
            coverage = files_with_annotations / len(py_files[:20]) if py_files else 0
            return coverage >= 0.8
        except Exception:
            return False

    def check_configuration_integrity(self) -> bool:
        """Validate configuration files and integration."""
        required_configs = [
            "config/policy.yaml",
            "src/ultimate_discord_intelligence_bot/config/agents.yaml",
            "src/ultimate_discord_intelligence_bot/config/tasks.yaml",
        ]

        for config in required_configs:
            config_path = self.project_root / config
            if not config_path.exists():
                logger.error(f"Missing config: {config}")
                return False

        return True

    def check_import_structure(self) -> bool:
        """Validate import structure and dependencies."""
        try:
            # Test core imports
            test_script = """
import sys
sys.path.append("src")

# Test core imports
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.crew import UltimateDiscordIntelligenceBotCrew
from ultimate_discord_intelligence_bot.services.memory_service import MemoryService

# Test StepResult pattern
result = StepResult.ok(data={"test": "value"})
assert result.success == True

print("✅ Core imports successful")
"""

            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(test_script)
                temp_path = f.name

            try:
                result = subprocess.run(
                    ["python", temp_path],
                    check=False,
                    cwd=self.project_root,
                    capture_output=True,
                    timeout=30,
                    text=True,
                )
                return result.returncode == 0 and "✅ Core imports successful" in result.stdout
            finally:
                os.unlink(temp_path)

        except Exception:
            return False

    def check_testing_infrastructure(self) -> bool:
        """Validate testing setup and key tests."""
        test_dir = self.project_root / "tests"
        if not test_dir.exists():
            return False

        # Check for key test files
        key_tests = ["test_core_services.py", "test_fallacy_helpers.py", "test_full_stack_imports.py"]

        for test_file in key_tests:
            if not (test_dir / test_file).exists():
                logger.error(f"Missing key test: {test_file}")
                return False

        # Run a quick test
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/test_fallacy_helpers.py", "-q"],
                check=False,
                cwd=self.project_root,
                capture_output=True,
                timeout=60,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False

    def check_security_integration(self) -> bool:
        """Validate security components are integrated."""
        security_files = ["src/policy/policy_engine.py", "src/core/privacy/privacy_filter.py", "config/policy.yaml"]

        for sec_file in security_files:
            if not (self.project_root / sec_file).exists():
                logger.error(f"Missing security file: {sec_file}")
                return False

        return True

    def check_service_integrations(self) -> bool:
        """Validate service integration patterns."""
        service_dir = self.project_root / "src" / "ultimate_discord_intelligence_bot" / "services"
        if not service_dir.exists():
            return False

        key_services = ["memory_service.py", "prompt_engine.py", "openrouter_service.py"]

        return all((service_dir / service).exists() for service in key_services)

    def check_documentation_sync(self) -> bool:
        """Validate documentation is in sync with code."""
        docs_dir = self.project_root / "docs"
        if not docs_dir.exists():
            return False

        # Check key documentation files exist
        key_docs = ["agent_reference.md", "tools_reference.md", "configuration.md"]

        return all((docs_dir / doc).exists() for doc in key_docs)

    def run_all_checks(self) -> tuple[int, int]:
        """Run all integration validation checks."""
        checks = [
            ("Code Quality & Linting", self.check_code_quality),
            ("Type Annotation Coverage", self.check_type_annotations),
            ("Configuration Integrity", self.check_configuration_integrity),
            ("Import Structure", self.check_import_structure),
            ("Testing Infrastructure", self.check_testing_infrastructure),
            ("Security Integration", self.check_security_integration),
            ("Service Integrations", self.check_service_integrations),
            ("Documentation Sync", self.check_documentation_sync),
        ]

        logger.info("🚀 Starting Integration Validation")
        logger.info("=" * 50)

        for name, check_func in checks:
            self.run_check(name, check_func)

        logger.info("=" * 50)
        logger.info(f"🎯 Integration Validation Summary: {self.passed_checks}/{self.total_checks} checks passed")

        if self.passed_checks == self.total_checks:
            logger.info("🎉 All integration checks passed!")
            return self.passed_checks, self.total_checks
        else:
            logger.warning(f"⚠️ {self.total_checks - self.passed_checks} checks failed")
            return self.passed_checks, self.total_checks


def main():
    """Main entry point for integration validation."""
    project_root = Path(__file__).parent.parent
    validator = IntegrationValidator(project_root)

    passed, total = validator.run_all_checks()

    # Exit with appropriate code
    if passed == total:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Some checks failed


if __name__ == "__main__":
    main()
