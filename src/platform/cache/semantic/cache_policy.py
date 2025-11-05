"""
Semantic Cache Policy Logic
Promotion/demotion for semantic cache entries based on hit rate and evaluation score.
"""

from typing import Any


class SemanticCachePolicy:
    def __init__(self, promote_threshold: float = 0.8, demote_threshold: float = 0.3, min_hits: int = 10):
        """
        Args:
            promote_threshold: Score above which entries are promoted.
            demote_threshold: Score below which entries are demoted.
            min_hits: Minimum cache hits before considering promotion/demotion.
        """
        self.promote_threshold = promote_threshold
        self.demote_threshold = demote_threshold
        self.min_hits = min_hits

    def evaluate_entry(self, entry: dict[str, Any]) -> str:
        """
        Evaluate cache entry for promotion/demotion.
        Args:
            entry: Dict with keys 'hit_rate', 'eval_score', 'hits'.
        Returns:
            'promote', 'demote', or 'retain'.
        """
        hits = entry.get("hits", 0)
        hit_rate = entry.get("hit_rate", 0.0)
        eval_score = entry.get("eval_score", 0.0)

        if hits < self.min_hits:
            return "retain"
        if eval_score >= self.promote_threshold and hit_rate >= 0.7:
            return "promote"
        if eval_score <= self.demote_threshold or hit_rate < 0.2:
            return "demote"
        return "retain"

    def batch_evaluate(self, entries: dict[str, dict[str, Any]]) -> dict[str, str]:
        """
        Batch evaluate multiple cache entries.
        Args:
            entries: Dict of entry_id -> entry dict.
        Returns:
            Dict of entry_id -> action ('promote', 'demote', 'retain').
        """
        return {eid: self.evaluate_entry(entry) for eid, entry in entries.items()}
