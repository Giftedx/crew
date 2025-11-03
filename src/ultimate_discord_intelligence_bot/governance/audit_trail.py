from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from platform.core.step_result import StepResult
from typing import Any


logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """Types of governance decisions that can be audited."""

    INSTRUCTION_EVALUATION = "instruction_evaluation"
    CONTENT_CLASSIFICATION = "content_classification"
    BIAS_DETECTION = "bias_detection"
    REFUSAL_EVENT = "refusal_event"
    GOVERNANCE_DECISION = "governance_decision"
    RED_LINE_CHECK = "red_line_check"
    SAFETY_CLASSIFICATION = "safety_classification"


@dataclass
class GovernanceDecision:
    """Represents a governance decision for audit trail."""

    decision_id: str
    decision_type: DecisionType
    timestamp: float
    user_id: str | None
    tenant: str | None
    workspace: str | None
    input_content: str
    decision_outcome: str
    confidence_score: float | None = None
    reasoning: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AuditTrail:
    """Maintains an audit trail of governance decisions."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.decisions: list[GovernanceDecision] = []
        self.retention_days = 90

    def log_decision(
        self,
        decision_type: DecisionType,
        input_content: str,
        decision_outcome: str,
        user_id: str | None = None,
        tenant: str | None = None,
        workspace: str | None = None,
        confidence_score: float | None = None,
        reasoning: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StepResult:
        """Log a governance decision to the audit trail."""
        if metadata is None:
            metadata = {}
        decision_id = self._generate_decision_id()
        timestamp = time.time()
        decision = GovernanceDecision(
            decision_id=decision_id,
            decision_type=decision_type,
            timestamp=timestamp,
            user_id=user_id,
            tenant=tenant,
            workspace=workspace,
            input_content=input_content,
            decision_outcome=decision_outcome,
            confidence_score=confidence_score,
            reasoning=reasoning,
            metadata=metadata,
        )
        self.decisions.append(decision)
        self.logger.info(
            "Governance decision logged",
            extra={
                "decision_id": decision_id,
                "decision_type": decision_type.value,
                "outcome": decision_outcome,
                "confidence": confidence_score,
            },
        )
        return StepResult.ok(data={"decision_id": decision_id, "decision": decision})

    def get_decisions(
        self,
        decision_type: DecisionType | None = None,
        user_id: str | None = None,
        tenant: str | None = None,
        workspace: str | None = None,
        start_time: float | None = None,
        end_time: float | None = None,
        limit: int = 100,
    ) -> StepResult:
        """Retrieve governance decisions with optional filtering."""
        filtered_decisions = self.decisions
        if decision_type:
            filtered_decisions = [d for d in filtered_decisions if d.decision_type == decision_type]
        if user_id:
            filtered_decisions = [d for d in filtered_decisions if d.user_id == user_id]
        if tenant:
            filtered_decisions = [d for d in filtered_decisions if d.tenant == tenant]
        if workspace:
            filtered_decisions = [d for d in filtered_decisions if d.workspace == workspace]
        if start_time:
            filtered_decisions = [d for d in filtered_decisions if d.timestamp >= start_time]
        if end_time:
            filtered_decisions = [d for d in filtered_decisions if d.timestamp <= end_time]
        filtered_decisions.sort(key=lambda d: d.timestamp, reverse=True)
        filtered_decisions = filtered_decisions[:limit]
        self.logger.info("Retrieved %d governance decisions", len(filtered_decisions))
        return StepResult.ok(data={"decisions": filtered_decisions, "count": len(filtered_decisions)})

    def get_decision_statistics(self, start_time: float | None = None, end_time: float | None = None) -> StepResult:
        """Get statistics about governance decisions."""
        if start_time is None:
            start_time = time.time() - self.retention_days * 24 * 60 * 60
        if end_time is None:
            end_time = time.time()
        filtered_decisions = [d for d in self.decisions if start_time <= d.timestamp <= end_time]
        stats = {
            "total_decisions": len(filtered_decisions),
            "decisions_by_type": {},
            "decisions_by_outcome": {},
            "average_confidence": 0.0,
            "high_confidence_decisions": 0,
            "low_confidence_decisions": 0,
        }
        for decision in filtered_decisions:
            decision_type = decision.decision_type.value
            stats["decisions_by_type"][decision_type] = stats["decisions_by_type"].get(decision_type, 0) + 1
        for decision in filtered_decisions:
            outcome = decision.decision_outcome
            stats["decisions_by_outcome"][outcome] = stats["decisions_by_outcome"].get(outcome, 0) + 1
        confidence_scores = [d.confidence_score for d in filtered_decisions if d.confidence_score is not None]
        if confidence_scores:
            stats["average_confidence"] = sum(confidence_scores) / len(confidence_scores)
            stats["high_confidence_decisions"] = len([c for c in confidence_scores if c >= 0.8])
            stats["low_confidence_decisions"] = len([c for c in confidence_scores if c < 0.5])
        self.logger.info("Generated decision statistics: %s", stats)
        return StepResult.ok(data={"statistics": stats})

    def export_audit_trail(
        self, fmt: str = "json", start_time: float | None = None, end_time: float | None = None
    ) -> StepResult:
        """Export audit trail data in specified format."""
        if start_time is None:
            start_time = time.time() - self.retention_days * 24 * 60 * 60
        if end_time is None:
            end_time = time.time()
        filtered_decisions = [d for d in self.decisions if start_time <= d.timestamp <= end_time]
        if fmt == "json":
            return self._export_json(filtered_decisions)
        elif fmt == "csv":
            return self._export_csv(filtered_decisions)
        else:
            return StepResult.fail(f"Unsupported export format: {fmt}")

    def _export_json(self, decisions: list[GovernanceDecision]) -> StepResult:
        """Export decisions as JSON."""
        try:
            decisions_data = []
            for decision in decisions:
                decision_dict = {
                    "decision_id": decision.decision_id,
                    "decision_type": decision.decision_type.value,
                    "timestamp": decision.timestamp,
                    "user_id": decision.user_id,
                    "tenant": decision.tenant,
                    "workspace": decision.workspace,
                    "input_content": decision.input_content,
                    "decision_outcome": decision.decision_outcome,
                    "confidence_score": decision.confidence_score,
                    "reasoning": decision.reasoning,
                    "metadata": decision.metadata,
                }
                decisions_data.append(decision_dict)
            export_data = {
                "export_timestamp": time.time(),
                "total_decisions": len(decisions_data),
                "decisions": decisions_data,
            }
            self.logger.info("Exported %d decisions as JSON", len(decisions_data))
            return StepResult.ok(data={"format": "json", "data": export_data})
        except Exception as e:
            self.logger.error("Failed to export audit trail as JSON: %s", e)
            return StepResult.fail(f"JSON export failed: {e}")

    def _export_csv(self, decisions: list[GovernanceDecision]) -> StepResult:
        """Export decisions as CSV."""
        try:
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(
                [
                    "decision_id",
                    "decision_type",
                    "timestamp",
                    "user_id",
                    "tenant",
                    "workspace",
                    "input_content",
                    "decision_outcome",
                    "confidence_score",
                    "reasoning",
                ]
            )
            for decision in decisions:
                writer.writerow(
                    [
                        decision.decision_id,
                        decision.decision_type.value,
                        decision.timestamp,
                        decision.user_id,
                        decision.tenant,
                        decision.workspace,
                        decision.input_content,
                        decision.decision_outcome,
                        decision.confidence_score,
                        decision.reasoning,
                    ]
                )
            csv_data = output.getvalue()
            output.close()
            self.logger.info("Exported %d decisions as CSV", len(decisions))
            return StepResult.ok(data={"format": "csv", "data": csv_data})
        except Exception as e:
            self.logger.error("Failed to export audit trail as CSV: %s", e)
            return StepResult.fail(f"CSV export failed: {e}")

    def cleanup_old_decisions(self) -> StepResult:
        """Remove decisions older than the retention period."""
        cutoff_time = time.time() - self.retention_days * 24 * 60 * 60
        original_count = len(self.decisions)
        self.decisions = [d for d in self.decisions if d.timestamp >= cutoff_time]
        removed_count = original_count - len(self.decisions)
        self.logger.info("Cleaned up %d old decisions, %d remaining", removed_count, len(self.decisions))
        return StepResult.ok(data={"removed_count": removed_count, "remaining_count": len(self.decisions)})

    def _generate_decision_id(self) -> str:
        """Generate a unique decision ID."""
        import uuid

        return f"decision_{int(time.time())}_{str(uuid.uuid4())[:8]}"
