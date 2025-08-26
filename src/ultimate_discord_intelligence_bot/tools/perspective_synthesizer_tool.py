"""Combine search results into a coherent perspective."""

from crewai_tools import BaseTool

from ..services import MemoryService, OpenRouterService, PromptEngine


class PerspectiveSynthesizerTool(BaseTool):
    name = "Perspective Synthesizer"
    description = "Merge multiple search backends into a unified summary"

    def __init__(
        self,
        router: OpenRouterService | None = None,
        prompt_engine: PromptEngine | None = None,
        memory: MemoryService | None = None,
    ) -> None:
        super().__init__()
        self.router = router or OpenRouterService()
        self.prompt_engine = prompt_engine or PromptEngine()
        self.memory = memory or MemoryService()

    def _run(self, *search_results) -> dict:
        combined = "\n".join(str(r) for r in search_results if r).strip()
        if not combined:
            return {"status": "success", "summary": ""}

        memories = [m["text"] for m in self.memory.retrieve(combined)]
        if memories:
            combined = combined + "\n" + "\n".join(memories)

        prompt = self.prompt_engine.generate(
            "Summarise the following information:\n{content}", {"content": combined}
        )
        routed = self.router.route(prompt, task_type="analysis")
        return {
            "status": "success",
            "summary": routed.get("response", combined),
            "model": routed.get("model"),
            "tokens": routed.get("tokens"),
        }

    def run(self, *args, **kwargs):  # pragma: no cover
        return self._run(*args, **kwargs)
