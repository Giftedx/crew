import json
from pathlib import Path

import yaml

SNAPSHOT_PATH = Path(__file__).parent / "deprecations_snapshot.json"
DEP_FILE = Path("config/deprecations.yaml")
CHANGELOG = Path("CHANGELOG.md")


def _load_snapshot() -> dict[str, str]:
    return json.loads(SNAPSHOT_PATH.read_text()) if SNAPSHOT_PATH.exists() else {}


def _load_current() -> dict[str, str]:
    data = yaml.safe_load(DEP_FILE.read_text()) or {}
    flags = data.get("flags") or []
    current: dict[str, str] = {}
    for entry in flags:
        name = entry.get("name")
        remove_after = entry.get("remove_after")
    if isinstance(name, str) and isinstance(remove_after, str | int | float):
            # Only accept ISO date strings; ignore others for robustness
            current[name] = str(remove_after)
    return current


def _load_changelog() -> str:
    return CHANGELOG.read_text() if CHANGELOG.exists() else ""


def test_deprecation_dates_not_extended():
    """Fail if any removal date increases without explicit changelog note.

    Rationale: Prevent silent extension of deprecation periods. If extending
    a date, add a CHANGELOG line containing the symbol name and 'date update'
    (case-insensitive) to legitimize the change.
    """
    snapshot = _load_snapshot()
    current = _load_current()
    changelog = _load_changelog().lower()

    regressions: list[str] = []
    for name, old_date in snapshot.items():
        new_date = current.get(name)
        if (
            new_date
            and new_date > old_date  # lexicographic works for ISO YYYY-MM-DD
            and (name.lower() not in changelog or "date update" not in changelog)
        ):
            regressions.append(
                f"{name}: {old_date} -> {new_date} (missing changelog 'date update' note)"
            )
    assert not regressions, "\n" + "\n".join(regressions)


def test_snapshot_stays_in_sync():
    """Remind contributors to update snapshot when adding new deprecations."""
    snapshot = _load_snapshot()
    current = _load_current()
    missing = sorted(set(current) - set(snapshot))
    assert not missing, (
        "Snapshot missing entries: " + ", ".join(missing) +
        "; update tests/deprecations_snapshot.json to include new deprecations."
    )
