"""HippoRAG monitoring and alerting configuration.

This module defines Prometheus alerting rules for HippoRAG continual memory,
enabling early detection of memory degradation, performance issues, and system failures.

Alerts defined:
1. HippoRAGHighIndexingLatency: Indexing taking too long (p95 > 5s)
2. HippoRAGInitializationFailures: Repeated initialization failures
3. HippoRAGMemoryBloat: Unbounded memory growth
4. HippoRAGLowSuccessRate: Success rate below 90%
5. HippoRAGNoConsolidation: No consolidation activity for extended period

Integration:
- Export to Prometheus alert manager
- Trigger notifications via configured channels (Slack, PagerDuty, etc.)
- Dashboard annotations for visual correlation
"""

PROMETHEUS_ALERT_RULES = """
groups:
  - name: hipporag_continual_learning
    interval: 30s
    rules:
      # High indexing latency - indicates performance degradation
      - alert: HippoRAGHighIndexingLatency
        expr: histogram_quantile(0.95, rate(hipporag_indexing_latency_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
          component: hipporag
          category: performance
        annotations:
          summary: "HippoRAG indexing latency is high ({{ $value }}s)"
          description: "p95 indexing latency for namespace {{ $labels.namespace }} is {{ $value }}s, exceeding 5s threshold. This may indicate resource contention or model performance issues."
          dashboard: "/d/hipporag/hipporag-continual-learning-metrics"

      # Initialization failures - indicates configuration or dependency issues
      - alert: HippoRAGInitializationFailures
        expr: increase(hipporag_init_failures[15m]) > 5
        for: 5m
        labels:
          severity: critical
          component: hipporag
          category: availability
        annotations:
          summary: "HippoRAG initialization failures detected"
          description: "{{ $value }} initialization failures in the last 15 minutes for namespace {{ $labels.namespace }}. Check logs for missing dependencies or configuration errors."
          runbook: "https://docs.example.com/runbooks/hipporag-init-failures"

      # Memory bloat - unbounded growth indicates lack of consolidation
      - alert: HippoRAGMemoryBloat
        expr: rate(hipporag_memory_size_bytes[1h]) > 100000000  # 100MB/hour growth
        for: 2h
        labels:
          severity: warning
          component: hipporag
          category: resource
        annotations:
          summary: "HippoRAG memory growing rapidly"
          description: "Memory for namespace {{ $labels.namespace }} is growing at {{ $value | humanize }}B/s. Current size: {{ query \"hipporag_memory_size_bytes{namespace='\" }}{{ $labels.namespace }}{{ query \"'}\" | first | value | humanize }}B"
          remediation: "Consider enabling or tuning consolidation frequency."

      # Low success rate - indicates errors or fallback mode
      - alert: HippoRAGLowSuccessRate
        expr: |
          (
            rate(tool_runs_total{tool="hipporag_continual_memory",outcome="success"}[10m])
            /
            rate(tool_runs_total{tool="hipporag_continual_memory"}[10m])
          ) < 0.90
        for: 10m
        labels:
          severity: warning
          component: hipporag
          category: quality
        annotations:
          summary: "HippoRAG success rate below 90%"
          description: "Success rate is {{ $value | humanizePercentage }}. Check error logs and fallback rates."
          dashboard: "/d/hipporag/hipporag-continual-learning-metrics?viewPanel=5"

      # No consolidation activity - indicates disabled consolidation or stuck process
      - alert: HippoRAGNoConsolidation
        expr: rate(hipporag_consolidations_total[1h]) == 0
        for: 4h
        labels:
          severity: info
          component: hipporag
          category: learning
        annotations:
          summary: "No HippoRAG consolidation activity"
          description: "No memory consolidations detected for namespace {{ $labels.namespace }} in the past 4 hours. Continual learning may be disabled or stalled."

      # High fallback rate - indicates HippoRAG unavailability
      - alert: HippoRAGHighFallbackRate
        expr: |
          (
            rate(tool_runs_total{tool="hipporag_continual_memory",outcome="fallback"}[10m])
            /
            rate(tool_runs_total{tool="hipporag_continual_memory"}[10m])
          ) > 0.50
        for: 15m
        labels:
          severity: warning
          component: hipporag
          category: availability
        annotations:
          summary: "HippoRAG fallback rate exceeds 50%"
          description: "{{ $value | humanizePercentage }} of operations are using fallback storage. HippoRAG may be unavailable or misconfigured."
          remediation: "Check HippoRAG dependencies, model endpoints, and configuration."

      # Memory efficiency degradation - excessive storage per document
      - alert: HippoRAGMemoryInefficiency
        expr: (hipporag_memory_size_bytes / hipporag_document_count) > 10000000  # 10MB per document
        for: 30m
        labels:
          severity: info
          component: hipporag
          category: efficiency
        annotations:
          summary: "HippoRAG memory efficiency degraded"
          description: "Average storage per document is {{ $value | humanize }}B for namespace {{ $labels.namespace }}. This may indicate inefficient consolidation or duplicate storage."
          investigation: "Review consolidation settings and check for duplicate document indexing."
"""


def get_prometheus_alerts() -> str:
    """Return Prometheus alert rules in YAML format."""
    return PROMETHEUS_ALERT_RULES


def export_alerts_file(output_path: str = "alerts/hipporag_alerts.yml") -> None:
    """Export alert rules to a file for Prometheus configuration.

    Args:
        output_path: Path to write alert rules file
    """
    from pathlib import Path

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        f.write(get_prometheus_alerts())

    print(f"HippoRAG alert rules exported to {output_path}")


if __name__ == "__main__":
    # Export alerts for Prometheus configuration
    export_alerts_file()
    print("\nAlert rules ready for Prometheus Alert Manager integration.")
    print("Add to prometheus.yml:")
    print("  rule_files:")
    print("    - 'alerts/hipporag_alerts.yml'")
