#!/usr/bin/env python3
"""Tool Health Monitoring System with CI Integration.

This script validates tool imports, checks tool health, and provides
comprehensive monitoring for the consolidated tool system.
"""

from __future__ import annotations

import ast
import importlib
import json
import sys
import time
from pathlib import Path
from typing import Any


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class ToolHealthMonitor:
    """Comprehensive tool health monitoring system."""

    def __init__(self):
        """Initialize the health monitor."""
        self.results: dict[str, Any] = {}
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.healthy_tools: list[str] = []

    def check_tool_imports(self) -> dict[str, Any]:
        """Check if all tools can be imported successfully."""
        print("🔍 Checking tool imports...")

        import_results = {}
        failed_imports = []

        # Core tool imports to test
        tool_imports = [
            ("AudioTranscriptionTool", "ultimate_discord_intelligence_bot.tools.acquisition.audio_transcription_tool"),
            (
                "MultiPlatformDownloadTool",
                "ultimate_discord_intelligence_bot.tools.acquisition.multi_platform_download_tool",
            ),
            ("UnifiedMemoryTool", "ultimate_discord_intelligence_bot.tools.memory.unified_memory_tool"),
            (
                "ContentQualityAssessmentTool",
                "ultimate_discord_intelligence_bot.tools.analysis.content_quality_assessment_tool",
            ),
            ("FactCheckTool", "ultimate_discord_intelligence_bot.tools.verification.fact_check_tool"),
            ("StepResult", "ultimate_discord_intelligence_bot.step_result"),
        ]

        for tool_name, module_path in tool_imports:
            try:
                start_time = time.perf_counter()
                module = importlib.import_module(module_path)
                end_time = time.perf_counter()

                import_time = end_time - start_time
                import_results[tool_name] = {"status": "success", "import_time": import_time, "module": module_path}
                self.healthy_tools.append(tool_name)
                print(f"  ✅ {tool_name}: {import_time:.4f}s")

            except ImportError as e:
                import_results[tool_name] = {"status": "failed", "error": str(e), "module": module_path}
                failed_imports.append(tool_name)
                self.errors.append(f"Failed to import {tool_name}: {e}")
                print(f"  ❌ {tool_name}: {e}")

        return {
            "import_results": import_results,
            "failed_imports": failed_imports,
            "successful_imports": len(import_results) - len(failed_imports),
            "total_imports": len(import_results),
        }

    def check_tool_instantiation(self) -> dict[str, Any]:
        """Check if tools can be instantiated successfully."""
        print("🔧 Checking tool instantiation...")

        instantiation_results = {}
        failed_instantiations = []

        try:
            from ultimate_discord_intelligence_bot.tools.acquisition.audio_transcription_tool import (
                AudioTranscriptionTool,
            )
            from ultimate_discord_intelligence_bot.tools.acquisition.multi_platform_download_tool import (
                MultiPlatformDownloadTool,
            )
            from ultimate_discord_intelligence_bot.tools.analysis.content_quality_assessment_tool import (
                ContentQualityAssessmentTool,
            )
            from ultimate_discord_intelligence_bot.tools.memory.unified_memory_tool import UnifiedMemoryTool
            from ultimate_discord_intelligence_bot.tools.verification.fact_check_tool import FactCheckTool

            tools_to_test = [
                ("AudioTranscriptionTool", AudioTranscriptionTool),
                ("MultiPlatformDownloadTool", MultiPlatformDownloadTool),
                ("UnifiedMemoryTool", UnifiedMemoryTool),
                ("ContentQualityAssessmentTool", ContentQualityAssessmentTool),
                ("FactCheckTool", FactCheckTool),
            ]

            for tool_name, tool_class in tools_to_test:
                try:
                    start_time = time.perf_counter()
                    instance = tool_class()
                    end_time = time.perf_counter()

                    instantiation_time = end_time - start_time
                    instantiation_results[tool_name] = {
                        "status": "success",
                        "instantiation_time": instantiation_time,
                        "has_run_method": hasattr(instance, "_run") or hasattr(instance, "run"),
                        "has_name": hasattr(instance, "name"),
                        "has_description": hasattr(instance, "description"),
                    }
                    print(f"  ✅ {tool_name}: {instantiation_time:.4f}s")

                except Exception as e:
                    instantiation_results[tool_name] = {"status": "failed", "error": str(e)}
                    failed_instantiations.append(tool_name)
                    self.errors.append(f"Failed to instantiate {tool_name}: {e}")
                    print(f"  ❌ {tool_name}: {e}")

        except ImportError as e:
            return {"error": f"Import failed: {e}"}

        return {
            "instantiation_results": instantiation_results,
            "failed_instantiations": failed_instantiations,
            "successful_instantiations": len(instantiation_results) - len(failed_instantiations),
            "total_instantiations": len(instantiation_results),
        }

    def check_stepresult_compliance(self) -> dict[str, Any]:
        """Check StepResult compliance across tools."""
        print("📋 Checking StepResult compliance...")

        compliance_results = {
            "compliant_tools": [],
            "non_compliant_tools": [],
            "missing_stepresult_import": [],
            "warnings": [],
        }

        # Check tools directory for StepResult compliance
        tools_dir = Path(__file__).parent.parent / "src" / "ultimate_discord_intelligence_bot" / "tools"

        if not tools_dir.exists():
            self.warnings.append("Tools directory not found")
            return compliance_results

        # Check each tool file
        for tool_file in tools_dir.rglob("*.py"):
            if tool_file.name.startswith("_") or tool_file.name == "__init__.py":
                continue

            try:
                with open(tool_file) as f:
                    content = f.read()

                # Parse AST
                tree = ast.parse(content)

                # Check for StepResult import
                has_stepresult_import = False
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and "step_result" in node.module:
                            has_stepresult_import = True
                            break
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if "step_result" in alias.name:
                                has_stepresult_import = True
                                break

                if not has_stepresult_import:
                    compliance_results["missing_stepresult_import"].append(str(tool_file))
                    continue

                # Check for tool classes
                tool_classes = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if "Tool" in node.name:
                            tool_classes.append(node.name)

                if tool_classes:
                    compliance_results["compliant_tools"].extend(tool_classes)
                else:
                    compliance_results["non_compliant_tools"].append(str(tool_file))

            except Exception as e:
                self.warnings.append(f"Failed to parse {tool_file}: {e}")

        return compliance_results

    def check_agent_tool_wiring(self) -> dict[str, Any]:
        """Check agent-tool wiring health."""
        print("👥 Checking agent-tool wiring...")

        wiring_results = {"agents_checked": 0, "tools_accessible": 0, "wiring_errors": [], "agent_tool_counts": {}}

        try:
            from ultimate_discord_intelligence_bot.crew import create_crew

            crew = create_crew()
            wiring_results["agents_checked"] = len(crew.agents)

            for agent in crew.agents:
                agent_name = getattr(agent, "role", "Unknown")
                tools = getattr(agent, "tools", [])
                wiring_results["agent_tool_counts"][agent_name] = len(tools)
                wiring_results["tools_accessible"] += len(tools)

                # Check if tools are accessible
                for tool in tools:
                    if not hasattr(tool, "_run") and not hasattr(tool, "run"):
                        wiring_results["wiring_errors"].append(
                            f"Agent {agent_name} has tool {type(tool).__name__} without run method"
                        )

            print(f"  📊 Agents: {wiring_results['agents_checked']}")
            print(f"  📊 Total tools: {wiring_results['tools_accessible']}")

        except Exception as e:
            wiring_results["wiring_errors"].append(f"Crew loading failed: {e}")
            self.errors.append(f"Agent-tool wiring check failed: {e}")

        return wiring_results

    def check_memory_usage(self) -> dict[str, Any]:
        """Check memory usage and potential leaks."""
        print("💾 Checking memory usage...")

        try:
            import os

            import psutil

            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()

            memory_results = {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "memory_percent": process.memory_percent(),
                "status": "healthy" if memory_info.rss < 1024 * 1024 * 1024 else "high",  # 1GB threshold
            }

            if memory_results["status"] == "high":
                self.warnings.append(f"High memory usage: {memory_results['rss_mb']:.2f} MB")

            print(f"  📊 RSS Memory: {memory_results['rss_mb']:.2f} MB")
            print(f"  📊 VMS Memory: {memory_results['vms_mb']:.2f} MB")

            return memory_results

        except ImportError:
            self.warnings.append("psutil not available for memory monitoring")
            return {"status": "unavailable"}
        except Exception as e:
            self.warnings.append(f"Memory check failed: {e}")
            return {"status": "error", "error": str(e)}

    def generate_health_report(self) -> dict[str, Any]:
        """Generate comprehensive health report."""
        print("📊 Generating health report...")

        health_score = 100
        total_checks = 0
        passed_checks = 0

        # Import health
        import_health = self.check_tool_imports()
        total_checks += 1
        if import_health["failed_imports"]:
            health_score -= len(import_health["failed_imports"]) * 10
        else:
            passed_checks += 1

        # Instantiation health
        instantiation_health = self.check_tool_instantiation()
        total_checks += 1
        if instantiation_health["failed_instantiations"]:
            health_score -= len(instantiation_health["failed_instantiations"]) * 10
        else:
            passed_checks += 1

        # StepResult compliance
        compliance_health = self.check_stepresult_compliance()
        total_checks += 1
        if compliance_health["non_compliant_tools"]:
            health_score -= len(compliance_health["non_compliant_tools"]) * 5
        else:
            passed_checks += 1

        # Agent-tool wiring
        wiring_health = self.check_agent_tool_wiring()
        total_checks += 1
        if wiring_health["wiring_errors"]:
            health_score -= len(wiring_health["wiring_errors"]) * 5
        else:
            passed_checks += 1

        # Memory health
        memory_health = self.check_memory_usage()
        total_checks += 1
        if memory_health.get("status") == "healthy":
            passed_checks += 1
        else:
            health_score -= 10

        # Calculate final health score
        health_score = max(0, health_score)
        health_status = "excellent" if health_score >= 90 else "good" if health_score >= 70 else "poor"

        return {
            "health_score": health_score,
            "health_status": health_status,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "import_health": import_health,
            "instantiation_health": instantiation_health,
            "compliance_health": compliance_health,
            "wiring_health": wiring_health,
            "memory_health": memory_health,
            "errors": self.errors,
            "warnings": self.warnings,
            "healthy_tools": self.healthy_tools,
        }

    def run_health_check(self) -> dict[str, Any]:
        """Run comprehensive health check."""
        print("🚀 Starting Tool Health Monitoring")
        print("=" * 50)

        start_time = time.perf_counter()

        try:
            health_report = self.generate_health_report()

            end_time = time.perf_counter()
            health_report["check_duration"] = end_time - start_time

            # Print summary
            print("\n📊 Health Check Summary")
            print("=" * 50)
            print(f"Health Score: {health_report['health_score']}/100")
            print(f"Health Status: {health_report['health_status'].upper()}")
            print(f"Checks Passed: {health_report['passed_checks']}/{health_report['total_checks']}")
            print(f"Duration: {health_report['check_duration']:.4f}s")

            if health_report["errors"]:
                print(f"\n❌ Errors: {len(health_report['errors'])}")
                for error in health_report["errors"][:5]:  # Show first 5 errors
                    print(f"  • {error}")

            if health_report["warnings"]:
                print(f"\n⚠️  Warnings: {len(health_report['warnings'])}")
                for warning in health_report["warnings"][:5]:  # Show first 5 warnings
                    print(f"  • {warning}")

            if health_report["healthy_tools"]:
                print(f"\n✅ Healthy Tools: {len(health_report['healthy_tools'])}")
                for tool in health_report["healthy_tools"][:5]:  # Show first 5 tools
                    print(f"  • {tool}")

            return health_report

        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return {"error": str(e), "health_score": 0, "health_status": "failed"}


def main():
    """Main health monitoring function."""
    monitor = ToolHealthMonitor()

    try:
        health_report = monitor.run_health_check()

        # Save results
        with open("tool_health_report.json", "w") as f:
            json.dump(health_report, f, indent=2)

        print("\n💾 Health report saved to tool_health_report.json")

        # Exit with appropriate code for CI
        if health_report.get("health_score", 0) < 70:
            print("❌ Health check failed - score below 70")
            return 1
        elif health_report.get("errors"):
            print("⚠️  Health check passed with errors")
            return 1
        else:
            print("✅ Health check passed")
            return 0

    except Exception as e:
        print(f"❌ Health monitoring failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
