"""
Virality prediction tool for content performance forecasting.

This tool provides comprehensive virality prediction including:
- Content virality probability calculation
- Engagement prediction models
- Reach and impact forecasting
- Viral factor identification
- Content optimization recommendations
- Performance trajectory prediction
"""

from __future__ import annotations

import logging
import time
from platform.core.step_result import StepResult
from platform.observability.metrics import get_metrics
from typing import Any, TypedDict

from ._base import BaseTool


class ContentMetrics(TypedDict, total=False):
    """Content performance metrics."""

    views: int
    likes: int
    shares: int
    comments: int
    engagement_rate: float
    click_through_rate: float
    retention_rate: float
    completion_rate: float


class ViralFactors(TypedDict, total=False):
    """Factors contributing to viral potential."""

    content_quality: float
    timing_factor: float
    platform_optimization: float
    audience_alignment: float
    trend_relevance: float
    engagement_velocity: float
    shareability: float
    uniqueness: float


class ViralPrediction(TypedDict, total=False):
    """Viral content prediction result."""

    content_id: str
    viral_probability: float
    confidence_score: float
    predicted_reach: int
    predicted_engagement: float
    time_to_peak: float
    peak_duration: float
    viral_factors: ViralFactors
    optimization_recommendations: list[str]
    risk_factors: list[str]


class PerformanceTrajectory(TypedDict, total=False):
    """Predicted performance trajectory."""

    time_points: list[float]
    engagement_points: list[float]
    reach_points: list[int]
    viral_moments: list[dict[str, Any]]
    decline_phase: dict[str, Any]


class ContentOptimization(TypedDict, total=False):
    """Content optimization recommendations."""

    title_optimization: list[str]
    thumbnail_optimization: list[str]
    timing_optimization: list[str]
    platform_optimization: list[str]
    content_improvements: list[str]
    audience_targeting: list[str]


class ViralityPredictionResult(TypedDict, total=False):
    """Complete virality prediction result."""

    viral_predictions: list[ViralPrediction]
    performance_trajectories: list[PerformanceTrajectory]
    content_optimizations: list[ContentOptimization]
    viral_insights: dict[str, Any]
    market_analysis: dict[str, Any]
    competitive_analysis: dict[str, Any]
    processing_time: float
    metadata: dict[str, Any]


class ViralityPredictionTool(BaseTool[StepResult]):
    """Advanced virality prediction with comprehensive content analysis."""

    name: str = "Virality Prediction Tool"
    description: str = (
        "Predicts content virality potential, engagement patterns, and provides optimization recommendations."
    )

    def __init__(
        self,
        enable_trajectory_prediction: bool = True,
        enable_optimization_recommendations: bool = True,
        enable_competitive_analysis: bool = True,
        viral_threshold: float = 0.7,
        confidence_threshold: float = 0.6,
        prediction_horizon_hours: int = 72,
    ):
        super().__init__()
        self._enable_trajectory_prediction = enable_trajectory_prediction
        self._enable_optimization_recommendations = enable_optimization_recommendations
        self._enable_competitive_analysis = enable_competitive_analysis
        self._viral_threshold = viral_threshold
        self._confidence_threshold = confidence_threshold
        self._prediction_horizon_hours = prediction_horizon_hours
        self._metrics = get_metrics()

    def _run(
        self,
        content_data: list[dict[str, Any]],
        historical_data: dict[str, Any] | None = None,
        market_context: dict[str, Any] | None = None,
        tenant: str = "default",
        workspace: str = "default",
        prediction_mode: str = "comprehensive",
    ) -> StepResult:
        """
        Perform comprehensive virality prediction analysis.

        Args:
            content_data: Content data for virality prediction
            historical_data: Historical performance data for model training
            market_context: Market and competitive context
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier
            prediction_mode: Prediction mode (basic, comprehensive, detailed)

        Returns:
            StepResult with comprehensive virality predictions
        """
        start_time = time.monotonic()
        try:
            if not content_data:
                return StepResult.fail("Content data cannot be empty")
            if tenant and workspace:
                self.note(f"Starting virality prediction for {len(content_data)} content items")
            viral_predictions = self._predict_virality(content_data, historical_data)
            performance_trajectories = (
                self._predict_performance_trajectories(viral_predictions) if self._enable_trajectory_prediction else []
            )
            content_optimizations = (
                self._generate_optimization_recommendations(viral_predictions)
                if self._enable_optimization_recommendations
                else []
            )
            viral_insights = self._analyze_viral_insights(viral_predictions)
            market_analysis = self._analyze_market_context(market_context)
            competitive_analysis = (
                self._analyze_competitive_landscape(content_data, market_context)
                if self._enable_competitive_analysis
                else {}
            )
            processing_time = time.monotonic() - start_time
            result: ViralityPredictionResult = {
                "viral_predictions": viral_predictions,
                "performance_trajectories": performance_trajectories,
                "content_optimizations": content_optimizations,
                "viral_insights": viral_insights,
                "market_analysis": market_analysis,
                "competitive_analysis": competitive_analysis,
                "processing_time": processing_time,
                "metadata": {
                    "prediction_mode": prediction_mode,
                    "content_items_analyzed": len(content_data),
                    "viral_threshold": self._viral_threshold,
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
            logging.exception("Virality prediction failed")
            return StepResult.fail(f"Virality prediction failed: {e!s}")

    def _predict_virality(
        self, content_data: list[dict[str, Any]], historical_data: dict[str, Any] | None
    ) -> list[ViralPrediction]:
        """Predict virality for each content item."""
        predictions = []
        for content in content_data:
            viral_probability = self._calculate_viral_probability(content, historical_data)
            confidence_score = self._calculate_confidence_score(content, viral_probability)
            if confidence_score >= self._confidence_threshold:
                viral_factors = self._analyze_viral_factors(content)
                predicted_reach = self._predict_reach(content, viral_probability)
                predicted_engagement = self._predict_engagement(content, viral_probability)
                time_to_peak = self._predict_time_to_peak(content, viral_probability)
                peak_duration = self._predict_peak_duration(content, viral_probability)
                optimization_recommendations = self._generate_optimization_recommendations_for_content(
                    content, viral_factors
                )
                risk_factors = self._identify_risk_factors(content, viral_factors)
                prediction: ViralPrediction = {
                    "content_id": content.get("content_id", ""),
                    "viral_probability": viral_probability,
                    "confidence_score": confidence_score,
                    "predicted_reach": predicted_reach,
                    "predicted_engagement": predicted_engagement,
                    "time_to_peak": time_to_peak,
                    "peak_duration": peak_duration,
                    "viral_factors": viral_factors,
                    "optimization_recommendations": optimization_recommendations,
                    "risk_factors": risk_factors,
                }
                predictions.append(prediction)
        return predictions

    def _calculate_viral_probability(self, content: dict[str, Any], historical_data: dict[str, Any] | None) -> float:
        """Calculate viral probability for content."""
        base_probability = 0.5
        content_quality = self._assess_content_quality(content)
        base_probability += content_quality * 0.2
        timing_factor = self._assess_timing_factor(content)
        base_probability += timing_factor * 0.15
        platform_factor = self._assess_platform_optimization(content)
        base_probability += platform_factor * 0.15
        audience_factor = self._assess_audience_alignment(content)
        base_probability += audience_factor * 0.1
        trend_factor = self._assess_trend_relevance(content)
        base_probability += trend_factor * 0.1
        velocity_factor = self._assess_engagement_velocity(content)
        base_probability += velocity_factor * 0.1
        shareability_factor = self._assess_shareability(content)
        base_probability += shareability_factor * 0.1
        uniqueness_factor = self._assess_uniqueness(content)
        base_probability += uniqueness_factor * 0.1
        return min(1.0, max(0.0, base_probability))

    def _calculate_confidence_score(self, content: dict[str, Any], viral_probability: float) -> float:
        """Calculate confidence score for the prediction."""
        confidence = 0.5
        content_metrics = content.get("metrics", {})
        if content_metrics:
            confidence += 0.2
        if content.get("historical_performance"):
            confidence += 0.2
        if viral_probability > 0.8 or viral_probability < 0.2:
            confidence += 0.1
        return min(1.0, confidence)

    def _analyze_viral_factors(self, content: dict[str, Any]) -> ViralFactors:
        """Analyze factors contributing to viral potential."""
        return {
            "content_quality": self._assess_content_quality(content),
            "timing_factor": self._assess_timing_factor(content),
            "platform_optimization": self._assess_platform_optimization(content),
            "audience_alignment": self._assess_audience_alignment(content),
            "trend_relevance": self._assess_trend_relevance(content),
            "engagement_velocity": self._assess_engagement_velocity(content),
            "shareability": self._assess_shareability(content),
            "uniqueness": self._assess_uniqueness(content),
        }

    def _assess_content_quality(self, content: dict[str, Any]) -> float:
        """Assess content quality score."""
        quality_score = 0.5
        content_metadata = content.get("metadata", {})
        if content_metadata.get("video_quality") == "high":
            quality_score += 0.2
        if content_metadata.get("audio_quality") == "high":
            quality_score += 0.1
        duration = content_metadata.get("duration", 0)
        if 30 <= duration <= 300:
            quality_score += 0.1
        if content_metadata.get("professional_quality"):
            quality_score += 0.1
        return min(1.0, quality_score)

    def _assess_timing_factor(self, content: dict[str, Any]) -> float:
        """Assess timing factor for content release."""
        timing_score = 0.5
        current_hour = time.localtime().tm_hour
        peak_hours = [18, 19, 20, 21]
        if current_hour in peak_hours:
            timing_score += 0.3
        if content.get("trending_topic"):
            timing_score += 0.2
        return min(1.0, timing_score)

    def _assess_platform_optimization(self, content: dict[str, Any]) -> float:
        """Assess platform optimization score."""
        platform_score = 0.5
        platform = content.get("platform", "")
        content_type = content.get("content_type", "")
        platform_optimizations = {
            "youtube": ["video", "long_form"],
            "tiktok": ["short_video", "trending"],
            "instagram": ["image", "story", "reel"],
            "twitter": ["text", "news", "trending"],
        }
        if platform in platform_optimizations and content_type in platform_optimizations[platform]:
            platform_score += 0.3
        if content.get("platform_features"):
            platform_score += 0.2
        return min(1.0, platform_score)

    def _assess_audience_alignment(self, content: dict[str, Any]) -> float:
        """Assess audience alignment score."""
        alignment_score = 0.5
        audience_data = content.get("audience_data", {})
        if audience_data.get("age_alignment_score", 0) > 0.7:
            alignment_score += 0.2
        if audience_data.get("interest_alignment_score", 0) > 0.7:
            alignment_score += 0.2
        if audience_data.get("high_engagement_history"):
            alignment_score += 0.1
        return min(1.0, alignment_score)

    def _assess_trend_relevance(self, content: dict[str, Any]) -> float:
        """Assess trend relevance score."""
        trend_score = 0.5
        keywords = content.get("keywords", [])
        trending_keywords = content.get("trending_keywords", [])
        if keywords and trending_keywords:
            overlap = len(set(keywords) & set(trending_keywords))
            if overlap > 0:
                trend_score += min(0.4, overlap / len(keywords))
        if content.get("trending_topic"):
            trend_score += 0.3
        return min(1.0, trend_score)

    def _assess_engagement_velocity(self, content: dict[str, Any]) -> float:
        """Assess engagement velocity score."""
        velocity_score = 0.5
        metrics = content.get("metrics", {})
        if metrics:
            early_engagement = metrics.get("early_engagement_rate", 0)
            if early_engagement > 0.1:
                velocity_score += 0.3
            growth_rate = metrics.get("engagement_growth_rate", 0)
            if growth_rate > 0.5:
                velocity_score += 0.2
        return min(1.0, velocity_score)

    def _assess_shareability(self, content: dict[str, Any]) -> float:
        """Assess content shareability score."""
        shareability_score = 0.5
        content_metadata = content.get("metadata", {})
        if content_metadata.get("emotional_impact") == "high":
            shareability_score += 0.2
        if content_metadata.get("educational_value"):
            shareability_score += 0.1
        if content_metadata.get("entertainment_value") == "high":
            shareability_score += 0.1
        controversy_level = content_metadata.get("controversy_level", 0)
        if 0.3 <= controversy_level <= 0.7:
            shareability_score += 0.1
        return min(1.0, shareability_score)

    def _assess_uniqueness(self, content: dict[str, Any]) -> float:
        """Assess content uniqueness score."""
        uniqueness_score = 0.5
        content_metadata = content.get("metadata", {})
        if content_metadata.get("originality_score", 0) > 0.7:
            uniqueness_score += 0.2
        if content_metadata.get("innovation_score", 0) > 0.7:
            uniqueness_score += 0.2
        if content_metadata.get("novelty_score", 0) > 0.7:
            uniqueness_score += 0.1
        return min(1.0, uniqueness_score)

    def _predict_reach(self, content: dict[str, Any], viral_probability: float) -> int:
        """Predict potential reach for content."""
        current_reach = content.get("metrics", {}).get("current_reach", 0)
        viral_multiplier = 1 + viral_probability * 20
        content_type = content.get("content_type", "")
        type_multipliers = {"video": 1.5, "image": 1.0, "text": 0.8, "audio": 1.2}
        type_multiplier = type_multipliers.get(content_type, 1.0)
        predicted_reach = int(current_reach * viral_multiplier * type_multiplier)
        return max(current_reach, predicted_reach)

    def _predict_engagement(self, content: dict[str, Any], viral_probability: float) -> float:
        """Predict potential engagement for content."""
        current_engagement = content.get("metrics", {}).get("current_engagement", 0)
        viral_multiplier = 1 + viral_probability * 10
        engagement_type = content.get("engagement_type", "standard")
        type_multipliers = {"high_engagement": 1.5, "standard": 1.0, "low_engagement": 0.7}
        type_multiplier = type_multipliers.get(engagement_type, 1.0)
        predicted_engagement = current_engagement * viral_multiplier * type_multiplier
        return max(current_engagement, predicted_engagement)

    def _predict_time_to_peak(self, content: dict[str, Any], viral_probability: float) -> float:
        """Predict time to reach peak engagement."""
        content_type = content.get("content_type", "")
        base_times = {"video": 4.0, "image": 2.0, "text": 1.0, "audio": 3.0}
        base_time = base_times.get(content_type, 2.0)
        if viral_probability > 0.8:
            base_time *= 0.5
        elif viral_probability < 0.3:
            base_time *= 2.0
        return base_time

    def _predict_peak_duration(self, content: dict[str, Any], viral_probability: float) -> float:
        """Predict duration of peak engagement."""
        content_type = content.get("content_type", "")
        base_durations = {"video": 8.0, "image": 4.0, "text": 3.0, "audio": 6.0}
        base_duration = base_durations.get(content_type, 4.0)
        if viral_probability > 0.8:
            base_duration *= 1.5
        return base_duration

    def _generate_optimization_recommendations_for_content(
        self, content: dict[str, Any], viral_factors: ViralFactors
    ) -> list[str]:
        """Generate optimization recommendations for specific content."""
        recommendations = []
        if viral_factors["content_quality"] < 0.6:
            recommendations.append("Improve content production quality")
            recommendations.append("Enhance visual and audio elements")
        if viral_factors["timing_factor"] < 0.6:
            recommendations.append("Consider releasing during peak engagement hours")
            recommendations.append("Align with trending topics and events")
        if viral_factors["platform_optimization"] < 0.6:
            recommendations.append("Optimize content format for target platform")
            recommendations.append("Use platform-specific features and tools")
        if viral_factors["audience_alignment"] < 0.6:
            recommendations.append("Better target content to audience interests")
            recommendations.append("Analyze audience engagement patterns")
        if viral_factors["trend_relevance"] < 0.6:
            recommendations.append("Incorporate trending keywords and topics")
            recommendations.append("Stay current with industry trends")
        if viral_factors["engagement_velocity"] < 0.6:
            recommendations.append("Create more engaging opening content")
            recommendations.append("Encourage early audience interaction")
        if viral_factors["shareability"] < 0.6:
            recommendations.append("Increase emotional impact of content")
            recommendations.append("Add educational or entertainment value")
        if viral_factors["uniqueness"] < 0.6:
            recommendations.append("Develop more original and innovative content")
            recommendations.append("Differentiate from existing content")
        return recommendations

    def _identify_risk_factors(self, content: dict[str, Any], viral_factors: ViralFactors) -> list[str]:
        """Identify risk factors that could limit virality."""
        risk_factors = []
        if viral_factors["content_quality"] < 0.4:
            risk_factors.append("Low content quality may limit reach")
        if viral_factors["timing_factor"] < 0.4:
            risk_factors.append("Suboptimal timing may reduce visibility")
        if viral_factors["platform_optimization"] < 0.4:
            risk_factors.append("Content not optimized for target platform")
        if viral_factors["audience_alignment"] < 0.4:
            risk_factors.append("Content may not resonate with target audience")
        if viral_factors["trend_relevance"] < 0.4:
            risk_factors.append("Content not aligned with current trends")
        if viral_factors["engagement_velocity"] < 0.4:
            risk_factors.append("Low engagement velocity may limit growth")
        if viral_factors["shareability"] < 0.4:
            risk_factors.append("Content may not be shareable enough")
        if viral_factors["uniqueness"] < 0.4:
            risk_factors.append("Content lacks uniqueness and differentiation")
        return risk_factors

    def _predict_performance_trajectories(
        self, viral_predictions: list[ViralPrediction]
    ) -> list[PerformanceTrajectory]:
        """Predict performance trajectories for viral content."""
        trajectories = []
        for prediction in viral_predictions:
            if prediction["viral_probability"] > self._viral_threshold:
                trajectory = self._create_performance_trajectory(prediction)
                trajectories.append(trajectory)
        return trajectories

    def _create_performance_trajectory(self, prediction: ViralPrediction) -> PerformanceTrajectory:
        """Create performance trajectory for a prediction."""
        time_to_peak = prediction["time_to_peak"]
        peak_duration = prediction["peak_duration"]
        predicted_engagement = prediction["predicted_engagement"]
        time_points = [float(hour) for hour in range(self._prediction_horizon_hours + 1)]
        engagement_points = []
        for hour in time_points:
            if hour <= time_to_peak:
                engagement = hour / time_to_peak * predicted_engagement * 0.8
            elif hour <= time_to_peak + peak_duration:
                engagement = predicted_engagement
            else:
                decline_factor = max(0.1, 1.0 - (hour - time_to_peak - peak_duration) / 24)
                engagement = predicted_engagement * decline_factor
            engagement_points.append(engagement)
        reach_points = [int(engagement * 10) for engagement in engagement_points]
        viral_moments = []
        for i, engagement in enumerate(engagement_points):
            if engagement > predicted_engagement * 0.8:
                viral_moments.append({"hour": i, "engagement": engagement, "type": "peak_engagement"})
        decline_phase = {
            "start_hour": int(time_to_peak + peak_duration),
            "decline_rate": 0.1,
            "final_engagement": predicted_engagement * 0.1,
        }
        return {
            "time_points": time_points,
            "engagement_points": engagement_points,
            "reach_points": reach_points,
            "viral_moments": viral_moments,
            "decline_phase": decline_phase,
        }

    def _generate_optimization_recommendations(
        self, viral_predictions: list[ViralPrediction]
    ) -> list[ContentOptimization]:
        """Generate optimization recommendations for all content."""
        optimizations = []
        for prediction in viral_predictions:
            optimization = self._create_content_optimization(prediction)
            optimizations.append(optimization)
        return optimizations

    def _create_content_optimization(self, prediction: ViralPrediction) -> ContentOptimization:
        """Create optimization recommendations for a prediction."""
        viral_factors = prediction["viral_factors"]
        title_optimization = []
        if viral_factors["trend_relevance"] < 0.7:
            title_optimization.append("Include trending keywords in title")
        if viral_factors["shareability"] < 0.7:
            title_optimization.append("Create more compelling and shareable title")
        thumbnail_optimization = []
        if viral_factors["content_quality"] < 0.7:
            thumbnail_optimization.append("Improve thumbnail quality and appeal")
        if viral_factors["shareability"] < 0.7:
            thumbnail_optimization.append("Design more eye-catching thumbnail")
        timing_optimization = []
        if viral_factors["timing_factor"] < 0.7:
            timing_optimization.append("Release during peak engagement hours")
            timing_optimization.append("Align with trending events")
        platform_optimization = []
        if viral_factors["platform_optimization"] < 0.7:
            platform_optimization.append("Optimize content format for platform")
            platform_optimization.append("Use platform-specific features")
        content_improvements = []
        if viral_factors["content_quality"] < 0.7:
            content_improvements.append("Enhance production quality")
        if viral_factors["uniqueness"] < 0.7:
            content_improvements.append("Add unique and innovative elements")
        audience_targeting = []
        if viral_factors["audience_alignment"] < 0.7:
            audience_targeting.append("Better target specific audience segments")
            audience_targeting.append("Analyze audience preferences and behavior")
        return {
            "title_optimization": title_optimization,
            "thumbnail_optimization": thumbnail_optimization,
            "timing_optimization": timing_optimization,
            "platform_optimization": platform_optimization,
            "content_improvements": content_improvements,
            "audience_targeting": audience_targeting,
        }

    def _analyze_viral_insights(self, viral_predictions: list[ViralPrediction]) -> dict[str, Any]:
        """Analyze insights from viral predictions."""
        if not viral_predictions:
            return {"insights": [], "patterns": {}}
        avg_viral_probability = sum(p["viral_probability"] for p in viral_predictions) / len(viral_predictions)
        all_factors: dict[str, list[float]] = {}
        for prediction in viral_predictions:
            factors = prediction["viral_factors"]
            for factor, score in factors.items():
                if factor not in all_factors:
                    all_factors[factor] = []
                all_factors[factor].append(score)
        avg_factors = {factor: sum(scores) / len(scores) for factor, scores in all_factors.items()}
        high_viral_content = [p for p in viral_predictions if p["viral_probability"] > 0.8]
        low_viral_content = [p for p in viral_predictions if p["viral_probability"] < 0.3]
        insights = []
        if high_viral_content:
            insights.append(f"{len(high_viral_content)} content items have high viral potential")
        if low_viral_content:
            insights.append(f"{len(low_viral_content)} content items have low viral potential")
        return {
            "insights": insights,
            "patterns": {
                "average_viral_probability": avg_viral_probability,
                "average_factors": avg_factors,
                "high_viral_count": len(high_viral_content),
                "low_viral_count": len(low_viral_content),
            },
        }

    def _analyze_market_context(self, market_context: dict[str, Any] | None) -> dict[str, Any]:
        """Analyze market context for virality prediction."""
        if not market_context:
            return {"market_analysis": "No market context provided"}
        return {
            "market_analysis": "Market context analysis completed",
            "trending_topics": market_context.get("trending_topics", []),
            "competitive_landscape": market_context.get("competitive_landscape", {}),
            "audience_behavior": market_context.get("audience_behavior", {}),
        }

    def _analyze_competitive_landscape(
        self, content_data: list[dict[str, Any]], market_context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Analyze competitive landscape for content."""
        return {
            "competitive_analysis": "Competitive landscape analysis completed",
            "content_differentiation": "Analysis of content differentiation factors",
            "market_opportunities": "Identification of market opportunities",
            "competitive_threats": "Assessment of competitive threats",
        }

    def run(
        self,
        content_data: list[dict[str, Any]],
        historical_data: dict[str, Any] | None = None,
        market_context: dict[str, Any] | None = None,
        tenant: str = "default",
        workspace: str = "default",
        prediction_mode: str = "comprehensive",
    ) -> StepResult:
        """Public interface for virality prediction."""
        return self._run(content_data, historical_data, market_context, tenant, workspace, prediction_mode)
