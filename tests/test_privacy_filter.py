from ultimate_discord_intelligence_bot.policy import policy_engine
from ultimate_discord_intelligence_bot.privacy import pii_detector
from ultimate_discord_intelligence_bot.services import MemoryService


def test_detect_email_and_phone():
    text = "Contact us at test@example.com or +1 555-123-4567"
    spans = pii_detector.detect(text)
    types = {s.type for s in spans}
    assert "email" in types and "phone" in types


def test_detect_ip():
    spans = pii_detector.detect("connect 192.168.0.1")
    assert any(s.type == "ip" for s in spans)


def test_memory_service_redacts_pii():
    mem = MemoryService()
    mem.add("Email me at test@example.com", {})
    results = mem.retrieve("email")
    assert "[redacted-email]" in results[0]["text"]


def test_policy_decision_block_unknown_source():
    policy = policy_engine.load_policy()
    decision = policy_engine.check_source({"source_platform": "unknown"}, policy)
    assert decision.decision == "block"
