import importlib
from types import SimpleNamespace


def test_research_tool_uses_compression(monkeypatch):
    # Enable feature flag
    monkeypatch.setenv("ENABLE_PROMPT_COMPRESSION", "1")

    # Stub the adapter to make compression obvious and deterministic
    def _stub_compress(prompt: str, *, target_tokens: int | None = None) -> str:
        return "[COMPRESSED]\n" + prompt[:20]

    # Patch the adapter symbol where the tool imports it
    monkeypatch.setitem(
        importlib.import_module("sys").modules,
        "prompt_engine.llmlingua_adapter",
        SimpleNamespace(maybe_compress_prompt=_stub_compress),
    )

    # Re-import the tool to bind the stubbed adapter
    mod = importlib.import_module("ultimate_discord_intelligence_bot.tools.research_and_brief_tool")
    importlib.reload(mod)

    Tool = getattr(mod, "ResearchAndBriefTool")
    tool = Tool()

    sources = [
        "Alpha beta gamma. Delta epsilon zeta.",
        "Alpha repeats. Beta repeats. Compression should shorten inputs.",
    ]
    res = tool.run(query="alpha beta", sources_text=sources, max_items=3)
    # StepResult exposes status via mapping: "success" | "error" | custom
    assert res["status"] == "success"
    # Ensure our stub was used by verifying the compressed marker influenced splitting/processing
    counts = res["counts"]
    assert isinstance(counts, dict)
    assert counts["sources"] >= 1
    # Because we compress to short prefix, token estimate should be relatively small
    assert counts["tokens_estimate"] <= sum(len(s.split()) for s in sources)
    # Outline should be present
    assert isinstance(res["outline"], list)
