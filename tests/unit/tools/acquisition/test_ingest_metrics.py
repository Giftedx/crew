from __future__ import annotations
import sys
import types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / 'src'))
from ultimate_discord_intelligence_bot.ingest import pipeline as ip
from platform.observability import metrics

class _CounterStub:

    def __init__(self) -> None:
        self.incs: int = 0
        self.last_labels: dict[str, str] | None = None

    def labels(self, **kwargs):
        self.last_labels = dict(kwargs)
        return self

    def inc(self) -> None:
        self.incs += 1

def test_ingest_transcript_fallback_metric(monkeypatch):
    prov = types.SimpleNamespace(fetch_metadata=lambda url: types.SimpleNamespace(id='id1', channel='c'), fetch_transcript=lambda url: None)
    monkeypatch.setattr(ip, '_get_provider', lambda src: (prov, 'channel'))
    stub = _CounterStub()
    monkeypatch.setattr(metrics, 'INGEST_TRANSCRIPT_FALLBACKS', stub)
    store = types.SimpleNamespace(upsert=lambda ns, recs: None)
    monkeypatch.setattr(ip.transcribe, 'run_whisper', lambda path: types.SimpleNamespace(segments=[]))
    job = ip.IngestJob(source='youtube', external_id='e', url='u', tenant='t', workspace='w', tags=[])
    ip.run(job, store)
    assert stub.incs == 1
    assert stub.last_labels and stub.last_labels.get('source') == 'youtube'

def test_ingest_missing_id_fallback_metric(monkeypatch):
    prov = types.SimpleNamespace(fetch_metadata=lambda url: types.SimpleNamespace(id=None, channel='c'), fetch_transcript=lambda url: 'hi\nthere')
    monkeypatch.setattr(ip, '_get_provider', lambda src: (prov, 'channel'))
    stub = _CounterStub()
    monkeypatch.setattr(metrics, 'INGEST_MISSING_ID_FALLBACKS', stub)
    store = types.SimpleNamespace(upsert=lambda ns, recs: None)
    job = ip.IngestJob(source='twitch', external_id='e', url='u', tenant='t', workspace='w', tags=[])
    ip.run(job, store)
    assert stub.incs == 1
    assert stub.last_labels and stub.last_labels.get('source') == 'twitch'