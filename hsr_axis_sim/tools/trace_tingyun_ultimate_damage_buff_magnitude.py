from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "manual_video_traces"
DEFAULT_INTAKE = BASE / "normalized_character_facts" / "tingyun_ultimate_damage_buff_magnitude_intake_v0_1.json"
INTAKE_STATUSES = {"captured_exact_table", "blocked_source_unavailable"}
SOURCE_TYPES = {"structured_game_database", "official_game_text", "official_web", "community_mechanics_reference"}
SUPPORT_LEVELS = {"supports_exact_field", "supports_context_only"}
ATTEMPT_OUTCOMES = {"no_usable_exact_table", "access_unavailable"}
FORBIDDEN_KEYS = {"effects", "effect", "executor", "handlerkey", "bindingdatapath", "characterspec", "skillspec", "realtraceexecutable"}
EXPECTED_FACT_ID = "tingyun.ultimate.damage_buff.magnitude_by_trace_level"
EXPECTED_UNRESOLVED = {
    "real_video_trace_level",
    "real_video_selected_ally",
    "damage_buff_application_order_relative_to_energy_restore",
    "same_current_turn_duration_behavior",
}
WARNING = "NON-EXECUTABLE MAGNITUDE EVIDENCE INTAKE. No row authorizes simulator binding or selection of a real-video trace level."


@dataclass(frozen=True)
class MagnitudeEvidenceReport:
    intake_id: str
    version: str
    warning: str
    intake_status: str
    fact_id: str
    accepted_sources: tuple[dict[str, Any], ...]
    context_sources: tuple[dict[str, Any], ...]
    raw_tables: tuple[dict[str, Any], ...]
    normalized_table: tuple[dict[str, Any], ...]
    acquisition_attempts: tuple[dict[str, str], ...]
    blocked_reasons: tuple[str, ...]
    real_video_trace_level: None
    preserved_unresolved_fields: tuple[str, ...]
    readiness_status: str
    simulator_binding_allowed: bool


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def build_report(data: Any) -> MagnitudeEvidenceReport:
    issues: list[str] = []
    if not isinstance(data, dict):
        raise ValueError("Tingyun magnitude intake validation failed:\n- intake must be an object.")
    _reject_executable_schema(data, "intake", issues)
    for field in ("intake_id", "version", "fact_id", "intake_status", "readiness_status"):
        if not isinstance(data.get(field), str) or not data[field]:
            issues.append(f"{field} must be a non-empty string.")
    status = data.get("intake_status")
    if isinstance(status, str) and status not in INTAKE_STATUSES:
        issues.append("intake_status is unsupported.")
    if data.get("fact_id") != EXPECTED_FACT_ID:
        issues.append(f"fact_id must be {EXPECTED_FACT_ID!r}.")
    if data.get("real_video_trace_level") is not None:
        issues.append("real_video_trace_level must remain null.")
    if data.get("readiness_status") != "blocked_by_both":
        issues.append("readiness_status must remain 'blocked_by_both'.")
    if data.get("simulator_binding_allowed") is not False:
        issues.append("simulator_binding_allowed must be false.")
    unresolved = _string_list(data.get("preserved_unresolved_fields"), "preserved_unresolved_fields", issues)
    if set(unresolved) != EXPECTED_UNRESOLVED:
        issues.append("preserved_unresolved_fields must contain the exact required unresolved fields.")

    sources = _sources(data.get("accepted_sources"), issues)
    context_sources = _sources(data.get("context_sources"), issues, "context_sources")
    raw_tables = _raw_tables(data.get("raw_tables"), sources, issues)
    normalized = _normalized_table(data.get("normalized_table"), raw_tables, sources, issues)
    attempts = _attempts(data.get("acquisition_attempts"), issues)
    blocked_reasons = _string_list(data.get("blocked_reasons"), "blocked_reasons", issues)

    if status == "blocked_source_unavailable":
        if sources or raw_tables or normalized:
            issues.append("blocked intake must not contain accepted sources or table rows.")
        if not attempts or not blocked_reasons:
            issues.append("blocked intake requires acquisition attempts and blocked reasons.")
    elif status == "captured_exact_table":
        exact_sources = [source for source in sources.values() if source["support_level"] == "supports_exact_field"]
        if len(exact_sources) < 2:
            issues.append("captured table requires at least two exact-field sources.")
        for source in exact_sources:
            for field in ("repository", "commit", "path", "snapshot_qualification"):
                if not isinstance(source.get(field), str) or not source[field]:
                    issues.append(f"accepted exact source {source['source_id']!r} requires {field}.")
        if len(raw_tables) != len(sources) or not normalized:
            issues.append("captured table requires one raw table per source and normalized rows.")
        if sorted(row["normalized_trace_level"] for row in normalized) != list(range(1, 16)):
            issues.append("captured table must normalize the exact levels 1 through 15.")
        if blocked_reasons:
            issues.append("captured table must not declare blocked reasons.")

    if issues:
        raise ValueError("Tingyun magnitude intake validation failed:\n" + "\n".join(f"- {issue}" for issue in issues))
    return MagnitudeEvidenceReport(
        intake_id=data["intake_id"],
        version=data["version"],
        warning=WARNING,
        intake_status=status,
        fact_id=data["fact_id"],
        accepted_sources=tuple(sorted(sources.values(), key=lambda item: item["source_id"])),
        context_sources=tuple(sorted(context_sources.values(), key=lambda item: item["source_id"])),
        raw_tables=tuple(sorted(raw_tables.values(), key=lambda item: item["source_id"])),
        normalized_table=tuple(sorted(normalized, key=lambda item: item["normalized_trace_level"])),
        acquisition_attempts=tuple(sorted(attempts, key=lambda item: item["attempt_id"])),
        blocked_reasons=tuple(sorted(blocked_reasons)),
        real_video_trace_level=None,
        preserved_unresolved_fields=tuple(sorted(unresolved)),
        readiness_status="blocked_by_both",
        simulator_binding_allowed=False,
    )


def _sources(value: Any, issues: list[str], label_prefix: str = "accepted_sources") -> dict[str, dict[str, Any]]:
    if not isinstance(value, list):
        issues.append(f"{label_prefix} must be a list.")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(value):
        label = f"{label_prefix}[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{label} must be an object.")
            continue
        row: dict[str, str] = {}
        for field in ("source_id", "title", "locator", "source_type", "language", "game_version", "retrieval_date", "exact_field_locator", "support_level", "level_mapping_basis"):
            raw = item.get(field)
            if not isinstance(raw, str) or not raw:
                issues.append(f"{label}.{field} must be a non-empty string.")
            else:
                row[field] = raw
        for field in ("repository", "commit", "path", "snapshot_qualification"):
            raw = item.get(field)
            if raw is not None:
                if not isinstance(raw, str) or not raw:
                    issues.append(f"{label}.{field} must be a non-empty string when provided.")
                else:
                    row[field] = raw
        if row.get("source_type") not in SOURCE_TYPES:
            issues.append(f"{label}.source_type is unsupported.")
        if row.get("support_level") not in SUPPORT_LEVELS:
            issues.append(f"{label}.support_level is unsupported.")
        source_id = row.get("source_id")
        if source_id:
            if source_id in result:
                issues.append(f"duplicate source ID {source_id!r}.")
            elif all(field in row for field in ("source_id", "title", "locator", "source_type", "language", "game_version", "retrieval_date", "exact_field_locator", "support_level", "level_mapping_basis")):
                result[source_id] = row
    return result


def _raw_tables(value: Any, sources: dict[str, dict[str, Any]], issues: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list):
        issues.append("raw_tables must be a list.")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for index, table in enumerate(value):
        label = f"raw_tables[{index}]"
        if not isinstance(table, dict):
            issues.append(f"{label} must be an object.")
            continue
        source_id = table.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            issues.append(f"{label}.source_id must be a non-empty string.")
            continue
        if source_id not in sources:
            issues.append(f"{label} has a dangling source reference.")
        if source_id in result:
            issues.append(f"duplicate raw table source ID {source_id!r}.")
        if table.get("unit") != "ratio":
            issues.append(f"{label}.unit must be 'ratio'.")
        rows = _raw_rows(table.get("rows"), f"{label}.rows", issues)
        if source_id in sources and source_id not in result:
            result[source_id] = {"source_id": source_id, "unit": "ratio", "rows": rows}
    return result


def _raw_rows(value: Any, label: str, issues: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        issues.append(f"{label} must be a non-empty list.")
        return []
    result: list[dict[str, Any]] = []
    levels: list[int] = []
    for index, row in enumerate(value):
        row_label = f"{label}[{index}]"
        if not isinstance(row, dict):
            issues.append(f"{row_label} must be an object.")
            continue
        level, ratio = row.get("raw_level_index"), row.get("dmg_increase_ratio")
        if type(level) is not int or level < 1:
            issues.append(f"{row_label}.raw_level_index must be a positive integer.")
            continue
        if isinstance(ratio, bool) or not isinstance(ratio, (int, float)) or not math.isfinite(ratio) or ratio < 0:
            issues.append(f"{row_label}.dmg_increase_ratio must be a finite nonnegative number.")
            continue
        levels.append(level)
        result.append({"raw_level_index": level, "dmg_increase_ratio": ratio})
    if len(set(levels)) != len(levels):
        issues.append(f"{label} contains duplicate levels.")
    return sorted(result, key=lambda item: item["raw_level_index"])


def _numeric_rows(value: Any, label: str, level_field: str, issues: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        issues.append(f"{label} must be a non-empty list.")
        return []
    result: list[dict[str, Any]] = []
    levels: list[int] = []
    for index, row in enumerate(value):
        row_label = f"{label}[{index}]"
        if not isinstance(row, dict):
            issues.append(f"{row_label} must be an object.")
            continue
        level = row.get(level_field)
        amount = row.get("dmg_increase_percent")
        if type(level) is not int or level < 1:
            issues.append(f"{row_label}.{level_field} must be a positive integer.")
            continue
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount < 0:
            issues.append(f"{row_label}.dmg_increase_percent must be a finite nonnegative number.")
            continue
        levels.append(level)
        result.append({level_field: level, "dmg_increase_percent": amount})
    if len(set(levels)) != len(levels):
        issues.append(f"{label} contains duplicate levels.")
    return sorted(result, key=lambda item: item[level_field])


def _normalized_table(value: Any, raw_tables: dict[str, dict[str, Any]], sources: dict[str, dict[str, Any]], issues: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        issues.append("normalized_table must be a list.")
        return []
    result: list[dict[str, Any]] = []
    levels: list[int] = []
    for index, row in enumerate(value):
        label = f"normalized_table[{index}]"
        validated = _numeric_rows([row], label, "normalized_trace_level", issues)
        if not validated:
            continue
        level_row = validated[0]
        if row.get("unit") != "percent":
            issues.append(f"{label}.unit must be 'percent'.")
        refs = row.get("raw_source_rows") if isinstance(row, dict) else None
        if not isinstance(refs, list) or not refs:
            issues.append(f"{label}.raw_source_rows must be a non-empty list.")
            continue
        seen: list[str] = []
        refs_out: list[dict[str, Any]] = []
        for ref_index, ref in enumerate(refs):
            ref_label = f"{label}.raw_source_rows[{ref_index}]"
            if not isinstance(ref, dict):
                issues.append(f"{ref_label} must be an object.")
                continue
            source_id, raw_level = ref.get("source_id"), ref.get("raw_level_index")
            if not isinstance(source_id, str) or not source_id:
                issues.append(f"{ref_label}.source_id must be a non-empty string.")
                continue
            if type(raw_level) is not int or raw_level < 1:
                issues.append(f"{ref_label}.raw_level_index must be a positive integer.")
                continue
            seen.append(source_id)
            raw_rows = raw_tables.get(source_id, {}).get("rows", [])
            match = next((raw for raw in raw_rows if raw["raw_level_index"] == raw_level), None)
            if source_id not in sources or match is None:
                issues.append(f"{ref_label} has a dangling raw source row.")
            elif not math.isclose(match["dmg_increase_ratio"] * 100, level_row["dmg_increase_percent"], rel_tol=0, abs_tol=1e-12):
                issues.append(f"{ref_label} magnitude conflicts with normalized row.")
            refs_out.append({"source_id": source_id, "raw_level_index": raw_level})
        if len(set(seen)) != len(seen):
            issues.append(f"{label}.raw_source_rows contains duplicate source IDs.")
        if set(seen) != set(sources):
            issues.append(f"{label} must reference every accepted source.")
        levels.append(level_row["normalized_trace_level"])
        result.append({**level_row, "unit": "percent", "raw_source_rows": sorted(refs_out, key=lambda item: (item["source_id"], item["raw_level_index"]))})
    if len(set(levels)) != len(levels):
        issues.append("normalized_table contains duplicate levels.")
    return result


def _attempts(value: Any, issues: list[str]) -> list[dict[str, str]]:
    if not isinstance(value, list):
        issues.append("acquisition_attempts must be a list.")
        return []
    result: list[dict[str, str]] = []
    ids: list[str] = []
    for index, item in enumerate(value):
        label = f"acquisition_attempts[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{label} must be an object.")
            continue
        row: dict[str, str] = {}
        for field in ("attempt_id", "locator", "retrieval_date", "outcome", "notes"):
            raw = item.get(field)
            if not isinstance(raw, str) or not raw:
                issues.append(f"{label}.{field} must be a non-empty string.")
            else:
                row[field] = raw
        if row.get("outcome") not in ATTEMPT_OUTCOMES:
            issues.append(f"{label}.outcome is unsupported.")
        if len(row) == 5:
            ids.append(row["attempt_id"])
            result.append(row)
    if len(set(ids)) != len(ids):
        issues.append("acquisition_attempts contains duplicate attempt IDs.")
    return result


def _string_list(value: Any, label: str, issues: list[str]) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        issues.append(f"{label} must be a list of non-empty strings.")
        return []
    if len(set(value)) != len(value):
        issues.append(f"{label} must not contain duplicates.")
    return value


def _reject_executable_schema(value: Any, label: str, issues: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z]", "", key.lower())
            if normalized in FORBIDDEN_KEYS:
                issues.append(f"{label}.{key} is an executable schema key and is forbidden.")
            _reject_executable_schema(child, f"{label}.{key}", issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_executable_schema(child, f"{label}[{index}]", issues)


def render_json(report: MagnitudeEvidenceReport) -> str:
    return json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n"


def render_markdown(report: MagnitudeEvidenceReport) -> str:
    lines = [
        "# Tingyun Ultimate DMG-Buff Magnitude Evidence Intake",
        "",
        f"> {report.warning}",
        "",
        f"Intake status: `{report.intake_status}`  ",
        f"Readiness: `{report.readiness_status}`",
        "",
        "## Accepted Sources",
        "",
    ]
    if not report.accepted_sources:
        lines.append("- None. No exact table was accepted.")
    for source in report.accepted_sources:
        lines.append(f"- `{source['source_id']}`: `{source['repository']}` commit `{source['commit']}`, `{source['path']}`, `{source['exact_field_locator']}`. {source['snapshot_qualification']}")
    lines.extend(["", "## Context-Only Sources", ""])
    for source in report.context_sources:
        lines.append(f"- `{source['source_id']}`: {source['title']} ({source['game_version']}); `{source['exact_field_locator']}`. This source is not used as a complete table.")
    lines.extend(["", "## Raw Source Tables", ""])
    if not report.raw_tables:
        lines.append("- No raw rows captured.")
    for table in report.raw_tables:
        lines.append(f"### {table['source_id']}")
        lines.append("")
        lines.extend(f"- Raw level {row['raw_level_index']}: ratio {row['dmg_increase_ratio']}" for row in table["rows"])
    lines.extend(["", "## Normalized Table", ""])
    if not report.normalized_table:
        lines.append("- No normalized levels. The magnitude fact remains missing.")
    for row in report.normalized_table:
        lines.append(f"- Trace level {row['normalized_trace_level']}: {row['dmg_increase_percent']}%")
    lines.extend(["", "## Acquisition Attempts", ""])
    if not report.acquisition_attempts:
        lines.append("- None. The accepted tables are recorded above.")
    else:
        lines.extend(f"- `{item['attempt_id']}` ({item['retrieval_date']}, {item['outcome']}): {item['locator']}. {item['notes']}" for item in report.acquisition_attempts)
    lines.extend(["", "## Normalization", "", "- Raw source rows are decimal ratios; normalized rows multiply each ratio by 100 and store unit `percent`.", "", "## Blockers", ""])
    if not report.blocked_reasons:
        lines.append("- No magnitude-source blocker remains; readiness is still blocked by separately unresolved effect-order and duration-semantics evidence.")
    else:
        lines.extend(f"- {item}" for item in report.blocked_reasons)
    lines.extend(["", "## Preserved Unknowns", "", *(f"- `{item}`" for item in report.preserved_unresolved_fields), "", "- Real-video trace level: `null`.", "- Simulator binding allowed: `false`."])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and render Tingyun Ultimate magnitude evidence intake.")
    parser.add_argument("--intake", default=str(DEFAULT_INTAKE))
    parser.add_argument("--format", choices=["markdown", "json"], required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        data = load_json(args.intake)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR Tingyun magnitude intake input failure: {exc}", file=sys.stderr)
        return 2
    try:
        report = build_report(data)
    except ValueError as exc:
        print(f"FAIL Tingyun magnitude intake validation: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR Tingyun magnitude intake could not run: {exc}", file=sys.stderr)
        return 2
    rendered = render_markdown(report) if args.format == "markdown" else render_json(report)
    try:
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except OSError as exc:
        print(f"ERROR Tingyun magnitude intake output failure: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
