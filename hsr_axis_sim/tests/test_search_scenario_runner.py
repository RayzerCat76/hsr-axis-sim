import contextlib
import io
import json
from pathlib import Path

import pytest

from hsr_axis_sim.search import SearchReport
from hsr_axis_sim.search.scenario import (
    load_search_scenario,
    main,
    render_search_scenario_report,
    run_search_scenario,
)


SCENARIO_PATH = Path("hsr_axis_sim/data/search_scenarios/basic_search_mvp.json")
CONSTRAINED_SCENARIO_PATH = Path("hsr_axis_sim/data/search_scenarios/constrained_search_mvp.json")


def test_scenario_json_loads_and_resolves_relative_paths():
    scenario = load_search_scenario(SCENARIO_PATH)

    assert scenario.id == "basic_search_mvp"
    assert scenario.characters_dir.is_absolute()
    assert scenario.team_path.is_absolute()
    assert scenario.characters_dir.name == "sample_characters"
    assert scenario.team_path.name == "bronya_seele_team.json"


def test_scenario_config_parses_constraints():
    scenario = load_search_scenario(CONSTRAINED_SCENARIO_PATH)

    assert scenario.constraints is not None
    assert scenario.constraints.allowed_actor_ids == {"seele_like", "bronya_like"}
    assert scenario.constraints.disabled_target_ids == {"enemy_2"}
    assert scenario.constraints.max_choices_per_node == 4


def test_run_search_scenario_returns_report_with_axis_or_terminal_reason():
    scenario = load_search_scenario(SCENARIO_PATH)

    report = run_search_scenario(scenario)

    assert isinstance(report, SearchReport)
    assert report.best_axis_steps or report.best_terminal_reason is not None


def test_markdown_rendering_contains_report_title():
    report = run_search_scenario(load_search_scenario(SCENARIO_PATH))

    rendered = render_search_scenario_report(report, "markdown")

    assert "# HSR Axis Search Report" in rendered


def test_text_rendering_contains_report_title():
    report = run_search_scenario(load_search_scenario(SCENARIO_PATH))

    rendered = render_search_scenario_report(report, "text")

    assert "HSR Axis Search Report" in rendered


def test_json_rendering_is_valid_and_contains_best_axis_steps():
    report = run_search_scenario(load_search_scenario(SCENARIO_PATH))

    rendered = render_search_scenario_report(report, "json")
    payload = json.loads(rendered)

    assert "best_axis_steps" in payload
    assert "snapshot_after" in payload["best_axis_steps"][0]


def test_cli_stdout_works_for_text_format():
    stdout = io.StringIO()

    with contextlib.redirect_stdout(stdout):
        result = main([str(SCENARIO_PATH), "--format", "text"])

    assert result == 0
    assert "HSR Axis Search Report" in stdout.getvalue()


def test_cli_output_writes_file(tmp_path):
    output_path = tmp_path / "axis_report.md"

    result = main([str(SCENARIO_PATH), "--format", "markdown", "--output", str(output_path)])

    assert result == 0
    assert "# HSR Axis Search Report" in output_path.read_text(encoding="utf-8")


def test_cli_include_snapshots_markdown_stdout():
    stdout = io.StringIO()

    with contextlib.redirect_stdout(stdout):
        result = main([str(SCENARIO_PATH), "--format", "markdown", "--include-snapshots"])

    assert result == 0
    assert "## Timeline Snapshots" in stdout.getvalue()


def test_cli_output_writes_file_with_snapshots(tmp_path):
    output_path = tmp_path / "axis_report_snapshots.md"

    result = main(
        [
            str(SCENARIO_PATH),
            "--format",
            "markdown",
            "--include-snapshots",
            "--output",
            str(output_path),
        ]
    )

    assert result == 0
    assert "## Timeline Snapshots" in output_path.read_text(encoding="utf-8")


def test_unknown_report_format_fails_clearly():
    report = run_search_scenario(load_search_scenario(SCENARIO_PATH))

    with pytest.raises(ValueError, match="Unknown report format"):
        render_search_scenario_report(report, "html")


def test_unknown_evaluator_profile_fails_clearly():
    scenario = load_search_scenario(SCENARIO_PATH)
    scenario.profile = "not_a_profile"

    with pytest.raises(ValueError, match="Unknown score profile"):
        run_search_scenario(scenario)


def test_constrained_scenario_avoids_disabled_target_in_best_axis():
    report = run_search_scenario(load_search_scenario(CONSTRAINED_SCENARIO_PATH))

    assert report.best_axis_steps
    assert report.best_terminal_reason == "constraints_no_choices"
    for step in report.best_axis_steps:
        assert "enemy_2" not in step.target_ids


def test_constrained_scenario_cli_runs_markdown():
    stdout = io.StringIO()

    with contextlib.redirect_stdout(stdout):
        result = main([str(CONSTRAINED_SCENARIO_PATH), "--format", "markdown"])

    assert result == 0
    output = stdout.getvalue()
    assert "# HSR Axis Search Report" in output
    assert "enemy_2" not in output


def test_constrained_scenario_json_output_avoids_disabled_target_in_steps():
    report = run_search_scenario(load_search_scenario(CONSTRAINED_SCENARIO_PATH))
    rendered = render_search_scenario_report(report, "json")
    payload = json.loads(rendered)

    for step in payload["best_axis_steps"]:
        assert "enemy_2" not in step["target_ids"]
