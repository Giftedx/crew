from __future__ import annotations

from ingest.providers import twitch, youtube


def test_youtube_empty_fields(monkeypatch):
    monkeypatch.setattr(
        youtube,
        "youtube_fetch_metadata",
        lambda url: {"id": "", "title": "", "channel": "", "url": ""},
    )
    m = youtube.fetch_metadata("https://example.com/v")
    # provider should not invent values; empty strings preserved
    assert m.id == ""
    assert m.title == ""
    assert m.channel == ""
    # url falls back to input when upstream empty
    assert m.url == "https://example.com/v"


def test_twitch_empty_fields(monkeypatch):
    monkeypatch.setattr(
        twitch,
        "twitch_fetch_metadata",
        lambda url: {"id": "", "title": "", "streamer": "", "url": ""},
    )
    m = twitch.fetch_metadata("https://example.com/c")
    assert m.id == ""
    assert m.title == ""
    assert m.streamer == ""
    assert m.url == "https://example.com/c"
