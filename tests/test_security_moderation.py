from security.moderation import Moderation


def test_moderation_allows_clean_text():
    mod = Moderation(banned_terms=["bad"], action="redact")
    res = mod.check("hello world")
    assert res.action == "allow"
    assert res.text == "hello world"


def test_moderation_redacts_banned_term():
    mod = Moderation(banned_terms=["bad"], action="redact")
    res = mod.check("Bad word here")
    assert res.action == "redact"
    assert res.text == "[redacted] word here"


def test_moderation_blocks_when_configured():
    mod = Moderation(banned_terms=["bad"], action="block")
    res = mod.check("bad")
    assert res.action == "block"
