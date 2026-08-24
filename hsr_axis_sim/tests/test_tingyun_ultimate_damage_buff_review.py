import copy
import json
import subprocess
import sys
from pathlib import Path

from hsr_axis_sim.sim import Action, AddBuff, BattleState, Timeline, TurnContext, Unit
from hsr_axis_sim.tools.trace_tingyun_ultimate_damage_buff_review import (
    DEFAULT_FACTS,
    DEFAULT_SOURCES,
    build_report,
    load_json,
    render_json,
    render_markdown,
)


BASE = Path(__file__).resolve().parents[1]
REPORTS = BASE / "data" / "manual_video_traces" / "real_binding_audits"


def inputs():
    return load_json(DEFAULT_SOURCES), load_json(DEFAULT_FACTS)


def expect_error(values, text):
    try:
        build_report(*values)
    except ValueError as exc:
        assert text in str(exc)
    else:
        raise AssertionError("Expected damage-buff review validation failure.")


def test_atomic_fact_coverage_provenance_and_readiness():
    report = build_report(*inputs())
    facts = {fact.fact_id: fact for fact in report.facts}
    assert report.readiness_status == "blocked_by_both"
    assert report.simulator_binding_allowed is False
    assert facts["tingyun.ultimate.damage_buff.target_scope"].normalized_value == "selected_single_ally"
    assert facts["tingyun.ultimate.damage_buff.duration_turns"].normalized_value == 2
    assert facts["tingyun.ultimate.damage_buff.magnitude_by_trace_level"].verification_status == "missing"
    assert facts["tingyun.ultimate.damage_buff.application_order"].verification_status == "unresolved"
    assert facts["tingyun.ultimate.damage_buff.real_video_trace_level"].normalized_value is None
    assert all(fact.simulator_binding_allowed is False for fact in report.facts)
    assert all(item.source_locator for fact in report.facts for item in fact.provenance)
    assert all(item.field_locator for fact in report.facts for item in fact.provenance)


def test_duration_boundary_matches_current_engine_behavior():
    report = build_report(*inputs())
    assessment = report.duration_semantics
    target = Unit("target", "Target", "ally", 100, current_av=0)
    source = Unit("tingyun", "Tingyun", "ally", 110, current_av=50)
    state = BattleState([target, source])
    active_target_turn = Timeline.next_turn(state)
    interrupt = Action(
        id="review_only_buff_probe",
        name="Review-only buff probe",
        actor_id="tingyun",
        target_ids=["target"],
        effects=[AddBuff(id="probe", name="Probe", remaining_turns=2)],
        ends_turn=False,
    )
    interrupt.execute(state, TurnContext(actor_id="tingyun", is_interrupt=True))
    assert target.buffs["probe"].remaining_turns == 2
    Timeline.end_turn(state, active_target_turn)
    assert target.buffs["probe"].remaining_turns == 1
    Timeline.end_turn(state, TurnContext(actor_id="target", is_extra_turn=True))
    assert target.buffs["probe"].remaining_turns == 1
    Timeline.end_turn(state, TurnContext(actor_id="target"))
    assert "probe" not in target.buffs
    assert assessment.cast_interrupt_decrements is False
    assert assessment.current_target_normal_turn_decrements_at_end_if_already_applied is True
    assert assessment.extra_turn_decrements is False
    assert assessment.non_ending_action_decrements is False
    assert assessment.engine_representation_status == "representable_with_source_unverified_same_turn_edge"
    assert assessment.verified_game_equivalence is False


def test_schema_provenance_status_and_executable_fields_rejected():
    values = list(inputs())
    values[1]["facts"][0]["verification_status"] = "verified_by_guess"
    expect_error(values, "verification_status")

    values = list(inputs())
    values[1]["facts"][0]["provenance"][0]["source_id"] = "missing_source"
    expect_error(values, "dangling source")

    values = list(inputs())
    values[1]["facts"][0]["provenance"][0]["release_status"] = "beta_leak"
    expect_error(values, "release_status")

    values = list(inputs())
    values[1]["facts"][0]["provenance"][0]["locator"] = ""
    expect_error(values, "locator")

    values = list(inputs())
    values[1]["facts"][0]["simulator_binding_allowed"] = True
    expect_error(values, "simulator_binding_allowed")

    values = list(inputs())
    values[1]["effects"] = []
    expect_error(values, "executable schema")


def test_enum_like_values_and_source_catalog_fields_have_strict_types():
    for field in ("verification_status",):
        for value in ({"bad": True}, ["bad"]):
            values = list(inputs())
            values[1]["facts"][0][field] = value
            expect_error(values, field)
    for field in ("source_id", "release_status", "corroboration_status"):
        for value in ({"bad": True}, ["bad"]):
            values = list(inputs())
            values[1]["facts"][0]["provenance"][0][field] = value
            expect_error(values, field)
    for value in ({"bad": True}, ["bad"]):
        values = list(inputs())
        values[1]["declared_readiness_status"] = value
        expect_error(values, "declared_readiness_status")
    for field in ("title", "locator", "source_type", "language", "game_version"):
        for value in ({"bad": True}, ["bad"]):
            values = list(inputs())
            values[0]["sources"][0][field] = value
            expect_error(values, f"sources[0].{field}")


def test_duplicate_provenance_and_fact_specific_values_rejected():
    values = list(inputs())
    values[1]["facts"][0]["provenance"].append(
        copy.deepcopy(values[1]["facts"][0]["provenance"][0])
    )
    expect_error(values, "duplicate source IDs")

    cases = [
        ("tingyun.ultimate.damage_buff.target_scope", "normalized_value", "all_allies", "normalized_value"),
        ("tingyun.ultimate.damage_buff.duration_turns", "normalized_value", 999, "integer 2"),
        ("tingyun.ultimate.damage_buff.duration_turns", "normalized_value", True, "integer 2"),
        ("tingyun.ultimate.damage_buff.duration_turns", "unit", "percent", ".unit"),
        ("tingyun.ultimate.damage_buff.duration_turns", "unit", {"bad": True}, ".unit"),
        ("tingyun.ultimate.damage_buff.release_scope", "normalized_value", {"bad": True}, "normalized_value"),
        ("tingyun.ultimate.damage_buff.magnitude_by_trace_level", "normalized_value", {"level_10": 50}, "normalized_value"),
        ("tingyun.ultimate.damage_buff.application_order", "normalized_value", "before_energy", "normalized_value"),
    ]
    for fact_id, field, value, text in cases:
        values = list(inputs())
        fact = next(item for item in values[1]["facts"] if item["fact_id"] == fact_id)
        fact[field] = value
        expect_error(values, text)


def test_all_direct_malformed_schema_cases_raise_value_error():
    malformed_values = [
        (["not-an-object"], load_json(DEFAULT_FACTS)),
        (load_json(DEFAULT_SOURCES), ["not-an-object"]),
    ]
    for values in malformed_values:
        try:
            build_report(*values)
        except ValueError:
            pass
        except Exception as exc:
            raise AssertionError(f"Expected controlled ValueError, got {type(exc).__name__}") from exc
        else:
            raise AssertionError("Expected validation failure")


def test_malformed_provenance_rows_are_rejected_before_sorting():
    for locator in ({"bad": 1}, ["bad"]):
        values = list(inputs())
        duplicate = copy.deepcopy(values[1]["facts"][0]["provenance"][0])
        duplicate["locator"] = locator
        values[1]["facts"][0]["provenance"][1] = duplicate
        expect_error(values, "locator")

    for source_ids, locators in [
        (({"bad": 1}, ["bad"]), ({"bad": 1}, "valid locator")),
        ((["bad"], {"bad": 1}), (["bad"], "valid locator")),
    ]:
        values = list(inputs())
        provenance = values[1]["facts"][0]["provenance"]
        provenance[0]["source_id"], provenance[1]["source_id"] = source_ids
        provenance[0]["locator"], provenance[1]["locator"] = locators
        expect_error(values, "source_id")

    values = list(inputs())
    values[1]["facts"][0]["provenance"][0]["locator"] = {"bad": 1}
    values[1]["facts"][0]["provenance"][0]["evidence_summary"] = ["bad"]
    expect_error(values, "evidence_summary")


def test_duplicate_missing_fact_and_readiness_mismatch_rejected():
    values = list(inputs())
    values[1]["facts"].append(copy.deepcopy(values[1]["facts"][0]))
    expect_error(values, "fact IDs must be unique")

    values = list(inputs())
    values[1]["facts"].pop()
    expect_error(values, "exact required")

    values = list(inputs())
    values[1]["declared_readiness_status"] = "ready_for_separate_binding_task"
    expect_error(values, "computed status")


def test_duration_assessment_contract_rejected_when_distorted():
    for field, value in [
        ("verified_duration_turns", 3),
        ("cast_interrupt_decrements", True),
        ("extra_turn_decrements", True),
        ("non_ending_action_decrements", True),
        ("verified_game_equivalence", True),
    ]:
        values = list(inputs())
        values[1]["duration_semantics"][field] = value
        expect_error(values, f"duration_semantics.{field}")


def test_input_order_determinism_and_committed_reports():
    values = list(inputs())
    expected = build_report(*values)
    values[1]["facts"].reverse()
    for fact in values[1]["facts"]:
        fact["provenance"].reverse()
    actual = build_report(*values)
    assert render_json(actual) == render_json(expected)
    assert render_markdown(actual) == render_markdown(expected)
    assert render_markdown(expected) == (REPORTS / "tingyun_ultimate_damage_buff_readiness_v0_1.md").read_text(encoding="utf-8")
    assert render_json(expected) == (REPORTS / "tingyun_ultimate_damage_buff_readiness_v0_1.json").read_text(encoding="utf-8")


def test_cli_stdout_file_and_exit_codes(tmp_path):
    command = [
        sys.executable,
        "-m",
        "hsr_axis_sim.tools.trace_tingyun_ultimate_damage_buff_review",
    ]
    markdown = subprocess.run(command + ["--format", "markdown"], capture_output=True, text=True)
    output = tmp_path / "review.json"
    written = subprocess.run(
        command + ["--format", "json", "--output", str(output)],
        capture_output=True,
        text=True,
    )
    invalid_data = load_json(DEFAULT_FACTS)
    invalid_data["declared_readiness_status"] = {"bad": True}
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text(json.dumps(invalid_data), encoding="utf-8")
    invalid = subprocess.run(
        command + ["--facts", str(invalid_path), "--format", "json"],
        capture_output=True,
        text=True,
    )
    unreadable = subprocess.run(
        command + ["--facts", str(tmp_path / "missing.json"), "--format", "json"],
        capture_output=True,
        text=True,
    )
    assert markdown.returncode == written.returncode == 0
    assert markdown.stdout == (REPORTS / "tingyun_ultimate_damage_buff_readiness_v0_1.md").read_text(encoding="utf-8")
    assert output.read_text(encoding="utf-8") == (REPORTS / "tingyun_ultimate_damage_buff_readiness_v0_1.json").read_text(encoding="utf-8")
    assert invalid.returncode == 1
    assert unreadable.returncode == 2
    assert "Traceback" not in invalid.stderr + unreadable.stderr


def test_cli_malformed_provenance_exits_one_without_traceback(tmp_path):
    malformed = load_json(DEFAULT_FACTS)
    duplicate = copy.deepcopy(malformed["facts"][0]["provenance"][0])
    duplicate["locator"] = {"bad": 1}
    malformed["facts"][0]["provenance"][1] = duplicate
    path = tmp_path / "malformed_provenance.json"
    path.write_text(json.dumps(malformed), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "hsr_axis_sim.tools.trace_tingyun_ultimate_damage_buff_review",
            "--facts",
            str(path),
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
