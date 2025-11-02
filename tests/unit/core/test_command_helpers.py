import importlib
import os
import types


# Force lightweight mode off so helpers are available (but we won't start the bot)
os.environ.pop("LIGHTWEIGHT_IMPORT", None)

mod = importlib.import_module("scripts.start_full_bot")


def test_infer_platform_youtube():
    plat, desc = mod._infer_platform("https://www.youtube.com/watch?v=abc123")
    assert plat == "YouTube"
    assert "commentary" in desc.lower()


def test_infer_platform_twitch():
    plat, desc = mod._infer_platform("https://twitch.tv/somechannel")
    assert plat == "Twitch"
    assert "stream" in desc.lower()


def test_infer_platform_unknown():
    plat, desc = mod._infer_platform("https://example.com/video")
    assert plat == "Unknown"
    assert "pending" in desc.lower()


class DummyFactTool:
    def _run(self, claim):  # mimic external tool interface
        return types.SimpleNamespace(
            status="success",
            data={
                "verdict": "True",
                "confidence": 0.77,
                "explanation": "External verification successful",
            },
        )


def test_evaluate_claim_pattern_match():
    verdict, confidence, explanation = mod._evaluate_claim("The Earth is flat", None)
    assert verdict == "False"
    assert confidence > 0.9
    assert "earth" in explanation.lower()


def test_evaluate_claim_external_tool_used():
    tool = DummyFactTool()
    # Use a claim that does not match any static patterns
    verdict, confidence, explanation = mod._evaluate_claim("Quantum tunneling proves cats fly", tool)
    assert verdict == "True"
    assert 0.7 < confidence < 0.8
    assert "external" in explanation.lower()


def test_evaluate_claim_uncertain_without_tool():
    verdict, confidence, explanation = mod._evaluate_claim("Some obscure unverifiable claim", None)
    assert verdict == "Uncertain"
    assert confidence == 0.5
    assert "manual" in explanation.lower()
