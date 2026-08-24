from __future__ import annotations

from dataclasses import dataclass, field

from hsr_axis_sim.sim.action_generator import ActionChoice


@dataclass
class SearchConstraints:
    allowed_actor_ids: set[str] | None = None
    disabled_actor_ids: set[str] = field(default_factory=set)
    allowed_skill_ids: set[str] | None = None
    disabled_skill_ids: set[str] = field(default_factory=set)
    allowed_skill_ids_by_actor: dict[str, set[str]] = field(default_factory=dict)
    disabled_skill_ids_by_actor: dict[str, set[str]] = field(default_factory=dict)
    allowed_target_ids: set[str] | None = None
    disabled_target_ids: set[str] = field(default_factory=set)
    max_choices_per_node: int | None = None


def filter_action_choices(
    choices: list[ActionChoice],
    constraints: SearchConstraints | None,
) -> list[ActionChoice]:
    if constraints is None:
        return list(choices)

    filtered = [
        choice
        for choice in choices
        if _actor_allowed(choice, constraints)
        and _skill_allowed(choice, constraints)
        and _targets_allowed(choice, constraints)
    ]
    if constraints.max_choices_per_node is not None:
        return sorted(filtered, key=_choice_key)[: constraints.max_choices_per_node]
    return filtered


def _actor_allowed(choice: ActionChoice, constraints: SearchConstraints) -> bool:
    if constraints.allowed_actor_ids is not None and choice.actor_id not in constraints.allowed_actor_ids:
        return False
    return choice.actor_id not in constraints.disabled_actor_ids


def _skill_allowed(choice: ActionChoice, constraints: SearchConstraints) -> bool:
    if constraints.allowed_skill_ids is not None and choice.skill_id not in constraints.allowed_skill_ids:
        return False
    if choice.skill_id in constraints.disabled_skill_ids:
        return False
    actor_allowed = constraints.allowed_skill_ids_by_actor.get(choice.actor_id)
    if actor_allowed is not None and choice.skill_id not in actor_allowed:
        return False
    actor_disabled = constraints.disabled_skill_ids_by_actor.get(choice.actor_id, set())
    return choice.skill_id not in actor_disabled


def _targets_allowed(choice: ActionChoice, constraints: SearchConstraints) -> bool:
    target_ids = set(choice.target_ids)
    if constraints.allowed_target_ids is not None and not target_ids <= constraints.allowed_target_ids:
        return False
    return not target_ids & constraints.disabled_target_ids


def _choice_key(choice: ActionChoice) -> tuple[str, str, str]:
    return (choice.actor_id, choice.skill_id, ",".join(choice.target_ids))
