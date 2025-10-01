from __future__ import annotations

from memory import embeddings as emb
from memory import vector_store as vs
from ultimate_discord_intelligence_bot.step_result import StepResult


def test_autointel_vertical_slice_round_trip() -> None:
    # Build a minimal in-memory vertical slice: ingest -> memory -> retrieve -> answer
    store = vs.VectorStore()
    ns = vs.VectorStore.namespace("test", "main", "slice")

    # Ingest a simple document
    doc_text = "Python is a popular programming language created by Guido van Rossum."
    vec = emb.embed([doc_text])[0]
    store.upsert(ns, [vs.VectorRecord(vector=vec, payload={"text": doc_text, "title": "Python Intro"})])

    # Query
    q = emb.embed(["What is Python?"])[0]
    hits = store.query(ns, q, top_k=1)

    assert hits, "Expected at least one retrieval result"
    top = hits[0]
    payload = getattr(top, "payload", {}) or {}

    # Synthesize a minimal answer and citations using StepResult
    answer = f"Python is a programming language. Source: {payload.get('title', 'N/A')}"
    res = StepResult.ok(answer=answer, citations=[payload.get("text", "")], hits=len(hits))

    # Validate StepResult mapping/equality behavior
    assert res["status"] == "success"
    assert res["hits"] == 1
    assert "Python is a programming language" in res["answer"]
