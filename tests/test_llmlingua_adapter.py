import importlib
import sys
import types


def _reload_adapter():
    # Ensure a fresh import of the adapter to reset internal module state
    if "prompt_engine.llmlingua_adapter" in sys.modules:
        importlib.reload(sys.modules["prompt_engine.llmlingua_adapter"])  # type: ignore[call-arg]
    else:
        importlib.import_module("prompt_engine.llmlingua_adapter")
    return sys.modules["prompt_engine.llmlingua_adapter"]


def test_adapter_returns_original_when_flag_disabled(monkeypatch):
    # Ensure flag is disabled
    monkeypatch.delenv("ENABLE_PROMPT_COMPRESSION", raising=False)
    adapter = _reload_adapter()
    out = adapter.maybe_compress_prompt("Hello World")
    assert out == "Hello World"


def test_adapter_returns_original_when_dependency_missing(monkeypatch):
    # Enable flag but simulate missing llmlingua or missing attribute
    monkeypatch.setenv("ENABLE_PROMPT_COMPRESSION", "1")

    # Provide a dummy 'llmlingua' module without PromptCompressor to force ImportError
    dummy = types.ModuleType("llmlingua")
    sys.modules["llmlingua"] = dummy

    adapter = _reload_adapter()
    out = adapter.maybe_compress_prompt("Sample text")
    assert out == "Sample text"


def test_adapter_handles_compressor_runtime_error(monkeypatch):
    # Enable flag and provide a stub compressor that raises on compress_prompt
    monkeypatch.setenv("ENABLE_PROMPT_COMPRESSION", "1")

    class _BadCompressor:
        def compress_prompt(self, *a, **k):  # noqa: D401 - stub raising
            raise RuntimeError("boom")

    # Create a stub llmlingua module exposing PromptCompressor
    stub = types.ModuleType("llmlingua")
    stub.PromptCompressor = _BadCompressor  # type: ignore[attr-defined]
    sys.modules["llmlingua"] = stub

    adapter = _reload_adapter()
    out = adapter.maybe_compress_prompt("Keep original on error")
    assert out == "Keep original on error"


def test_adapter_uses_stubbed_compressor_when_available(monkeypatch):
    # Enable flag and provide a compressor that returns a compressed prompt
    monkeypatch.setenv("ENABLE_PROMPT_COMPRESSION", "1")

    class _GoodCompressor:
        def compress_prompt(self, prompt, *a, **k):  # noqa: D401 - stub success
            return {"compressed_prompt": "COMPRESSED:" + str(prompt)[:10]}

    stub = types.ModuleType("llmlingua")
    stub.PromptCompressor = _GoodCompressor  # type: ignore[attr-defined]
    sys.modules["llmlingua"] = stub

    adapter = _reload_adapter()
    out = adapter.maybe_compress_prompt("abcdefghijklmno")
    assert out.startswith("COMPRESSED:")


def test_adapter_truthy_env_values(monkeypatch):
    # Use an alternate truthy value for the env to ensure it's recognized
    monkeypatch.setenv("ENABLE_PROMPT_COMPRESSION", "true")

    class _GoodCompressor:
        def compress_prompt(self, prompt, *a, **k):  # noqa: D401 - stub success
            return {"compressed_prompt": "OK:" + str(prompt)[:5]}

    import sys
    import types

    stub = types.ModuleType("llmlingua")
    stub.PromptCompressor = _GoodCompressor  # type: ignore[attr-defined]
    sys.modules["llmlingua"] = stub

    adapter = _reload_adapter()
    out = adapter.maybe_compress_prompt("abcdefghijklmno")
    assert out.startswith("OK:")
