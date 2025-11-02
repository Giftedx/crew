from platform.security.moderation import Moderation

def test_queue_block_event_and_storage(monkeypatch, tmp_path):
    cfg = tmp_path / 'security.yaml'
    cfg.write_text('\nmoderation:\n  banned_terms: [foo]\n  action: block\n  review_queue:\n    enabled: true\n    emit_events: false\n    queue_redacted: false\n    max_items: 10\n    snippet_chars: 8\n')
    m = Moderation(config_path=cfg)
    res = m.check('Foo bar baz qux', actor='user1')
    assert res.action == 'block'
    assert res.queue_id is not None
    items = m.list_queue()
    assert len(items) == 1
    item = items[0]
    assert item.term == 'foo'
    assert item.snippet.lower() == 'foo bar '[:8]

def test_queue_redacted_when_enabled(tmp_path):
    cfg = tmp_path / 'security.yaml'
    cfg.write_text('\nmoderation:\n  banned_terms: [secret]\n  action: redact\n  review_queue:\n    enabled: true\n    emit_events: false\n    queue_redacted: true\n    max_items: 10\n    snippet_chars: 20\n')
    m = Moderation(config_path=cfg)
    res = m.check('This SECRET token')
    assert res.action == 'redact'
    assert res.queue_id is not None
    assert '[redacted]' in res.text

def test_queue_disabled(tmp_path):
    cfg = tmp_path / 'security.yaml'
    cfg.write_text('\nmoderation:\n  banned_terms: [bad]\n  action: block\n  review_queue:\n    enabled: false\n    emit_events: false\n')
    m = Moderation(config_path=cfg)
    res = m.check('bad stuff here')
    assert res.action == 'block'
    assert res.queue_id is None
    assert m.list_queue() == []

def test_max_items_trim(tmp_path):
    cfg = tmp_path / 'security.yaml'
    cfg.write_text('\nmoderation:\n  banned_terms: [x]\n  action: block\n  review_queue:\n    enabled: true\n    emit_events: false\n    max_items: 3\n    snippet_chars: 5\n')
    m = Moderation(config_path=cfg)
    for i in range(5):
        m.check(f'x message {i}')
    items = m.list_queue()
    assert len(items) == 3

def test_resolve_and_purge(tmp_path):
    cfg = tmp_path / 'security.yaml'
    cfg.write_text('\nmoderation:\n  banned_terms: [y]\n  action: block\n  review_queue:\n    enabled: true\n    emit_events: false\n    max_items: 5\n    snippet_chars: 10\n')
    m = Moderation(config_path=cfg)
    res = m.check('y content one')
    assert res.queue_id
    ok = m.resolve(res.queue_id, 'approved', resolver='mod1')
    assert ok
    removed = m.purge_resolved()
    assert removed == 1
    assert m.list_queue() == []