# Webhook and Callback Signing

The `security.signing` module provides helpers for attaching and verifying
HMAC‑SHA256 signatures on arbitrary payloads. Signatures include a
caller‑supplied timestamp and nonce to protect against replay.  Convenience
helpers are provided to build and validate HTTP-style headers (`X-Signature`,
`X-Timestamp`, `X-Nonce`).

```python
from security.signing import (
    build_signature_headers,
    verify_signature_headers,
)

payload = b"{\"status\": \"ok\"}"
secret = "topsecret"
headers = build_signature_headers(payload, secret)
assert verify_signature_headers(payload, secret, headers)
```

Verification fails if the timestamp differs from the current time by more
than the default 300 seconds, if the signature does not match the payload, or
if the nonce is reused. A small in-memory cache of the last ~4k nonces is
maintained to provide this replay protection; entries expire after the
timestamp tolerance window.
