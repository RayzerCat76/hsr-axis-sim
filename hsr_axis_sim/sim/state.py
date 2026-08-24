from __future__ import annotations

from dataclasses import dataclass, field

from .events import Event, Trigger, dispatch_event
from .turn_context import TurnContext
from .unit import Unit


@dataclass
class BattleState:
    units: list[Unit]
    global_av: float = 0
    skill_points: int = 0
    max_skill_points: int = 5
    extra_turn_stack: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    triggers: list[Trigger] = field(default_factory=list)
    pending_events: list[Event] = field(default_factory=list)
    trigger_fire_counts: dict[str, int] = field(default_factory=dict)
    event_dispatch_count: int = 0
    event_dispatch_limit: int = 100
    enemy_ai_plans: dict[str, object] = field(default_factory=dict)
    enemy_ai_cursors: dict[str, int] = field(default_factory=dict)

    def get_unit(self, unit_id: str) -> Unit:
        for unit in self.units:
            if unit.id == unit_id:
                return unit
        raise KeyError(f"Unknown unit id: {unit_id}")

    def alive_units(self) -> list[Unit]:
        return [unit for unit in self.units if unit.is_alive]

    def emit_event(self, event: Event, turn_context: TurnContext | None = None) -> None:
        dispatch_event(self, event, turn_context)
