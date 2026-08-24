import copy
import json
import math
import subprocess
import sys
from pathlib import Path

from hsr_axis_sim.real_bindings.pela_skill_v0_1 import DEFAULT_FIXTURE as PELA_FIXTURE, build_fixture_state as build_pela_state, load_json as load_binding_json
from hsr_axis_sim.real_bindings.registry import execute_reviewed_binding, load_reviewed_binding_registry
from hsr_axis_sim.real_bindings.tingyun_ultimate_v0_1 import DEFAULT_FIXTURE as TINGYUN_FIXTURE, build_fixture_state as build_tingyun_state
from hsr_axis_sim.tools.trace_tingyun_ultimate_damage_buff_magnitude import (
    DEFAULT_INTAKE,
    build_report,
    load_json,
    render_json,
    render_markdown,
)


BASE = Path(__file__).resolve().parents[1]
REPORTS = BASE / "data" / "manual_video_traces" / "real_binding_audits"
RATIOS = [0.20, 0.23, 0.26, 0.29, 0.32, 0.35, 0.3875, 0.425, 0.4625, 0.50, 0.53, 0.56, 0.59, 0.62, 0.65]
PERCENTS = [20, 23, 26, 29, 32, 35, 38.75, 42.5, 46.25, 50, 53, 56, 59, 62, 65]


def captured_fixture():
    source_template = {
        "title": "Synthetic exact table source",
        "locator": "https://example.test/source",
        "source_type": "structured_game_database",
        "language": "en",
        "game_version": "release snapshot",
        "retrieval_date": "2026-07-12",
        "exact_field_locator": "AvatarSkillConfig[1202].Ultimate.Parameters[1]",
        "support_level": "supports_exact_field",
        "level_mapping_basis": "Source raw level index explicitly equals trace level for rows 1-15.",
        "repository": "synthetic/repository",
        "commit": "0123456789abcdef0123456789abcdef01234567",
        "path": "data/tingyun.json",
        "snapshot_qualification": "Synthetic test-only snapshot, not game evidence.",
    }
    sources = []
    raw_tables = []
    for source_id in ("synthetic_a", "synthetic_b"):
        source = copy.deepcopy(source_template)
        source["source_id"] = source_id
        source["locator"] = f"https://example.test/{source_id}"
        sources.append(source)
        raw_tables.append({
            "source_id": source_id,
            "unit": "ratio",
            "rows": [
                {"raw_level_index": level, "dmg_increase_ratio": ratio}
                for level, ratio in enumerate(RATIOS, start=1)
            ] + [{"raw_level_index": 16, "dmg_increase_ratio": 0.68}],
        })
    normalized = [
        {
            "normalized_trace_level": level,
            "dmg_increase_percent": amount,
            "unit": "percent",
            "raw_source_rows": [
                {"source_id": source_id, "raw_level_index": level}
                for source_id in ("synthetic_a", "synthetic_b")
            ],
        }
        for level, amount in enumerate(PERCENTS, start=1)
    ]
    return {
        "intake_id": "synthetic_test_only",
        "version": "0.1",
        "intake_status": "captured_exact_table",
        "fact_id": "tingyun.ultimate.damage_buff.magnitude_by_trace_level",
        "accepted_sources": sources,
        "context_sources": [],
        "raw_tables": raw_tables,
        "normalized_table": normalized,
        "acquisition_attempts": [],
        "blocked_reasons": [],
        "real_video_trace_level": None,
        "preserved_unresolved_fields": [
            "real_video_trace_level",
            "real_video_selected_ally",
            "damage_buff_application_order_relative_to_energy_restore",
            "same_current_turn_duration_behavior",
        ],
        "readiness_status": "blocked_by_both",
        "simulator_binding_allowed": False,
    }


def expect_error(data, text):
    try:
        build_report(data)
    except ValueError as exc:
        assert text in str(exc)
    else:
        raise AssertionError("Expected magnitude intake validation failure")


def test_valid_exact_table_ingestion_preserves_raw_extra_rows():
    report = build_report(captured_fixture())
    assert report.intake_status == "captured_exact_table"
    assert [row["normalized_trace_level"] for row in report.normalized_table] == list(range(1, 16))
    assert [row["raw_level_index"] for row in report.raw_tables[0]["rows"]] == list(range(1, 17))
    assert report.real_video_trace_level is None
    assert report.readiness_status == "blocked_by_both"
    assert report.simulator_binding_allowed is False


def test_committed_captured_intake_and_reports_are_deterministic():
    data = load_json(DEFAULT_INTAKE)
    report = build_report(data)
    assert report.intake_status == "captured_exact_table"
    assert [row["dmg_increase_percent"] for row in report.normalized_table] == PERCENTS
    assert {source["source_id"] for source in report.accepted_sources} == {
        "mar7th_starrailres_v4_3_commit_7b349e39",
        "kqm_srl_commit_de0e5c09",
    }
    assert {(source["repository"], source["commit"], source["path"]) for source in report.accepted_sources} == {
        ("Mar-7th/StarRailRes", "7b349e39ee0f6f3bf814567995829b99c95e7a93", "index_new/en/character_skills.json"),
        ("KQM-git/SRL", "de0e5c09c8dbba9577367ad86e991fe91c4f0e36", "src/data/characters/Tingyun.json"),
    }
    assert all(table["unit"] == "ratio" and [row["dmg_increase_ratio"] for row in table["rows"]] == RATIOS for table in report.raw_tables)
    assert len(report.accepted_sources) == 2
    assert len(report.context_sources) == 1
    assert render_markdown(report) == (REPORTS / "tingyun_ultimate_damage_buff_magnitude_intake_v0_1.md").read_text(encoding="utf-8")
    assert render_json(report) == (REPORTS / "tingyun_ultimate_damage_buff_magnitude_intake_v0_1.json").read_text(encoding="utf-8")
    data["acquisition_attempts"].reverse()
    data["blocked_reasons"].reverse()
    data["accepted_sources"].reverse()
    data["context_sources"].reverse()
    data["raw_tables"].reverse()
    data["normalized_table"].reverse()
    assert render_json(build_report(data)) == render_json(report)


def test_captured_table_order_is_deterministic():
    data = captured_fixture()
    expected = render_json(build_report(data))
    data["accepted_sources"].reverse()
    data["raw_tables"].reverse()
    data["normalized_table"].reverse()
    for table in data["raw_tables"]:
        table["rows"].reverse()
    for row in data["normalized_table"]:
        row["raw_source_rows"].reverse()
    assert render_json(build_report(data)) == expected


def test_duplicate_levels_and_source_ids_rejected():
    data = captured_fixture()
    data["raw_tables"][0]["rows"].append(copy.deepcopy(data["raw_tables"][0]["rows"][0]))
    expect_error(data, "duplicate levels")
    data = captured_fixture()
    data["normalized_table"].append(copy.deepcopy(data["normalized_table"][0]))
    expect_error(data, "duplicate levels")
    data = captured_fixture()
    data["accepted_sources"][1]["source_id"] = data["accepted_sources"][0]["source_id"]
    expect_error(data, "duplicate source ID")
    data = captured_fixture()
    data["raw_tables"][1]["rows"][9]["dmg_increase_ratio"] = 0.51
    expect_error(data, "magnitude conflicts")


def test_source_ids_and_exact_locators_require_strings():
    for field in ("source_id", "locator", "exact_field_locator"):
        for value in ({"bad": 1}, ["bad"]):
            data = captured_fixture()
            data["accepted_sources"][0][field] = value
            expect_error(data, field)


def test_numeric_fields_reject_json_nonnumbers_booleans_nan_and_infinity():
    for value in ({"bad": 1}, [1], True, None, math.nan, math.inf, -math.inf):
        data = captured_fixture()
        data["raw_tables"][0]["rows"][0]["dmg_increase_ratio"] = value
        expect_error(data, "finite nonnegative number")
    for value in ({"bad": 1}, [1], True, None):
        data = captured_fixture()
        data["normalized_table"][0]["normalized_trace_level"] = value
        expect_error(data, "positive integer")


def test_executable_schema_and_real_video_inference_rejected():
    data = captured_fixture()
    data["effects"] = []
    expect_error(data, "executable schema")
    data = captured_fixture()
    data["real_video_trace_level"] = 10
    expect_error(data, "must remain null")
    data = captured_fixture()
    data["simulator_binding_allowed"] = True
    expect_error(data, "must be false")


def test_cli_exit_codes_and_output(tmp_path):
    command = [sys.executable, "-m", "hsr_axis_sim.tools.trace_tingyun_ultimate_damage_buff_magnitude"]
    markdown = subprocess.run(command + ["--format", "markdown"], capture_output=True, text=True)
    output = tmp_path / "out.json"
    written = subprocess.run(command + ["--format", "json", "--output", str(output)], capture_output=True, text=True)
    malformed = captured_fixture()
    malformed["raw_tables"][0]["rows"][0]["dmg_increase_ratio"] = True
    malformed_path = tmp_path / "malformed.json"
    malformed_path.write_text(json.dumps(malformed), encoding="utf-8")
    invalid = subprocess.run(command + ["--intake", str(malformed_path), "--format", "json"], capture_output=True, text=True)
    missing = subprocess.run(command + ["--intake", str(tmp_path / "missing.json"), "--format", "json"], capture_output=True, text=True)
    assert markdown.returncode == written.returncode == 0
    assert invalid.returncode == 1 and missing.returncode == 2
    assert "Traceback" not in invalid.stderr + missing.stderr
    assert output.read_text(encoding="utf-8") == (REPORTS / "tingyun_ultimate_damage_buff_magnitude_intake_v0_1.json").read_text(encoding="utf-8")


def test_reviewed_bindings_remain_exactly_two_and_execute_unchanged():
    registry = load_reviewed_binding_registry()
    assert len(registry.bindings) == 2
    tingyun = build_tingyun_state(load_binding_json(TINGYUN_FIXTURE))
    context, _ = execute_reviewed_binding("tingyun_ultimate_partial_resource_interrupt_shell_v0_1", tingyun, ["ally"], registry=registry)
    assert (tingyun.get_unit("tingyun").energy, tingyun.get_unit("ally").energy) == (0, 90)
    assert context.is_interrupt and context.should_end_turn is False
    pela = build_pela_state(load_binding_json(PELA_FIXTURE))
    context, removed = execute_reviewed_binding("pela_skill_partial_resource_target_dispel_shell_v0_1", pela, ["enemy"], registry=registry)
    assert removed == "alpha_guard"
    assert (pela.skill_points, pela.get_unit("pela").energy, context.should_end_turn) == (2, 40, True)
