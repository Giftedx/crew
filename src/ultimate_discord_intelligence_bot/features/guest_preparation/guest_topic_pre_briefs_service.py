"""Guest/Topic Pre-Briefs Service for Creator Intelligence.

This module provides automated pre-interview briefing capabilities including:
- Opponent-process summaries of guest arguments
- Weak/strong argument identification
- Likely audience reactions and questions
- Live sidecar prompts for fact-checking during interviews

Features:
- Argument strength analysis and categorization
- Audience reaction prediction based on topic analysis
- Real-time fact-checking prompts for live interviews
- Integration with topic segmentation and claim extraction

Dependencies:
- Topic analysis service for content categorization
- Claim extraction service for argument identification
- Sentiment analysis for reaction prediction
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Literal

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


@dataclass
class ArgumentAnalysis:
    """Analysis of a guest's argument."""

    argument_text: str
    strength_score: float
    strength_category: str
    evidence_quality: float
    logical_coherence: float
    potential_counterarguments: list[str]


@dataclass
class AudienceReactionPrediction:
    """Predicted audience reaction to content."""

    primary_reaction: str
    confidence: float
    likely_questions: list[str]
    engagement_potential: float
    controversy_risk: float


@dataclass
class OpponentProcessSummary:
    """Opponent-process summary of guest's position."""

    guest_position_summary: str
    key_arguments: list[ArgumentAnalysis]
    potential_weaknesses: list[str]
    audience_hooks: list[str]
    fact_check_priorities: list[str]


@dataclass
class InterviewPreparationBrief:
    """Complete pre-interview briefing document."""

    guest_name: str
    topic_overview: str
    opponent_process_summary: OpponentProcessSummary
    audience_reaction_prediction: AudienceReactionPrediction
    interview_strategy: list[str]
    live_fact_check_prompts: list[str]
    key_questions_to_ask: list[str]
    confidence_score: float


@dataclass
class GuestTopicPreBriefsResult:
    """Result of guest/topic pre-briefs generation."""

    interview_brief: InterviewPreparationBrief
    processing_time_ms: float = 0.0


class GuestTopicPreBriefsService:
    """Service for generating pre-interview briefs for guests and topics.

    Usage:
        service = GuestTopicPreBriefsService()
        result = service.generate_interview_brief(guest_content, topic_analysis)
        brief = result.data["interview_brief"]
    """

    def __init__(self, cache_size: int = 1000):
        """Initialize guest preparation service.

        Args:
            cache_size: Maximum number of cached results
        """
        self.cache_size = cache_size
        self._briefs_cache: dict[str, GuestTopicPreBriefsResult] = {}
        self._strength_indicators = {
            "strong": [
                "research shows",
                "studies indicate",
                "data demonstrates",
                "experts agree",
                "evidence suggests",
                "statistics show",
                "proven",
                "established",
                "well-documented",
            ],
            "weak": [
                "I think",
                "I believe",
                "in my opinion",
                "feels like",
                "seems",
                "maybe",
                "possibly",
                "could be",
                "might be",
            ],
        }
        self._controversy_indicators = {
            "high": ["controversial", "debated", "disputed", "contentious", "polarizing"],
            "medium": ["complex", "nuanced", "challenging", "sensitive"],
            "low": ["straightforward", "clear", "obvious", "simple"],
        }

    def generate_interview_brief(
        self,
        guest_content: list[dict[str, Any]],
        topic_analysis: dict[str, Any] | None = None,
        guest_name: str = "Guest",
        interview_style: str = "conversational",
        model: Literal["fast", "balanced", "quality"] = "balanced",
        use_cache: bool = True,
    ) -> StepResult:
        """Generate comprehensive pre-interview briefing.

        Args:
            guest_content: Guest's previous content/statements
            topic_analysis: Topic analysis results (optional)
            guest_name: Name of the guest
            interview_style: Style of interview (conversational, debate, educational)
            model: Model selection
            use_cache: Whether to use briefs cache

        Returns:
            StepResult with interview briefing
        """
        try:
            import time

            start_time = time.time()
            if not guest_content:
                return StepResult.fail("Guest content cannot be empty", status="bad_request")
            if use_cache:
                cache_result = self._check_cache(guest_content, guest_name, interview_style, model)
                if cache_result:
                    logger.info("Interview brief cache hit")
                    return StepResult.ok(
                        data={
                            "interview_brief": cache_result.interview_brief.__dict__,
                            "cache_hit": True,
                            "processing_time_ms": (time.time() - start_time) * 1000,
                        }
                    )
            model_name = self._select_model(model)
            brief_result = self._generate_interview_brief(
                guest_content, topic_analysis, guest_name, interview_style, model_name
            )
            if brief_result:
                if use_cache:
                    self._cache_result(guest_content, guest_name, interview_style, model, brief_result)
                processing_time = (time.time() - start_time) * 1000
                return StepResult.ok(
                    data={
                        "interview_brief": brief_result.__dict__,
                        "cache_hit": False,
                        "processing_time_ms": processing_time,
                    }
                )
            else:
                return StepResult.fail("Brief generation failed", status="retryable")
        except Exception as e:
            logger.error(f"Interview brief generation failed: {e}")
            return StepResult.fail(f"Brief generation failed: {e!s}", status="retryable")

    def generate_live_fact_check_prompts(
        self, guest_statements: list[dict[str, Any]], verification_sources: list[dict[str, Any]] | None = None
    ) -> list[str]:
        """Generate real-time fact-checking prompts for live interviews.

        Args:
            guest_statements: Statements made by guest during interview
            verification_sources: Known reliable sources for fact-checking

        Returns:
            List of fact-checking prompts
        """
        prompts = []
        for statement in guest_statements:
            statement_text = statement.get("text", "")
            confidence = statement.get("confidence", 0.5)
            if 0.3 <= confidence <= 0.8:
                prompts.append(
                    f"Verify: '{statement_text}' - Check against {verification_sources or 'reliable sources'}"
                )
            if self._is_potentially_controversial(statement_text):
                prompts.append(f"Fact-check controversial claim: '{statement_text}'")
        return prompts[:10]

    def predict_audience_reactions(
        self, content_topics: list[str], guest_background: dict[str, Any] | None = None
    ) -> AudienceReactionPrediction:
        """Predict likely audience reactions to content.

        Args:
            content_topics: Topics to be discussed
            guest_background: Guest's background and reputation

        Returns:
            AudienceReactionPrediction
        """
        controversy_score = self._calculate_topic_controversy(content_topics)
        if controversy_score > 0.7:
            primary_reaction = "controversy"
        elif controversy_score > 0.4:
            primary_reaction = "mixed_reactions"
        else:
            primary_reaction = "excitement"
        likely_questions = self._generate_likely_questions(content_topics, guest_background)
        engagement_potential = min(controversy_score + 0.5, 1.0)
        controversy_risk = controversy_score
        return AudienceReactionPrediction(
            primary_reaction=primary_reaction,
            confidence=0.8,
            likely_questions=likely_questions,
            engagement_potential=engagement_potential,
            controversy_risk=controversy_risk,
        )

    def _select_model(self, model_alias: str) -> str:
        """Select actual model configuration from alias.

        Args:
            model_alias: Model alias (fast, balanced, quality)

        Returns:
            Model configuration string
        """
        model_configs = {"fast": "fast_briefing", "balanced": "balanced_briefing", "quality": "quality_briefing"}
        return model_configs.get(model_alias, "balanced_briefing")

    def _generate_interview_brief(
        self,
        guest_content: list[dict[str, Any]],
        topic_analysis: dict[str, Any] | None,
        guest_name: str,
        interview_style: str,
        model_name: str,
    ) -> InterviewPreparationBrief | None:
        """Generate comprehensive interview briefing.

        Args:
            guest_content: Guest's previous content
            topic_analysis: Topic analysis results
            guest_name: Guest name
            interview_style: Interview style
            model_name: Model configuration

        Returns:
            InterviewPreparationBrief or None if generation fails
        """
        try:
            arguments = self._extract_guest_arguments(guest_content)
            opponent_summary = self._generate_opponent_process_summary(arguments, guest_name)
            content_topics = topic_analysis.get("topics", []) if topic_analysis else []
            audience_prediction = self.predict_audience_reactions(content_topics)
            strategy = self._generate_interview_strategy(interview_style, audience_prediction, arguments)
            fact_check_prompts = self.generate_live_fact_check_prompts(
                [{"text": arg.argument_text, "confidence": arg.strength_score} for arg in arguments]
            )
            key_questions = self._generate_key_questions(arguments, audience_prediction)
            confidence = self._calculate_brief_confidence(arguments, audience_prediction)
            return InterviewPreparationBrief(
                guest_name=guest_name,
                topic_overview=self._generate_topic_overview(content_topics),
                opponent_process_summary=opponent_summary,
                audience_reaction_prediction=audience_prediction,
                interview_strategy=strategy,
                live_fact_check_prompts=fact_check_prompts,
                key_questions_to_ask=key_questions,
                confidence_score=confidence,
            )
        except Exception as e:
            logger.error(f"Interview brief generation failed: {e}")
            return None

    def _extract_guest_arguments(self, guest_content: list[dict[str, Any]]) -> list[ArgumentAnalysis]:
        """Extract and analyze arguments from guest content.

        Args:
            guest_content: Guest's previous statements/content

        Returns:
            List of analyzed arguments
        """
        arguments = []
        for content_item in guest_content:
            text = content_item.get("text", "")
            if not text:
                continue
            sentences = re.split("[.!?]+", text)
            sentences = [s.strip() for s in sentences if s.strip() and len(s) > 20]
            for sentence in sentences:
                strength_score = self._calculate_argument_strength(sentence)
                strength_category = self._categorize_argument_strength(strength_score)
                evidence_quality = self._assess_evidence_quality(sentence)
                logical_coherence = self._assess_logical_coherence(sentence)
                counterarguments = self._generate_counterarguments(sentence)
                argument = ArgumentAnalysis(
                    argument_text=sentence,
                    strength_score=strength_score,
                    strength_category=strength_category,
                    evidence_quality=evidence_quality,
                    logical_coherence=logical_coherence,
                    potential_counterarguments=counterarguments,
                )
                arguments.append(argument)
        arguments.sort(key=lambda a: a.strength_score, reverse=True)
        return arguments[:10]

    def _calculate_argument_strength(self, argument_text: str) -> float:
        """Calculate argument strength score.

        Args:
            argument_text: Text of the argument

        Returns:
            Strength score (0.0 to 1.0)
        """
        text_lower = argument_text.lower()
        strong_indicators = sum(1 for indicator in self._strength_indicators["strong"] if indicator in text_lower)
        weak_indicators = sum(1 for indicator in self._strength_indicators["weak"] if indicator in text_lower)
        total_indicators = strong_indicators + weak_indicators
        base_strength = 0.5 if total_indicators == 0 else strong_indicators / total_indicators
        length_factor = min(len(argument_text) / 100, 1.0)
        specificity_factor = self._calculate_specificity_score(argument_text)
        final_strength = base_strength * 0.5 + length_factor * 0.3 + specificity_factor * 0.2
        return min(final_strength, 1.0)

    def _categorize_argument_strength(self, strength_score: float) -> str:
        """Categorize argument strength.

        Args:
            strength_score: Strength score (0.0 to 1.0)

        Returns:
            Strength category
        """
        if strength_score >= 0.7:
            return "strong"
        elif strength_score >= 0.4:
            return "moderate"
        else:
            return "weak"

    def _assess_evidence_quality(self, argument_text: str) -> float:
        """Assess quality of evidence in argument.

        Args:
            argument_text: Argument text

        Returns:
            Evidence quality score (0.0 to 1.0)
        """
        text_lower = argument_text.lower()
        high_quality_evidence = [
            "research shows",
            "studies demonstrate",
            "data indicates",
            "statistics show",
            "experts confirm",
            "clinical trials",
        ]
        medium_quality_evidence = [
            "according to",
            "sources say",
            "reports suggest",
            "commonly believed",
            "generally accepted",
        ]
        low_quality_evidence = ["I think", "I feel", "in my opinion", "people say", "I heard", "I believe"]
        high_count = sum(1 for indicator in high_quality_evidence if indicator in text_lower)
        medium_count = sum(1 for indicator in medium_quality_evidence if indicator in text_lower)
        low_count = sum(1 for indicator in low_quality_evidence if indicator in text_lower)
        total_evidence = high_count + medium_count + low_count
        if total_evidence == 0:
            return 0.5
        evidence_score = (high_count * 1.0 + medium_count * 0.6 + low_count * 0.2) / total_evidence
        return min(evidence_score, 1.0)

    def _assess_logical_coherence(self, argument_text: str) -> float:
        """Assess logical coherence of argument.

        Args:
            argument_text: Argument text

        Returns:
            Logical coherence score (0.0 to 1.0)
        """
        coherence_indicators = [
            "therefore",
            "consequently",
            "because",
            "since",
            "as a result",
            "this means",
            "which implies",
            "leading to",
            "due to",
        ]
        text_lower = argument_text.lower()
        coherence_count = sum(1 for indicator in coherence_indicators if indicator in text_lower)
        base_coherence = min(coherence_count * 0.2, 1.0)
        length_factor = min(len(argument_text) / 50, 1.0)
        return base_coherence * 0.7 + length_factor * 0.3

    def _generate_counterarguments(self, argument_text: str) -> list[str]:
        """Generate potential counterarguments.

        Args:
            argument_text: Original argument

        Returns:
            List of potential counterarguments
        """
        counterarguments = []
        text_lower = argument_text.lower()
        if "always" in text_lower or "never" in text_lower:
            counterarguments.append("There may be exceptions or edge cases")
        if "everyone" in text_lower or "all people" in text_lower:
            counterarguments.append("Different people may have different experiences")
        if "proven" in text_lower or "definite" in text_lower:
            counterarguments.append("The evidence may be preliminary or context-dependent")
        if "obvious" in text_lower or "clear" in text_lower:
            counterarguments.append("The issue may be more complex than it appears")
        return counterarguments[:3]

    def _generate_opponent_process_summary(
        self, arguments: list[ArgumentAnalysis], guest_name: str
    ) -> OpponentProcessSummary:
        """Generate opponent-process summary of guest's position.

        Args:
            arguments: Analyzed arguments
            guest_name: Guest name

        Returns:
            OpponentProcessSummary
        """
        strong_arguments = [arg for arg in arguments if arg.strength_category == "strong"]
        position_summary = self._summarize_position(strong_arguments, guest_name)
        key_arguments = arguments[:5]
        weak_arguments = [arg for arg in arguments if arg.strength_category == "weak"]
        weaknesses = []
        for arg in weak_arguments[:3]:
            weaknesses.extend(arg.potential_counterarguments)
        audience_hooks = self._generate_audience_hooks(arguments)
        fact_check_priorities = self._generate_fact_check_priorities(arguments)
        return OpponentProcessSummary(
            guest_position_summary=position_summary,
            key_arguments=key_arguments,
            potential_weaknesses=weaknesses,
            audience_hooks=audience_hooks,
            fact_check_priorities=fact_check_priorities,
        )

    def _summarize_position(self, strong_arguments: list[ArgumentAnalysis], guest_name: str) -> str:
        """Summarize guest's position from strong arguments.

        Args:
            strong_arguments: Strong arguments from guest
            guest_name: Guest name

        Returns:
            Position summary
        """
        if not strong_arguments:
            return f"{guest_name} has moderate arguments on various topics."
        themes = []
        for arg in strong_arguments[:3]:
            words = arg.argument_text.split()[:5]
            theme = " ".join(words)
            themes.append(theme)
        theme_text = ", ".join(themes)
        return f"{guest_name} strongly advocates for {theme_text}, supported by evidence-based reasoning."

    def _generate_audience_hooks(self, arguments: list[ArgumentAnalysis]) -> list[str]:
        """Generate audience engagement hooks.

        Args:
            arguments: Guest arguments

        Returns:
            List of audience hooks
        """
        hooks = []
        for arg in arguments[:3]:
            if arg.strength_score > 0.7:
                hooks.append(f"Strong evidence: {arg.argument_text[:50]}...")
            elif arg.strength_score > 0.5:
                hooks.append(f"Interesting perspective: {arg.argument_text[:50]}...")
        return hooks[:3]

    def _generate_fact_check_priorities(self, arguments: list[ArgumentAnalysis]) -> list[str]:
        """Generate fact-checking priorities.

        Args:
            arguments: Guest arguments

        Returns:
            List of fact-check priorities
        """
        priorities = []
        for arg in arguments:
            if arg.strength_score > 0.7:
                priorities.append(f"Verify: {arg.argument_text[:60]}...")
        return priorities[:5]

    def _generate_topic_overview(self, content_topics: list[str]) -> str:
        """Generate topic overview.

        Args:
            content_topics: List of topics

        Returns:
            Topic overview string
        """
        if not content_topics:
            return "General discussion topics"
        return f"Discussion will cover: {', '.join(content_topics[:5])}"

    def _generate_interview_strategy(
        self, interview_style: str, audience_prediction: AudienceReactionPrediction, arguments: list[ArgumentAnalysis]
    ) -> list[str]:
        """Generate interview strategy recommendations.

        Args:
            interview_style: Style of interview
            audience_prediction: Predicted audience reactions
            arguments: Guest arguments

        Returns:
            List of strategy recommendations
        """
        strategy = []
        if interview_style == "debate":
            strategy.append("Challenge strong arguments with evidence-based counterpoints")
            strategy.append("Focus on areas where guest's evidence may be weak")
        elif interview_style == "educational":
            strategy.append("Emphasize learning and clarification over confrontation")
            strategy.append("Ask questions that help audience understand complex topics")
        else:
            strategy.append("Maintain friendly, engaging tone")
            strategy.append("Balance agreement with thoughtful questions")
        if audience_prediction.engagement_potential > 0.7:
            strategy.append("Content likely to generate high engagement - lean into popular topics")
        if audience_prediction.controversy_risk > 0.6:
            strategy.append("High controversy risk - prepare for heated discussion")
        return strategy

    def _generate_key_questions(
        self, arguments: list[ArgumentAnalysis], audience_prediction: AudienceReactionPrediction
    ) -> list[str]:
        """Generate key questions to ask during interview.

        Args:
            arguments: Guest arguments
            audience_prediction: Audience reaction predictions

        Returns:
            List of key questions
        """
        questions = []
        for arg in arguments[:3]:
            if arg.strength_score > 0.7:
                questions.append(f"What evidence supports this claim: '{arg.argument_text[:50]}...'?")
        if audience_prediction.likely_questions:
            questions.extend(audience_prediction.likely_questions[:2])
        questions.extend(
            [
                "What would you say to someone who disagrees with this position?",
                "How has your thinking on this topic evolved over time?",
            ]
        )
        return questions[:8]

    def _calculate_brief_confidence(
        self, arguments: list[ArgumentAnalysis], audience_prediction: AudienceReactionPrediction
    ) -> float:
        """Calculate overall confidence in the brief.

        Args:
            arguments: Analyzed arguments
            audience_prediction: Audience predictions

        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not arguments:
            return 0.5
        avg_argument_strength = sum(arg.strength_score for arg in arguments) / len(arguments)
        audience_confidence = audience_prediction.confidence
        overall_confidence = avg_argument_strength * 0.7 + audience_confidence * 0.3
        return min(overall_confidence, 1.0)

    def _calculate_topic_controversy(self, topics: list[str]) -> float:
        """Calculate controversy level of topics.

        Args:
            topics: List of topic strings

        Returns:
            Controversy score (0.0 to 1.0)
        """
        if not topics:
            return 0.3
        controversy_score = 0.0
        for topic in topics:
            topic_lower = topic.lower()
            for level, indicators in self._controversy_indicators.items():
                if any(indicator in topic_lower for indicator in indicators):
                    if level == "high":
                        controversy_score = max(controversy_score, 0.8)
                    elif level == "medium":
                        controversy_score = max(controversy_score, 0.5)
                    else:
                        controversy_score = max(controversy_score, 0.2)
        return controversy_score

    def _generate_likely_questions(self, topics: list[str], guest_background: dict[str, Any] | None) -> list[str]:
        """Generate likely audience questions.

        Args:
            topics: Discussion topics
            guest_background: Guest background information

        Returns:
            List of likely questions
        """
        questions = []
        for topic in topics[:3]:
            questions.append(f"How does {topic} impact everyday people?")
            questions.append(f"What are the biggest challenges in {topic}?")
        questions.extend(
            [
                "What's the most surprising thing you've learned recently?",
                "What advice would you give to someone just starting in this field?",
            ]
        )
        return questions[:6]

    def _is_potentially_controversial(self, statement: str) -> bool:
        """Check if a statement is potentially controversial.

        Args:
            statement: Statement text

        Returns:
            True if potentially controversial
        """
        controversial_indicators = [
            "controversial",
            "debated",
            "disputed",
            "contentious",
            "everyone agrees",
            "obviously",
            "clearly wrong",
        ]
        statement_lower = statement.lower()
        return any(indicator in statement_lower for indicator in controversial_indicators)

    def _calculate_specificity_score(self, text: str) -> float:
        """Calculate specificity score of text.

        Args:
            text: Text to analyze

        Returns:
            Specificity score (0.0 to 1.0)
        """
        concrete_words = [
            "data",
            "research",
            "study",
            "evidence",
            "statistics",
            "specific",
            "detailed",
            "analysis",
            "findings",
        ]
        abstract_words = ["think", "feel", "believe", "maybe", "possibly", "general", "overall", "concept", "idea"]
        text_lower = text.lower()
        concrete_count = sum(1 for word in concrete_words if word in text_lower)
        abstract_count = sum(1 for word in abstract_words if word in text_lower)
        total_indicators = concrete_count + abstract_count
        if total_indicators == 0:
            return 0.5
        return concrete_count / total_indicators

    def _check_cache(
        self, guest_content: list[dict[str, Any]], guest_name: str, interview_style: str, model: str
    ) -> GuestTopicPreBriefsResult | None:
        """Check if interview brief exists in cache.

        Args:
            guest_content: Guest content
            guest_name: Guest name
            interview_style: Interview style
            model: Model alias

        Returns:
            Cached GuestTopicPreBriefsResult or None
        """
        import hashlib

        content_hash = hashlib.sha256(str(guest_content).encode()).hexdigest()[:16]
        cache_key = f"{content_hash}:{guest_name}:{interview_style}:{model}"
        if cache_key in self._briefs_cache:
            return self._briefs_cache[cache_key]
        return None

    def _cache_result(
        self,
        guest_content: list[dict[str, Any]],
        guest_name: str,
        interview_style: str,
        model: str,
        result: GuestTopicPreBriefsResult,
    ) -> None:
        """Cache interview brief result.

        Args:
            guest_content: Guest content
            guest_name: Guest name
            interview_style: Interview style
            model: Model alias
            result: GuestTopicPreBriefsResult to cache
        """
        import hashlib

        content_hash = hashlib.sha256(str(guest_content).encode()).hexdigest()[:16]
        cache_key = f"{content_hash}:{guest_name}:{interview_style}:{model}"
        if len(self._briefs_cache) >= self.cache_size:
            first_key = next(iter(self._briefs_cache))
            del self._briefs_cache[first_key]
        self._briefs_cache[cache_key] = result

    def clear_cache(self) -> StepResult:
        """Clear interview briefs cache.

        Returns:
            StepResult with cache clear status
        """
        cache_size = len(self._briefs_cache)
        self._briefs_cache.clear()
        logger.info(f"Cleared {cache_size} cached interview briefs")
        return StepResult.ok(data={"cleared_entries": cache_size})

    def get_cache_stats(self) -> StepResult:
        """Get interview briefs cache statistics.

        Returns:
            StepResult with cache statistics
        """
        try:
            stats = {
                "total_cached": len(self._briefs_cache),
                "cache_size_limit": self.cache_size,
                "utilization": len(self._briefs_cache) / self.cache_size if self.cache_size > 0 else 0.0,
            }
            return StepResult.ok(data=stats)
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return StepResult.fail(f"Failed to get cache stats: {e!s}")


_pre_briefs_service: GuestTopicPreBriefsService | None = None


def get_guest_topic_pre_briefs_service() -> GuestTopicPreBriefsService:
    """Get singleton guest preparation service instance.

    Returns:
        Initialized GuestTopicPreBriefsService instance
    """
    global _pre_briefs_service
    if _pre_briefs_service is None:
        _pre_briefs_service = GuestTopicPreBriefsService()
    return _pre_briefs_service
