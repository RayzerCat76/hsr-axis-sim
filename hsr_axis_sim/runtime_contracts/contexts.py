"""Immutable Action / Attack / Hit contract contexts."""

from dataclasses import dataclass, field
from typing import Any, Mapping

from .enums import (
    ActionFamily,
    PriorityClass,
    SamePriorityPolicy,
    TargetPolicyKind,
    TargetRole,
    TurnKind,
)
from .serialization import freeze_mapping


def _require_id(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _optional_id(value: str | None, name: str) -> None:
    if value is not None:
        _require_id(value, name)


def _unique_sorted(values: tuple[str, ...], name: str) -> tuple[str, ...]:
    for value in values:
        _require_id(value, name)
    if len(set(values)) != len(values):
        raise ValueError(f"{name} values must be unique")
    return tuple(sorted(values))


@dataclass(frozen=True)
class ActionContext:
    action_id: str
    actor_id: str
    owner_id: str | None
    source_id: str | None
    family: ActionFamily
    turn_kind: TurnKind
    priority_class: PriorityClass
    same_priority_policy: SamePriorityPolicy
    trigger_sequence: int | None
    parent_event_id: str | None
    rng_scope: str | None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_id(self.action_id, "action_id")
        _require_id(self.actor_id, "actor_id")
        _optional_id(self.owner_id, "owner_id")
        _optional_id(self.source_id, "source_id")
        _optional_id(self.parent_event_id, "parent_event_id")
        _optional_id(self.rng_scope, "rng_scope")
        if self.trigger_sequence is not None and self.trigger_sequence < 0:
            raise ValueError("trigger_sequence must be non-negative")
        object.__setattr__(self, "metadata", freeze_mapping(self.metadata, path="metadata"))


_PRIMARY_TARGET_POLICIES = frozenset(
    {
        TargetPolicyKind.SINGLE,
        TargetPolicyKind.BLAST,
        TargetPolicyKind.BOUNCE,
        TargetPolicyKind.LOCKED,
        TargetPolicyKind.ADJACENT,
    }
)


@dataclass(frozen=True)
class AttackContext:
    attack_id: str
    action_id: str
    attacker_id: str
    attack_tags: tuple[str, ...]
    target_policy: TargetPolicyKind
    selected_primary_target_id: str | None
    is_follow_up: bool
    is_counter: bool
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_id(self.attack_id, "attack_id")
        _require_id(self.action_id, "action_id")
        _require_id(self.attacker_id, "attacker_id")
        _optional_id(self.selected_primary_target_id, "selected_primary_target_id")
        if self.is_counter and not self.is_follow_up:
            raise ValueError("is_counter=True requires is_follow_up=True")
        if (
            self.target_policy in _PRIMARY_TARGET_POLICIES
            and self.selected_primary_target_id is None
        ):
            raise ValueError(f"{self.target_policy.value} requires a primary target")
        object.__setattr__(self, "attack_tags", _unique_sorted(self.attack_tags, "attack_tags"))
        object.__setattr__(self, "metadata", freeze_mapping(self.metadata, path="metadata"))


@dataclass(frozen=True)
class HitContext:
    hit_id: str
    attack_id: str
    hit_index: int
    target_id: str
    target_role: TargetRole
    damage_request_id: str | None
    toughness_request_id: str | None
    application_request_ids: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_id(self.hit_id, "hit_id")
        _require_id(self.attack_id, "attack_id")
        _require_id(self.target_id, "target_id")
        _optional_id(self.damage_request_id, "damage_request_id")
        _optional_id(self.toughness_request_id, "toughness_request_id")
        if self.hit_index < 0:
            raise ValueError("hit_index must be non-negative")
        object.__setattr__(
            self,
            "application_request_ids",
            _unique_sorted(self.application_request_ids, "application_request_ids"),
        )
        object.__setattr__(self, "metadata", freeze_mapping(self.metadata, path="metadata"))
