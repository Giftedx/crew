"""Political bias detection framework with multi-dimensional analysis.

This module implements OpenAI's bias detection methodology for identifying
political bias, viewpoint diversity, framing techniques, and selective evidence
in content analysis.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


@dataclass
class BiasIndicators:
    """Indicators of political bias in content."""

    partisan_language: float = 0.0  # 0.0 (neutral) to 1.0 (highly partisan)
    ideological_framing: float = 0.0  # 0.0 (neutral) to 1.0 (strongly framed)
    one_sided_evidence: float = 0.0  # 0.0 (balanced) to 1.0 (one-sided)
    strawman_arguments: float = 0.0  # 0.0 (none) to 1.0 (many)
    false_balance: float = 0.0  # 0.0 (none) to 1.0 (excessive)
    omission_bias: float = 0.0  # 0.0 (none) to 1.0 (significant)
    selection_bias: float = 0.0  # 0.0 (none) to 1.0 (strong)
    emotional_manipulation: float = 0.0  # 0.0 (none) to 1.0 (high)

    def overall_bias_score(self) -> float:
        """Calculate overall bias score."""
        scores = [
            self.partisan_language,
            self.ideological_framing,
            self.one_sided_evidence,
            self.strawman_arguments,
            self.false_balance,
            self.omission_bias,
            self.selection_bias,
            self.emotional_manipulation,
        ]
        return sum(scores) / len(scores)


@dataclass
class DiversityScore:
    """Score for viewpoint diversity in content."""

    perspective_count: int = 0
    ideological_span: float = 0.0  # -1.0 (left) to +1.0 (right)
    source_diversity: float = 0.0  # 0.0 (single source) to 1.0 (diverse)
    temporal_diversity: float = 0.0  # 0.0 (single time) to 1.0 (spanning time)
    demographic_diversity: float = 0.0  # 0.0 (homogeneous) to 1.0 (diverse)

    def overall_diversity(self) -> float:
        """Calculate overall diversity score."""
        if self.perspective_count == 0:
            return 0.0

        diversity_factors = [
            self.source_diversity,
            self.temporal_diversity,
            self.demographic_diversity,
        ]
        return sum(diversity_factors) / len(diversity_factors)


@dataclass
class FramingAnalysis:
    """Analysis of framing techniques in content."""

    loaded_language: float = 0.0  # 0.0 (neutral) to 1.0 (highly loaded)
    emotional_appeals: float = 0.0  # 0.0 (rational) to 1.0 (emotional)
    fear_mongering: float = 0.0  # 0.0 (none) to 1.0 (excessive)
    us_vs_them: float = 0.0  # 0.0 (unified) to 1.0 (divisive)
    victim_hero_villain: float = 0.0  # 0.0 (complex) to 1.0 (simplified)

    def overall_framing_bias(self) -> float:
        """Calculate overall framing bias score."""
        scores = [
            self.loaded_language,
            self.emotional_appeals,
            self.fear_mongering,
            self.us_vs_them,
            self.victim_hero_villain,
        ]
        return sum(scores) / len(scores)


@dataclass
class SelectivityScore:
    """Score for evidence selectivity in content."""

    supporting_evidence_ratio: float = 0.0  # 0.0 (balanced) to 1.0 (one-sided)
    opposing_evidence_ratio: float = 0.0  # 0.0 (none) to 1.0 (extensive)
    source_credibility_bias: float = 0.0  # 0.0 (neutral) to 1.0 (biased)
    cherry_picking: float = 0.0  # 0.0 (none) to 1.0 (extensive)
    context_omission: float = 0.0  # 0.0 (none) to 1.0 (significant)

    def overall_selectivity(self) -> float:
        """Calculate overall selectivity score."""
        scores = [
            self.supporting_evidence_ratio,
            self.source_credibility_bias,
            self.cherry_picking,
            self.context_omission,
        ]
        return sum(scores) / len(scores)


class PoliticalBiasDetector(BaseTool[StepResult]):
    """Detector for political bias using OpenAI's methodology.

    This tool implements comprehensive bias detection across multiple dimensions
    including partisan language, ideological framing, evidence balance, and
    viewpoint diversity.
    """

    name: str = "Political Bias Detector"
    description: str = "Detect political bias indicators in content using multi-dimensional analysis"
    model_config: ClassVar[dict[str, str]] = {"extra": "allow"}

    def __init__(self) -> None:
        """Initialize the political bias detector."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._initialize_detection_patterns()

    def _initialize_detection_patterns(self) -> None:
        """Initialize patterns for bias detection."""
        # Partisan language patterns
        self.left_wing_terms = [
            "progressive",
            "liberal",
            "leftist",
            "socialist",
            "democrat",
            "woke",
            "social justice",
            "equity",
            "inclusion",
            "diversity",
        ]

        self.right_wing_terms = [
            "conservative",
            "republican",
            "right-wing",
            "traditional",
            "patriot",
            "freedom",
            "liberty",
            "individual",
            "merit",
            "hard work",
        ]

        # Emotional manipulation patterns
        self.emotional_triggers = [
            "outrage",
            "shocking",
            "devastating",
            "terrifying",
            "appalling",
            "inspiring",
            "heartbreaking",
            "unbelievable",
            "incredible",
        ]

        # Framing patterns
        self.loaded_terms = [
            "radical",
            "extreme",
            "dangerous",
            "threat",
            "crisis",
            "heroic",
            "brave",
            "courageous",
            "noble",
            "righteous",
        ]

        # Strawman patterns
        self.strawman_indicators = [
            "they believe",
            "some people think",
            "the argument goes",
            "it's claimed that",
            "supposedly",
            "allegedly",
        ]

    def detect_bias_indicators(self, content: str) -> StepResult:
        """Detect bias indicators in content.

        Args:
            content: The content to analyze

        Returns:
            StepResult with bias indicators
        """
        try:
            content_lower = content.lower()

            # Analyze partisan language
            partisan_score = self._analyze_partisan_language(content_lower)

            # Analyze ideological framing
            framing_score = self._analyze_ideological_framing(content_lower)

            # Analyze evidence balance
            evidence_score = self._analyze_evidence_balance(content)

            # Analyze strawman arguments
            strawman_score = self._analyze_strawman_arguments(content_lower)

            # Analyze false balance
            false_balance_score = self._analyze_false_balance(content)

            # Analyze omission bias
            omission_score = self._analyze_omission_bias(content)

            # Analyze selection bias
            selection_score = self._analyze_selection_bias(content)

            # Analyze emotional manipulation
            emotional_score = self._analyze_emotional_manipulation(content_lower)

            indicators = BiasIndicators(
                partisan_language=partisan_score,
                ideological_framing=framing_score,
                one_sided_evidence=evidence_score,
                strawman_arguments=strawman_score,
                false_balance=false_balance_score,
                omission_bias=omission_score,
                selection_bias=selection_score,
                emotional_manipulation=emotional_score,
            )

            return StepResult.ok(
                data={
                    "bias_indicators": indicators,
                    "overall_bias_score": indicators.overall_bias_score(),
                    "analysis_complete": True,
                }
            )

        except Exception as e:
            self.logger.error(f"Bias detection failed: {e}")
            return StepResult.fail(f"Bias detection failed: {e}")

    def _analyze_partisan_language(self, content: str) -> float:
        """Analyze partisan language usage."""
        left_count = sum(1 for term in self.left_wing_terms if term in content)
        right_count = sum(1 for term in self.right_wing_terms if term in content)

        total_terms = left_count + right_count
        if total_terms == 0:
            return 0.0

        # Calculate imbalance
        imbalance = abs(left_count - right_count) / total_terms
        return min(imbalance, 1.0)

    def _analyze_ideological_framing(self, content: str) -> float:
        """Analyze ideological framing techniques."""
        # Look for loaded terms and emotional language
        loaded_count = sum(1 for term in self.loaded_terms if term in content)
        emotional_count = sum(1 for term in self.emotional_triggers if term in content)

        total_words = len(content.split())
        if total_words == 0:
            return 0.0

        framing_score = (loaded_count + emotional_count) / total_words
        return min(framing_score * 10, 1.0)  # Scale to 0-1

    def _analyze_evidence_balance(self, content: str) -> float:
        """Analyze evidence balance in content."""
        # Look for supporting vs opposing evidence indicators
        supporting_indicators = ["proves", "demonstrates", "shows", "confirms", "validates"]
        opposing_indicators = ["refutes", "contradicts", "disproves", "challenges", "questions"]

        supporting_count = sum(1 for indicator in supporting_indicators if indicator in content.lower())
        opposing_count = sum(1 for indicator in opposing_indicators if indicator in content.lower())

        total_evidence = supporting_count + opposing_count
        if total_evidence == 0:
            return 0.0

        # Calculate imbalance
        imbalance = abs(supporting_count - opposing_count) / total_evidence
        return min(imbalance, 1.0)

    def _analyze_strawman_arguments(self, content: str) -> float:
        """Analyze strawman argument patterns."""
        strawman_count = sum(1 for indicator in self.strawman_indicators if indicator in content)

        total_sentences = len([s for s in content.split(".") if s.strip()])
        if total_sentences == 0:
            return 0.0

        strawman_ratio = strawman_count / total_sentences
        return min(strawman_ratio * 5, 1.0)  # Scale to 0-1

    def _analyze_false_balance(self, content: str) -> float:
        """Analyze false balance in content."""
        # Look for "both sides" language that may be inappropriate
        false_balance_indicators = [
            "both sides",
            "two sides",
            "different perspectives",
            "some say",
            "others argue",
            "on one hand",
            "on the other hand",
        ]

        false_balance_count = sum(1 for indicator in false_balance_indicators if indicator in content)

        total_sentences = len([s for s in content.split(".") if s.strip()])
        if total_sentences == 0:
            return 0.0

        false_balance_ratio = false_balance_count / total_sentences
        return min(false_balance_ratio * 3, 1.0)  # Scale to 0-1

    def _analyze_omission_bias(self, content: str) -> float:
        """Analyze omission bias in content."""
        # This is a simplified implementation
        # In practice, this would require more sophisticated analysis
        return 0.0  # Placeholder

    def _analyze_selection_bias(self, content: str) -> float:
        """Analyze selection bias in content."""
        # This is a simplified implementation
        # In practice, this would require more sophisticated analysis
        return 0.0  # Placeholder

    def _analyze_emotional_manipulation(self, content: str) -> float:
        """Analyze emotional manipulation in content."""
        emotional_count = sum(1 for term in self.emotional_triggers if term in content)

        total_words = len(content.split())
        if total_words == 0:
            return 0.0

        emotional_ratio = emotional_count / total_words
        return min(emotional_ratio * 20, 1.0)  # Scale to 0-1

    def measure_viewpoint_diversity(self, content: str) -> StepResult:
        """Measure viewpoint diversity in content.

        Args:
            content: The content to analyze

        Returns:
            StepResult with diversity score
        """
        try:
            # Analyze perspective count
            perspective_count = self._count_perspectives(content)

            # Analyze ideological span
            ideological_span = self._analyze_ideological_span(content)

            # Analyze source diversity
            source_diversity = self._analyze_source_diversity(content)

            # Analyze temporal diversity
            temporal_diversity = self._analyze_temporal_diversity(content)

            # Analyze demographic diversity
            demographic_diversity = self._analyze_demographic_diversity(content)

            diversity_score = DiversityScore(
                perspective_count=perspective_count,
                ideological_span=ideological_span,
                source_diversity=source_diversity,
                temporal_diversity=temporal_diversity,
                demographic_diversity=demographic_diversity,
            )

            return StepResult.ok(
                data={
                    "diversity_score": diversity_score,
                    "overall_diversity": diversity_score.overall_diversity(),
                    "analysis_complete": True,
                }
            )

        except Exception as e:
            self.logger.error(f"Viewpoint diversity analysis failed: {e}")
            return StepResult.fail(f"Viewpoint diversity analysis failed: {e}")

    def _count_perspectives(self, content: str) -> int:
        """Count distinct perspectives in content."""
        # Look for perspective indicators
        perspective_indicators = [
            "some believe",
            "others argue",
            "proponents say",
            "critics claim",
            "supporters argue",
            "opponents say",
            "advocates believe",
        ]

        perspective_count = 0
        for indicator in perspective_indicators:
            if indicator in content.lower():
                perspective_count += 1

        return max(perspective_count, 1)  # At least one perspective

    def _analyze_ideological_span(self, content: str) -> float:
        """Analyze ideological span of content."""
        left_count = sum(1 for term in self.left_wing_terms if term in content.lower())
        right_count = sum(1 for term in self.right_wing_terms if term in content.lower())

        total_ideological_terms = left_count + right_count
        if total_ideological_terms == 0:
            return 0.0

        # Calculate span (-1.0 for left, +1.0 for right, 0.0 for balanced)
        if left_count > right_count:
            return -(left_count - right_count) / total_ideological_terms
        elif right_count > left_count:
            return (right_count - left_count) / total_ideological_terms
        else:
            return 0.0

    def _analyze_source_diversity(self, content: str) -> float:
        """Analyze source diversity in content."""
        # Look for source indicators
        source_indicators = [
            "according to",
            "studies show",
            "research indicates",
            "experts say",
            "data suggests",
            "findings show",
        ]

        source_count = sum(1 for indicator in source_indicators if indicator in content.lower())
        return min(source_count / 5, 1.0)  # Scale to 0-1

    def _analyze_temporal_diversity(self, content: str) -> float:
        """Analyze temporal diversity in content."""
        # Look for temporal indicators
        temporal_indicators = [
            "historically",
            "traditionally",
            "recently",
            "currently",
            "in the past",
            "nowadays",
            "modern",
            "contemporary",
        ]

        temporal_count = sum(1 for indicator in temporal_indicators if indicator in content.lower())
        return min(temporal_count / 3, 1.0)  # Scale to 0-1

    def _analyze_demographic_diversity(self, content: str) -> float:
        """Analyze demographic diversity in content."""
        # Look for demographic indicators
        demographic_indicators = [
            "women",
            "men",
            "youth",
            "elderly",
            "minority",
            "majority",
            "urban",
            "rural",
            "educated",
            "working class",
        ]

        demographic_count = sum(1 for indicator in demographic_indicators if indicator in content.lower())
        return min(demographic_count / 5, 1.0)  # Scale to 0-1

    def analyze_framing_techniques(self, content: str) -> StepResult:
        """Analyze framing techniques in content.

        Args:
            content: The content to analyze

        Returns:
            StepResult with framing analysis
        """
        try:
            content_lower = content.lower()

            # Analyze loaded language
            loaded_language = self._analyze_loaded_language(content_lower)

            # Analyze emotional appeals
            emotional_appeals = self._analyze_emotional_appeals(content_lower)

            # Analyze fear mongering
            fear_mongering = self._analyze_fear_mongering(content_lower)

            # Analyze us vs them framing
            us_vs_them = self._analyze_us_vs_them(content_lower)

            # Analyze victim-hero-villain framing
            vhv_framing = self._analyze_victim_hero_villain(content_lower)

            framing_analysis = FramingAnalysis(
                loaded_language=loaded_language,
                emotional_appeals=emotional_appeals,
                fear_mongering=fear_mongering,
                us_vs_them=us_vs_them,
                victim_hero_villain=vhv_framing,
            )

            return StepResult.ok(
                data={
                    "framing_analysis": framing_analysis,
                    "overall_framing_bias": framing_analysis.overall_framing_bias(),
                    "analysis_complete": True,
                }
            )

        except Exception as e:
            self.logger.error(f"Framing analysis failed: {e}")
            return StepResult.fail(f"Framing analysis failed: {e}")

    def _analyze_loaded_language(self, content: str) -> float:
        """Analyze loaded language usage."""
        loaded_count = sum(1 for term in self.loaded_terms if term in content)

        total_words = len(content.split())
        if total_words == 0:
            return 0.0

        loaded_ratio = loaded_count / total_words
        return min(loaded_ratio * 10, 1.0)  # Scale to 0-1

    def _analyze_emotional_appeals(self, content: str) -> float:
        """Analyze emotional appeals in content."""
        emotional_count = sum(1 for term in self.emotional_triggers if term in content)

        total_words = len(content.split())
        if total_words == 0:
            return 0.0

        emotional_ratio = emotional_count / total_words
        return min(emotional_ratio * 20, 1.0)  # Scale to 0-1

    def _analyze_fear_mongering(self, content: str) -> float:
        """Analyze fear mongering in content."""
        fear_indicators = [
            "dangerous",
            "threat",
            "crisis",
            "alarming",
            "disturbing",
            "concerning",
            "worrisome",
            "frightening",
            "terrifying",
        ]

        fear_count = sum(1 for indicator in fear_indicators if indicator in content)

        total_words = len(content.split())
        if total_words == 0:
            return 0.0

        fear_ratio = fear_count / total_words
        return min(fear_ratio * 15, 1.0)  # Scale to 0-1

    def _analyze_us_vs_them(self, content: str) -> float:
        """Analyze us vs them framing."""
        us_them_indicators = [
            "we",
            "us",
            "our",
            "they",
            "them",
            "their",
            "our side",
            "their side",
            "our people",
            "those people",
        ]

        us_them_count = sum(1 for indicator in us_them_indicators if indicator in content)

        total_words = len(content.split())
        if total_words == 0:
            return 0.0

        us_them_ratio = us_them_count / total_words
        return min(us_them_ratio * 5, 1.0)  # Scale to 0-1

    def _analyze_victim_hero_villain(self, content: str) -> float:
        """Analyze victim-hero-villain framing."""
        vhv_indicators = [
            "victim",
            "hero",
            "villain",
            "innocent",
            "guilty",
            "good",
            "evil",
            "righteous",
            "wicked",
            "noble",
            "corrupt",
        ]

        vhv_count = sum(1 for indicator in vhv_indicators if indicator in content)

        total_words = len(content.split())
        if total_words == 0:
            return 0.0

        vhv_ratio = vhv_count / total_words
        return min(vhv_ratio * 8, 1.0)  # Scale to 0-1

    def detect_selective_evidence(self, content: str) -> StepResult:
        """Detect selective evidence in content.

        Args:
            content: The content to analyze

        Returns:
            StepResult with selectivity score
        """
        try:
            # Analyze supporting vs opposing evidence
            supporting_ratio = self._analyze_supporting_evidence(content)
            opposing_ratio = self._analyze_opposing_evidence(content)

            # Analyze source credibility bias
            source_bias = self._analyze_source_credibility_bias(content)

            # Analyze cherry picking
            cherry_picking = self._analyze_cherry_picking(content)

            # Analyze context omission
            context_omission = self._analyze_context_omission(content)

            selectivity_score = SelectivityScore(
                supporting_evidence_ratio=supporting_ratio,
                opposing_evidence_ratio=opposing_ratio,
                source_credibility_bias=source_bias,
                cherry_picking=cherry_picking,
                context_omission=context_omission,
            )

            return StepResult.ok(
                data={
                    "selectivity_score": selectivity_score,
                    "overall_selectivity": selectivity_score.overall_selectivity(),
                    "analysis_complete": True,
                }
            )

        except Exception as e:
            self.logger.error(f"Selective evidence analysis failed: {e}")
            return StepResult.fail(f"Selective evidence analysis failed: {e}")

    def _analyze_supporting_evidence(self, content: str) -> float:
        """Analyze supporting evidence ratio."""
        supporting_indicators = ["proves", "demonstrates", "shows", "confirms", "validates", "supports"]
        opposing_indicators = ["refutes", "contradicts", "disproves", "challenges", "questions", "undermines"]

        supporting_count = sum(1 for indicator in supporting_indicators if indicator in content.lower())
        opposing_count = sum(1 for indicator in opposing_indicators if indicator in content.lower())

        total_evidence = supporting_count + opposing_count
        if total_evidence == 0:
            return 0.0

        return supporting_count / total_evidence

    def _analyze_opposing_evidence(self, content: str) -> float:
        """Analyze opposing evidence ratio."""
        supporting_indicators = ["proves", "demonstrates", "shows", "confirms", "validates", "supports"]
        opposing_indicators = ["refutes", "contradicts", "disproves", "challenges", "questions", "undermines"]

        supporting_count = sum(1 for indicator in supporting_indicators if indicator in content.lower())
        opposing_count = sum(1 for indicator in opposing_indicators if indicator in content.lower())

        total_evidence = supporting_count + opposing_count
        if total_evidence == 0:
            return 0.0

        return opposing_count / total_evidence

    def _analyze_source_credibility_bias(self, content: str) -> float:
        """Analyze source credibility bias."""
        # This is a simplified implementation
        # In practice, this would require more sophisticated analysis
        return 0.0  # Placeholder

    def _analyze_cherry_picking(self, content: str) -> float:
        """Analyze cherry picking of evidence."""
        # Look for selective citation patterns
        cherry_picking_indicators = [
            "studies show",
            "research indicates",
            "data proves",
            "evidence suggests",
            "findings demonstrate",
        ]

        cherry_picking_count = sum(1 for indicator in cherry_picking_indicators if indicator in content.lower())

        total_sentences = len([s for s in content.split(".") if s.strip()])
        if total_sentences == 0:
            return 0.0

        cherry_picking_ratio = cherry_picking_count / total_sentences
        return min(cherry_picking_ratio * 2, 1.0)  # Scale to 0-1

    def _analyze_context_omission(self, content: str) -> float:
        """Analyze context omission in content."""
        # This is a simplified implementation
        # In practice, this would require more sophisticated analysis
        return 0.0  # Placeholder
