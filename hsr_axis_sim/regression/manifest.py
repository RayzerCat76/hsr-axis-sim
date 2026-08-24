from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SUPPORTED_GROUPS = {
    "replays", "manual", "scenarios", "action_sequence_traces", "trace_evidence"
}
ORDERED_GROUPS = [
    "replays", "manual", "scenarios", "action_sequence_traces", "trace_evidence"
]
SUPPORTED_ACTION_SEQUENCE_CHECKS = {"lint", "action_sequence"}
SUPPORTED_TRACE_EVIDENCE_CHECKS = {"semantic_map", "frame_anchors"}
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class RegressionManifestEntry:
    id: str
    path: Path
    checks: list[str] = field(default_factory=list)
    check: str | None = None
    source_trace_path: Path | None = None


@dataclass
class RegressionManifest:
    manifest_id: str
    project: str
    description: str
    path: Path
    groups: dict[str, list[RegressionManifestEntry]] = field(default_factory=dict)

    def paths_for_group(self, group: str) -> list[Path]:
        return [entry.path for entry in self.groups.get(group, [])]

    def counts_by_group(self) -> dict[str, int]:
        return {group: len(self.groups.get(group, [])) for group in ORDERED_GROUPS}


def load_regression_manifest(path: str | Path) -> RegressionManifest:
    manifest_path = Path(path)
    with manifest_path.open(encoding="utf-8") as manifest_file:
        data = json.load(manifest_file)
    return regression_manifest_from_dict(data, manifest_path=manifest_path)


def regression_manifest_from_dict(
    data: dict[str, Any],
    manifest_path: Path,
) -> RegressionManifest:
    if not isinstance(data, dict):
        raise ValueError("Regression manifest must be an object.")
    _require_fields(data, ["manifest_id", "project", "description", "groups"], "manifest")
    groups_data = data["groups"]
    if not isinstance(groups_data, dict):
        raise ValueError("manifest.groups must be an object.")

    unknown_groups = sorted(set(groups_data) - SUPPORTED_GROUPS)
    if unknown_groups:
        raise ValueError(f"Unsupported manifest group(s): {unknown_groups}.")

    groups: dict[str, list[RegressionManifestEntry]] = {}
    for group in ORDERED_GROUPS:
        entries_data = groups_data.get(group, [])
        if not isinstance(entries_data, list):
            raise ValueError(f"manifest.groups.{group} must be a list.")
        groups[group] = _entries_from_list(group, entries_data)

    return RegressionManifest(
        manifest_id=data["manifest_id"],
        project=data["project"],
        description=data["description"],
        path=manifest_path.resolve(),
        groups=groups,
    )


def _entries_from_list(
    group: str,
    entries_data: list[Any],
) -> list[RegressionManifestEntry]:
    seen_ids: set[str] = set()
    entries: list[RegressionManifestEntry] = []
    for index, entry_data in enumerate(entries_data):
        label = f"manifest.groups.{group}[{index}]"
        if not isinstance(entry_data, dict):
            raise ValueError(f"{label} must be an object.")
        _require_fields(entry_data, ["id", "path"], label)
        entry_id = entry_data["id"]
        entry_path = entry_data["path"]
        entry_checks = entry_data.get("checks", [])
        if not isinstance(entry_id, str) or not entry_id:
            raise ValueError(f"{label}.id must be a non-empty string.")
        if not isinstance(entry_path, str) or not entry_path:
            raise ValueError(f"{label}.path must be a non-empty string.")
        if not isinstance(entry_checks, list):
            raise ValueError(f"{label}.checks must be a list when present.")
        if group == "action_sequence_traces":
            if not entry_checks:
                entry_checks = ["lint", "action_sequence"]
            invalid_checks = [
                check for check in entry_checks if check not in SUPPORTED_ACTION_SEQUENCE_CHECKS
            ]
            if invalid_checks:
                raise ValueError(f"{label}.checks has unsupported check(s): {invalid_checks}.")
            if "lint" not in entry_checks or "action_sequence" not in entry_checks:
                raise ValueError(
                    f"{label}.checks must include both 'lint' and 'action_sequence'."
                )
        elif entry_checks:
            raise ValueError(f"{label}.checks is only supported for action_sequence_traces.")
        entry_check: str | None = None
        source_trace_path: Path | None = None
        if group == "trace_evidence":
            _require_fields(entry_data, ["source_trace_path", "check"], label)
            entry_check = entry_data["check"]
            source_trace_value = entry_data["source_trace_path"]
            if not isinstance(entry_check, str) or entry_check not in SUPPORTED_TRACE_EVIDENCE_CHECKS:
                raise ValueError(
                    f"{label}.check must be one of {sorted(SUPPORTED_TRACE_EVIDENCE_CHECKS)}."
                )
            if not isinstance(source_trace_value, str) or not source_trace_value:
                raise ValueError(f"{label}.source_trace_path must be a non-empty string.")
            source_trace_path = _resolve_manifest_fixture_path(source_trace_value)
            if not source_trace_path.exists():
                raise ValueError(
                    f"Manifest source trace path does not exist: {source_trace_path}"
                )
        if entry_id in seen_ids:
            raise ValueError(f"Duplicate manifest id {entry_id!r} in group {group!r}.")
        seen_ids.add(entry_id)

        resolved_path = _resolve_manifest_fixture_path(entry_path)
        if not resolved_path.exists():
            raise ValueError(f"Manifest fixture path does not exist: {resolved_path}")
        entries.append(
            RegressionManifestEntry(
                id=entry_id,
                path=resolved_path,
                checks=list(entry_checks),
                check=entry_check,
                source_trace_path=source_trace_path,
            )
        )
    return entries


def _resolve_manifest_fixture_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


def _require_fields(data: dict[str, Any], fields: list[str], label: str) -> None:
    missing = [field for field in fields if field not in data]
    if missing:
        raise ValueError(f"{label} missing required field(s): {missing}.")
