#!/usr/bin/env python3
"""Migration script to replace scattered os.getenv() calls with secure configuration.

This script identifies and helps migrate tools and services to use the new
centralized secure configuration system instead of direct os.getenv() calls.

Usage:
    python scripts/migrate_to_secure_config.py --analyze
    python scripts/migrate_to_secure_config.py --migrate --dry-run
    python scripts/migrate_to_secure_config.py --migrate
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path
from typing import NamedTuple

logger = logging.getLogger(__name__)


class ConfigUsage(NamedTuple):
    file_path: Path
    line_number: int
    env_var: str
    context: str
    suggested_replacement: str


# Mapping of environment variables to secure config methods
API_KEY_MAPPING = {
    "OPENAI_API_KEY": "config.get_api_key('openai')",
    "OPENROUTER_API_KEY": "config.get_api_key('openrouter')",
    "GOOGLE_API_KEY": "config.get_api_key('google')",
    "PERSPECTIVE_API_KEY": "config.get_api_key('perspective')",
    "SERPLY_API_KEY": "config.get_api_key('serply')",
    "EXA_API_KEY": "config.get_api_key('exa')",
    "PERPLEXITY_API_KEY": "config.get_api_key('perplexity')",
    "WOLFRAM_ALPHA_APP_ID": "config.get_api_key('wolfram')",
}

WEBHOOK_MAPPING = {
    "DISCORD_WEBHOOK": "config.get_webhook('discord')",
    "DISCORD_PRIVATE_WEBHOOK": "config.get_webhook('discord_private')",
    "DISCORD_ALERT_WEBHOOK": "config.get_webhook('discord_alert')",
}

FEATURE_FLAG_MAPPING = {
    "ENABLE_HTTP_RETRY": "config.is_feature_enabled('http_retry')",
    "ENABLE_CACHE_GLOBAL": "config.is_feature_enabled('cache_global')",
    "ENABLE_RL_GLOBAL": "config.is_feature_enabled('rl_global')",
    "ENABLE_DISCORD_COMMANDS": "config.is_feature_enabled('discord_commands')",
    "ENABLE_PII_DETECTION": "config.is_feature_enabled('pii_detection')",
    "ENABLE_CONTENT_MODERATION": "config.is_feature_enabled('content_moderation')",
    "ENABLE_RATE_LIMITING": "config.is_feature_enabled('rate_limiting')",
}

SETTING_MAPPING = {
    "HTTP_TIMEOUT": "config.http_timeout",
    "RETRY_MAX_ATTEMPTS": "config.retry_max_attempts",
    "VECTOR_BATCH_SIZE": "config.vector_batch_size",
    "QDRANT_URL": "config.qdrant_url",
    "QDRANT_API_KEY": "config.qdrant_api_key",
}


def find_os_getenv_usage(root_path: Path) -> list[ConfigUsage]:
    """Find all os.getenv() calls in Python files."""
    usages = []

    for py_file in root_path.rglob("*.py"):
        if "test" in str(py_file) or "migration" in str(py_file):
            continue  # Skip test files and migration scripts

        try:
            content = py_file.read_text(encoding="utf-8")
            lines = content.splitlines()

            for line_num, line in enumerate(lines, 1):
                # Find os.getenv() patterns
                getenv_pattern = r'os\.getenv\s*\(\s*["\']([^"\']+)["\']'
                matches = re.findall(getenv_pattern, line)

                for env_var in matches:
                    # Determine suggested replacement
                    if env_var in API_KEY_MAPPING:
                        replacement = API_KEY_MAPPING[env_var]
                    elif env_var in WEBHOOK_MAPPING:
                        replacement = WEBHOOK_MAPPING[env_var]
                    elif env_var in FEATURE_FLAG_MAPPING:
                        replacement = FEATURE_FLAG_MAPPING[env_var]
                    elif env_var in SETTING_MAPPING:
                        replacement = SETTING_MAPPING[env_var]
                    else:
                        replacement = f"config.get_setting('{env_var.lower()}')"

                    usages.append(ConfigUsage(
                        file_path=py_file,
                        line_number=line_num,
                        env_var=env_var,
                        context=line.strip(),
                        suggested_replacement=replacement
                    ))

        except Exception as e:
            logger.warning(f"Error processing {py_file}: {e}")

    return usages


def analyze_usage(root_path: Path) -> None:
    """Analyze current os.getenv() usage and report findings."""
    usages = find_os_getenv_usage(root_path)

    print(f"Found {len(usages)} os.getenv() calls that should be migrated:")
    print()

    # Group by category
    api_keys = [u for u in usages if u.env_var in API_KEY_MAPPING]
    webhooks = [u for u in usages if u.env_var in WEBHOOK_MAPPING]
    feature_flags = [u for u in usages if u.env_var in FEATURE_FLAG_MAPPING]
    settings = [u for u in usages if u.env_var in SETTING_MAPPING]
    other = [u for u in usages if u.env_var not in {**API_KEY_MAPPING, **WEBHOOK_MAPPING, **FEATURE_FLAG_MAPPING, **SETTING_MAPPING}]

    if api_keys:
        print("🔑 API Keys:")
        for usage in api_keys:
            print(f"  {usage.file_path}:{usage.line_number} - {usage.env_var}")
            print(f"    Current: {usage.context}")
            print(f"    Suggested: {usage.suggested_replacement}")
            print()

    if webhooks:
        print("🔗 Webhooks:")
        for usage in webhooks:
            print(f"  {usage.file_path}:{usage.line_number} - {usage.env_var}")
            print(f"    Current: {usage.context}")
            print(f"    Suggested: {usage.suggested_replacement}")
            print()

    if feature_flags:
        print("🚩 Feature Flags:")
        for usage in feature_flags:
            print(f"  {usage.file_path}:{usage.line_number} - {usage.env_var}")
            print(f"    Current: {usage.context}")
            print(f"    Suggested: {usage.suggested_replacement}")
            print()

    if settings:
        print("⚙️  Settings:")
        for usage in settings:
            print(f"  {usage.file_path}:{usage.line_number} - {usage.env_var}")
            print(f"    Current: {usage.context}")
            print(f"    Suggested: {usage.suggested_replacement}")
            print()

    if other:
        print("❓ Other Environment Variables:")
        for usage in other:
            print(f"  {usage.file_path}:{usage.line_number} - {usage.env_var}")
            print(f"    Current: {usage.context}")
            print()

    print("Summary:")
    print(f"  API Keys: {len(api_keys)} files")
    print(f"  Webhooks: {len(webhooks)} files")
    print(f"  Feature Flags: {len(feature_flags)} files")
    print(f"  Settings: {len(settings)} files")
    print(f"  Other: {len(other)} files")
    print(f"  Total: {len(usages)} usages across {len(set(u.file_path for u in usages))} files")


def migrate_file(file_path: Path, dry_run: bool = True) -> bool:
    """Migrate a single file to use secure configuration."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # Add import if not present
        if "from core.secure_config import get_config" not in content:
            # Find appropriate place to add import
            import_lines = []
            other_lines = []
            in_imports = True

            for line in content.splitlines():
                if line.startswith(("import ", "from ")) and in_imports:
                    import_lines.append(line)
                else:
                    if in_imports and line.strip() and not line.startswith("#"):
                        # Add our import before first non-import line
                        import_lines.append("from core.secure_config import get_config")
                        in_imports = False
                    other_lines.append(line)

            if in_imports:  # All imports at end of file
                import_lines.append("from core.secure_config import get_config")

            content = "\n".join(import_lines + other_lines)

        # Add config instance if not present
        if "config = get_config()" not in content and "get_config()" in content:
            # Add after imports
            lines = content.splitlines()
            insert_idx = 0
            for i, line in enumerate(lines):
                if not line.startswith(("import ", "from ", "#", '"""', "'''")) and line.strip():
                    insert_idx = i
                    break

            lines.insert(insert_idx, "")
            lines.insert(insert_idx + 1, "config = get_config()")
            lines.insert(insert_idx + 2, "")
            content = "\n".join(lines)

        # Replace os.getenv() calls
        all_mappings = {**API_KEY_MAPPING, **WEBHOOK_MAPPING, **FEATURE_FLAG_MAPPING, **SETTING_MAPPING}

        for env_var, replacement in all_mappings.items():
            # Match various os.getenv() patterns
            patterns = [
                rf'os\.getenv\s*\(\s*["\']?{env_var}["\']?\s*\)',
                rf'os\.getenv\s*\(\s*["\']?{env_var}["\']?\s*,\s*[^)]+\)',
            ]

            for pattern in patterns:
                content = re.sub(pattern, replacement, content)

        if content != original_content:
            if not dry_run:
                file_path.write_text(content, encoding="utf-8")
                print(f"✅ Migrated: {file_path}")
            else:
                print(f"🔄 Would migrate: {file_path}")
            return True

        return False

    except Exception as e:
        print(f"❌ Error migrating {file_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Migrate to secure configuration system")
    parser.add_argument("--analyze", action="store_true", help="Analyze current usage")
    parser.add_argument("--migrate", action="store_true", help="Perform migration")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed")
    parser.add_argument("--root", type=Path, default=Path("src"), help="Root directory to scan")

    args = parser.parse_args()

    if args.analyze:
        analyze_usage(args.root)
    elif args.migrate:
        usages = find_os_getenv_usage(args.root)
        files_to_migrate = list(set(u.file_path for u in usages))

        print(f"Migrating {len(files_to_migrate)} files...")
        print()

        migrated_count = 0
        for file_path in files_to_migrate:
            if migrate_file(file_path, dry_run=args.dry_run):
                migrated_count += 1

        print()
        print(f"Migration complete: {migrated_count}/{len(files_to_migrate)} files processed")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
