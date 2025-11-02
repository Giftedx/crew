"""Adaptive Decision Tree with fast-path rules and LLM-based reasoning branches.

This module implements an adaptive decision tree that uses fast-path rule-based
decisions for common cases and LLM-based reasoning for complex scenarios.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from platform.core.step_result import StepResult
from typing import TYPE_CHECKING, Any

from .token_interpreter import InterpretedTokens


if TYPE_CHECKING:
    from platform.llm.providers.openrouter.adaptive_routing import AdaptiveRoutingManager
    from platform.prompts.engine import PromptEngine
logger = logging.getLogger(__name__)


@dataclass
class DecisionNode:
    """A node in the decision tree."""

    node_id: str
    condition: str | None = None
    action: str | None = None
    confidence: float = 1.0
    requires_llm: bool = False
    next_nodes: list[str] = field(default_factory=list)


@dataclass
class DecisionPath:
    """Path taken through the decision tree."""

    nodes_visited: list[str]
    final_decision: dict[str, Any]
    confidence: float
    reasoning: str
    used_llm: bool = False


class AdaptiveDecisionTree:
    """Adaptive decision tree with fast-path rules and LLM reasoning."""

    def __init__(self, routing_manager: AdaptiveRoutingManager, prompt_engine: PromptEngine):
        """Initialize decision tree with routing and prompt capabilities."""
        self.routing_manager = routing_manager
        self.prompt_engine = prompt_engine
        self.nodes: dict[str, DecisionNode] = {}
        self._build_tree()

    def _build_tree(self) -> None:
        """Build the decision tree with fast-path rules and LLM branches."""
        self.nodes["root"] = DecisionNode(
            node_id="root", condition="always", next_nodes=["check_ignore", "check_priority"]
        )
        self.nodes["check_ignore"] = DecisionNode(
            node_id="check_ignore", condition="action_type == 'ignore'", action="skip_response", next_nodes=[]
        )
        self.nodes["check_priority"] = DecisionNode(
            node_id="check_priority",
            condition="priority >= 8 AND is_direct_mention",
            action="respond_immediately",
            confidence=0.95,
            next_nodes=["llm_evaluate"],
        )
        self.nodes["check_greeting"] = DecisionNode(
            node_id="check_greeting",
            condition="intent == 'greeting'",
            action="respond_friendly",
            confidence=0.9,
            next_nodes=[],
        )
        self.nodes["check_low_priority"] = DecisionNode(
            node_id="check_low_priority",
            condition="intent == 'statement' AND priority < 3 AND NOT is_direct_mention",
            action="skip_response",
            confidence=0.8,
            next_nodes=[],
        )
        self.nodes["llm_evaluate"] = DecisionNode(
            node_id="llm_evaluate", condition=None, requires_llm=True, next_nodes=[]
        )

    async def evaluate(
        self, interpreted_tokens: InterpretedTokens, message_metadata: dict[str, Any]
    ) -> StepResult[DecisionPath]:
        """Evaluate message using adaptive decision tree.

        Args:
            interpreted_tokens: Interpreted tokens from token interpreter
            message_metadata: Additional message metadata

        Returns:
            StepResult with DecisionPath showing decision and reasoning
        """
        try:
            path = DecisionPath(nodes_visited=[], final_decision={}, confidence=0.0, reasoning="")
            current_node_id = "root"
            visited: set[str] = set()
            while current_node_id and current_node_id not in visited:
                visited.add(current_node_id)
                path.nodes_visited.append(current_node_id)
                node = self.nodes.get(current_node_id)
                if not node:
                    logger.warning(f"Node {current_node_id} not found in tree")
                    break
                if node.action and (not node.next_nodes):
                    path.final_decision = {
                        "action": node.action,
                        "confidence": node.confidence,
                        "node_id": node.node_id,
                    }
                    path.confidence = node.confidence
                    path.reasoning = f"Fast-path decision via {node.node_id}: {node.action}"
                    return StepResult.ok(data=path)
                if node.requires_llm:
                    llm_result = await self._llm_reasoning(interpreted_tokens, message_metadata)
                    if llm_result.success:
                        path.used_llm = True
                        decision_data = llm_result.data
                        path.final_decision = decision_data
                        path.confidence = decision_data.get("confidence", 0.7)
                        path.reasoning = decision_data.get("reasoning", "LLM-based reasoning")
                        return StepResult.ok(data=path)
                    else:
                        path.final_decision = {
                            "action": "respond",
                            "confidence": 0.6,
                            "node_id": "llm_evaluate_fallback",
                        }
                        path.confidence = 0.6
                        path.reasoning = "LLM reasoning failed, using fallback"
                        return StepResult.ok(data=path)
                condition_result = self._evaluate_condition(node.condition, interpreted_tokens, message_metadata)
                if condition_result:
                    if node.action:
                        path.final_decision = {
                            "action": node.action,
                            "confidence": node.confidence,
                            "node_id": node.node_id,
                        }
                        path.confidence = node.confidence
                        path.reasoning = f"Fast-path rule matched at {node.node_id}: {node.action}"
                        return StepResult.ok(data=path)
                    elif node.next_nodes:
                        current_node_id = node.next_nodes[0]
                        continue
                if node.next_nodes:
                    if len(node.next_nodes) > 1:
                        current_node_id = node.next_nodes[1]
                    else:
                        current_node_id = node.next_nodes[0]
                else:
                    path.final_decision = {"action": "respond", "confidence": 0.5, "node_id": "default"}
                    path.confidence = 0.5
                    path.reasoning = "Reached terminal node without decision, using default"
                    return StepResult.ok(data=path)
            path.final_decision = {"action": "respond", "confidence": 0.6, "node_id": "fallback"}
            path.confidence = 0.6
            path.reasoning = "Decision tree evaluation completed with fallback"
            return StepResult.ok(data=path)
        except Exception as e:
            logger.error(f"Decision tree evaluation failed: {e}", exc_info=True)
            return StepResult.fail(f"Decision tree evaluation failed: {e!s}")

    def _evaluate_condition(self, condition: str | None, tokens: InterpretedTokens, metadata: dict[str, Any]) -> bool:
        """Evaluate a fast-path condition against tokens and metadata."""
        if not condition or condition == "always":
            return True
        try:
            action_type = tokens.action.action_type
            priority = tokens.action.priority
            intent = tokens.intent.primary_intent
            is_direct_mention = bool(metadata.get("mentions"))
            if "action_type == 'ignore'" in condition:
                return action_type == "ignore"
            elif "priority >= 8" in condition and "is_direct_mention" in condition:
                return priority >= 8 and is_direct_mention
            elif "intent == 'greeting'" in condition:
                return intent == "greeting"
            elif (
                "intent == 'statement'" in condition
                and "priority < 3" in condition
                and ("NOT is_direct_mention" in condition)
            ):
                return intent == "statement" and priority < 3 and (not is_direct_mention)
            elif "intent == 'statement'" in condition:
                return intent == "statement"
            return False
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False

    async def _llm_reasoning(self, tokens: InterpretedTokens, metadata: dict[str, Any]) -> StepResult[dict[str, Any]]:
        """Perform LLM-based reasoning for complex cases."""
        try:
            prompt = f"\nYou are evaluating a Discord message to determine if an AI bot should respond.\n\nMESSAGE INTENT: {tokens.intent.primary_intent}\nACTION TYPE: {tokens.action.action_type}\nPRIORITY: {tokens.action.priority}\nURGENCY: {tokens.context.urgency}\nSENTIMENT: {tokens.context.sentiment}\nIS DIRECT MENTION: {bool(metadata.get('mentions'))}\nUSER OPTED IN: {metadata.get('user_opt_in_status', False)}\n\nAnalyze this message and provide a JSON response with:\n- should_respond: boolean\n- confidence: float (0.0 to 1.0)\n- reasoning: string explaining your decision\n- recommended_priority: string (\"high\", \"medium\", \"low\")\n\nRespond with ONLY valid JSON, no additional text.\n"
            model_suggestion = await self.routing_manager.suggest_model(
                task_type="decision_making", context={"complexity": "high", "requires_reasoning": True}
            )
            if not model_suggestion.success:
                return StepResult.fail("Failed to get model for LLM reasoning")
            model = model_suggestion.data.get("model")
            if hasattr(self.prompt_engine, "generate_response"):
                result = await self.prompt_engine.generate_response(
                    prompt=prompt, model=model, max_tokens=300, temperature=0.3
                )
                if result.success:
                    import json

                    response_text = result.data
                    try:
                        json_start = response_text.find("{")
                        json_end = response_text.rfind("}") + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = response_text[json_start:json_end]
                            decision_data = json.loads(json_str)
                            return StepResult.ok(
                                data={
                                    "action": "respond" if decision_data.get("should_respond") else "skip",
                                    "confidence": float(decision_data.get("confidence", 0.7)),
                                    "reasoning": str(decision_data.get("reasoning", "LLM reasoning")),
                                    "priority": str(decision_data.get("recommended_priority", "medium")),
                                }
                            )
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse LLM JSON response: {e}")
                        return StepResult.ok(
                            data={
                                "action": "respond",
                                "confidence": 0.7,
                                "reasoning": "LLM reasoning (parse error, using defaults)",
                                "priority": "medium",
                            }
                        )
                return StepResult.fail("LLM reasoning generation failed")
            else:
                return StepResult.ok(
                    data={
                        "action": "respond",
                        "confidence": 0.7,
                        "reasoning": "LLM reasoning unavailable, using default",
                        "priority": "medium",
                    }
                )
        except Exception as e:
            logger.error(f"LLM reasoning failed: {e}", exc_info=True)
            return StepResult.fail(f"LLM reasoning failed: {e!s}")
