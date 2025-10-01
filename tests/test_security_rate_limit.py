import time

import pytest

from security.rate_limit import TokenBucket


def test_token_bucket_behavior():
    bucket = TokenBucket(rate=1, capacity=2)
    assert bucket.allow("k")
    assert bucket.allow("k")
    assert not bucket.allow("k")
    time.sleep(1.1)
    assert bucket.allow("k")


def test_token_bucket_rejects_non_positive_tokens():
    bucket = TokenBucket(rate=1, capacity=1)
    with pytest.raises(ValueError):
        bucket.allow("k", tokens=0)
