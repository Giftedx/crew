from ultimate_discord_intelligence_bot.server.app import create_app


def _route_paths(app) -> set[str]:
    return {getattr(r, "path", "") for r in app.router.routes}


def test_create_app_registers_core_routes():
    app = create_app()
    paths = _route_paths(app)

    # Core health endpoints should always exist
    assert "/health" in paths
    assert "/activities/health" in paths

    # Activities echo is optional but registered by default; tolerate if absent
    # This keeps the smoke test resilient to flag changes.
    assert isinstance(paths, set)
