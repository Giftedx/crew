from security.rbac import RBAC
import pytest


def test_rbac_has_permission():
    rbac = RBAC(role_permissions={"ops": {"ingest.backfill"}, "viewer": set()})
    assert rbac.has_perm(["ops"], "ingest.backfill")
    assert not rbac.has_perm(["viewer"], "ingest.backfill")
    wildcard = RBAC(role_permissions={"admin": {"*"}})
    assert wildcard.has_perm(["admin"], "anything")


def test_rbac_require_decorator():
    rbac = RBAC(role_permissions={"ops": {"ingest.backfill"}})

    @rbac.require("ingest.backfill")
    def do_work():
        return "ok"

    assert do_work(roles=["ops"]) == "ok"
    with pytest.raises(PermissionError):
        do_work(roles=["viewer"])
    with pytest.raises(PermissionError):
        do_work()  # missing roles defaults to empty
