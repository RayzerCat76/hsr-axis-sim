"""Schema-v1-compatible resource change observation payloads."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from .enums import RuntimeResourceKind, RuntimeResourceScope


Number = int | float


@dataclass(frozen=True)
class RuntimeResourceChangeObservation:
    resource_kind: RuntimeResourceKind
    scope: RuntimeResourceScope
    before: Number
    after: Number
    requested_delta: Number
    applied_delta: Number
    cap: Number
    unit_id: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.resource_kind, RuntimeResourceKind):
            raise TypeError("resource_kind must be RuntimeResourceKind")
        if not isinstance(self.scope, RuntimeResourceScope):
            raise TypeError("scope must be RuntimeResourceScope")

        for name in ("before", "after", "requested_delta", "applied_delta", "cap"):
            value = getattr(self, name)
            _require_finite_number(value, name)

        if self.applied_delta != self.after - self.before:
            raise ValueError("applied_delta must equal after - before")

        if self.resource_kind is RuntimeResourceKind.ENERGY:
            if self.scope is not RuntimeResourceScope.UNIT:
                raise ValueError("ENERGY observations require UNIT scope")
            if not isinstance(self.unit_id, str) or not self.unit_id.strip():
                raise ValueError("ENERGY observations require a non-empty unit_id")
            return

        if self.resource_kind is RuntimeResourceKind.SKILL_POINTS:
            if self.scope is not RuntimeResourceScope.TEAM:
                raise ValueError("SKILL_POINTS observations require TEAM scope")
            if self.unit_id is not None:
                raise ValueError("SKILL_POINTS observations require unit_id=None")
            for name in ("before", "after", "requested_delta", "applied_delta", "cap"):
                if type(getattr(self, name)) is not int:
                    raise TypeError(f"SKILL_POINTS {name} must be an integer")
            return

        raise ValueError(f"unsupported resource_kind: {self.resource_kind!r}")

    def to_payload(self) -> dict[str, Any]:
        """Return the exact schema-v1 event-payload representation."""

        return {
            "resource_kind": self.resource_kind.value,
            "scope": self.scope.value,
            "before": self.before,
            "after": self.after,
            "requested_delta": self.requested_delta,
            "applied_delta": self.applied_delta,
            "cap": self.cap,
            "unit_id": self.unit_id,
        }


def _require_finite_number(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite int or float")
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")
