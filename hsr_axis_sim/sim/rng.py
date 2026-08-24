from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ForcedRng:
    values: dict[str, Any] = field(default_factory=dict)

    def crit(self) -> bool:
        return bool(self.values.get("crit", False))


@dataclass
class RngContext:
    forced_rng: ForcedRng = field(default_factory=ForcedRng)

    @classmethod
    def from_dict(cls, values: dict[str, Any] | None) -> "RngContext":
        return cls(forced_rng=ForcedRng(dict(values or {})))

    def crit(self) -> bool:
        return self.forced_rng.crit()

