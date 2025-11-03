from platform.llm.providers.openrouter import quality as q

import pytest


@pytest.fixture(autouse=True)
def stub_prompt_engine(monkeypatch):
    """Stub PromptEngine.count_tokens to avoid heavy deps during tests.

    This keeps tests fast and independent from optional tokenizer packages.
    """

    class _StubEngine:
        def count_tokens(self, text: str) -> int:
            return max(1, len((text or "").split()))

    monkeypatch.setattr(q, "PromptEngine", lambda: _StubEngine())
    yield


def test_basic_quality_assessment_empty():
    res = q.basic_quality_assessment("")
    assert "score" in res and 0.0 <= res["score"] <= 1.0
    assert res["tokens"] >= 1
    assert res["signals"] == {"has_apology": False, "has_structure": False, "has_suspicious": False}


def test_apology_and_structure_signals():
    text = "I'm sorry, I cannot assist with that.\n- First\n- Second\n- Third"
    res = q.basic_quality_assessment(text)
    assert res["signals"]["has_apology"] is True
    assert res["signals"]["has_structure"] is True


def test_length_increases_score():
    short = "word " * 10
    long = "word " * 200
    res_short = q.basic_quality_assessment(short)
    res_long = q.basic_quality_assessment(long)
    assert res_long["score"] >= res_short["score"]


def test_structure_bonus():
    base = "This is a response with some content."
    structured = base + "\n- bullet one\n- bullet two"
    res_base = q.basic_quality_assessment(base)
    res_structured = q.basic_quality_assessment(structured)
    assert res_structured["score"] >= res_base["score"]


def test_suspicious_penalty():
    base = "Clear and concise explanation about the topic at hand."
    suspicious_blob = "/very/long/path/without/tld/or/scheme/that_looks_questionable_1234567890"
    with_penalty = base + " " + suspicious_blob
    res_base = q.basic_quality_assessment(base)
    res_penalty = q.basic_quality_assessment(with_penalty)
    assert res_penalty["score"] <= res_base["score"]


def test_min_tokens_parameter_affects_score():
    text = "word " * 50
    res_default = q.basic_quality_assessment(text)
    res_stricter = q.basic_quality_assessment(text, min_tokens=200)
    assert res_stricter["score"] <= res_default["score"]


def test_quality_assessment_with_prompt_relevance():
    prompt = "Explain what Python programming language is and list two key features."
    text = "Python is a high-level programming language.\n- Easy to read\n- Large standard library"
    res = q.quality_assessment(text, prompt=prompt)
    assert 0.0 <= res["signals"]["relevance"] <= 1.0
    assert res["signals"]["relevance"] >= 0.15


def test_quality_assessment_json_expectation_bonus_and_penalty():
    good_json = '{"a": 1, "b": [1,2,3]}'
    bad_json = '{"a": 1,}'
    res_good = q.quality_assessment(good_json, expect_json=True)
    res_bad = q.quality_assessment(bad_json, expect_json=True)
    assert res_good["signals"]["json_valid"] is True
    assert res_bad["signals"]["json_valid"] is False
    assert res_good["score"] >= res_bad["score"]


def test_quality_assessment_repetition_penalty():
    repetitive = "good good good good good good good good good good"
    non_repetitive = "This is a clear and concise explanation of a concept."
    res_rep = q.quality_assessment(repetitive)
    res_non = q.quality_assessment(non_repetitive)
    assert res_rep["score"] <= res_non["score"]


def test_quality_assessment_code_explanation_balance():
    code_only = "```python\nprint('hi')\n```"
    code_with_explain = "Here is how to print in Python:\n```python\nprint('hi')\n```\nThis prints a greeting."
    res_code_only = q.quality_assessment(code_only)
    res_with_explain = q.quality_assessment(code_with_explain)
    assert res_with_explain["score"] >= res_code_only["score"]


def test_quality_assessment_list_expectation():
    prompt = "List 3 key benefits of unit testing."
    two_items = "- Faster bug detection\n- Safer refactoring"
    three_items = "- Faster bug detection\n- Safer refactoring\n- Documentation of behavior"
    res_two = q.quality_assessment(two_items, prompt=prompt)
    res_three = q.quality_assessment(three_items, prompt=prompt)
    assert res_three["signals"]["expected_list_items"] == 3
    assert res_three["signals"]["list_items"] >= 3
    assert res_three["score"] >= res_two["score"]


def test_quality_assessment_python_parseability_signal():
    ok = "```python\nprint('hello')\n```\nExplanation here."
    bad = "```python\nprint(\n```\nExplanation here."
    res_ok = q.quality_assessment(ok)
    res_bad = q.quality_assessment(bad)
    assert res_ok["signals"]["python_blocks_total"] == 1
    assert res_ok["signals"]["python_blocks_ok"] == 1
    assert res_bad["signals"]["python_blocks_total"] == 1
    assert res_bad["signals"]["python_blocks_ok"] == 0
    assert res_ok["score"] >= res_bad["score"]


def test_quality_assessment_ttr_influence():
    repetitive = "test test test test test test test test"
    varied = "tests verify code reliability and prevent regressions"
    res_rep = q.quality_assessment(repetitive)
    res_var = q.quality_assessment(varied)
    assert res_var["signals"]["ttr"] >= res_rep["signals"]["ttr"]
    assert res_var["score"] >= res_rep["score"]


def test_quality_ensemble_assessment_metrics_and_best_selection():
    prompt = "Explain caching and list 3 benefits."
    r1 = "Caching stores results to speed up repeated requests.\n- Faster responses\n- Lower load\n- Reduced cost"
    r2 = "Caching reduces latency and offloads compute.\n- Speed\n- Scale\n- Savings"
    r3 = "It is a technique that may or may not help."
    ens = q.quality_ensemble_assessment([r1, r2, r3], prompt=prompt)
    assert isinstance(ens["assessments"], list) and len(ens["assessments"]) == 3
    assert 0.0 <= ens["avg_pairwise_diversity"] <= 1.0
    assert ens["cluster_count"] >= 1
    scores = [a["score"] for a in ens["assessments"]]
    assert ens["best_score"] == max(scores)
