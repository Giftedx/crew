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
        # Updated for Phase 1-6 consolidations
        self.IMPORT_MAPPINGS: dict[str, str] = {
            # === Platform Layer Migrations ===
            # Core infrastructure
            "core.step_result": "platform.core.step_result",
            "core.http_utils": "platform.http.http_utils",
            "core.http": "platform.http",
            "core.cache": "platform.cache",
            "core.rl": "platform.rl",
            "core.observability": "platform.observability",
            "core.security": "platform.security",
            "core.realtime": "platform.realtime",
            "core.configuration": "platform.config.configuration",
            "core.dependencies": "platform.config.dependencies",
            "core.memory": "platform.cache.memory",
            "core.multimodal": "platform.llm.multimodal",
            "core.privacy": "platform.security.privacy",
            "core.rate_limiting": "platform.security.rate_limiting",
            "core.resilience": "platform.http.resilience",
            "core.routing": "platform.llm.routing",
            "core.structured_llm": "platform.llm.structured",
            "core.vector_search": "domains.memory.vector.search",
            "core.learning_engine": "platform.rl.learning_engine",
            "core.secure_config": "platform.config.configuration",
            "core.settings": "platform.config.settings",
            "core": "platform",
            
            # AI/RL migrations
            "ai": "platform.rl",
            "ai.rl": "platform.rl",
            "ai.routing": "platform.llm.routing",
            "ai.bandits": "platform.rl.bandits",
            "ai.meta_learning": "platform.rl.meta_learning",
            "ai.feature_engineering": "platform.rl.feature_engineering",
            
            # Observability migrations
            "obs": "platform.observability",
            "obs.metrics": "platform.observability.metrics",
            "obs.tracing": "platform.observability.tracing",
            "obs.logging": "platform.observability.logging",
            
            # === Domain Layer Migrations ===
            # Ingestion
            "ingest": "domains.ingestion.pipeline",
            "ingest.pipeline": "domains.ingestion.pipeline",
            "ingest.providers": "domains.ingestion.providers",
            "ingest.sources": "domains.ingestion.pipeline.sources",
            "ingest.models": "domains.ingestion.pipeline.models",
            
            # Analysis
            "analysis": "domains.intelligence.analysis",
            "analysis.deduplication": "domains.intelligence.analysis.deduplication",
            "analysis.highlight": "domains.intelligence.analysis.highlight",
            "analysis.nlp": "domains.intelligence.analysis.nlp",
            "analysis.safety": "domains.intelligence.analysis.safety",
            "analysis.sentiment": "domains.intelligence.analysis.sentiment",
            "analysis.topic": "domains.intelligence.analysis.topic",
            "analysis.transcription": "domains.intelligence.analysis.transcription",
            "analysis.vision": "domains.intelligence.analysis.vision",
            "analysis.rerank": "domains.intelligence.analysis.rerank",
            
            # Memory
            "memory": "domains.memory",
            "memory.api": "domains.memory.api",
            "memory.store": "domains.memory.store",
            "memory.embeddings": "domains.memory.embeddings",
            "memory.vector_store": "domains.memory.vector_store",
            "memory.vector": "domains.memory.vector",
            "memory.graph": "domains.memory.graph",
            "memory.continual": "domains.memory.continual",
            "memory.qdrant_provider": "domains.memory.vector.qdrant",
            
            # === App Layer Migrations ===
            # Discord bot
            "ultimate_discord_intelligence_bot.discord": "app.discord",
            "ultimate_discord_intelligence_bot.discord_bot": "app.discord",
            "ultimate_discord_intelligence_bot.crew": "app.crew_executor",
            "ultimate_discord_intelligence_bot.config": "app.config",
            "ultimate_discord_intelligence_bot.main": "app.main",
            "ultimate_discord_intelligence_bot.step_result": "platform.core.step_result",
            "ultimate_discord_intelligence_bot.settings": "app.config.settings",
            
            # Orchestration
            "ultimate_discord_intelligence_bot.orchestrator": "domains.orchestration",
            "ultimate_discord_intelligence_bot.agents": "domains.orchestration.crewai.agents",
            "ultimate_discord_intelligence_bot.crew_core": "domains.orchestration.crew",
            "ultimate_discord_intelligence_bot.crew_components": "domains.orchestration.crewai",
            
            # Services
            "ultimate_discord_intelligence_bot.services.openrouter_service": "platform.llm.providers.openrouter",
            "ultimate_discord_intelligence_bot.services.prompt_engine": "platform.prompts.engine",
            "ultimate_discord_intelligence_bot.services.memory_service": "domains.memory",
            
            # Tools (moved to domains)
            "ultimate_discord_intelligence_bot.tools.analysis": "domains.intelligence.analysis.tools",
            "ultimate_discord_intelligence_bot.tools.verification": "domains.intelligence.verification.tools",
            "ultimate_discord_intelligence_bot.tools.acquisition": "domains.ingestion.providers.tools",
            "ultimate_discord_intelligence_bot.tools.memory": "domains.memory.tools",
            
            # Observability
            "ultimate_discord_intelligence_bot.observability": "platform.observability",
            "ultimate_discord_intelligence_bot.obs": "platform.observability",
            
            # Memory (app layer)
            "ultimate_discord_intelligence_bot.memory": "domains.memory",
            
            # === Framework Consolidations ===
            # CrewAI
            "domains.orchestration.crewai.agents": "domains.orchestration.crewai.agents",
            "domains.orchestration.crewai.tasks": "domains.orchestration.crewai.tasks",
            "domains.orchestration.crewai.crew": "domains.orchestration.crewai.crew",
            
            # Qdrant
            "domains.memory.vector.qdrant": "domains.memory.vector.qdrant",
            
            # DSPy
            "platform.prompts.dspy": "platform.prompts.dspy",
            
            # LlamaIndex
            "platform.rag.llamaindex": "platform.rag.llamaindex",
            
            # Mem0
            "domains.memory.continual.mem0": "domains.memory.continual.mem0",
            
            # HippoRAG
            "domains.memory.continual.hipporag": "domains.memory.continual.hipporag",
            
            # === Preserved Modules ===
            "server": "server",
            "mcp_server": "mcp_server",
            "graphs": "graphs",
            "eval": "eval",
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


def rewrite_file(file_path: Path, dry_run: bool = False, backup: bool = True) -> tuple[bool, list[str]]:
    """Rewrite imports in a single file using AST.

    Args:
        file_path: Path to Python file to rewrite
        dry_run: If True, don't actually write changes
        backup: If True, create .bak backup file

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
            # Create backup if requested
            if backup:
                backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                backup_path.write_text(source, encoding="utf-8")
            
            file_path.write_text(new_source, encoding="utf-8")

        return True, rewriter.changes

    except SyntaxError as e:
        return False, [f"SYNTAX ERROR: {e}"]
    except Exception as e:
        return False, [f"ERROR: {e}"]


def main(target_dirs: list[Path], dry_run: bool = True, verbose: bool = False, backup: bool = True, pattern_filter: str | None = None):
    """Run migration across all Python files.

    Args:
        target_dirs: List of directories to process
        dry_run: If True, don't actually write changes
        verbose: If True, show all changes, not just summary
        backup: If True, create .bak backup files
        pattern_filter: Optional pattern to filter files (e.g., "core", "ai", "obs")
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

    # Filter files by pattern if specified
    if pattern_filter:
        files = [f for f in files if pattern_filter in str(f) or pattern_filter in f.read_text()]
    
    # Exclude backup files
    files = [f for f in files if not f.name.endswith(".bak")]

    total = len(files)
    modified = 0
    errors = 0

    print(f"Scanning {total} Python files in {len(target_dirs)} locations...")
    if pattern_filter:
        print(f"Pattern filter: {pattern_filter}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    if backup and not dry_run:
        print("Backup: Enabled (creating .bak files)")
    print()

    for i, file_path in enumerate(files, 1):
        changed, changes = rewrite_file(file_path, dry_run=dry_run, backup=backup)

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
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Don't create .bak backup files",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        help="Filter files by pattern (e.g., 'core', 'ai', 'obs')",
    )

    args = parser.parse_args()

    # If --execute is set, turn off dry_run
    dry_run = args.dry_run and not args.execute

    if not dry_run:
        print("⚠️  Executing import migration - files will be modified")
        # Auto-confirm when called from automation

    main(args.targets, dry_run=dry_run, verbose=args.verbose, backup=not args.no_backup, pattern_filter=args.pattern)
