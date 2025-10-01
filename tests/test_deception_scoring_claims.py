from ultimate_discord_intelligence_bot.tools.deception_scoring_tool import DeceptionScoringTool


def test_deception_scoring_per_claim_and_source_weighting():
    tool = DeceptionScoringTool()
    factchecks = [
        {
            "claim": "The moon is made of cheese",
            "verdict": "False",
            "confidence": 0.9,
            "source": "snopes",
            "source_trust": 0.9,
            "salience": 1.0,
        },
        {
            "claim": "The moon is made of cheese",
            "verdict": "Likely False",
            "confidence": 0.8,
            "source": "randomblog",
            "source_trust": 0.2,
            "salience": 0.8,
        },
        {
            "claim": "Water boils at 100C at sea level",
            "verdict": "True",
            "confidence": 0.95,
            "source": "encyclopedia",
            "source_trust": 0.95,
        },
    ]
    # A fallacy should add a small contribution
    fallacies = {"fallacies": [{"type": "strawman"}]}
    res = tool.run({"factchecks": factchecks, "fallacies": fallacies})
    assert res["status"] == "success"
    score = res.get("score")
    assert isinstance(score, float)
    components = res.get("components")
    assert isinstance(components, dict)
    # Should include per-claim breakdown
    claims = components.get("claims")
    assert isinstance(claims, list)
    # Top claim should reference the cheese claim with non-zero score
    assert any("cheese" in (c.get("claim") or "").lower() and c.get("score", 0) > 0 for c in claims)
