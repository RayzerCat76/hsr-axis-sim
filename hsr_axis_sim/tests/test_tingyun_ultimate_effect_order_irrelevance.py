import copy
import json
import subprocess
import sys

import pytest

from hsr_axis_sim.tools.trace_tingyun_ultimate_effect_order_irrelevance import (
    DEFAULT_REVIEW,
    ROOT,
    STATE_FIELDS,
    UNIT_FIELDS,
    BUFF_FIELDS,
    EVENT_FIELDS,
    TRIGGER_FIELDS,
    TURN_CONTEXT_FIELDS,
    _validate_snapshot,
    build_report,
    load_json,
    run_comparison_case,
)


REPORTS = ROOT / "data" / "manual_video_traces" / "real_binding_audits"
REPORT_JSON = REPORTS / "tingyun_ultimate_effect_order_irrelevance_v0_1.json"
REPORT_MD = REPORTS / "tingyun_ultimate_effect_order_irrelevance_v0_1.md"


def evidence():
    return load_json(DEFAULT_REVIEW)


def historical_report():
    return json.loads(REPORT_JSON.read_text(encoding="utf-8"))


def current_supersession_error(data=None):
    with pytest.raises(ValueError) as exc_info:
        build_report(evidence() if data is None else data)
    message = str(exc_info.value)
    assert "effect-order proof validation failed" in message
    assert "sha256 is stale" in message
    assert "pinned_sources must contain every required current-contract source" in message
    return message


def expect_controlled_error(data, text):
    with pytest.raises(ValueError, match=text):
        build_report(data)


def test_every_required_comparison_is_preserved_as_historical_but_no_longer_current():
    report = historical_report()
    assert report["conclusion"] == "proven_irrelevant_under_current_simulator_contract"
    assert report["every_case_equal"] is True
    assert len(report["comparison_results"]) == 6
    assert all(item["equal"] for item in report["comparison_results"])
    assert report["derived_generic_readiness"] == "blocked_by_duration_semantics"
    assert report["accepted_video_binding_readiness"] == "blocked_by_unknown_target_and_trace_level"
    assert report["release_game_order_known"] is False
    assert report["same_current_turn_duration_resolved"] is False
    assert report["accepted_video_target"] is None
    assert report["accepted_video_trace_level"] is None
    assert report["simulator_binding_allowed"] is False
    current_supersession_error()


def test_complete_historical_snapshot_contract_is_preserved_while_current_validation_rejects():
    report = historical_report()
    contract = report["observation_contract"]
    assert set(contract["state_fields"]) == set(STATE_FIELDS)
    assert set(contract["unit_fields"]) == set(UNIT_FIELDS)
    assert set(contract["buff_fields"]) == set(BUFF_FIELDS)
    assert set(contract["event_fields"]) == set(EVENT_FIELDS)
    assert set(contract["trigger_fields"]) == set(TRIGGER_FIELDS)
    assert set(contract["turn_context_fields"]) == set(TURN_CONTEXT_FIELDS)
    assert contract["excluded_fields"] == []
    snapshot = report["comparison_results"][0]["order_a_snapshot"]
    assert snapshot["turn_context"]["is_interrupt"] is True
    assert snapshot["turn_context"]["should_end_turn"] is False
    assert snapshot["action_result"] == {"return_type": "TurnContext", "returned_same_context": True}
    assert [event["type"] for event in snapshot["state"]["pending_events"]][-2:] == ["action_started", "action_finished"]
    assert snapshot["state"]["trigger_fire_counts"] == {"order_probe_action_finished": 1, "order_probe_action_started": 1}
    assert snapshot["state"]["event_dispatch_count"] == 2
    current_supersession_error()


def test_positive_conclusion_rejects_missing_or_failed_case():
    missing = evidence()
    missing["comparison_cases"].pop()
    expect_controlled_error(missing, "exact six required cases")
    failed = evidence()
    failed["comparison_cases"][0]["expected_equal"] = False
    expect_controlled_error(failed, "expected_equal must be true")


def test_stale_digest_duplicate_source_and_duplicate_case_are_rejected():
    stale = evidence()
    stale["pinned_sources"][0]["sha256"] = "0" * 64
    expect_controlled_error(stale, "sha256 is stale")
    duplicate_source = evidence()
    duplicate_source["pinned_sources"][1]["source_id"] = duplicate_source["pinned_sources"][0]["source_id"]
    expect_controlled_error(duplicate_source, "duplicate source ID")
    duplicate_case = evidence()
    duplicate_case["comparison_cases"][1]["case_id"] = duplicate_case["comparison_cases"][0]["case_id"]
    expect_controlled_error(duplicate_case, "duplicate case ID")


@pytest.mark.parametrize(
    ("field", "invalid", "message"),
    [
        ("release_game_order_known", True, "release_game_order_known"),
        ("same_current_turn_duration_resolved", True, "same_current_turn_duration_resolved"),
        ("simulator_binding_allowed", True, "simulator_binding_allowed"),
        ("accepted_video_target", "target", "accepted_video_target"),
        ("accepted_video_trace_level", 10, "accepted_video_trace_level"),
        ("registry_expected_count", 3, "registry_expected_count"),
    ],
)
def test_positive_conclusion_cannot_cross_safety_boundaries(field, invalid, message):
    data = evidence()
    data[field] = invalid
    expect_controlled_error(data, message)


def test_manifest_count_changes_and_incomplete_observation_contract_are_rejected():
    counts = evidence()
    counts["manifest_expected_counts"]["replays"] = 13
    expect_controlled_error(counts, "manifest_expected_counts.replays")
    omitted = evidence()
    omitted["observation_contract"]["state_fields"].remove("logs")
    expect_controlled_error(omitted, "every required observable field")


@pytest.mark.parametrize("invalid", [{"bad": "value"}, ["bad"], True, 7, None])
@pytest.mark.parametrize(
    "location",
    [
        ("review_id",),
        ("conclusion",),
        ("pinned_sources", 0, "source_id"),
        ("pinned_sources", 0, "path"),
        ("pinned_sources", 0, "sha256"),
        ("pinned_sources", 0, "locators", 0),
        ("comparison_cases", 0, "case_id"),
        ("comparison_cases", 0, "target_energy"),
        ("comparison_cases", 0, "target_max_energy"),
        ("synthetic_fixture", "units", 0, "id"),
        ("synthetic_fixture", "units", 0, "hp"),
        ("synthetic_fixture", "pending_events", 0, "type"),
        ("synthetic_fixture", "triggers", 0, "event_type"),
        ("synthetic_fixture", "unrelated_statuses", 0, "id"),
    ],
)
def test_json_compatible_scalar_mutations_never_leak_native_exceptions(location, invalid):
    data = evidence()
    target = data
    for key in location[:-1]:
        target = target[key]
    target[location[-1]] = invalid
    expect_controlled_error(data, "effect-order proof validation failed")


def test_malformed_nested_fixture_data_is_controlled():
    mutations = [
        ("units", 0, "weaknesses", {"bad": "value"}),
        ("unrelated_statuses", 0, "data", ["bad"]),
        ("pending_events", 0, "data", ["bad"]),
        ("triggers", 0, "condition", ["bad"]),
    ]
    for collection, index, field, invalid in mutations:
        data = evidence()
        data["synthetic_fixture"][collection][index][field] = invalid
        expect_controlled_error(data, "synthetic_fixture")


def test_snapshot_validator_rejects_omissions_and_malformed_nested_data():
    data = evidence()
    fixture = data["synthetic_fixture"]
    snapshot = run_comparison_case(fixture, 10, 100, False, "energy_then_buff")
    mutations = []
    missing_state = copy.deepcopy(snapshot)
    del missing_state["state"]["logs"]
    mutations.append(missing_state)
    malformed_unit = copy.deepcopy(snapshot)
    malformed_unit["state"]["units"][0] = []
    mutations.append(malformed_unit)
    malformed_event = copy.deepcopy(snapshot)
    malformed_event["state"]["pending_events"][0]["data"] = []
    mutations.append(malformed_event)
    malformed_trigger = copy.deepcopy(snapshot)
    malformed_trigger["state"]["triggers"][0]["effects"] = {}
    mutations.append(malformed_trigger)
    malformed_buff = copy.deepcopy(snapshot)
    target = next(unit for unit in malformed_buff["state"]["units"] if unit["id"] == "target")
    del target["buffs"]["synthetic_tingyun_order_probe"]["data"]
    mutations.append(malformed_buff)
    missing_context = copy.deepcopy(snapshot)
    del missing_context["turn_context"]["forced_rng"]
    mutations.append(missing_context)
    for index, mutation in enumerate(mutations):
        with pytest.raises(ValueError, match="snapshot validation failed"):
            _validate_snapshot(mutation, f"mutation[{index}]")


def test_reversed_historical_input_is_still_controlled_as_superseded():
    original = evidence()
    reversed_data = copy.deepcopy(original)
    for field in ("pinned_sources", "implementation_locators", "comparison_cases", "proof_boundaries"):
        reversed_data[field].reverse()
    for source in reversed_data["pinned_sources"]:
        source["locators"].reverse()
    for values in reversed_data["observation_contract"].values():
        values.reverse()
    current_supersession_error(original)
    current_supersession_error(reversed_data)


def test_committed_historical_reports_remain_readable_but_are_not_regenerated_from_current_engine():
    report = historical_report()
    source = evidence()
    effects_pin = next(row for row in source["pinned_sources"] if row["source_id"] == "effects")
    assert "GainEnergy.apply: max-Energy clamp assignment with no event emission" in effects_pin["locators"]
    assert any("No current primitive event exposes intermediate state" in item for item in source["proof_boundaries"])
    assert report["conclusion"] == "proven_irrelevant_under_current_simulator_contract"
    assert "NON-EXECUTABLE CURRENT-CONTRACT PROOF" in REPORT_MD.read_text(encoding="utf-8")
    current_supersession_error()


def test_cli_now_rejects_default_historical_current_contract_proof_without_traceback(tmp_path):
    module = "hsr_axis_sim.tools.trace_tingyun_ultimate_effect_order_irrelevance"
    base = [sys.executable, "-m", module]
    stdout = subprocess.run(base + ["--format", "json"], cwd=ROOT.parent, text=True, capture_output=True, check=False)
    assert stdout.returncode == 1
    assert stdout.stdout == ""
    assert "sha256 is stale" in stdout.stderr
    assert "Traceback" not in stdout.stderr

    output = tmp_path / "report.md"
    written = subprocess.run(base + ["--format", "markdown", "--output", str(output)], cwd=ROOT.parent, text=True, capture_output=True, check=False)
    assert written.returncode == 1
    assert not output.exists()
    assert "Traceback" not in written.stderr

    invalid = evidence()
    invalid["conclusion"] = []
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text(json.dumps(invalid), encoding="utf-8")
    failed = subprocess.run(base + ["--format", "json", "--review", str(invalid_path)], cwd=ROOT.parent, text=True, capture_output=True, check=False)
    missing = subprocess.run(base + ["--format", "json", "--review", str(tmp_path / "missing.json")], cwd=ROOT.parent, text=True, capture_output=True, check=False)
    assert failed.returncode == 1 and "Traceback" not in failed.stderr
    assert missing.returncode == 2 and "Traceback" not in missing.stderr
