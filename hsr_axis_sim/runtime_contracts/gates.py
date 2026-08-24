"""Evidence-aware semantic binding gates."""

from dataclasses import dataclass

from .contexts import _require_id, _unique_sorted
from .enums import BindingStatus, EvidenceStatus


class UnresolvedMechanicError(RuntimeError):
    """Raised when execution is requested for an unbound mechanic."""


@dataclass(frozen=True)
class SemanticContract:
    mechanic_id: str
    evidence_status: EvidenceStatus
    binding_status: BindingStatus
    selected_policy: str | None
    source_refs: tuple[str, ...]
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_id(self.mechanic_id, "mechanic_id")
        refs = _unique_sorted(self.source_refs, "source_refs")
        object.__setattr__(self, "source_refs", refs)
        if self.selected_policy is not None:
            _require_id(self.selected_policy, "selected_policy")
        if self.evidence_status is EvidenceStatus.PARTIAL and self.binding_status not in {
            BindingStatus.INTERFACE_ONLY,
            BindingStatus.UNRESOLVED,
        }:
            raise ValueError("PARTIAL evidence cannot be BOUND")
        if self.evidence_status is EvidenceStatus.UNKNOWN and self.binding_status is not BindingStatus.UNRESOLVED:
            raise ValueError("UNKNOWN evidence must be UNRESOLVED")
        if self.binding_status is BindingStatus.BOUND:
            if self.evidence_status is not EvidenceStatus.CONFIRMED:
                raise ValueError("only CONFIRMED evidence may be BOUND")
            if not refs:
                raise ValueError("CONFIRMED + BOUND requires a source reference")
        if self.binding_status is BindingStatus.UNRESOLVED and self.selected_policy is not None:
            raise ValueError("UNRESOLVED contracts cannot select a policy")

    def require_bound(self) -> "SemanticContract":
        if self.binding_status is not BindingStatus.BOUND:
            raise UnresolvedMechanicError(
                f"mechanic {self.mechanic_id!r} is {self.binding_status.value}, not BOUND"
            )
        return self
