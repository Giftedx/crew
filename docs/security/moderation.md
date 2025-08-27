# Content Moderation

The `security.moderation` helper provides a minimal rule-based filter for user
and model text. Banned terms are configured in `config/security.yaml` and may
be redacted or blocked entirely.

Example:

```python
from security.moderation import Moderation

mod = Moderation()
result = mod.check("bad word here")
if result.action == "block":
    raise ValueError("content not allowed")
text = result.text  # contains redactions when action == "redact"
```

This layer is intentionally simple; integrate with external moderation services
or LLM-based classifiers where needed.
