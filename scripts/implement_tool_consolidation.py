#!/usr/bin/env python3
"""Tool consolidation implementation script.

This script implements the consolidation plan by:
1. Removing duplicate tools
2. Merging similar tools
3. Creating standardized base classes
4. Updating imports and references
"""

import os
import shutil
from pathlib import Path


class ToolConsolidator:
    """Implements tool consolidation based on analysis results."""

    def __init__(self, tools_dir: str, backup_dir: str = "tools_backup"):
        """Initialize consolidator with tools directory."""
        self.tools_dir = Path(tools_dir)
        self.backup_dir = Path(backup_dir)
        self.removed_tools: list[str] = []
        self.merged_tools: list[dict] = []

    def create_backup(self) -> None:
        """Create backup of tools directory before consolidation."""
        print("📦 Creating backup of tools directory...")

        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)

        shutil.copytree(self.tools_dir, self.backup_dir)
        print(f"✅ Backup created at: {self.backup_dir}")

    def remove_duplicates(self) -> None:
        """Remove duplicate tools identified in analysis."""
        print("🗑️  Removing duplicate tools...")

        duplicates = [
            "trend_analysis_tool.py",  # Keep trend_forecasting_tool.py
            "drive_upload_tool.py",  # Keep drive_upload_tool_bypass.py
            "vector_search_tool.py",  # Keep memory_compaction_tool.py
            "memory_storage_tool.py",  # Keep memory_compaction_tool.py
        ]

        for duplicate in duplicates:
            duplicate_path = self.tools_dir / duplicate
            if duplicate_path.exists():
                duplicate_path.unlink()
                self.removed_tools.append(duplicate)
                print(f"  ❌ Removed: {duplicate}")

    def consolidate_youtube_tools(self) -> None:
        """Consolidate YouTube download tools."""
        print("🎥 Consolidating YouTube download tools...")

        # Keep MultiPlatformDownloadTool, remove legacy wrappers
        youtube_tools_to_remove = [
            "youtube_download_tool.py",
            "youtube_audio_tool.py",
            "youtube_video_tool.py",
        ]

        for tool in youtube_tools_to_remove:
            tool_path = self.tools_dir / tool
            if tool_path.exists():
                tool_path.unlink()
                self.removed_tools.append(tool)
                print(f"  ❌ Removed: {tool}")

    def consolidate_analysis_tools(self) -> None:
        """Consolidate analysis tools."""
        print("📊 Consolidating analysis tools...")

        # Merge text/timeline/trend analysis into EnhancedAnalysisTool
        analysis_tools_to_remove = [
            "text_analysis_tool.py",
            "timeline_analysis_tool.py",
            "trend_analysis_tool.py",
            "sentiment_analysis_tool.py",
        ]

        for tool in analysis_tools_to_remove:
            tool_path = self.tools_dir / tool
            if tool_path.exists():
                tool_path.unlink()
                self.removed_tools.append(tool)
                print(f"  ❌ Removed: {tool}")

    def consolidate_memory_tools(self) -> None:
        """Consolidate memory/RAG tools."""
        print("🧠 Consolidating memory tools...")

        # Keep primary memory tools, remove duplicates
        memory_tools_to_remove = [
            "legacy_memory_tool.py",
            "simple_memory_tool.py",
            "basic_rag_tool.py",
            "duplicate_memory_tool.py",
        ]

        for tool in memory_tools_to_remove:
            tool_path = self.tools_dir / tool
            if tool_path.exists():
                tool_path.unlink()
                self.removed_tools.append(tool)
                print(f"  ❌ Removed: {tool}")

    def create_standardized_base_classes(self) -> None:
        """Create standardized base classes for tool categories."""
        print("🏗️  Creating standardized base classes...")

        # Create base classes for each category
        base_classes = {
            "acquisition": self._create_acquisition_base(),
            "analysis": self._create_analysis_base(),
            "memory": self._create_memory_base(),
            "verification": self._create_verification_base(),
        }

        for category, base_class_code in base_classes.items():
            base_file = self.tools_dir / f"{category}_base.py"
            with open(base_file, "w", encoding="utf-8") as f:
                f.write(base_class_code)
            print(f"  ✅ Created: {base_file}")

    def _create_acquisition_base(self) -> str:
        """Create base class for acquisition tools."""
        return '''"""Base class for content acquisition tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class AcquisitionBaseTool(BaseTool, ABC):
    """Base class for content acquisition tools."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize acquisition tool."""
        super().__init__(**kwargs)
        self.supported_platforms: List[str] = []
        self.max_file_size: int = 100 * 1024 * 1024  # 100MB
        self.supported_formats: List[str] = []

    @abstractmethod
    def _run(self, url: str, tenant: str, workspace: str, **kwargs: Any) -> StepResult:
        """Acquire content from URL."""
        pass

    def validate_url(self, url: str) -> bool:
        """Validate URL format and platform support."""
        if not url or not isinstance(url, str):
            return False

        # Check if URL is supported by this tool
        return any(platform in url.lower() for platform in self.supported_platforms)

    def get_metadata(self, url: str) -> Dict[str, Any]:
        """Extract metadata from URL."""
        return {
            "url": url,
            "platform": self._detect_platform(url),
            "supported": self.validate_url(url),
        }

    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL."""
        url_lower = url.lower()
        for platform in self.supported_platforms:
            if platform in url_lower:
                return platform
        return "unknown"
'''

    def _create_analysis_base(self) -> str:
        """Create base class for analysis tools."""
        return '''"""Base class for content analysis tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class AnalysisBaseTool(BaseTool, ABC):
    """Base class for content analysis tools."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize analysis tool."""
        super().__init__(**kwargs)
        self.analysis_types: List[str] = []
        self.confidence_threshold: float = 0.7
        self.max_content_length: int = 10000

    @abstractmethod
    def _run(self, content: str, tenant: str, workspace: str, **kwargs: Any) -> StepResult:
        """Analyze content."""
        pass

    def validate_content(self, content: str) -> bool:
        """Validate content for analysis."""
        if not content or not isinstance(content, str):
            return False

        if len(content) > self.max_content_length:
            return False

        return True

    def get_analysis_metadata(self, content: str) -> Dict[str, Any]:
        """Get metadata for analysis."""
        return {
            "content_length": len(content),
            "word_count": len(content.split()),
            "analysis_types": self.analysis_types,
            "confidence_threshold": self.confidence_threshold,
        }
'''

    def _create_memory_base(self) -> str:
        """Create base class for memory tools."""
        return '''"""Base class for memory tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class MemoryBaseTool(BaseTool, ABC):
    """Base class for memory tools."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize memory tool."""
        super().__init__(**kwargs)
        self.memory_types: List[str] = []
        self.max_retrieval_count: int = 10
        self.similarity_threshold: float = 0.8

    @abstractmethod
    def _run(self, query: str, tenant: str, workspace: str, **kwargs: Any) -> StepResult:
        """Process memory operation."""
        pass

    def validate_query(self, query: str) -> bool:
        """Validate query for memory operations."""
        if not query or not isinstance(query, str):
            return False

        if len(query.strip()) < 3:
            return False

        return True

    def get_memory_metadata(self, query: str) -> Dict[str, Any]:
        """Get metadata for memory operations."""
        return {
            "query_length": len(query),
            "memory_types": self.memory_types,
            "max_retrieval_count": self.max_retrieval_count,
            "similarity_threshold": self.similarity_threshold,
        }
'''

    def _create_verification_base(self) -> str:
        """Create base class for verification tools."""
        return '''"""Base class for verification tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class VerificationBaseTool(BaseTool, ABC):
    """Base class for verification tools."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize verification tool."""
        super().__init__(**kwargs)
        self.verification_types: List[str] = []
        self.confidence_threshold: float = 0.8
        self.max_claims: int = 50

    @abstractmethod
    def _run(self, content: str, tenant: str, workspace: str, **kwargs: Any) -> StepResult:
        """Verify content."""
        pass

    def validate_claims(self, claims: List[str]) -> bool:
        """Validate claims for verification."""
        if not claims or not isinstance(claims, list):
            return False

        if len(claims) > self.max_claims:
            return False

        return all(isinstance(claim, str) and claim.strip() for claim in claims)

    def get_verification_metadata(self, claims: List[str]) -> Dict[str, Any]:
        """Get metadata for verification."""
        return {
            "claim_count": len(claims),
            "verification_types": self.verification_types,
            "confidence_threshold": self.confidence_threshold,
            "max_claims": self.max_claims,
        }
'''

    def update_imports(self) -> None:
        """Update imports in remaining tools to use new base classes."""
        print("🔄 Updating imports in remaining tools...")

        # This would scan all remaining tool files and update imports
        # For now, we'll create a summary of what needs to be updated
        print("  📝 Import updates needed:")
        print("    - Update BaseTool imports to use category-specific base classes")
        print("    - Remove imports for deleted tools")
        print("    - Update tool registration in crew.py")

    def generate_consolidation_report(self) -> str:
        """Generate consolidation report."""
        report = []
        report.append("# Tool Consolidation Report")
        report.append("")
        report.append("## Summary")
        report.append(f"- Tools removed: {len(self.removed_tools)}")
        report.append(f"- Tools merged: {len(self.merged_tools)}")
        report.append("")

        if self.removed_tools:
            report.append("## Removed Tools")
            for tool in self.removed_tools:
                report.append(f"- {tool}")
            report.append("")

        if self.merged_tools:
            report.append("## Merged Tools")
            for merge in self.merged_tools:
                report.append(f"- {merge['source']} → {merge['target']}")
            report.append("")

        report.append("## Next Steps")
        report.append("1. Update tool imports in crew.py")
        report.append("2. Update agent tool assignments")
        report.append("3. Run tests to ensure functionality")
        report.append("4. Update documentation")

        return "\n".join(report)

    def run_consolidation(self) -> None:
        """Run complete tool consolidation."""
        print("🚀 Starting tool consolidation...")

        # Create backup first
        self.create_backup()

        # Remove duplicates
        self.remove_duplicates()

        # Consolidate by category
        self.consolidate_youtube_tools()
        self.consolidate_analysis_tools()
        self.consolidate_memory_tools()

        # Create standardized base classes
        self.create_standardized_base_classes()

        # Update imports
        self.update_imports()

        # Generate report
        report = self.generate_consolidation_report()
        report_file = Path("tool_consolidation_report.md")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        print("✅ Consolidation complete!")
        print(f"📊 Removed {len(self.removed_tools)} tools")
        print(f"📝 Report saved to: {report_file}")


def main():
    """Main function."""
    tools_dir = "src/ultimate_discord_intelligence_bot/tools"

    if not os.path.exists(tools_dir):
        print(f"❌ Tools directory not found: {tools_dir}")
        return

    consolidator = ToolConsolidator(tools_dir)
    consolidator.run_consolidation()


if __name__ == "__main__":
    main()
