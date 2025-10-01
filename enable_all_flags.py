#!/usr/bin/env python3
"""
Script to enable all currently disabled flags in .env
"""

import re


def enable_all_flags():
    # Read current .env
    with open(".env") as f:
        content = f.read()

    # Pattern to match ENABLE_*=false (both commented and uncommented)
    patterns = [
        (r"^ENABLE_([^=]+)=false", r"ENABLE_\1=true"),
        (r"^# ENABLE_([^=]+)=false", r"ENABLE_\1=true"),
    ]

    changes = []
    new_content = content

    for pattern, replacement in patterns:
        matches = re.findall(pattern, new_content, re.MULTILINE)
        if matches:
            changes.extend(matches)
            new_content = re.sub(pattern, replacement, new_content, flags=re.MULTILINE)

    # Write back to file
    with open(".env", "w") as f:
        f.write(new_content)

    print(f"Enabled {len(changes)} flags:")
    for flag in sorted(set(changes)):
        print(f"  - ENABLE_{flag}")


if __name__ == "__main__":
    enable_all_flags()
