"""Dependency checking utilities and validation.

This module provides utilities for checking dependency availability,
validating installation requirements, and generating helpful error messages.
"""

from __future__ import annotations

import importlib
import logging
import os
import subprocess
import sys
from typing import Any

logger = logging.getLogger(__name__)


class DependencyChecker:
    """Utility class for checking and validating dependencies."""

    def __init__(self):
        self._checked_modules: set[str] = set()
        self._module_versions: dict[str, str] = {}

    def check_module_available(self, module_name: str) -> bool:
        """Check if a module is available for import."""
        if module_name in self._checked_modules:
            return True

        try:
            importlib.import_module(module_name)
            self._checked_modules.add(module_name)
            return True
        except ImportError:
            return False

    def get_module_version(self, module_name: str) -> str | None:
        """Get the version of an installed module."""
        if module_name in self._module_versions:
            return self._module_versions[module_name]

        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", None)
            if version is None:
                # Try alternative version attributes
                version = getattr(module, "VERSION", None)
                if version is None:
                    version = getattr(module, "version", None)

            self._module_versions[module_name] = version
            return version
        except ImportError:
            return None

    def check_version_requirement(self, module_name: str, min_version: str) -> bool:
        """Check if a module meets the minimum version requirement."""
        version = self.get_module_version(module_name)
        if version is None:
            return False

        try:
            from packaging import version as packaging_version

            return packaging_version.parse(version) >= packaging_version.parse(min_version)
        except ImportError:
            # Fallback to simple string comparison if packaging is not available
            logger.warning("packaging module not available, using simple version comparison")
            return version >= min_version

    def check_system_requirements(self) -> dict[str, Any]:
        """Check system-level requirements."""
        requirements = {
            "python_version": sys.version_info,
            "platform": sys.platform,
            "architecture": os.uname().machine if hasattr(os, "uname") else "unknown",
        }

        # Check if we're in a virtual environment
        requirements["virtual_env"] = hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        )

        return requirements

    def validate_dependency_group(self, dependencies: list[tuple[str, str | None]]) -> dict[str, Any]:
        """Validate a group of dependencies with optional version requirements."""
        results = {
            "available": [],
            "missing": [],
            "version_mismatches": [],
            "total": len(dependencies),
        }

        for module_name, min_version in dependencies:
            if not self.check_module_available(module_name):
                results["missing"].append(
                    {
                        "module": module_name,
                        "required_version": min_version,
                    }
                )
                continue

            results["available"].append(module_name)

            if min_version and not self.check_version_requirement(module_name, min_version):
                actual_version = self.get_module_version(module_name)
                results["version_mismatches"].append(
                    {
                        "module": module_name,
                        "required_version": min_version,
                        "actual_version": actual_version,
                    }
                )

        return results

    def generate_install_commands(self, missing_deps: list[dict[str, Any]]) -> list[str]:
        """Generate pip install commands for missing dependencies."""
        commands = []
        for dep in missing_deps:
            module_name = dep["module"]
            version = dep.get("required_version")
            if version:
                commands.append(f"pip install {module_name}>={version}")
            else:
                commands.append(f"pip install {module_name}")
        return commands

    def check_pip_available(self) -> bool:
        """Check if pip is available."""
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def get_package_info(self, package_name: str) -> dict[str, Any] | None:
        """Get information about an installed package."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", package_name],
                capture_output=True,
                text=True,
                check=True,
            )
            info = {}
            for line in result.stdout.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    info[key.strip()] = value.strip()
            return info
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def suggest_alternatives(self, missing_module: str) -> list[str]:
        """Suggest alternative modules for missing dependencies."""
        alternatives_map = {
            "redis": ["aioredis", "hiredis"],
            "psycopg2": ["psycopg2-binary", "asyncpg"],
            "mysql": ["mysqlclient", "PyMySQL"],
            "pandas": ["pyarrow", "fastparquet"],
            "numpy": ["scipy", "numba"],
            "torch": ["tensorflow", "jax"],
            "transformers": ["sentence-transformers", "spacy"],
            "qdrant_client": ["chromadb", "pinecone", "weaviate"],
            "prometheus_client": ["grafana_api", "datadog"],
        }
        return alternatives_map.get(missing_module, [])

    def generate_dependency_report(self) -> dict[str, Any]:
        """Generate a comprehensive dependency report."""
        report = {
            "system_info": self.check_system_requirements(),
            "python_modules": {},
            "package_info": {},
            "recommendations": [],
        }

        # Check common dependencies
        common_deps = [
            ("requests", "2.25.0"),
            ("pydantic", "1.8.0"),
            ("structlog", "21.0.0"),
            ("redis", None),
            ("qdrant_client", None),
            ("prometheus_client", None),
            ("psycopg2", None),
            ("transformers", None),
            ("torch", None),
            ("pandas", None),
            ("numpy", None),
        ]

        validation_results = self.validate_dependency_group(common_deps)
        report["validation_results"] = validation_results

        # Get detailed info for available modules
        for module_name in validation_results["available"]:
            version = self.get_module_version(module_name)
            report["python_modules"][module_name] = {
                "available": True,
                "version": version,
            }

            # Get pip package info if available
            package_info = self.get_package_info(module_name)
            if package_info:
                report["package_info"][module_name] = package_info

        # Generate recommendations
        if validation_results["missing"]:
            install_commands = self.generate_install_commands(validation_results["missing"])
            report["recommendations"].extend(install_commands)

        if validation_results["version_mismatches"]:
            for mismatch in validation_results["version_mismatches"]:
                report["recommendations"].append(
                    f"Upgrade {mismatch['module']} from {mismatch['actual_version']} to >= {mismatch['required_version']}"
                )

        return report


# Global dependency checker instance
_dependency_checker = DependencyChecker()


def get_dependency_checker() -> DependencyChecker:
    """Get the global dependency checker instance."""
    return _dependency_checker


def check_module_available(module_name: str) -> bool:
    """Check if a module is available for import."""
    return _dependency_checker.check_module_available(module_name)


def get_module_version(module_name: str) -> str | None:
    """Get the version of an installed module."""
    return _dependency_checker.get_module_version(module_name)


def check_version_requirement(module_name: str, min_version: str) -> bool:
    """Check if a module meets the minimum version requirement."""
    return _dependency_checker.check_version_requirement(module_name, min_version)


def generate_dependency_report() -> dict[str, Any]:
    """Generate a comprehensive dependency report."""
    return _dependency_checker.generate_dependency_report()


def validate_requirements_file(requirements_file: str) -> dict[str, Any]:
    """Validate a requirements.txt file."""
    if not os.path.exists(requirements_file):
        return {"error": f"Requirements file not found: {requirements_file}"}

    dependencies = []
    with open(requirements_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Parse requirement line (simplified)
                if ">=" in line:
                    parts = line.split(">=")
                    module_name = parts[0].strip()
                    version = parts[1].strip()
                    dependencies.append((module_name, version))
                elif "==" in line:
                    parts = line.split("==")
                    module_name = parts[0].strip()
                    version = parts[1].strip()
                    dependencies.append((module_name, version))
                else:
                    dependencies.append((line, None))

    return _dependency_checker.validate_dependency_group(dependencies)
