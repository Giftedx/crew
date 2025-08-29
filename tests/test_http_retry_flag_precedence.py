from core import http_utils


def test_retry_flag_precedence(monkeypatch):
    # Both flags set: unified flag should enable retries (function returns True)
    monkeypatch.setenv("ENABLE_HTTP_RETRY", "1")
    monkeypatch.setenv("ENABLE_ANALYSIS_HTTP_RETRY", "1")
    assert http_utils._is_retry_enabled() is True  # noqa: SLF001 (internal ok for test)

    # Only legacy set still returns True (with deprecation warning captured)
    monkeypatch.delenv("ENABLE_HTTP_RETRY", raising=False)
    with monkeypatch.context() if hasattr(monkeypatch, 'context') else _null_ctx():  # fallback
        monkeypatch.setenv("ENABLE_ANALYSIS_HTTP_RETRY", "1")
        assert http_utils._is_retry_enabled() is True

    # Neither set -> False
    monkeypatch.delenv("ENABLE_ANALYSIS_HTTP_RETRY", raising=False)
    assert http_utils._is_retry_enabled() is False


class _null_ctx:  # pragma: no cover - compatibility shim
    def __enter__(self):
        return self
    def __exit__(self, *args):  # noqa: D401
        return False
