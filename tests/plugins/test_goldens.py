import json
from pathlib import Path

from ultimate_discord_intelligence_bot.plugins.testkit import goldens


def test_load_jsonl(tmp_path: Path) -> None:
    p = tmp_path / "sample.jsonl"
    with p.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps({"id": 1}) + "\n")
        fh.write("\n")
        fh.write(json.dumps({"id": 2}))
    records = goldens.load(str(p))
    assert records == [{"id": 1}, {"id": 2}]
