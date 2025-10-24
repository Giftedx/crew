"""
Engagement prediction tool for user engagement probability scoring and optimization.

This tool provides comprehensive engagement prediction including:
- User engagement probability scoring
- Optimal posting time prediction
- Content format optimization recommendations
- Audience segment targeting
- Engagement rate forecasting
"""

from __future__ import annotations

import logging
import time
from typing import Any, TypedDict

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool


class AudienceProfile(TypedDict, total=False):
    """Audience profile for engagement prediction."""

    demographics: dict[str, Any]
    interests: list[str]
    behavior_patterns: dict[str, Any]
    engagement_history: list[dict[str, Any]]
    platform_preferences: dict[str, float]
    time_activity: dict[str, float]


class EngagementProbability(TypedDict, total=False):
    """Engagement probability prediction result."""

    overall_probability: float
    like_probability: float
    share_probability: float
    comment_probability: float
    save_probability: float
    click_through_probability: float
    confidence_score: float
    factors: dict[str, float]


class PostingSchedule(TypedDict, total=False):
    """Optimal posting schedule recommendation."""

    optimal_times: list[dict[str, Any]]
    timezone: str
    frequency_recommendation: str
    content_type_schedule: dict[str, list[dict[str, Any]]]
    audience_peak_times: dict[str, list[float]]
    engagement_potential: dict[str, float]


class FormatRecommendation(TypedDict, total=False):
    """Content format optimization recommendation."""

    recommended_formats: list[str]
    format_scores: dict[str, float]
    optimization_suggestions: list[str]
    platform_specific_recommendations: dict[str, dict[str, Any]]
    audience_preferences: dict[str, float]
    performance_predictions: dict[str, float]


class EngagementForecast(TypedDict, total=False):
    """Engagement rate forecasting result."""

    forecast_horizon: int
    predicted_engagement_rates: list[float]
    confidence_intervals: list[dict[str, float]]
    peak_engagement_time: float
    engagement_decay_rate: float
    viral_potential: float
    sustainability_score: float


class EngagementPredictionResult(TypedDict, total=False):
    """Complete engagement prediction result."""

    engagement_probabilities: list[EngagementProbability]
    posting_schedules: list[PostingSchedule]
    format_recommendations: list[FormatRecommendation]
    engagement_forecasts: list[EngagementForecast]
    audience_insights: dict[str, Any]
    optimization_recommendations: list[str]
    model_performance: dict[str, Any]
    processing_time: float
    metadata: dict[str, Any]


class EngagementPredictionTool(BaseTool[StepResult]):
    """Advanced engagement prediction with optimization recommendations."""

    name: str = "Engagement Prediction Tool"
    description: str = (
        "Predicts user engagement probability, optimizes posting schedules, "
        "recommends content formats, and forecasts engagement rates."
    )

    def __init__(
        self,
        enable_posting_optimization: bool = True,
        enable_format_recommendations: bool = True,
        enable_engagement_forecasting: bool = True,
        enable_audience_analysis: bool = True,
        prediction_horizon_hours: int = 72,
        confidence_threshold: float = 0.6,
    ):
        super().__init__()
        self._enable_posting_optimization = enable_posting_optimization
        self._enable_format_recommendations = enable_format_recommendations
        self._enable_engagement_forecasting = enable_engagement_forecasting
        self._enable_audience_analysis = enable_audience_analysis
        self._prediction_horizon_hours = prediction_horizon_hours
        self._confidence_threshold = confidence_threshold
        self._metrics = get_metrics()

    def _run(
        self,
        content_data: list[dict[str, Any]],
        audience_profiles: list[AudienceProfile] | None = None,
        historical_engagement: dict[str, Any] | None = None,
        prediction_config: dict[str, Any] | None = None,
        tenant: str = "default",
        workspace: str = "default",
        prediction_mode: str = "comprehensive",
    ) -> StepResult:
        """
        Perform comprehensive engagement prediction analysis.

        Args:
            content_data: Content items to analyze for engagement prediction
            audience_profiles: Audience profiles for targeting analysis
            historical_engagement: Historical engagement data for context
            prediction_config: Configuration for prediction models
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier
            prediction_mode: Prediction mode (basic, comprehensive, detailed)

        Returns:
            StepResult with comprehensive engagement prediction results
        """
        start_time = time.monotonic()

        try:
            # Input validation
            if not content_data:
                return StepResult.fail("Content data cannot be empty")

            if tenant and workspace:
                self.note(f"Starting engagement prediction for {len(content_data)} content items")

            # Perform engagement prediction analysis
            engagement_probabilities = self._predict_engagement_probabilities(content_data, audience_profiles)
            posting_schedules = (
                self._optimize_posting_schedules(content_data, audience_profiles)
                if self._enable_posting_optimization
                else []
            )
            format_recommendations = (
                self._recommend_content_formats(content_data, audience_profiles)
                if self._enable_format_recommendations
                else []
            )
            engagement_forecasts = (
                self._forecast_engagement_rates(content_data, historical_engagement)
                if self._enable_engagement_forecasting
                else []
            )
            audience_insights = (
                self._analyze_audience_insights(audience_profiles) if self._enable_audience_analysis else {}
            )
            optimization_recommendations = self._generate_optimization_recommendations(
                engagement_probabilities, posting_schedules, format_recommendations
            )
            model_performance = self._assess_model_performance(content_data, historical_engagement)

            processing_time = time.monotonic() - start_time

            result: EngagementPredictionResult = {
                "engagement_probabilities": engagement_probabilities,
                "posting_schedules": posting_schedules,
                "format_recommendations": format_recommendations,
                "engagement_forecasts": engagement_forecasts,
                "audience_insights": audience_insights,
                "optimization_recommendations": optimization_recommendations,
                "model_performance": model_performance,
                "processing_time": processing_time,
                "metadata": {
                    "prediction_mode": prediction_mode,
                    "content_items_analyzed": len(content_data),
                    "prediction_horizon_hours": self._prediction_horizon_hours,
                    "tenant": tenant,
                    "workspace": workspace,
                    "timestamp": time.time(),
                },
            }

            self._metrics.counter("tool_runs_total", labels={"tool": self.name, "outcome": "success"}).inc()
            self._metrics.histogram("tool_run_seconds", processing_time, labels={"tool": self.name})

            return StepResult.ok(data=result)

        except Exception as e:
            processing_time = time.monotonic() - start_time
            self._metrics.counter("tool_runs_total", labels={"tool": self.name, "outcome": "error"}).inc()
            logging.exception("Engagement prediction failed")
            return StepResult.fail(f"Engagement prediction failed: {e!s}")

    def _predict_engagement_probabilities(
        self,
        content_data: list[dict[str, Any]],
        audience_profiles: list[AudienceProfile] | None,
    ) -> list[EngagementProbability]:
        """Predict engagement probabilities for content items."""
        probabilities = []

        for content in content_data:
            # Calculate base engagement probability
            overall_probability = self._calculate_base_engagement_probability(content)
            like_probability = self._calculate_like_probability(content, overall_probability)
            share_probability = self._calculate_share_probability(content, overall_probability)
            comment_probability = self._calculate_comment_probability(content, overall_probability)
            save_probability = self._calculate_save_probability(content, overall_probability)
            click_through_probability = self._calculate_click_through_probability(content, overall_probability)
            confidence_score = self._calculate_engagement_confidence(content, audience_profiles)
            factors = self._analyze_engagement_factors(content, audience_profiles)

            if confidence_score >= self._confidence_threshold:
                probability: EngagementProbability = {
                    "overall_probability": overall_probability,
                    "like_probability": like_probability,
                    "share_probability": share_probability,
                    "comment_probability": comment_probability,
                    "save_probability": save_probability,
                    "click_through_probability": click_through_probability,
                    "confidence_score": confidence_score,
                    "factors": factors,
                }
                probabilities.append(probability)

        return probabilities

    def _optimize_posting_schedules(
        self,
        content_data: list[dict[str, Any]],
        audience_profiles: list[AudienceProfile] | None,
    ) -> list[PostingSchedule]:
        """Optimize posting schedules for content."""
        schedules = []

        for content in content_data:
            content_type = content.get("content_type", "unknown")
            content.get("platform", "unknown")

            # Calculate optimal posting times
            optimal_times = self._calculate_optimal_posting_times(content, audience_profiles)
            timezone = self._determine_optimal_timezone(audience_profiles)
            frequency_recommendation = self._recommend_posting_frequency(content, audience_profiles)
            content_type_schedule = self._create_content_type_schedule(content_type, optimal_times)
            audience_peak_times = self._identify_audience_peak_times(audience_profiles)
            engagement_potential = self._calculate_engagement_potential_by_time(optimal_times, audience_profiles)

            schedule: PostingSchedule = {
                "optimal_times": optimal_times,
                "timezone": timezone,
                "frequency_recommendation": frequency_recommendation,
                "content_type_schedule": content_type_schedule,
                "audience_peak_times": audience_peak_times,
                "engagement_potential": engagement_potential,
            }
            schedules.append(schedule)

        return schedules

    def _recommend_content_formats(
        self,
        content_data: list[dict[str, Any]],
        audience_profiles: list[AudienceProfile] | None,
    ) -> list[FormatRecommendation]:
        """Recommend optimal content formats."""
        recommendations = []

        for content in content_data:
            platform = content.get("platform", "unknown")
            content.get("topic", "general")

            # Analyze format options
            recommended_formats = self._identify_recommended_formats(content, audience_profiles)
            format_scores = self._score_content_formats(recommended_formats, content, audience_profiles)
            optimization_suggestions = self._generate_format_optimization_suggestions(content, format_scores)
            platform_specific_recommendations = self._create_platform_specific_recommendations(
                platform, recommended_formats
            )
            audience_preferences = self._analyze_audience_format_preferences(audience_profiles)
            performance_predictions = self._predict_format_performance(recommended_formats, content, audience_profiles)

            recommendation: FormatRecommendation = {
                "recommended_formats": recommended_formats,
                "format_scores": format_scores,
                "optimization_suggestions": optimization_suggestions,
                "platform_specific_recommendations": platform_specific_recommendations,
                "audience_preferences": audience_preferences,
                "performance_predictions": performance_predictions,
            }
            recommendations.append(recommendation)

        return recommendations

    def _forecast_engagement_rates(
        self,
        content_data: list[dict[str, Any]],
        historical_engagement: dict[str, Any] | None,
    ) -> list[EngagementForecast]:
        """Forecast engagement rates over time."""
        forecasts = []

        for content in content_data:
            # Generate engagement forecast
            forecast_horizon = self._prediction_horizon_hours
            predicted_engagement_rates = self._predict_engagement_rates_over_time(
                content, forecast_horizon, historical_engagement
            )
            confidence_intervals = self._calculate_engagement_confidence_intervals(predicted_engagement_rates, content)
            peak_engagement_time = self._predict_peak_engagement_time(predicted_engagement_rates)
            engagement_decay_rate = self._calculate_engagement_decay_rate(predicted_engagement_rates)
            viral_potential = self._assess_viral_potential(content, predicted_engagement_rates)
            sustainability_score = self._calculate_sustainability_score(
                predicted_engagement_rates, engagement_decay_rate
            )

            forecast: EngagementForecast = {
                "forecast_horizon": forecast_horizon,
                "predicted_engagement_rates": predicted_engagement_rates,
                "confidence_intervals": confidence_intervals,
                "peak_engagement_time": peak_engagement_time,
                "engagement_decay_rate": engagement_decay_rate,
                "viral_potential": viral_potential,
                "sustainability_score": sustainability_score,
            }
            forecasts.append(forecast)

        return forecasts

    def _calculate_base_engagement_probability(self, content: dict[str, Any]) -> float:
        """Calculate base engagement probability for content."""
        base_probability = 0.5  # Start with 50% base probability

        # Content quality factors
        content_metadata = content.get("metadata", {})

        # Video quality
        if content_metadata.get("video_quality") == "high":
            base_probability += 0.1
        elif content_metadata.get("video_quality") == "low":
            base_probability -= 0.1

        # Content length optimization
        duration = content_metadata.get("duration", 0)
        content_type = content.get("content_type", "unknown")

        if content_type == "video":
            if 30 <= duration <= 300:  # 30 seconds to 5 minutes
                base_probability += 0.1
            elif duration > 600:  # Over 10 minutes
                base_probability -= 0.05
        elif content_type == "text":
            word_count = content_metadata.get("word_count", 0)
            if 50 <= word_count <= 500:
                base_probability += 0.1
            elif word_count > 1000:
                base_probability -= 0.05

        # Trending topics
        if content.get("trending_topic"):
            base_probability += 0.15

        # Emotional content
        sentiment = content_metadata.get("sentiment", "neutral")
        if sentiment in ["positive", "negative"]:
            base_probability += 0.1

        return min(1.0, max(0.0, base_probability))

    def _calculate_like_probability(self, content: dict[str, Any], base_probability: float) -> float:
        """Calculate like probability."""
        like_probability = base_probability

        # Adjust for content characteristics that drive likes
        content_metadata = content.get("metadata", {})

        # Visual appeal
        if content_metadata.get("visual_appeal") == "high":
            like_probability += 0.1

        # Entertainment value
        if content_metadata.get("entertainment_value") == "high":
            like_probability += 0.1

        # Educational content
        if content_metadata.get("educational_value"):
            like_probability += 0.05

        return min(1.0, max(0.0, like_probability))

    def _calculate_share_probability(self, content: dict[str, Any], base_probability: float) -> float:
        """Calculate share probability."""
        share_probability = base_probability * 0.7  # Shares are typically lower than likes

        # Adjust for shareable content characteristics
        content_metadata = content.get("metadata", {})

        # Controversy (moderate amount)
        controversy_level = content_metadata.get("controversy_level", 0)
        if 0.3 <= controversy_level <= 0.7:
            share_probability += 0.1

        # Emotional impact
        emotional_impact = content_metadata.get("emotional_impact", "neutral")
        if emotional_impact == "high":
            share_probability += 0.1

        # Call to action
        if content_metadata.get("has_call_to_action"):
            share_probability += 0.05

        return min(1.0, max(0.0, share_probability))

    def _calculate_comment_probability(self, content: dict[str, Any], base_probability: float) -> float:
        """Calculate comment probability."""
        comment_probability = base_probability * 0.5  # Comments are typically lower than likes

        # Adjust for content that drives discussion
        content_metadata = content.get("metadata", {})

        # Controversial content
        controversy_level = content_metadata.get("controversy_level", 0)
        if controversy_level > 0.5:
            comment_probability += 0.1

        # Question or poll
        if content_metadata.get("is_question") or content_metadata.get("is_poll"):
            comment_probability += 0.15

        # Educational content
        if content_metadata.get("educational_value"):
            comment_probability += 0.05

        return min(1.0, max(0.0, comment_probability))

    def _calculate_save_probability(self, content: dict[str, Any], base_probability: float) -> float:
        """Calculate save probability."""
        save_probability = base_probability * 0.3  # Saves are typically lower than other engagements

        # Adjust for content worth saving
        content_metadata = content.get("metadata", {})

        # Educational content
        if content_metadata.get("educational_value"):
            save_probability += 0.1

        # Reference material
        if content_metadata.get("is_reference_material"):
            save_probability += 0.1

        # High quality content
        if content_metadata.get("content_quality") == "high":
            save_probability += 0.05

        return min(1.0, max(0.0, save_probability))

    def _calculate_click_through_probability(self, content: dict[str, Any], base_probability: float) -> float:
        """Calculate click-through probability."""
        click_through_probability = base_probability * 0.4  # CTR is typically lower than other engagements

        # Adjust for clickable content
        content_metadata = content.get("metadata", {})

        # Has links
        if content_metadata.get("has_links"):
            click_through_probability += 0.1

        # Call to action
        if content_metadata.get("has_call_to_action"):
            click_through_probability += 0.1

        # Curiosity gap
        if content_metadata.get("creates_curiosity"):
            click_through_probability += 0.05

        return min(1.0, max(0.0, click_through_probability))

    def _calculate_engagement_confidence(
        self, content: dict[str, Any], audience_profiles: list[AudienceProfile] | None
    ) -> float:
        """Calculate confidence in engagement prediction."""
        confidence = 0.5  # Base confidence

        # Increase confidence based on content data quality
        content_metadata = content.get("metadata", {})
        if content_metadata:
            confidence += 0.2

        # Increase confidence based on audience data availability
        if audience_profiles and len(audience_profiles) > 0:
            confidence += 0.2

        # Increase confidence for content with clear engagement indicators
        if content_metadata.get("trending_topic"):
            confidence += 0.1

        return min(1.0, confidence)

    def _analyze_engagement_factors(
        self, content: dict[str, Any], audience_profiles: list[AudienceProfile] | None
    ) -> dict[str, float]:
        """Analyze factors contributing to engagement prediction."""
        factors = {}

        # Content factors
        content_metadata = content.get("metadata", {})
        factors["content_quality"] = 0.8 if content_metadata.get("content_quality") == "high" else 0.5
        factors["trending_relevance"] = 0.9 if content.get("trending_topic") else 0.3
        factors["emotional_impact"] = 0.8 if content_metadata.get("emotional_impact") == "high" else 0.5
        factors["entertainment_value"] = 0.8 if content_metadata.get("entertainment_value") == "high" else 0.5
        factors["educational_value"] = 0.7 if content_metadata.get("educational_value") else 0.3

        # Platform factors
        platform = content.get("platform", "unknown")
        platform_engagement_factors = {
            "youtube": 0.8,
            "tiktok": 0.9,
            "instagram": 0.8,
            "twitter": 0.6,
            "linkedin": 0.5,
        }
        factors["platform_optimization"] = platform_engagement_factors.get(platform, 0.5)

        # Audience factors
        if audience_profiles:
            factors["audience_alignment"] = 0.8  # Simplified calculation
            factors["audience_activity"] = 0.7  # Simplified calculation
        else:
            factors["audience_alignment"] = 0.5
            factors["audience_activity"] = 0.5

        return factors

    def _calculate_optimal_posting_times(
        self, content: dict[str, Any], audience_profiles: list[AudienceProfile] | None
    ) -> list[dict[str, Any]]:
        """Calculate optimal posting times for content."""
        optimal_times = []
        time.time()

        # Default optimal times (based on general social media patterns)
        default_times = [
            {
                "hour": 9,
                "day": "weekday",
                "engagement_score": 0.8,
                "description": "Morning commute",
            },
            {
                "hour": 12,
                "day": "weekday",
                "engagement_score": 0.9,
                "description": "Lunch break",
            },
            {
                "hour": 18,
                "day": "weekday",
                "engagement_score": 0.9,
                "description": "Evening wind-down",
            },
            {
                "hour": 20,
                "day": "weekday",
                "engagement_score": 0.8,
                "description": "Prime time",
            },
            {
                "hour": 10,
                "day": "weekend",
                "engagement_score": 0.7,
                "description": "Weekend morning",
            },
            {
                "hour": 14,
                "day": "weekend",
                "engagement_score": 0.8,
                "description": "Weekend afternoon",
            },
        ]

        # Adjust based on audience profiles
        if audience_profiles:
            for profile in audience_profiles:
                time_activity = profile.get("time_activity", {})
                if time_activity:
                    # Adjust times based on audience activity patterns
                    for time_slot in default_times:
                        hour_key = f"hour_{time_slot['hour']}"
                        if hour_key in time_activity:
                            time_slot["engagement_score"] *= time_activity[hour_key]

        # Sort by engagement score
        optimal_times = sorted(default_times, key=lambda x: x["engagement_score"], reverse=True)

        return optimal_times[:5]  # Return top 5 optimal times

    def _determine_optimal_timezone(self, audience_profiles: list[AudienceProfile] | None) -> str:
        """Determine optimal timezone for posting."""
        if not audience_profiles:
            return "UTC"

        # Analyze audience demographics for timezone
        timezones = []
        for profile in audience_profiles:
            demographics = profile.get("demographics", {})
            timezone = demographics.get("timezone", "UTC")
            timezones.append(timezone)

        # Return most common timezone
        if timezones:
            return max(set(timezones), key=timezones.count)

        return "UTC"

    def _recommend_posting_frequency(
        self, content: dict[str, Any], audience_profiles: list[AudienceProfile] | None
    ) -> str:
        """Recommend optimal posting frequency."""
        content_type = content.get("content_type", "unknown")
        platform = content.get("platform", "unknown")

        # Base frequency recommendations by platform and content type
        frequency_recommendations = {
            "youtube": {"video": "daily", "short": "multiple_daily"},
            "tiktok": {"video": "multiple_daily", "image": "daily"},
            "instagram": {"image": "daily", "story": "multiple_daily", "reel": "daily"},
            "twitter": {"text": "multiple_daily", "image": "daily"},
            "linkedin": {"text": "daily", "article": "weekly"},
        }

        platform_recs = frequency_recommendations.get(platform, {})
        frequency = platform_recs.get(content_type, "daily")

        # Adjust based on audience activity
        if audience_profiles:
            for profile in audience_profiles:
                behavior_patterns = profile.get("behavior_patterns", {})
                if behavior_patterns.get("high_activity"):
                    # Increase frequency for highly active audiences
                    if frequency == "weekly":
                        frequency = "daily"
                    elif frequency == "daily":
                        frequency = "multiple_daily"

        return frequency

    def _create_content_type_schedule(
        self, content_type: str, optimal_times: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Create content type specific schedule."""
        schedule = {}

        # Adjust optimal times based on content type
        if content_type == "video":
            # Videos perform better in evening
            schedule["video"] = [t for t in optimal_times if t["hour"] >= 18]
        elif content_type == "image":
            # Images perform well throughout the day
            schedule["image"] = optimal_times
        elif content_type == "text":
            # Text content performs well during work hours
            schedule["text"] = [t for t in optimal_times if 9 <= t["hour"] <= 17]
        else:
            schedule[content_type] = optimal_times

        return schedule

    def _identify_audience_peak_times(self, audience_profiles: list[AudienceProfile] | None) -> dict[str, list[float]]:
        """Identify peak activity times for audience segments."""
        peak_times = {}

        if not audience_profiles:
            # Default peak times
            peak_times["general"] = [9.0, 12.0, 18.0, 20.0]
            return peak_times

        # Analyze audience activity patterns
        for profile in audience_profiles:
            time_activity = profile.get("time_activity", {})
            if time_activity:
                # Find peak hours (activity > 0.7)
                peaks = [float(hour.split("_")[1]) for hour, activity in time_activity.items() if activity > 0.7]
                if peaks:
                    segment_id = profile.get("demographics", {}).get("segment", "general")
                    peak_times[segment_id] = peaks

        return peak_times

    def _calculate_engagement_potential_by_time(
        self,
        optimal_times: list[dict[str, Any]],
        audience_profiles: list[AudienceProfile] | None,
    ) -> dict[str, float]:
        """Calculate engagement potential by time slot."""
        engagement_potential = {}

        for time_slot in optimal_times:
            hour = time_slot["hour"]
            base_score = time_slot["engagement_score"]

            # Adjust based on audience profiles
            if audience_profiles:
                for profile in audience_profiles:
                    time_activity = profile.get("time_activity", {})
                    hour_key = f"hour_{hour}"
                    if hour_key in time_activity:
                        base_score *= time_activity[hour_key]

            engagement_potential[f"hour_{hour}"] = min(1.0, base_score)

        return engagement_potential

    def _identify_recommended_formats(
        self, content: dict[str, Any], audience_profiles: list[AudienceProfile] | None
    ) -> list[str]:
        """Identify recommended content formats."""
        platform = content.get("platform", "unknown")
        topic = content.get("topic", "general")

        # Base format recommendations by platform
        platform_formats = {
            "youtube": ["video", "short", "live"],
            "tiktok": ["video", "image"],
            "instagram": ["image", "story", "reel", "carousel"],
            "twitter": ["text", "image", "video"],
            "linkedin": ["text", "image", "article", "video"],
        }

        base_formats = platform_formats.get(platform, ["text", "image"])

        # Adjust based on topic
        topic_format_preferences = {
            "tutorial": ["video", "carousel"],
            "news": ["text", "image"],
            "entertainment": ["video", "image"],
            "educational": ["video", "carousel", "article"],
            "promotional": ["image", "video"],
        }

        topic_formats = topic_format_preferences.get(topic, base_formats)

        # Combine and prioritize
        recommended_formats = list(set(base_formats + topic_formats))

        return recommended_formats[:3]  # Return top 3 recommendations

    def _score_content_formats(
        self,
        formats: list[str],
        content: dict[str, Any],
        audience_profiles: list[AudienceProfile] | None,
    ) -> dict[str, float]:
        """Score content formats for engagement potential."""
        scores = {}

        for format_type in formats:
            base_score = 0.5

            # Platform optimization
            platform = content.get("platform", "unknown")
            platform_scores = {
                "youtube": {"video": 0.9, "short": 0.8, "live": 0.7},
                "tiktok": {"video": 0.9, "image": 0.6},
                "instagram": {"image": 0.8, "story": 0.7, "reel": 0.9, "carousel": 0.7},
                "twitter": {"text": 0.7, "image": 0.8, "video": 0.8},
                "linkedin": {"text": 0.8, "image": 0.7, "article": 0.9, "video": 0.8},
            }

            platform_format_scores = platform_scores.get(platform, {})
            format_score = platform_format_scores.get(format_type, 0.5)
            base_score = (base_score + format_score) / 2

            # Audience preference adjustment
            if audience_profiles:
                for profile in audience_profiles:
                    preferences = profile.get("platform_preferences", {})
                    if format_type in preferences:
                        base_score *= preferences[format_type]

            scores[format_type] = min(1.0, base_score)

        return scores

    def _generate_format_optimization_suggestions(
        self, content: dict[str, Any], format_scores: dict[str, float]
    ) -> list[str]:
        """Generate format optimization suggestions."""
        suggestions = []

        # Find highest scoring format
        best_format = max(format_scores.items(), key=lambda x: x[1])[0] if format_scores else "unknown"

        if best_format == "video":
            suggestions.append("Create engaging video content with clear visuals and audio")
            suggestions.append("Keep video length optimized for platform (30s-5min)")
        elif best_format == "image":
            suggestions.append("Use high-quality, visually appealing images")
            suggestions.append("Include compelling captions and hashtags")
        elif best_format == "text":
            suggestions.append("Write clear, engaging text with proper formatting")
            suggestions.append("Include relevant hashtags and mentions")
        elif best_format == "carousel":
            suggestions.append("Create a series of related images or slides")
            suggestions.append("Tell a story across multiple slides")

        # General suggestions based on scores
        low_scoring_formats = [fmt for fmt, score in format_scores.items() if score < 0.6]
        if low_scoring_formats:
            suggestions.append(f"Avoid {', '.join(low_scoring_formats)} format for this content")

        return suggestions

    def _create_platform_specific_recommendations(self, platform: str, formats: list[str]) -> dict[str, dict[str, Any]]:
        """Create platform-specific format recommendations."""
        recommendations = {}

        for format_type in formats:
            platform_specific = {}

            if platform == "youtube":
                if format_type == "video":
                    platform_specific = {
                        "optimal_length": "8-15 minutes",
                        "aspect_ratio": "16:9",
                        "thumbnail_importance": "high",
                        "seo_optimization": "critical",
                    }
                elif format_type == "short":
                    platform_specific = {
                        "optimal_length": "15-60 seconds",
                        "aspect_ratio": "9:16",
                        "thumbnail_importance": "medium",
                        "seo_optimization": "important",
                    }
            elif platform == "instagram":
                if format_type == "image":
                    platform_specific = {
                        "optimal_size": "1080x1080",
                        "aspect_ratio": "1:1",
                        "hashtag_count": "5-10",
                        "caption_length": "125-150 characters",
                    }
                elif format_type == "story":
                    platform_specific = {
                        "optimal_size": "1080x1920",
                        "aspect_ratio": "9:16",
                        "duration": "15 seconds",
                        "interactive_elements": "recommended",
                    }
            elif platform == "twitter" and format_type == "text":
                platform_specific = {
                    "character_limit": 280,
                    "hashtag_count": "1-2",
                    "mention_usage": "sparingly",
                    "thread_opportunity": "consider",
                }

            recommendations[format_type] = platform_specific

        return recommendations

    def _analyze_audience_format_preferences(self, audience_profiles: list[AudienceProfile] | None) -> dict[str, float]:
        """Analyze audience format preferences."""
        preferences = {}

        if not audience_profiles:
            # Default preferences
            preferences = {
                "video": 0.7,
                "image": 0.8,
                "text": 0.6,
                "audio": 0.5,
            }
            return preferences

        # Aggregate preferences from audience profiles
        format_totals = {}
        format_counts = {}

        for profile in audience_profiles:
            platform_preferences = profile.get("platform_preferences", {})
            for format_type, preference in platform_preferences.items():
                if format_type not in format_totals:
                    format_totals[format_type] = 0
                    format_counts[format_type] = 0
                format_totals[format_type] += preference
                format_counts[format_type] += 1

        # Calculate average preferences
        for format_type in format_totals:
            if format_counts[format_type] > 0:
                preferences[format_type] = format_totals[format_type] / format_counts[format_type]

        return preferences

    def _predict_format_performance(
        self,
        formats: list[str],
        content: dict[str, Any],
        audience_profiles: list[AudienceProfile] | None,
    ) -> dict[str, float]:
        """Predict performance for each format."""
        performance = {}

        for format_type in formats:
            base_performance = 0.5

            # Content type compatibility
            content_type = content.get("content_type", "unknown")
            compatibility_scores = {
                "tutorial": {"video": 0.9, "carousel": 0.8, "text": 0.6},
                "news": {"text": 0.8, "image": 0.7, "video": 0.6},
                "entertainment": {"video": 0.9, "image": 0.8, "text": 0.5},
                "educational": {"video": 0.9, "carousel": 0.8, "article": 0.7},
            }

            compatibility = compatibility_scores.get(content_type, {}).get(format_type, 0.5)
            base_performance = (base_performance + compatibility) / 2

            # Audience preference adjustment
            if audience_profiles:
                for profile in audience_profiles:
                    platform_preferences = profile.get("platform_preferences", {})
                    if format_type in platform_preferences:
                        base_performance *= platform_preferences[format_type]

            performance[format_type] = min(1.0, base_performance)

        return performance

    def _predict_engagement_rates_over_time(
        self,
        content: dict[str, Any],
        horizon_hours: int,
        historical_engagement: dict[str, Any] | None,
    ) -> list[float]:
        """Predict engagement rates over time."""
        # Get base engagement rate
        base_rate = self._calculate_base_engagement_probability(content)

        # Create time series prediction
        rates = []
        for hour in range(horizon_hours):
            # Simulate engagement curve (peak early, then decay)
            if hour < 6:  # First 6 hours - growth phase
                rate = base_rate * (0.5 + 0.5 * (hour / 6))
            elif hour < 24:  # 6-24 hours - peak phase
                rate = base_rate * 0.9
            else:  # After 24 hours - decay phase
                decay_factor = max(0.1, 1.0 - ((hour - 24) / 48))
                rate = base_rate * 0.9 * decay_factor

            rates.append(rate)

        return rates

    def _calculate_engagement_confidence_intervals(
        self, predicted_rates: list[float], content: dict[str, Any]
    ) -> list[dict[str, float]]:
        """Calculate confidence intervals for engagement predictions."""
        intervals = []

        # Calculate standard deviation based on content characteristics
        content_metadata = content.get("metadata", {})
        volatility = 0.1  # Base volatility

        if content_metadata.get("controversy_level", 0) > 0.5:
            volatility += 0.1

        if content.get("trending_topic"):
            volatility += 0.05

        for rate in predicted_rates:
            margin_of_error = rate * volatility
            intervals.append(
                {
                    "lower": max(0.0, rate - margin_of_error),
                    "upper": rate + margin_of_error,
                }
            )

        return intervals

    def _predict_peak_engagement_time(self, predicted_rates: list[float]) -> float:
        """Predict peak engagement time."""
        if not predicted_rates:
            return 0.0

        max_rate = max(predicted_rates)
        peak_index = predicted_rates.index(max_rate)

        return float(peak_index)

    def _calculate_engagement_decay_rate(self, predicted_rates: list[float]) -> float:
        """Calculate engagement decay rate."""
        if len(predicted_rates) < 2:
            return 0.0

        # Find peak and calculate decay
        max_rate = max(predicted_rates)
        peak_index = predicted_rates.index(max_rate)

        if peak_index < len(predicted_rates) - 1:
            # Calculate decay from peak to end
            end_rate = predicted_rates[-1]
            if max_rate > 0:
                decay_rate = (max_rate - end_rate) / max_rate
                return min(1.0, decay_rate)

        return 0.0

    def _assess_viral_potential(self, content: dict[str, Any], predicted_rates: list[float]) -> float:
        """Assess viral potential of content."""
        viral_potential = 0.0

        # Base viral potential from content characteristics
        content_metadata = content.get("metadata", {})

        if content_metadata.get("emotional_impact") == "high":
            viral_potential += 0.3

        if content_metadata.get("entertainment_value") == "high":
            viral_potential += 0.2

        if content.get("trending_topic"):
            viral_potential += 0.2

        # Adjust based on predicted engagement rates
        if predicted_rates:
            max_rate = max(predicted_rates)
            if max_rate > 0.8:
                viral_potential += 0.2
            elif max_rate > 0.6:
                viral_potential += 0.1

        return min(1.0, viral_potential)

    def _calculate_sustainability_score(self, predicted_rates: list[float], decay_rate: float) -> float:
        """Calculate sustainability score for engagement."""
        if not predicted_rates:
            return 0.0

        # Base sustainability from decay rate
        sustainability = 1.0 - decay_rate

        # Adjust based on rate consistency
        if len(predicted_rates) > 1:
            rate_variance = sum(
                (rate - sum(predicted_rates) / len(predicted_rates)) ** 2 for rate in predicted_rates
            ) / len(predicted_rates)
            consistency = max(0.0, 1.0 - rate_variance)
            sustainability = (sustainability + consistency) / 2

        return min(1.0, sustainability)

    def _analyze_audience_insights(self, audience_profiles: list[AudienceProfile] | None) -> dict[str, Any]:
        """Analyze audience insights for engagement optimization."""
        insights = {
            "audience_segments": [],
            "engagement_patterns": {},
            "preferences": {},
            "recommendations": [],
        }

        if not audience_profiles:
            insights["recommendations"].append("Collect audience data for better engagement predictions")
            return insights

        # Analyze audience segments
        segments = {}
        for profile in audience_profiles:
            demographics = profile.get("demographics", {})
            segment = demographics.get("segment", "general")
            if segment not in segments:
                segments[segment] = 0
            segments[segment] += 1

        insights["audience_segments"] = list(segments.keys())

        # Analyze engagement patterns
        for profile in audience_profiles:
            behavior_patterns = profile.get("behavior_patterns", {})
            for pattern, value in behavior_patterns.items():
                if pattern not in insights["engagement_patterns"]:
                    insights["engagement_patterns"][pattern] = []
                insights["engagement_patterns"][pattern].append(value)

        # Generate recommendations
        if len(audience_profiles) > 1:
            insights["recommendations"].append("Consider segment-specific content strategies")

        high_activity_count = sum(
            1 for profile in audience_profiles if profile.get("behavior_patterns", {}).get("high_activity")
        )
        if high_activity_count > len(audience_profiles) / 2:
            insights["recommendations"].append("Audience is highly active - increase posting frequency")

        return insights

    def _generate_optimization_recommendations(
        self,
        engagement_probabilities: list[EngagementProbability],
        posting_schedules: list[PostingSchedule],
        format_recommendations: list[FormatRecommendation],
    ) -> list[str]:
        """Generate optimization recommendations."""
        recommendations = []

        # Analyze engagement probabilities
        if engagement_probabilities:
            avg_probability = sum(p["overall_probability"] for p in engagement_probabilities) / len(
                engagement_probabilities
            )

            if avg_probability < 0.5:
                recommendations.append("Improve content quality to increase engagement probability")

            high_share_prob = [p for p in engagement_probabilities if p["share_probability"] > 0.7]
            if high_share_prob:
                recommendations.append("Content has high share potential - optimize for viral spread")

        # Analyze posting schedules
        if posting_schedules:
            for schedule in posting_schedules:
                frequency = schedule.get("frequency_recommendation", "daily")
                if frequency == "multiple_daily":
                    recommendations.append("High posting frequency recommended - ensure content quality")
                elif frequency == "weekly":
                    recommendations.append("Low posting frequency - consider increasing for better reach")

        # Analyze format recommendations
        if format_recommendations:
            for rec in format_recommendations:
                best_format = (
                    max(rec["format_scores"].items(), key=lambda x: x[1])[0] if rec["format_scores"] else "unknown"
                )
                recommendations.append(f"Optimize content for {best_format} format")

        return recommendations

    def _assess_model_performance(
        self,
        content_data: list[dict[str, Any]],
        historical_engagement: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Assess prediction model performance."""
        performance = {
            "data_quality": "good",
            "model_confidence": 0.7,
            "limitations": [],
            "improvements": [],
        }

        # Assess data quality
        if len(content_data) < 5:
            performance["data_quality"] = "limited"
            performance["limitations"].append("Insufficient content data for reliable predictions")
            performance["model_confidence"] = 0.4

        # Check content metadata completeness
        metadata_complete = 0
        for content in content_data:
            if content.get("metadata"):
                metadata_complete += 1

        if metadata_complete / len(content_data) < 0.7:
            performance["limitations"].append("Incomplete content metadata")
            performance["model_confidence"] *= 0.8

        # Check historical data availability
        if not historical_engagement:
            performance["limitations"].append("No historical engagement data available")
            performance["model_confidence"] *= 0.9

        # Suggest improvements
        if len(content_data) < 20:
            performance["improvements"].append("Collect more content examples for better predictions")

        if not historical_engagement:
            performance["improvements"].append("Include historical engagement data for enhanced accuracy")

        return performance

    def run(
        self,
        content_data: list[dict[str, Any]],
        audience_profiles: list[AudienceProfile] | None = None,
        historical_engagement: dict[str, Any] | None = None,
        prediction_config: dict[str, Any] | None = None,
        tenant: str = "default",
        workspace: str = "default",
        prediction_mode: str = "comprehensive",
    ) -> StepResult:
        """Public interface for engagement prediction."""
        return self._run(
            content_data,
            audience_profiles,
            historical_engagement,
            prediction_config,
            tenant,
            workspace,
            prediction_mode,
        )
