"""Signature verification helpers for marketplace artifacts.

The implementation is intentionally lightweight: signatures are expected to be
hex-encoded SHA256 digests of the payload.  The :class:`MarketplaceStore` is
consulted to ensure the signer is known, within its validity window and not
revoked.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from core.time import default_utc_now


if TYPE_CHECKING:
    from datetime import datetime

    from .store import MarketplaceStore


@dataclass(slots=True)
class VerificationReport:
    ok: bool
    errors: list[str]
    signer_fingerprint: str | None = None
    chain_summary: str | None = None


def verify_manifest(
    manifest: bytes,
    signature: str,
    signer_fingerprint: str,
    store: MarketplaceStore,
    now: datetime | None = None,
) -> VerificationReport:
    """Verify a manifest signature using SHA256 digests.

    Parameters
    ----------
    manifest:
        Raw manifest bytes.
    signature:
        Expected hex digest of the manifest.
    signer_fingerprint:
        Fingerprint referencing a signer stored in :class:`MarketplaceStore`.
    store:
        Marketplace storage providing signer metadata.
    now:
        Optional timestamp used for validity checks.  Defaults to ``datetime.now(timezone.utc)``.
    """

    errors: list[str] = []
    now = now or default_utc_now()

    signer = store.get_signer(signer_fingerprint)
    if not signer:
        errors.append("unknown signer")
        return VerificationReport(False, errors)

    if signer.revoked:
        errors.append("signer revoked")
    if not (signer.not_before <= now <= signer.not_after):
        errors.append("signer not valid at this time")

    digest = hashlib.sha256(manifest).hexdigest()
    if digest != signature:
        errors.append("signature mismatch")

    return VerificationReport(len(errors) == 0, errors, signer_fingerprint, None)
