from security.net_guard import is_safe_url


def test_safe_and_unsafe_urls():
    assert is_safe_url("https://example.com")
    assert not is_safe_url("http://127.0.0.1")
    assert not is_safe_url("file:///etc/passwd")
    assert not is_safe_url("http://[::1]")
    assert not is_safe_url("http://localhost")  # resolves to loopback
    assert not is_safe_url("http://169.254.0.1")  # link-local
    assert not is_safe_url("http://127.0.0.1\n")  # trailing whitespace stripped


def test_domain_with_mixed_ips(monkeypatch):
    from security import net_guard

    def fake_resolve(host: str):
        return ["93.184.216.34", "127.0.0.1"]  # example.com + loopback

    monkeypatch.setattr(net_guard, "_resolve_host", fake_resolve)
    assert not net_guard.is_safe_url("http://example.com")
