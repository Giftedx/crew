from ultimate_discord_intelligence_bot.tools import PromptCompressionTool


def test_compression_reduces_tokens():
    tool = PromptCompressionTool()
    long_context = ["This is a very long context..."] * 100
    result = tool.run(long_context, target_token=500)

    assert result.success
    assert result.data["compressed_tokens"] < result.data["origin_tokens"]
    assert result.data["tokens_saved"] > 0


def test_compression_skipped_when_disabled(monkeypatch):
    monkeypatch.setenv("ENABLE_PROMPT_COMPRESSION", "0")
    tool = PromptCompressionTool()
    result = tool.run(["context"])

    assert result.custom_status == "skipped"
