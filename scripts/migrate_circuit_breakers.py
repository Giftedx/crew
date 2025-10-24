#!/usr/bin/env python3
"""
Circuit Breaker Migration Script

This script migrates all existing circuit breaker implementations to use the canonical
circuit breaker implementation, ensuring consistent behavior across the codebase.
"""

import re
import sys
from pathlib import Path


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def migrate_file(file_path: Path) -> bool:
    """Migrate a single file to use canonical circuit breaker."""
    print(f"Migrating {file_path}")

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False

    original_content = content

    # Replace imports
    import_replacements = [
        # Core circuit breaker
        (
            r"from src\.core\.circuit_breaker import",
            "from ultimate_discord_intelligence_bot.core.circuit_breaker_canonical import",
        ),
        (
            r"from ultimate_discord_intelligence_bot\.creator_ops\.utils\.circuit_breaker import",
            "from ultimate_discord_intelligence_bot.core.circuit_breaker_canonical import",
        ),
        (
            r"from core\.resilience\.circuit_breaker import",
            "from ultimate_discord_intelligence_bot.core.circuit_breaker_canonical import",
        ),
        (
            r"from core\.http\.retry import.*_CircuitBreaker",
            "from ultimate_discord_intelligence_bot.core.circuit_breaker_canonical import CircuitBreaker as _CircuitBreaker",
        ),
    ]

    for old_import, new_import in import_replacements:
        content = re.sub(old_import, new_import, content)

    # Replace class instantiations
    class_replacements = [
        # Standard CircuitBreaker
        (r"CircuitBreaker\(", "CircuitBreaker("),
        # HTTP-specific _CircuitBreaker
        (r"_CircuitBreaker\(", "CircuitBreaker("),
    ]

    for old_class, new_class in class_replacements:
        content = re.sub(old_class, new_class, content)

    # Replace decorators
    decorator_replacements = [
        (r"@with_circuit_breaker\(", "@with_circuit_breaker("),
        (r"@circuit_breaker\(", "@circuit_breaker("),
    ]

    for old_decorator, new_decorator in decorator_replacements:
        content = re.sub(old_decorator, new_decorator, content)

    # Replace method calls
    method_replacements = [
        # State checking
        (r'\.state\s*==\s*["\']closed["\']', ".state == CircuitState.CLOSED"),
        (r'\.state\s*==\s*["\']open["\']', ".state == CircuitState.OPEN"),
        (r'\.state\s*==\s*["\']half_open["\']', ".state == CircuitState.HALF_OPEN"),
        # Method name changes
        (r"\.get_status\(\)", ".get_health_status()"),
        (r"\.get_metrics\(\)", ".get_stats()"),
    ]

    for old_method, new_method in method_replacements:
        content = re.sub(old_method, new_method, content)

    # Replace manager calls
    manager_replacements = [
        (
            r"circuit_manager\.get_breaker\(",
            "get_circuit_breaker_registry().get_circuit_breaker_sync(",
        ),
        (
            r"get_circuit_breaker_manager\(\)\.get_breaker\(",
            "get_circuit_breaker_registry().get_circuit_breaker_sync(",
        ),
        (
            r"_global_manager\.get_breaker_sync\(",
            "get_circuit_breaker_registry().get_circuit_breaker_sync(",
        ),
    ]

    for old_manager, new_manager in manager_replacements:
        content = re.sub(old_manager, new_manager, content)

    # Add necessary imports if we made changes
    if content != original_content:
        if "from ultimate_discord_intelligence_bot.core.circuit_breaker_canonical import" not in content:
            # Add import at the top
            lines = content.split("\n")
            import_line = "from ultimate_discord_intelligence_bot.core.circuit_breaker_canonical import CircuitBreaker, CircuitState, get_circuit_breaker_registry"

            # Find the right place to insert the import
            insert_index = 0
            for i, line in enumerate(lines):
                if line.startswith(("import ", "from ")):
                    insert_index = i + 1
                elif line.strip() == "":
                    continue
                else:
                    break

            lines.insert(insert_index, import_line)
            content = "\n".join(lines)

    # Write back if changed
    if content != original_content:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✓ Migrated {file_path}")
            return True
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            return False
    else:
        print(f"- No changes needed for {file_path}")
        return True


def main():
    """Main migration function."""
    print("🔄 Starting Circuit Breaker Migration")

    # Files to migrate
    files_to_migrate = [
        "src/ultimate_discord_intelligence_bot/creator_ops/integrations/youtube.py",
        "src/ultimate_discord_intelligence_bot/creator_ops/integrations/twitch.py",
        "src/ultimate_discord_intelligence_bot/creator_ops/integrations/tiktok.py",
        "src/ultimate_discord_intelligence_bot/creator_ops/integrations/instagram.py",
        "src/ultimate_discord_intelligence_bot/creator_ops/integrations/x.py",
        "src/core/http_utils.py",
        "src/core/structured_llm/service.py",
        "src/ultimate_discord_intelligence_bot/tools/pipeline_tool.py",
        "src/ultimate_discord_intelligence_bot/health_check.py",
        "src/ultimate_discord_intelligence_bot/performance_dashboard.py",
        "tests/test_http_circuit_breaker.py",
        "tests/test_service_integration_errors.py",
        "tests/creator_ops/utils/test_resilience.py",
        "tests/test_resilience_patterns.py",
    ]

    migrated_count = 0
    total_count = len(files_to_migrate)

    for file_path_str in files_to_migrate:
        file_path = Path(file_path_str)
        if file_path.exists():
            if migrate_file(file_path):
                migrated_count += 1
        else:
            print(f"- File not found: {file_path}")

    print(f"\n✅ Migration complete: {migrated_count}/{total_count} files migrated")

    # Create wrapper functions for backward compatibility
    create_compatibility_wrappers()


def create_compatibility_wrappers():
    """Create compatibility wrapper files for existing implementations."""
    print("\n📦 Creating compatibility wrappers...")

    # Create wrapper for core/resilience/circuit_breaker.py
    resilience_wrapper = '''"""
Compatibility wrapper for core/resilience/circuit_breaker.py

This module provides backward compatibility for the old circuit breaker implementation.
All functionality has been migrated to the canonical implementation.
"""

from ultimate_discord_intelligence_bot.core.circuit_breaker_canonical import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerConfig as CircuitConfig,
    CircuitBreakerMetrics as CircuitStats,
    CircuitBreakerError as CircuitBreakerOpenError,
    CircuitBreakerManager as CircuitBreakerRegistry,
    get_circuit_breaker as get_circuit_breaker_sync,
    get_circuit_breaker_manager as get_circuit_breaker_registry,
    circuit_breaker,
)

__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "CircuitConfig",
    "CircuitStats",
    "CircuitBreakerOpenError",
    "CircuitBreakerRegistry",
    "get_circuit_breaker_sync",
    "get_circuit_breaker_registry",
    "circuit_breaker",
]
'''

    with open("src/core/resilience/circuit_breaker.py", "w") as f:
        f.write(resilience_wrapper)

    # Create wrapper for creator_ops/utils/circuit_breaker.py
    creator_ops_wrapper = '''"""
Compatibility wrapper for creator_ops/utils/circuit_breaker.py

This module provides backward compatibility for the creator ops circuit breaker implementation.
All functionality has been migrated to the canonical implementation.
"""

from ultimate_discord_intelligence_bot.core.circuit_breaker_canonical import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    CircuitBreakerManager as CircuitBreakerRegistry,
    with_circuit_breaker,
    get_circuit_breaker_registry,
)

# Legacy compatibility
circuit_manager = get_circuit_breaker_registry()

__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerOpenError",
    "CircuitBreakerRegistry",
    "circuit_manager",
    "with_circuit_breaker",
]
'''

    with open(
        "src/ultimate_discord_intelligence_bot/creator_ops/utils/circuit_breaker.py",
        "w",
    ) as f:
        f.write(creator_ops_wrapper)

    print("✓ Created compatibility wrappers")


if __name__ == "__main__":
    main()
