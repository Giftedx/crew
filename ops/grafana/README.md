# Grafana Dashboards

Import the JSON dashboards into Grafana and select your Prometheus datasource.

- LLM Routing Overview: `ops/grafana/dashboards/llm_routing_overview.json`
  - Panels: selections by model/provider, avg estimated cost per call, budget rejections, cache hit rate, latency p95
  - Templates: `tenant`, `workspace`, `task`
- HTTP Retries & Latency: `ops/grafana/dashboards/http_retries.json`
  - Panels: retry attempts/giveups by method, HTTP latency p95

Steps:
1. Grafana → Dashboards → New → Import
2. Upload JSON file, set `DS_PROMETHEUS` to your Prometheus datasource
3. Save dashboard

# Alerting

Prometheus alert rules are provided under `ops/alerts/prometheus/alerts.yml`.

- LLM budget rejections rate
- LLM latency p95 threshold
- LLM cache hit rate threshold
- HTTP retries exhausted

Load rules:
- promtool check rules ops/alerts/prometheus/alerts.yml
- Add to Prometheus config under `rule_files:`

# Alertmanager (example)

For Slack (incoming webhook):
```yaml
route:
  group_by: [alertname]
  receiver: slack
receivers:
  - name: slack
    slack_configs:
      - send_resolved: true
        channel: "#alerts"
        username: "alertmanager"
        api_url: "https://hooks.slack.com/services/..."
```

For a generic webhook adapter (e.g., to forward to Discord):
```yaml
route:
  receiver: webhook
receivers:
  - name: webhook
    webhook_configs:
      - url: "http://adapter:8080/alert"
        send_resolved: true
```

Note: Discord requires a specific JSON shape; use an adapter or a dedicated integration.
