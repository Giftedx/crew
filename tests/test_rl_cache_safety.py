import time
from core.cache.llm_cache import memo_llm, llm_cache
from core.learning_engine import LearningEngine
from core.rl.policies.bandit_base import EpsilonGreedyBandit
from core.privacy import privacy_filter


def test_rl_cache_domain():
    engine = LearningEngine()
    engine.register_domain(
        "cache", policy=EpsilonGreedyBandit(epsilon=0.0), priors={"bypass": 5.0, "use": 0.0}
    )

    calls = {"n": 0}

    @memo_llm(lambda *_: {}, learning=engine)
    def expensive():
        calls["n"] += 1
        return calls["n"]

    assert expensive() == 1
    assert expensive() == 2  # bypassing cache, function executed again

    engine = LearningEngine()
    engine.register_domain(
        "cache", policy=EpsilonGreedyBandit(epsilon=0.0), priors={"use": 5.0}
    )

    @memo_llm(lambda *_: {}, learning=engine)
    def cheap():
        calls["n"] += 1
        return calls["n"]

    val1 = cheap()
    val2 = cheap()
    assert val1 == val2
    assert calls["n"] == 3  # first call of expensive twice + cheap once


def test_rl_safety_domain():
    engine = LearningEngine()
    engine.register_domain("safety", priors={"strict": 5.0})
    text, report = privacy_filter.filter_text("email me at test@example.com", {"tenant": None}, learning=engine)
    assert "[redacted-email]" in text
    assert report.redacted_by_type.get("email") == 1
