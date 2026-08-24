from __future__ import annotations

from .break_logic import recover_break_if_needed
from .events import Event
from .state import BattleState
from .turn_context import TurnContext
from .unit import Unit


class Timeline:
    @staticmethod
    def next_turn(state: BattleState) -> TurnContext:
        while state.extra_turn_stack:
            # MVP policy: extra turns resolve LIFO; golden replay testing may revise this.
            actor_id = state.extra_turn_stack.pop()
            actor = state.get_unit(actor_id)
            if actor.is_alive:
                state.logs.append(f"extra_turn:{actor.id}")
                turn_context = TurnContext(actor_id=actor.id, is_extra_turn=True)
                state.emit_event(
                    Event(
                        "turn_started",
                        {"actor_id": actor.id, "is_extra_turn": True},
                    ),
                    turn_context,
                )
                return turn_context

        actor = Timeline._select_next_normal_actor(state)
        turn_context = TurnContext(actor_id=actor.id, is_extra_turn=False)
        state.emit_event(
            Event("turn_started", {"actor_id": actor.id, "is_extra_turn": False}),
            turn_context,
        )
        return turn_context

    @staticmethod
    def end_turn(state: BattleState, turn_context: TurnContext) -> None:
        if not turn_context.should_end_turn:
            return

        if not turn_context.is_extra_turn:
            actor = state.get_unit(turn_context.actor_id)
            actor.current_av += actor.base_av
            actor.tick_target_normal_turn_statuses()
            recover_break_if_needed(actor)
            state.logs.append(f"normal_turn_end:{actor.id}")
        else:
            state.logs.append(f"extra_turn_end:{turn_context.actor_id}")

        for unit in state.units:
            unit.expire_current_turn_statuses()

        state.emit_event(
            Event(
                "turn_ended",
                {
                    "actor_id": turn_context.actor_id,
                    "is_extra_turn": turn_context.is_extra_turn,
                },
            ),
            turn_context,
        )

    @staticmethod
    def _select_next_normal_actor(state: BattleState) -> Unit:
        alive_units = state.alive_units()
        if not alive_units:
            raise ValueError("Cannot select a turn with no alive units.")

        actor = min(alive_units, key=lambda unit: (unit.current_av, unit.id))
        elapsed = actor.current_av
        state.global_av += elapsed

        for unit in alive_units:
            unit.current_av -= elapsed
            if abs(unit.current_av) < 1e-12:
                unit.current_av = 0

        actor.current_av = 0
        state.logs.append(f"normal_turn:{actor.id}:elapsed:{elapsed}")
        return actor
