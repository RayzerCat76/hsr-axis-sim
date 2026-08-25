import inspect
import json

import pytest

from hsr_axis_sim.runtime_contracts import enums
from hsr_axis_sim.runtime_contracts.contexts import ActionContext


EXPECTED = {
    "EvidenceStatus": ["CONFIRMED", "PARTIAL", "UNKNOWN"],
    "BindingStatus": ["BOUND", "INTERFACE_ONLY", "UNRESOLVED"],
    "TurnKind": ["NORMAL", "EXTRA", "INTERRUPT", "NONE"],
    "ActionFamily": ["NORMAL_TURN", "EXTRA_TURN", "EXTRA_ACTION", "FOLLOW_UP", "COUNTER", "ULTIMATE_INTERRUPT", "DOES_NOT_END_TURN", "SUMMON_ACTION", "JOINT_ACTION", "CONTENT_DEFINED"],
    "PriorityClass": ["FOLLOW_UP", "ULTIMATE_OR_EXTRA_TURN", "DOES_NOT_END_TURN", "NORMAL_TURN", "CONTENT_DEFINED"],
    "SamePriorityPolicy": ["FIFO", "LIFO", "EXPLICIT_ORDER", "UNRESOLVED"],
    "TargetPolicyKind": ["SINGLE", "BLAST", "AOE", "BOUNCE", "RANDOM", "LOCKED", "ADJACENT", "CONTENT_DEFINED"],
    "TargetInvalidationPolicy": ["ABORT", "RETARGET_RANDOM", "RETARGET_LOCKED", "RETARGET_MARKED", "WAIT_FOR_NEW_TARGET", "CONTINUE_CHAIN", "CONTENT_DEFINED"],
    "MultiHitContinuationPolicy": ["STOP", "RETARGET", "CONTINUE_ON_CORPSE", "CONTINUE_CHAIN", "CONTENT_DEFINED"],
    "BounceRepeatPolicy": ["WITH_REPLACEMENT", "WITHOUT_REPLACEMENT", "WEIGHTED", "CONTENT_DEFINED", "UNRESOLVED"],
    "TriggerScope": ["PER_ACTION", "PER_ATTACK", "PER_HIT", "PER_TARGET", "PER_DISTINCT_TARGET", "PER_EFFECT_ACTIVATION", "PER_TURN", "PER_WAVE", "PER_BATTLE"],
    "StackPolicy": ["NON_STACKING", "ADD_STACK", "EXTEND_DURATION", "REFRESH_DURATION", "REPLACE_VALUE", "INDEPENDENT_INSTANCES", "CONTENT_DEFINED"],
    "WavePolicy": ["KEEP", "REMOVE", "RESET_COUNTER", "KEEP_AV", "REBASE_AV", "REAPPLY", "CONTENT_DEFINED"],
    "RemovalChannel": ["CLEANSE", "DISPEL", "NATURAL_EXPIRATION", "TRANSFORM", "WEAKNESS_BREAK", "KILLING_BLOW", "OWNER_DOWNED", "COUNTDOWN", "RESOURCE_DEPLETION", "LINKED_ENTITY_DEFEATED", "PHASE_CHANGE", "SCRIPTED"],
    "LifecycleState": ["ACTIVE", "DISABLED", "CROWD_CONTROLLED", "OFF_FIELD", "UNTARGETABLE", "REMOVED", "KNOCKED_DOWN", "DEAD", "PENDING_REVIVE", "REVIVING", "REVIVED", "DESPAWNED"],
    "QuantizationPolicy": ["NONE", "FLOOR", "CEIL", "ROUND_HALF_UP", "ROUND_HALF_EVEN", "TRUNCATE", "DISPLAY_ONLY", "CONTENT_DEFINED"],
    "DotEvaluationPolicy": ["SNAPSHOT", "DYNAMIC", "HYBRID", "CONTENT_DEFINED", "UNRESOLVED"],
    "MaxHpCouplingPolicy": ["PRESERVE_CURRENT", "PRESERVE_RATIO", "ADD_DELTA", "CLAMP_ONLY", "LINK_PERCENTAGE", "CONTENT_DEFINED", "UNRESOLVED"],
    "DamageFamily": ["DIRECT", "DOT", "BREAK", "SUPER_BREAK", "ADDITIONAL", "TRUE", "ELATION", "ENCOUNTER_SCRIPTED", "CONTENT_DEFINED"],
    "DefenseMechanism": ["NORMAL_SHIELD_INSTANCE", "STACKABLE_SHIELD_FAMILY", "COLLECTIVE_SHIELD_POOL", "BARRIER", "DMG_MITIGATION", "DAMAGE_DISTRIBUTION", "HP_FLOOR", "LETHAL_INTERCEPT", "SCRIPTED_INVULNERABILITY", "CONTENT_DEFINED"],
    "TargetRole": ["PRIMARY", "SECONDARY", "ADJACENT", "BOUNCE", "AOE", "RANDOM", "LOCKED", "CONTENT_DEFINED"],
    "RuntimeResourceKind": ["ENERGY", "SKILL_POINTS"],
    "RuntimeResourceScope": ["UNIT", "TEAM"],
    "RuntimeEventType": ["BATTLE_START", "WAVE_START", "TURN_ENTRY", "TURN_START", "ACTION_QUEUED", "ACTION_START", "ACTION_VALUE_ADVANCED", "ACTION_VALUE_DELAYED", "ATTACK_DECLARED", "ATTACK_CONTACT", "TARGET_ATTACKED", "HIT_RESOLVED", "BEFORE_DAMAGE", "DAMAGE_RESOLVED", "SHIELD_CHANGED", "SHIELD_DAMAGED", "HP_CHANGED", "HP_DAMAGED", "HP_LOST", "TOUGHNESS_REDUCED", "WEAKNESS_BROKEN", "ENERGY_CHANGED", "SKILL_POINTS_CHANGED", "EFFECT_APPLICATION_ATTEMPT", "EFFECT_APPLIED", "EFFECT_RESISTED", "EFFECT_IMMUNE", "EFFECT_REMOVED", "EFFECT_TRANSFORMED", "FOLLOW_UP_QUEUED", "COUNTER_QUEUED", "EXTRA_TURN_QUEUED", "ACTION_END", "TURN_END", "BEFORE_LETHAL", "LETHAL_INTERCEPTED", "DOWNED", "KNOCKED_DOWN", "DEATH", "REVIVE", "WAVE_END", "BATTLE_END", "CONTENT_DEFINED"],
}


@pytest.mark.parametrize(("name", "values"), EXPECTED.items())
def test_exact_stable_enum_values(name, values):
    enum_type = getattr(enums, name)
    assert [member.value for member in enum_type] == values
    assert all(isinstance(member.value, str) for member in enum_type)
    assert json.loads(json.dumps(list(enum_type))) == values


def test_no_numeric_priority_or_custom_ordering_api():
    assert all(not isinstance(member.value, (int, float)) for member in enums.PriorityClass)
    assert "__lt__" not in enums.PriorityClass.__dict__
    assert "rank" not in enums.PriorityClass.__dict__


def test_same_priority_policy_is_required_on_action_context():
    parameter = inspect.signature(ActionContext).parameters["same_priority_policy"]
    assert parameter.default is inspect.Parameter.empty
