from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TurnContext:
    actor_id: str
    is_extra_turn: bool = False
    is_interrupt: bool = False
    should_end_turn: bool = True
    actions_taken: list[str] = field(default_factory=list)
    forced_rng: dict = field(default_factory=dict)
