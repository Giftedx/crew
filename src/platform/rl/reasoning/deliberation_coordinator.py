"""Deliberation coordinator for multi-agent collaborative reasoning.

Orchestrates agent communication, vote collection, and consensus building
for complex decisions requiring collective intelligence.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics

from .consensus_protocol import AgentVote, ConsensusProtocol, ConsensusResult, VoteAggregationStrategy


if TYPE_CHECKING:
    from platform.rl.agent_messaging.redis_bus import AgentMessage, AgentMessageBus
logger = logging.getLogger(__name__)


@dataclass
class DeliberationRequest:
    """Request for multi-agent deliberation."""

    question: str
    options: list[Any]
    context: dict[str, Any] = field(default_factory=dict)
    requesting_agent_id: str | None = None
    min_agents: int = 3
    timeout_seconds: int = 30
    strategy: VoteAggregationStrategy = VoteAggregationStrategy.CONFIDENCE_WEIGHTED
    deliberation_id: str = field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DeliberationCoordinator:
    """Coordinate multi-agent deliberation sessions.

    Manages:
    - Broadcasting deliberation requests via message bus
    - Collecting agent votes
    - Running consensus protocols
    - Handling timeouts and partial responses
    """

    def __init__(
        self,
        message_bus: AgentMessageBus,
        *,
        default_timeout: int = 30,
        default_strategy: VoteAggregationStrategy = VoteAggregationStrategy.CONFIDENCE_WEIGHTED,
    ):
        """Initialize deliberation coordinator.

        Args:
            message_bus: AgentMessageBus for agent communication.
            default_timeout: Default deliberation timeout in seconds.
            default_strategy: Default consensus strategy.
        """
        self.message_bus = message_bus
        self.default_timeout = default_timeout
        self.default_strategy = default_strategy
        self._active_deliberations: dict[str, DeliberationRequest] = {}
        self._collected_votes: dict[str, list[AgentVote]] = {}
        self._metrics = get_metrics()

    async def request_deliberation(
        self, request: DeliberationRequest, *, tenant_id: str = "default"
    ) -> ConsensusResult:
        """Request multi-agent deliberation and wait for consensus.

        Args:
            request: DeliberationRequest with question and options.
            tenant_id: Tenant context for deliberation.

        Returns:
            ConsensusResult with agent votes and consensus decision.
        """
        from platform.rl.agent_messaging.redis_bus import AgentMessage, MessagePriority, MessageType

        deliberation_id = request.deliberation_id
        self._active_deliberations[deliberation_id] = request
        self._collected_votes[deliberation_id] = []
        logger.info(
            f"Starting deliberation {deliberation_id}: '{request.question}' (min_agents={request.min_agents}, timeout={request.timeout_seconds}s)"
        )
        try:
            message = AgentMessage(
                type=MessageType.REQUEST_REVIEW,
                content=request.question,
                sender_agent_id=request.requesting_agent_id,
                target_agent_id=None,
                priority=MessagePriority.HIGH,
                metadata={
                    "deliberation_id": deliberation_id,
                    "options": request.options,
                    "context": request.context,
                    "min_agents": request.min_agents,
                    "timeout_seconds": request.timeout_seconds,
                },
            )
            await self.message_bus.publish(message, tenant_id=tenant_id)
            self._metrics.counter("deliberations_requested_total", labels={"strategy": request.strategy.value}).inc()
            start_time = asyncio.get_event_loop().time()
            timeout = request.timeout_seconds
            while True:
                current_votes = len(self._collected_votes.get(deliberation_id, []))
                if current_votes >= request.min_agents:
                    logger.info(f"Deliberation {deliberation_id}: received {current_votes} votes (threshold met)")
                    break
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= timeout:
                    logger.warning(
                        f"Deliberation {deliberation_id}: timeout after {elapsed:.1f}s (received {current_votes}/{request.min_agents} votes)"
                    )
                    break
                await asyncio.sleep(0.5)
            votes = self._collected_votes.get(deliberation_id, [])
            if not votes:
                logger.warning(f"Deliberation {deliberation_id}: no votes received")
                return ConsensusResult(
                    decision=None,
                    confidence=0.0,
                    votes=[],
                    strategy=request.strategy,
                    is_consensus=False,
                    reasoning="No agent responses received within timeout",
                )
            protocol = ConsensusProtocol(strategy=request.strategy)
            result = protocol.aggregate_votes(votes)
            logger.info(
                f"Deliberation {deliberation_id}: consensus={result.is_consensus}, decision={result.decision}, confidence={result.confidence:.2f}"
            )
            self._metrics.counter(
                "deliberations_completed_total",
                labels={"strategy": request.strategy.value, "consensus": str(result.is_consensus).lower()},
            ).inc()
            return result
        finally:
            self._active_deliberations.pop(deliberation_id, None)
            self._collected_votes.pop(deliberation_id, None)

    async def submit_vote(
        self,
        deliberation_id: str,
        agent_id: str,
        decision: Any,
        confidence: float,
        reasoning: str = "",
        evidence: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Submit an agent's vote for an active deliberation.

        Args:
            deliberation_id: ID of the deliberation session.
            agent_id: ID of the voting agent.
            decision: The agent's decision/choice.
            confidence: Confidence score (0.0-1.0).
            reasoning: Explanation of the decision.
            evidence: Supporting evidence.
            metadata: Additional metadata (e.g., expertise_score).

        Returns:
            True if vote was accepted, False if deliberation not found.
        """
        if deliberation_id not in self._active_deliberations:
            logger.warning(f"Vote from {agent_id} rejected: deliberation {deliberation_id} not found")
            return False
        vote = AgentVote(
            agent_id=agent_id,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            evidence=evidence or [],
            metadata=metadata or {},
        )
        if deliberation_id not in self._collected_votes:
            self._collected_votes[deliberation_id] = []
        self._collected_votes[deliberation_id].append(vote)
        logger.debug(
            f"Vote recorded for deliberation {deliberation_id}: {agent_id} voted '{decision}' (confidence={confidence:.2f})"
        )
        self._metrics.counter("deliberation_votes_received_total").inc()
        return True

    async def handle_vote_message(self, message: AgentMessage) -> None:
        """Handle incoming vote messages from agents.

        Args:
            message: AgentMessage containing a vote (type=VOTE).
        """
        from platform.rl.agent_messaging.redis_bus import MessageType

        if message.type != MessageType.VOTE:
            return
        deliberation_id = message.metadata.get("deliberation_id")
        if not deliberation_id:
            logger.warning(f"Vote message from {message.sender_agent_id} missing deliberation_id")
            return
        decision = message.metadata.get("decision")
        confidence = message.metadata.get("confidence", 0.5)
        reasoning = message.content
        evidence = message.metadata.get("evidence", [])
        metadata = message.metadata.get("agent_metadata", {})
        await self.submit_vote(
            deliberation_id=deliberation_id,
            agent_id=message.sender_agent_id or "unknown",
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            evidence=evidence,
            metadata=metadata,
        )


__all__ = ["DeliberationCoordinator", "DeliberationRequest"]
