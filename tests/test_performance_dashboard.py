"""Tests for the performance dashboard API and integration."""

from __future__ import annotations

import pytest

from fastapi.testclient import TestClient
from server.app import create_app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    app = create_app()
    return TestClient(app)


class TestDashboardAPI:
    """Test suite for dashboard API endpoints."""

    def test_get_dashboard_data(self, client):
        """Test GET /api/performance/ returns complete dashboard data."""
        response = client.get("/api/performance/?hours=24")
        assert response.status_code == 200

        data = response.json()
        assert "overall_metrics" in data
        assert "content_type_breakdown" in data
        assert "checkpoint_analytics" in data
        assert "quality_trends" in data
        assert "generated_at" in data

        # Validate overall_metrics structure
        metrics = data["overall_metrics"]
        assert "total_processed" in metrics
        assert "quality_bypassed" in metrics
        assert "early_exits" in metrics
        assert "full_processing" in metrics
        assert "bypass_rate" in metrics
        assert "early_exit_rate" in metrics
        assert "avg_time_savings" in metrics
        assert "total_time_saved_hours" in metrics

    def test_get_metrics_summary(self, client):
        """Test GET /api/performance/metrics/summary endpoint."""
        response = client.get("/api/performance/metrics/summary")
        assert response.status_code == 200

        metrics = response.json()
        assert "total_processed" in metrics
        assert "bypass_rate" in metrics
        assert "avg_time_savings" in metrics

    def test_get_content_types(self, client):
        """Test GET /api/performance/content-types endpoint."""
        response = client.get("/api/performance/content-types")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_checkpoints(self, client):
        """Test GET /api/performance/checkpoints endpoint."""
        response = client.get("/api/performance/checkpoints")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_quality_trends(self, client):
        """Test GET /api/performance/quality-trends endpoint."""
        response = client.get("/api/performance/quality-trends?hours=24")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_record_pipeline_result(self, client):
        """Test POST /api/performance/record endpoint."""
        response = client.post(
            "/api/performance/record",
            params={
                "processing_type": "early_exit",
                "content_type": "discussion",
                "quality_score": 0.42,
                "processing_time": 35.2,
                "exit_checkpoint": "post_quality_filtering",
                "exit_reason": "low_quality",
                "exit_confidence": 0.85,
                "time_saved_pct": 0.75,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "recorded"
        assert data["processing_type"] == "early_exit"

    def test_record_updates_metrics(self, client):
        """Test that recording updates dashboard metrics."""
        # Reset metrics first
        client.delete("/api/performance/reset")

        # Record a result
        client.post(
            "/api/performance/record",
            params={
                "processing_type": "lightweight",
                "content_type": "entertainment",
                "quality_score": 0.35,
                "processing_time": 45.2,
                "time_saved_pct": 0.80,
            },
        )

        # Check metrics were updated
        response = client.get("/api/performance/metrics/summary")
        metrics = response.json()
        assert metrics["total_processed"] == 1
        assert metrics["quality_bypassed"] == 1
        assert metrics["bypass_rate"] == 1.0

    def test_reset_metrics(self, client):
        """Test DELETE /api/performance/reset endpoint."""
        # Record some data
        client.post(
            "/api/performance/record",
            params={"processing_type": "full", "time_saved_pct": 0.0},
        )

        # Reset
        response = client.delete("/api/performance/reset")
        assert response.status_code == 200
        assert response.json()["status"] == "reset"

        # Verify metrics are cleared
        metrics = client.get("/api/performance/metrics/summary").json()
        assert metrics["total_processed"] == 0

    def test_dashboard_page_endpoint(self, client):
        """Test that /dashboard serves HTML page."""
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestDashboardIntegration:
    """Test dashboard integration scenarios."""

    def test_multiple_content_types(self, client):
        """Test dashboard tracks multiple content types correctly."""
        client.delete("/api/performance/reset")

        # Record different content types
        for ct, quality in [
            ("discussion", 0.82),
            ("discussion", 0.78),
            ("entertainment", 0.35),
            ("news", 0.65),
        ]:
            client.post(
                "/api/performance/record",
                params={
                    "processing_type": "full" if quality > 0.65 else "lightweight",
                    "content_type": ct,
                    "quality_score": quality,
                    "processing_time": 100.0,
                },
            )

        # Check content type breakdown
        response = client.get("/api/performance/content-types")
        content_types = response.json()
        assert len(content_types) == 3

        # Find discussion type
        discussion = next((ct for ct in content_types if ct["content_type"] == "discussion"), None)
        assert discussion is not None
        assert discussion["count"] == 2
        assert discussion["avg_quality_score"] > 0.75

    def test_checkpoint_analytics(self, client):
        """Test checkpoint analytics tracking."""
        client.delete("/api/performance/reset")

        # Record early exits at different checkpoints
        checkpoints = [
            ("post_download", "too_short", 0.90),
            ("post_download", "too_short", 0.88),
            ("post_transcription", "low_confidence", 0.75),
            ("post_quality_filtering", "low_quality", 0.85),
        ]

        for cp, reason, confidence in checkpoints:
            client.post(
                "/api/performance/record",
                params={
                    "processing_type": "early_exit",
                    "exit_checkpoint": cp,
                    "exit_reason": reason,
                    "exit_confidence": confidence,
                },
            )

        # Check checkpoint analytics
        response = client.get("/api/performance/checkpoints")
        analytics = response.json()
        assert len(analytics) == 3

        # Find post_download checkpoint
        post_download = next((cp for cp in analytics if cp["checkpoint_name"] == "post_download"), None)
        assert post_download is not None
        assert post_download["exit_count"] == 2
        assert len(post_download["top_exit_reasons"]) > 0
        assert post_download["top_exit_reasons"][0]["reason"] == "too_short"

    def test_time_savings_calculation(self, client):
        """Test time savings are calculated correctly."""
        client.delete("/api/performance/reset")

        # Record items with different time savings
        savings = [0.75, 0.80, 0.60, 0.90, 0.70]
        for saving in savings:
            client.post(
                "/api/performance/record",
                params={
                    "processing_type": "early_exit",
                    "time_saved_pct": saving,
                },
            )

        # Check average
        response = client.get("/api/performance/metrics/summary")
        metrics = response.json()
        expected_avg = sum(savings) / len(savings)
        assert abs(metrics["avg_time_savings"] - expected_avg) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
