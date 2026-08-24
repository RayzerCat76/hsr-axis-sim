from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

from .turn_context import TurnContext


@dataclass
class Event:
    type: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class Trigger:
    id: str
    owner_id: str
    event_type: str
    condition: dict[str, Any]
    effects: list[Any] = field(default_factory=list)
    max_triggers_per_action: int = 1
    enabled: bool = True


def dispatch_event(state: Any, event: Event, turn_context: TurnContext | None = None) -> None:
    state.event_dispatch_count += 1
    if state.event_dispatch_count > state.event_dispatch_limit:
        raise ValueError(
            f"Event dispatch limit exceeded: {state.event_dispatch_limit} events."
        )

    state.pending_events.append(event)
    for trigger in sorted(state.triggers, key=lambda item: item.id):
        if not _trigger_matches(trigger, event):
            continue

        fire_count = state.trigger_fire_counts.get(trigger.id, 0)
        if fire_count >= trigger.max_triggers_per_action:
            continue
        state.trigger_fire_counts[trigger.id] = fire_count + 1
        state.logs.append(f"trigger:{trigger.id}")

        synthetic_action = SimpleNamespace(
            id=f"trigger:{trigger.id}",
            name=f"Trigger {trigger.id}",
            actor_id=trigger.owner_id,
            target_ids=[],
            event_data=event.data,
        )
        trigger_context = turn_context or TurnContext(actor_id=trigger.owner_id)
        for effect in trigger.effects:
            effect.apply(state, synthetic_action, trigger_context)


def _trigger_matches(trigger: Trigger, event: Event) -> bool:
    if not trigger.enabled:
        return False
    if trigger.event_type != event.type:
        return False
    return _condition_matches(trigger.condition, trigger.owner_id, event)


def _condition_matches(condition: dict[str, Any], owner_id: str, event: Event) -> bool:
    condition_type = condition.get("type", "always")

    if condition_type == "always":
        return True
    if condition_type == "event_actor_is_owner":
        return event.data.get("actor_id") == owner_id
    if condition_type == "event_source_is_owner":
        return event.data.get("source_id") == owner_id
    if condition_type == "event_target_is_owner":
        return event.data.get("target_id") == owner_id
    if condition_type == "event_killer_is_owner":
        return event.data.get("killer_id") == owner_id
    if condition_type == "field_equals":
        return event.data.get(condition.get("field")) == condition.get("value")

    return False
