"""Detect logical fallacies in text using pattern matching and heuristics.

Enhanced from basic keyword matching to include more sophisticated pattern
recognition for common logical fallacies in debates and arguments.

With ENABLE_INSTRUCTOR=True, uses LLM-based analysis for more accurate detection.
"""

import logging
import re
from typing import ClassVar

from ai.response_models import FallacyAnalysisResult
from ai.structured_outputs import InstructorClientFactory
from core.secure_config import get_config
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Heuristic threshold constants
# ---------------------------------------------------------------------------
ABSOLUTE_WORD_THRESHOLD = 3
EMOTIONAL_WORD_THRESHOLD = 2
LOADED_QUESTION_CONFIDENCE = 0.6
FALSE_ANALOGY_CONFIDENCE = 0.7
HASTY_GENERALIZATION_CONFIDENCE = 0.6
APPEAL_TO_EMOTION_CONFIDENCE = 0.5


class LogicalFallacyTool(BaseTool[StepResult]):
    name: str = "Logical Fallacy Detector"
    description: str = "Identify logical fallacies in statements using pattern matching and linguistic analysis"

    # Basic keyword-based fallacies
    KEYWORD_FALLACIES: ClassVar[dict[str, list[str]]] = {
        "ad hominem": [
            "you're stupid",
            "you're an idiot",
            "you're wrong because you're",
            "shut up",
            "you don't know",
            "personal attack",
            "attack the person",
        ],
        "appeal to authority": [
            "because i said so",
            "trust me",
            "i'm an expert",
            "authorities say",
        ],
        "bandwagon": [
            "everyone knows",
            "everybody does it",
            "most people",
            "popular opinion",
            "everyone believes",
            "everybody thinks",
            "everyone says",
            "most believe",
        ],
        "red herring": ["red herring", "that's not the point", "changing the subject"],
        "straw man": ["straw man", "that's not what i said", "misrepresenting"],
    }

    # Pattern-based fallacies using regex
    PATTERN_FALLACIES: ClassVar[dict[str, list[str]]] = {
        "false dilemma": [
            r"\b(either\s+\w+\s+or\s+\w+|only\s+two\s+options?|black\s+and\s+white)\b",
            r"\b(you\'re\s+(either\s+)?with\s+us\s+or\s+against\s+us)\b",
        ],
        "slippery slope": [
            r"\b(if\s+we\s+\w+.*then.*inevitably|this\s+will\s+lead\s+to|next\s+thing\s+you\s+know)\b",
            r"\b(opens?\s+the\s+floodgates?|slippery\s+slope|where\s+will\s+it\s+end)\b",
            r"\b(if\s+we\s+allow.*world\s+will\s+end|if.*then.*everything\s+will)\b",
            r"\b(this\s+leads?\s+to.*disaster|one\s+step\s+away\s+from)\b",
        ],
        "circular reasoning": [
            r"\b(because\s+it\s+is|it\'s\s+true\s+because|obviously\s+true)\b",
            r"\b\w+\s+is\s+\w+\s+because\s+\w+\s+is\s+\w+\b",
        ],
        "hasty generalization": [
            r"\b(all\s+\w+\s+are|every\s+\w+\s+is|always\s+happens?|never\s+works?)\b",
            r"\b(based\s+on\s+(this\s+)?one\s+(example|case|instance))\b",
        ],
        "appeal to emotion": [
            r"\b(think\s+of\s+the\s+children|won\'t\s+somebody\s+think|how\s+can\s+you\s+be\s+so)\b",
            r"\b(imagine\s+if\s+it\s+were\s+your|you\s+should\s+feel|makes?\s+me\s+(angry|sad))\b",
        ],
        "appeal to ignorance": [
            r"\b(you\s+can\'t\s+prove|no\s+one\s+has\s+shown|absence\s+of\s+evidence)\b",
            r"\b(until\s+proven\s+otherwise|no\s+evidence\s+against)\b",
        ],
        "false cause": [
            r"\b(after\s+this,?\s+therefore\s+because\s+of\s+this|correlation\s+(equals|means)\s+causation)\b",
            r"\b(happened\s+right\s+after|must\s+have\s+caused)\b",
        ],
    }

    # Structural fallacies that require sentence analysis
    STRUCTURAL_PATTERNS: ClassVar[dict[str, list[str]]] = {
        "begging the question": [
            r"\b\w+\s+is\s+\w+\s+because\s+\w+\s+is\s+\w+\b",
            r"\bsince\s+\w+\s+is\s+obviously\s+(true|false|correct)\b",
        ],
        "appeal to consequences": [
            r"\b(if\s+this\s+is\s+true,?\s+then\s+something\s+(bad|terrible)\s+will\s+happen)\b",
            r"\b(we\s+can\'t\s+believe\s+this\s+because\s+it\s+would\s+mean)\b",
        ],
        "tu quoque": [
            r"\b(you\s+do\s+it\s+too|what\s+about\s+when\s+you|hypocrite)\b",
            r"\b(look\s+who\'s\s+talking|pot\s+calling\s+kettle\s+black)\b",
        ],
    }

    def __init__(self) -> None:  # pragma: no cover - trivial init
        super().__init__()
        self._metrics = get_metrics()

    def _run_llm_analysis(self, text: str) -> StepResult:
        """Use LLM with Instructor for structured fallacy detection.

        Args:
            text: Content to analyze for logical fallacies

        Returns:
            StepResult with FallacyAnalysisResult data

        Raises:
            Exception: Any error during LLM call (caught by caller for fallback)
        """
        config = get_config()

        # Create Instructor-wrapped OpenRouter client
        client = InstructorClientFactory.create_openrouter_client()

        # Craft analysis prompt
        prompt = f"""Analyze the following text for logical fallacies. Identify specific instances with quotes, explain why each is a fallacy, assess severity, and provide an overall credibility score.

Text to analyze:
{text}

Be thorough but fair. Not every argument flaw is a fallacy. Focus on clear logical errors that undermine the argument's validity."""

        # Make structured LLM call
        result: FallacyAnalysisResult = client.chat.completions.create(  # type: ignore[call-overload]
            model=config.openrouter_analysis_model or "anthropic/claude-3.5-sonnet",
            response_model=FallacyAnalysisResult,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in critical thinking and logical reasoning. Analyze arguments for fallacies with precision and fairness.",
                },
                {"role": "user", "content": prompt},
            ],
            max_retries=config.instructor_max_retries,
        )

        # Convert FallacyAnalysisResult to StepResult format
        # Build confidence_scores dict from fallacy instances
        confidence_scores = {}
        for fallacy in result.fallacies:
            # Map ConfidenceLevel enum to float
            confidence_map = {"low": 0.3, "medium": 0.6, "high": 0.8, "very_high": 0.95}
            confidence_scores[fallacy.fallacy_type.value] = confidence_map.get(fallacy.confidence.value, 0.5)

        # Build details dict with explanations
        details = {fallacy.fallacy_type.value: fallacy.explanation for fallacy in result.fallacies}

        self._metrics.counter(
            "tool_runs_total",
            labels={"tool": "logical_fallacy", "outcome": "success_llm"},
        ).inc()

        return StepResult.ok(
            fallacies=[f.fallacy_type.value for f in result.fallacies],
            count=len(result.fallacies),
            confidence_scores=confidence_scores,
            details=details,
            # Additional rich data from LLM analysis
            overall_quality=result.overall_quality.value,
            credibility_score=result.credibility_score,
            summary=result.summary,
            recommendations=result.recommendations,
            key_issues=result.key_issues,
            analysis_method="llm_instructor",
        )

    def _run(self, text: str) -> StepResult:
        # NOTE: Branch count is intentionally high due to sequential heuristic
        # pattern groups. Refactoring into many tiny helper methods would reduce
        # readability; kept as-is with clear section comments.

        if not text or not text.strip():
            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": "logical_fallacy", "outcome": "skipped"},
            ).inc()
            return StepResult.skip(
                reason="empty text",
                fallacies=[],
                count=0,
                confidence_scores={},
                details={},
            )

        # Check if Instructor is enabled for LLM-based analysis
        if InstructorClientFactory.is_enabled():
            try:
                return self._run_llm_analysis(text)
            except Exception as exc:
                logger.warning(f"LLM analysis failed, falling back to pattern matching: {exc}")
                # Fall through to pattern matching

        # Pattern-matching fallback
        findings = []
        confidence_scores = {}
        text_lower = text.lower()

        # Check keyword-based fallacies
        for fallacy, keywords in self.KEYWORD_FALLACIES.items():
            matches = [kw for kw in keywords if kw in text_lower]
            if matches:
                findings.append(fallacy)
                confidence_scores[fallacy] = min(len(matches) / len(keywords), 1.0)

        # Check pattern-based fallacies
        for fallacy, patterns in self.PATTERN_FALLACIES.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    if fallacy not in findings:
                        findings.append(fallacy)
                        confidence_scores[fallacy] = 0.8
                    break

        # Check structural fallacies
        for fallacy, patterns in self.STRUCTURAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    if fallacy not in findings:
                        findings.append(fallacy)
                        confidence_scores[fallacy] = 0.7
                    break

        # Additional heuristic checks
        additional_fallacies = self._check_heuristic_fallacies(text)
        for fallacy, confidence in additional_fallacies:
            if fallacy not in findings:
                findings.append(fallacy)
                confidence_scores[fallacy] = confidence

        result_data = {
            "fallacies": findings,
            "count": len(findings),
            "confidence_scores": confidence_scores,
            "details": self._generate_explanations(findings),
            "analysis_method": "pattern_matching",
        }
        outcome = "success"
        self._metrics.counter("tool_runs_total", labels={"tool": "logical_fallacy", "outcome": outcome}).inc()
        return StepResult.ok(**result_data)

    def _check_heuristic_fallacies(self, text: str) -> list[tuple[str, float]]:
        """Check for fallacies using heuristic analysis."""
        fallacies = []
        text_lower = text.lower()

        # Check for excessive use of absolutes
        absolute_words = [
            "all",
            "every",
            "always",
            "never",
            "everyone",
            "nobody",
            "everything",
            "nothing",
        ]
        absolute_count = sum(1 for word in absolute_words if word in text_lower)
        if absolute_count >= ABSOLUTE_WORD_THRESHOLD:
            fallacies.append(("hasty generalization", HASTY_GENERALIZATION_CONFIDENCE))

        # Check for excessive emotional language
        emotional_words = [
            "terrible",
            "horrible",
            "wonderful",
            "amazing",
            "disgusting",
            "outrageous",
        ]
        emotional_count = sum(1 for word in emotional_words if word in text_lower)
        if emotional_count >= EMOTIONAL_WORD_THRESHOLD:
            fallacies.append(("appeal to emotion", APPEAL_TO_EMOTION_CONFIDENCE))

        # Check for loaded questions
        if "?" in text:
            loaded_question_patterns = [
                "why do you",
                "how can you",
                "when will you stop",
            ]
            if any(pattern in text_lower for pattern in loaded_question_patterns):
                fallacies.append(("loaded question", LOADED_QUESTION_CONFIDENCE))

        # Check for false analogies
        if any(phrase in text_lower for phrase in ["like comparing", "apples to oranges", "different as"]):
            fallacies.append(("false analogy", FALSE_ANALOGY_CONFIDENCE))

        return fallacies

    def _generate_explanations(self, fallacies: list[str]) -> dict[str, str]:
        """Generate brief explanations for detected fallacies."""
        explanations = {
            "ad hominem": "Attacking the person making the argument rather than the argument itself",
            "appeal to authority": "Using authority or expertise as the sole basis for accepting a claim",
            "bandwagon": "Arguing something is true because many people believe it",
            "red herring": "Introducing irrelevant information to distract from the main issue",
            "straw man": "Misrepresenting someone's argument to make it easier to attack",
            "false dilemma": "Presenting only two options when more exist",
            "slippery slope": "Arguing that one event will inevitably lead to negative consequences",
            "circular reasoning": "Using the conclusion as evidence for the premise",
            "hasty generalization": "Drawing broad conclusions from limited examples",
            "appeal to emotion": "Using emotional manipulation instead of logical reasoning",
            "appeal to ignorance": "Arguing something is true because it can't be proven false",
            "false cause": "Assuming correlation implies causation",
            "begging the question": "Assuming the conclusion in the premises",
            "appeal to consequences": "Arguing something is false because of undesirable consequences",
            "tu quoque": "Avoiding criticism by turning it back on the accuser",
            "loaded question": "Asking a question that contains controversial assumptions",
            "false analogy": "Making comparisons between fundamentally different things",
        }

        return {fallacy: explanations.get(fallacy, "Logical fallacy detected") for fallacy in fallacies}

    def run(self, text: str) -> StepResult:  # pragma: no cover - thin wrapper
        try:
            return self._run(text)
        except Exception as exc:  # pragma: no cover - unexpected failure path
            self._metrics.counter(
                "tool_runs_total",
                labels={"tool": "logical_fallacy", "outcome": "error"},
            ).inc()
            return StepResult.fail(error=str(exc))
