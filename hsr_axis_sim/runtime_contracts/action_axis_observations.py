"""Schema-v1-compatible action-axis observation payloads."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any


Number = int | float


@dataclass(frozen=True)
class RuntimeActionAdvanceObservation:
    """One completed production AdvanceAction mutation for one target Unit."""

    target_id: str
    before_av: Number
    after_av: Number
    base_av: Number
    requested_percent: Number
    requested_delta_av: Number
    applied_delta_av: Number
    clamped_to_zero: bool

    def __post_init__(self) -> None:
        if not isinstance(self.target_id, str) or not self.target_id.strip():
            raise ValueError("target_id must be a non-empty string")

        for name in (
            "before_av",
            "after_av",
            "base_av",
            "requested_percent",
            "requested_delta_av",
            "applied_delta_av",
        ):
            _require_finite_number(getattr(self, name), name)

        if self.base_av <= 0:
            raise ValueError("base_av must be positive")
        if type(self.clamped_to_zero) is not bool:
            raise TypeError("clamped_to_zero must be a bool")

        expected_requested_delta = -(self.base_av * self.requested_percent)
        if self.requested_delta_av != expected_requested_delta:
            raise ValueError(
                "requested_delta_av must equal -(base_av * requested_percent)"
            )

        if self.applied_delta_av != self.after_av - self.before_av:
            raise ValueError("applied_delta_av must equal after_av - before_av")

        unclamped_after = self.before_av + self.requested_delta_av
        expected_after = max(0, unclamped_after)
        if self.after_av != expected_after:
            raise ValueError(
                "after_av must equal max(0, before_av + requested_delta_av)"
            )

        expected_clamped = unclamped_after < 0
        if self.clamped_to_zero is not expected_clamped:
            raise ValueError(
                "clamped_to_zero must identify whether the requested result was below zero"
            )

    def to_payload(self) -> dict[str, Any]:
        """Return the exact schema-v1 event-payload representation."""

        return {
            "target_id": self.target_id,
            "before_av": self.before_av,
            "after_av": self.after_av,
            "base_av": self.base_av,
            "requested_percent": self.requested_percent,
            "requested_delta_av": self.requested_delta_av,
            "applied_delta_av": self.applied_delta_av,
            "clamped_to_zero": self.clamped_to_zero,
        }


@dataclass(frozen=True)
class RuntimeActionDelayObservation:
    """One completed production DelayAction mutation for one target Unit."""

    target_id: str
    before_av: Number
    after_av: Number
    base_av: Number
    requested_percent: Number
    requested_delta_av: Number
    applied_delta_av: Number

    def __post_init__(self) -> None:
        if not isinstance(self.target_id, str) or not self.target_id.strip():
            raise ValueError("target_id must be a non-empty string")

        for name in (
            "before_av",
            "after_av",
            "base_av",
            "requested_percent",
            "requested_delta_av",
            "applied_delta_av",
        ):
            _require_finite_number(getattr(self, name), name)

        if self.base_av <= 0:
            raise ValueError("base_av must be positive")

        expected_requested_delta = self.base_av * self.requested_percent
        if self.requested_delta_av != expected_requested_delta:
            raise ValueError(
                "requested_delta_av must equal base_av * requested_percent"
            )

        expected_after = self.before_av + self.requested_delta_av
        if self.after_av != expected_after:
            raise ValueError("after_av must equal before_av + requested_delta_av")

        if self.applied_delta_av != self.after_av - self.before_av:
            raise ValueError("applied_delta_av must equal after_av - before_av")

    def to_payload(self) -> dict[str, Any]:
        """Return the exact schema-v1 event-payload representation."""

        return {
            "target_id": self.target_id,
            "before_av": self.before_av,
            "after_av": self.after_av,
            "base_av": self.base_av,
            "requested_percent": self.requested_percent,
            "requested_delta_av": self.requested_delta_av,
            "applied_delta_av": self.applied_delta_av,
        }


@dataclass(frozen=True)
class RuntimeSpeedChangeObservation:
    """One completed production ChangeSpeed mutation for one target Unit."""

    target_id: str
    before_speed: Number
    after_speed: Number
    before_av: Number
    after_av: Number

    def __post_init__(self) -> None:
        if not isinstance(self.target_id, str) or not self.target_id.strip():
            raise ValueError("target_id must be a non-empty string")

        for name in (
            "before_speed",
            "after_speed",
            "before_av",
            "after_av",
        ):
            _require_finite_number(getattr(self, name), name)

        if self.before_speed <= 0:
            raise ValueError("before_speed must be positive")
        if self.after_speed <= 0:
            raise ValueError("after_speed must be positive")

        expected_after_av = self.before_av * self.before_speed / self.after_speed
        if self.after_av != expected_after_av:
            raise ValueError(
                "after_av must equal before_av * before_speed / after_speed"
            )

    def to_payload(self) -> dict[str, Any]:
        """Return the exact schema-v1 event-payload representation."""

        return {
            "target_id": self.target_id,
            "before_speed": self.before_speed,
            "after_speed": self.after_speed,
            "before_av": self.before_av,
            "after_av": self.after_av,
        }


def _require_finite_number(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite int or float")
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")
