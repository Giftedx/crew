from debate.panel import PanelConfig, run_panel
from debate.store import Debate, DebateStore
from discord import commands as dc
from ultimate_discord_intelligence_bot.core.learning_engine import LearningEngine
from ultimate_discord_intelligence_bot.core.router import Router


class DummyRouter(Router):
    def __init__(self):
        super().__init__(LearningEngine())

    def route(self, task, candidates, context):
        return candidates[0]


def dummy_call(model: str, prompt: str) -> str:
    return f"{model}:{prompt}"[:20]


def test_run_panel_basic():
    router = DummyRouter()
    cfg = PanelConfig(roles=["steelman", "skeptic"], n_rounds=1)
    report = run_panel("question?", router, dummy_call, cfg)
    assert len(report.agents) == 2
    assert report.final


def test_store_round_trip(tmp_path):
    db = DebateStore(tmp_path / "debate.db")
    d = Debate(
        id=None,
        tenant="t1",
        workspace="w",
        query="q",
        panel_config_json="{}",
        n_rounds=1,
        final_output="ans",
        created_at="now",
    )
    debate_id = db.add_debate(d)
    rows = db.list_debates("t1", "w")
    assert rows[0].id == debate_id


def test_ops_debate_run_and_inspect():
    dc._DEBATE_STORE = DebateStore()
    res = dc.ops_debate_run("q", ["steelman", "skeptic"])
    assert res["final"]
    rid = res["id"]
    details = dc.ops_debate_inspect(rid)
    assert details["final"] == res["final"]
    assert res["status"]["debate"]["arms"]["panel"]["q"] >= 0


def test_ops_debate_stats():
    dc._DEBATE_STORE = DebateStore()
    dc.ops_debate_run("q1", ["steelman", "skeptic"])
    dc.ops_debate_run("q2", ["steelman", "skeptic"])
    stats = dc.ops_debate_stats()
    assert stats["count"] == 2
    assert stats["avg_rounds"] >= 1
