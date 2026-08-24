import copy
import inspect
import json
import subprocess
import sys
from pathlib import Path

from hsr_axis_sim.tools.trace_character_source_registry import (
    build_source_registry_report,
    load_json,
    render_json,
    render_markdown,
)


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "manual_video_traces"
EVIDENCE = BASE / "reports" / "real_video_trace_001_botu_dilemma_evidence_report_v0_1.json"
GAPS = BASE / "binding_inventories" / "real_video_trace_001_botu_dilemma_binding_gap_inventory_v0_1.json"
SOURCES = BASE / "source_registry" / "sources_v0_1.json"
FACTS = BASE / "source_registry" / "real_video_trace_001_required_facts_v0_1.json"
REPORTS = BASE / "source_registry" / "reports"


def valid_inputs():
    return load_json(EVIDENCE), load_json(GAPS), load_json(SOURCES), load_json(FACTS)


def expect_error(inputs, text):
    try:
        build_source_registry_report(*inputs)
    except ValueError as exc:
        assert text in str(exc)
    else:
        raise AssertionError("Expected source-registry validation failure.")


def test_exact_trace_coverage_and_compatibility_identities():
    report = build_source_registry_report(*valid_inputs())

    assert len(report.coverage) == 10
    assert [(item["actor"], item["action"]) for item in report.coverage] == [
        ("pela", "technique"), ("tingyun", "ultimate"), ("pela", "skill"),
        ("remembrance_trailblazer", "skill"), ("tingyun", "skill"),
        ("pela", "ultimate"), ("naxia", "ultimate"),
        ("naxia", "basic_plus_extra_skill"), ("mem", "advance_naxia"),
        ("naxia", "skill_plus_extra_skill"),
    ]
    identities = {item.internal_actor_id: item for item in report.identities}
    assert identities["naxia"].canonical_english_name == "Anaxa"
    assert identities["naxia"].canonical_chinese_name == "那刻夏"
    assert identities["naxia"].character_game_data_id == "1405"


def test_unresolved_facts_and_binding_boundary_are_preserved():
    report = build_source_registry_report(*valid_inputs())

    missing = [fact for fact in report.facts if fact.verification_status == "missing"]
    assert missing and all(fact.value is None for fact in missing)
    assert all(fact.simulator_binding_allowed is False for fact in report.facts)
    assert all(item["simulator_binding_allowed"] is False for item in report.coverage)


def test_duplicate_ids_statuses_and_dangling_sources_are_rejected():
    inputs = list(valid_inputs())
    inputs[2]["sources"].append(copy.deepcopy(inputs[2]["sources"][0]))
    expect_error(inputs, "Duplicate source IDs")

    inputs = list(valid_inputs())
    inputs[3]["facts"].append(copy.deepcopy(inputs[3]["facts"][0]))
    expect_error(inputs, "Duplicate fact IDs")

    inputs = list(valid_inputs())
    inputs[2]["sources"][0]["source_type"] = "wiki"
    expect_error(inputs, "source_type is unsupported")

    inputs = list(valid_inputs())
    inputs[3]["facts"][0]["verification_status"] = "certain"
    expect_error(inputs, "verification_status is unsupported")

    inputs = list(valid_inputs())
    inputs[3]["facts"][0]["provenance"][0]["source_id"] = "missing_source"
    expect_error(inputs, "unknown source")


def test_locator_and_verification_qualification_rules_are_enforced():
    inputs = list(valid_inputs())
    inputs[2]["sources"][1]["locator"] = "not-a-url"
    expect_error(inputs, "locator is malformed")

    inputs = list(valid_inputs())
    fact = inputs[3]["facts"][0]
    fact["verification_status"] = "verified_official"
    expect_error(inputs, "lacks a qualifying source")

    inputs = list(valid_inputs())
    fact = inputs[3]["facts"][0]
    fact["verification_status"] = "conflicting"
    expect_error(inputs, "requires two conflicting")


def test_missing_binding_and_executable_schema_rules_are_enforced():
    inputs = list(valid_inputs())
    missing = next(fact for fact in inputs[3]["facts"] if fact["verification_status"] == "missing")
    missing["value"] = "guessed"
    expect_error(inputs, "must have value null")

    inputs = list(valid_inputs())
    inputs[3]["facts"][0]["simulator_binding_allowed"] = True
    expect_error(inputs, "must be false")

    inputs = list(valid_inputs())
    inputs[3]["CharacterSpec"] = {}
    expect_error(inputs, "executable schema key")


def test_output_is_order_independent_and_deterministic():
    inputs = list(valid_inputs())
    expected_json = render_json(build_source_registry_report(*inputs))
    expected_markdown = render_markdown(build_source_registry_report(*inputs))
    inputs[2]["sources"].reverse()
    inputs[3]["facts"].reverse()
    inputs[3]["identities"].reverse()
    report = build_source_registry_report(*inputs)

    assert render_json(report) == expected_json
    assert render_markdown(report) == expected_markdown
    assert "Non-executable source registry only" in expected_markdown


def test_committed_outputs_and_cli_stdout_file_output(tmp_path):
    report = build_source_registry_report(*valid_inputs())
    markdown = render_markdown(report)
    rendered_json = render_json(report)
    assert (REPORTS / "real_video_trace_001_character_source_registry_v0_1.md").read_text(encoding="utf-8") == markdown
    assert (REPORTS / "real_video_trace_001_character_source_registry_v0_1.json").read_text(encoding="utf-8") == rendered_json

    command = [sys.executable, "-m", "hsr_axis_sim.tools.trace_character_source_registry", "--evidence-report", str(EVIDENCE), "--gap-inventory", str(GAPS), "--sources", str(SOURCES), "--facts", str(FACTS)]
    stdout = subprocess.run(command + ["--format", "markdown"], check=False, capture_output=True, text=True)
    output = tmp_path / "registry.json"
    written = subprocess.run(command + ["--format", "json", "--output", str(output)], check=False, capture_output=True, text=True)
    assert stdout.returncode == written.returncode == 0
    assert stdout.stdout == markdown
    assert output.read_text(encoding="utf-8") == rendered_json


def test_cli_exit_one_and_two(tmp_path):
    inputs = valid_inputs()
    invalid_facts = tmp_path / "invalid_facts.json"
    bad = copy.deepcopy(inputs[3])
    bad["facts"][0]["simulator_binding_allowed"] = True
    invalid_facts.write_text(json.dumps(bad), encoding="utf-8")
    command = [sys.executable, "-m", "hsr_axis_sim.tools.trace_character_source_registry", "--evidence-report", str(EVIDENCE), "--gap-inventory", str(GAPS), "--sources", str(SOURCES)]
    invalid = subprocess.run(command + ["--facts", str(invalid_facts), "--format", "json"], check=False, capture_output=True, text=True)
    unreadable = subprocess.run(command + ["--facts", str(tmp_path / "missing.json"), "--format", "json"], check=False, capture_output=True, text=True)
    assert invalid.returncode == 1
    assert unreadable.returncode == 2
    assert "Traceback" not in invalid.stderr + unreadable.stderr
