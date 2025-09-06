from __future__ import annotations

from ingest.providers import twitch, youtube


def test_youtube_fetch_metadata_malformed(monkeypatch):
    monkeypatch.setattr(
        youtube, "youtube_fetch_metadata", lambda url: {
            "id": 123,
            "title": None,
            "channel": None,
            "published_at": 1,
            "duration": "10",
            "url": None,
            "thumbnails": [1, "t2"],
        }
    )
    meta = youtube.fetch_metadata("u")
    assert meta.id == "123"
    assert meta.title == ""
    assert meta.channel == ""
    assert meta.url == "u"  # fallback
    assert meta.thumbnails == ["1", "t2"]
    assert isinstance(meta.duration, int | float) and float(meta.duration) == 10.0


def test_twitch_fetch_metadata_malformed(monkeypatch):
    monkeypatch.setattr(
        twitch, "twitch_fetch_metadata", lambda url: {
            "id": None,
            "title": 42,
            "streamer": None,
            "published_at": 0,
            "duration": None,
            "url": None,
        }
    )
    meta = twitch.fetch_metadata("v")
    assert meta.id == ""
    assert meta.title == "42"
    assert meta.streamer == ""
    assert meta.url == "v"
    assert meta.duration is None
