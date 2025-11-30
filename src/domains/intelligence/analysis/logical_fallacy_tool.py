"""Detect logical fallacies in text using pattern matching and heuristics.

Enhanced from basic keyword matching to include more sophisticated pattern
recognition for common logical fallacies in debates and arguments.

With ENABLE_INSTRUCTOR=True, uses LLM-based analysis for more accurate detection.
"""

import logging
import re
from platform.cache.tool_cache_decorator import cache_tool_result
from typing import ClassVar

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool


logger = logging.getLogger(__name__)
ABSOLUTE_WORD_THRESHOLD = 3
EMOTIONAL_WORD_THRESHOLD = 2
LOADED_QUESTION_CONFIDENCE = 0.6
FALSE_ANALOGY_CONFIDENCE = 0.7
HASTY_GENERALIZATION_CONFIDENCE = 0.6
APPEAL_TO_EMOTION_CONFIDENCE = 0.5


class LogicalFallacyTool(BaseTool[StepResult]):
    """Tool for identifying logical fallacies in text.

    This tool analyzes text input to detect common logical fallacies using a
    combination of keyword matching, regex pattern recognition, and heuristic
    rules. It identifies fallacies such as ad hominem attacks, straw man
    arguments, false dilemmas, and more.

    Attributes:
        name (str): The name of the tool.
        description (str): A brief description of the tool's purpose.
        KEYWORD_FALLACIES (ClassVar[dict]): Dictionary mapping fallacy names to list of keywords.
        PATTERN_FALLACIES (ClassVar[dict]): Dictionary mapping fallacy names to list of regex patterns.
        STRUCTURAL_PATTERNS (ClassVar[dict]): Dictionary mapping fallacy names to structural regex patterns.
    """

    name: str = "Logical Fallacy Detector"
    description: str = "Identify logical fallacies in statements using pattern matching and linguistic analysis"
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
        "appeal to authority": ["because i said so", "trust me", "i'm an expert", "authorities say"],
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
    PATTERN_FALLACIES: ClassVar[dict[str, list[str]]] = {
        "false dilemma": [
            "\\b(either\\s+\\w+\\s+or\\s+\\w+|only\\s+two\\s+options?|black\\s+and\\s+white)\\b",
            "\\b(you\\'re\\s+(either\\s+)?with\\s+us\\s+or\\s+against\\s+us)\\b",
        ],
        "slippery slope": [
            "\\b(if\\s+we\\s+\\w+.*then.*inevitably|this\\s+will\\s+lead\\s+to|next\\s+thing\\s+you\\s+know)\\b",
            "\\b(opens?\\s+the\\s+floodgates?|slippery\\s+slope|where\\s+will\\s+it\\s+end)\\b",
            "\\b(if\\s+we\\s+allow.*world\\s+will\\s+end|if.*then.*everything\\s+will)\\b",
            "\\b(this\\s+leads?\\s+to.*disaster|one\\s+step\\s+away\\s+from)\\b",
        ],
        "circular reasoning": [
            "\\b(because\\s+it\\s+is|it\\'s\\s+true\\s+because|obviously\\s+true)\\b",
            "\\b\\w+\\s+is\\s+\\w+\\s+because\\s+\\w+\\s+is\\s+\\w+\\b",
        ],
        "hasty generalization": [
            "\\b(all\\s+\\w+\\s+are|every\\s+\\w+\\s+is|always\\s+happens?|never\\s+works?)\\b",
            "\\b(based\\s+on\\s+(this\\s+)?one\\s+(example|case|instance))\\b",
        ],
        "appeal to emotion": [
            "\\b(think\\s+of\\s+the\\s+children|won\\'t\\s+somebody\\s+think|how\\s+can\\s+you\\s+be\\s+so)\\b",
            "\\b(imagine\\s+if\\s+it\\s+were\\s+your|you\\s+should\\s+feel|makes?\\s+me\\s+(angry|sad))\\b",
        ],
        "appeal to ignorance": [
            "\\b(you\\s+can\\'t\\s+prove|no\\s+one\\s+has\\s+shown|absence\\s+of\\s+evidence)\\b",
            "\\b(until\\s+proven\\s+otherwise|no\\s+evidence\\s+against)\\b",
        ],
        "false cause": [
            "\\b(after\\s+this,?\\s+therefore\\s+because\\s+of\\s+this|correlation\\s+(equals|means)\\s+causation)\\b",
            "\\b(happened\\s+right\\s+after|must\\s+have\\s+caused)\\b",
        ],
    }
    STRUCTURAL_PATTERNS: ClassVar[dict[str, list[str]]] = {
        "begging the question": [
            "\\b\\w+\\s+is\\s+\\w+\\s+because\\s+\\w+\\s+is\\s+\\w+\\b",
            "\\bsince\\s+\\w+\\s+is\\s+obviously\\s+(true|false|correct)\\b",
        ],
        "appeal to consequences": [
            "\\b(if\\s+this\\s+is\\s+true,?\\s+then\\s+something\\s+(bad|terrible)\\s+will\\s+happen)\\b",
            "\\b(we\\s+can\\'t\\s+believe\\s+this\\s+because\\s+it\\s+would\\s+mean)\\b",
        ],
        "tu quoque": [
            "\\b(you\\s+do\\s+it\\s+too|what\\s+about\\s+when\\s+you|hypocrite)\\b",
            "\\b(look\\s+who\\'s\\s+talking|pot\\s+calling\\s+kettle\\s+black)\\b",
        ],
    }

    def __init__(self) -> None:
        """Initialize the LogicalFallacyTool and set up metrics."""
        super().__init__()
        self._metrics = get_metrics()

    @cache_tool_result(namespace="tool:logical_fallacy", ttl=3600)
    def _run(self, text: str) -> StepResult:
        """Execute the logical fallacy detection analysis.

        Args:
            text (str): The text content to analyze.

        Returns:
            StepResult: A result object containing a list of detected fallacies,
                confidence scores, and detailed explanations. Returns a skipped
                result if the input text is empty or None.
        """
        if not text or not text.strip():
            self._metrics.counter("tool_runs_total", labels={"tool": "logical_fallacy", "outcome": "skipped"}).inc()
            return StepResult.skip(reason="empty text", fallacies=[], count=0, confidence_scores={}, details={})
        findings = []
        confidence_scores = {}
        text_lower = text.lower()
        for fallacy, keywords in self.KEYWORD_FALLACIES.items():
            matches = [kw for kw in keywords if kw in text_lower]
            if matches:
                findings.append(fallacy)
                confidence_scores[fallacy] = min(len(matches) / len(keywords), 1.0)
        for fallacy, patterns in self.PATTERN_FALLACIES.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    if fallacy not in findings:
                        findings.append(fallacy)
                        confidence_scores[fallacy] = 0.8
                    break
        for fallacy, patterns in self.STRUCTURAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    if fallacy not in findings:
                        findings.append(fallacy)
                        confidence_scores[fallacy] = 0.7
                    break
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
        """Check for fallacies using heuristic analysis.

        Analyzes the text for patterns like overuse of absolute words,
        highly emotional language, loaded questions, and potential false analogies.

        Args:
            text (str): The text to analyze.

        Returns:
            list[tuple[str, float]]: A list of tuples, each containing the name
                of a detected fallacy and its confidence score.
        """
        fallacies = []
        text_lower = text.lower()
        absolute_words = ["all", "every", "always", "never", "everyone", "nobody", "everything", "nothing"]
        absolute_count = sum(1 for word in absolute_words if word in text_lower)
        if absolute_count >= ABSOLUTE_WORD_THRESHOLD:
            fallacies.append(("hasty generalization", HASTY_GENERALIZATION_CONFIDENCE))
        emotional_words = ["terrible", "horrible", "wonderful", "amazing", "disgusting", "outrageous"]
        emotional_count = sum(1 for word in emotional_words if word in text_lower)
        if emotional_count >= EMOTIONAL_WORD_THRESHOLD:
            fallacies.append(("appeal to emotion", APPEAL_TO_EMOTION_CONFIDENCE))
        if "?" in text:
            loaded_question_patterns = ["why do you", "how can you", "when will you stop"]
            if any(pattern in text_lower for pattern in loaded_question_patterns):
                fallacies.append(("loaded question", LOADED_QUESTION_CONFIDENCE))
        if any(phrase in text_lower for phrase in ["like comparing", "apples to oranges", "different as"]):
            fallacies.append(("false analogy", FALSE_ANALOGY_CONFIDENCE))
        return fallacies

    def _generate_explanations(self, fallacies: list[str]) -> dict[str, str]:
        """Generate brief explanations for detected fallacies.

        Args:
            fallacies (list[str]): List of detected fallacy names.

        Returns:
            dict[str, str]: A dictionary mapping each fallacy name to its explanation.
        """
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

    def run(self, text: str) -> StepResult:
        """Public interface for running the tool.

        Wraps the internal _run method with error handling and metric recording.

        Args:
            text (str): The text to analyze.

        Returns:
            StepResult: The result of the analysis, or a failure result if an
                exception occurred.
        """
        try:
            return self._run(text)
        except Exception as exc:
            self._metrics.counter("tool_runs_total", labels={"tool": "logical_fallacy", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc))
