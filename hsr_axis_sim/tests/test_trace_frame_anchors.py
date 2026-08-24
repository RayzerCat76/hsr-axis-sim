import copy
import json
import subprocess
import sys
from pathlib import Path

from hsr_axis_sim.tools.trace_frame_anchors import load_json, validate_frame_anchors


ROOT = Path(__file__).resolve().parents[1]
TRACE_PATH = ROOT / "data" / "manual_video_traces" / "intake" / "real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only.json"
ANCHOR_PATH = ROOT / "data" / "manual_video_traces" / "frame_anchors" / "real_video_trace_001_botu_dilemma_frame_anchors_v0_1.json"


def load_valid_pair():
    return load_json(TRACE_PATH), load_json(ANCHOR_PATH)


def test_valid_botu_frame_anchors_pass():
    trace, anchors = load_valid_pair()
    assert validate_frame_anchors(trace, anchors) == []


def test_missing_step_anchor_fails():
    trace, anchors = load_valid_pair()
    anchors["steps"] = anchors["steps"][:-1]
    assert any("exactly one anchor" in issue for issue in validate_frame_anchors(trace, anchors))


def test_source_trace_mismatch_fails():
    trace, anchors = load_valid_pair()
    anchors["source_trace"] = "wrong_trace_name"
    assert any("source_trace" in issue for issue in validate_frame_anchors(trace, anchors))


def test_actor_action_mismatch_fails():
    trace, anchors = load_valid_pair()
    anchors["steps"][0]["actor"] = "pela"
    issues = validate_frame_anchors(trace, anchors)
    assert any("exactly one anchor" in issue for issue in issues)
    assert any("extra anchor" in issue for issue in issues)


def test_reversed_timestamp_interval_fails():
    trace, anchors = load_valid_pair()
    anchors["steps"][0]["time_start_seconds"] = 6.0
    anchors["steps"][0]["time_end_seconds"] = 5.5
    assert any("less than or equal" in issue for issue in validate_frame_anchors(trace, anchors))


def test_decreasing_step_order_fails():
    trace, anchors = load_valid_pair()
    anchors["steps"][1]["time_start_seconds"] = 1.0
    assert any("nondecreasing" in issue for issue in validate_frame_anchors(trace, anchors))


def test_invalid_frame_filename_fails():
    trace, anchors = load_valid_pair()
    anchors["steps"][0]["representative_frames"][0] = "frame.txt"
    assert any("image filename" in issue for issue in validate_frame_anchors(trace, anchors))


def test_invalid_confidence_fails():
    trace, anchors = load_valid_pair()
    anchors["steps"][0]["confidence"] = "certain"
    assert any("confidence" in issue for issue in validate_frame_anchors(trace, anchors))


def test_forbidden_combat_state_field_fails():
    trace, anchors = load_valid_pair()
    anchors["steps"][0]["energy"] = 50
    assert any("forbidden combat-state field" in issue for issue in validate_frame_anchors(trace, anchors))


def test_wrong_status_fails():
    trace, anchors = load_valid_pair()
    anchors["status"] = "executable"
    assert any("status" in issue for issue in validate_frame_anchors(trace, anchors))


def test_wrong_timestamp_basis_fails():
    trace, anchors = load_valid_pair()
    anchors["timestamp_basis"] = "simulator_time"
    assert any("timestamp_basis" in issue for issue in validate_frame_anchors(trace, anchors))


def test_empty_or_non_string_frame_anchor_id_fails():
    trace, anchors = load_valid_pair()
    anchors["frame_anchor_id"] = ""
    assert any("frame_anchor_id" in issue for issue in validate_frame_anchors(trace, anchors))
    anchors["frame_anchor_id"] = 1
    assert any("frame_anchor_id" in issue for issue in validate_frame_anchors(trace, anchors))


def test_empty_or_non_string_version_fails():
    trace, anchors = load_valid_pair()
    anchors["version"] = ""
    assert any("version" in issue for issue in validate_frame_anchors(trace, anchors))
    anchors["version"] = 1
    assert any("version" in issue for issue in validate_frame_anchors(trace, anchors))


def test_frame_anchor_cli_returns_zero_for_valid_fixture():
    result = subprocess.run([sys.executable, "-m", "hsr_axis_sim.tools.trace_frame_anchors", "--trace", str(TRACE_PATH), "--anchors", str(ANCHOR_PATH)], check=False, capture_output=True, text=True)
    assert result.returncode == 0
    assert "PASS frame anchor validation passed." in result.stdout


def test_frame_anchor_cli_returns_nonzero_for_invalid_fixture(tmp_path):
    trace, anchors = load_valid_pair()
    invalid_path = tmp_path / "invalid_frame_anchors.json"
    invalid = copy.deepcopy(anchors)
    invalid["steps"] = invalid["steps"][:-1]
    invalid_path.write_text(json.dumps(invalid, indent=2), encoding="utf-8")
    result = subprocess.run([sys.executable, "-m", "hsr_axis_sim.tools.trace_frame_anchors", "--trace", str(TRACE_PATH), "--anchors", str(invalid_path)], check=False, capture_output=True, text=True)
    assert result.returncode == 1
    assert "FAIL frame anchor validation found" in result.stdout
