"""Adaptive Decision Tree with fast-path rules and LLM-based reasoning branches.

This module implements an adaptive decision tree that uses fast-path rule-based
decisions for common cases and LLM-based reasoning for complex scenarios.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.step_result import StepResult

from .token_interpreter import InterpretedTokens


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.services.openrouter_service.adaptive_routing import AdaptiveRoutingManager
    from ultimate_discord_intelligence_bot.services.prompt_engine import PromptEngine


logger = logging.getLogger(__name__)


@dataclass
class DecisionNode:
    """A node in the decision tree."""

    node_id: str
    condition: str | None = None  # Fast-path rule or None for LLM branch
    action: str | None = None  # Action to take if condition matches
    confidence: float = 1.0
    requires_llm: bool = False  # Whether this node requires LLM reasoning
    next_nodes: list[str] = field(default_factory=list)  # IDs of next nodes to evaluate


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
        # Root node - start evaluation
        self.nodes["root"] = DecisionNode(
            node_id="root",
            condition="always",
            next_nodes=["check_ignore", "check_priority"],
        )

        # Fast-path: Ignore node
        self.nodes["check_ignore"] = DecisionNode(
            node_id="check_ignore",
            condition="action_type == 'ignore'",
            action="skip_response",
            next_nodes=[],
        )

        # Fast-path: High priority direct mention
        self.nodes["check_priority"] = DecisionNode(
            node_id="check_priority",
            condition="priority >= 8 AND is_direct_mention",
            action="respond_immediately",
            confidence=0.95,
            next_nodes=["llm_evaluate"],
        )

        # Fast-path: Greeting
        self.nodes["check_greeting"] = DecisionNode(
            node_id="check_greeting",
            condition="intent == 'greeting'",
            action="respond_friendly",
            confidence=0.9,
            next_nodes=[],
        )

        # Fast-path: Low priority statement
        self.nodes["check_low_priority"] = DecisionNode(
            node_id="check_low_priority",
            condition="intent == 'statement' AND priority < 3 AND NOT is_direct_mention",
            action="skip_response",
            confidence=0.8,
            next_nodes=[],
        )

        # LLM reasoning branch
        self.nodes["llm_evaluate"] = DecisionNode(
            node_id="llm_evaluate",
            condition=None,  # Always requires LLM
            requires_llm=True,
            next_nodes=[],
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

            # Start at root
            current_node_id = "root"
            visited: set[str] = set()

            while current_node_id and current_node_id not in visited:
                visited.add(current_node_id)
                path.nodes_visited.append(current_node_id)

                node = self.nodes.get(current_node_id)
                if not node:
                    logger.warning(f"Node {current_node_id} not found in tree")
                    break

                # Check if this is a terminal node (has action, no next nodes)
                if node.action and not node.next_nodes:
                    path.final_decision = {
                        "action": node.action,
                        "confidence": node.confidence,
                        "node_id": node.node_id,
                    }
                    path.confidence = node.confidence
                    path.reasoning = f"Fast-path decision via {node.node_id}: {node.action}"
                    return StepResult.ok(data=path)

                # Evaluate condition or use LLM
                if node.requires_llm:
                    # LLM-based reasoning
                    llm_result = await self._llm_reasoning(interpreted_tokens, message_metadata)
                    if llm_result.success:
                        path.used_llm = True
                        decision_data = llm_result.data
                        path.final_decision = decision_data
                        path.confidence = decision_data.get("confidence", 0.7)
                        path.reasoning = decision_data.get("reasoning", "LLM-based reasoning")
                        return StepResult.ok(data=path)
                    else:
                        # LLM failed, use fallback
                        path.final_decision = {
                            "action": "respond",
                            "confidence": 0.6,
                            "node_id": "llm_evaluate_fallback",
                        }
                        path.confidence = 0.6
                        path.reasoning = "LLM reasoning failed, using fallback"
                        return StepResult.ok(data=path)

                # Fast-path rule evaluation
                condition_result = self._evaluate_condition(node.condition, interpreted_tokens, message_metadata)

                if condition_result:
                    # Condition matched - follow to next node or take action
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
                        # Move to next node
                        current_node_id = node.next_nodes[0]  # Simple: take first next node
                        continue

                # Condition didn't match - check other branches or default
                if node.next_nodes:
                    # Try next node in sequence
                    if len(node.next_nodes) > 1:
                        current_node_id = node.next_nodes[1]
                    else:
                        # Only one next node, follow it
                        current_node_id = node.next_nodes[0]
                else:
                    # No next nodes and no action - default decision
                    path.final_decision = {
                        "action": "respond",
                        "confidence": 0.5,
                        "node_id": "default",
                    }
                    path.confidence = 0.5
                    path.reasoning = "Reached terminal node without decision, using default"
                    return StepResult.ok(data=path)

            # Loop prevention fallback
            path.final_decision = {
                "action": "respond",
                "confidence": 0.6,
                "node_id": "fallback",
            }
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
            # Simple condition evaluation
            # In production, would use a proper expression evaluator

            # Extract variables from context
            action_type = tokens.action.action_type
            priority = tokens.action.priority
            intent = tokens.intent.primary_intent
            is_direct_mention = bool(metadata.get("mentions"))

            # Evaluate condition string (simplified evaluation)
            if "action_type == 'ignore'" in condition:
                return action_type == "ignore"
            elif "priority >= 8" in condition and "is_direct_mention" in condition:
                return priority >= 8 and is_direct_mention
            elif "intent == 'greeting'" in condition:
                return intent == "greeting"
            elif (
                "intent == 'statement'" in condition
                and "priority < 3" in condition
                and "NOT is_direct_mention" in condition
            ):
                return intent == "statement" and priority < 3 and not is_direct_mention
            elif "intent == 'statement'" in condition:
                return intent == "statement"

            return False

        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False

    async def _llm_reasoning(self, tokens: InterpretedTokens, metadata: dict[str, Any]) -> StepResult[dict[str, Any]]:
        """Perform LLM-based reasoning for complex cases."""
        try:
            # Build reasoning prompt
            prompt = f"""
You are evaluating a Discord message to determine if an AI bot should respond.

MESSAGE INTENT: {tokens.intent.primary_intent}
ACTION TYPE: {tokens.action.action_type}
PRIORITY: {tokens.action.priority}
URGENCY: {tokens.context.urgency}
SENTIMENT: {tokens.context.sentiment}
IS DIRECT MENTION: {bool(metadata.get('mentions'))}
USER OPTED IN: {metadata.get('user_opt_in_status', False)}

Analyze this message and provide a JSON response with:
- should_respond: boolean
- confidence: float (0.0 to 1.0)
- reasoning: string explaining your decision
- recommended_priority: string ("high", "medium", "low")

Respond with ONLY valid JSON, no additional text.
"""

            # Get model suggestion
            model_suggestion = await self.routing_manager.suggest_model(
                task_type="decision_making",
                context={"complexity": "high", "requires_reasoning": True},
            )

            if not model_suggestion.success:
                return StepResult.fail("Failed to get model for LLM reasoning")

            model = model_suggestion.data.get("model")

            # Generate reasoning using prompt engine (via adapter)
            if hasattr(self.prompt_engine, "generate_response"):
                result = await self.prompt_engine.generate_response(
                    prompt=prompt,
                    model=model,
                    max_tokens=300,
                    temperature=0.3,
                )

                if result.success:
                    import json

                    response_text = result.data

                    # Parse JSON response
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
                        # Fallback parsing
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
                # Prompt engine doesn't have generate_response - fallback
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
