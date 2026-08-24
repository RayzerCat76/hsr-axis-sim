from pathlib import Path

import pytest

from hsr_axis_sim.sim import (
    Action,
    ConsumeEnergy,
    DealDamage,
    ReplayValidator,
    TurnContext,
    execute_interrupt_action,
    legal_ultimate_choices,
)
from hsr_axis_sim.sim.data_loader import action_from_skill, build_battle_state_from_files


ROOT = Path(__file__).resolve().parents[1]
CHARACTERS_DIR = ROOT / "data" / "sample_characters"
TEAM_PATH = ROOT / "data" / "sample_teams" / "bronya_seele_team.json"
ULTIMATE_REPLAY_PATH = ROOT / "data" / "golden_replays" / "ultimate_interrupt_mvp.json"
GOLDEN_REPLAYS_DIR = ROOT / "data" / "golden_replays"


def loaded_state():
    return build_battle_state_from_files(TEAM_PATH, CHARACTERS_DIR)


def test_legal_ultimate_choices_returns_only_affordable_ultimates():
    state, skill_lookup = loaded_state()
    state.get_unit("seele_like").energy = 80

    choices = legal_ultimate_choices(state, skill_lookup)

    assert [choice.skill_id for choice in choices] == ["ultimate", "ultimate"]
    assert all(choice.skill_type == "ultimate" for choice in choices)
    assert [choice.target_ids for choice in choices] == [["enemy_1"], ["enemy_2"]]


def test_insufficient_energy_excludes_ultimate():
    state, skill_lookup = loaded_state()
    state.get_unit("seele_like").energy = 79

    assert legal_ultimate_choices(state, skill_lookup) == []


def test_dead_ultimate_users_are_excluded():
    state, skill_lookup = loaded_state()
    state.get_unit("seele_like").energy = 80
    state.get_unit("seele_like").is_alive = False

    assert legal_ultimate_choices(state, skill_lookup) == []


def test_dead_targets_are_excluded_from_ultimate_choices():
    state, skill_lookup = loaded_state()
    state.get_unit("seele_like").energy = 80
    state.get_unit("enemy_1").is_alive = False

    choices = legal_ultimate_choices(state, skill_lookup)

    assert [choice.target_ids for choice in choices] == [["enemy_2"]]


def test_ultimate_choice_order_is_unit_skill_target_order():
    state, skill_lookup = loaded_state()
    state.get_unit("seele_like").energy = 80

    choices = legal_ultimate_choices(state, skill_lookup)

    assert [(choice.actor_id, choice.skill_id, choice.target_ids) for choice in choices] == [
        ("seele_like", "ultimate", ["enemy_1"]),
        ("seele_like", "ultimate", ["enemy_2"]),
    ]


def test_ultimate_choice_generation_does_not_mutate_state():
    state, skill_lookup = loaded_state()
    state.get_unit("seele_like").energy = 80
    before = {
        "global_av": state.global_av,
        "skill_points": state.skill_points,
        "energies": {unit.id: unit.energy for unit in state.units},
        "hps": {unit.id: unit.hp for unit in state.units},
        "current_avs": {unit.id: unit.current_av for unit in state.units},
    }

    choices = legal_ultimate_choices(state, skill_lookup)

    assert len(choices) == 2
    assert state.global_av == before["global_av"]
    assert state.skill_points == before["skill_points"]
    assert {unit.id: unit.energy for unit in state.units} == before["energies"]
    assert {unit.id: unit.hp for unit in state.units} == before["hps"]
    assert {unit.id: unit.current_av for unit in state.units} == before["current_avs"]


def test_execute_interrupt_action_does_not_advance_global_av_or_reset_current_av():
    state, skill_lookup = loaded_state()
    actor = state.get_unit("seele_like")
    target = state.get_unit("enemy_1")
    actor.energy = 80
    actor.current_av = 42
    state.global_av = 12
    action = action_from_skill(
        skill_lookup["seele_like"]["ultimate"],
        actor_id="seele_like",
        target_ids=["enemy_1"],
        state=state,
        validate_targets=True,
    )

    turn_context = execute_interrupt_action(state, action)

    assert isinstance(turn_context, TurnContext)
    assert turn_context.is_interrupt is True
    assert turn_context.is_extra_turn is False
    assert state.global_av == 12
    assert actor.current_av == 42
    assert actor.energy == 0
    assert target.hp == 100


def test_interrupt_action_with_ends_turn_true_fails_clearly():
    state, _ = loaded_state()
    action = Action(
        id="bad_interrupt",
        name="Bad Interrupt",
        actor_id="seele_like",
        ends_turn=True,
    )

    with pytest.raises(ValueError, match="ends_turn=True"):
        execute_interrupt_action(state, action)


def test_interrupt_action_can_use_forced_rng():
    state, _ = loaded_state()
    actor = state.get_unit("seele_like")
    target = state.get_unit("enemy_1")
    actor.energy = 80
    actor.atk = 100
    actor.crit_dmg = 0.5
    action = Action(
        id="crit_interrupt",
        name="Crit Interrupt",
        actor_id="seele_like",
        target_ids=["enemy_1"],
        effects=[
            ConsumeEnergy(amount=80, target_ref="actor"),
            DealDamage(multiplier=2, target_ref="action_targets"),
        ],
        ends_turn=False,
    )

    execute_interrupt_action(state, action, forced_rng={"crit": True})

    assert actor.energy == 0
    assert target.hp == 200


def test_replay_validator_supports_interrupt_step():
    validator = ReplayValidator()
    replay = validator.load_replay(ULTIMATE_REPLAY_PATH)

    result = validator.validate(replay)

    assert result.passed is True
    assert result.checked_steps == 3


def test_all_golden_replays_still_pass():
    validator = ReplayValidator()

    for replay_path in sorted(GOLDEN_REPLAYS_DIR.glob("*.json")):
        result = validator.validate(validator.load_replay(replay_path))
        assert result.passed is True, (replay_path.name, result.mismatches)
