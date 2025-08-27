import json
import pytest

from security.rbac import RBAC
from security.moderation import Moderation
from obs import logging as obs_logging


@pytest.fixture
def capture_logs(monkeypatch):
    records = []

    def fake_info(message: str, **fields):  # type: ignore[override]
        records.append({"msg": message, **fields})

    monkeypatch.setattr(obs_logging.logger, "info", fake_info)
    return records


def test_rbac_denial_logged(capture_logs):
    rbac = RBAC({"user": set()})
    wrapped = rbac.require("perm")(lambda: None)
    with pytest.raises(PermissionError):
        wrapped(roles=["user"], actor="alice", tenant="t1", workspace="w1")
    data = capture_logs[-1]
    assert data["msg"] == "security_event"
    assert data["action"] == "rbac"
    assert data["decision"] == "deny"
    assert data["resource"] == "perm"
    assert data["actor"] == "alice"
    assert data["tenant"] == "t1"
    assert data["workspace"] == "w1"


def test_moderation_logs_block(capture_logs):
    mod = Moderation(banned_terms=["bad"], action="block")
    res = mod.check("a BAD word")
    assert res.action == "block"
    data = capture_logs[-1]
    assert data["action"] == "moderation"
    assert data["decision"] == "block"
    assert data["reason"] == "banned_term"
    assert data["resource"] == "bad"
