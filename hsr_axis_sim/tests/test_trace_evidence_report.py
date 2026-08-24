import copy
import json
import subprocess
import sys
from pathlib import Path

from hsr_axis_sim.tools.trace_evidence_report import (
    build_trace_evidence_report,
    load_json,
    render_json,
    render_markdown,
)


ROOT = Path(__file__).resolve().parents[1]
TRACE_PATH = ROOT / "data" / "manual_video_traces" / "intake" / "real_video_trace_001_botu_dilemma_floor12_side1_action_sequence_only.json"
SEMANTIC_PATH = ROOT / "data" / "manual_video_traces" / "semantic_maps" / "real_video_trace_001_botu_dilemma_semantics_v0_1.json"
ANCHOR_PATH = ROOT / "data" / "manual_video_traces" / "frame_anchors" / "real_video_trace_001_botu_dilemma_frame_anchors_v0_1.json"
REPORTS = ROOT / "data" / "manual_video_traces" / "reports"


def valid_inputs():
    return load_json(TRACE_PATH), load_json(SEMANTIC_PATH), load_json(ANCHOR_PATH)


def test_report_builds_source_ordered_evidence_and_preserves_unknowns():
    trace, semantic, anchors = valid_inputs()
    report = build_trace_evidence_report(trace, semantic, anchors)

    assert len(report.prebattle) == 1
    assert len(report.steps) == 9
    assert [(step.step, step.actor, step.action) for step in report.steps] == [
        (item["step"], item["actor"], item["action"]) for item in trace["steps"]
    ]
    assert report.steps[0].target == "unknown"
    assert report.steps[0].target_confidence == "unknown"
    assert report.steps[7].target == "naxia"
    assert report.steps[0].media_evidence.time_start_seconds == 2.0
    assert report.steps[0].media_evidence.representative_frames[0] == "t_002.0.jpg"


def test_renderers_are_deterministic_and_label_media_evidence():
    report = build_trace_evidence_report(*valid_inputs())
    markdown = render_markdown(report)
    rendered_json = render_json(report)

    assert markdown == render_markdown(report)
    assert rendered_json == render_json(report)
    assert "停云终结技" in markdown
    assert "Evidence-only and non-executable" in markdown
    assert "not AV or simulator time" in markdown
    payload = json.loads(rendered_json)
    assert "media_evidence" in payload["steps"][0]
    assert "action_value" not in rendered_json


def test_report_is_independent_of_semantic_and_anchor_list_order():
    trace, semantic, anchors = valid_inputs()
    expected = render_json(build_trace_evidence_report(trace, semantic, anchors))
    semantic["steps"].reverse()
    anchors["steps"].reverse()

    assert render_json(build_trace_evidence_report(trace, semantic, anchors)) == expected


def test_missing_semantic_mapping_is_rejected():
    trace, semantic, anchors = valid_inputs()
    semantic["steps"] = semantic["steps"][:-1]
    try:
        build_trace_evidence_report(trace, semantic, anchors)
    except ValueError as exc:
        assert "exactly one" in str(exc)
    else:
        raise AssertionError("Expected missing semantic mapping failure.")


def test_missing_frame_anchor_is_rejected():
    trace, semantic, anchors = valid_inputs()
    anchors["steps"] = anchors["steps"][:-1]
    try:
        build_trace_evidence_report(trace, semantic, anchors)
    except ValueError as exc:
        assert "exactly one" in str(exc)
    else:
        raise AssertionError("Expected missing frame anchor failure.")


def test_mismatched_evidence_and_source_trace_are_rejected():
    trace, semantic, anchors = valid_inputs()
    semantic["steps"][0]["actor"] = "pela"
    try:
        build_trace_evidence_report(trace, semantic, anchors)
    except ValueError as exc:
        assert "exactly one" in str(exc)
    else:
        raise AssertionError("Expected semantic actor mismatch failure.")

    trace, semantic, anchors = valid_inputs()
    anchors["source_trace"] = "other_trace"
    try:
        build_trace_evidence_report(trace, semantic, anchors)
    except ValueError as exc:
        assert "source_trace" in str(exc)
    else:
        raise AssertionError("Expected source trace mismatch failure.")


def test_cli_stdout_output_and_committed_samples_match_generated(tmp_path):
    command = [
        sys.executable, "-m", "hsr_axis_sim.tools.trace_evidence_report",
        "--trace", str(TRACE_PATH), "--semantic-map", str(SEMANTIC_PATH),
        "--frame-anchors", str(ANCHOR_PATH),
    ]
    markdown = subprocess.run(command + ["--format", "markdown"], check=False, capture_output=True, text=True)
    json_result = subprocess.run(command + ["--format", "json"], check=False, capture_output=True, text=True)
    output_path = tmp_path / "report.json"
    written = subprocess.run(command + ["--format", "json", "--output", str(output_path)], check=False, capture_output=True, text=True)

    assert markdown.returncode == json_result.returncode == written.returncode == 0
    assert output_path.read_text(encoding="utf-8") == json_result.stdout
    assert (REPORTS / "real_video_trace_001_botu_dilemma_evidence_report_v0_1.md").read_text(encoding="utf-8") == markdown.stdout
    assert (REPORTS / "real_video_trace_001_botu_dilemma_evidence_report_v0_1.json").read_text(encoding="utf-8") == json_result.stdout
