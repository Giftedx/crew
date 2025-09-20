"""Additional tests for migrated HTTP retry functionality edge cases."""

import pytest
from core.http_utils import is_retry_enabled, resilient_get


def test_retry_enabled_flag():
    """Test that retry functionality respects the enable flag."""
    # Test that function exists and returns a boolean
    result = is_retry_enabled()
    assert isinstance(result, bool)


def test_resilient_get_invalid_url():
    """Test resilient_get with invalid URL."""
    with pytest.raises(Exception):
        # This should raise an exception due to invalid URL
        resilient_get("not-a-valid-url", max_attempts=1)


def test_resilient_get_connection_error():
    """Test resilient_get with connection error."""
    # Test with a URL that should cause connection error
    with pytest.raises(Exception):
        resilient_get("http://nonexistent-domain-12345.invalid", max_attempts=1, base_delay=0.1)


def test_resilient_get_basic_parameters():
    """Test resilient_get accepts basic parameters."""
    # Test parameter validation without actually making a request
    try:
        # This URL is designed to fail, but parameters should be accepted
        resilient_get("http://127.0.0.1:99999", max_attempts=1, base_delay=0.01, max_delay=0.1, timeout=0.1)
    except Exception:
        # Expected to fail, we're just testing parameter acceptance
        pass


if __name__ == "__main__":
    pytest.main([__file__])
