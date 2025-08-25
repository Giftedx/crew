"""Detect basic logical fallacies in text.

Currently a lightweight placeholder that scans for a small set of common
fallacy indicators. This provides a foundation for future, more advanced
reasoning modules.
"""

from crewai_tools import BaseTool


class LogicalFallacyTool(BaseTool):
    name = "Logical Fallacy Detector"
    description = "Identify simple logical fallacies in statements"

    FALLACIES = {
        "ad hominem": ["ad hominem"],
        "appeal to authority": ["appeal to authority", "because i said so"],
        "bandwagon": ["everyone knows", "bandwagon"],
        "circular reasoning": ["circular reasoning", "because because"],
        "false dilemma": ["either", "neither"],
        "red herring": ["red herring"],
        "slippery slope": ["slippery slope", "inevitably"],
        "straw man": ["straw man"],
    }

    def _run(self, text: str) -> dict:
        findings = []
        lower = text.lower()
        for fallacy, keywords in self.FALLACIES.items():
            if any(k in lower for k in keywords):
                findings.append(fallacy)
        return {"status": "success", "fallacies": findings}

    def run(self, *args, **kwargs):  # pragma: no cover
        return self._run(*args, **kwargs)

