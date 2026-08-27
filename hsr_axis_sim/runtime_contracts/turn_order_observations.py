"""Schema-v1-compatible deterministic turn-order observation payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RuntimeExtraTurnQueuedObservation:
    """One completed production append to the deterministic extra-turn stack."""

    target_id: str
    stack_depth_before: int
    stack_depth_after: int

    def __post_init__(self) -> None:
        if not isinstance(self.target_id, str) or not self.target_id.strip():
            raise ValueError("target_id must be a non-empty string")
        for name in ("stack_depth_before", "stack_depth_after"):
            value = getattr(self, name)
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer")
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.stack_depth_after != self.stack_depth_before + 1:
            raise ValueError("stack_depth_after must equal stack_depth_before + 1")

    def to_payload(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "stack_depth_before": self.stack_depth_before,
            "stack_depth_after": self.stack_depth_after,
        }
