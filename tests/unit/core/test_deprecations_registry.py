import datetime as _dt
import re
from pathlib import Path

import yaml


DEP_FILE = Path("config/deprecations.yaml")

ALLOWED_STAGES = {"deprecated", "pending_removal", "removed"}
ISO_DATE_RE = re.compile(r"^20\d{2}-\d{2}-\d{2}$")
TODAY = _dt.date(2025, 8, 30)


def _load():
    with DEP_FILE.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def test_deprecations_file_structure():
    data = _load()
    flags = data.get("flags")
    assert isinstance(flags, list) and flags, "flags list must exist and be non-empty"
    for entry in flags:
        assert "name" in entry, "each entry needs name"
        assert entry.get("stage") in ALLOWED_STAGES, f"invalid stage for {entry.get('name')}"
        remove_after = entry.get("remove_after")
        # PyYAML may load ISO date as datetime.date; accept and normalize.
        if not isinstance(remove_after, str):
            # Attempt to serialize if it's a date-like object
            try:
                remove_after_str = remove_after.isoformat()
            except Exception:
                raise AssertionError(f"invalid date for {entry['name']}")
        else:
            remove_after_str = remove_after
        assert ISO_DATE_RE.match(remove_after_str), f"invalid date for {entry['name']}"
        # Replace entry value with normalized string for downstream logic
        entry["remove_after"] = remove_after_str
        # replacement required for deprecated or pending_removal stages
        if entry["stage"] in {"deprecated", "pending_removal"}:
            assert entry.get("replacement"), f"replacement required for {entry['name']}"
        # If removal date passed, stage must NOT still be plain deprecated
    ra_date = _dt.date.fromisoformat(remove_after_str)
    if ra_date < TODAY:
        assert entry["stage"] == "removed", f"{entry['name']} past removal date but not marked removed"
    # If marked removed, its code reference should generally be gone; we cannot
    # cheaply assert absence here without false positives (scanner handles),
    # but we at least enforce stage consistency above.
