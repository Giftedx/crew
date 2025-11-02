"""Contextual Token Interpreter for extracting intent, context, and action tokens from messages.

This module provides sophisticated message analysis capabilities that extract structured
semantic tokens representing user intent, conversational context, and required actions.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class IntentToken:
    """Represents user intent extracted from message."""

    primary_intent: str  # question, command, statement, greeting, complaint, request
    confidence: float = 1.0
    sub_intents: list[str] = field(default_factory=list)
    entities: dict[str, Any] = field(default_factory=dict)  # Extracted entities
    keywords: list[str] = field(default_factory=list)


@dataclass
class ContextToken:
    """Represents conversational context extracted from message."""

    topic: str | None = None
    sentiment: str = "neutral"  # positive, negative, neutral, mixed
    urgency: str = "normal"  # low, normal, high, critical
    channel_context: dict[str, Any] = field(default_factory=dict)
    temporal_references: list[str] = field(default_factory=list)  # "yesterday", "next week", etc.
    entity_mentions: list[str] = field(default_factory=list)  # People, places, concepts mentioned


@dataclass
class ActionToken:
    """Represents action that should be taken based on message."""

    action_type: str  # respond, analyze, retrieve, delegate, ignore
    priority: int = 0  # 0-10, higher = more urgent
    requires_knowledge: bool = False
    requires_crewmai: bool = False
    requires_reasoning: bool = False
    suggested_agents: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InterpretedTokens:
    """Complete token interpretation of a message."""

    intent: IntentToken
    context: ContextToken
    action: ActionToken
    raw_message: str
    confidence_score: float = 0.0


class ContextualTokenInterpreter:
    """Sophisticated token interpreter for Discord messages."""

    def __init__(self):
        """Initialize the token interpreter with pattern matching and heuristics."""
        # Intent patterns (regex)
        self.intent_patterns = {
            "question": [
                r"\?+$",  # Ends with question mark
                r"^(who|what|when|where|why|how|is|are|can|could|would|should|do|does|did|will|has|have)\s",  # Question words
                r"\?{1,3}\s*$",  # Multiple question marks
            ],
            "command": [
                r"^(tell|show|find|get|search|look|check|analyze|explain|help|list|create|make|do)\s",
                r"^/(\w+)",  # Slash commands
                r"^!(\w+)",  # Prefix commands
            ],
            "greeting": [
                r"^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening)|sup|yo)\s*[,!.]*",
            ],
            "complaint": [
                r"(don't|doesn't|didn't|wont|won't|cant|can't|problem|issue|broken|error|wrong|bad|terrible|awful)",
                r"(why\s+(is|are|cant|can't|does|do))",
            ],
            "request": [
                r"^(please|could you|can you|would you|i need|i want|i'd like)\s",
                r"(can|could|would)\s+you",
            ],
            "statement": [
                r"^(i|we|they|it|this|that)\s+(think|believe|know|feel|am|are|is)\s",
                r"\.{1,3}\s*$",  # Ends with period(s)
            ],
        }

        # Context extraction patterns
        self.sentiment_indicators = {
            "positive": [
                "good",
                "great",
                "excellent",
                "awesome",
                "amazing",
                "thanks",
                "thank you",
                "love",
                "like",
                "wonderful",
                "fantastic",
                "perfect",
                "best",
                "brilliant",
            ],
            "negative": [
                "bad",
                "terrible",
                "awful",
                "hate",
                "dislike",
                "worst",
                "horrible",
                "wrong",
                "broken",
                "error",
                "problem",
                "issue",
                "stupid",
                "dumb",
            ],
            "urgency": [
                "urgent",
                "asap",
                "immediately",
                "now",
                "quickly",
                "fast",
                "emergency",
                "critical",
                "important",
                "please hurry",
            ],
        }

        # Action triggers
        self.action_triggers = {
            "analyze": ["analyze", "analysis", "examine", "study", "investigate", "research", "review"],
            "retrieve": ["find", "search", "look", "get", "retrieve", "fetch", "show me", "tell me"],
            "delegate": ["help", "can you", "could you", "would you", "please"],
            "ignore": ["nevermind", "nvm", "cancel", "ignore", "skip"],
        }

    def interpret(self, message_content: str, message_metadata: dict[str, Any] | None = None) -> InterpretedTokens:
        """Interpret a message and extract intent, context, and action tokens.

        Args:
            message_content: The message text to interpret
            message_metadata: Additional metadata about the message (optional)

        Returns:
            InterpretedTokens object with complete interpretation
        """
        try:
            message_metadata = message_metadata or {}
            content_lower = message_content.lower().strip()

            # Extract intent
            intent = self._extract_intent(content_lower, message_content)

            # Extract context
            context = self._extract_context(content_lower, message_metadata)

            # Extract action
            action = self._extract_action(content_lower, intent, context, message_metadata)

            # Calculate overall confidence
            confidence = self._calculate_confidence(intent, context, action)

            return InterpretedTokens(
                intent=intent,
                context=context,
                action=action,
                raw_message=message_content,
                confidence_score=confidence,
            )

        except Exception as e:
            logger.error(f"Token interpretation failed: {e}", exc_info=True)
            # Return safe defaults
            return InterpretedTokens(
                intent=IntentToken(primary_intent="statement", confidence=0.0),
                context=ContextToken(),
                action=ActionToken(action_type="ignore", priority=0),
                raw_message=message_content,
                confidence_score=0.0,
            )

    def _extract_intent(self, content_lower: str, original_content: str) -> IntentToken:
        """Extract intent tokens from message content."""
        matched_intents: list[tuple[str, float]] = []

        # Check each intent pattern
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    # Calculate confidence based on match strength
                    confidence = 0.8 if pattern.startswith("^") else 0.6  # Anchored patterns are stronger
                    matched_intents.append((intent_type, confidence))
                    break

        # Determine primary intent
        if matched_intents:
            # Prioritize: question > command > request > greeting > complaint > statement
            priority_order = ["question", "command", "request", "greeting", "complaint", "statement"]
            for p_intent in priority_order:
                for intent_type, conf in matched_intents:
                    if intent_type == p_intent:
                        sub_intents = [i for i, _ in matched_intents if i != intent_type]
                        return IntentToken(
                            primary_intent=intent_type,
                            confidence=conf,
                            sub_intents=sub_intents,
                            keywords=self._extract_keywords(original_content),
                        )
            # Fallback to first matched
            primary, confidence = matched_intents[0]
            return IntentToken(
                primary_intent=primary,
                confidence=confidence,
                sub_intents=[i for i, _ in matched_intents if i != primary],
                keywords=self._extract_keywords(original_content),
            )

        # Default to statement if no pattern matches
        return IntentToken(
            primary_intent="statement",
            confidence=0.5,
            keywords=self._extract_keywords(original_content),
        )

    def _extract_context(self, content_lower: str, metadata: dict[str, Any]) -> ContextToken:
        """Extract context tokens from message."""
        # Extract sentiment
        sentiment = self._detect_sentiment(content_lower)

        # Extract urgency
        urgency = self._detect_urgency(content_lower)

        # Extract topic (simplified - would use NLP in production)
        topic = self._extract_topic(content_lower)

        # Extract temporal references
        temporal_refs = self._extract_temporal_references(content_lower)

        # Extract entity mentions (simplified)
        entity_mentions = self._extract_entities(content_lower, metadata)

        return ContextToken(
            topic=topic,
            sentiment=sentiment,
            urgency=urgency,
            temporal_references=temporal_refs,
            entity_mentions=entity_mentions,
            channel_context=metadata.get("channel_context", {}),
        )

    def _extract_action(
        self, content_lower: str, intent: IntentToken, context: ContextToken, metadata: dict[str, Any]
    ) -> ActionToken:
        """Extract action tokens based on intent and context."""
        # Determine action type based on intent
        action_type = "respond"  # Default

        if intent.primary_intent == "command":
            # Check if it's a specific command that requires CrewAI
            if any(trigger in content_lower for trigger in self.action_triggers["analyze"]):
                action_type = "analyze"
                requires_crewmai = True
                requires_reasoning = True
            elif any(trigger in content_lower for trigger in self.action_triggers["retrieve"]):
                action_type = "retrieve"
                requires_reasoning = True
            else:
                action_type = "respond"
                requires_crewmai = False
                requires_reasoning = False
        elif intent.primary_intent == "question":
            # Questions typically need knowledge retrieval
            action_type = "retrieve"
            requires_knowledge = True
            requires_reasoning = True
            requires_crewmai = False
        elif intent.primary_intent == "greeting":
            action_type = "respond"
            requires_knowledge = False
            requires_crewmai = False
            requires_reasoning = False
        elif any(trigger in content_lower for trigger in self.action_triggers["ignore"]):
            action_type = "ignore"
            requires_knowledge = False
            requires_crewmai = False
            requires_reasoning = False

        # Calculate priority
        priority = self._calculate_priority(intent, context, action_type)

        # Suggest agents if CrewAI needed
        suggested_agents: list[str] = []
        if requires_crewmai:
            if "analyze" in content_lower:
                suggested_agents = ["content_analyst", "fact_checker", "debate_scorer"]
            elif "fact" in content_lower or "verify" in content_lower:
                suggested_agents = ["fact_checker", "verification_director"]

        return ActionToken(
            action_type=action_type,
            priority=priority,
            requires_knowledge=requires_knowledge if "requires_knowledge" in locals() else False,
            requires_crewmai=requires_crewmai if "requires_crewmai" in locals() else False,
            requires_reasoning=requires_reasoning if "requires_reasoning" in locals() else False,
            suggested_agents=suggested_agents,
            metadata={"intent": intent.primary_intent, "urgency": context.urgency},
        )

    def _detect_sentiment(self, content: str) -> str:
        """Detect sentiment from content."""
        positive_count = sum(1 for word in self.sentiment_indicators["positive"] if word in content)
        negative_count = sum(1 for word in self.sentiment_indicators["negative"] if word in content)

        if positive_count > negative_count and positive_count > 0:
            return "positive"
        elif negative_count > positive_count and negative_count > 0:
            return "negative"
        elif positive_count > 0 and negative_count > 0:
            return "mixed"
        else:
            return "neutral"

    def _detect_urgency(self, content: str) -> str:
        """Detect urgency level from content."""
        urgency_words = self.sentiment_indicators["urgency"]
        if any(word in content for word in urgency_words):
            if any(word in content for word in ["critical", "emergency", "urgent"]):
                return "critical"
            elif any(word in content for word in ["asap", "immediately", "now", "hurry"]):
                return "high"
            else:
                return "normal"
        return "normal"

    def _extract_topic(self, content: str) -> str | None:
        """Extract topic from content (simplified)."""
        # In production, this would use NLP/NER
        # For now, return None or simple keyword extraction
        if len(content.split()) > 2:
            # Return first few words as topic indication
            words = content.split()[:5]
            # Filter out common words
            stop_words = {
                "the",
                "a",
                "an",
                "is",
                "are",
                "was",
                "were",
                "be",
                "been",
                "have",
                "has",
                "had",
                "do",
                "does",
                "did",
            }
            topic_words = [w for w in words if w.lower() not in stop_words]
            if topic_words:
                return " ".join(topic_words[:3])
        return None

    def _extract_temporal_references(self, content: str) -> list[str]:
        """Extract temporal references from content."""
        temporal_patterns = [
            r"(yesterday|today|tomorrow|now|later|soon)",
            r"(last|next)\s+(week|month|year|day)",
            r"\d+\s+(days?|weeks?|months?|years?)\s+(ago|from now)",
        ]

        refs: list[str] = []
        for pattern in temporal_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            refs.extend([m if isinstance(m, str) else " ".join(m) for m in matches])

        return list(set(refs))  # Deduplicate

    def _extract_entities(self, content: str, metadata: dict[str, Any]) -> list[str]:
        """Extract entity mentions (simplified)."""
        entities: list[str] = []

        # Extract mentions from metadata if available
        if "mentions" in metadata:
            entities.extend([str(m) for m in metadata["mentions"]])

        # Extract URLs
        url_pattern = r"https?://\S+"
        entities.extend(re.findall(url_pattern, content))

        return entities

    def _extract_keywords(self, content: str) -> list[str]:
        """Extract keywords from content."""
        # Simple keyword extraction (would use NLP in production)
        words = content.lower().split()
        stop_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "should",
            "could",
            "can",
            "may",
            "might",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "to",
            "of",
            "in",
            "on",
            "at",
            "for",
            "with",
            "by",
            "from",
            "and",
            "or",
            "but",
        }
        keywords = [w for w in words if w.lower() not in stop_words and len(w) > 2]
        # Return top 10 keywords
        return keywords[:10]

    def _calculate_priority(self, intent: IntentToken, context: ContextToken, action_type: str) -> int:
        """Calculate action priority (0-10)."""
        priority = 0

        # Base priority by action type
        if action_type == "ignore":
            return 0
        elif action_type == "analyze":
            priority = 8
        elif action_type == "retrieve":
            priority = 6
        elif action_type == "respond":
            priority = 4

        # Boost for urgency
        urgency_boost = {"low": 0, "normal": 0, "high": 2, "critical": 4}
        priority += urgency_boost.get(context.urgency, 0)

        # Boost for direct mention
        if intent.primary_intent in ["command", "question"]:
            priority += 1

        # Cap at 10
        return min(10, priority)

    def _calculate_confidence(self, intent: IntentToken, context: ContextToken, action: ActionToken) -> float:
        """Calculate overall interpretation confidence."""
        # Average confidence from components
        intent_conf = intent.confidence
        action_conf = 0.8 if action.action_type != "ignore" else 1.0  # Action type is usually reliable

        # Context confidence (simplified)
        context_conf = 0.7  # Would be more sophisticated with actual NLP

        return intent_conf * 0.4 + action_conf * 0.4 + context_conf * 0.2
