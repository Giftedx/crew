from pathlib import Path
import pytest

from security import validate_url, validate_filename, validate_path, validate_mime


def test_validate_url_rejects_private():
    with pytest.raises(ValueError):
        validate_url("http://127.0.0.1")


def test_validate_filename_blocks_traversal():
    with pytest.raises(ValueError):
        validate_filename("../secret.txt")
    assert validate_filename("safe.txt") == "safe.txt"


def test_validate_path_prevents_escape(tmp_path: Path):
    base = tmp_path / "base"
    base.mkdir()
    safe = validate_path("file.txt", base)
    assert safe.parent == base
    with pytest.raises(ValueError):
        validate_path("../etc/passwd", base)


def test_validate_mime_mismatch():
    with pytest.raises(ValueError):
        validate_mime("file.txt", "image/png")
    # matching MIME should pass
    validate_mime("file.txt", "text/plain")
