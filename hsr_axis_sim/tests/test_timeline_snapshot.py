import json

from hsr_axis_sim.search import (
    Evaluator,
    beam_search,
    build_search_report,
    format_axis_markdown,
    format_axis_text,
    search_report_to_dict,
    snapshot_battle_state,
)
from hsr_axis_sim.sim import BattleState, Unit
from hsr_axis_sim.sim.buffs import Buff
from hsr_axis_sim.sim.data_schema import SkillSpec


def make_skill(skill_id, amount):
    return SkillSpec(
        id=skill_id,
        name=skill_id,
        skill_type="skill",
        target_type="single_enemy",
        sp_delta=0,
        energy_delta=0,
        ends_turn=True,
        effects=[
            {
                "type": "DealDamage",
                "amount": amount,
                "target_ref": "action_targets",
            }
        ],
    )


def make_result():
    ally = Unit("carry", "Carry", "ally", 100, current_av=0, hp=1000, max_hp=1000)
    enemy = Unit(
        "enemy",
        "Enemy",
        "enemy",
        100,
        current_av=100,
        hp=50,
        max_hp=50,
        current_toughness=20,
        max_toughness=60,
    )
    state = BattleState(units=[ally, enemy], skill_points=3)
    skills = {"carry": {"kill": make_skill("kill", 100)}}
    return beam_search(state, skills, max_depth=1, beam_width=1)


def test_snapshot_helper_returns_stable_unit_snapshots():
    ally = Unit("ally", "Ally", "ally", 120, current_av=12, hp=800, max_hp=1000)
    enemy = Unit("enemy", "Enemy", "enemy", 90, current_av=33, hp=500, max_hp=600)
    ally.buffs["atk_up"] = Buff(
        id="atk_up",
        name="ATK Up",
        target_id="ally",
        source_id=None,
        kind="buff",
        duration_type="target_normal_turns",
        remaining_turns=1,
    )
    state = BattleState(units=[ally, enemy], global_av=7, skill_points=2)

    snapshot = snapshot_battle_state(state)

    assert snapshot.global_av == 7
    assert snapshot.skill_points == 2
    assert [unit.unit_id for unit in snapshot.units] == ["ally", "enemy"]
    assert snapshot.units[0].buffs == ["atk_up"]
    assert snapshot.units[1].team == "enemy"


def test_json_report_includes_snapshot_after_for_best_axis_steps():
    report = build_search_report(make_result(), evaluator=Evaluator())

    payload = search_report_to_dict(report)

    snapshot_after = payload["best_axis_steps"][0]["snapshot_after"]
    assert snapshot_after["skill_points"] == 3
    assert snapshot_after["units"][1]["unit_id"] == "enemy"
    assert json.dumps(payload, sort_keys=True)


def test_markdown_with_snapshots_contains_timeline_section():
    report = build_search_report(make_result())

    markdown = format_axis_markdown(report, include_snapshots=True)

    assert "## Timeline Snapshots" in markdown
    assert "### After Step 1" in markdown
    assert "| Unit | Team | HP | Energy | AV | Toughness | Broken | Alive |" in markdown


def test_text_with_snapshots_contains_timeline_section():
    report = build_search_report(make_result())

    text = format_axis_text(report, include_snapshots=True)

    assert "Timeline Snapshots" in text
    assert "After Step 1" in text
    assert "Unit | Team | HP | Energy | AV | Toughness | Broken | Alive" in text
