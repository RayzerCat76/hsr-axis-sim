from dataclasses import FrozenInstanceError

import pytest

from hsr_axis_sim.runtime_contracts import (
    ActionContext,
    ActionFamily,
    AttackContext,
    HitContext,
    PriorityClass,
    SamePriorityPolicy,
    TargetPolicyKind,
    TargetRole,
    TurnKind,
    canonical_json_dumps,
)


def action(**overrides):
    values = dict(
        action_id="action-1", actor_id="actor-1", owner_id=None, source_id="skill-1",
        family=ActionFamily.NORMAL_TURN, turn_kind=TurnKind.NORMAL,
        priority_class=PriorityClass.NORMAL_TURN,
        same_priority_policy=SamePriorityPolicy.UNRESOLVED,
        trigger_sequence=None, parent_event_id=None, rng_scope="scope-1",
        metadata={"z": [2, 1], "a": True},
    )
    values.update(overrides)
    return ActionContext(**values)


def attack(**overrides):
    values = dict(
        attack_id="attack-1", action_id="action-1", attacker_id="actor-1",
        attack_tags=("skill", "damage"), target_policy=TargetPolicyKind.SINGLE,
        selected_primary_target_id="enemy-1", is_follow_up=False, is_counter=False,
        metadata={},
    )
    values.update(overrides)
    return AttackContext(**values)


def hit(**overrides):
    values = dict(
        hit_id="hit-1", attack_id="attack-1", hit_index=0, target_id="enemy-1",
        target_role=TargetRole.PRIMARY, damage_request_id="damage-1",
        toughness_request_id=None, application_request_ids=("effect-b", "effect-a"),
        metadata={},
    )
    values.update(overrides)
    return HitContext(**values)


def test_valid_contexts_are_frozen_sorted_and_serializable():
    action_context = action()
    attack_context = attack()
    hit_context = hit()
    assert attack_context.attack_tags == ("damage", "skill")
    assert hit_context.application_request_ids == ("effect-a", "effect-b")
    assert '"action_id":"action-1"' in canonical_json_dumps(action_context)
    with pytest.raises(FrozenInstanceError):
        action_context.action_id = "changed"
    with pytest.raises(TypeError):
        action_context.metadata["new"] = 1


@pytest.mark.parametrize("factory, field", [(action, "action_id"), (attack, "attack_id"), (hit, "hit_id")])
def test_empty_ids_rejected(factory, field):
    with pytest.raises(ValueError):
        factory(**{field: " "})


def test_negative_hit_index_rejected():
    with pytest.raises(ValueError):
        hit(hit_index=-1)


def test_counter_requires_follow_up():
    with pytest.raises(ValueError):
        attack(is_counter=True, is_follow_up=False)


@pytest.mark.parametrize("policy", [TargetPolicyKind.SINGLE, TargetPolicyKind.BLAST, TargetPolicyKind.BOUNCE, TargetPolicyKind.LOCKED, TargetPolicyKind.ADJACENT])
def test_primary_target_policies_reject_missing_target(policy):
    with pytest.raises(ValueError):
        attack(target_policy=policy, selected_primary_target_id=None)


def test_aoe_does_not_require_primary_target():
    assert attack(target_policy=TargetPolicyKind.AOE, selected_primary_target_id=None)


def test_duplicate_tags_and_request_ids_rejected():
    with pytest.raises(ValueError):
        attack(attack_tags=("damage", "damage"))
    with pytest.raises(ValueError):
        hit(application_request_ids=("effect", "effect"))


def test_opaque_metadata_rejected_without_repr_fallback():
    with pytest.raises(TypeError):
        action(metadata={"bad": object()})
