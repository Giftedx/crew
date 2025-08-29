"""Utilities for accessing secrets with optional versioning and caching.

Secrets are read from environment variables and cached in-memory to avoid
repeated lookups. A secret reference may include an optional version suffix
separated by a colon, e.g. ``OPENAI_KEY:v2`` maps to the environment variable
``OPENAI_KEY_V2``.

Examples
--------
>>> import os
>>> from security.secrets import get_secret, rotate_secret
>>> os.environ['DEMO_TOKEN_V1'] = 'one'
>>> get_secret('DEMO_TOKEN:v1')
'one'
>>> os.environ['DEMO_TOKEN_V1'] = 'two'
>>> get_secret('DEMO_TOKEN:v1')  # cached
'one'
>>> rotate_secret('DEMO_TOKEN:v1')
'two'
"""

from __future__ import annotations

import os

_cache: dict[str, str] = {}


def _env_key(ref: str) -> str:
    name, _, version = ref.partition(":")
    key = name
    if version:
        key = f"{name}_{version}"
    return key.upper().replace("-", "_")


def get_secret(ref: str) -> str:
    """Return the secret value for ``ref``.

    Parameters
    ----------
    ref:
        Secret reference in the form ``NAME`` or ``NAME:version``.

    Raises
    ------
    KeyError
        If the corresponding environment variable is not set.
    """

    key = _env_key(ref)
    if key in _cache:
        return _cache[key]
    try:
        value = os.environ[key]
    except KeyError as exc:  # pragma: no cover - defensive
        raise KeyError(f"Missing secret: {key}") from exc
    _cache[key] = value
    return value


def rotate_secret(ref: str) -> str:
    """Refresh and return the secret value for ``ref``.

    This clears any cached value and re-reads from the environment.
    """

    key = _env_key(ref)
    _cache.pop(key, None)
    return get_secret(ref)
