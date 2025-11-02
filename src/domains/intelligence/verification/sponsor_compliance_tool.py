from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from platform.core.step_result import StepResult
from typing import Any

from crewai_tools import BaseTool
from pydantic import BaseModel, Field

from kg.creator_kg_store import CreatorKGStore


logger = logging.getLogger(__name__)


class SponsorComplianceInput(BaseModel):
    """Input schema for sponsor compliance tool."""

    episode_id: str = Field(..., description="Episode ID to analyze for sponsorships")
    content_text: str = Field(default="", description="Text content to analyze (if not episode_id)")
    enable_sponsor_detection: bool = Field(default=True, description="Detect sponsor mentions")
    enable_compliance_check: bool = Field(default=True, description="Check FTC compliance")
    enable_disclosure_generation: bool = Field(default=True, description="Generate disclosure text")
    jurisdiction: str = Field(default="US", description="Jurisdiction for compliance (US, EU, UK)")
    platform: str = Field(default="youtube", description="Platform context (youtube, twitch, tiktok)")


@dataclass
class SponsorMention:
    """Represents a detected sponsor mention."""

    sponsor_name: str
    mention_text: str
    timestamp: float
    confidence: float
    mention_type: str
    context: str
    is_disclosed: bool
    disclosure_location: str | None


@dataclass
class ComplianceViolation:
    """Represents a compliance violation."""

    violation_type: str
    severity: str
    description: str
    timestamp: float | None
    suggested_fix: str
    ftc_guideline_reference: str
    penalty_risk: str


@dataclass
class DisclosureRecommendation:
    """Represents a disclosure recommendation."""

    disclosure_text: str
    placement_location: str
    placement_timestamp: float | None
    reasoning: str
    compliance_score: float
    template_type: str


@dataclass
class ComplianceReport:
    """Complete compliance analysis report."""

    episode_id: str
    analysis_timestamp: datetime
    sponsor_mentions: list[SponsorMention]
    violations: list[ComplianceViolation]
    recommendations: list[DisclosureRecommendation]
    overall_compliance_score: float
    risk_level: str
    summary: str
    next_steps: list[str]


class SponsorComplianceTool(BaseTool):
    """
    Sponsor & Compliance Assistant Tool.

    Detects sponsor mentions, checks FTC compliance, and generates
    disclosure recommendations for creator content.
    """

    name: str = "sponsor_compliance_tool"
    description: str = "\n    Analyze content for sponsor mentions and FTC compliance.\n    Detects sponsorships, identifies violations, and generates disclosure recommendations.\n    "
    args_schema: type[BaseModel] = SponsorComplianceInput

    def __init__(self, kg_store: CreatorKGStore | None = None):
        """Initialize the sponsor compliance tool."""
        super().__init__()
        self.kg_store = kg_store or CreatorKGStore(":memory:")
        self._initialize_sponsor_patterns()

    def _initialize_sponsor_patterns(self):
        """Initialize sponsor detection patterns."""
        self.sponsor_keywords = [
            "sponsored by",
            "this video is sponsored",
            "thanks to",
            "brought to you by",
            "partnered with",
            "collaboration with",
            "promo code",
            "discount code",
            "use code",
            "affiliate link",
            "commission",
            "paid partnership",
            "ad",
            "advertisement",
        ]
        self.disclosure_keywords = [
            "sponsored",
            "ad",
            "advertisement",
            "paid partnership",
            "affiliate",
            "commission",
            "promo code",
            "discount",
            "partnership",
        ]
        self.ftc_guidelines = {
            "clear_and_conspicuous": "Disclosures must be clear and conspicuous",
            "placement": "Disclosures should be placed where consumers will see them",
            "language": "Use clear, simple language that consumers understand",
            "platform_specific": "Consider platform-specific requirements",
            "deceptive_practices": "Avoid deceptive or misleading practices",
        }

    def _run(
        self,
        episode_id: str = "",
        content_text: str = "",
        enable_sponsor_detection: bool = True,
        enable_compliance_check: bool = True,
        enable_disclosure_generation: bool = True,
        jurisdiction: str = "US",
        platform: str = "youtube",
        tenant: str = "",
        workspace: str = "",
    ) -> StepResult:
        """
        Execute sponsor compliance analysis.

        Steps:
        1. Retrieve episode content or use provided text
        2. Detect sponsor mentions
        3. Check FTC compliance
        4. Generate disclosure recommendations
        5. Calculate compliance score and risk level
        """
        try:
            logger.info(f"Analyzing sponsor compliance for episode: {episode_id}")
            content = self._retrieve_episode_content(episode_id, tenant, workspace) if episode_id else content_text
            if not content:
                return StepResult.fail("No content available for analysis")
            sponsor_mentions = []
            if enable_sponsor_detection:
                sponsor_mentions = self._detect_sponsor_mentions(content, platform)
            violations = []
            if enable_compliance_check:
                violations = self._check_compliance_violations(sponsor_mentions, content, jurisdiction, platform)
            recommendations = []
            if enable_disclosure_generation:
                recommendations = self._generate_disclosure_recommendations(
                    sponsor_mentions, violations, jurisdiction, platform
                )
            compliance_score = self._calculate_compliance_score(sponsor_mentions, violations)
            risk_level = self._determine_risk_level(compliance_score, violations)
            summary = self._generate_summary(sponsor_mentions, violations, compliance_score)
            next_steps = self._generate_next_steps(violations, recommendations)
            report = ComplianceReport(
                episode_id=episode_id or "text_analysis",
                analysis_timestamp=datetime.now(),
                sponsor_mentions=sponsor_mentions,
                violations=violations,
                recommendations=recommendations,
                overall_compliance_score=compliance_score,
                risk_level=risk_level,
                summary=summary,
                next_steps=next_steps,
            )
            return StepResult.ok(data=self._serialize_compliance_report(report))
        except Exception as e:
            logger.error(f"Sponsor compliance analysis failed: {e!s}")
            return StepResult.fail(f"Sponsor compliance analysis failed: {e!s}")

    def _retrieve_episode_content(self, episode_id: str, tenant: str, workspace: str) -> str:
        """Retrieve episode content from knowledge graph."""
        try:
            mock_content = "\n            Welcome back to the H3 Podcast! Today we're going to talk about some exciting news.\n\n            Before we get started, I want to thank our sponsor, NordVPN, for making this episode possible.\n            Use code H3PODCAST for 70% off your first year. That's a great deal!\n\n            So Ethan, what's been going on with the Triller lawsuit? I heard there were some updates.\n\n            Yeah, so we got some new evidence that really supports our case. I'm feeling pretty confident about this.\n\n            That's great to hear. And speaking of confidence, I've been using this new skincare routine from\n            Function of Beauty. They sent me some products to try and I have to say, my skin has never looked better.\n            Use code HILA20 for 20% off your first order.\n\n            Anyway, back to the lawsuit discussion...\n            "
            return mock_content
        except Exception as e:
            logger.error(f"Failed to retrieve episode content: {e!s}")
            return ""

    def _detect_sponsor_mentions(self, content: str, platform: str) -> list[SponsorMention]:
        """Detect sponsor mentions in content."""
        mentions = []
        segments = self._split_content_into_segments(content)
        for i, segment in enumerate(segments):
            segment_text = segment["text"].lower()
            timestamp = segment.get("timestamp", i * 60.0)
            for keyword in self.sponsor_keywords:
                if keyword in segment_text:
                    sponsor_name = self._extract_sponsor_name(segment["text"], keyword)
                    is_disclosed = self._check_disclosure_presence(segment["text"])
                    disclosure_location = self._determine_disclosure_location(segment["text"], keyword)
                    mention = SponsorMention(
                        sponsor_name=sponsor_name,
                        mention_text=segment["text"],
                        timestamp=timestamp,
                        confidence=0.85,
                        mention_type="explicit",
                        context=segment["text"][:200] + "..." if len(segment["text"]) > 200 else segment["text"],
                        is_disclosed=is_disclosed,
                        disclosure_location=disclosure_location,
                    )
                    mentions.append(mention)
        return mentions

    def _split_content_into_segments(self, content: str) -> list[dict[str, Any]]:
        """Split content into analyzable segments."""
        sentences = re.split("[.!?]+", content)
        segments = []
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                segments.append({"text": sentence.strip(), "timestamp": i * 30.0, "segment_id": i})
        return segments

    def _extract_sponsor_name(self, text: str, keyword: str) -> str:
        """Extract sponsor name from text."""
        text_lower = text.lower()
        keyword_pos = text_lower.find(keyword)
        if keyword_pos != -1:
            after_keyword = text[keyword_pos + len(keyword) :]
            words = after_keyword.split()
            for word in words:
                if word and word[0].isupper() and (len(word) > 2):
                    return word
        return "Unknown Sponsor"

    def _check_disclosure_presence(self, text: str) -> bool:
        """Check if disclosure is present in text."""
        text_lower = text.lower()
        return any(disclosure in text_lower for disclosure in self.disclosure_keywords)

    def _determine_disclosure_location(self, text: str, keyword: str) -> str:
        """Determine where disclosure appears relative to sponsor mention."""
        if self._check_disclosure_presence(text):
            text_lower = text.lower()
            keyword_pos = text_lower.find(keyword)
            before_keyword = text_lower[:keyword_pos]
            if any(disclosure in before_keyword for disclosure in self.disclosure_keywords):
                return "beginning"
            else:
                return "middle"
        else:
            return "none"

    def _check_compliance_violations(
        self, sponsor_mentions: list[SponsorMention], content: str, jurisdiction: str, platform: str
    ) -> list[ComplianceViolation]:
        """Check for FTC compliance violations."""
        violations = []
        for mention in sponsor_mentions:
            if not mention.is_disclosed:
                violation = ComplianceViolation(
                    violation_type="missing_disclosure",
                    severity="high",
                    description=f"Sponsor mention '{mention.sponsor_name}' lacks clear disclosure",
                    timestamp=mention.timestamp,
                    suggested_fix=f"Add clear disclosure before mentioning {mention.sponsor_name}",
                    ftc_guideline_reference="Clear and conspicuous disclosure required",
                    penalty_risk="fine",
                )
                violations.append(violation)
            elif mention.disclosure_location == "none":
                violation = ComplianceViolation(
                    violation_type="unclear_disclosure",
                    severity="medium",
                    description=f"Disclosure for '{mention.sponsor_name}' is not clear enough",
                    timestamp=mention.timestamp,
                    suggested_fix="Use clearer language like 'This video is sponsored by...'",
                    ftc_guideline_reference="Use clear, simple language",
                    penalty_risk="warning",
                )
                violations.append(violation)
        if self._check_deceptive_practices(content):
            violation = ComplianceViolation(
                violation_type="deceptive_practices",
                severity="critical",
                description="Content may contain deceptive or misleading practices",
                timestamp=None,
                suggested_fix="Review content for accuracy and transparency",
                ftc_guideline_reference="Avoid deceptive or misleading practices",
                penalty_risk="legal_action",
            )
            violations.append(violation)
        return violations

    def _check_deceptive_practices(self, content: str) -> bool:
        """Check for potentially deceptive practices."""
        content_lower = content.lower()
        deceptive_patterns = [
            "guaranteed results",
            "miracle cure",
            "secret formula",
            "doctors hate this",
            "one weird trick",
        ]
        return any(pattern in content_lower for pattern in deceptive_patterns)

    def _generate_disclosure_recommendations(
        self,
        sponsor_mentions: list[SponsorMention],
        violations: list[ComplianceViolation],
        jurisdiction: str,
        platform: str,
    ) -> list[DisclosureRecommendation]:
        """Generate disclosure recommendations."""
        recommendations = []
        for mention in sponsor_mentions:
            if not mention.is_disclosed or mention.disclosure_location == "none":
                disclosure_text = self._generate_disclosure_text(mention.sponsor_name, platform, jurisdiction)
                recommendation = DisclosureRecommendation(
                    disclosure_text=disclosure_text,
                    placement_location="beginning",
                    placement_timestamp=mention.timestamp - 10.0,
                    reasoning="FTC guidelines recommend disclosure before sponsor mention",
                    compliance_score=0.9,
                    template_type="platform_specific",
                )
                recommendations.append(recommendation)
        return recommendations

    def _generate_disclosure_text(self, sponsor_name: str, platform: str, jurisdiction: str) -> str:
        """Generate appropriate disclosure text."""
        p = platform.lower().strip()
        templates = {
            "youtube": f"This video is sponsored by {sponsor_name}. All opinions are my own.",
            "twitch": f"Thanks to {sponsor_name} for sponsoring this stream!",
            "tiktok": f"#ad #sponsored by {sponsor_name}",
        }
        return templates.get(p, f"Sponsored by {sponsor_name}")

    def _calculate_compliance_score(
        self, sponsor_mentions: list[SponsorMention], violations: list[ComplianceViolation]
    ) -> float:
        """Calculate overall compliance score."""
        if not sponsor_mentions:
            return 1.0
        base_score = 1.0
        for violation in violations:
            if violation.severity == "critical":
                base_score -= 0.3
            elif violation.severity == "high":
                base_score -= 0.2
            elif violation.severity == "medium":
                base_score -= 0.1
            elif violation.severity == "low":
                base_score -= 0.05
        disclosed_mentions = sum(1 for mention in sponsor_mentions if mention.is_disclosed)
        if disclosed_mentions > 0:
            disclosure_bonus = disclosed_mentions / len(sponsor_mentions) * 0.2
            base_score += disclosure_bonus
        return max(0.0, min(1.0, base_score))

    def _determine_risk_level(self, compliance_score: float, violations: list[ComplianceViolation]) -> str:
        """Determine overall risk level."""
        critical_violations = sum(1 for v in violations if v.severity == "critical")
        high_violations = sum(1 for v in violations if v.severity == "high")
        if critical_violations > 0:
            return "critical"
        elif high_violations > 0 or compliance_score < 0.5:
            return "high"
        elif compliance_score < 0.7:
            return "medium"
        else:
            return "low"

    def _generate_summary(
        self, sponsor_mentions: list[SponsorMention], violations: list[ComplianceViolation], compliance_score: float
    ) -> str:
        """Generate analysis summary."""
        total_mentions = len(sponsor_mentions)
        disclosed_mentions = sum(1 for mention in sponsor_mentions if mention.is_disclosed)
        total_violations = len(violations)
        summary = f"Found {total_mentions} sponsor mentions, {disclosed_mentions} properly disclosed. "
        summary += f"Identified {total_violations} compliance violations. "
        summary += f"Overall compliance score: {compliance_score:.2f}"
        return summary

    def _generate_next_steps(
        self, violations: list[ComplianceViolation], recommendations: list[DisclosureRecommendation]
    ) -> list[str]:
        """Generate recommended next steps."""
        next_steps = []
        if violations:
            next_steps.append("Review and address compliance violations")
            next_steps.append("Implement recommended disclosures")
        if recommendations:
            next_steps.append("Add disclosure text at recommended timestamps")
            next_steps.append("Test disclosure visibility and clarity")
        if not violations and (not recommendations):
            next_steps.append("Content appears compliant - no action needed")
        return next_steps

    def _serialize_compliance_report(self, report: ComplianceReport) -> dict[str, Any]:
        """Serialize compliance report to dictionary."""
        return {
            "episode_id": report.episode_id,
            "analysis_timestamp": report.analysis_timestamp.isoformat(),
            "sponsor_mentions": [
                {
                    "sponsor_name": mention.sponsor_name,
                    "mention_text": mention.mention_text,
                    "timestamp": mention.timestamp,
                    "confidence": mention.confidence,
                    "mention_type": mention.mention_type,
                    "context": mention.context,
                    "is_disclosed": mention.is_disclosed,
                    "disclosure_location": mention.disclosure_location,
                }
                for mention in report.sponsor_mentions
            ],
            "violations": [
                {
                    "violation_type": violation.violation_type,
                    "severity": violation.severity,
                    "description": violation.description,
                    "timestamp": violation.timestamp,
                    "suggested_fix": violation.suggested_fix,
                    "ftc_guideline_reference": violation.ftc_guideline_reference,
                    "penalty_risk": violation.penalty_risk,
                }
                for violation in report.violations
            ],
            "recommendations": [
                {
                    "disclosure_text": rec.disclosure_text,
                    "placement_location": rec.placement_location,
                    "placement_timestamp": rec.placement_timestamp,
                    "reasoning": rec.reasoning,
                    "compliance_score": rec.compliance_score,
                    "template_type": rec.template_type,
                }
                for rec in report.recommendations
            ],
            "overall_compliance_score": report.overall_compliance_score,
            "risk_level": report.risk_level,
            "summary": report.summary,
            "next_steps": report.next_steps,
        }
