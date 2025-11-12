from ultimate_discord_intelligence_bot.obs.metrics import get_metrics


def test_metrics_facade_helper_methods_execute_without_backend() -> None:
    metrics = get_metrics()

    # Should not raise even if no metrics backend is configured
    metrics.increment_counter("unit_test_counter", 2.0, labels={"tenant": "demo"})
    metrics.increment_counter("unit_test_counter")

    metrics.set_gauge("unit_test_gauge", 3.14, labels={"tenant": "demo"})
    metrics.set_gauge("unit_test_gauge", 0.0)

    metrics.observe_histogram("unit_test_histogram", 1.23, labels={"tenant": "demo"})
    metrics.observe_histogram("unit_test_histogram", 4.56)
