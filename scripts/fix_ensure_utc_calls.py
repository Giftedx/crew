#!/usr/bin/env python3
"""Fix ensure_utc() calls that should be default_utc_now() calls."""

import re
from pathlib import Path


def fix_ensure_utc_calls():
    """Replace ensure_utc() calls with default_utc_now() calls."""

    # Files to fix based on the grep results
    files_to_fix = [
        "src/ultimate_discord_intelligence_bot/advanced_performance_analytics_alert_management.py",
        "src/ultimate_discord_intelligence_bot/advanced_performance_analytics_discord_integration.py",
        "src/ultimate_discord_intelligence_bot/advanced_performance_analytics_alert_engine.py",
        "src/ultimate_discord_intelligence_bot/tools/advanced_performance_analytics_tool.py",
    ]

    for file_path in files_to_fix:
        path = Path(file_path)
        if not path.exists():
            print(f"File not found: {file_path}")
            continue

        print(f"Fixing {file_path}...")

        # Read file content
        with open(path) as f:
            content = f.read()

        # Add import if not present
        if "from core.time import ensure_utc" in content and "default_utc_now" not in content:
            content = content.replace(
                "from core.time import ensure_utc", "from core.time import ensure_utc, default_utc_now"
            )

        # Replace ensure_utc() calls
        content = re.sub(r"\bensure_utc\(\)", "default_utc_now()", content)

        # Write back
        with open(path, "w") as f:
            f.write(content)

        print(f"Fixed {file_path}")


if __name__ == "__main__":
    fix_ensure_utc_calls()
    print("All ensure_utc() calls fixed!")
