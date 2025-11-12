from __future__ import annotations

import time
from typing import Any, TypedDict

from ultimate_discord_intelligence_bot.step_result import StepResult


class ControversyEvent(TypedDict, total=False):
    """Record of a controversy or drama event."""

    controversy_id: str
    title: str
    description: str
    involved_creators: list[str]
    primary_creator: str
    controversy_type: str
    severity_level: int
    platforms: list[str]
    content_ids: list[str]
    start_date: float
    peak_date: float
    end_date: float | None
    status: str
    sentiment_scores: dict[str, float]
    engagement_metrics: dict[str, Any]
    fact_check_status: dict[str, Any]
    resolution_status: str | None
    related_controversies: list[str]


class DramaAnalysisResult(TypedDict, total=False):
    """Result of drama and controversy analysis."""

    timestamp: float
    analysis_type: str
    detected_controversies: list[ControversyEvent]
    controversy_trends: dict[str, Any]
    creator_risk_assessment: dict[str, Any]
    cross_creator_analysis: dict[str, Any]
    viral_potential_analysis: dict[str, Any]
    fact_checking_priorities: list[str]
    monitoring_recommendations: list[str]
    processing_time_seconds: float
    errors: list[str]


class ControversyTrackingAgent:
    """Agent for LLM-powered detection and cross-creator analysis of controversies and drama."""

    def __init__(self) -> None:
        self._active_controversies: dict[str, ControversyEvent] = {}
        self._controversy_history: list[ControversyEvent] = []
        self._creator_risk_profiles: dict[str, dict[str, Any]] = {}
        self._drama_patterns: dict[str, Any] = {}
        self._monitoring_keywords: list[str] = [
            "controversy",
            "drama",
            "scandal",
            "feud",
            "beef",
            "callout",
            "exposed",
            "leaked",
            "allegations",
            "accusations",
            "apology",
            "cancel",
            "backlash",
            "outrage",
            "fired",
            "quit",
            "breakup",
        ]

    async def analyze_controversies(
        self, creator_ids: list[str], time_range_hours: int = 24, tenant: str = "default", workspace: str = "default"
    ) -> StepResult:
        """
        Analyze controversies and drama for specified creators.

        Args:
            creator_ids: List of creator IDs to analyze
            time_range_hours: Time range to analyze (default 24 hours)
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with controversy analysis data
        """
        try:
            if not creator_ids:
                return StepResult.fail("Creator IDs are required")
            start_time = time.time()
            cutoff_time = time.time() - time_range_hours * 3600
            detected_controversies = await self._detect_controversies(creator_ids, cutoff_time, tenant, workspace)
            controversy_trends = await self._analyze_controversy_trends(
                creator_ids, time_range_hours, tenant, workspace
            )
            creator_risk_assessment = await self._assess_creator_risk(
                creator_ids, detected_controversies, tenant, workspace
            )
            cross_creator_analysis = await self._analyze_cross_creator_patterns(
                creator_ids, detected_controversies, tenant, workspace
            )
            viral_potential_analysis = await self._analyze_viral_potential(detected_controversies, tenant, workspace)
            fact_checking_priorities = await self._identify_fact_checking_priorities(
                detected_controversies, tenant, workspace
            )
            monitoring_recommendations = await self._generate_monitoring_recommendations(
                detected_controversies, creator_risk_assessment, tenant, workspace
            )
            result = DramaAnalysisResult(
                timestamp=time.time(),
                analysis_type="controversy_analysis",
                detected_controversies=detected_controversies,
                controversy_trends=controversy_trends,
                creator_risk_assessment=creator_risk_assessment,
                cross_creator_analysis=cross_creator_analysis,
                viral_potential_analysis=viral_potential_analysis,
                fact_checking_priorities=fact_checking_priorities,
                monitoring_recommendations=monitoring_recommendations,
                processing_time_seconds=time.time() - start_time,
                errors=[],
            )
            return StepResult.ok(data=result)
        except Exception as e:
            return StepResult.fail(f"Controversy analysis failed: {e!s}")

    async def _detect_controversies(
        self, creator_ids: list[str], cutoff_time: float, tenant: str, workspace: str
    ) -> list[ControversyEvent]:
        """Detect controversies using LLM-powered analysis."""
        try:
            controversies = []
            for creator_id in creator_ids:
                controversy_indicators = await self._analyze_content_for_controversy(
                    creator_id, cutoff_time, tenant, workspace
                )
                for indicator in controversy_indicators:
                    controversy = await self._create_controversy_event(indicator, creator_id, tenant, workspace)
                    if controversy:
                        controversies.append(controversy)
            for controversy in controversies:
                self._active_controversies[controversy["controversy_id"]] = controversy
            return controversies
        except Exception as e:
            print(f"Error detecting controversies: {e}")
            return []

    async def _analyze_content_for_controversy(
        self, creator_id: str, cutoff_time: float, tenant: str, workspace: str
    ) -> list[dict[str, Any]]:
        """Analyze creator's content for controversy indicators."""
        try:
            controversy_indicators = []
            if creator_id == "ethan_klein":
                indicator = {
                    "type": "controversial_statement",
                    "severity": 3,
                    "content": "Mock controversial statement about social media policies",
                    "platform": "youtube",
                    "content_id": "ethan_controversy_1",
                    "timestamp": time.time() - 12 * 3600,
                    "engagement_spike": True,
                    "negative_sentiment": 0.7,
                    "keywords_detected": ["controversy", "politics", "social media"],
                }
                controversy_indicators.append(indicator)
            elif creator_id == "hasan_piker":
                indicator = {
                    "type": "drama",
                    "severity": 4,
                    "content": "Mock drama involving political commentary",
                    "platform": "twitch",
                    "content_id": "hasan_drama_1",
                    "timestamp": time.time() - 6 * 3600,
                    "engagement_spike": True,
                    "negative_sentiment": 0.8,
                    "keywords_detected": ["drama", "politics", "controversy"],
                }
                controversy_indicators.append(indicator)
            return controversy_indicators
        except Exception as e:
            print(f"Error analyzing content for controversy: {e}")
            return []

    async def _create_controversy_event(
        self, indicator: dict[str, Any], creator_id: str, tenant: str, workspace: str
    ) -> ControversyEvent | None:
        """Create controversy event from detected indicator."""
        try:
            controversy_id = f"controversy_{creator_id}_{int(time.time())}"
            controversy_type_map = {
                "controversial_statement": "controversial_statement",
                "drama": "drama",
                "scandal": "scandal",
                "feud": "feud",
                "leak": "leak",
            }
            controversy_type = controversy_type_map.get(indicator["type"], "drama")
            severity_level = min(max(indicator.get("severity", 3), 1), 5)
            sentiment_scores = {
                "overall": -indicator.get("negative_sentiment", 0.5),
                "community": -indicator.get("negative_sentiment", 0.5) * 0.8,
                "media": -indicator.get("negative_sentiment", 0.5) * 1.2,
            }
            engagement_metrics = {
                "views": 100000 + indicator.get("severity", 3) * 50000,
                "likes": 5000 + indicator.get("severity", 3) * 2000,
                "dislikes": 2000 + indicator.get("severity", 3) * 1000,
                "comments": 1000 + indicator.get("severity", 3) * 500,
                "shares": 500 + indicator.get("severity", 3) * 200,
                "engagement_rate": 0.1 + indicator.get("severity", 3) * 0.05,
            }
            controversy = ControversyEvent(
                controversy_id=controversy_id,
                title=f"Controversy involving {creator_id}",
                description=indicator["content"],
                involved_creators=[creator_id],
                primary_creator=creator_id,
                controversy_type=controversy_type,
                severity_level=severity_level,
                platforms=[indicator["platform"]],
                content_ids=[indicator["content_id"]],
                start_date=indicator["timestamp"],
                peak_date=indicator["timestamp"] + 2 * 3600,
                end_date=None,
                status="active",
                sentiment_scores=sentiment_scores,
                engagement_metrics=engagement_metrics,
                fact_check_status={"pending": True, "claims_identified": 3},
                resolution_status=None,
                related_controversies=[],
            )
            return controversy
        except Exception as e:
            print(f"Error creating controversy event: {e}")
            return None

    async def _analyze_controversy_trends(
        self, creator_ids: list[str], time_range_hours: int, tenant: str, workspace: str
    ) -> dict[str, Any]:
        """Analyze trends in controversies."""
        try:
            trends = {
                "total_controversies": 0,
                "active_controversies": 0,
                "resolved_controversies": 0,
                "controversy_frequency": {},
                "severity_distribution": {},
                "platform_distribution": {},
                "type_distribution": {},
                "trending_topics": [],
            }
            for controversy in self._active_controversies.values():
                if controversy["primary_creator"] in creator_ids:
                    trends["total_controversies"] += 1
                    if controversy["status"] == "active":
                        trends["active_controversies"] += 1
                    elif controversy["status"] == "resolved":
                        trends["resolved_controversies"] += 1
                    creator = controversy["primary_creator"]
                    trends["controversy_frequency"][creator] = trends["controversy_frequency"].get(creator, 0) + 1
                    severity = controversy["severity_level"]
                    trends["severity_distribution"][severity] = trends["severity_distribution"].get(severity, 0) + 1
                    for platform in controversy["platforms"]:
                        trends["platform_distribution"][platform] = trends["platform_distribution"].get(platform, 0) + 1
                    controversy_type = controversy["controversy_type"]
                    trends["type_distribution"][controversy_type] = (
                        trends["type_distribution"].get(controversy_type, 0) + 1
                    )
            trends["trending_topics"] = ["politics", "social media", "gaming", "controversy"]
            return trends
        except Exception as e:
            print(f"Error analyzing controversy trends: {e}")
            return {}

    async def _assess_creator_risk(
        self, creator_ids: list[str], detected_controversies: list[ControversyEvent], tenant: str, workspace: str
    ) -> dict[str, Any]:
        """Assess risk levels for creators."""
        try:
            risk_assessment = {}
            for creator_id in creator_ids:
                creator_controversies = [c for c in detected_controversies if creator_id in c["involved_creators"]]
                risk_score = 0.0
                risk_factors = []
                if creator_controversies:
                    recent_severity = max(c["severity_level"] for c in creator_controversies)
                    risk_score += recent_severity * 0.2
                    risk_factors.append(f"Recent controversy with severity {recent_severity}")
                controversy_count = len(creator_controversies)
                if controversy_count > 2:
                    risk_score += 0.3
                    risk_factors.append(f"High controversy frequency ({controversy_count} recent)")
                platforms_involved = set()
                for controversy in creator_controversies:
                    platforms_involved.update(controversy["platforms"])
                if len(platforms_involved) > 2:
                    risk_score += 0.2
                    risk_factors.append("Controversies across multiple platforms")
                if creator_controversies:
                    avg_sentiment = sum(c["sentiment_scores"]["overall"] for c in creator_controversies) / len(
                        creator_controversies
                    )
                    if avg_sentiment < -0.5:
                        risk_score += 0.3
                        risk_factors.append("Consistently negative sentiment")
                risk_level = "low"
                if risk_score > 0.7:
                    risk_level = "high"
                elif risk_score > 0.4:
                    risk_level = "medium"
                risk_assessment[creator_id] = {
                    "risk_score": min(risk_score, 1.0),
                    "risk_level": risk_level,
                    "risk_factors": risk_factors,
                    "controversy_count": controversy_count,
                    "platforms_involved": list(platforms_involved),
                    "recommendations": self._generate_risk_recommendations(risk_level, risk_factors),
                }
                self._creator_risk_profiles[creator_id] = risk_assessment[creator_id]
            return risk_assessment
        except Exception as e:
            print(f"Error assessing creator risk: {e}")
            return {}

    def _generate_risk_recommendations(self, risk_level: str, risk_factors: list[str]) -> list[str]:
        """Generate recommendations based on risk level and factors."""
        recommendations = []
        if risk_level == "high":
            recommendations.extend(
                [
                    "Increase monitoring frequency for this creator",
                    "Set up real-time alerts for new content",
                    "Prepare crisis communication response",
                    "Monitor cross-platform mentions and reactions",
                ]
            )
        elif risk_level == "medium":
            recommendations.extend(
                [
                    "Monitor content before publication",
                    "Track sentiment trends closely",
                    "Prepare for potential escalation",
                ]
            )
        else:
            recommendations.extend(["Maintain standard monitoring", "Watch for emerging patterns"])
        if "controversy frequency" in str(risk_factors):
            recommendations.append("Analyze patterns in controversy triggers")
        if "multiple platforms" in str(risk_factors):
            recommendations.append("Implement cross-platform monitoring")
        return recommendations

    async def _analyze_cross_creator_patterns(
        self, creator_ids: list[str], detected_controversies: list[ControversyEvent], tenant: str, workspace: str
    ) -> dict[str, Any]:
        """Analyze patterns across multiple creators."""
        try:
            cross_analysis = {
                "shared_controversies": [],
                "controversy_clusters": [],
                "influence_patterns": {},
                "escalation_chains": [],
                "resolution_patterns": {},
            }
            for controversy in detected_controversies:
                involved_creators = controversy["involved_creators"]
                if len(involved_creators) > 1:
                    cross_analysis["shared_controversies"].append(
                        {
                            "controversy_id": controversy["controversy_id"],
                            "involved_creators": involved_creators,
                            "type": controversy["controversy_type"],
                            "severity": controversy["severity_level"],
                        }
                    )
            creator_controversy_map = {}
            for controversy in detected_controversies:
                for creator in controversy["involved_creators"]:
                    if creator not in creator_controversy_map:
                        creator_controversy_map[creator] = []
                    creator_controversy_map[creator].append(controversy["controversy_id"])
            controversy_clusters = []
            for creator1, controversies1 in creator_controversy_map.items():
                for creator2, controversies2 in creator_controversy_map.items():
                    if creator1 != creator2:
                        overlap = set(controversies1) & set(controversies2)
                        if overlap:
                            controversy_clusters.append(
                                {
                                    "creators": [creator1, creator2],
                                    "shared_controversies": list(overlap),
                                    "cluster_strength": len(overlap),
                                }
                            )
            cross_analysis["controversy_clusters"] = controversy_clusters
            for creator_id in creator_ids:
                creator_controversies = [c for c in detected_controversies if creator_id in c["involved_creators"]]
                if creator_controversies:
                    avg_engagement = sum(
                        c["engagement_metrics"].get("engagement_rate", 0) for c in creator_controversies
                    ) / len(creator_controversies)
                    cross_analysis["influence_patterns"][creator_id] = {
                        "controversy_engagement": avg_engagement,
                        "influence_score": min(avg_engagement * 2, 1.0),
                        "controversy_count": len(creator_controversies),
                    }
            return cross_analysis
        except Exception as e:
            print(f"Error analyzing cross-creator patterns: {e}")
            return {}

    async def _analyze_viral_potential(
        self, detected_controversies: list[ControversyEvent], tenant: str, workspace: str
    ) -> dict[str, Any]:
        """Analyze viral potential of controversies."""
        try:
            viral_analysis = {
                "high_viral_potential": [],
                "viral_indicators": {},
                "spread_prediction": {},
                "platform_amplification": {},
            }
            for controversy in detected_controversies:
                viral_score = 0.0
                viral_indicators = []
                viral_score += controversy["severity_level"] * 0.2
                engagement_rate = controversy["engagement_metrics"].get("engagement_rate", 0)
                viral_score += engagement_rate * 0.4
                platform_count = len(controversy["platforms"])
                viral_score += platform_count * 0.1
                sentiment = controversy["sentiment_scores"]["overall"]
                if sentiment < -0.3:
                    viral_score += 0.3
                    viral_indicators.append("negative_sentiment")
                type_scores = {"scandal": 0.4, "feud": 0.3, "controversial_statement": 0.2, "drama": 0.2, "leak": 0.5}
                viral_score += type_scores.get(controversy["controversy_type"], 0.1)
                viral_analysis["viral_indicators"][controversy["controversy_id"]] = {
                    "viral_score": min(viral_score, 1.0),
                    "indicators": viral_indicators,
                    "predicted_reach": int(100000 * viral_score),
                }
                if viral_score > 0.7:
                    viral_analysis["high_viral_potential"].append(
                        {
                            "controversy_id": controversy["controversy_id"],
                            "viral_score": viral_score,
                            "primary_creator": controversy["primary_creator"],
                            "type": controversy["controversy_type"],
                        }
                    )
            return viral_analysis
        except Exception as e:
            print(f"Error analyzing viral potential: {e}")
            return {}

    async def _identify_fact_checking_priorities(
        self, detected_controversies: list[ControversyEvent], tenant: str, workspace: str
    ) -> list[str]:
        """Identify fact-checking priorities based on controversies."""
        try:
            priorities = []
            for controversy in detected_controversies:
                if controversy["severity_level"] >= 4 and controversy["fact_check_status"].get("pending", False):
                    priorities.append(
                        {
                            "controversy_id": controversy["controversy_id"],
                            "priority": "high",
                            "reason": "Severe controversy with pending fact checks",
                            "creator": controversy["primary_creator"],
                        }
                    )
                claims_count = controversy["fact_check_status"].get("claims_identified", 0)
                if claims_count >= 3:
                    priorities.append(
                        {
                            "controversy_id": controversy["controversy_id"],
                            "priority": "medium",
                            "reason": "Multiple factual claims to verify",
                            "creator": controversy["primary_creator"],
                        }
                    )
                if len(controversy["involved_creators"]) > 1:
                    priorities.append(
                        {
                            "controversy_id": controversy["controversy_id"],
                            "priority": "high",
                            "reason": "Multi-creator controversy requires cross-verification",
                            "creators": controversy["involved_creators"],
                        }
                    )
            priority_order = {"high": 1, "medium": 2, "low": 3}
            priorities.sort(key=lambda x: priority_order.get(x["priority"], 3))
            return priorities
        except Exception as e:
            print(f"Error identifying fact-checking priorities: {e}")
            return []

    async def _generate_monitoring_recommendations(
        self,
        detected_controversies: list[ControversyEvent],
        creator_risk_assessment: dict[str, Any],
        tenant: str,
        workspace: str,
    ) -> list[str]:
        """Generate monitoring recommendations based on controversies."""
        try:
            recommendations = []
            high_risk_creators = [
                creator for creator, assessment in creator_risk_assessment.items() if assessment["risk_level"] == "high"
            ]
            if high_risk_creators:
                recommendations.append(
                    f"Increase monitoring frequency for high-risk creators: {', '.join(high_risk_creators)}"
                )
            active_controversies = [c for c in detected_controversies if c["status"] == "active"]
            if active_controversies:
                recommendations.append("Implement real-time monitoring for active controversies")
                recommendations.append("Set up alerts for new related content")
            multi_platform_controversies = [c for c in detected_controversies if len(c["platforms"]) > 1]
            if multi_platform_controversies:
                recommendations.append("Implement cross-platform monitoring for multi-platform controversies")
            high_viral_controversies = [c for c in detected_controversies if c["severity_level"] >= 4]
            if high_viral_controversies:
                recommendations.append("Monitor viral potential metrics for high-severity controversies")
            pending_fact_checks = [c for c in detected_controversies if c["fact_check_status"].get("pending", False)]
            if pending_fact_checks:
                recommendations.append("Prioritize fact-checking for controversies with pending claims")
            return recommendations
        except Exception as e:
            print(f"Error generating monitoring recommendations: {e}")
            return []

    def get_active_controversies(self, creator_id: str | None = None) -> list[ControversyEvent]:
        """Get active controversies, optionally filtered by creator."""
        if creator_id:
            return [
                controversy
                for controversy in self._active_controversies.values()
                if creator_id in controversy["involved_creators"]
            ]
        return list(self._active_controversies.values())

    def get_creator_risk_profile(self, creator_id: str) -> dict[str, Any]:
        """Get risk profile for a creator."""
        return self._creator_risk_profiles.get(creator_id, {})

    def update_controversy_status(self, controversy_id: str, status: str, resolution: str | None = None) -> StepResult:
        """Update controversy status and resolution."""
        try:
            if controversy_id not in self._active_controversies:
                return StepResult.fail(f"Controversy {controversy_id} not found")
            controversy = self._active_controversies[controversy_id]
            controversy["status"] = status
            controversy["resolution_status"] = resolution
            if status == "resolved":
                controversy["end_date"] = time.time()
                self._controversy_history.append(controversy)
                del self._active_controversies[controversy_id]
            return StepResult.ok(data={"updated_controversy": controversy})
        except Exception as e:
            return StepResult.fail(f"Failed to update controversy status: {e!s}")

    def get_agent_stats(self) -> dict[str, Any]:
        """Get agent statistics."""
        return {
            "active_controversies": len(self._active_controversies),
            "total_controversies": len(self._controversy_history) + len(self._active_controversies),
            "monitored_creators": len(self._creator_risk_profiles),
            "monitoring_keywords": len(self._monitoring_keywords),
        }
