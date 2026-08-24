from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .action import Action
from .action_generator import ActionChoice, is_skill_affordable
from .data_loader import action_from_skill
from .data_schema import SkillSpec
from .state import BattleState
from .targeting import legal_target_groups
from .turn_context import TurnContext


@dataclass
class DecisionWindow:
    window_type: str
    active_actor_id: str | None = None
    source: str | None = None


def legal_ultimate_choices(
    state: BattleState,
    skill_lookup: dict[str, dict[str, SkillSpec]],
    window: DecisionWindow | None = None,
) -> list[ActionChoice]:
    choices: list[ActionChoice] = []

    for unit in state.units:
        if not unit.is_alive:
            continue
        for skill in skill_lookup.get(unit.id, {}).values():
            if skill.skill_type != "ultimate":
                continue
            if not is_skill_affordable(state, unit.id, skill):
                continue
            for target_group in legal_target_groups(state, unit.id, skill.target_type):
                action = action_from_skill(
                    skill,
                    actor_id=unit.id,
                    target_ids=target_group,
                    state=state,
                    validate_targets=True,
                )
                choices.append(
                    ActionChoice(
                        actor_id=unit.id,
                        skill_id=skill.id,
                        skill_type=skill.skill_type,
                        target_ids=list(action.target_ids),
                        action=action,
                    )
                )

    return choices


def execute_interrupt_action(
    state: BattleState,
    action: Action,
    forced_rng: dict[str, Any] | None = None,
) -> TurnContext:
    if action.ends_turn:
        raise ValueError(
            f"Interrupt action {action.id!r} cannot have ends_turn=True."
        )

    turn_context = TurnContext(
        actor_id=action.actor_id,
        is_interrupt=True,
        should_end_turn=False,
        forced_rng=dict(forced_rng or {}),
    )
    return action.execute(state, turn_context)
