import importlib
import sys

import pytest


def test_requires_nltk(monkeypatch):
    # Ensure module sees missing nltk dependency
    monkeypatch.delitem(sys.modules, "ultimate_discord_intelligence_bot.tools.text_analysis_tool", raising=False)
    monkeypatch.setitem(sys.modules, "nltk", None)

    mod = importlib.import_module("ultimate_discord_intelligence_bot.tools.text_analysis_tool")
    with pytest.raises(RuntimeError):
        mod.TextAnalysisTool()
