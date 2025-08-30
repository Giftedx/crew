from grounding.contracts import build_contract
from grounding.schema import Evidence


def test_build_contract_appends_numeric_citations():
    ev = [Evidence(source_type="doc"), Evidence(source_type="web"), Evidence(source_type="pdf")]
    contract = build_contract("Answer body", ev, use_case="default")
    assert contract.answer_text.endswith("[1][2][3]"), contract.answer_text
    assert contract.answer_text.startswith("Answer body")


def test_build_contract_idempotent_when_already_has_tail():
    ev = [Evidence(source_type="doc"), Evidence(source_type="web")]
    # Pre-supplied answer already has correct tail
    contract = build_contract("Body [1][2]", ev, use_case="default")
    assert contract.answer_text == "Body [1][2]"
