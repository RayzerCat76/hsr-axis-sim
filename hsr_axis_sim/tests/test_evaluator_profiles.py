import pytest

from hsr_axis_sim.search import (
    Evaluator,
    ScoreConfig,
    ScoreProfile,
    format_score_breakdown,
)
from hsr_axis_sim.sim import BattleState, Unit


def make_state(
    enemy_hp=50,
    enemy_alive=True,
    ally_hp=1000,
    ally_alive=True,
    global_av=0,
    skill_points=3,
):
    ally = Unit(
        "ally",
        "Ally",
        "ally",
        100,
        hp=ally_hp,
        max_hp=1000,
        is_alive=ally_alive,
    )
    enemy = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        hp=enemy_hp,
        max_hp=100,
        is_alive=enemy_alive,
    )
    return BattleState(
        units=[ally, enemy],
        global_av=global_av,
        skill_points=skill_points,
    )


def test_default_evaluator_remains_backward_compatible_float():
    state = make_state(enemy_hp=50, global_av=2, skill_points=3)

    score = Evaluator().evaluate(state, depth=1)

    assert score == pytest.approx(580, abs=1e-6)


def test_required_profiles_can_be_instantiated():
    for profile_id in [
        "generic_kill",
        "zero_cycle",
        "damage_race",
        "survival_safe",
        "sp_conservative",
    ]:
        assert Evaluator(profile=profile_id).profile.id == profile_id


def test_evaluate_breakdown_total_equals_component_sum():
    state = make_state(enemy_hp=40)
    breakdown = Evaluator(profile="damage_race").evaluate_breakdown(state, depth=2)

    assert breakdown.total == pytest.approx(sum(breakdown.components.values()), abs=1e-6)


def test_format_score_breakdown_is_readable():
    state = make_state(enemy_hp=40)
    breakdown = Evaluator().evaluate_breakdown(state, depth=1)

    formatted = format_score_breakdown(breakdown)

    assert "generic_kill total=" in formatted
    assert "enemy_hp_missing=" in formatted


def test_zero_cycle_penalizes_global_av_more_than_generic_kill():
    fast = make_state(enemy_hp=50, global_av=0)
    slow = make_state(enemy_hp=50, global_av=10)

    generic_delta = Evaluator("generic_kill").evaluate(fast, 1) - Evaluator(
        "generic_kill"
    ).evaluate(slow, 1)
    zero_cycle_delta = Evaluator("zero_cycle").evaluate(fast, 1) - Evaluator(
        "zero_cycle"
    ).evaluate(slow, 1)

    assert zero_cycle_delta > generic_delta


def test_damage_race_rewards_hp_missing_more_than_survival_safe():
    low_damage = make_state(enemy_hp=90)
    high_damage = make_state(enemy_hp=10)

    damage_race_delta = Evaluator("damage_race").evaluate(high_damage, 1) - Evaluator(
        "damage_race"
    ).evaluate(low_damage, 1)
    survival_delta = Evaluator("survival_safe").evaluate(high_damage, 1) - Evaluator(
        "survival_safe"
    ).evaluate(low_damage, 1)

    assert damage_race_delta > survival_delta


def test_survival_safe_penalizes_defeated_allies():
    alive_state = make_state(ally_hp=1000, ally_alive=True)
    defeated_state = make_state(ally_hp=0, ally_alive=False)

    alive_score = Evaluator("survival_safe").evaluate(alive_state, 1)
    defeated_score = Evaluator("survival_safe").evaluate(defeated_state, 1)

    assert alive_score > defeated_score


def test_sp_conservative_rewards_skill_points_more_than_damage_race():
    low_sp = make_state(skill_points=0)
    high_sp = make_state(skill_points=5)

    sp_delta = Evaluator("sp_conservative").evaluate(high_sp, 1) - Evaluator(
        "sp_conservative"
    ).evaluate(low_sp, 1)
    damage_race_delta = Evaluator("damage_race").evaluate(high_sp, 1) - Evaluator(
        "damage_race"
    ).evaluate(low_sp, 1)

    assert sp_delta > damage_race_delta


def test_custom_profile_works():
    profile = ScoreProfile(
        id="custom_test",
        defeated_enemy_bonus=1,
        all_enemies_defeated_bonus=2,
        enemy_hp_missing_weight=3,
        global_av_penalty=4,
        depth_penalty=5,
        skill_point_bonus=6,
        alive_ally_bonus=7,
        ally_hp_remaining_weight=8,
        defeated_ally_penalty=9,
    )
    state = make_state(enemy_hp=90, ally_hp=100)

    breakdown = Evaluator(profile=profile).evaluate_breakdown(state, depth=1)

    assert breakdown.profile_id == "custom_test"
    assert breakdown.components["enemy_hp_missing"] == pytest.approx(30, abs=1e-6)
    assert breakdown.components["ally_hp_remaining"] == pytest.approx(800, abs=1e-6)


def test_score_config_compatibility_still_works():
    evaluator = Evaluator(config=ScoreConfig(enemy_hp_missing_weight=10))
    state = make_state(enemy_hp=90)

    breakdown = evaluator.evaluate_breakdown(state, depth=0)

    assert breakdown.profile_id == "custom_config"
    assert breakdown.components["enemy_hp_missing"] == pytest.approx(100, abs=1e-6)
