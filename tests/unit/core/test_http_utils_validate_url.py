from __future__ import annotations
import pytest
from platform.http.http_utils import validate_public_https_url

def test_validate_public_https_url_accepts_dns_hostname():
    assert validate_public_https_url('https://example.com/path?q=1')

@pytest.mark.parametrize('url', ['http://example.com', 'https://127.0.0.1', 'https://10.0.0.1', 'https://192.168.1.1', 'https://172.16.0.1'])
def test_validate_public_https_url_rejects_insecure_and_private(url: str):
    with pytest.raises(ValueError):
        validate_public_https_url(url)