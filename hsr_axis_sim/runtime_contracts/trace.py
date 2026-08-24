"""Immutable trace records with lossless raw/display numeric separation."""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .contexts import ActionContext, AttackContext, HitContext, _require_id, _unique_sorted
from .enums import QuantizationPolicy
from .events import RuntimeEvent


@dataclass(frozen=True)
class TraceNumericValue:
    raw_value: str
    displayed_value: str | None
    quantization_policy: QuantizationPolicy

    def __post_init__(self) -> None:
        _require_id(self.raw_value, "raw_value")
        if self.displayed_value is not None:
            _require_id(self.displayed_value, "displayed_value")


@dataclass(frozen=True)
class RuntimeTraceRecord:
    sequence: int
    event: RuntimeEvent
    action_context: ActionContext | None
    attack_context: AttackContext | None
    hit_context: HitContext | None
    numeric_values: Mapping[str, TraceNumericValue] = field(default_factory=dict)
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")
        for key, value in self.numeric_values.items():
            _require_id(key, "numeric_values key")
            if not isinstance(value, TraceNumericValue):
                raise TypeError("numeric_values values must be TraceNumericValue")
        object.__setattr__(
            self,
            "numeric_values",
            MappingProxyType(dict(sorted(self.numeric_values.items()))),
        )
        object.__setattr__(self, "notes", _unique_sorted(self.notes, "notes"))

        action = self.action_context
        attack = self.attack_context
        hit = self.hit_context
        if action and attack and action.action_id != attack.action_id:
            raise ValueError("action_context and attack_context action IDs disagree")
        if attack and hit and attack.attack_id != hit.attack_id:
            raise ValueError("attack_context and hit_context attack IDs disagree")
        pairs = (
            (self.event.action_id, action.action_id if action else None, "action_id"),
            (self.event.attack_id, attack.attack_id if attack else None, "attack_id"),
            (self.event.hit_id, hit.hit_id if hit else None, "hit_id"),
        )
        for event_id, context_id, name in pairs:
            if event_id is not None and context_id is not None and event_id != context_id:
                raise ValueError(f"event and context {name} values disagree")
