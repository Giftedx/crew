from ultimate_discord_intelligence_bot.profiles.schema import (
    CreatorProfile,
    Platforms,
    load_seeds,
)
from ultimate_discord_intelligence_bot.profiles.store import ProfileStore
from ultimate_discord_intelligence_bot.tools.platform_resolver import (
    resolve_twitch_login,
    resolve_youtube_handle,
)


def test_load_seeds_and_store_roundtrip(tmp_path):
    seeds = load_seeds("profiles.yaml")
    assert seeds, "seed profiles should load"
    first = seeds[0]
    assert first.name == "H3H3 Productions"

    # Use resolver to build canonical profile
    yt_channel = resolve_youtube_handle(first.seed_handles["youtube"][0])
    profile = CreatorProfile(
        name=first.name,
        type=first.type,
        roles=first.roles,
        shows=first.shows,
        content_tags=first.content_tags,
        platforms=Platforms(youtube=[yt_channel]),
    )

    store = ProfileStore(tmp_path / "profiles.db")
    store.upsert_profile(profile)
    loaded = store.get_profile(first.name)
    assert loaded is not None
    assert loaded.platforms.youtube[0].handle == yt_channel.handle
    store.close()


def test_resolvers_produce_canonical_links():
    yt = resolve_youtube_handle("@Example")
    assert yt.url == "https://www.youtube.com/@Example"
    tw = resolve_twitch_login("twitch.tv/Streamer")
    assert tw.url == "https://twitch.tv/Streamer"
