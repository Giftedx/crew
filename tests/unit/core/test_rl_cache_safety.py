from platform.cache.llm_cache import memo_llm
from platform.core.learning_engine import LearningEngine
from platform.core.privacy import privacy_filter
from platform.core.rl.policies.bandit_base import EpsilonGreedyBandit


def test_rl_cache_domain():
    engine = LearningEngine()
    engine.register_domain("cache", policy=EpsilonGreedyBandit(epsilon=0.0), priors={"bypass": 5.0, "use": 0.0})
    calls = {"n": 0}

    @memo_llm(lambda *_: {}, learning=engine)
    def expensive():
        calls["n"] += 1
        return calls["n"]

    assert expensive() == 1
    assert expensive() == 2
    engine = LearningEngine()
    engine.register_domain("cache", policy=EpsilonGreedyBandit(epsilon=0.0), priors={"use": 5.0})

    @memo_llm(lambda *_: {}, learning=engine)
    def cheap():
        calls["n"] += 1
        return calls["n"]

    val1 = cheap()
    val2 = cheap()
    assert val1 == val2
    assert calls["n"] == 3


def test_rl_safety_domain():
    engine = LearningEngine()
    engine.register_domain("safety", priors={"strict": 5.0})
    text, report = privacy_filter.filter_text("email me at test@example.com", {"tenant": None}, learning=engine)
    assert "[redacted-email]" in text
    assert report.redacted_by_type.get("email") == 1
