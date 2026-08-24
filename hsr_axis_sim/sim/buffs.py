from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class Buff:
    id: str
    name: str
    target_id: str
    source_id: str | None
    kind: Literal["buff", "debuff"]
    duration_type: str
    remaining_turns: int | None
    stacks: int = 1
    max_stacks: int = 1
    data: dict[str, Any] = field(default_factory=dict)

