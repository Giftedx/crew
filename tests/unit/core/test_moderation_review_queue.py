from src.security.moderation import Moderation


def test_queue_block_event_and_storage(monkeypatch, tmp_path):
    # Prepare a temporary config enabling queue
    cfg = tmp_path / "security.yaml"
    cfg.write_text(
        """
moderation:
  banned_terms: [foo]
  action: block
  review_queue:
    enabled: true
    emit_events: false
    queue_redacted: false
    max_items: 10
    snippet_chars: 8
"""
    )
    m = Moderation(config_path=cfg)
    res = m.check("Foo bar baz qux", actor="user1")
    assert res.action == "block"
    assert res.queue_id is not None
    items = m.list_queue()
    assert len(items) == 1
    item = items[0]
    assert item.term == "foo"
    assert item.snippet.lower() == "foo bar "[:8]


def test_queue_redacted_when_enabled(tmp_path):
    cfg = tmp_path / "security.yaml"
    cfg.write_text(
        """
moderation:
  banned_terms: [secret]
  action: redact
  review_queue:
    enabled: true
    emit_events: false
    queue_redacted: true
    max_items: 10
    snippet_chars: 20
"""
    )
    m = Moderation(config_path=cfg)
    res = m.check("This SECRET token")
    assert res.action == "redact"
    assert res.queue_id is not None
    assert "[redacted]" in res.text


def test_queue_disabled(tmp_path):
    cfg = tmp_path / "security.yaml"
    cfg.write_text(
        """
moderation:
  banned_terms: [bad]
  action: block
  review_queue:
    enabled: false
    emit_events: false
"""
    )
    m = Moderation(config_path=cfg)
    res = m.check("bad stuff here")
    assert res.action == "block"
    assert res.queue_id is None
    assert m.list_queue() == []


def test_max_items_trim(tmp_path):
    cfg = tmp_path / "security.yaml"
    cfg.write_text(
        """
moderation:
  banned_terms: [x]
  action: block
  review_queue:
    enabled: true
    emit_events: false
    max_items: 3
    snippet_chars: 5
"""
    )
    m = Moderation(config_path=cfg)
    for i in range(5):
        m.check(f"x message {i}")
    items = m.list_queue()
    assert len(items) == 3  # trimmed to max_items


def test_resolve_and_purge(tmp_path):
    cfg = tmp_path / "security.yaml"
    cfg.write_text(
        """
moderation:
  banned_terms: [y]
  action: block
  review_queue:
    enabled: true
    emit_events: false
    max_items: 5
    snippet_chars: 10
"""
    )
    m = Moderation(config_path=cfg)
    res = m.check("y content one")
    assert res.queue_id
    ok = m.resolve(res.queue_id, "approved", resolver="mod1")
    assert ok
    # Purge resolved
    removed = m.purge_resolved()
    assert removed == 1
    assert m.list_queue() == []
