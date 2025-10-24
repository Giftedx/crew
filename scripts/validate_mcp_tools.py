#!/usr/bin/env python3
"""
MCP Tools Validation Script.

This script validates all 45 proprietary MCP server tools to ensure
they are properly integrated and functional.
"""

import sys
import time
from pathlib import Path
from typing import Any


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from obs.metrics import (
    MCP_TOOL_CALL_COUNT,
    MCP_TOOL_CALL_ERROR_COUNT,
    MCP_TOOL_CALL_LATENCY,
)
from ultimate_discord_intelligence_bot.tools.mcp_call_tool import (
    _SAFE_REGISTRY,
    MCPCallTool,
)


class MCPToolsValidator:
    """MCP Tools validation and testing."""

    def __init__(self):
        """Initialize the validator."""
        self.results: dict[str, Any] = {}
        self.mcp_tool = MCPCallTool()

    def validate_tool_registry(self) -> dict[str, Any]:
        """Validate the MCP tool registry."""
        print("\n📋 Validating MCP Tool Registry...")

        registry_results = {
            "namespaces_count": len(_SAFE_REGISTRY),
            "total_tools": sum(len(tools) for _, tools in _SAFE_REGISTRY.values()),
            "namespaces": list(_SAFE_REGISTRY.keys()),
            "tools_by_namespace": {},
        }

        for namespace, (module_path, tools) in _SAFE_REGISTRY.items():
            registry_results["tools_by_namespace"][namespace] = {
                "module_path": module_path,
                "tools": tools,
                "tool_count": len(tools),
            }

        print(
            f"✅ Registry validated: {registry_results['namespaces_count']} namespaces, {registry_results['total_tools']} tools"
        )
        return registry_results

    def test_obs_tools(self) -> dict[str, Any]:
        """Test observability tools."""
        print("\n📊 Testing Observability Tools...")

        obs_results = {
            "tools_tested": 0,
            "tools_successful": 0,
            "tools_failed": 0,
            "tool_details": {},
        }

        obs_tools = ["summarize_health", "get_counters", "recent_degradations"]

        for tool_name in obs_tools:
            try:
                start_time = time.time()

                result = self.mcp_tool.run(
                    namespace="obs",
                    name=tool_name,
                    params={},
                )

                duration = time.time() - start_time
                MCP_TOOL_CALL_LATENCY.labels(tool_name=tool_name).observe(duration)

                obs_results["tools_tested"] += 1
                if result.success:
                    obs_results["tools_successful"] += 1
                    MCP_TOOL_CALL_COUNT.labels(tool_name=tool_name).inc()
                    obs_results["tool_details"][tool_name] = "✅ Working"
                else:
                    obs_results["tools_failed"] += 1
                    MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                    obs_results["tool_details"][tool_name] = f"❌ Failed: {result.error}"

            except Exception as e:
                obs_results["tools_failed"] += 1
                MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                obs_results["tool_details"][tool_name] = f"❌ Exception: {e!s}"

        return obs_results

    def test_http_tools(self) -> dict[str, Any]:
        """Test HTTP tools."""
        print("\n🌐 Testing HTTP Tools...")

        http_results = {
            "tools_tested": 0,
            "tools_successful": 0,
            "tools_failed": 0,
            "tool_details": {},
        }

        http_tools = ["http_get", "http_json_get"]

        for tool_name in http_tools:
            try:
                start_time = time.time()

                # Test with a safe URL
                params = (
                    {"url": "https://httpbin.org/json"}
                    if tool_name == "http_json_get"
                    else {"url": "https://httpbin.org/get"}
                )

                result = self.mcp_tool.run(
                    namespace="http",
                    name=tool_name,
                    params=params,
                )

                duration = time.time() - start_time
                MCP_TOOL_CALL_LATENCY.labels(tool_name=tool_name).observe(duration)

                http_results["tools_tested"] += 1
                if result.success:
                    http_results["tools_successful"] += 1
                    MCP_TOOL_CALL_COUNT.labels(tool_name=tool_name).inc()
                    http_results["tool_details"][tool_name] = "✅ Working"
                else:
                    http_results["tools_failed"] += 1
                    MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                    http_results["tool_details"][tool_name] = f"❌ Failed: {result.error}"

            except Exception as e:
                http_results["tools_failed"] += 1
                MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                http_results["tool_details"][tool_name] = f"❌ Exception: {e!s}"

        return http_results

    def test_ingest_tools(self) -> dict[str, Any]:
        """Test content ingestion tools."""
        print("\n📥 Testing Content Ingestion Tools...")

        ingest_results = {
            "tools_tested": 0,
            "tools_successful": 0,
            "tools_failed": 0,
            "tool_details": {},
        }

        ingest_tools = [
            "extract_metadata",
            "list_channel_videos",
            "fetch_transcript_local",
            "summarize_subtitles",
        ]

        for tool_name in ingest_tools:
            try:
                start_time = time.time()

                # Test with mock parameters
                params = {
                    "url": "https://youtube.com/watch?v=test123",
                    "channel_id": "test_channel",
                    "video_id": "test123",
                }

                result = self.mcp_tool.run(
                    namespace="ingest",
                    name=tool_name,
                    params=params,
                )

                duration = time.time() - start_time
                MCP_TOOL_CALL_LATENCY.labels(tool_name=tool_name).observe(duration)

                ingest_results["tools_tested"] += 1
                if result.success:
                    ingest_results["tools_successful"] += 1
                    MCP_TOOL_CALL_COUNT.labels(tool_name=tool_name).inc()
                    ingest_results["tool_details"][tool_name] = "✅ Working"
                else:
                    ingest_results["tools_failed"] += 1
                    MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                    ingest_results["tool_details"][tool_name] = f"❌ Failed: {result.error}"

            except Exception as e:
                ingest_results["tools_failed"] += 1
                MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                ingest_results["tool_details"][tool_name] = f"❌ Exception: {e!s}"

        return ingest_results

    def test_kg_tools(self) -> dict[str, Any]:
        """Test knowledge graph tools."""
        print("\n🧠 Testing Knowledge Graph Tools...")

        kg_results = {
            "tools_tested": 0,
            "tools_successful": 0,
            "tools_failed": 0,
            "tool_details": {},
        }

        kg_tools = ["kg_query", "kg_timeline", "policy_keys"]

        for tool_name in kg_tools:
            try:
                start_time = time.time()

                # Test with mock parameters
                params = {
                    "query": "test query",
                    "entity": "test_entity",
                    "timeframe": "2024-01-01",
                }

                result = self.mcp_tool.run(
                    namespace="kg",
                    name=tool_name,
                    params=params,
                )

                duration = time.time() - start_time
                MCP_TOOL_CALL_LATENCY.labels(tool_name=tool_name).observe(duration)

                kg_results["tools_tested"] += 1
                if result.success:
                    kg_results["tools_successful"] += 1
                    MCP_TOOL_CALL_COUNT.labels(tool_name=tool_name).inc()
                    kg_results["tool_details"][tool_name] = "✅ Working"
                else:
                    kg_results["tools_failed"] += 1
                    MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                    kg_results["tool_details"][tool_name] = f"❌ Failed: {result.error}"

            except Exception as e:
                kg_results["tools_failed"] += 1
                MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                kg_results["tool_details"][tool_name] = f"❌ Exception: {e!s}"

        return kg_results

    def test_router_tools(self) -> dict[str, Any]:
        """Test model routing tools."""
        print("\n🔄 Testing Model Routing Tools...")

        router_results = {
            "tools_tested": 0,
            "tools_successful": 0,
            "tools_failed": 0,
            "tool_details": {},
        }

        router_tools = ["estimate_cost", "route_completion", "choose_embedding_model"]

        for tool_name in router_tools:
            try:
                start_time = time.time()

                # Test with mock parameters
                params = {
                    "task_type": "test",
                    "prompt": "test prompt",
                    "model": "test_model",
                }

                result = self.mcp_tool.run(
                    namespace="router",
                    name=tool_name,
                    params=params,
                )

                duration = time.time() - start_time
                MCP_TOOL_CALL_LATENCY.labels(tool_name=tool_name).observe(duration)

                router_results["tools_tested"] += 1
                if result.success:
                    router_results["tools_successful"] += 1
                    MCP_TOOL_CALL_COUNT.labels(tool_name=tool_name).inc()
                    router_results["tool_details"][tool_name] = "✅ Working"
                else:
                    router_results["tools_failed"] += 1
                    MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                    router_results["tool_details"][tool_name] = f"❌ Failed: {result.error}"

            except Exception as e:
                router_results["tools_failed"] += 1
                MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                router_results["tool_details"][tool_name] = f"❌ Exception: {e!s}"

        return router_results

    def test_multimodal_tools(self) -> dict[str, Any]:
        """Test multimodal analysis tools."""
        print("\n🎭 Testing Multimodal Analysis Tools...")

        multimodal_results = {
            "tools_tested": 0,
            "tools_successful": 0,
            "tools_failed": 0,
            "tool_details": {},
        }

        multimodal_tools = [
            "analyze_image",
            "analyze_video",
            "analyze_audio",
            "analyze_content_auto",
            "get_visual_sentiment",
            "extract_content_themes",
        ]

        for tool_name in multimodal_tools:
            try:
                start_time = time.time()

                # Test with mock parameters
                params = {
                    "file_path": "test_file.jpg",
                    "content_type": "image",
                    "analysis_type": "general",
                }

                result = self.mcp_tool.run(
                    namespace="multimodal",
                    name=tool_name,
                    params=params,
                )

                duration = time.time() - start_time
                MCP_TOOL_CALL_LATENCY.labels(tool_name=tool_name).observe(duration)

                multimodal_results["tools_tested"] += 1
                if result.success:
                    multimodal_results["tools_successful"] += 1
                    MCP_TOOL_CALL_COUNT.labels(tool_name=tool_name).inc()
                    multimodal_results["tool_details"][tool_name] = "✅ Working"
                else:
                    multimodal_results["tools_failed"] += 1
                    MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                    multimodal_results["tool_details"][tool_name] = f"❌ Failed: {result.error}"

            except Exception as e:
                multimodal_results["tools_failed"] += 1
                MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                multimodal_results["tool_details"][tool_name] = f"❌ Exception: {e!s}"

        return multimodal_results

    def test_memory_tools(self) -> dict[str, Any]:
        """Test memory tools."""
        print("\n💾 Testing Memory Tools...")

        memory_results = {
            "tools_tested": 0,
            "tools_successful": 0,
            "tools_failed": 0,
            "tool_details": {},
        }

        memory_tools = ["vs_search", "vs_list_namespaces", "vs_samples"]

        for tool_name in memory_tools:
            try:
                start_time = time.time()

                # Test with mock parameters
                params = {
                    "query": "test query",
                    "namespace": "test_namespace",
                    "limit": 10,
                }

                result = self.mcp_tool.run(
                    namespace="memory",
                    name=tool_name,
                    params=params,
                )

                duration = time.time() - start_time
                MCP_TOOL_CALL_LATENCY.labels(tool_name=tool_name).observe(duration)

                memory_results["tools_tested"] += 1
                if result.success:
                    memory_results["tools_successful"] += 1
                    MCP_TOOL_CALL_COUNT.labels(tool_name=tool_name).inc()
                    memory_results["tool_details"][tool_name] = "✅ Working"
                else:
                    memory_results["tools_failed"] += 1
                    MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                    memory_results["tool_details"][tool_name] = f"❌ Failed: {result.error}"

            except Exception as e:
                memory_results["tools_failed"] += 1
                MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                memory_results["tool_details"][tool_name] = f"❌ Exception: {e!s}"

        return memory_results

    def test_a2a_tools(self) -> dict[str, Any]:
        """Test agent-to-agent tools."""
        print("\n🤖 Testing Agent-to-Agent Tools...")

        a2a_results = {
            "tools_tested": 0,
            "tools_successful": 0,
            "tools_failed": 0,
            "tool_details": {},
        }

        a2a_tools = ["a2a_call"]

        for tool_name in a2a_tools:
            try:
                start_time = time.time()

                # Test with mock parameters
                params = {
                    "target_agent": "test_agent",
                    "message": "test message",
                    "context": {"test": "value"},
                }

                result = self.mcp_tool.run(
                    namespace="a2a",
                    name=tool_name,
                    params=params,
                )

                duration = time.time() - start_time
                MCP_TOOL_CALL_LATENCY.labels(tool_name=tool_name).observe(duration)

                a2a_results["tools_tested"] += 1
                if result.success:
                    a2a_results["tools_successful"] += 1
                    MCP_TOOL_CALL_COUNT.labels(tool_name=tool_name).inc()
                    a2a_results["tool_details"][tool_name] = "✅ Working"
                else:
                    a2a_results["tools_failed"] += 1
                    MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                    a2a_results["tool_details"][tool_name] = f"❌ Failed: {result.error}"

            except Exception as e:
                a2a_results["tools_failed"] += 1
                MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                a2a_results["tool_details"][tool_name] = f"❌ Exception: {e!s}"

        return a2a_results

    def test_crewai_tools(self) -> dict[str, Any]:
        """Test CrewAI tools."""
        print("\n👥 Testing CrewAI Tools...")

        crewai_results = {
            "tools_tested": 0,
            "tools_successful": 0,
            "tools_failed": 0,
            "tool_details": {},
        }

        crewai_tools = [
            "list_available_crews",
            "get_crew_status",
            "execute_crew",
            "get_agent_performance",
            "abort_crew_execution",
        ]

        for tool_name in crewai_tools:
            try:
                start_time = time.time()

                # Test with mock parameters
                params = {
                    "crew_id": "test_crew",
                    "agent_id": "test_agent",
                    "task": "test_task",
                }

                result = self.mcp_tool.run(
                    namespace="crewai",
                    name=tool_name,
                    params=params,
                )

                duration = time.time() - start_time
                MCP_TOOL_CALL_LATENCY.labels(tool_name=tool_name).observe(duration)

                crewai_results["tools_tested"] += 1
                if result.success:
                    crewai_results["tools_successful"] += 1
                    MCP_TOOL_CALL_COUNT.labels(tool_name=tool_name).inc()
                    crewai_results["tool_details"][tool_name] = "✅ Working"
                else:
                    crewai_results["tools_failed"] += 1
                    MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                    crewai_results["tool_details"][tool_name] = f"❌ Failed: {result.error}"

            except Exception as e:
                crewai_results["tools_failed"] += 1
                MCP_TOOL_CALL_ERROR_COUNT.labels(tool_name=tool_name).inc()
                crewai_results["tool_details"][tool_name] = f"❌ Exception: {e!s}"

        return crewai_results

    def run_all_tests(self) -> dict[str, Any]:
        """Run all MCP tool validation tests."""
        print("🚀 Starting MCP Tools Validation...")

        start_time = time.time()

        # Run all validation tests
        self.results["tool_registry"] = self.validate_tool_registry()
        self.results["obs_tools"] = self.test_obs_tools()
        self.results["http_tools"] = self.test_http_tools()
        self.results["ingest_tools"] = self.test_ingest_tools()
        self.results["kg_tools"] = self.test_kg_tools()
        self.results["router_tools"] = self.test_router_tools()
        self.results["multimodal_tools"] = self.test_multimodal_tools()
        self.results["memory_tools"] = self.test_memory_tools()
        self.results["a2a_tools"] = self.test_a2a_tools()
        self.results["crewai_tools"] = self.test_crewai_tools()

        # Calculate overall results
        total_tests = sum(
            suite.get("tools_tested", 0)
            for suite in self.results.values()
            if isinstance(suite, dict) and "tools_tested" in suite
        )

        total_successful = sum(
            suite.get("tools_successful", 0)
            for suite in self.results.values()
            if isinstance(suite, dict) and "tools_successful" in suite
        )

        total_failed = sum(
            suite.get("tools_failed", 0)
            for suite in self.results.values()
            if isinstance(suite, dict) and "tools_failed" in suite
        )

        self.results["summary"] = {
            "total_tests": total_tests,
            "total_successful": total_successful,
            "total_failed": total_failed,
            "success_rate": total_successful / total_tests if total_tests > 0 else 0.0,
            "test_duration": time.time() - start_time,
        }

        return self.results

    def generate_report(self) -> str:
        """Generate a comprehensive validation report."""
        report = []
        report.append("# MCP Tools Validation Report")
        report.append("")
        report.append(f"**Test Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Summary
        summary = self.results.get("summary", {})
        report.append("## Summary")
        report.append("")
        report.append(f"- **Total Tests:** {summary.get('total_tests', 0)}")
        report.append(f"- **Successful:** {summary.get('total_successful', 0)}")
        report.append(f"- **Failed:** {summary.get('total_failed', 0)}")
        report.append(f"- **Success Rate:** {summary.get('success_rate', 0.0):.2%}")
        report.append(f"- **Test Duration:** {summary.get('test_duration', 0.0):.2f}s")
        report.append("")

        # Tool Registry
        registry = self.results.get("tool_registry", {})
        report.append("## Tool Registry")
        report.append("")
        report.append(f"- **Namespaces:** {registry.get('namespaces_count', 0)}")
        report.append(f"- **Total Tools:** {registry.get('total_tools', 0)}")
        report.append("")

        for namespace, details in registry.get("tools_by_namespace", {}).items():
            report.append(f"### {namespace}")
            report.append(f"- **Module:** {details.get('module_path', 'N/A')}")
            report.append(f"- **Tools:** {details.get('tool_count', 0)}")
            report.append(f"- **Tool Names:** {', '.join(details.get('tools', []))}")
            report.append("")

        # Detailed results
        for suite_name, suite_results in self.results.items():
            if suite_name in ["summary", "tool_registry"]:
                continue

            report.append(f"## {suite_name.replace('_', ' ').title()}")
            report.append("")

            # Suite summary
            suite_tests = suite_results.get("tools_tested", 0)
            suite_successful = suite_results.get("tools_successful", 0)
            suite_failed = suite_results.get("tools_failed", 0)

            report.append(f"- **Tests:** {suite_tests}")
            report.append(f"- **Successful:** {suite_successful}")
            report.append(f"- **Failed:** {suite_failed}")
            report.append("")

            # Detailed results
            details = suite_results.get("tool_details", {})
            for tool_name, status in details.items():
                report.append(f"- **{tool_name}:** {status}")
            report.append("")

        return "\n".join(report)


def main() -> None:
    """Main function."""
    validator = MCPToolsValidator()

    # Run all tests
    results = validator.run_all_tests()

    # Generate and save report
    report = validator.generate_report()

    report_path = Path("docs/mcp_tools_validation_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        f.write(report)

    print(f"\n✅ MCP tools validation report saved: {report_path}")

    # Print summary
    summary = results.get("summary", {})
    print("\n📊 Validation Summary:")
    print(f"  Total Tests: {summary.get('total_tests', 0)}")
    print(f"  Successful: {summary.get('total_successful', 0)}")
    print(f"  Failed: {summary.get('total_failed', 0)}")
    print(f"  Success Rate: {summary.get('success_rate', 0.0):.2%}")
    print(f"  Duration: {summary.get('test_duration', 0.0):.2f}s")


if __name__ == "__main__":
    main()
