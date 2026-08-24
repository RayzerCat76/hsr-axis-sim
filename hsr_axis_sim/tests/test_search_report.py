import json

from hsr_axis_sim.search import (
    Evaluator,
    beam_search,
    build_search_report,
    format_axis,
    format_axis_markdown,
    format_axis_text,
    search_report_to_dict,
)
from hsr_axis_sim.sim import BattleState, Unit
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


def make_result(beam_width=2):
    ally = Unit("carry", "Carry", "ally", 100, current_av=0, hp=1000, max_hp=1000)
    enemy = Unit("enemy", "Enemy", "enemy", 100, current_av=100, hp=50, max_hp=50)
    state = BattleState(units=[ally, enemy], skill_points=3)
    skills = {
        "carry": {
            "poke": make_skill("poke", 10),
            "kill": make_skill("kill", 100),
        }
    }
    return beam_search(state, skills, max_depth=1, beam_width=beam_width)


def test_report_can_be_built_from_beam_search_result():
    result = make_result()

    report = build_search_report(result)

    assert report.best_score == result.best_node.score
    assert report.best_terminal_reason == "all_enemies_defeated"
    assert report.nodes_expanded == result.nodes_expanded
    assert report.final_beam_count == len(result.final_beam)


def test_best_axis_steps_are_present_and_ordered():
    report = build_search_report(make_result())

    assert [step.step for step in report.best_axis_steps] == [1]
    assert report.best_axis_steps[0].actor_id == "carry"
    assert report.best_axis_steps[0].action_id == "kill"
    assert report.best_axis_steps[0].target_ids == ["enemy"]


def test_markdown_contains_expected_sections():
    report = build_search_report(make_result())

    markdown = format_axis_markdown(report)

    assert "# HSR Axis Search Report" in markdown
    assert "## Summary" in markdown
    assert "## Best Axis" in markdown
    assert "## Final Beam Candidates" in markdown


def test_text_report_is_readable():
    report = build_search_report(make_result())

    text = format_axis_text(report)

    assert "HSR Axis Search Report" in text
    assert "Best Axis" in text
    assert "carry uses kill on enemy" in text


def test_dict_export_is_json_serializable():
    report = build_search_report(make_result(), evaluator=Evaluator("generic_kill"))

    payload = search_report_to_dict(report)

    encoded = json.dumps(payload, sort_keys=True)
    assert "best_axis_steps" in encoded
    assert payload["final_score_breakdown"]["profile_id"] == "generic_kill"


def test_score_breakdown_appears_when_evaluator_is_provided():
    report = build_search_report(make_result(), evaluator=Evaluator("damage_race"))
    markdown = format_axis_markdown(report)

    assert report.final_score_breakdown is not None
    assert report.final_score_breakdown.profile_id == "damage_race"
    assert "## Score Breakdown" in markdown
    assert "damage_race total=" in markdown


def test_top_k_candidate_limit_works():
    report = build_search_report(make_result(beam_width=2), top_k=1)

    assert len(report.top_candidates) == 1
    assert report.top_candidates[0].rank == 1


def test_existing_format_axis_compatibility_is_not_broken():
    result = make_result()

    axis = format_axis(result.best_node)

    assert "AV 0.000" in axis
    assert "carry uses kill on enemy" in axis
    assert "SP=3" in axis
