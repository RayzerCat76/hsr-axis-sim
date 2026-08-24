from __future__ import annotations

from typing import Any


class TargetValidationError(ValueError):
    pass


NO_SELECTION_TARGET_TYPES = {"none", "all_enemies", "all_allies", "all_units"}


def legal_target_groups(state: Any, actor_id: str, target_type: str) -> list[list[str]]:
    actor = _get_unit_or_raise(state, actor_id)

    if target_type == "self":
        return [[actor_id]]
    if target_type in NO_SELECTION_TARGET_TYPES:
        return [[]]
    if target_type == "single_enemy":
        return [[unit.id] for unit in state.units if unit.team != actor.team and unit.is_alive]
    if target_type == "single_ally":
        return [[unit.id] for unit in state.units if unit.team == actor.team and unit.is_alive]
    if target_type == "single_other_ally":
        return [
            [unit.id]
            for unit in state.units
            if unit.team == actor.team and unit.is_alive and unit.id != actor_id
        ]
    if target_type == "single_any":
        return [[unit.id] for unit in state.units if unit.is_alive]

    raise TargetValidationError(f"Unknown target_type: {target_type!r}.")


def normalize_and_validate_target_ids(
    state: Any,
    actor_id: str,
    target_type: str,
    target_ids: list[str] | None,
) -> list[str]:
    selected_ids = list(target_ids or [])
    actor = _get_unit_or_raise(state, actor_id)

    if target_type == "self":
        if not selected_ids:
            return [actor_id]
        if selected_ids == [actor_id]:
            return [actor_id]
        raise TargetValidationError(
            f"Skill target_type 'self' only allows actor {actor_id!r}."
        )

    if target_type in NO_SELECTION_TARGET_TYPES:
        if selected_ids:
            raise TargetValidationError(
                f"Skill target_type {target_type!r} does not accept selected targets."
            )
        return []

    if target_type in {"single_enemy", "single_ally", "single_other_ally", "single_any"}:
        if not selected_ids:
            raise TargetValidationError(
                f"Skill target_type {target_type!r} requires exactly one selected target."
            )
        if len(selected_ids) != 1:
            raise TargetValidationError(
                f"Skill target_type {target_type!r} requires exactly one selected target."
            )

        target = _get_unit_or_raise(state, selected_ids[0])
        if not target.is_alive:
            raise TargetValidationError(f"Target {target.id!r} is not alive.")
        if target_type == "single_enemy" and target.team == actor.team:
            raise TargetValidationError(
                f"Target {target.id!r} is not an enemy of actor {actor_id!r}."
            )
        if target_type == "single_ally" and target.team != actor.team:
            raise TargetValidationError(
                f"Target {target.id!r} is not an ally of actor {actor_id!r}."
            )
        if target_type == "single_other_ally":
            if target.team != actor.team:
                raise TargetValidationError(
                    f"Target {target.id!r} is not an ally of actor {actor_id!r}."
                )
            if target.id == actor_id:
                raise TargetValidationError(
                    f"Skill target_type 'single_other_ally' cannot target the actor."
                )
        return [target.id]

    raise TargetValidationError(f"Unknown target_type: {target_type!r}.")


def _get_unit_or_raise(state: Any, unit_id: str) -> Any:
    try:
        return state.get_unit(unit_id)
    except KeyError as exc:
        raise TargetValidationError(f"Unknown target id: {unit_id!r}.") from exc

