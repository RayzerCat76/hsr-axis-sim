"""Generic, dispatch-free runtime event envelope."""

from dataclasses import dataclass, field
from typing import Any, Mapping

from .contexts import _optional_id, _require_id
from .enums import RuntimeEventType
from .serialization import freeze_mapping


@dataclass(frozen=True)
class RuntimeEvent:
    event_id: str
    event_type: RuntimeEventType
    sequence: int
    action_id: str | None
    attack_id: str | None
    hit_id: str | None
    actor_id: str | None
    source_id: str | None
    target_id: str | None
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_id(self.event_id, "event_id")
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")
        for name in (
            "action_id",
            "attack_id",
            "hit_id",
            "actor_id",
            "source_id",
            "target_id",
        ):
            _optional_id(getattr(self, name), name)
        object.__setattr__(self, "payload", freeze_mapping(self.payload, path="payload"))
