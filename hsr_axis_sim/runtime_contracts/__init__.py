"""Sidecar contracts for the future universal HSR runtime."""

from .action_axis_observations import (
    RuntimeActionAdvanceObservation,
    RuntimeActionDelayObservation,
)
from .contexts import ActionContext, AttackContext, HitContext
from .enums import (
    ActionFamily,
    BindingStatus,
    BounceRepeatPolicy,
    DamageFamily,
    DefenseMechanism,
    DotEvaluationPolicy,
    EvidenceStatus,
    LifecycleState,
    MaxHpCouplingPolicy,
    MultiHitContinuationPolicy,
    PriorityClass,
    QuantizationPolicy,
    RemovalChannel,
    RuntimeEventType,
    RuntimeResourceKind,
    RuntimeResourceScope,
    SamePriorityPolicy,
    StackPolicy,
    TargetInvalidationPolicy,
    TargetPolicyKind,
    TargetRole,
    TriggerScope,
    TurnKind,
    WavePolicy,
)
from .events import RuntimeEvent
from .gates import SemanticContract, UnresolvedMechanicError
from .resource_observations import RuntimeResourceChangeObservation
from .serialization import canonical_json_bytes, canonical_json_dumps, to_canonical_data
from .trace import RuntimeTraceRecord, TraceNumericValue

__all__ = [name for name in globals() if not name.startswith("_")]
