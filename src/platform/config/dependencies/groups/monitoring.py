"""Monitoring dependency group definitions."""

# Core monitoring dependencies
MONITORING_GROUP: set[str] = {
    "prometheus_client",
    "grafana_api",
    "datadog",
    "newrelic",
    "sentry-sdk",
    "opentelemetry-api",
    "opentelemetry-sdk",
    "opentelemetry-instrumentation",
}

# Optional monitoring dependencies
MONITORING_OPTIONAL: set[str] = {
    "jaeger-client",
    "zipkin",
    "elastic-apm",
    "rollbar",
    "bugsnag",
    "honeycomb-beeline",
    "lightstep",
}
