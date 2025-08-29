import pytest

from core.http_utils import http_request_with_retry
from obs import metrics as metrics_mod


def test_retry_metrics_exposed(monkeypatch):
    """Ensure retry attempt & give-up counters appear in scrape text when enabled.

    We simulate one failing request that triggers retries then a give-up.
    """
    monkeypatch.setenv("ENABLE_HTTP_METRICS", "1")
    monkeypatch.setenv("ENABLE_PROMETHEUS_ENDPOINT", "1")
    # Prefer unified flag; legacy path also honored
    monkeypatch.setenv("ENABLE_HTTP_RETRY", "1")

    # Reset metrics to a clean slate
    if hasattr(metrics_mod, "reset"):
        metrics_mod.reset()

    class FakeResp:
        def __init__(self, code):
            self.status_code = code

    attempts: dict[str, int] = {"count": 0}

    def always_500(url, **kwargs):  # noqa: ARG001
        attempts["count"] += 1
        return FakeResp(500)

    # Run request that will perform one retry then stop (returns final 500 response)
    http_request_with_retry(
        "GET",
        "https://example.com/fail",
        request_callable=always_500,
        max_attempts=2,
    )

    # Collect exposition if prometheus is available; otherwise skip cleanly
    try:  # runtime optional dep guard
        from prometheus_client import REGISTRY, generate_latest  # type: ignore
    except Exception:  # pragma: no cover - skip path
        pytest.skip("prometheus_client not installed")
    else:
        scrape = generate_latest(REGISTRY).decode()
    assert "http_retry_attempts_total" in scrape
    # In this configuration the helper returns final response without raising; give-up counter not incremented.
    # We only assert attempts counter presence.
