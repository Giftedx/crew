from security.secrets import get_secret, rotate_secret


def test_get_secret_and_rotation(monkeypatch):
    monkeypatch.setenv("EXAMPLE_TOKEN_V1", "alpha")
    assert get_secret("EXAMPLE_TOKEN:v1") == "alpha"

    monkeypatch.setenv("EXAMPLE_TOKEN_V1", "beta")
    # cached value
    assert get_secret("EXAMPLE_TOKEN:v1") == "alpha"

    # rotate to refresh
    assert rotate_secret("EXAMPLE_TOKEN:v1") == "beta"
