import copy
import json
import subprocess
import sys

import pytest

from hsr_axis_sim.tools.trace_tingyun_ultimate_turn_entry_duration_gap import (
    DEFAULT_BILIBILI_TEMPLATE,
    DEFAULT_REVIEW,
    GAP_STATUSES,
    PROJECT_ROOT,
    ROOT,
    _validate_bilibili_template,
    build_report,
    load_json,
    render_json,
    render_markdown,
)


REPORTS = ROOT / "data" / "manual_video_traces" / "real_binding_audits"
REPORT_JSON = REPORTS / "tingyun_ultimate_turn_entry_duration_gap_v0_1.json"
REPORT_MD = REPORTS / "tingyun_ultimate_turn_entry_duration_gap_v0_1.md"


def evidence():
    return load_json(DEFAULT_REVIEW)


def expect_controlled_error(data, text):
    with pytest.raises(ValueError, match=text):
        build_report(data)


def test_exact_evidence_statuses_conclusion_and_readiness_are_preserved():
    report = build_report(evidence())
    claims = {row["claim_id"]: row for row in report.claims}
    assert claims["duration_count_2"]["verification_status"] == "source_cross_checked"
    assert claims["turn_entry_settlement"]["verification_status"] == "accepted_project_domain_correction_pending_independent_frame_verification"
    assert claims["bilibili_candidate"]["verification_status"] == "candidate_identified_page_or_frames_not_retrieved"
    assert claims["zero_counter_effect_lifetime"]["verification_status"] == "unresolved"
    assert claims["extra_action_consumption"]["verification_status"] == "unresolved_not_infer_from_normal_turn_entry"
    assert claims["extra_turn_consumption"]["verification_status"] == "unresolved_not_infer_from_normal_turn_entry"
    assert claims["turn_started_event_order"]["verification_status"] == "unresolved"
    assert report.conclusion == "turn_entry_claim_normalized_current_engine_gap_confirmed_runtime_change_blocked"
    assert report.generic_binding_readiness == "blocked_by_duration_semantics"
    assert report.accepted_video_binding_readiness == "blocked_by_unknown_target_and_trace_level"
    assert report.release_game_duration_policy is None
    assert report.simulator_binding_allowed is False


def test_current_engine_gap_and_all_unresolved_gap_ids_are_classified():
    report = build_report(evidence())
    gaps = {gap.gap_id: gap.status for gap in report.gaps}
    assert gaps == GAP_STATUSES
    assert report.engine_audit["target_normal_turn_tick_boundary"] == "Timeline.end_turn after a normal turn"
    assert report.engine_audit["target_normal_turn_entry_tick_path_present"] is False
    assert report.engine_audit["buff_application_turn_marker_present"] is False
    assert report.engine_audit["current_engine_conforms_to_accepted_boundary"] is False


def test_synthetic_matrix_reproduces_current_boundaries_without_release_inference():
    cases = {case.case_id: case for case in build_report(evidence()).boundary_matrix}
    assert len(cases) == 7
    before = cases["applied_before_next_normal_turn"].counter_checkpoints
    assert before == {"after_application": 2, "after_normal_turn_entry": 2, "after_normal_turn_end": 1}
    active = cases["applied_during_active_normal_turn"].counter_checkpoints
    assert active["after_interrupt_application"] == 2
    assert active["after_active_normal_turn_end"] == 1
    refresh = cases["same_id_refresh_during_active_normal_turn"].counter_checkpoints
    assert refresh["after_same_id_refresh"] == 2
    assert refresh["after_active_normal_turn_end"] == 1
    assert cases["non_ending_extra_action"].counter_checkpoints["after_non_ending_action"] == 2
    assert cases["granted_extra_turn"].counter_checkpoints == {"after_extra_turn_entry": 2, "after_extra_turn_end": 2}
    advanced = cases["action_advanced_into_next_normal_turn"].counter_checkpoints
    assert advanced["after_normal_turn_entry"] == 2 and advanced["after_normal_turn_end"] == 1
    transitions = cases["evidence_model_counter_transitions"].counter_checkpoints
    assert transitions["current_engine_after_entry_from_1"] == 1
    assert transitions["current_engine_after_end_from_1"] is None
    assert all(not case.fully_decidable and case.runtime_assertion_unsafe for case in cases.values())
    assert all(case.unresolved_fields for case in cases.values())


def test_bilibili_template_requires_unknown_fields_to_remain_unknown():
    template = load_json(DEFAULT_BILIBILI_TEMPLATE)
    assert template["bvid"] == "BV1yz4y1t79s"
    assert template["verification_status"] == "candidate_identified_page_or_frames_not_retrieved"
    for field in ("uploader", "timestamp_start_seconds", "timestamp_end_seconds", "transition_2_to_1_observation", "transition_1_to_0_observation"):
        invalid = copy.deepcopy(template)
        invalid[field] = "fabricated"
        issues = []
        _validate_bilibili_template(invalid, issues)
        assert issues


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (("accepted_project_domain_boundary", "target_normal_turn_end"), "accepted_project_domain_boundary"),
        (("release_game_duration_policy", "Policy A"), "obsolete end-turn Policy"),
        (("end_turn_dual_policy_selected", True), "end_turn_dual_policy_selected"),
        (("simulator_binding_allowed", True), "simulator_binding_allowed"),
        (("accepted_video_target", "target"), "accepted_video_target"),
        (("accepted_video_trace_level", 10), "accepted_video_trace_level"),
    ],
)
def test_obsolete_or_executable_policy_and_video_inference_are_rejected(mutation, message):
    data = evidence()
    data[mutation[0]] = mutation[1]
    expect_controlled_error(data, message)


def test_overstated_video_zero_extra_and_engine_conformance_claims_are_rejected():
    mutations = [
        ("bilibili_candidate", "verification_status", "video_verified"),
        ("zero_counter_effect_lifetime", "claim_value", True),
        ("extra_action_consumption", "claim_value", True),
        ("extra_turn_consumption", "claim_value", True),
    ]
    for claim_id, field, value in mutations:
        data = evidence()
        next(row for row in data["claims"] if row["claim_id"] == claim_id)[field] = value
        expect_controlled_error(data, "turn-entry duration audit validation failed")
    conforming = evidence()
    conforming["engine_audit"]["current_engine_conforms_to_accepted_boundary"] = True
    expect_controlled_error(conforming, "current_engine_conforms_to_accepted_boundary")


@pytest.mark.parametrize(
    ("claim_id", "field", "invented_value"),
    [
        ("zero_counter_effect_lifetime", "effect_active_during_entered_turn", "true"),
        ("extra_action_consumption", "extra_action_consumes", "true"),
        ("extra_turn_consumption", "extra_turn_consumes", "true"),
        ("turn_started_event_order", "event_order_relative_to_turn_started", "before_turn_started"),
        ("same_id_refresh_active_turn", "refresh_behavior", "refresh_consumes_active_turn"),
    ],
)
def test_unresolved_semantic_outputs_cannot_be_filled_with_invented_assertions(claim_id, field, invented_value):
    data = evidence()
    next(row for row in data["claims"] if row["claim_id"] == claim_id)[field] = invented_value
    expect_controlled_error(data, "exact accepted semantic contract")


@pytest.mark.parametrize("collection", ["supplied_references", "pinned_sources"])
def test_source_locator_pins_are_exact(collection):
    data = evidence()
    data[collection][0]["locators"][0] = "tampered"
    expect_controlled_error(data, "exact accepted locator contract")


def test_claim_source_ids_unresolved_labels_case_labels_and_gap_summary_are_exact():
    removed_source = evidence()
    next(row for row in removed_source["claims"] if row["claim_id"] == "duration_count_2")["source_ids"].pop()
    expect_controlled_error(removed_source, "exact accepted semantic contract")
    added_source = evidence()
    next(row for row in added_source["claims"] if row["claim_id"] == "duration_count_2")["source_ids"].append("timeline")
    expect_controlled_error(added_source, "exact accepted semantic contract")
    claim_label = evidence()
    next(row for row in claim_label["claims"] if row["claim_id"] == "duration_count_2")["unresolved_fields"][0] = "tampered"
    expect_controlled_error(claim_label, "exact accepted semantic contract")
    case_label = evidence()
    case_label["boundary_cases"][0]["unresolved_fields"][0] = "tampered"
    expect_controlled_error(case_label, "exact accepted boundary-case contract")
    gap_summary = evidence()
    gap_summary["gap_classifications"][0]["summary"] = "tampered"
    expect_controlled_error(gap_summary, "exact accepted gap contract")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("review_id", "tampered", "review_id must be"),
        ("version", "0.2", "version must be"),
    ],
)
def test_review_identity_is_exact(field, value, message):
    data = evidence()
    data[field] = value
    expect_controlled_error(data, message)


def test_community_simulator_cannot_be_promoted_to_release_authority():
    data = evidence()
    next(row for row in data["claims"] if row["claim_id"] == "turn_entry_settlement")["release_game_claim"] = "A community simulator proves release-game authority."
    expect_controlled_error(data, "community simulator")


def test_missing_proven_gap_duplicates_stale_pins_and_count_changes_are_rejected():
    missing = evidence()
    missing["gap_classifications"] = [row for row in missing["gap_classifications"] if row["gap_id"] != "GAP_TARGET_NORMAL_TURN_TICK_BOUNDARY"]
    expect_controlled_error(missing, "every required gap")
    duplicate = evidence()
    duplicate["claims"][1]["claim_id"] = duplicate["claims"][0]["claim_id"]
    expect_controlled_error(duplicate, "duplicate claim ID")
    duplicate_path = evidence()
    duplicate_path["pinned_sources"][1]["path"] = duplicate_path["pinned_sources"][0]["path"]
    expect_controlled_error(duplicate_path, "duplicate source path")
    stale = evidence()
    stale["pinned_sources"][0]["sha256"] = "0" * 64
    expect_controlled_error(stale, "accepted source pin")
    registry = evidence()
    registry["registry_expected_count"] = 3
    expect_controlled_error(registry, "registry_expected_count")
    manifest = evidence()
    manifest["manifest_expected_counts"]["replays"] = 13
    expect_controlled_error(manifest, "manifest_expected_counts.replays")


@pytest.mark.parametrize("invalid", [{"bad":"value"}, ["bad"], True, 7, None])
@pytest.mark.parametrize(
    "location",
    [
        ("review_id",),
        ("conclusion",),
        ("supplied_references",0,"source_id"),
        ("pinned_sources",0,"path"),
        ("claims",0,"claim_id"),
        ("claims",0,"verification_status"),
        ("claims",0,"claim_scope"),
        ("claims",0,"release_game_claim"),
        ("gap_classifications",0,"gap_id"),
        ("gap_classifications",0,"status"),
        ("boundary_cases",0,"case_id"),
        ("boundary_cases",0,"evidence_settlement_boundary"),
    ],
)
def test_json_compatible_scalar_mutations_are_controlled(location, invalid):
    data = evidence()
    target = data
    for key in location[:-1]:
        target = target[key]
    target[location[-1]] = invalid
    expect_controlled_error(data, "turn-entry duration audit validation failed")


def test_reversed_unordered_collections_are_deterministic():
    original = evidence()
    reversed_data = copy.deepcopy(original)
    for field in ("supplied_references", "pinned_sources", "claims", "gap_classifications", "boundary_cases"):
        reversed_data[field].reverse()
    for source in reversed_data["supplied_references"] + reversed_data["pinned_sources"]:
        source["locators"].reverse()
    for claim in reversed_data["claims"]:
        claim["source_ids"].reverse()
        claim["unresolved_fields"].reverse()
    for case in reversed_data["boundary_cases"]:
        case["unresolved_fields"].reverse()
    first, second = build_report(original), build_report(reversed_data)
    assert render_json(first) == render_json(second)
    assert render_markdown(first) == render_markdown(second)


def test_committed_reports_match_generated_bytes():
    report = build_report(evidence())
    assert REPORT_JSON.read_text(encoding="utf-8") == render_json(report)
    assert REPORT_MD.read_text(encoding="utf-8") == render_markdown(report)


def test_cli_stdout_file_and_exit_codes(tmp_path):
    module = "hsr_axis_sim.tools.trace_tingyun_ultimate_turn_entry_duration_gap"
    base = [sys.executable, "-m", module]
    stdout = subprocess.run(base + ["--format", "json"], cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
    assert stdout.returncode == 0
    assert stdout.stdout == render_json(build_report(evidence()))
    output = tmp_path / "report.md"
    written = subprocess.run(base + ["--format", "markdown", "--output", str(output)], cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
    assert written.returncode == 0
    assert output.read_text(encoding="utf-8") == render_markdown(build_report(evidence()))
    invalid = evidence()
    invalid["conclusion"] = []
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text(json.dumps(invalid), encoding="utf-8")
    failed = subprocess.run(base + ["--format", "json", "--review", str(invalid_path)], cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
    missing = subprocess.run(base + ["--format", "json", "--review", str(tmp_path / "missing.json")], cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
    assert failed.returncode == 1 and "Traceback" not in failed.stderr
    assert missing.returncode == 2 and "Traceback" not in missing.stderr


@pytest.mark.parametrize(
    ("claim_id", "field"),
    [
        ("zero_counter_effect_lifetime", "effect_active_during_entered_turn"),
        ("extra_action_consumption", "extra_action_consumes"),
        ("extra_turn_consumption", "extra_turn_consumes"),
    ],
)
def test_cli_confirmed_semantic_tampers_exit_1_without_report_body(tmp_path, claim_id, field):
    data = evidence()
    next(row for row in data["claims"] if row["claim_id"] == claim_id)[field] = "true"
    path = tmp_path / f"{claim_id}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    command = [
        sys.executable, "-m", "hsr_axis_sim.tools.trace_tingyun_ultimate_turn_entry_duration_gap",
        "--review", str(path), "--format", "json",
    ]
    result = subprocess.run(command, cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 1
    assert "FAIL Tingyun turn-entry duration validation" in result.stderr
    assert "Traceback" not in result.stderr
    assert result.stdout == ""
