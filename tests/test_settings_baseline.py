from ultimate_discord_intelligence_bot.core.settings import Settings, get_settings


def test_get_settings_returns_singleton():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2, "get_settings() should be memoized (singleton style)"
    assert isinstance(s1, Settings)


def test_defaults_values_present():
    s = get_settings()
    # Spot check a few representative fields across categories
    assert s.cache_compression_enabled is True
    assert s.enable_reranker is False
    assert s.reward_cost_weight == 0.5
    assert s.rl_policy_model_selection == "epsilon_greedy"
    assert s.download_quality_default == "1080p"
    # Secrets default to None
    assert s.archive_api_token is None
    assert s.discord_bot_token is None


def test_attribute_stability_list():
    s = get_settings()
    expected = {
        "cache_compression_enabled",
        "cache_promotion_enabled",
        "enable_reranker",
        "enable_faster_whisper",
        "enable_local_llm",
        "enable_prompt_compression",
        "enable_token_aware_chunker",
        "enable_semantic_cache",
        "rerank_provider",
        "local_llm_url",
        "openrouter_referer",
        "openrouter_title",
        "reward_cost_weight",
        "reward_latency_weight",
        "reward_latency_ms_window",
        "rl_policy_model_selection",
        "token_chunk_target_tokens",
        "prompt_compression_max_repeated_blank_lines",
        "semantic_cache_threshold",
        "semantic_cache_ttl_seconds",
        "download_quality_default",
        "archive_api_token",
        "discord_bot_token",
    }
    missing = [name for name in expected if not hasattr(s, name)]
    assert not missing, f"Missing expected settings attributes: {missing}"
