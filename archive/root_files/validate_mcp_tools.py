#!/usr/bin/env python3
"""Comprehensive MCP Tools Validation Script.

This script validates all 45+ MCP tools and research workflows in the system.
It provides detailed reporting on functionality, performance, and integration.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from validation.mcp_tools_validator import (
    validate_all_mcp_tools,
    validate_research_workflows,
)


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def print_header(title: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n📋 {title}")
    print("-" * 40)


def print_server_results(server_results: list) -> None:
    """Print detailed server validation results."""
    for result in server_results:
        status = "✅ AVAILABLE" if result.available else "❌ UNAVAILABLE"
        print(f"\n🔧 Server: {result.server_name}")
        print(f"   Status: {status}")
        print(f"   Tools Validated: {result.tools_validated}")
        print(f"   Tools Failed: {result.tools_failed}")
        print(f"   Total Latency: {result.total_latency_ms:.1f}ms")

        if result.error_summary:
            print(f"   Error: {result.error_summary}")

        # Print individual tool results
        if result.validation_results:
            print("   Tool Details:")
            for tool_result in result.validation_results:
                tool_status = "✅" if tool_result.success else "❌"
                print(f"     {tool_status} {tool_result.tool_name}: {tool_result.latency_ms:.1f}ms")
                if tool_result.error_message:
                    print(f"       Error: {tool_result.error_message}")


def print_recommendations(recommendations: list[str]) -> None:
    """Print recommendations for improvement."""
    if not recommendations:
        print("   🎉 No recommendations - all systems working optimally!")
        return

    print("\n💡 Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")


def print_workflow_results(workflow_data: dict) -> None:
    """Print research workflow validation results."""
    print("\n📊 Workflow Validation Summary:")
    print(f"   Successful Workflows: {workflow_data['successful_workflows']}/{workflow_data['total_workflows']}")
    print(f"   Success Rate: {workflow_data['workflow_success_rate']:.1f}%")
    print(f"   Average Latency: {workflow_data['average_workflow_latency_ms']:.1f}ms")

    print("\n🔍 Individual Workflow Results:")
    for workflow in workflow_data["workflow_results"]:
        status = "✅" if workflow["success"] else "❌"
        print(f"   {status} {workflow['workflow']}")
        print(f"      Steps: {' → '.join(workflow['steps'])}")
        print(f"      Latency: {workflow['total_latency_ms']:.1f}ms")
        if "error" in workflow:
            print(f"      Error: {workflow['error']}")


async def main() -> int:
    """Main validation function."""
    print_header("MCP Tools & Research Workflows Validation")

    print("🔍 Starting comprehensive validation of MCP tools and research workflows...")
    print("   This will test all available MCP servers, tools, and end-to-end workflows.")

    start_time = time.time()

    try:
        # Validate all MCP tools
        print_section("MCP Tools Validation")
        print("Testing all MCP servers and their tools...")

        mcp_report = await validate_all_mcp_tools(enable_all_servers=True)

        # Print MCP validation results
        print("\n📊 MCP Validation Summary:")
        print(f"   Total Servers: {mcp_report.total_servers}")
        print(f"   Available Servers: {mcp_report.available_servers}")
        print(f"   Total Tools: {mcp_report.total_tools}")
        print(f"   Validated Tools: {mcp_report.validated_tools}")
        print(f"   Failed Tools: {mcp_report.failed_tools}")
        print(f"   Overall Success Rate: {mcp_report.overall_success_rate:.1f}%")
        print(f"   Average Latency: {mcp_report.average_latency_ms:.1f}ms")

        # Print detailed server results
        print_server_results(mcp_report.server_results)

        # Print recommendations
        print_recommendations(mcp_report.recommendations)

        # Validate research workflows
        print_section("Research Workflows Validation")
        print("Testing end-to-end research workflows...")

        workflow_result = await validate_research_workflows()

        if workflow_result.success and workflow_result.data:
            actual_data = workflow_result.data.get("data", workflow_result.data)
            print_workflow_results(actual_data)
        else:
            print(f"❌ Workflow validation failed: {workflow_result.error}")

        # Overall summary
        total_time = time.time() - start_time
        print_header("Validation Summary")

        print(f"⏱️  Total Validation Time: {total_time:.2f} seconds")
        print(
            f"🔧 MCP Tools: {mcp_report.validated_tools}/{mcp_report.total_tools} successful ({mcp_report.overall_success_rate:.1f}%)"
        )

        if workflow_result.success and workflow_result.data:
            actual_data = workflow_result.data.get("data", workflow_result.data)
            print(
                f"🔄 Workflows: {actual_data['successful_workflows']}/{actual_data['total_workflows']} successful "
                f"({actual_data['workflow_success_rate']:.1f}%)"
            )
        else:
            print("🔄 Workflows: Validation failed")

        # Determine overall success
        mcp_success = mcp_report.overall_success_rate >= 80  # 80% threshold
        workflow_success = (
            workflow_result.success
            and workflow_result.data
            and workflow_result.data.get("data", workflow_result.data)["workflow_success_rate"] >= 70
        )  # 70% threshold

        if mcp_success and workflow_success:
            print("\n🎉 VALIDATION PASSED!")
            print("   ✅ MCP tools are working correctly")
            print("   ✅ Research workflows are functional")
            print("   ✅ System is ready for production use")
            return 0
        else:
            print("\n⚠️  VALIDATION PARTIALLY PASSED")
            if not mcp_success:
                print(f"   ❌ MCP tools success rate below threshold ({mcp_report.overall_success_rate:.1f}% < 80%)")
            if not workflow_success:
                actual_data = workflow_result.data.get("data", workflow_result.data) if workflow_result.data else {}
                workflow_rate = actual_data.get("workflow_success_rate", 0)
                print(f"   ❌ Workflows success rate below threshold ({workflow_rate:.1f}% < 70%)")
            print("   💡 Review recommendations above and fix issues before production deployment")
            return 1

    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        print("\n❌ VALIDATION FAILED!")
        print(f"   Error: {e}")
        return 2


def save_report_to_file(report_data: dict, filename: str = "mcp_validation_report.json") -> None:
    """Save validation report to JSON file."""
    try:
        with open(filename, "w") as f:
            json.dump(report_data, f, indent=2, default=str)
        print(f"\n💾 Validation report saved to: {filename}")
    except Exception as e:
        print(f"\n⚠️  Failed to save report: {e}")


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(3)
