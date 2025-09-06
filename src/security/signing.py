"""HMAC helpers for webhook and callback signing.

The helpers here provide both low level primitives for generating and
verifying signatures as well as convenience functions for HTTP style header
handling.  Signatures are ``HMAC-SHA256`` over ``timestamp`` ``nonce`` and the
payload bytes joined with a period.  The module also implements a bounded
nonce cache to offer basic replay protection without unbounded memory use.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from collections import OrderedDict
from collections.abc import Mapping

# ``OrderedDict`` gives us a tiny LRU cache so replay protection does not grow
# without bound.  Keys are nonces, values are the timestamp they were first
# seen at.  Entries older than the verification tolerance are pruned on every
# verify call and the cache size itself is capped at ``MAX_NONCES``.
MAX_NONCES = 4096
_seen_nonces: OrderedDict[str, int] = OrderedDict()


def _prune_nonces(now: int, tolerance: int) -> None:
    """Drop cached nonces that have aged past ``tolerance`` seconds or exceed
    the ``MAX_NONCES`` limit."""
    while _seen_nonces and (now - next(iter(_seen_nonces.values())) > tolerance or len(_seen_nonces) > MAX_NONCES):
        _seen_nonces.popitem(last=False)


def sign_message(payload: bytes, secret: str, timestamp: int, nonce: str) -> str:
    """Return a hex digest signature for ``payload``.

    The signature is ``HMAC-SHA256`` over ``timestamp`` ``nonce`` and ``payload``
    bytes joined with a period. Callers must supply the same values to
    :func:`verify_signature`.
    """
    base = f"{timestamp}.{nonce}.".encode() + payload
    return hmac.new(secret.encode(), base, hashlib.sha256).hexdigest()


def build_signature_headers(
    payload: bytes,
    secret: str,
    *,
    timestamp: int | None = None,
    nonce: str | None = None,
) -> dict[str, str]:
    """Return signature headers for ``payload``.

    Parameters
    ----------
    payload:
        Request body bytes to sign.
    secret:
        Shared secret used to compute the HMAC.
    timestamp, nonce:
        Optional values to use instead of generating fresh ones.  ``timestamp``
        defaults to ``time.time()`` and ``nonce`` is generated with
        :func:`secrets.token_hex` when omitted.
    """

    ts = int(time.time()) if timestamp is None else int(timestamp)
    n = nonce or secrets.token_hex(8)
    sig = sign_message(payload, secret, ts, n)
    return {"X-Signature": sig, "X-Timestamp": str(ts), "X-Nonce": n}


def verify_signature(  # noqa: PLR0913 - cryptographic interface requires explicit parameters for auditability (payload, secret, signature, timestamp, nonce, tolerance)
    payload: bytes,
    secret: str,
    signature: str,
    timestamp: int,
    nonce: str,
    *,
    tolerance: int = 300,
) -> bool:  # noqa: PLR0913 - explicit parameters reflect cryptographic inputs; bundling harms auditability
    """Validate ``signature`` for ``payload`` and check freshness.

    Parameters
    ----------
    payload:
        Original payload bytes.
    secret:
        Shared secret used to compute the HMAC.
    signature:
        Hex digest produced by :func:`sign_message`.
    timestamp:
        Unix epoch seconds supplied by the caller when the signature was
        generated. The signature is rejected if this differs from the current
        time by more than ``tolerance`` seconds.
    nonce:
        Unique nonce provided by the caller. Reusing a nonce will cause
        verification to fail.
    tolerance:
        Maximum age in seconds for a signature to be considered valid.
    """

    now = int(time.time())
    _prune_nonces(now, tolerance)
    if abs(now - int(timestamp)) > tolerance:
        return False
    expected = sign_message(payload, secret, int(timestamp), nonce)
    if not hmac.compare_digest(expected, signature):
        return False
    # basic replay protection
    if nonce in _seen_nonces:
        return False
    _seen_nonces[nonce] = now
    _prune_nonces(now, tolerance)
    return True


def verify_signature_headers(  # noqa: PLR0913 - explicit header names improve security review & maintainability
    payload: bytes,
    secret: str,
    headers: Mapping[str, str],
    *,
    signature_header: str = "X-Signature",
    timestamp_header: str = "X-Timestamp",
    nonce_header: str = "X-Nonce",
    tolerance: int = 300,
) -> bool:  # noqa: PLR0913 - explicit header names aid transparency & security review
    """Validate signature contained in HTTP-style ``headers``.

    The helper expects the same header names produced by
    :func:`build_signature_headers` but they can be overridden.
    Missing headers cause the check to fail.
    """

    try:
        signature = headers[signature_header]
        timestamp = int(headers[timestamp_header])
        nonce = headers[nonce_header]
    except KeyError:
        return False
    return verify_signature(payload, secret, signature, timestamp, nonce, tolerance=tolerance)
