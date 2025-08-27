from __future__ import annotations

from kg import KGStore, extract, timeline, viz


def test_store_crud_and_neighbors():
    store = KGStore()
    a = store.add_node("t", "entity", "Alice")
    b = store.add_node("t", "episode", "Ep1")
    c = store.add_node("t", "episode", "Ep2")
    store.add_edge(a, b, "mentions", created_at="1")
    store.add_edge(a, c, "mentions", created_at="2")
    neigh = set(store.neighbors(a, depth=1))
    assert neigh == {b, c}


def test_extract_entities_claims():
    text = "Alice is great. Bob was here."
    entities, claims = extract(text)
    assert any(e.text == "Alice" for e in entities)
    assert any("was here" in c.text for c in claims)


def test_timeline_ordering():
    store = KGStore()
    ent = store.add_node("t", "entity", "Alice")
    ep1 = store.add_node("t", "episode", "Ep1")
    ep2 = store.add_node("t", "episode", "Ep2")
    store.add_edge(ent, ep2, "mentions", created_at="2")
    store.add_edge(ent, ep1, "mentions", created_at="1")
    events = timeline(store, "Alice", "t")
    assert [e.name for e in events] == ["Ep1", "Ep2"]


def test_viz_render():
    store = KGStore()
    a = store.add_node("t", "entity", "Alice")
    b = store.add_node("t", "entity", "Bob")
    store.add_edge(a, b, "knows")
    nodes = [store.get_node(a), store.get_node(b)]
    edges = store.query_edges()
    dot = viz.render(nodes, edges)
    assert b"Alice" in dot and b"Bob" in dot and b"knows" in dot
