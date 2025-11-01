#!/usr/bin/env python3
"""Documentation organization script for the Ultimate Discord Intelligence Bot.

This script analyzes the documentation structure, identifies stale content,
and reorganizes documentation to reduce file count from 180+ to <100.
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path


class DocumentationOrganizer:
    """Organizes and consolidates documentation."""

    def __init__(self, docs_dir: str, archive_dir: str = "docs/archive"):
        """Initialize organizer with docs directory."""
        self.docs_dir = Path(docs_dir)
        self.archive_dir = Path(archive_dir)
        self.consolidated_files: list[str] = []
        self.archived_files: list[str] = []
        self.duplicate_files: list[tuple[str, str]] = []

    def analyze_documentation(self) -> dict[str, any]:
        """Analyze current documentation structure."""
        print("🔍 Analyzing documentation structure...")

        analysis = {
            "total_files": 0,
            "root_files": 0,
            "subdirectory_files": 0,
            "stale_files": [],
            "duplicate_content": [],
            "large_files": [],
            "recent_files": [],
            "categories": {},
        }

        # Count files
        for md_file in self.docs_dir.rglob("*.md"):
            analysis["total_files"] += 1

            if md_file.parent == self.docs_dir:
                analysis["root_files"] += 1
            else:
                analysis["subdirectory_files"] += 1

            # Check file size
            file_size = md_file.stat().st_size
            if file_size > 50000:  # 50KB
                analysis["large_files"].append(str(md_file))

            # Check modification time
            mod_time = datetime.fromtimestamp(md_file.stat().st_mtime)
            if mod_time > datetime.now() - timedelta(days=30):
                analysis["recent_files"].append(str(md_file))
            elif mod_time < datetime.now() - timedelta(days=365):
                analysis["stale_files"].append(str(md_file))

            # Categorize by directory
            category = str(md_file.parent.relative_to(self.docs_dir))
            if category == ".":
                category = "root"

            if category not in analysis["categories"]:
                analysis["categories"][category] = 0
            analysis["categories"][category] += 1

        return analysis

    def identify_consolidation_opportunities(self) -> list[dict[str, str]]:
        """Identify files that can be consolidated."""
        print("🎯 Identifying consolidation opportunities...")

        opportunities = []

        # Group similar files by name patterns
        name_groups = {}
        for md_file in self.docs_dir.rglob("*.md"):
            base_name = md_file.stem.lower()

            # Extract common patterns
            if "test" in base_name and "report" in base_name:
                group_key = "test_reports"
            elif "phase" in base_name and ("report" in base_name or "summary" in base_name):
                group_key = "phase_reports"
            elif "performance" in base_name:
                group_key = "performance_docs"
            elif "setup" in base_name or "installation" in base_name:
                group_key = "setup_docs"
            elif "guide" in base_name or "tutorial" in base_name:
                group_key = "guides"
            else:
                continue

            if group_key not in name_groups:
                name_groups[group_key] = []
            name_groups[group_key].append(str(md_file))

        # Create consolidation opportunities
        for group_key, files in name_groups.items():
            if len(files) > 2:  # Only consolidate if 3+ files
                target_file = f"docs/{group_key}.md"
                opportunities.append(
                    {
                        "target": target_file,
                        "source_files": files,
                        "reason": f"Consolidate {len(files)} {group_key} files",
                    }
                )

        return opportunities

    def identify_stale_content(self) -> list[str]:
        """Identify stale documentation files."""
        print("📅 Identifying stale content...")

        stale_files = []
        cutoff_date = datetime.now() - timedelta(days=180)  # 6 months

        for md_file in self.docs_dir.rglob("*.md"):
            mod_time = datetime.fromtimestamp(md_file.stat().st_mtime)

            if mod_time < cutoff_date and not self._has_recent_references(md_file):
                # File is stale with no recent references
                stale_files.append(str(md_file))

        return stale_files

    def _has_recent_references(self, file_path: Path) -> bool:
        """Check if a file has recent references in other files."""
        file_name = file_path.name

        # Check for references in other markdown files
        for other_file in self.docs_dir.rglob("*.md"):
            if other_file == file_path:
                continue

            try:
                with open(other_file, encoding="utf-8") as f:
                    content = f.read()
                    if file_name in content or file_path.stem in content:
                        return True
            except Exception:
                continue

        return False

    def create_archive_structure(self) -> None:
        """Create archive directory structure."""
        print("📁 Creating archive structure...")

        archive_categories = ["stale_reports", "old_guides", "deprecated_features", "test_reports", "phase_reports"]

        for category in archive_categories:
            category_dir = self.archive_dir / category
            category_dir.mkdir(parents=True, exist_ok=True)

    def consolidate_similar_files(self, opportunities: list[dict[str, str]]) -> None:
        """Consolidate similar files into single documents."""
        print("📝 Consolidating similar files...")

        for opportunity in opportunities:
            target_file = Path(opportunity["target"])
            source_files = [Path(f) for f in opportunity["source_files"]]

            # Create consolidated content
            consolidated_content = []
            consolidated_content.append(f"# {target_file.stem.replace('_', ' ').title()}")
            consolidated_content.append("")
            consolidated_content.append("*This document consolidates multiple related files for better organization.*")
            consolidated_content.append("")

            for source_file in source_files:
                try:
                    with open(source_file, encoding="utf-8") as f:
                        content = f.read()

                    # Add section header
                    consolidated_content.append(f"## {source_file.stem.replace('_', ' ').title()}")
                    consolidated_content.append("")
                    consolidated_content.append(content)
                    consolidated_content.append("")
                    consolidated_content.append("---")
                    consolidated_content.append("")

                except Exception as e:
                    print(f"⚠️  Error reading {source_file}: {e}")

            # Write consolidated file
            try:
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(consolidated_content))

                # Archive original files
                for source_file in source_files:
                    archive_path = self.archive_dir / "consolidated" / source_file.name
                    archive_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source_file), str(archive_path))
                    self.archived_files.append(str(source_file))

                self.consolidated_files.append(str(target_file))
                print(f"  ✅ Consolidated {len(source_files)} files into {target_file}")

            except Exception as e:
                print(f"  ❌ Error consolidating {target_file}: {e}")

    def archive_stale_content(self, stale_files: list[str]) -> None:
        """Archive stale documentation files."""
        print("📦 Archiving stale content...")

        for stale_file in stale_files:
            try:
                file_path = Path(stale_file)
                archive_path = self.archive_dir / "stale" / file_path.name
                archive_path.parent.mkdir(parents=True, exist_ok=True)

                shutil.move(stale_file, str(archive_path))
                self.archived_files.append(stale_file)
                print(f"  📦 Archived: {file_path.name}")

            except Exception as e:
                print(f"  ❌ Error archiving {stale_file}: {e}")

    def create_documentation_index(self) -> None:
        """Create a comprehensive documentation index."""
        print("📚 Creating documentation index...")

        index_content = []
        index_content.append("# Ultimate Discord Intelligence Bot - Documentation Index")
        index_content.append("")
        index_content.append("*Comprehensive guide to all documentation in this repository.*")
        index_content.append("")

        # Core documentation
        index_content.append("## Core Documentation")
        index_content.append("")
        index_content.append("- [README](README.md) - Project overview and quick start")
        index_content.append("- [Configuration](configuration.md) - Configuration reference")
        index_content.append("- [Tools Reference](tools_reference.md) - Complete tools documentation")
        index_content.append("- [Agent Reference](agent_reference.md) - Agent documentation")
        index_content.append("")

        # Architecture
        index_content.append("## Architecture & Design")
        index_content.append("")
        index_content.append("- [System Architecture](architecture/) - System design documents")
        index_content.append("- [Pipeline Design](pipeline.md) - Content processing pipeline")
        index_content.append("- [Memory Systems](memory.md) - Vector storage and memory")
        index_content.append("")

        # Development
        index_content.append("## Development")
        index_content.append("")
        index_content.append("- [Getting Started](getting_started.md) - Development setup")
        index_content.append("- [Testing Guide](testing/) - Testing documentation")
        index_content.append("- [Deployment Guide](deployment/) - Production deployment")
        index_content.append("")

        # Operations
        index_content.append("## Operations")
        index_content.append("")
        index_content.append("- [Monitoring](observability.md) - System monitoring")
        index_content.append("- [Performance](performance/) - Performance optimization")
        index_content.append("- [Security](security/) - Security documentation")
        index_content.append("")

        # Write index file
        index_file = self.docs_dir / "INDEX.md"
        with open(index_file, "w", encoding="utf-8") as f:
            f.write("\n".join(index_content))

        print(f"  ✅ Created documentation index: {index_file}")

    def generate_organization_report(self) -> str:
        """Generate organization report."""
        report = []
        report.append("# Documentation Organization Report")
        report.append("")
        report.append("## Summary")
        report.append(f"- Files consolidated: {len(self.consolidated_files)}")
        report.append(f"- Files archived: {len(self.archived_files)}")
        report.append(f"- Duplicates found: {len(self.duplicate_files)}")
        report.append("")

        if self.consolidated_files:
            report.append("## Consolidated Files")
            for file in self.consolidated_files:
                report.append(f"- {file}")
            report.append("")

        if self.archived_files:
            report.append("## Archived Files")
            for file in self.archived_files:
                report.append(f"- {file}")
            report.append("")

        report.append("## Next Steps")
        report.append("1. Review consolidated files for accuracy")
        report.append("2. Update internal links to point to new locations")
        report.append("3. Update README.md to reference INDEX.md")
        report.append("4. Remove archived files after verification")

        return "\n".join(report)

    def run_organization(self) -> None:
        """Run complete documentation organization."""
        print("🚀 Starting documentation organization...")

        # Analyze current state
        analysis = self.analyze_documentation()
        print(f"📊 Found {analysis['total_files']} documentation files")
        print(f"📁 Root files: {analysis['root_files']}")
        print(f"📁 Subdirectory files: {analysis['subdirectory_files']}")
        print(f"📅 Stale files: {len(analysis['stale_files'])}")

        # Create archive structure
        self.create_archive_structure()

        # Identify consolidation opportunities
        opportunities = self.identify_consolidation_opportunities()
        print(f"🎯 Found {len(opportunities)} consolidation opportunities")

        # Identify stale content
        stale_files = self.identify_stale_content()
        print(f"📅 Found {len(stale_files)} stale files")

        # Consolidate similar files
        if opportunities:
            self.consolidate_similar_files(opportunities)

        # Archive stale content
        if stale_files:
            self.archive_stale_content(stale_files)

        # Create documentation index
        self.create_documentation_index()

        # Generate report
        report = self.generate_organization_report()
        report_file = Path("documentation_organization_report.md")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        print("✅ Documentation organization complete!")
        print(f"📊 Consolidated {len(self.consolidated_files)} files")
        print(f"📦 Archived {len(self.archived_files)} files")
        print(f"📝 Report saved to: {report_file}")


def main():
    """Main function."""
    docs_dir = "docs"

    if not os.path.exists(docs_dir):
        print(f"❌ Documentation directory not found: {docs_dir}")
        return

    organizer = DocumentationOrganizer(docs_dir)
    organizer.run_organization()


if __name__ == "__main__":
    main()
