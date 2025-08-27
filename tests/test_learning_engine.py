from ultimate_discord_intelligence_bot.services.learning_engine import LearningEngine


def test_bandit_recommend_and_update():
    eng = LearningEngine(epsilon=0.0)
    eng.register_policy("p", ["a", "b"])
    first = eng.recommend("p")
    assert first in {"a", "b"}
    eng.record_outcome("p", "a", 1.0)
    eng.record_outcome("p", "b", 0.0)
    # after rewards, recommend should favour "a"
    choice = eng.recommend("p")
    assert choice == "a"
