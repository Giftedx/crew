from ultimate_discord_intelligence_bot.cache import TranscriptCache


def test_transcript_cache_store_and_load(tmp_path):
    cache = TranscriptCache(root=tmp_path, enabled=True)

    cache.store("video123", "whisper-base", "hello world", [{"start": 0.0, "end": 1.0, "text": "hello"}])

    cached = cache.load("video123", "whisper-base")
    assert cached is not None
    assert cached["transcript"] == "hello world"
    assert cached["video_id"] == "video123"
    assert cached["model"] == "whisper-base"
    assert cached["segments"][0]["text"] == "hello"
    assert cached["cached_at"] is not None


def test_transcript_cache_disabled_noop(tmp_path):
    cache = TranscriptCache(root=tmp_path, enabled=False)

    cache.store("video123", "whisper-base", "hello", [])
    assert cache.load("video123", "whisper-base") is None
    assert not any(tmp_path.iterdir())
