from pathlib import Path

import pytest

from hsr_axis_sim.sim import (
    SkillSpec,
    is_skill_affordable,
    legal_action_choices_for_actor,
    legal_actions_for_actor,
    skill_affordability,
)
from hsr_axis_sim.sim.data_loader import build_battle_state_from_files


ROOT = Path(__file__).resolve().parents[1]
CHARACTERS_DIR = ROOT / "data" / "sample_characters"
TEAM_PATH = ROOT / "data" / "sample_teams" / "bronya_seele_team.json"


def loaded_state():
    return build_battle_state_from_files(TEAM_PATH, CHARACTERS_DIR)


def make_skill(
    skill_id: str,
    skill_type: str = "special",
    target_type: str = "self",
    sp_delta: int | None = 0,
    energy_delta: float | None = 0,
) -> SkillSpec:
    return SkillSpec(
        id=skill_id,
        name=skill_id,
        skill_type=skill_type,
        target_type=target_type,
        sp_delta=sp_delta,
        energy_delta=energy_delta,
        ends_turn=True,
        effects=[],
    )


def test_generates_basic_and_skill_choices_for_seele_like_when_sp_available():
    state, skill_lookup = loaded_state()

    choices = legal_action_choices_for_actor(
        state,
        "seele_like",
        skill_lookup["seele_like"],
    )

    assert [choice.skill_id for choice in choices] == ["basic", "basic", "skill", "skill"]
    assert [choice.target_ids for choice in choices] == [
        ["enemy_1"],
        ["enemy_2"],
        ["enemy_1"],
        ["enemy_2"],
    ]


def test_single_enemy_skills_generate_one_choice_per_alive_enemy():
    state, skill_lookup = loaded_state()

    choices = legal_action_choices_for_actor(
        state,
        "seele_like",
        [skill_lookup["seele_like"]["basic"]],
    )

    assert [choice.target_ids for choice in choices] == [["enemy_1"], ["enemy_2"]]


def test_dead_targets_are_excluded():
    state, skill_lookup = loaded_state()
    state.get_unit("enemy_1").is_alive = False

    choices = legal_action_choices_for_actor(
        state,
        "seele_like",
        [skill_lookup["seele_like"]["basic"]],
    )

    assert [choice.target_ids for choice in choices] == [["enemy_2"]]


def test_sp_affordability_excludes_and_includes_skill():
    state, skill_lookup = loaded_state()
    skill = skill_lookup["seele_like"]["skill"]

    state.skill_points = 0
    result = skill_affordability(state, "seele_like", skill)
    choices = legal_action_choices_for_actor(state, "seele_like", [skill])

    assert result.affordable is False
    assert is_skill_affordable(state, "seele_like", skill) is False
    assert any("skill point" in reason for reason in result.reasons)
    assert choices == []

    state.skill_points = 1
    assert is_skill_affordable(state, "seele_like", skill) is True
    assert [choice.target_ids for choice in legal_action_choices_for_actor(state, "seele_like", [skill])] == [
        ["enemy_1"],
        ["enemy_2"],
    ]


def test_energy_affordability_excludes_and_includes_skill():
    state, _ = loaded_state()
    skill = make_skill("ultimate_like", skill_type="ultimate", energy_delta=-120)

    state.get_unit("seele_like").energy = 119
    result = skill_affordability(state, "seele_like", skill)

    assert result.affordable is False
    assert any("energy" in reason for reason in result.reasons)
    assert legal_action_choices_for_actor(state, "seele_like", [skill]) == []

    state.get_unit("seele_like").energy = 120
    choices = legal_action_choices_for_actor(state, "seele_like", [skill])

    assert len(choices) == 1
    assert choices[0].skill_id == "ultimate_like"
    assert choices[0].target_ids == ["seele_like"]


def test_self_target_skills_normalize_to_actor_id():
    state, skill_lookup = loaded_state()
    wait_skill = skill_lookup["enemy_1"]["wait"]

    choices = legal_action_choices_for_actor(state, "enemy_1", [wait_skill])

    assert len(choices) == 1
    assert choices[0].target_ids == ["enemy_1"]
    assert choices[0].action.target_ids == ["enemy_1"]


def test_all_enemies_skill_generates_one_no_selected_target_choice():
    state, _ = loaded_state()
    skill = make_skill("aoe_like", target_type="all_enemies")

    choices = legal_action_choices_for_actor(state, "seele_like", [skill])

    assert len(choices) == 1
    assert choices[0].target_ids == []
    assert legal_actions_for_actor(state, "seele_like", [skill])[0].target_ids == []


def test_dead_actor_generates_no_choices():
    state, skill_lookup = loaded_state()
    state.get_unit("seele_like").is_alive = False

    assert legal_action_choices_for_actor(
        state,
        "seele_like",
        skill_lookup["seele_like"],
    ) == []


def test_unknown_actor_fails_clearly():
    state, skill_lookup = loaded_state()

    with pytest.raises(ValueError, match="Unknown actor id"):
        legal_action_choices_for_actor(state, "missing_actor", skill_lookup["seele_like"])


def test_generation_does_not_mutate_state():
    state, skill_lookup = loaded_state()
    actor = state.get_unit("seele_like")
    target = state.get_unit("enemy_1")
    before = {
        "skill_points": state.skill_points,
        "actor_energy": actor.energy,
        "target_hp": target.hp,
        "current_avs": {unit.id: unit.current_av for unit in state.units},
    }

    choices = legal_action_choices_for_actor(
        state,
        "seele_like",
        skill_lookup["seele_like"],
    )

    assert len(choices) == 4
    assert state.skill_points == before["skill_points"]
    assert actor.energy == before["actor_energy"]
    assert target.hp == before["target_hp"]
    assert {unit.id: unit.current_av for unit in state.units} == before["current_avs"]
