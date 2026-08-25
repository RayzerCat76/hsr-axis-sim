"""Manual, one-way adaptation of legacy MVP event observations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Iterable, Mapping

from hsr_axis_sim.runtime_contracts import (
    BindingStatus,
    EvidenceStatus,
    RuntimeEvent,
    RuntimeEventType,
    RuntimeResourceChangeObservation,
    RuntimeResourceKind,
    RuntimeResourceScope,
    SemanticContract,
)
from hsr_axis_sim.sim.events import Event

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - Python < 3.11 compatibility
    class StrEnum(str, Enum):
        """Minimal standard-library-compatible StrEnum fallback."""


class UnknownLegacyEventPolicy(StrEnum):
    PRESERVE_AS_CONTENT_DEFINED = "PRESERVE_AS_CONTENT_DEFINED"
    REJECT = "REJECT"


class AmbiguousLegacyEventPolicy(StrEnum):
    PRESERVE_AS_CONTENT_DEFINED = "PRESERVE_AS_CONTENT_DEFINED"
    REJECT = "REJECT"


class LegacyEventAdapterError(RuntimeError):
    """Base class for controlled legacy adapter failures."""


class UnmappedLegacyEventError(LegacyEventAdapterError):
    """Raised when an explicitly rejected unknown event is observed."""


class AmbiguousLegacyEventError(LegacyEventAdapterError):
    """Raised when an explicitly rejected ambiguous event is observed."""


class LegacyEventSchemaError(LegacyEventAdapterError):
    """Raised when a legacy event cannot form a valid immutable envelope."""


def _require_non_empty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LegacyEventSchemaError(f"{name} must be a non-empty string")
    return value


@dataclass(frozen=True)
class LegacyEventAdapterConfig:
    stream_id: str
    unknown_event_policy: UnknownLegacyEventPolicy
    ambiguous_event_policy: AmbiguousLegacyEventPolicy

    def __post_init__(self) -> None:
        _require_non_empty(self.stream_id, "stream_id")
        if not isinstance(self.unknown_event_policy, UnknownLegacyEventPolicy):
            raise LegacyEventSchemaError("unknown_event_policy has an invalid type")
        if not isinstance(self.ambiguous_event_policy, AmbiguousLegacyEventPolicy):
            raise LegacyEventSchemaError("ambiguous_event_policy has an invalid type")


@dataclass(frozen=True)
class LegacyEventMapping:
    legacy_event_type: str
    runtime_event_type: RuntimeEventType
    semantic_contract: SemanticContract
    normalized_field_map: Mapping[str, str]
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.legacy_event_type, "legacy_event_type")
        if not isinstance(self.runtime_event_type, RuntimeEventType):
            raise LegacyEventSchemaError("runtime_event_type has an invalid type")
        if not isinstance(self.semantic_contract, SemanticContract):
            raise LegacyEventSchemaError("semantic_contract has an invalid type")
        normalized: dict[str, str] = {}
        for runtime_field, legacy_field in sorted(self.normalized_field_map.items()):
            _require_non_empty(runtime_field, "normalized runtime field")
            _require_non_empty(legacy_field, "normalized legacy field")
            normalized[runtime_field] = legacy_field
        object.__setattr__(self, "normalized_field_map", MappingProxyType(normalized))


def _bound_mapping(
    legacy_type: str,
    runtime_type: RuntimeEventType,
    source_ref: str,
    normalized_field_map: Mapping[str, str],
    notes: str | None = None,
) -> LegacyEventMapping:
    return LegacyEventMapping(
        legacy_event_type=legacy_type,
        runtime_event_type=runtime_type,
        semantic_contract=SemanticContract(
            mechanic_id=f"LEGACY_EVENT.{legacy_type.upper()}",
            evidence_status=EvidenceStatus.CONFIRMED,
            binding_status=BindingStatus.BOUND,
            selected_policy=runtime_type.value,
            source_refs=(source_ref,),
            notes=notes,
        ),
        normalized_field_map=normalized_field_map,
        notes=notes,
    )


_MAPPINGS = (
    _bound_mapping(
        "action_finished", RuntimeEventType.ACTION_END,
        "hsr_axis_sim/sim/action.py", {"action_id": "action_id", "actor_id": "actor_id"},
    ),
    _bound_mapping(
        "action_started", RuntimeEventType.ACTION_START,
        "hsr_axis_sim/sim/action.py", {"action_id": "action_id", "actor_id": "actor_id"},
    ),
    _bound_mapping(
        "damage_dealt", RuntimeEventType.DAMAGE_RESOLVED,
        "hsr_axis_sim/sim/effects.py", {"source_id": "source_id", "target_id": "target_id"},
        "Preserve amount and formula parts as raw legacy data; infer no hit or attack.",
    ),
    _bound_mapping(
        "energy_changed", RuntimeEventType.ENERGY_CHANGED,
        "hsr_axis_sim/sim/effects.py",
        {"action_id": "action_id", "actor_id": "actor_id", "target_id": "unit_id"},
        "Validate and expose ARCH-019 resource_change while preserving raw legacy data.",
    ),
    _bound_mapping(
        "skill_points_changed", RuntimeEventType.SKILL_POINTS_CHANGED,
        "hsr_axis_sim/sim/effects.py",
        {"action_id": "action_id", "actor_id": "actor_id"},
        "Validate and expose ARCH-019 resource_change while preserving raw legacy data.",
    ),
    _bound_mapping(
        "turn_ended", RuntimeEventType.TURN_END,
        "hsr_axis_sim/sim/timeline.py", {"actor_id": "actor_id"},
    ),
    _bound_mapping(
        "turn_started", RuntimeEventType.TURN_START,
        "hsr_axis_sim/sim/timeline.py", {"actor_id": "actor_id"},
        "Do not infer turn kind or priority from is_extra_turn.",
    ),
    LegacyEventMapping(
        legacy_event_type="unit_defeated",
        runtime_event_type=RuntimeEventType.CONTENT_DEFINED,
        semantic_contract=SemanticContract(
            mechanic_id="LEGACY_EVENT.UNIT_DEFEATED_LIFECYCLE",
            evidence_status=EvidenceStatus.UNKNOWN,
            binding_status=BindingStatus.UNRESOLVED,
            selected_policy=None,
            source_refs=("hsr_axis_sim/sim/effects.py",),
            notes="Legacy defeat does not distinguish current runtime lifecycle states.",
        ),
        normalized_field_map={"target_id": "target_id"},
        notes="Preserve killer_id only in legacy_data; do not infer source_id.",
    ),
    _bound_mapping(
        "weakness_break", RuntimeEventType.WEAKNESS_BROKEN,
        "hsr_axis_sim/sim/effects.py", {"source_id": "source_id", "target_id": "target_id"},
    ),
)

LEGACY_EVENT_MAPPINGS: Mapping[str, LegacyEventMapping] = MappingProxyType(
    {mapping.legacy_event_type: mapping for mapping in _MAPPINGS}
)

_RESOURCE_EVENT_KINDS: Mapping[str, RuntimeResourceKind] = MappingProxyType(
    {
        "energy_changed": RuntimeResourceKind.ENERGY,
        "skill_points_changed": RuntimeResourceKind.SKILL_POINTS,
    }
)


def _validate_event(event: object) -> Event:
    if not isinstance(event, Event):
        raise LegacyEventSchemaError("event must be hsr_axis_sim.sim.events.Event")
    _require_non_empty(event.type, "event.type")
    if not isinstance(event.data, Mapping):
        raise LegacyEventSchemaError("event.data must be a mapping")
    return event


def _normalized_ids(mapping: LegacyEventMapping, data: Mapping[str, object]) -> dict[str, str]:
    values: dict[str, str] = {}
    for runtime_field, legacy_field in mapping.normalized_field_map.items():
        if legacy_field not in data:
            raise LegacyEventSchemaError(
                f"{mapping.legacy_event_type} is missing normalized field {legacy_field!r}"
            )
        values[runtime_field] = _require_non_empty(data[legacy_field], legacy_field)
    return values


def _resource_change_payload(
    legacy_event_type: str,
    data: Mapping[str, object],
) -> dict[str, object] | None:
    expected_kind = _RESOURCE_EVENT_KINDS.get(legacy_event_type)
    if expected_kind is None:
        return None

    try:
        observation = RuntimeResourceChangeObservation(
            resource_kind=RuntimeResourceKind(data["resource_kind"]),
            scope=RuntimeResourceScope(data["scope"]),
            before=data["before"],
            after=data["after"],
            requested_delta=data["requested_delta"],
            applied_delta=data["applied_delta"],
            cap=data["cap"],
            unit_id=data["unit_id"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise LegacyEventSchemaError(
            f"invalid {legacy_event_type} resource observation: {exc}"
        ) from exc

    if observation.resource_kind is not expected_kind:
        raise LegacyEventSchemaError(
            f"{legacy_event_type} requires resource_kind={expected_kind.value}"
        )
    return observation.to_payload()


def adapt_legacy_event(
    event: Event,
    *,
    sequence: int,
    config: LegacyEventAdapterConfig,
) -> RuntimeEvent:
    """Adapt one legacy observation without reading or mutating simulator state."""
    if not isinstance(config, LegacyEventAdapterConfig):
        raise LegacyEventSchemaError("config must be LegacyEventAdapterConfig")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
        raise LegacyEventSchemaError("sequence must be a non-negative integer")
    legacy_event = _validate_event(event)
    mapping = LEGACY_EVENT_MAPPINGS.get(legacy_event.type)

    if mapping is None:
        if config.unknown_event_policy is UnknownLegacyEventPolicy.REJECT:
            raise UnmappedLegacyEventError(f"unmapped legacy event: {legacy_event.type}")
        runtime_type = RuntimeEventType.CONTENT_DEFINED
        mapping_status = "UNMAPPED_PRESERVED"
        mechanic_id = "LEGACY_EVENT.UNMAPPED_TYPE"
        binding_status = BindingStatus.UNRESOLVED
        semantic_gap_ids = [mechanic_id]
        normalized: dict[str, str] = {}
    else:
        contract = mapping.semantic_contract
        if contract.binding_status is BindingStatus.UNRESOLVED:
            if config.ambiguous_event_policy is AmbiguousLegacyEventPolicy.REJECT:
                raise AmbiguousLegacyEventError(
                    f"ambiguous legacy event: {legacy_event.type}"
                )
            mapping_status = "AMBIGUOUS"
            semantic_gap_ids = [contract.mechanic_id]
        else:
            contract.require_bound()
            mapping_status = "BOUND"
            semantic_gap_ids = []
        runtime_type = mapping.runtime_event_type
        mechanic_id = contract.mechanic_id
        binding_status = contract.binding_status
        normalized = _normalized_ids(mapping, legacy_event.data)

    resource_change = _resource_change_payload(legacy_event.type, legacy_event.data)
    payload = {
        "adapter": {
            "adapter_name": "legacy_mvp_event_adapter",
            "adapter_version": "1.0",
            "binding_status": binding_status.value,
            "legacy_event_type": legacy_event.type,
            "mapping_status": mapping_status,
            "mechanic_id": mechanic_id,
            "semantic_gap_ids": semantic_gap_ids,
        },
        "legacy_data": legacy_event.data,
    }
    if resource_change is not None:
        payload["resource_change"] = resource_change

    try:
        return RuntimeEvent(
            event_id=f"legacy:{config.stream_id}:{sequence}",
            event_type=runtime_type,
            sequence=sequence,
            action_id=normalized.get("action_id"),
            attack_id=None,
            hit_id=None,
            actor_id=normalized.get("actor_id"),
            source_id=normalized.get("source_id"),
            target_id=normalized.get("target_id"),
            payload=payload,
        )
    except (TypeError, ValueError) as exc:
        raise LegacyEventSchemaError(f"invalid legacy event payload: {exc}") from exc


def adapt_legacy_event_stream(
    events: Iterable[Event],
    *,
    start_sequence: int,
    config: LegacyEventAdapterConfig,
) -> tuple[RuntimeEvent, ...]:
    """Adapt one iterable exactly once, preserving observation order."""
    if not isinstance(config, LegacyEventAdapterConfig):
        raise LegacyEventSchemaError("config must be LegacyEventAdapterConfig")
    if not isinstance(start_sequence, int) or isinstance(start_sequence, bool) or start_sequence < 0:
        raise LegacyEventSchemaError("start_sequence must be a non-negative integer")
    return tuple(
        adapt_legacy_event(event, sequence=sequence, config=config)
        for sequence, event in enumerate(events, start=start_sequence)
    )
