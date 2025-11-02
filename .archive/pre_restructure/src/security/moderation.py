"""Simple content moderation utilities."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .events import log_security_event


# Standardized moderation action names (hierarchical dotted form)
ACTION_MODERATION = "moderation"
ACTION_MODERATION_REVIEW = "moderation.review"
ACTION_MODERATION_REVIEW_RESOLVE = "moderation.review.resolve"
__all__ = [
    "ACTION_MODERATION",
    "ACTION_MODERATION_REVIEW",
    "ACTION_MODERATION_REVIEW_RESOLVE",
    "Moderation",
    "ModerationResult",
    "ReviewItem",
]

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "security.yaml"


@dataclass
class ModerationResult:
    action: str
    text: str
    # Optional queue identifier if the item was queued for review.
    queue_id: str | None = None


@dataclass
class ReviewItem:
    id: str
    term: str
    snippet: str
    original: str
    actor: str | None
    tenant: str | None
    workspace: str | None
    timestamp: float = field(default_factory=lambda: time.time())
    resolved: bool = False
    resolution: str | None = None  # "approved" | "rejected"
    resolver: str | None = None
    resolved_at: float | None = None


class Moderation:
    """Rule-based moderation checker using banned terms."""

    def __init__(
        self,
        banned_terms: list[str] | None = None,
        action: str | None = None,
        config_path: Path | None = None,
    ) -> None:
        self._config_path = config_path or DEFAULT_CONFIG_PATH
        if banned_terms is None or action is None:
            data = self._load()
            banned_terms = banned_terms or data.get("banned_terms", [])
            action = action or data.get("action", "block")
        self.banned_terms = [t.lower() for t in banned_terms]
        self.action = action
        # In-memory review queue store
        self._queue: dict[str, ReviewItem] = {}
        self._queue_order: list[str] = []  # maintain insertion order

    def _load(self) -> dict:
        if not self._config_path.exists():
            return {}
        data = yaml.safe_load(self._config_path.read_text()) or {}
        return data.get("moderation", {})

    def check(
        self,
        text: str,
        *,
        actor: str | None = None,
        tenant: str | None = None,
        workspace: str | None = None,
    ) -> ModerationResult:
        lowered = text.lower()
        found = False
        cleaned = text
        offending = None
        data = self._load()
        review_queue = data.get("review_queue", {}) if isinstance(data, dict) else {}
        review_enabled = bool(review_queue.get("enabled", False))
        emit_events = bool(review_queue.get("emit_events", False))
        queue_redacted = bool(review_queue.get("queue_redacted", False))
        max_items = int(review_queue.get("max_items", 500))
        snippet_chars = int(review_queue.get("snippet_chars", 120))
        for term in self.banned_terms:
            if term in lowered:
                found = True
                offending = term
                if self.action == "redact":
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    cleaned = pattern.sub("[redacted]", cleaned)
        if not found:
            return ModerationResult("allow", text)
        decision = "redact" if self.action == "redact" else "block"
        queue_id: str | None = None
        # Queue when review is enabled for both block and redact decisions.
        # If queue_redacted is True and decision is redact we store the redacted snippet; otherwise original text.
        should_queue = review_enabled and decision in {"block", "redact"}
        if should_queue:
            # Create review item (bounded queue with trimming)
            base_snippet_source = cleaned if (decision == "redact" and queue_redacted) else text
            snippet = base_snippet_source[:snippet_chars]
            queue_id = f"rvw_{int(time.time() * 1000)}_{len(self._queue)}"
            item = ReviewItem(
                id=queue_id,
                term=offending or "",
                snippet=snippet,
                original=text,
                actor=actor,
                tenant=tenant,
                workspace=workspace,
            )
            self._queue[queue_id] = item
            self._queue_order.append(queue_id)
            # Trim if exceeding max_items (drop oldest unresolved first)
            if len(self._queue_order) > max_items:
                while len(self._queue_order) > max_items:
                    oldest_id = self._queue_order.pop(0)
                    self._queue.pop(oldest_id, None)
            if emit_events:
                # Emit a separate review event but preserve original moderation event semantics.
                log_security_event(
                    actor=actor or "system",
                    action=ACTION_MODERATION_REVIEW,
                    resource=offending or "text",
                    decision="queue",
                    reason=("banned_term_block" if decision == "block" else "banned_term_redact"),
                    tenant=tenant,
                    workspace=workspace,
                )
        # Emit the primary moderation event LAST so tests (and downstream observers) see the canonical
        # moderation action as the most recent security event; auxiliary review events (if any) precede it.
        log_security_event(
            actor=actor or "system",
            action=ACTION_MODERATION,
            resource=offending or "text",
            decision=decision,
            reason="banned_term",
            tenant=tenant,
            workspace=workspace,
        )
        if decision == "redact":
            return ModerationResult("redact", cleaned, queue_id=queue_id)
        return ModerationResult("block", text, queue_id=queue_id)

    # Review queue management API
    def list_queue(self, include_resolved: bool = False) -> list[ReviewItem]:
        return [self._queue[qid] for qid in self._queue_order if include_resolved or not self._queue[qid].resolved]

    def get_item(self, item_id: str) -> ReviewItem | None:
        return self._queue.get(item_id)

    def resolve(self, item_id: str, resolution: str, *, resolver: str | None = None) -> bool:
        if resolution not in {"approved", "rejected"}:
            raise ValueError("resolution must be 'approved' or 'rejected'")
        item = self._queue.get(item_id)
        if not item or item.resolved:
            return False
        item.resolved = True
        item.resolution = resolution
        item.resolver = resolver
        item.resolved_at = time.time()
        log_security_event(
            actor=resolver or "system",
            action=ACTION_MODERATION_REVIEW_RESOLVE,
            resource=item.term or "text",
            decision=resolution,
            reason="review_resolution",
            tenant=item.tenant,
            workspace=item.workspace,
        )
        return True

    def purge_resolved(self) -> int:
        removed = 0
        remaining = []
        for qid in self._queue_order:
            item = self._queue.get(qid)
            if item and item.resolved:
                self._queue.pop(qid, None)
                removed += 1
            else:
                remaining.append(qid)
        self._queue_order = remaining
        return removed
