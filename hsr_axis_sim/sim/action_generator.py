from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .action import Action
from .data_loader import action_from_skill
from .data_schema import SkillSpec
from .state import BattleState
from .targeting import legal_target_groups


@dataclass
class ActionChoice:
    actor_id: str
    skill_id: str
    skill_type: str
    target_ids: list[str]
    action: Action


@dataclass
class AffordabilityResult:
    affordable: bool
    reasons: list[str]


def skill_affordability(
    state: BattleState,
    actor_id: str,
    skill: SkillSpec,
) -> AffordabilityResult:
    actor = _get_actor_or_raise(state, actor_id)
    reasons: list[str] = []

    if not actor.is_alive:
        reasons.append(f"Actor {actor_id!r} is not alive.")

    if skill.sp_delta is not None and skill.sp_delta < 0:
        required_sp = -skill.sp_delta
        if state.skill_points < required_sp:
            reasons.append(
                f"Skill {skill.id!r} requires {required_sp} skill point(s), "
                f"but state has {state.skill_points}."
            )

    if skill.energy_delta is not None and skill.energy_delta < 0:
        required_energy = -skill.energy_delta
        if actor.energy < required_energy:
            reasons.append(
                f"Skill {skill.id!r} requires {required_energy} energy, "
                f"but actor {actor_id!r} has {actor.energy}."
            )

    return AffordabilityResult(affordable=not reasons, reasons=reasons)


def is_skill_affordable(state: BattleState, actor_id: str, skill: SkillSpec) -> bool:
    return skill_affordability(state, actor_id, skill).affordable


def legal_action_choices_for_actor(
    state: BattleState,
    actor_id: str,
    skills: Iterable[SkillSpec] | Mapping[str, SkillSpec],
) -> list[ActionChoice]:
    actor = _get_actor_or_raise(state, actor_id)
    if not actor.is_alive:
        return []

    choices: list[ActionChoice] = []
    for skill in _iter_skills(skills):
        if not is_skill_affordable(state, actor_id, skill):
            continue
        for target_group in legal_target_groups(state, actor_id, skill.target_type):
            action = action_from_skill(
                skill,
                actor_id=actor_id,
                target_ids=target_group,
                state=state,
                validate_targets=True,
            )
            choices.append(
                ActionChoice(
                    actor_id=actor_id,
                    skill_id=skill.id,
                    skill_type=skill.skill_type,
                    target_ids=list(action.target_ids),
                    action=action,
                )
            )

    return choices


def legal_actions_for_actor(
    state: BattleState,
    actor_id: str,
    skills: Iterable[SkillSpec] | Mapping[str, SkillSpec],
) -> list[Action]:
    return [
        choice.action
        for choice in legal_action_choices_for_actor(state, actor_id, skills)
    ]


def _iter_skills(
    skills: Iterable[SkillSpec] | Mapping[str, SkillSpec],
) -> list[SkillSpec]:
    if isinstance(skills, Mapping):
        return list(skills.values())
    return list(skills)


def _get_actor_or_raise(state: BattleState, actor_id: str):
    try:
        return state.get_unit(actor_id)
    except KeyError as exc:
        raise ValueError(f"Unknown actor id: {actor_id!r}.") from exc
