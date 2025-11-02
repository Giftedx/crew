"""
Personality dashboard and analytics for Discord AI chatbot.

This module provides comprehensive personality analytics, evolution tracking,
and user feedback visualization for the bot's personality system.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from platform.core.step_result import StepResult
from typing import Any


@dataclass
class PersonalityTraitSnapshot:
    """Snapshot of a personality trait at a specific time."""

    trait_name: str
    value: float
    timestamp: float
    confidence: float
    user_feedback_count: int
    positive_feedback: int
    negative_feedback: int
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class PersonalityEvolution:
    """Evolution tracking for personality traits."""

    trait_name: str
    evolution_points: list[PersonalityTraitSnapshot] = field(default_factory=list)
    trend_direction: str = "stable"
    trend_strength: float = 0.0
    volatility: float = 0.0
    user_satisfaction_correlation: float = 0.0


@dataclass
class UserPersonalityProfile:
    """User's interaction profile with bot personality."""

    user_id: str
    preferred_traits: dict[str, float] = field(default_factory=dict)
    feedback_history: list[dict[str, Any]] = field(default_factory=list)
    interaction_count: int = 0
    satisfaction_scores: list[float] = field(default_factory=list)
    personality_preferences: dict[str, Any] = field(default_factory=dict)


@dataclass
class PersonalityAnalytics:
    """Comprehensive personality analytics."""

    trait_distributions: dict[str, list[float]] = field(default_factory=dict)
    user_satisfaction_by_trait: dict[str, list[float]] = field(default_factory=list)
    trait_correlations: dict[str, dict[str, float]] = field(default_factory=dict)
    evolution_insights: dict[str, str] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)


class PersonalityDashboard:
    """
    Comprehensive personality dashboard and analytics system.

    This dashboard provides insights into personality evolution, user preferences,
    and optimization recommendations for the bot's personality system.
    """

    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        self._trait_snapshots: dict[str, list[PersonalityTraitSnapshot]] = defaultdict(list)
        self._trait_evolutions: dict[str, PersonalityEvolution] = {}
        self._user_profiles: dict[str, UserPersonalityProfile] = {}
        self._analytics_cache: dict[str, Any] = {}
        self._cache_timestamp: float = 0.0
        self._cache_ttl: float = 300.0
        self._lock = asyncio.Lock()
        self._stats = {
            "total_traits_tracked": 0,
            "total_snapshots": 0,
            "active_users": 0,
            "avg_user_satisfaction": 0.0,
            "personality_evolution_rate": 0.0,
        }

    async def record_trait_snapshot(
        self,
        trait_name: str,
        value: float,
        confidence: float = 1.0,
        user_feedback: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> StepResult:
        """Record a snapshot of a personality trait."""
        try:
            async with self._lock:
                snapshot = PersonalityTraitSnapshot(
                    trait_name=trait_name,
                    value=value,
                    timestamp=time.time(),
                    confidence=confidence,
                    context=context or {},
                )
                if user_feedback:
                    snapshot.user_feedback_count = user_feedback.get("count", 0)
                    snapshot.positive_feedback = user_feedback.get("positive", 0)
                    snapshot.negative_feedback = user_feedback.get("negative", 0)
                self._trait_snapshots[trait_name].append(snapshot)
                if len(self._trait_snapshots[trait_name]) > self.max_history_size:
                    self._trait_snapshots[trait_name] = self._trait_snapshots[trait_name][-self.max_history_size :]
                await self._update_trait_evolution(trait_name, snapshot)
                self._analytics_cache.clear()
                self._stats["total_snapshots"] += 1
                return StepResult.ok(data={"trait_name": trait_name, "snapshot_recorded": True, "current_value": value})
        except Exception as e:
            return StepResult.fail(f"Failed to record trait snapshot: {e!s}")

    async def record_user_feedback(
        self, user_id: str, trait_name: str, feedback_value: float, context: dict[str, Any] | None = None
    ) -> StepResult:
        """Record user feedback on personality traits."""
        try:
            async with self._lock:
                if user_id not in self._user_profiles:
                    self._user_profiles[user_id] = UserPersonalityProfile(user_id=user_id)
                user_profile = self._user_profiles[user_id]
                user_profile.interaction_count += 1
                feedback_record = {
                    "trait_name": trait_name,
                    "feedback_value": feedback_value,
                    "timestamp": time.time(),
                    "context": context or {},
                }
                user_profile.feedback_history.append(feedback_record)
                if trait_name in user_profile.preferred_traits:
                    current_pref = user_profile.preferred_traits[trait_name]
                    weight = 0.1
                    user_profile.preferred_traits[trait_name] = current_pref * (1 - weight) + feedback_value * weight
                else:
                    user_profile.preferred_traits[trait_name] = feedback_value
                if len(user_profile.feedback_history) > 1000:
                    user_profile.feedback_history = user_profile.feedback_history[-1000:]
                if self._trait_snapshots.get(trait_name):
                    latest_snapshot = self._trait_snapshots[trait_name][-1]
                    latest_snapshot.user_feedback_count += 1
                    if feedback_value > 0:
                        latest_snapshot.positive_feedback += 1
                    elif feedback_value < 0:
                        latest_snapshot.negative_feedback += 1
                return StepResult.ok(data={"user_id": user_id, "trait_name": trait_name, "feedback_recorded": True})
        except Exception as e:
            return StepResult.fail(f"Failed to record user feedback: {e!s}")

    async def get_trait_evolution(self, trait_name: str) -> StepResult:
        """Get evolution data for a specific trait."""
        try:
            async with self._lock:
                if trait_name not in self._trait_evolutions:
                    return StepResult.fail(f"Trait {trait_name} not found")
                evolution = self._trait_evolutions[trait_name]
                return StepResult.ok(data={"trait_name": trait_name, "evolution": evolution})
        except Exception as e:
            return StepResult.fail(f"Failed to get trait evolution: {e!s}")

    async def get_user_personality_profile(self, user_id: str) -> StepResult:
        """Get personality interaction profile for a user."""
        try:
            async with self._lock:
                if user_id not in self._user_profiles:
                    return StepResult.fail(f"User {user_id} not found")
                user_profile = self._user_profiles[user_id]
                if user_profile.feedback_history:
                    recent_feedback = user_profile.feedback_history[-10:]
                    avg_satisfaction = sum(f["feedback_value"] for f in recent_feedback) / len(recent_feedback)
                    user_profile.satisfaction_scores.append(avg_satisfaction)
                    if len(user_profile.satisfaction_scores) > 100:
                        user_profile.satisfaction_scores = user_profile.satisfaction_scores[-100:]
                return StepResult.ok(data={"user_profile": user_profile})
        except Exception as e:
            return StepResult.fail(f"Failed to get user personality profile: {e!s}")

    async def get_personality_analytics(self) -> StepResult:
        """Get comprehensive personality analytics."""
        try:
            current_time = time.time()
            if current_time - self._cache_timestamp < self._cache_ttl and self._analytics_cache:
                return StepResult.ok(data={"analytics": self._analytics_cache})
            async with self._lock:
                analytics = PersonalityAnalytics()
                for trait_name, snapshots in self._trait_snapshots.items():
                    if snapshots:
                        values = [s.value for s in snapshots]
                        analytics.trait_distributions[trait_name] = values
                        satisfaction_scores = []
                        for snapshot in snapshots:
                            if snapshot.user_feedback_count > 0:
                                satisfaction = (
                                    snapshot.positive_feedback - snapshot.negative_feedback
                                ) / snapshot.user_feedback_count
                                satisfaction_scores.append(satisfaction)
                        if satisfaction_scores:
                            analytics.user_satisfaction_by_trait[trait_name] = satisfaction_scores
                await self._analyze_trait_correlations(analytics)
                await self._generate_evolution_insights(analytics)
                await self._generate_recommendations(analytics)
                self._analytics_cache = analytics.__dict__
                self._cache_timestamp = current_time
                return StepResult.ok(data={"analytics": analytics.__dict__})
        except Exception as e:
            return StepResult.fail(f"Failed to get personality analytics: {e!s}")

    async def _update_trait_evolution(self, trait_name: str, snapshot: PersonalityTraitSnapshot):
        """Update trait evolution tracking."""
        if trait_name not in self._trait_evolutions:
            self._trait_evolutions[trait_name] = PersonalityEvolution(trait_name=trait_name)
        evolution = self._trait_evolutions[trait_name]
        evolution.evolution_points.append(snapshot)
        if len(evolution.evolution_points) > 1000:
            evolution.evolution_points = evolution.evolution_points[-1000:]
        if len(evolution.evolution_points) >= 3:
            await self._analyze_trait_trend(evolution)

    async def _analyze_trait_trend(self, evolution: PersonalityEvolution):
        """Analyze trend direction and strength for a trait."""
        points = evolution.evolution_points
        if len(points) < 3:
            return
        n = len(points)
        x_values = list(range(n))
        y_values = [p.value for p in points]
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n
        numerator = sum(((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values, strict=False)))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        if denominator != 0:
            slope = numerator / denominator
            if slope > 0.01:
                evolution.trend_direction = "increasing"
            elif slope < -0.01:
                evolution.trend_direction = "decreasing"
            else:
                evolution.trend_direction = "stable"
            evolution.trend_strength = min(abs(slope) * 10, 1.0)
        if len(y_values) > 1:
            differences = [abs(y_values[i] - y_values[i - 1]) for i in range(1, len(y_values))]
            evolution.volatility = sum(differences) / len(differences) if differences else 0.0

    async def _analyze_trait_correlations(self, analytics: PersonalityAnalytics):
        """Analyze correlations between personality traits."""
        trait_names = list(self._trait_snapshots.keys())
        for i, trait1 in enumerate(trait_names):
            analytics.trait_correlations[trait1] = {}
            for trait2 in trait_names[i + 1 :]:
                correlation = await self._calculate_correlation(trait1, trait2)
                analytics.trait_correlations[trait1][trait2] = correlation
                analytics.trait_correlations[trait2][trait1] = correlation

    async def _calculate_correlation(self, trait1: str, trait2: str) -> float:
        """Calculate correlation between two traits."""
        snapshots1 = self._trait_snapshots.get(trait1, [])
        snapshots2 = self._trait_snapshots.get(trait2, [])
        if not snapshots1 or not snapshots2:
            return 0.0
        values1 = [s.value for s in snapshots1]
        values2 = [s.value for s in snapshots2]
        n = min(len(values1), len(values2))
        if n < 2:
            return 0.0
        values1 = values1[:n]
        values2 = values2[:n]
        mean1 = sum(values1) / n
        mean2 = sum(values2) / n
        numerator = sum(((v1 - mean1) * (v2 - mean2) for v1, v2 in zip(values1, values2, strict=False)))
        denominator = (sum((v1 - mean1) ** 2 for v1 in values1) * sum((v2 - mean2) ** 2 for v2 in values2)) ** 0.5
        if denominator == 0:
            return 0.0
        return numerator / denominator

    async def _generate_evolution_insights(self, analytics: PersonalityAnalytics):
        """Generate insights about personality evolution."""
        for trait_name, evolution in self._trait_evolutions.items():
            if evolution.trend_direction == "increasing":
                analytics.evolution_insights[trait_name] = f"{trait_name} is becoming more prominent"
            elif evolution.trend_direction == "decreasing":
                analytics.evolution_insights[trait_name] = f"{trait_name} is becoming less prominent"
            else:
                analytics.evolution_insights[trait_name] = f"{trait_name} is stable"
            if evolution.volatility > 0.1:
                analytics.evolution_insights[trait_name] += " (high volatility)"

    async def _generate_recommendations(self, analytics: PersonalityAnalytics):
        """Generate optimization recommendations."""
        recommendations = []
        for trait_name, satisfaction_scores in analytics.user_satisfaction_by_trait.items():
            if satisfaction_scores:
                avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)
                if avg_satisfaction < -0.2:
                    recommendations.append(
                        f"Consider reducing {trait_name} intensity (low satisfaction: {avg_satisfaction:.2f})"
                    )
                elif avg_satisfaction > 0.2:
                    recommendations.append(
                        f"Consider increasing {trait_name} intensity (high satisfaction: {avg_satisfaction:.2f})"
                    )
        for trait_name, evolution in self._trait_evolutions.items():
            if evolution.volatility > 0.2:
                recommendations.append(f"High volatility in {trait_name} - consider stabilizing")
        for trait1, correlations in analytics.trait_correlations.items():
            for trait2, correlation in correlations.items():
                if abs(correlation) > 0.8:
                    recommendations.append(f"Strong correlation between {trait1} and {trait2} ({correlation:.2f})")
        analytics.recommendations = recommendations

    async def get_dashboard_summary(self) -> StepResult:
        """Get a summary for the personality dashboard."""
        try:
            async with self._lock:
                self._stats["total_traits_tracked"] = len(self._trait_snapshots)
                self._stats["active_users"] = len(self._user_profiles)
                all_satisfaction_scores = []
                for user_profile in self._user_profiles.values():
                    if user_profile.satisfaction_scores:
                        all_satisfaction_scores.extend(user_profile.satisfaction_scores)
                if all_satisfaction_scores:
                    self._stats["avg_user_satisfaction"] = sum(all_satisfaction_scores) / len(all_satisfaction_scores)
                evolution_rates = []
                for evolution in self._trait_evolutions.values():
                    if evolution.trend_strength > 0:
                        evolution_rates.append(evolution.trend_strength)
                if evolution_rates:
                    self._stats["personality_evolution_rate"] = sum(evolution_rates) / len(evolution_rates)
                return StepResult.ok(
                    data={
                        "dashboard_stats": self._stats,
                        "active_traits": len(self._trait_snapshots),
                        "tracked_users": len(self._user_profiles),
                        "cache_status": "valid" if time.time() - self._cache_timestamp < self._cache_ttl else "expired",
                    }
                )
        except Exception as e:
            return StepResult.fail(f"Failed to get dashboard summary: {e!s}")

    async def export_personality_data(self, fmt: str = "json") -> StepResult:
        """Export personality data for analysis."""
        try:
            async with self._lock:
                if fmt.lower() == "json":
                    export_data = {
                        "trait_snapshots": {
                            trait_name: [
                                {
                                    "value": snapshot.value,
                                    "timestamp": snapshot.timestamp,
                                    "confidence": snapshot.confidence,
                                    "user_feedback_count": snapshot.user_feedback_count,
                                    "positive_feedback": snapshot.positive_feedback,
                                    "negative_feedback": snapshot.negative_feedback,
                                    "context": snapshot.context,
                                }
                                for snapshot in snapshots
                            ]
                            for trait_name, snapshots in self._trait_snapshots.items()
                        },
                        "user_profiles": {
                            user_id: {
                                "preferred_traits": profile.preferred_traits,
                                "interaction_count": profile.interaction_count,
                                "satisfaction_scores": profile.satisfaction_scores,
                                "personality_preferences": profile.personality_preferences,
                            }
                            for user_id, profile in self._user_profiles.items()
                        },
                        "trait_evolutions": {
                            trait_name: {
                                "trend_direction": evolution.trend_direction,
                                "trend_strength": evolution.trend_strength,
                                "volatility": evolution.volatility,
                                "user_satisfaction_correlation": evolution.user_satisfaction_correlation,
                            }
                            for trait_name, evolution in self._trait_evolutions.items()
                        },
                        "export_timestamp": time.time(),
                    }
                    return StepResult.ok(data={"export_data": export_data, "format": format})
                else:
                    return StepResult.fail(f"Unsupported export format: {format}")
        except Exception as e:
            return StepResult.fail(f"Failed to export personality data: {e!s}")


def create_personality_dashboard(max_history_size: int = 10000) -> PersonalityDashboard:
    """Create a personality dashboard with the specified configuration."""
    return PersonalityDashboard(max_history_size)
