from ultimate_discord_intelligence_bot.tools.transcript_index_tool import TranscriptIndexTool


def test_index_and_get_context():
    tool = TranscriptIndexTool(window=30.0)
    transcript = "hello\nworld\nfoo"
    res = tool.index_transcript(transcript, "vid1")
    assert res["status"] == "success" and res["chunks"] == 3
    ctx = tool.get_context("vid1", ts=35)
    assert "world" in ctx
