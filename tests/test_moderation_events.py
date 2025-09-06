from security import moderation as moderation_module
from security.moderation import (
    ACTION_MODERATION,
    ACTION_MODERATION_REVIEW,
    ACTION_MODERATION_REVIEW_RESOLVE,
    Moderation,
)


def test_moderation_event_actions(caplog, monkeypatch):
    # Enable review queue with emit_events
    monkeypatch.setattr(
        Moderation,
        "_load",
        lambda self: {
            "banned_terms": ["forbidden"],
            "action": "block",
            "review_queue": {
                "enabled": True,
                "emit_events": True,
                "queue_redacted": True,
                "max_items": 10,
                "snippet_chars": 50,
            },
        },
    )
    mod = Moderation()
    captured: list[dict] = []

    def fake_log_security_event(**payload):  # type: ignore[no-untyped-def]
        captured.append(payload)

    monkeypatch.setattr(moderation_module, "log_security_event", fake_log_security_event)

    result = mod.check("This text contains forbidden material", actor="tester", tenant="t1", workspace="w1")
    # Expect base moderation and review events
    actions = [e.get("action") for e in captured]
    assert ACTION_MODERATION in actions, "Expected base moderation event"
    assert ACTION_MODERATION_REVIEW in actions, "Expected review queue event"
    # Resolve item and check resolve event
    if result.queue_id:
        caplog.clear()
        assert mod.resolve(result.queue_id, "approved", resolver="approver")
        actions2 = [e.get("action") for e in captured]
        assert ACTION_MODERATION_REVIEW_RESOLVE in actions2, "Expected review resolve event"
