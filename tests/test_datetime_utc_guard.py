from pathlib import Path


def test_analytics_module_uses_utc_now():
    """Ensure advanced_performance_analytics avoids naive datetime.now().

    Scope this guard narrowly to the analytics module we remediated, providing
    a regression check without breaking existing modules that still need cleanup.
    """
    repo = Path(__file__).resolve().parents[1]
    target = repo / "src/ultimate_discord_intelligence_bot/advanced_performance_analytics.py"
    text = target.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Simple state machine to ignore triple-quoted strings
    in_triple = False
    offenders = []
    for i, line in enumerate(lines, 1):
        if '"""' in line or "'''" in line:
            in_triple = not in_triple
        if in_triple:
            continue
        if "datetime.now(" in line and "UTC" not in line and "ensure_utc(" not in line:
            offenders.append((i, line.strip()))

    assert not offenders, "Naive datetime.now() remains in advanced_performance_analytics.py:\n" + "\n".join(
        f"L{ln}: {src}" for ln, src in offenders
    )

    assert "default_utc_now()" in text, "default_utc_now should be used in analytics timestamps"
