from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hsr_axis_sim.search.beam_search import beam_search
from hsr_axis_sim.search.constraints import SearchConstraints
from hsr_axis_sim.search.evaluator import Evaluator
from hsr_axis_sim.search.report import (
    SearchReport,
    build_search_report,
    format_axis_markdown,
    format_axis_text,
    search_report_to_dict,
)
from hsr_axis_sim.sim.data_loader import build_battle_state_from_files


@dataclass
class SearchScenario:
    id: str
    name: str
    description: str
    characters_dir: Path
    team_path: Path
    max_depth: int
    beam_width: int
    profile: str
    include_ultimates: bool
    max_global_av: float | None
    max_nodes_expanded: int | None
    constraints: SearchConstraints | None
    report_format: str
    top_k: int


def load_search_scenario(path: str | Path) -> SearchScenario:
    scenario_path = Path(path)
    if not scenario_path.exists():
        raise ValueError(f"Search scenario file not found: {scenario_path}")
    with scenario_path.open(encoding="utf-8") as scenario_file:
        data = json.load(scenario_file)
    return search_scenario_from_dict(data, base_dir=scenario_path.parent)


def search_scenario_from_dict(data: dict[str, Any], base_dir: Path) -> SearchScenario:
    _require_fields(data, ["id", "name", "description", "characters_dir", "team_path"], "scenario")
    search = data.get("search")
    if not isinstance(search, dict):
        raise ValueError("Search scenario requires a search object.")
    report = data.get("report", {})
    if not isinstance(report, dict):
        raise ValueError("Search scenario report must be an object.")
    _require_fields(search, ["max_depth", "beam_width", "profile"], "scenario.search")

    return SearchScenario(
        id=data["id"],
        name=data["name"],
        description=data["description"],
        characters_dir=_resolve_path(base_dir, data["characters_dir"]),
        team_path=_resolve_path(base_dir, data["team_path"]),
        max_depth=search["max_depth"],
        beam_width=search["beam_width"],
        profile=search["profile"],
        include_ultimates=search.get("include_ultimates", False),
        max_global_av=search.get("max_global_av"),
        max_nodes_expanded=search.get("max_nodes_expanded"),
        constraints=_constraints_from_dict(search.get("constraints")),
        report_format=report.get("format", "markdown"),
        top_k=report.get("top_k", 5),
    )


def run_search_scenario(scenario: SearchScenario) -> SearchReport:
    state, skill_lookup = build_battle_state_from_files(
        team_path=scenario.team_path,
        characters_dir=scenario.characters_dir,
    )
    evaluator = Evaluator(profile=scenario.profile)
    result = beam_search(
        initial_state=state,
        skill_lookup=skill_lookup,
        max_depth=scenario.max_depth,
        beam_width=scenario.beam_width,
        evaluator=evaluator,
        max_nodes_expanded=scenario.max_nodes_expanded,
        max_global_av=scenario.max_global_av,
        include_ultimates=scenario.include_ultimates,
        constraints=scenario.constraints,
    )
    return build_search_report(result, evaluator=evaluator, top_k=scenario.top_k)


def render_search_scenario_report(
    report: SearchReport,
    format: str,
    include_snapshots: bool = False,
) -> str:
    normalized = format.lower()
    if normalized == "markdown":
        return format_axis_markdown(report, include_snapshots=include_snapshots)
    if normalized == "text":
        return format_axis_text(report, include_snapshots=include_snapshots)
    if normalized == "json":
        return json.dumps(search_report_to_dict(report), indent=2, sort_keys=True)
    raise ValueError(f"Unknown report format: {format!r}.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a local HSR Axis search scenario.")
    parser.add_argument("scenario_path")
    parser.add_argument("--format", choices=["markdown", "text", "json"])
    parser.add_argument("--output")
    parser.add_argument("--profile")
    parser.add_argument("--max-depth", type=int)
    parser.add_argument("--beam-width", type=int)
    parser.add_argument("--include-ultimates", action="store_true")
    parser.add_argument("--include-snapshots", action="store_true")
    parser.add_argument("--top-k", type=int)
    args = parser.parse_args(argv)

    try:
        scenario = load_search_scenario(args.scenario_path)
        if args.profile is not None:
            scenario.profile = args.profile
        if args.max_depth is not None:
            scenario.max_depth = args.max_depth
        if args.beam_width is not None:
            scenario.beam_width = args.beam_width
        if args.include_ultimates:
            scenario.include_ultimates = True
        if args.top_k is not None:
            scenario.top_k = args.top_k
        selected_format = args.format or scenario.report_format
        report = run_search_scenario(scenario)
        rendered = render_search_scenario_report(
            report,
            selected_format,
            include_snapshots=args.include_snapshots,
        )
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def _resolve_path(base_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _require_fields(data: dict[str, Any], fields: list[str], label: str) -> None:
    missing = [field for field in fields if field not in data]
    if missing:
        raise ValueError(f"{label} missing required field(s): {missing}.")


def _constraints_from_dict(data: Any) -> SearchConstraints | None:
    if data is None:
        return None
    if not isinstance(data, dict):
        raise ValueError("scenario.search.constraints must be an object.")
    return SearchConstraints(
        allowed_actor_ids=_optional_string_set(data, "allowed_actor_ids"),
        disabled_actor_ids=_string_set(data, "disabled_actor_ids"),
        allowed_skill_ids=_optional_string_set(data, "allowed_skill_ids"),
        disabled_skill_ids=_string_set(data, "disabled_skill_ids"),
        allowed_skill_ids_by_actor=_actor_string_sets(data, "allowed_skill_ids_by_actor"),
        disabled_skill_ids_by_actor=_actor_string_sets(data, "disabled_skill_ids_by_actor"),
        allowed_target_ids=_optional_string_set(data, "allowed_target_ids"),
        disabled_target_ids=_string_set(data, "disabled_target_ids"),
        max_choices_per_node=_optional_positive_int(data, "max_choices_per_node"),
    )


def _optional_string_set(data: dict[str, Any], field_name: str) -> set[str] | None:
    if field_name not in data:
        return None
    return _string_set(data, field_name)


def _string_set(data: dict[str, Any], field_name: str) -> set[str]:
    value = data.get(field_name, [])
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"scenario.search.constraints.{field_name} must be a list of strings.")
    return set(value)


def _actor_string_sets(data: dict[str, Any], field_name: str) -> dict[str, set[str]]:
    value = data.get(field_name, {})
    if not isinstance(value, dict):
        raise ValueError(f"scenario.search.constraints.{field_name} must be an object.")
    result: dict[str, set[str]] = {}
    for actor_id, skill_ids in value.items():
        if not isinstance(actor_id, str):
            raise ValueError(f"scenario.search.constraints.{field_name} keys must be strings.")
        if not isinstance(skill_ids, list) or any(not isinstance(item, str) for item in skill_ids):
            raise ValueError(
                f"scenario.search.constraints.{field_name}.{actor_id} must be a list of strings."
            )
        result[actor_id] = set(skill_ids)
    return result


def _optional_positive_int(data: dict[str, Any], field_name: str) -> int | None:
    value = data.get(field_name)
    if value is None:
        return None
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"scenario.search.constraints.{field_name} must be a non-negative integer.")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
