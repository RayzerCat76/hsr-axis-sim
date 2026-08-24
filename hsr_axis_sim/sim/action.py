from __future__ import annotations

from dataclasses import dataclass, field

from .events import Event
from .effects import Effect
from .state import BattleState
from .timeline import Timeline
from .turn_context import TurnContext


@dataclass
class Action:
    id: str
    name: str
    actor_id: str
    target_ids: list[str] = field(default_factory=list)
    effects: list[Effect] = field(default_factory=list)
    ends_turn: bool = True

    def execute(
        self,
        state: BattleState,
        turn_context: TurnContext | None = None,
    ) -> TurnContext:
        if turn_context is None:
            turn_context = TurnContext(actor_id=self.actor_id)
        elif self.actor_id != turn_context.actor_id:
            raise ValueError(
                "Action actor_id must match the active turn context actor_id: "
                f"{self.actor_id!r} != {turn_context.actor_id!r}."
            )

        state.trigger_fire_counts = {}
        state.event_dispatch_count = 0
        turn_context.should_end_turn = self.ends_turn
        state.emit_event(
            Event(
                "action_started",
                {
                    "actor_id": self.actor_id,
                    "action_id": self.id,
                },
            ),
            turn_context,
        )
        for effect in self.effects:
            effect.apply(state, self, turn_context)

        turn_context.actions_taken.append(self.id)
        state.emit_event(
            Event(
                "action_finished",
                {
                    "actor_id": self.actor_id,
                    "action_id": self.id,
                },
            ),
            turn_context,
        )

        if turn_context.should_end_turn:
            Timeline.end_turn(state, turn_context)

        return turn_context
