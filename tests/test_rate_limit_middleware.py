import os
import time

from fastapi.testclient import TestClient
from ultimate_discord_intelligence_bot.server.app import create_app


def test_rate_limit_middleware_basic():
    os.environ["ENABLE_API"] = "1"
    os.environ["ENABLE_HTTP_METRICS"] = "0"
    os.environ["ENABLE_PROMETHEUS_ENDPOINT"] = "0"
    os.environ["ENABLE_RATE_LIMITING"] = "1"
    os.environ["RATE_LIMIT_RPS"] = "5"
    os.environ["RATE_LIMIT_BURST"] = "5"
    app = create_app()
    client = TestClient(app)

    allowed = 0
    limited = 0
    for _ in range(7):
        r = client.get("/__not_exist")
        if r.status_code == 429:
            limited += 1
        else:
            allowed += 1
    # With burst=5 we should allow ~5 immediately then start 429-ing
    assert allowed >= 5
    assert limited >= 1

    # After sleeping 1 second (5 tokens) we should allow again
    time.sleep(1.05)
    r2 = client.get("/__not_exist")
    assert r2.status_code != 429
