from copy import deepcopy
from pathlib import Path
import subprocess
import sys

import pytest

from hsr_axis_sim.sim import (
    AddBuff,
    AddDebuff,
    AdvanceAction,
    ChangeSpeed,
    ConsumeEnergy,
    ConsumeSkillPoint,
    DealDamage,
    DealToughnessDamage,
    DelayAction,
    DoesNotEndTurn,
    GainEnergy,
    GainSkillPoint,
    GrantExtraTurn,
    ImmediateAction,
    ReplayValidationError,
    ReplayValidator,
    RemoveBuff,
    RemoveDebuff,
)


GOLDEN_REPLAY_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "golden_replays"
    / "bronya_seele_timeline_mvp.json"
)
MULTISTEP_REPLAY_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "golden_replays"
    / "bronya_seele_multistep_mvp.json"
)
BUFF_DURATION_REPLAY_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "golden_replays"
    / "buff_duration_mvp.json"
)
DAMAGE_RNG_REPLAY_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "golden_replays"
    / "damage_rng_mvp.json"
)
TOUGHNESS_BREAK_REPLAY_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "golden_replays"
    / "toughness_break_mvp.json"
)
TRIGGER_REPLAY_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "golden_replays"
    / "trigger_on_kill_extra_turn_mvp.json"
)


def test_replay_validator_passes_sample_replay():
    validator = ReplayValidator()
    replay_data = validator.load_replay(GOLDEN_REPLAY_PATH)

    result = validator.validate(replay_data)

    assert result.passed is True
    assert result.replay_name == "bronya_seele_timeline_mvp"
    assert result.checked_steps == 1
    assert result.mismatches == []


def test_replay_validator_reports_wrong_actor():
    validator = ReplayValidator()
    replay_data = validator.load_replay(GOLDEN_REPLAY_PATH)
    replay_data["steps"][0]["expected_actor"] = "enemy_1"

    result = validator.validate(replay_data)

    assert result.passed is False
    assert result.checked_steps == 1
    assert any("expected actor" in mismatch for mismatch in result.mismatches)


def test_replay_validator_reports_numeric_mismatch():
    validator = ReplayValidator()
    replay_data = validator.load_replay(GOLDEN_REPLAY_PATH)
    replay_data["steps"][0]["expect"]["units"]["enemy_1"]["hp"] = 8500

    result = validator.validate(replay_data)

    assert result.passed is False
    assert result.checked_steps == 1
    assert any("enemy_1.hp" in mismatch for mismatch in result.mismatches)


def test_replay_validator_deserializes_effects():
    validator = ReplayValidator()
    action = validator.action_from_spec(
        {
            "id": "sample_action",
            "name": "Sample Action",
            "actor_id": "ally",
            "target_ids": ["enemy"],
            "effects": [
                {"type": "AddBuff", "id": "boost", "name": "Boost", "target_ids": ["ally"]},
                {"type": "AddDebuff", "id": "slow", "name": "Slow", "target_ids": ["enemy"]},
                {"type": "DealDamage", "amount": 1000, "target_ids": ["enemy"]},
                {
                    "type": "DealToughnessDamage",
                    "amount": 30,
                    "element": "quantum",
                    "target_ids": ["enemy"],
                },
                {"type": "GainSkillPoint", "amount": 1},
                {"type": "GainEnergy", "amount": 20, "target_ids": ["ally"]},
                {"type": "ConsumeEnergy", "amount": 10, "target_ids": ["ally"]},
                {"type": "ConsumeSkillPoint", "amount": 1},
                {"type": "AdvanceAction", "percent": 0.5, "target_ids": ["ally"]},
                {"type": "DelayAction", "percent": 0.25, "target_ids": ["enemy"]},
                {"type": "ChangeSpeed", "new_speed": 120, "target_ids": ["ally"]},
                {"type": "ImmediateAction", "target_ids": ["ally"]},
                {"type": "GrantExtraTurn", "target_ids": ["ally"]},
                {"type": "RemoveBuff", "id": "boost", "target_ids": ["ally"]},
                {"type": "RemoveDebuff", "id": "slow", "target_ids": ["enemy"]},
                {"type": "DoesNotEndTurn"},
            ],
        }
    )

    expected_types = [
        AddBuff,
        AddDebuff,
        DealDamage,
        DealToughnessDamage,
        GainSkillPoint,
        GainEnergy,
        ConsumeEnergy,
        ConsumeSkillPoint,
        AdvanceAction,
        DelayAction,
        ChangeSpeed,
        ImmediateAction,
        GrantExtraTurn,
        RemoveBuff,
        RemoveDebuff,
        DoesNotEndTurn,
    ]
    assert [type(effect) for effect in action.effects] == expected_types
    assert action.effects[0].target_ids == ["ally"]
    assert action.effects[1].target_ids == ["enemy"]
    assert action.effects[2].target_ids == ["enemy"]
    assert action.effects[3].target_ids == ["enemy"]
    assert action.effects[5].target_ids == ["ally"]


def test_replay_validator_rejects_unknown_effect_type():
    validator = ReplayValidator()

    with pytest.raises(ReplayValidationError, match="Unsupported effect type"):
        validator.effect_from_spec({"type": "UnknownEffect"})


def test_replay_validator_reports_unsupported_expected_field():
    validator = ReplayValidator()
    replay_data = validator.load_replay(GOLDEN_REPLAY_PATH)
    replay_data["steps"][0]["expect"]["unsupported"] = 123

    result = validator.validate(replay_data)

    assert result.passed is False
    assert any("unsupported expected field" in mismatch for mismatch in result.mismatches)


def test_replay_validator_reports_unknown_action():
    validator = ReplayValidator()
    replay_data = validator.load_replay(GOLDEN_REPLAY_PATH)
    replay_data["steps"][0]["action_id"] = "missing_action"

    result = validator.validate(replay_data)

    assert result.passed is False
    assert result.checked_steps == 0
    assert any("unknown action" in mismatch for mismatch in result.mismatches)


def test_replay_validator_returns_failed_result_for_unknown_effect_in_replay():
    validator = ReplayValidator()
    replay_data = validator.load_replay(GOLDEN_REPLAY_PATH)
    replay_data = deepcopy(replay_data)
    replay_data["actions"]["seele_basic"]["effects"].append({"type": "UnknownEffect"})

    result = validator.validate(replay_data)

    assert result.passed is False
    assert result.checked_steps == 0
    assert any("Unsupported effect type" in mismatch for mismatch in result.mismatches)


def test_replay_validator_passes_multistep_replay():
    validator = ReplayValidator()
    replay_data = validator.load_replay(MULTISTEP_REPLAY_PATH)

    result = validator.validate(replay_data)

    assert result.passed is True
    assert result.replay_name == "bronya_seele_multistep_mvp"
    assert result.checked_steps == 3
    assert result.mismatches == []


def test_replay_validator_reports_multistep_mismatch_with_step_and_field():
    validator = ReplayValidator()
    replay_data = validator.load_replay(MULTISTEP_REPLAY_PATH)
    replay_data["steps"][1]["expect"]["units"]["seele"]["current_av"] = 10

    result = validator.validate(replay_data)

    assert result.passed is False
    assert any(
        "step 2" in mismatch and "seele.current_av" in mismatch
        for mismatch in result.mismatches
    )


def test_replay_validator_reports_duplicate_unit_ids():
    validator = ReplayValidator()
    replay_data = validator.load_replay(GOLDEN_REPLAY_PATH)
    replay_data["initial_state"]["units"].append(deepcopy(replay_data["initial_state"]["units"][0]))

    result = validator.validate(replay_data)

    assert result.passed is False
    assert result.checked_steps == 0
    assert any("Duplicate unit id" in mismatch for mismatch in result.mismatches)


def test_replay_validator_step_target_override_controls_affected_unit():
    replay_data = {
        "name": "target_override",
        "tolerance": 0.001,
        "initial_state": {
            "global_av": 0,
            "skill_points": 0,
            "max_skill_points": 5,
            "units": [
                {
                    "id": "actor",
                    "name": "Actor",
                    "team": "ally",
                    "base_speed": 100,
                    "speed": 100,
                    "current_av": 0,
                },
                {
                    "id": "default_target",
                    "name": "Default Target",
                    "team": "enemy",
                    "base_speed": 100,
                    "speed": 100,
                    "current_av": 100,
                    "hp": 100,
                    "max_hp": 100,
                },
                {
                    "id": "override_target",
                    "name": "Override Target",
                    "team": "enemy",
                    "base_speed": 100,
                    "speed": 100,
                    "current_av": 100,
                    "hp": 100,
                    "max_hp": 100,
                },
            ],
        },
        "actions": {
            "hit": {
                "id": "hit",
                "name": "Hit",
                "actor_id": "actor",
                "target_ids": ["default_target"],
                "effects": [{"type": "DealDamage", "amount": 10}],
            }
        },
        "steps": [
            {
                "step": 1,
                "expected_actor": "actor",
                "action_id": "hit",
                "target_ids": ["override_target"],
                "expect": {
                    "units": {
                        "default_target": {"hp": 100},
                        "override_target": {"hp": 90},
                    }
                },
            }
        ],
    }

    result = ReplayValidator().validate(replay_data)

    assert result.passed is True
    assert result.checked_steps == 1


def test_replay_validator_accepts_forced_rng_without_mismatch():
    validator = ReplayValidator()
    replay_data = validator.load_replay(MULTISTEP_REPLAY_PATH)
    replay_data["steps"][0]["forced_rng"] = {"crit": False, "notes": "ignored in MVP"}

    result = validator.validate(replay_data)

    assert result.passed is True
    assert result.checked_steps == 3


def test_replay_validator_cli_passes_multistep_replay():
    completed = subprocess.run(
        [sys.executable, "-m", "hsr_axis_sim.sim.replay", str(MULTISTEP_REPLAY_PATH)],
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode == 0
    assert "PASS bronya_seele_multistep_mvp" in completed.stdout
    assert "checked 3 step(s)" in completed.stdout


def test_damage_rng_mvp_replay_passes_validation():
    validator = ReplayValidator()
    replay_data = validator.load_replay(DAMAGE_RNG_REPLAY_PATH)

    result = validator.validate(replay_data)

    assert result.passed is True
    assert result.replay_name == "damage_rng_mvp"
    assert result.checked_steps == 1


def test_replay_forced_rng_controls_calculated_crit_damage():
    validator = ReplayValidator()
    replay_data = validator.load_replay(DAMAGE_RNG_REPLAY_PATH)
    replay_data["steps"][0]["forced_rng"]["crit"] = False
    replay_data["steps"][0]["expect"]["units"]["enemy_1"]["hp"] = 8000

    result = validator.validate(replay_data)

    assert result.passed is True
    assert result.checked_steps == 1


def test_replay_validator_can_check_expected_buffs_and_debuffs():
    validator = ReplayValidator()
    replay_data = validator.load_replay(BUFF_DURATION_REPLAY_PATH)

    result = validator.validate(replay_data)

    assert result.passed is True
    assert result.checked_steps == 2


def test_buff_duration_mvp_replay_passes_validation():
    validator = ReplayValidator()
    replay_data = validator.load_replay(BUFF_DURATION_REPLAY_PATH)

    result = validator.validate(replay_data)

    assert result.passed is True
    assert result.replay_name == "buff_duration_mvp"
    assert result.checked_steps == 2


def test_replay_validator_reports_unsupported_buff_expectation_field():
    validator = ReplayValidator()
    replay_data = validator.load_replay(BUFF_DURATION_REPLAY_PATH)
    replay_data["steps"][0]["expect"]["units"]["seele"]["buffs"]["damage_boost"][
        "unsupported"
    ] = 1

    result = validator.validate(replay_data)

    assert result.passed is False
    assert any("unsupported expected status field" in mismatch for mismatch in result.mismatches)


def test_replay_validator_can_load_and_check_toughness_break_fields():
    validator = ReplayValidator()
    replay_data = validator.load_replay(TOUGHNESS_BREAK_REPLAY_PATH)

    result = validator.validate(replay_data)

    assert result.passed is True
    assert result.replay_name == "toughness_break_mvp"
    assert result.checked_steps == 2


def test_toughness_break_mvp_replay_passes_validation():
    validator = ReplayValidator()
    replay_data = validator.load_replay(TOUGHNESS_BREAK_REPLAY_PATH)

    result = validator.validate(replay_data)

    assert result.passed is True
    assert result.checked_steps == 2


def test_replay_validator_can_load_triggers():
    validator = ReplayValidator()
    replay_data = validator.load_replay(TRIGGER_REPLAY_PATH)

    state = validator.state_from_replay(replay_data)

    assert len(state.triggers) == 1
    assert state.triggers[0].id == "on_kill_extra_turn"
    assert state.triggers[0].owner_id == "seele_like"


def test_trigger_on_kill_extra_turn_mvp_replay_passes_validation():
    validator = ReplayValidator()
    replay_data = validator.load_replay(TRIGGER_REPLAY_PATH)

    result = validator.validate(replay_data)

    assert result.passed is True
    assert result.replay_name == "trigger_on_kill_extra_turn_mvp"
    assert result.checked_steps == 2


def test_replay_validator_reports_missing_expected_log_entry():
    validator = ReplayValidator()
    replay_data = validator.load_replay(TRIGGER_REPLAY_PATH)
    replay_data["steps"][0]["expect"]["logs_contains"] = ["trigger:missing"]

    result = validator.validate(replay_data)

    assert result.passed is False
    assert any("expected logs to contain" in mismatch for mismatch in result.mismatches)
