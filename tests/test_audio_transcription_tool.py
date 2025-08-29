import importlib
import sys


def test_missing_whisper_returns_error(monkeypatch, tmp_path):
    # Remove existing module so import uses patched sys.modules entry
    monkeypatch.delitem(
        sys.modules,
        "ultimate_discord_intelligence_bot.tools.audio_transcription_tool",
        raising=False,
    )
    monkeypatch.setitem(sys.modules, "whisper", None)

    mod = importlib.import_module(
        "ultimate_discord_intelligence_bot.tools.audio_transcription_tool"
    )
    tool = mod.AudioTranscriptionTool()

    video = tmp_path / "sample.mp4"
    video.write_text("dummy")

    result = tool.run(str(video))
    assert result["status"] == "error"
    assert "whisper" in result["error"].lower()
