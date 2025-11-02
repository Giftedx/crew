"""Consensus protocols for multi-agent deliberation.

Implements voting mechanisms, confidence weighting, and conflict resolution
for collaborative decision-making across agents.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class VoteAggregationStrategy(str, Enum):
    """Strategies for aggregating agent votes."""

    MAJORITY = "majority"  # Simple majority wins
    CONFIDENCE_WEIGHTED = "confidence_weighted"  # Weight by confidence scores
    UNANIMOUS = "unanimous"  # All agents must agree
    EXPERT_WEIGHTED = "expert_weighted"  # Weight by agent expertise/track record


@dataclass
class AgentVote:
    """Single agent's vote in a deliberation."""

    agent_id: str
    decision: Any  # The voted option/choice
    confidence: float  # 0.0 to 1.0
    reasoning: str = ""
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsensusResult:
    """Result of a consensus protocol execution."""

    decision: Any  # Winning decision
    confidence: float  # Aggregate confidence in decision
    votes: list[AgentVote]  # All votes cast
    strategy: VoteAggregationStrategy
    is_consensus: bool  # True if consensus achieved
    conflict_detected: bool = False
    reasoning: str = ""  # Aggregate reasoning
    metadata: dict[str, Any] = field(default_factory=dict)


class ConsensusProtocol:
    """Execute multi-agent consensus protocols."""

    def __init__(
        self,
        *,
        strategy: VoteAggregationStrategy = VoteAggregationStrategy.CONFIDENCE_WEIGHTED,
        min_confidence: float = 0.5,
        consensus_threshold: float = 0.7,
    ):
        """Initialize consensus protocol.

        Args:
            strategy: Voting aggregation strategy to use.
            min_confidence: Minimum confidence required for a decision.
            consensus_threshold: Threshold for declaring consensus (0.0-1.0).
        """
        self.strategy = strategy
        self.min_confidence = min_confidence
        self.consensus_threshold = consensus_threshold

    def aggregate_votes(self, votes: list[AgentVote]) -> ConsensusResult:
        """Aggregate votes using configured strategy.

        Args:
            votes: List of agent votes to aggregate.

        Returns:
            ConsensusResult with winning decision and metadata.
        """
        if not votes:
            return ConsensusResult(
                decision=None,
                confidence=0.0,
                votes=[],
                strategy=self.strategy,
                is_consensus=False,
                reasoning="No votes received",
            )

        if self.strategy == VoteAggregationStrategy.MAJORITY:
            return self._majority_vote(votes)
        elif self.strategy == VoteAggregationStrategy.CONFIDENCE_WEIGHTED:
            return self._confidence_weighted_vote(votes)
        elif self.strategy == VoteAggregationStrategy.UNANIMOUS:
            return self._unanimous_vote(votes)
        elif self.strategy == VoteAggregationStrategy.EXPERT_WEIGHTED:
            return self._expert_weighted_vote(votes)
        else:
            logger.warning(f"Unknown strategy {self.strategy}, falling back to majority")
            return self._majority_vote(votes)

    def _majority_vote(self, votes: list[AgentVote]) -> ConsensusResult:
        """Simple majority wins."""
        # Count votes by decision
        vote_counts: dict[Any, list[AgentVote]] = {}

        for vote in votes:
            decision_key = str(vote.decision)  # Convert to string for dict key
            if decision_key not in vote_counts:
                vote_counts[decision_key] = []
            vote_counts[decision_key].append(vote)

        # Find majority
        max_votes = max(len(v) for v in vote_counts.values())
        winners = [decision for decision, v in vote_counts.items() if len(v) == max_votes]

        # Check for tie
        if len(winners) > 1:
            return ConsensusResult(
                decision=None,
                confidence=0.0,
                votes=votes,
                strategy=self.strategy,
                is_consensus=False,
                conflict_detected=True,
                reasoning=f"Tie between {len(winners)} options",
            )

        winning_decision = winners[0]
        winning_votes = vote_counts[winning_decision]

        # Calculate consensus strength
        consensus_strength = len(winning_votes) / len(votes)
        avg_confidence = sum(v.confidence for v in winning_votes) / len(winning_votes)

        is_consensus = consensus_strength >= self.consensus_threshold and avg_confidence >= self.min_confidence

        # Aggregate reasoning
        reasoning = " ".join(v.reasoning for v in winning_votes if v.reasoning)

        return ConsensusResult(
            decision=winning_votes[0].decision,  # Use original type
            confidence=avg_confidence,
            votes=votes,
            strategy=self.strategy,
            is_consensus=is_consensus,
            reasoning=reasoning or f"Majority vote: {len(winning_votes)}/{len(votes)}",
            metadata={"vote_count": len(winning_votes), "total_votes": len(votes)},
        )

    def _confidence_weighted_vote(self, votes: list[AgentVote]) -> ConsensusResult:
        """Weight votes by confidence scores."""
        # Group by decision
        decision_weights: dict[Any, float] = {}
        decision_votes: dict[Any, list[AgentVote]] = {}

        for vote in votes:
            decision_key = str(vote.decision)

            if decision_key not in decision_weights:
                decision_weights[decision_key] = 0.0
                decision_votes[decision_key] = []

            decision_weights[decision_key] += vote.confidence
            decision_votes[decision_key].append(vote)

        # Find highest weighted decision
        winning_decision_key = max(decision_weights, key=decision_weights.get)  # type: ignore
        winning_votes = decision_votes[winning_decision_key]
        total_weight = sum(decision_weights.values())

        # Aggregate confidence
        consensus_strength = decision_weights[winning_decision_key] / total_weight if total_weight > 0 else 0.0
        avg_confidence = sum(v.confidence for v in winning_votes) / len(winning_votes)

        is_consensus = consensus_strength >= self.consensus_threshold and avg_confidence >= self.min_confidence

        # Check for close competition (potential conflict)
        sorted_weights = sorted(decision_weights.values(), reverse=True)
        conflict_detected = False
        if len(sorted_weights) > 1:
            weight_gap = (sorted_weights[0] - sorted_weights[1]) / total_weight
            conflict_detected = weight_gap < 0.2  # Less than 20% gap

        reasoning = " ".join(v.reasoning for v in winning_votes if v.reasoning)

        return ConsensusResult(
            decision=winning_votes[0].decision,
            confidence=avg_confidence,
            votes=votes,
            strategy=self.strategy,
            is_consensus=is_consensus,
            conflict_detected=conflict_detected,
            reasoning=reasoning or f"Confidence-weighted consensus: {consensus_strength:.1%}",
            metadata={"consensus_strength": consensus_strength, "total_weight": total_weight},
        )

    def _unanimous_vote(self, votes: list[AgentVote]) -> ConsensusResult:
        """All agents must agree."""
        if not votes:
            return ConsensusResult(
                decision=None,
                confidence=0.0,
                votes=[],
                strategy=self.strategy,
                is_consensus=False,
            )

        # Check if all decisions are the same
        first_decision = str(votes[0].decision)
        is_unanimous = all(str(v.decision) == first_decision for v in votes)

        if is_unanimous:
            avg_confidence = sum(v.confidence for v in votes) / len(votes)
            reasoning = " ".join(v.reasoning for v in votes if v.reasoning)

            return ConsensusResult(
                decision=votes[0].decision,
                confidence=avg_confidence,
                votes=votes,
                strategy=self.strategy,
                is_consensus=avg_confidence >= self.min_confidence,
                reasoning=reasoning or f"Unanimous agreement from {len(votes)} agents",
            )
        else:
            return ConsensusResult(
                decision=None,
                confidence=0.0,
                votes=votes,
                strategy=self.strategy,
                is_consensus=False,
                conflict_detected=True,
                reasoning="No unanimous agreement",
            )

    def _expert_weighted_vote(self, votes: list[AgentVote]) -> ConsensusResult:
        """Weight votes by agent expertise (from metadata)."""
        # Extract expertise scores from metadata (default to 1.0)
        decision_weights: dict[Any, float] = {}
        decision_votes: dict[Any, list[AgentVote]] = {}

        for vote in votes:
            expertise = vote.metadata.get("expertise_score", 1.0)
            confidence_adjusted_weight = vote.confidence * expertise

            decision_key = str(vote.decision)

            if decision_key not in decision_weights:
                decision_weights[decision_key] = 0.0
                decision_votes[decision_key] = []

            decision_weights[decision_key] += confidence_adjusted_weight
            decision_votes[decision_key].append(vote)

        winning_decision_key = max(decision_weights, key=decision_weights.get)  # type: ignore
        winning_votes = decision_votes[winning_decision_key]
        total_weight = sum(decision_weights.values())

        consensus_strength = decision_weights[winning_decision_key] / total_weight if total_weight > 0 else 0.0
        avg_confidence = sum(v.confidence for v in winning_votes) / len(winning_votes)

        is_consensus = consensus_strength >= self.consensus_threshold and avg_confidence >= self.min_confidence

        reasoning = " ".join(v.reasoning for v in winning_votes if v.reasoning)

        return ConsensusResult(
            decision=winning_votes[0].decision,
            confidence=avg_confidence,
            votes=votes,
            strategy=self.strategy,
            is_consensus=is_consensus,
            reasoning=reasoning or f"Expert-weighted consensus: {consensus_strength:.1%}",
            metadata={"consensus_strength": consensus_strength, "expert_weight": total_weight},
        )


__all__ = ["AgentVote", "ConsensusProtocol", "ConsensusResult", "VoteAggregationStrategy"]
