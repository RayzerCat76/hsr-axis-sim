import pytest

from hsr_axis_sim.sim import (
    BattleState,
    TargetValidationError,
    Unit,
    legal_target_groups,
    normalize_and_validate_target_ids,
)


def make_state():
    actor = Unit("actor", "Actor", "ally", 100)
    ally = Unit("ally", "Ally", "ally", 100)
    dead_ally = Unit("dead_ally", "Dead Ally", "ally", 100, is_alive=False)
    enemy = Unit("enemy", "Enemy", "enemy", 100)
    enemy_2 = Unit("enemy_2", "Enemy 2", "enemy", 100)
    dead_enemy = Unit("dead_enemy", "Dead Enemy", "enemy", 100, is_alive=False)
    return BattleState(units=[actor, ally, dead_ally, enemy, enemy_2, dead_enemy])


def test_legal_target_groups_for_required_target_types():
    state = make_state()

    assert legal_target_groups(state, "actor", "self") == [["actor"]]
    assert legal_target_groups(state, "actor", "none") == [[]]
    assert legal_target_groups(state, "actor", "single_enemy") == [["enemy"], ["enemy_2"]]
    assert legal_target_groups(state, "actor", "single_ally") == [["actor"], ["ally"]]
    assert legal_target_groups(state, "actor", "single_other_ally") == [["ally"]]
    assert legal_target_groups(state, "actor", "single_any") == [
        ["actor"],
        ["ally"],
        ["enemy"],
        ["enemy_2"],
    ]
    assert legal_target_groups(state, "actor", "all_enemies") == [[]]
    assert legal_target_groups(state, "actor", "all_allies") == [[]]


def test_validation_accepts_legal_target_selections():
    state = make_state()

    assert normalize_and_validate_target_ids(state, "actor", "self", None) == ["actor"]
    assert normalize_and_validate_target_ids(state, "actor", "self", ["actor"]) == ["actor"]
    assert normalize_and_validate_target_ids(state, "actor", "none", None) == []
    assert normalize_and_validate_target_ids(state, "actor", "single_enemy", ["enemy"]) == [
        "enemy"
    ]
    assert normalize_and_validate_target_ids(state, "actor", "single_ally", ["ally"]) == [
        "ally"
    ]
    assert normalize_and_validate_target_ids(state, "actor", "single_other_ally", ["ally"]) == [
        "ally"
    ]
    assert normalize_and_validate_target_ids(state, "actor", "single_any", ["enemy_2"]) == [
        "enemy_2"
    ]
    assert normalize_and_validate_target_ids(state, "actor", "all_enemies", []) == []
    assert normalize_and_validate_target_ids(state, "actor", "all_allies", None) == []


def test_validation_rejects_unknown_target_id():
    state = make_state()

    with pytest.raises(TargetValidationError, match="Unknown target id"):
        normalize_and_validate_target_ids(state, "actor", "single_enemy", ["missing"])


def test_validation_rejects_dead_single_target():
    state = make_state()

    with pytest.raises(TargetValidationError, match="not alive"):
        normalize_and_validate_target_ids(state, "actor", "single_enemy", ["dead_enemy"])


def test_validation_rejects_ally_for_single_enemy():
    state = make_state()

    with pytest.raises(TargetValidationError, match="not an enemy"):
        normalize_and_validate_target_ids(state, "actor", "single_enemy", ["ally"])


def test_validation_rejects_enemy_for_single_ally():
    state = make_state()

    with pytest.raises(TargetValidationError, match="not an ally"):
        normalize_and_validate_target_ids(state, "actor", "single_ally", ["enemy"])


def test_validation_rejects_actor_for_single_other_ally():
    state = make_state()

    with pytest.raises(TargetValidationError, match="cannot target the actor"):
        normalize_and_validate_target_ids(state, "actor", "single_other_ally", ["actor"])


def test_validation_rejects_too_many_targets_for_single_target_skill():
    state = make_state()

    with pytest.raises(TargetValidationError, match="exactly one"):
        normalize_and_validate_target_ids(state, "actor", "single_enemy", ["enemy", "enemy_2"])


def test_validation_rejects_missing_target_for_single_target_skill():
    state = make_state()

    with pytest.raises(TargetValidationError, match="exactly one"):
        normalize_and_validate_target_ids(state, "actor", "single_enemy", [])


def test_validation_rejects_explicit_targets_for_no_selection_target_types():
    state = make_state()

    for target_type in ["none", "all_enemies", "all_allies", "all_units"]:
        with pytest.raises(TargetValidationError, match="does not accept selected targets"):
            normalize_and_validate_target_ids(state, "actor", target_type, ["enemy"])

