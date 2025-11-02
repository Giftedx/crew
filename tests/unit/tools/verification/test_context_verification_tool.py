from ultimate_discord_intelligence_bot.tools.context_verification_tool import (
    ContextVerificationTool,
)
from ultimate_discord_intelligence_bot.tools.transcript_index_tool import (
    TranscriptIndexTool,
)


def test_verify_clip_context():
    idx = TranscriptIndexTool(window=30.0)
    idx.index_transcript("line1\nline2", "vid")
    tool = ContextVerificationTool(index_tool=idx)
    res = tool.run(video_id="vid", ts=15, clip_text="line1")
    assert res["verdict"] == "in-context"
    res2 = tool.run(video_id="vid", ts=15, clip_text="other")
    assert res2["verdict"] == "missing-context"
