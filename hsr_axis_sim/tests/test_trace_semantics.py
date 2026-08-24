import copy
import json
import subprocess
import sys
from pathlib import Path

from hsr_axis_sim.tools.trace_semantics import load_json, validate_semantic_map


ROOT = Path(__file__).resolve().parents[1]
TRACE_PATH = (
    ROOT
    / "data"
    / "manual_video_traces"
    / "intake"
    / "real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only.json"
)
SEMANTIC_MAP_PATH = (
    ROOT
    / "data"
    / "manual_video_traces"
    / "semantic_maps"
    / "real_video_trace_001_botu_dilemma_semantics_v0_1.json"
)


def load_valid_pair():
    return load_json(TRACE_PATH), load_json(SEMANTIC_MAP_PATH)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_valid_botu_semantic_map_passes():
    trace, semantic_map = load_valid_pair()

    assert validate_semantic_map(trace, semantic_map) == []


def test_semantic_map_missing_step_mapping_fails():
    trace, semantic_map = load_valid_pair()
    semantic_map["steps"] = semantic_map["steps"][:-1]

    issues = validate_semantic_map(trace, semantic_map)

    assert any("exactly one mapping" in issue for issue in issues)
    assert any("skill_plus_extra_skill" in issue for issue in issues)


def test_semantic_map_mismatched_source_trace_fails():
    trace, semantic_map = load_valid_pair()
    semantic_map["source_trace"] = "wrong_trace_name"

    issues = validate_semantic_map(trace, semantic_map)

    assert any("source_trace" in issue for issue in issues)


def test_semantic_map_numeric_claim_fails_when_not_allowed():
    trace, semantic_map = load_valid_pair()
    semantic_map["steps"][0]["known"].append("Tingyun restores 50 energy.")

    issues = validate_semantic_map(trace, semantic_map)

    assert any("numeric claim" in issue for issue in issues)


def test_semantic_map_extra_numeric_value_fails_when_not_allowed():
    trace, semantic_map = load_valid_pair()
    semantic_map["steps"][0]["energy_value"] = 50

    issues = validate_semantic_map(trace, semantic_map)

    assert any("numeric value" in issue for issue in issues)


def test_trace_semantics_cli_returns_zero_for_valid_fixture():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "hsr_axis_sim.tools.trace_semantics",
            "--trace",
            str(TRACE_PATH),
            "--semantic-map",
            str(SEMANTIC_MAP_PATH),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "PASS semantic map validation passed." in result.stdout


def test_trace_semantics_cli_returns_nonzero_for_invalid_fixture(tmp_path):
    trace, semantic_map = load_valid_pair()
    invalid_map = copy.deepcopy(semantic_map)
    invalid_map["steps"] = invalid_map["steps"][:-1]
    invalid_path = tmp_path / "invalid_semantic_map.json"
    write_json(invalid_path, invalid_map)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "hsr_axis_sim.tools.trace_semantics",
            "--trace",
            str(TRACE_PATH),
            "--semantic-map",
            str(invalid_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "FAIL semantic map validation found" in result.stdout
