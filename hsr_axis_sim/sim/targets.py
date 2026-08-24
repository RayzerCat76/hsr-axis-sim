from __future__ import annotations

from typing import Any


def resolve_target_ids(
    state: Any,
    action: Any,
    turn_context: Any,
    target_ref: str | None = None,
    target_ids: list[str] | None = None,
) -> list[str]:
    if target_ref is not None:
        return _resolve_target_ref(state, action, target_ref)
    if target_ids is not None:
        return list(target_ids)

    action_target_ids = list(getattr(action, "target_ids", []))
    if action_target_ids:
        return action_target_ids

    return [getattr(action, "actor_id")]


def _resolve_target_ref(state: Any, action: Any, target_ref: str) -> list[str]:
    actor_id = getattr(action, "actor_id")
    actor = state.get_unit(actor_id)

    if target_ref in {"actor", "self"}:
        return [actor_id]

    if target_ref in {"action_targets", "selected_targets"}:
        target_ids = list(getattr(action, "target_ids", []))
        if not target_ids:
            raise ValueError(f"target_ref {target_ref!r} requires selected target ids.")
        return target_ids

    if target_ref == "all_allies":
        return [unit.id for unit in state.units if unit.team == actor.team]
    if target_ref == "alive_allies":
        return [unit.id for unit in state.units if unit.team == actor.team and unit.is_alive]
    if target_ref == "all_enemies":
        return [unit.id for unit in state.units if unit.team != actor.team]
    if target_ref == "alive_enemies":
        return [unit.id for unit in state.units if unit.team != actor.team and unit.is_alive]

    event_data = dict(getattr(action, "event_data", {}) or {})
    if target_ref == "event_source":
        return _single_event_target(event_data, "source_id", target_ref)
    if target_ref == "event_target":
        return _single_event_target(event_data, "target_id", target_ref)
    if target_ref == "event_killer":
        return _single_event_target(event_data, "killer_id", target_ref)
    if target_ref == "event_victim":
        return _single_event_target(event_data, "target_id", target_ref)

    raise ValueError(f"Unknown target_ref: {target_ref!r}.")


def _single_event_target(event_data: dict[str, Any], field_name: str, target_ref: str) -> list[str]:
    unit_id = event_data.get(field_name)
    if unit_id is None:
        raise ValueError(f"target_ref {target_ref!r} requires event field {field_name!r}.")
    return [unit_id]

