"""AST-based import migration tool for repository restructuring.

This script systematically rewrites import statements across the codebase
to match the new 3-layer architecture (Platform → Domain → App).
"""

import argparse
import ast
from pathlib import Path


class ImportRewriter(ast.NodeTransformer):
    """AST transformer for systematic import migration."""

    def __init__(self, file_path: Path):
        """Initialize rewriter with file path for context."""
        self.file_path = file_path
        self.changes: list[str] = []

        # Comprehensive mapping: old_module -> new_module
        self.IMPORT_MAPPINGS: dict[str, str] = {
            # StepResult - YES, moved to platform
            "ultimate_discord_intelligence_bot.step_result": "platform.core.step_result",
            # Settings - NO, stays in app layer (not migrated yet)
            "ultimate_discord_intelligence_bot.settings": "ultimate_discord_intelligence_bot.settings",
            "ultimate_discord_intelligence_bot.config": "ultimate_discord_intelligence_bot.config",
            "ultimate_discord_intelligence_bot.config_schema": "ultimate_discord_intelligence_bot.config_schema",
            "ultimate_discord_intelligence_bot.config_types": "ultimate_discord_intelligence_bot.config_types",
            # Services migrations
            "ultimate_discord_intelligence_bot.services.openrouter_service": "platform.llm.providers.openrouter",
            "ultimate_discord_intelligence_bot.services.prompt_engine": "platform.prompts.engine",
            "ultimate_discord_intelligence_bot.services.memory_service": "domains.memory.vector_store",
            # Tools and analysis
            "ultimate_discord_intelligence_bot.tools.analysis": "domains.intelligence.analysis",
            "ultimate_discord_intelligence_bot.tools.verification": "domains.intelligence.verification",
            "ultimate_discord_intelligence_bot.tools.acquisition": "domains.ingestion.providers",
            # Orchestration
            "ultimate_discord_intelligence_bot.agents": "domains.orchestration.agents",
            "ultimate_discord_intelligence_bot.crew": "domains.orchestration.crew",
            "ultimate_discord_intelligence_bot.crew_core": "domains.orchestration.crew",
            # Observability
            "ultimate_discord_intelligence_bot.obs": "platform.observability",
            # HTTP and caching
            "ultimate_discord_intelligence_bot.core.http_utils": "platform.http.http_utils",
            "ultimate_discord_intelligence_bot.core.cache": "platform.cache",
            "ultimate_discord_intelligence_bot.core": "platform.core",
            # AI and RL
            "ultimate_discord_intelligence_bot.ai.rl": "platform.rl",
            "ultimate_discord_intelligence_bot.ai.routing": "platform.llm.routing",
            "ultimate_discord_intelligence_bot.ai": "platform.rl",
            # Security and policy
            "ultimate_discord_intelligence_bot.security": "platform.security",
            "ultimate_discord_intelligence_bot.policy": "platform.security.policy",
            # src.* imports (platform)
            "src.core": "platform.core",
            "src.ai": "platform.rl",
            "src.obs": "platform.observability",
            "src.http": "platform.http",
            "src.cache": "platform.cache",
            "src.config": "platform.config",
            "src.security": "platform.security",
            # src.* imports (domains - more complex mapping)
            "src.services.rag": "domains.memory.vector",
            "src.services": "domains",  # Will need suffix matching
            "src.ingest": "domains.ingestion",
            "src.analysis": "domains.intelligence.analysis",
            "src.verification": "domains.intelligence.verification",
            "src.memory": "domains.memory",
            "src.graphs": "graphs",  # Preserved module
            "src.eval": "eval",  # Preserved module
            # Legacy patterns
            "core.settings": "platform.config.settings",
            "core.secure_config": "platform.config.configuration",
            "core.step_result": "platform.core.step_result",
            "core.http_utils": "platform.http.http_utils",
            "core.cache": "platform.cache",
            "obs": "platform.observability",
            "obs.metrics": "platform.observability.metrics",
            # Ultimate app package config - keep in old location for now
            "ultimate_discord_intelligence_bot.config.feature_flags": "ultimate_discord_intelligence_bot.config.feature_flags",
            "ultimate_discord_intelligence_bot.config.base": "ultimate_discord_intelligence_bot.config.base",
            "ultimate_discord_intelligence_bot.config.paths": "ultimate_discord_intelligence_bot.config.paths",
            # Preserved modules (no change)
            "server": "server",
            "mcp_server": "mcp_server",
        }

    def visit_Import(self, node: ast.Import) -> ast.Import:
        """Rewrite 'import X' statements."""
        for alias in node.names:
            if new_name := self._map_module(alias.name):
                self.changes.append(f"import {alias.name} → import {new_name}")
                alias.name = new_name
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
        """Rewrite 'from X import Y' statements."""
        if node.module and (new_module := self._map_module(node.module)):
            old_from = f"from {node.module}"
            new_from = f"from {new_module}"
            self.changes.append(f"{old_from} → {new_from}")
            node.module = new_module
        return node

    def _map_module(self, old_module: str) -> str | None:
        """Map old module path to new location.

        Args:
            old_module: The old import module path

        Returns:
            New module path, or None if no mapping exists
        """
        # 1. Exact match
        if old_module in self.IMPORT_MAPPINGS:
            return self.IMPORT_MAPPINGS[old_module]

        # 2. Prefix match (e.g., ultimate_discord_intelligence_bot.tools.analysis.X)
        # Find longest matching prefix
        longest_match = ""
        longest_new_prefix = ""
        for old_prefix, new_prefix in self.IMPORT_MAPPINGS.items():
            if old_module.startswith(old_prefix + "."):
                # Use longest prefix to avoid partial matches
                if len(old_prefix) > len(longest_match):
                    longest_match = old_prefix
                    longest_new_prefix = new_prefix

        if longest_match:
            suffix = old_module[len(longest_match) :]
            return longest_new_prefix + suffix

        # 3. src.* imports → platform/domains (already handled above in mappings)
        # Keep as fallback for any edge cases
        if old_module.startswith("src."):
            parts = old_module.split(".")
            if len(parts) >= 2:
                if parts[1] in ["core", "ai", "obs", "http", "cache", "config", "security"]:
                    return f"platform.{'.'.join(parts[1:])}"

        return None


def rewrite_file(file_path: Path, dry_run: bool = False) -> tuple[bool, list[str]]:
    """Rewrite imports in a single file using AST.

    Args:
        file_path: Path to Python file to rewrite
        dry_run: If True, don't actually write changes

    Returns:
        Tuple of (changed?, list of change descriptions)
    """
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))

        rewriter = ImportRewriter(file_path)
        new_tree = rewriter.visit(tree)

        if not rewriter.changes:
            return False, []

        # Unparse and write back
        new_source = ast.unparse(new_tree)

        # Preserve original file if no changes were made to content
        # (AST might format slightly differently)
        if not dry_run:
            file_path.write_text(new_source, encoding="utf-8")

        return True, rewriter.changes

    except SyntaxError as e:
        return False, [f"SYNTAX ERROR: {e}"]
    except Exception as e:
        return False, [f"ERROR: {e}"]


def main(target_dirs: list[Path], dry_run: bool = True, verbose: bool = False):
    """Run migration across all Python files.

    Args:
        target_dirs: List of directories to process
        dry_run: If True, don't actually write changes
        verbose: If True, show all changes, not just summary
    """
    files: list[Path] = []
    for target_dir in target_dirs:
        if target_dir.is_file():
            files.append(target_dir)
        elif target_dir.is_dir():
            files.extend(target_dir.rglob("*.py"))
        else:
            print(f"Warning: {target_dir} is not a file or directory, skipping")
            continue

    total = len(files)
    modified = 0
    errors = 0

    print(f"Scanning {total} Python files in {len(target_dirs)} locations...")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    for i, file_path in enumerate(files, 1):
        changed, changes = rewrite_file(file_path, dry_run=dry_run)

        if changed:
            modified += 1
            if verbose or dry_run:
                print(f"\n[{i}/{total}] {file_path}")
                for change in changes[:10]:  # Limit output
                    print(f"  → {change}")
                if len(changes) > 10:
                    print(f"  ... and {len(changes) - 10} more")
        elif any("ERROR" in c for c in changes):
            errors += 1
            if verbose:
                print(f"\n[{i}/{total}] {file_path}")
                for error in changes:
                    print(f"  ⚠️  {error}")

    print(f"\n{'DRY RUN: ' if dry_run else ''}Modified {modified}/{total} files")
    if errors > 0:
        print(f"⚠️  {errors} files had errors")
    else:
        print("✅ All files processed successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate imports to new 3-layer architecture using AST transformation")
    parser.add_argument(
        "targets",
        nargs="+",
        type=Path,
        help="Files or directories to process",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Don't actually write changes (default: True)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually write changes (overrides --dry-run)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed output for all files",
    )

    args = parser.parse_args()

    # If --execute is set, turn off dry_run
    dry_run = args.dry_run and not args.execute

    if not dry_run:
        print("⚠️  Executing import migration - files will be modified")
        # Auto-confirm when called from automation

    main(args.targets, dry_run=dry_run, verbose=args.verbose)
