import pytest

from hsr_axis_sim.sim.data_schema import CharacterSpec


def valid_character_data():
    return {
        "id": "sample",
        "name": "Sample",
        "team": "ally",
        "element": "quantum",
        "path": "sample_path",
        "base_stats": {
            "hp": 1000,
            "atk": 100,
            "defense": 0,
            "base_speed": 100,
            "max_energy": 100,
            "crit_rate": 0,
            "crit_dmg": 0.5,
            "dmg_bonus": 0,
        },
        "skills": [
            {
                "id": "basic",
                "name": "Basic",
                "skill_type": "basic",
                "target_type": "single_enemy",
                "sp_delta": 1,
                "energy_delta": 20,
                "ends_turn": True,
                "effects": [{"type": "DealDamage", "amount": 100}],
            }
        ],
    }


def test_valid_character_loads():
    spec = CharacterSpec.from_dict(valid_character_data())

    assert spec.id == "sample"
    assert spec.base_stats.base_speed == 100
    assert spec.skills[0].id == "basic"


def test_missing_required_field_fails_clearly():
    data = valid_character_data()
    del data["base_stats"]["atk"]

    with pytest.raises(ValueError, match="missing required field"):
        CharacterSpec.from_dict(data)


def test_unknown_effect_type_fails_clearly():
    data = valid_character_data()
    data["skills"][0]["effects"] = [{"type": "UnknownEffect"}]

    with pytest.raises(ValueError, match="Unknown effect type"):
        CharacterSpec.from_dict(data)


def test_duplicate_skill_ids_fail_clearly():
    data = valid_character_data()
    data["skills"].append(dict(data["skills"][0]))

    with pytest.raises(ValueError, match="Duplicate skill id"):
        CharacterSpec.from_dict(data)

