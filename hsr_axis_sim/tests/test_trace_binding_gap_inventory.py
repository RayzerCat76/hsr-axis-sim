import copy
import inspect
import json
import subprocess
import sys
from pathlib import Path

from hsr_axis_sim.tools.trace_binding_gap_inventory import (
    build_binding_gap_inventory,
    load_json,
    render_json,
    render_markdown,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "data" / "manual_video_traces" / "reports" / "real_video_trace_001_botu_dilemma_evidence_report_v0_1.json"
ASSESSMENT_PATH = ROOT / "data" / "manual_video_traces" / "binding_assessments" / "real_video_trace_001_botu_dilemma_binding_assessment_v0_1.json"
INVENTORIES = ROOT / "data" / "manual_video_traces" / "binding_inventories"
EVIDENCE_ARGUMENT = (
    "hsr_axis_sim/data/manual_video_traces/reports/"
    "real_video_trace_001_botu_dilemma_evidence_report_v0_1.json"
)
ASSESSMENT_ARGUMENT = (
    "hsr_axis_sim/data/manual_video_traces/binding_assessments/"
    "real_video_trace_001_botu_dilemma_binding_assessment_v0_1.json"
)


def valid_inputs():
    return load_json(EVIDENCE_PATH), load_json(ASSESSMENT_PATH)


def expect_validation_error(evidence, assessment, text):
    try:
        build_binding_gap_inventory(evidence, assessment)
    except ValueError as exc:
        assert text in str(exc)
    else:
        raise AssertionError("Expected binding inventory validation failure.")


def test_inventory_preserves_evidence_order_and_is_non_executable():
    evidence, assessment = valid_inputs()
    inventory = build_binding_gap_inventory(evidence, assessment)

    assert len(inventory.prebattle) == 1
    assert len(inventory.steps) == 9
    assert [(item.step, item.actor, item.action) for item in inventory.steps] == [
        (item["step"], item["actor"], item["action"]) for item in evidence["steps"]
    ]
    assert all(item.executable_now is False for item in [*inventory.prebattle, *inventory.steps])
    assert "Initial SP, energy, speed/AV" in inventory.global_blockers[0]


def test_generic_primitives_do_not_create_character_bindings():
    inventory = build_binding_gap_inventory(*valid_inputs())
    tingyun_ultimate = inventory.steps[0]

    assert "ultimate interrupt windows" in tingyun_ultimate.generic_primitives
    assert tingyun_ultimate.missing_character_kit_semantics
    assert tingyun_ultimate.target_status == "unknown target"
    assert tingyun_ultimate.executable_now is False


def test_composites_and_mem_advance_remain_unresolved_without_numeric_claims():
    inventory = build_binding_gap_inventory(*valid_inputs())
    composite = inventory.steps[6]
    mem = inventory.steps[7]

    assert "unresolved_composite_action" in composite.binding_statuses
    assert "no executable split" in composite.unresolved_behavior[0]
    assert "unresolved_action_advance" in mem.binding_statuses
    assert "exact amount" in mem.unresolved_behavior[0]
    assert "advance_percent" not in render_json(inventory)
    assert "immediate-action claim" in mem.evidence_limitations[0]


def test_assessment_order_does_not_change_output():
    evidence, assessment = valid_inputs()
    expected = render_json(build_binding_gap_inventory(evidence, assessment))
    assessment["steps"].reverse()
    assessment["prebattle"].reverse()

    assert render_json(build_binding_gap_inventory(evidence, assessment)) == expected


def test_missing_duplicate_and_mismatched_assessments_are_rejected():
    evidence, assessment = valid_inputs()
    assessment["steps"] = assessment["steps"][:-1]
    expect_validation_error(evidence, assessment, "exactly one")

    evidence, assessment = valid_inputs()
    assessment["steps"].append(copy.deepcopy(assessment["steps"][0]))
    expect_validation_error(evidence, assessment, "exactly one")

    evidence, assessment = valid_inputs()
    assessment["steps"][0]["actor"] = "pela"
    expect_validation_error(evidence, assessment, "extra assessment")


def test_wrong_source_status_and_executable_claim_are_rejected():
    evidence, assessment = valid_inputs()
    assessment["source_evidence_report_id"] = "wrong_report"
    expect_validation_error(evidence, assessment, "source_evidence_report_id")

    evidence, assessment = valid_inputs()
    assessment["steps"][0]["binding_statuses"] = ["not_supported"]
    expect_validation_error(evidence, assessment, "unsupported status")

    evidence, assessment = valid_inputs()
    assessment["steps"][0]["executable_now"] = True
    expect_validation_error(evidence, assessment, "cannot be true")


def test_renderers_cli_and_committed_samples_are_deterministic(tmp_path):
    inventory = build_binding_gap_inventory(
        *valid_inputs(),
        source_evidence_report_path=EVIDENCE_ARGUMENT,
    )
    markdown = render_markdown(inventory)
    rendered_json = render_json(inventory)

    assert markdown == render_markdown(inventory)
    assert rendered_json == render_json(inventory)
    assert "Planning inventory only, not an executable replay" in markdown
    assert "Deduplicated Minimum Future Work" in markdown
    assert (INVENTORIES / "real_video_trace_001_botu_dilemma_binding_gap_inventory_v0_1.md").read_text(encoding="utf-8") == markdown
    assert (INVENTORIES / "real_video_trace_001_botu_dilemma_binding_gap_inventory_v0_1.json").read_text(encoding="utf-8") == rendered_json

    command = [
        sys.executable, "-m", "hsr_axis_sim.tools.trace_binding_gap_inventory",
        "--evidence-report", EVIDENCE_ARGUMENT, "--assessment", ASSESSMENT_ARGUMENT,
    ]
    stdout = subprocess.run(command + ["--format", "markdown"], check=False, capture_output=True, text=True)
    output_path = tmp_path / "inventory.json"
    written = subprocess.run(command + ["--format", "json", "--output", str(output_path)], check=False, capture_output=True, text=True)
    assert stdout.returncode == written.returncode == 0
    assert stdout.stdout == markdown
    assert output_path.read_text(encoding="utf-8") == rendered_json
