from __future__ import annotations

from ingest.providers import twitch, youtube


def test_provider_thumbnails_and_duration_edges(monkeypatch):
    # YouTube: mixed thumbnails and tricky durations
    monkeypatch.setattr(
        youtube,
        "youtube_fetch_metadata",
        lambda url: {
            "id": "yt",
            "title": "t",
            "channel": "c",
            "url": url,
            "duration": "NaN",
            "thumbnails": [None, 0, "ok"],
        },
    )
    m = youtube.fetch_metadata("u")
    assert m.duration is None
    assert m.thumbnails == ["", "0", "ok"]

    # Twitch: empty and non-numeric duration
    monkeypatch.setattr(
        twitch,
        "twitch_fetch_metadata",
        lambda url: {
            "id": "tw",
            "title": "t",
            "streamer": "s",
            "url": url,
            "duration": "abc",
        },
    )
    mt = twitch.fetch_metadata("v")
    assert mt.duration is None
