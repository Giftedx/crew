"""Detect logical fallacies in text using pattern matching and heuristics.

Enhanced from basic keyword matching to include more sophisticated pattern
recognition for common logical fallacies in debates and arguments.
"""

import re
from typing import ClassVar

from crewai.tools import BaseTool

# ---------------------------------------------------------------------------
# Heuristic threshold constants
# ---------------------------------------------------------------------------
ABSOLUTE_WORD_THRESHOLD = 3
EMOTIONAL_WORD_THRESHOLD = 2
LOADED_QUESTION_CONFIDENCE = 0.6
FALSE_ANALOGY_CONFIDENCE = 0.7
HASTY_GENERALIZATION_CONFIDENCE = 0.6
APPEAL_TO_EMOTION_CONFIDENCE = 0.5


class LogicalFallacyTool(BaseTool):
    name: str = "Logical Fallacy Detector"
    description: str = (
        "Identify logical fallacies in statements using pattern matching and linguistic analysis"
    )

    # Basic keyword-based fallacies
    KEYWORD_FALLACIES: ClassVar[dict[str, list[str]]] = {
        "ad hominem": ["ad hominem", "attack the person", "personal attack"],
        "appeal to authority": ["because i said so", "trust me", "i'm an expert"],
        "bandwagon": ["everyone knows", "everybody does it", "most people", "popular opinion"],
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

    def _run(self, text: str) -> dict:
        # NOTE: Branch count is intentionally high due to sequential heuristic
        # pattern groups. Refactoring into many tiny helper methods would reduce
        # readability; kept as-is with clear section comments.
        findings = []
        confidence_scores = {}

        if not text or not text.strip():
            return {"status": "success", "fallacies": [], "details": {}}

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

        return {
            "status": "success",
            "fallacies": findings,
            "count": len(findings),
            "confidence_scores": confidence_scores,
            "details": self._generate_explanations(findings),
        }

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
            loaded_question_patterns = ["why do you", "how can you", "when will you stop"]
            if any(pattern in text_lower for pattern in loaded_question_patterns):
                fallacies.append(("loaded question", LOADED_QUESTION_CONFIDENCE))

        # Check for false analogies
        if any(
            phrase in text_lower
            for phrase in ["like comparing", "apples to oranges", "different as"]
        ):
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

        return {
            fallacy: explanations.get(fallacy, "Logical fallacy detected") for fallacy in fallacies
        }

    def run(self, *args, **kwargs):
        return self._run(*args, **kwargs)
