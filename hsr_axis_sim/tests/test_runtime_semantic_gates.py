import pytest

from hsr_axis_sim.runtime_contracts import (
    BindingStatus,
    EvidenceStatus,
    SemanticContract,
    UnresolvedMechanicError,
)


LEGAL = [
    (EvidenceStatus.CONFIRMED, BindingStatus.BOUND, "policy", ("source-b", "source-a")),
    (EvidenceStatus.CONFIRMED, BindingStatus.INTERFACE_ONLY, None, ()),
    (EvidenceStatus.CONFIRMED, BindingStatus.UNRESOLVED, None, ()),
    (EvidenceStatus.PARTIAL, BindingStatus.INTERFACE_ONLY, "content-defined", ()),
    (EvidenceStatus.PARTIAL, BindingStatus.UNRESOLVED, None, ()),
    (EvidenceStatus.UNKNOWN, BindingStatus.UNRESOLVED, None, ()),
]


@pytest.mark.parametrize(("evidence", "binding", "policy", "refs"), LEGAL)
def test_legal_evidence_binding_combinations(evidence, binding, policy, refs):
    contract = SemanticContract("mechanic", evidence, binding, policy, refs)
    assert contract.source_refs == tuple(sorted(refs))


@pytest.mark.parametrize(
    ("evidence", "binding"),
    [
        (EvidenceStatus.PARTIAL, BindingStatus.BOUND),
        (EvidenceStatus.UNKNOWN, BindingStatus.BOUND),
        (EvidenceStatus.UNKNOWN, BindingStatus.INTERFACE_ONLY),
    ],
)
def test_illegal_evidence_binding_combinations(evidence, binding):
    with pytest.raises(ValueError):
        SemanticContract("mechanic", evidence, binding, None, ("source",))


def test_bound_confirmed_requires_source_and_unresolved_forbids_policy():
    with pytest.raises(ValueError):
        SemanticContract("mechanic", EvidenceStatus.CONFIRMED, BindingStatus.BOUND, None, ())
    with pytest.raises(ValueError):
        SemanticContract("mechanic", EvidenceStatus.UNKNOWN, BindingStatus.UNRESOLVED, "guess", ())


def test_sources_must_be_nonempty_and_unique():
    with pytest.raises(ValueError):
        SemanticContract("mechanic", EvidenceStatus.CONFIRMED, BindingStatus.BOUND, None, ("",))
    with pytest.raises(ValueError):
        SemanticContract("mechanic", EvidenceStatus.CONFIRMED, BindingStatus.BOUND, None, ("source", "source"))


def test_require_bound_returns_bound_and_controls_every_nonbound_case():
    bound = SemanticContract("bound", EvidenceStatus.CONFIRMED, BindingStatus.BOUND, None, ("source",))
    assert bound.require_bound() is bound
    for evidence, binding, policy, refs in LEGAL[1:]:
        contract = SemanticContract("mechanic", evidence, binding, policy, refs)
        with pytest.raises(UnresolvedMechanicError):
            contract.require_bound()
