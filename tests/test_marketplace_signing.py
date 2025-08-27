from datetime import datetime, timedelta

from ultimate_discord_intelligence_bot.marketplace.signing import verify_manifest
from ultimate_discord_intelligence_bot.marketplace.store import MarketplaceStore
from ultimate_discord_intelligence_bot.marketplace.models import Signer
from datetime import datetime, timedelta, timezone


def make_store() -> MarketplaceStore:
    store = MarketplaceStore(":memory:")
    signer = Signer(
        fingerprint="abc123",
        issuer="test-ca",
        subject="tester",
        trust_tier="verified",
        revoked=False,
        not_before=datetime.now(timezone.utc) - timedelta(days=1),
        not_after=datetime.now(timezone.utc) + timedelta(days=1),
    )
    store.upsert_signer(signer)
    return store


def test_verify_manifest_happy_path():
    store = make_store()
    manifest = b"example manifest"
    signature = __import__("hashlib").sha256(manifest).hexdigest()
    report = verify_manifest(manifest, signature, "abc123", store)
    assert report.ok
    assert report.errors == []


def test_verify_manifest_fails_for_bad_sig():
    store = make_store()
    manifest = b"example manifest"
    bad_signature = "deadbeef"
    report = verify_manifest(manifest, bad_signature, "abc123", store)
    assert not report.ok
    assert "signature mismatch" in report.errors


def test_verify_manifest_unknown_signer():
    store = MarketplaceStore(":memory:")
    manifest = b"data"
    signature = __import__("hashlib").sha256(manifest).hexdigest()
    report = verify_manifest(manifest, signature, "missing", store)
    assert not report.ok
    assert "unknown signer" in report.errors
