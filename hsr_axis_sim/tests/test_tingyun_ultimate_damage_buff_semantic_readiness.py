import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from hsr_axis_sim.tools.trace_tingyun_ultimate_damage_buff_semantic_readiness import (
    DEFAULT_REVIEW,
    EXPECTED_INPUTS,
    ROOT,
    build_report,
    load_json,
    render_json,
    render_markdown,
)


REPORTS = ROOT / "data" / "manual_video_traces" / "real_binding_audits"
REPORT_JSON = REPORTS / "tingyun_ultimate_damage_buff_semantic_readiness_v0_1.json"
REPORT_MD = REPORTS / "tingyun_ultimate_damage_buff_semantic_readiness_v0_1.md"


def review_data():
    return load_json(DEFAULT_REVIEW)


def expect_error(data, text, root=ROOT):
    with pytest.raises(ValueError, match=text):
        build_report(data, root=root)


def copied_inputs(tmp_path, data):
    for path in EXPECTED_INPUTS.values():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / path).read_bytes())
    return data


def refresh_digest(data, role, root):
    row = next(item for item in data["input_artifacts"] if item["role"] == role)
    row["sha256"] = hashlib.sha256((root / row["path"]).read_bytes()).hexdigest()


def test_committed_readiness_axes_and_exact_magnitude_table():
    report = build_report(review_data())
    assert report.generic_binding_readiness == "blocked_by_both_semantics"
    assert report.accepted_video_binding_readiness == "blocked_by_unknown_target_and_trace_level"
    assert report.accepted_video_semantic_readiness == "blocked_by_both_semantics"
    assert report.magnitude_levels_validated == tuple(range(1, 16))
    assert report.magnitude_percentages == (20, 23, 26, 29, 32, 35, 38.75, 42.5, 46.25, 50, 53, 56, 59, 62, 65)
    assert report.selected_magnitude_level is None
    assert report.simulator_binding_allowed is False


def test_effect_order_and_same_turn_edge_remain_unresolved():
    claims = {item.claim_id: item for item in build_report(review_data()).semantic_claims}
    assert claims["effect_order"].status == "unresolved"
    assert claims["same_current_turn_duration"].status == "unresolved"
    assert claims["accepted_video_target"].normalized_value is None
    assert claims["accepted_video_trace_level"].normalized_value is None


def test_wrong_magnitude_digest_and_path_are_rejected():
    wrong_digest = review_data()
    next(item for item in wrong_digest["input_artifacts"] if item["role"] == "magnitude_intake")["sha256"] = "0" * 64
    expect_error(wrong_digest, "sha256 does not match")
    wrong_path = review_data()
    next(item for item in wrong_path["input_artifacts"] if item["role"] == "magnitude_intake")["path"] = "data/wrong.json"
    expect_error(wrong_path, "path must be")


def test_magnitude_intake_must_remain_captured_exact_table(tmp_path):
    data = copied_inputs(tmp_path, review_data())
    magnitude_path = tmp_path / EXPECTED_INPUTS["magnitude_intake"]
    magnitude = json.loads(magnitude_path.read_text(encoding="utf-8"))
    magnitude["intake_status"] = "blocked_source_unavailable"
    magnitude_path.write_text(json.dumps(magnitude), encoding="utf-8")
    refresh_digest(data, "magnitude_intake", tmp_path)
    expect_error(data, "magnitude intake", root=tmp_path)


@pytest.mark.parametrize("value", [{"bad": "value"}, ["bad"], True, 0, None])
@pytest.mark.parametrize(
    ("claim_index", "field"),
    [
        (0, "claim_id"),
        (0, "semantic_field"),
        (0, "status"),
        (0, "normalized_value"),
        (0, "value_type"),
        (1, "unit"),
        (0, "evidence_summary"),
        (0, "unresolved_notes"),
        (0, "simulator_binding_allowed"),
    ],
)
def test_json_compatible_malformed_values_are_controlled_for_every_scalar_claim_field(claim_index, field, value):
    data = review_data()
    data["semantic_claims"][claim_index][field] = value
    expect_error(data, "semantic readiness validation failed")


def test_malformed_readiness_fields_are_rejected():
    for field in ("generic_binding_readiness", "accepted_video_binding_readiness", "accepted_video_semantic_readiness"):
        data = review_data()
        data[field] = []
        expect_error(data, field)


def test_duplicate_provenance_ids_and_conflicting_evidence_are_rejected():
    duplicate = review_data()
    duplicate["semantic_claims"][1]["provenance"][0]["provenance_id"] = duplicate["semantic_claims"][0]["provenance"][0]["provenance_id"]
    expect_error(duplicate, "duplicate provenance ID")
    conflict = review_data()
    conflict["semantic_claims"][3]["provenance"][0]["relationship"] = "conflicts"
    expect_error(conflict, "conflicting semantic evidence")


def test_reversed_unordered_inputs_are_deterministic():
    original = review_data()
    reversed_data = copy.deepcopy(original)
    for field in ("input_artifacts", "semantic_claims", "generic_blockers", "accepted_video_blockers", "interaction_protocols"):
        reversed_data[field].reverse()
    for claim in reversed_data["semantic_claims"]:
        claim["provenance"].reverse()
    for protocol in reversed_data["interaction_protocols"]:
        protocol["preconditions"].reverse()
        protocol["required_observations"].reverse()
    first = build_report(original)
    second = build_report(reversed_data)
    assert render_json(first) == render_json(second)
    assert render_markdown(first) == render_markdown(second)


def test_committed_reports_match_generated_bytes():
    report = build_report(review_data())
    assert REPORT_JSON.read_text(encoding="utf-8") == render_json(report)
    assert REPORT_MD.read_text(encoding="utf-8") == render_markdown(report)


def test_cli_stdout_and_output_file(tmp_path):
    command = [sys.executable, "-m", "hsr_axis_sim.tools.trace_tingyun_ultimate_damage_buff_semantic_readiness", "--format", "json"]
    stdout = subprocess.run(command, cwd=ROOT.parent, text=True, capture_output=True, check=False)
    assert stdout.returncode == 0
    assert stdout.stdout == render_json(build_report(review_data()))
    output = tmp_path / "report.md"
    file_run = subprocess.run(command[:-1] + ["markdown", "--output", str(output)], cwd=ROOT.parent, text=True, capture_output=True, check=False)
    assert file_run.returncode == 0
    assert output.read_text(encoding="utf-8") == render_markdown(build_report(review_data()))


@pytest.mark.parametrize("status", [{"bad": "status"}, ["bad"]])
def test_cli_status_object_or_list_returns_exit_1_without_traceback(tmp_path, status):
    invalid = review_data()
    invalid["semantic_claims"][0]["status"] = status
    invalid_path = tmp_path / "invalid-status.json"
    invalid_path.write_text(json.dumps(invalid), encoding="utf-8")
    command = [sys.executable, "-m", "hsr_axis_sim.tools.trace_tingyun_ultimate_damage_buff_semantic_readiness", "--format", "json", "--review", str(invalid_path)]
    failed = subprocess.run(command, cwd=ROOT.parent, text=True, capture_output=True, check=False)
    assert failed.returncode == 1
    assert "FAIL Tingyun semantic readiness validation" in failed.stderr
    assert "Traceback" not in failed.stderr


def test_cli_missing_input_returns_exit_2_without_traceback(tmp_path):
    invalid = review_data()
    invalid["generic_binding_readiness"] = "ready_for_separate_binding_task"
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text(json.dumps(invalid), encoding="utf-8")
    base = [sys.executable, "-m", "hsr_axis_sim.tools.trace_tingyun_ultimate_damage_buff_semantic_readiness", "--format", "json", "--review"]
    failed = subprocess.run(base + [str(invalid_path)], cwd=ROOT.parent, text=True, capture_output=True, check=False)
    missing = subprocess.run(base + [str(tmp_path / "missing.json")], cwd=ROOT.parent, text=True, capture_output=True, check=False)
    assert failed.returncode == 1 and "Traceback" not in failed.stderr
    assert missing.returncode == 2 and "Traceback" not in missing.stderr
