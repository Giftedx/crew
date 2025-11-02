from analysis import segmenter, transcribe
from obs import metrics


class DummySettings:
    enable_token_aware_chunker = True
    token_chunk_target_tokens = 20  # small target -> derived max_chars=80


def _make_transcript(num_segments: int, seg_len: int = 50) -> transcribe.Transcript:
    segs = []
    # produce deterministic text lengths
    base = "x" * seg_len
    for i in range(num_segments):
        segs.append(transcribe.Segment(start=float(i), end=float(i + 1), text=f"{base}{i}"))
    return transcribe.Transcript(segments=segs)


def test_token_aware_chunking_flushes(monkeypatch):
    # Reset metrics for a clean slate
    metrics.reset()
    from analysis import segmenter as segmenter_mod
    from core import settings as settings_mod

    # Patch both the source settings module and the already-imported reference inside segmenter
    monkeypatch.setattr(settings_mod, "get_settings", lambda: DummySettings())
    monkeypatch.setattr(segmenter_mod, "get_settings", lambda: DummySettings())

    # With heuristic 0.25 tokens per char -> max_chars ~= 160 for 40 tokens target
    # We'll build 10 segments of ~51 chars each -> flushes expected.
    # Build segments sized so cumulative tokens exceed target mid-way: seg_len=20 -> ~5 tokens per seg.
    # After 7 segments (~35 tokens) a flush should occur.
    tx = _make_transcript(15, seg_len=20)
    chunks = segmenter.chunk_transcript(tx, max_chars=800, overlap=0)  # overridden by token-aware

    assert len(chunks) >= 2, "Expected at least one flush producing multiple chunks"

    # Validate metrics recorded: chars + tokens histograms should have at least len(chunks) observations
    # We can't easily introspect histogram buckets without prometheus_client, but generate_latest() should include names.
    rendered = metrics.render().decode("utf-8") if metrics.PROMETHEUS_AVAILABLE else ""
    # Check metric identifiers appear
    assert "segment_chunk_size_chars" in rendered or not metrics.PROMETHEUS_AVAILABLE
    assert "segment_chunk_size_tokens" in rendered or not metrics.PROMETHEUS_AVAILABLE

    # Ensure first chunk respects target constraint (allow slight overshoot since condition triggers when > target)
    approx_tokens_per_char = 0.25
    first_chunk_tokens = int(len(chunks[0].text) * approx_tokens_per_char)
    assert first_chunk_tokens <= int(DummySettings.token_chunk_target_tokens * 1.10)


def test_segment_chunk_merges_counter(monkeypatch):
    metrics.reset()
    from analysis import segmenter as segmenter_mod
    from core import settings as settings_mod

    monkeypatch.setattr(settings_mod, "get_settings", lambda: DummySettings())
    monkeypatch.setattr(segmenter_mod, "get_settings", lambda: DummySettings())

    tx = _make_transcript(12, seg_len=60)
    chunks = segmenter.chunk_transcript(tx, max_chars=800)
    assert len(chunks) > 1
    # Merges counter increments only when flush happened
    rendered = metrics.render().decode("utf-8") if metrics.PROMETHEUS_AVAILABLE else ""
    assert "segment_chunk_merges_total" in rendered or not metrics.PROMETHEUS_AVAILABLE
