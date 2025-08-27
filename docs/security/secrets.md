# Secrets Management

Use the `security.secrets` helpers to load secrets from environment variables
with optional versioning. A reference such as `OPENAI_KEY:v2` maps to the
environment variable `OPENAI_KEY_V2`.

## Basic usage
```python
from security.secrets import get_secret, rotate_secret

key = get_secret("OPENAI_KEY:v2")
# ... later after rotating the key in the environment
new_key = rotate_secret("OPENAI_KEY:v2")
```

The helpers cache values in-memory to avoid repeated lookups. Calling
`rotate_secret` clears the cache for a reference and returns the fresh value.
