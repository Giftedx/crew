#!/usr/bin/env python3
"""Script to categorize and move test files to the new structure."""

import shutil
from pathlib import Path


# Test categorization rules
TEST_CATEGORIES = {
    # Unit tests - fast, isolated, mocked
    "unit": {
        "tools": {
            "acquisition": ["youtube", "download", "ingest", "multi_platform", "enhanced_youtube"],
            "analysis": [
                "enhanced_analysis",
                "text_analysis",
                "sentiment",
                "political",
                "bias",
                "content_analysis",
                "multimodal_analysis",
            ],
            "verification": ["fact_check", "claim", "verification", "deception", "fallacy"],
            "memory": ["memory_storage", "memory_service", "graph_memory", "memory_v2"],
            "observability": ["system_status", "performance", "metrics", "monitoring", "status"],
        },
        "services": [
            "prompt_engine",
            "memory_service",
            "openrouter_service",
            "embedding_service",
            "analytics_service",
            "asr_service",
        ],
        "crew": ["crew", "agent", "task", "orchestrator"],
        "core": ["core", "utils", "http_utils", "config", "settings"],
    },
    # Integration tests - medium speed, limited external deps
    "integration": {
        "pipeline": ["pipeline", "content_pipeline", "multimodal_pipeline", "analysis_pipeline"],
        "memory": ["memory_integration", "vector_storage", "qdrant"],
        "discord": ["discord", "bot", "post", "monitor", "alert"],
        "agents": ["agent_coordination", "crewai", "orchestration"],
    },
    # E2E tests - slow, full system
    "e2e": {
        "full_workflow": ["e2e", "end_to_end", "complete", "workflow"],
        "performance": ["performance", "stress", "load", "benchmark"],
        "real_world": ["real_world", "scenario", "production"],
    },
}


def categorize_test_file(filename: str) -> tuple[str, str]:
    """Categorize a test file based on its name and content."""
    filename_lower = filename.lower()

    # Check for E2E tests first (they're usually obvious)
    if any(keyword in filename_lower for keyword in ["e2e", "end_to_end", "complete_workflow"]):
        return "e2e", "full_workflow"

    # Check for performance tests
    if any(keyword in filename_lower for keyword in ["performance", "stress", "load", "benchmark"]):
        return "e2e", "performance"

    # Check for integration tests
    if any(keyword in filename_lower for keyword in ["integration", "pipeline", "coordination"]):
        return "integration", "pipeline"

    # Check for Discord integration
    if "discord" in filename_lower:
        return "integration", "discord"

    # Check for memory integration
    if any(keyword in filename_lower for keyword in ["memory_integration", "vector_storage"]):
        return "integration", "memory"

    # Check for tool tests
    for tool_category, keywords in TEST_CATEGORIES["unit"]["tools"].items():
        if any(keyword in filename_lower for keyword in keywords):
            return "unit", f"tools/{tool_category}"

    # Check for service tests
    for keyword in TEST_CATEGORIES["unit"]["services"]:
        if keyword in filename_lower:
            return "unit", "services"

    # Check for crew tests
    for keyword in TEST_CATEGORIES["unit"]["crew"]:
        if keyword in filename_lower:
            return "unit", "crew"

    # Check for core tests
    for keyword in TEST_CATEGORIES["unit"]["core"]:
        if keyword in filename_lower:
            return "unit", "core"

    # Default to unit test
    return "unit", "core"


def move_test_file(source_path: str, dest_dir: str):
    """Move a test file to the new structure."""
    source = Path(source_path)
    dest = Path(dest_dir) / source.name

    # Create destination directory if it doesn't exist
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Move the file
    shutil.move(str(source), str(dest))
    print(f"Moved {source} -> {dest}")


def main():
    """Main function to categorize and move test files."""
    tests_dir = Path("/home/crew/tests")
    new_tests_dir = Path("/home/crew/tests_new")

    # Get all test files
    test_files = list(tests_dir.glob("test_*.py"))

    print(f"Found {len(test_files)} test files to categorize")

    # Categorize and move each file
    for test_file in test_files:
        category, subcategory = categorize_test_file(test_file.name)
        dest_dir = new_tests_dir / category / subcategory
        move_test_file(str(test_file), str(dest_dir))

    print("Test categorization complete!")


if __name__ == "__main__":
    main()
