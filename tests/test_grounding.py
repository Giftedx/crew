from discord import commands as cmds
from grounding import contracts, retriever, verifier
from grounding.schema import Evidence
from memory import MemoryStore, vector_store
from memory import api as memory_api
from prompt_engine import guards


def test_contract_requires_citations():
    ev = [Evidence(source_type="url", locator={"t_start": 0}) for _ in range(3)]
    contract = contracts.build_contract("ok [1][2][3]", ev, use_case="context")
    report = verifier.verify(contract, use_case="context")
    assert report.verdict == "pass"


def test_contract_fails_when_missing_citations():
    ev = [Evidence(source_type="url", locator={"t_start": 0})]
    try:
        contracts.build_contract("bad", ev, use_case="context")
    except contracts.GroundingError:
        pass
    else:  # pragma: no cover
        assert False, "expected GroundingError"


def test_retriever_and_audit():
    mstore = MemoryStore(":memory:")
    vstore = vector_store.VectorStore()
    for txt in ["cats purr", "cats meow", "cats sleep"]:
        memory_api.store(mstore, vstore, tenant="t", workspace="w", text=txt)
    pack = retriever.gather(mstore, vstore, tenant="t", workspace="w", query="cats", k=3)
    contract = contracts.build_contract(
        "Cats make sounds [1][2][3]", pack.snippets, use_case="context"
    )
    report = verifier.verify(contract, use_case="context")
    audit = cmds.ops_grounding_audit(contract, report)
    assert audit["verdict"] == "pass"
    assert len(audit["citations"]) >= 3


def test_prompt_guard():
    assert guards.has_min_citations("hello [1] [2]", 2)
    assert not guards.has_min_citations("hello [1]", 2)
