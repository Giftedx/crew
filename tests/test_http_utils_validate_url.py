from __future__ import annotations

import pytest

from ultimate_discord_intelligence_bot.core.http_utils import validate_public_https_url


def test_validate_public_https_url_accepts_dns_hostname():
    assert validate_public_https_url("https://example.com/path?q=1")


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",  # insecure
        "https://127.0.0.1",  # loopback
        "https://10.0.0.1",  # private
        "https://192.168.1.1",  # private
        "https://172.16.0.1",  # private
    ],
)
def test_validate_public_https_url_rejects_insecure_and_private(url: str):
    with pytest.raises(ValueError):
        validate_public_https_url(url)
