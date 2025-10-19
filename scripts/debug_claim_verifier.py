#!/usr/bin/env python3
"""
Debug script for Claim Verifier Tool to understand the backend failure behavior.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Mock the crewai_tools import
class MockBaseTool:
    def __init__(self):
        self.name = "mock_tool"
        self.description = "Mock tool"
        self.args_schema = None


# Mock the imports
sys.modules["crewai_tools"] = type("MockModule", (), {"BaseTool": MockBaseTool})()

from unittest.mock import patch

from ultimate_discord_intelligence_bot.tools.claim_verifier_tool import ClaimVerifierTool


def test_backend_failure():
    """Test what happens when a backend fails."""
    tool = ClaimVerifierTool()

    print("Testing backend failure scenario...")

    with patch.object(tool, "_verify_with_serply", side_effect=Exception("API Error")):
        result = tool._run(claim_text="Test claim", backends=["serply"], tenant="test", workspace="test")

        print(f"Result success: {result.success}")
        print(f"Result error: {result.error}")

        if result.success:
            data = result.data["data"]
            print(f"Backend performance: {data['backend_performance']}")

            serply_perf = data["backend_performance"].get("serply", {})
            print(f"Serply success: {serply_perf.get('success')}")
            print(f"Serply error: {serply_perf.get('error')}")
        else:
            print("Result failed, no data to inspect")


if __name__ == "__main__":
    test_backend_failure()
