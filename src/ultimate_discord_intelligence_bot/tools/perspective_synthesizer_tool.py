"""Combine search results into a coherent perspective."""

from crewai_tools import BaseTool


class PerspectiveSynthesizerTool(BaseTool):
    name = "Perspective Synthesizer"
    description = "Merge multiple search backends into a unified summary"

    def _run(self, *search_results) -> dict:
        combined = "\n".join(str(r) for r in search_results if r)
        return {"status": "success", "summary": combined.strip()}

    def run(self, *args, **kwargs):  # pragma: no cover
        return self._run(*args, **kwargs)

