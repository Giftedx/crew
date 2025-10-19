"""
Metrics endpoint for Prometheus scraping.

This module provides HTTP endpoints to expose application metrics
in Prometheus format for monitoring and alerting.
"""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, Response
from prometheus_client import CONTENT_TYPE_LATEST

from .metrics import (
    get_metrics_data,
)
from .slo import SLO, SLOEvaluator

logger = logging.getLogger(__name__)


def create_metrics_app() -> Flask:
    """Create Flask app for metrics endpoints."""
    app = Flask(__name__)

    @app.route("/metrics")
    def metrics() -> Response:
        """Prometheus metrics endpoint."""
        try:
            data = get_metrics_data()
            return Response(data, mimetype=CONTENT_TYPE_LATEST)
        except Exception:
            logger.error("Failed to generate metrics", exc_info=True)
            return Response("Internal Server Error", status=500)

    @app.route("/health")
    def health() -> dict[str, Any]:
        """Health check endpoint."""
        return {"status": "healthy", "service": "metrics"}

    @app.route("/slo/status")
    def slo_status() -> dict[str, Any]:
        """SLO status endpoint."""
        try:
            # Define SLOs based on docs/SLO_DOCUMENT.md
            slos = [
                SLO(metric="p95_latency", threshold=2.0),
                SLO(metric="vector_search_latency", threshold=0.05),
                SLO(metric="cache_hit_rate", threshold=0.6),
                SLO(metric="error_rate", threshold=0.01),
            ]

            evaluator = SLOEvaluator(slos)

            # For a real system, you would query Prometheus here
            # For now, we'll return a placeholder status
            current_metrics = {
                "p95_latency": 0.0,  # Would be calculated from REQUEST_LATENCY
                "vector_search_latency": 0.0,  # Would be calculated from VECTOR_SEARCH_LATENCY
                "cache_hit_rate": 0.0,  # Would be calculated from cache metrics
                "error_rate": 0.0,  # Would be calculated from ERROR_COUNT
            }

            results = evaluator.evaluate(current_metrics)

            return {
                "status": "healthy" if all(results.values()) else "degraded",
                "slos": results,
                "metrics": current_metrics,
            }

        except Exception as e:
            logger.error("Failed to evaluate SLOs", exc_info=True)
            return {"status": "error", "error": str(e)}

    return app


def run_metrics_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    """Run the metrics server."""
    app = create_metrics_app()
    logger.info(f"Starting metrics server on {host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_metrics_server()
