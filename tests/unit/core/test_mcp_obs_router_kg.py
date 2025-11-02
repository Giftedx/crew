import pytest
pytest.importorskip('fastmcp', reason='FastMCP optional extra not installed')

def test_obs_summarize_health_shape():
    from mcp_server.obs_server import summarize_health
    out = summarize_health()
    assert isinstance(out, dict)
    assert 'status' in out
    assert 'prometheus_available' in out

def test_router_estimate_and_choose():
    from mcp_server.routing_server import choose_embedding_model, estimate_cost, route_completion
    est = estimate_cost(model='gpt-4o-mini', input_tokens=1000, output_tokens=200)
    assert isinstance(est, dict)
    assert 'usd' in est or 'cost_usd' in est
    emb = choose_embedding_model()
    assert isinstance(emb, dict)
    assert 'dimensions' in emb
    rc = route_completion(task='short_summary', tokens_hint=500)
    assert isinstance(rc, dict)
    assert 'model' in rc and 'est_cost_usd' in rc

def test_kg_tools_dont_crash():
    from mcp_server.kg_server import kg_query, kg_timeline
    q = kg_query('tenantA', 'Nonexistent', depth=1)
    assert isinstance(q, dict)
    assert 'nodes' in q and 'edges' in q
    t = kg_timeline('tenantA', 'Nonexistent')
    assert isinstance(t, dict)
    assert 'events' in t