"""Compose the strongest supportive argument for a claim."""

from __future__ import annotations

from crewai.tools import BaseTool


class SteelmanArgumentTool(BaseTool):
    """Combine evidence snippets into a steelman argument."""

    name: str = "Steelman Argument Tool"
    description: str = "Build the strongest possible version of a claim using supporting snippets"

    def _run(self, claim: str, evidence: list[dict[str, str]]) -> dict[str, str]:
        """Craft a steelman argument.

        Parameters
        ----------
        claim:
            The statement to strengthen.
        evidence:
            Sequence of dicts containing at least a ``snippet`` field with
            supportive text and optional ``source`` metadata.
        """

        snippets: list[str] = []
        for item in evidence:
            snippet = item.get("snippet")
            if snippet:
                source = item.get("source")
                if source:
                    snippets.append(f"[{source}] {snippet}")
                else:
                    snippets.append(snippet)
        if not snippets:
            return {
                "status": "uncertain",
                "argument": claim,
                "notes": "no supporting evidence provided",
            }
        argument = f"{claim}. " + " ".join(snippets)
        return {"status": "success", "argument": argument}

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
