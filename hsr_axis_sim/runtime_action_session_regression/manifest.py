from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


RUNTIME_ACTION_SESSION_REGRESSION_SCHEMA = "hsr_runtime_action_session_regression"
RUNTIME_ACTION_SESSION_REGRESSION_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RuntimeActionSessionRegressionAction:
    action_id: str
    name: str
    ends_turn: bool


@dataclass(frozen=True)
class RuntimeActionSessionRegressionCase:
    case_id: str
    expected_relative_path: str
    expected_path: Path
    expected_sha256: str
    stream_id: str
    actor_id: str
    actions: tuple[RuntimeActionSessionRegressionAction, ...]


@dataclass(frozen=True)
class RuntimeActionSessionRegressionManifest:
    manifest_id: str
    path: Path
    cases: tuple[RuntimeActionSessionRegressionCase, ...]


def load_runtime_action_session_regression_manifest(
    path: str | Path,
) -> RuntimeActionSessionRegressionManifest:
    manifest_path = Path(path).resolve()
    if not manifest_path.is_file():
        raise ValueError(f"Runtime action-session regression manifest is not a file: {manifest_path}")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid runtime action-session regression manifest JSON: {exc}") from exc
    return runtime_action_session_regression_manifest_from_dict(data, manifest_path)


def runtime_action_session_regression_manifest_from_dict(
    data: Any,
    manifest_path: Path,
) -> RuntimeActionSessionRegressionManifest:
    if not isinstance(data, dict):
        raise ValueError("Runtime action-session regression manifest must be an object.")
    expected_root_fields = {"schema", "version", "manifest_id", "cases"}
    _require_exact_fields(data, expected_root_fields, "manifest")
    if data["schema"] != RUNTIME_ACTION_SESSION_REGRESSION_SCHEMA:
        raise ValueError(
            f"manifest.schema must be {RUNTIME_ACTION_SESSION_REGRESSION_SCHEMA!r}."
        )
    if data["version"] != RUNTIME_ACTION_SESSION_REGRESSION_VERSION:
        raise ValueError(
            f"manifest.version must be {RUNTIME_ACTION_SESSION_REGRESSION_VERSION!r}."
        )
    manifest_id = _require_non_empty_string(data["manifest_id"], "manifest.manifest_id")
    cases_data = data["cases"]
    if not isinstance(cases_data, list) or not cases_data:
        raise ValueError("manifest.cases must be a non-empty list.")

    cases: list[RuntimeActionSessionRegressionCase] = []
    seen_ids: set[str] = set()
    for index, case_data in enumerate(cases_data):
        case = _case_from_dict(case_data, f"manifest.cases[{index}]")
        if case.case_id in seen_ids:
            raise ValueError(f"Duplicate runtime action-session regression case id {case.case_id!r}.")
        seen_ids.add(case.case_id)
        cases.append(case)

    return RuntimeActionSessionRegressionManifest(
        manifest_id=manifest_id,
        path=Path(manifest_path).resolve(),
        cases=tuple(cases),
    )


def _case_from_dict(data: Any, label: str) -> RuntimeActionSessionRegressionCase:
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object.")
    expected_fields = {
        "id",
        "expected_path",
        "expected_sha256",
        "stream_id",
        "actor_id",
        "actions",
    }
    _require_exact_fields(data, expected_fields, label)

    case_id = _require_non_empty_string(data["id"], f"{label}.id")
    relative_path = _require_non_empty_string(data["expected_path"], f"{label}.expected_path")
    expected_path = _resolve_repo_relative_path(relative_path, f"{label}.expected_path")
    expected_sha256 = data["expected_sha256"]
    if not _is_lower_sha256(expected_sha256):
        raise ValueError(
            f"{label}.expected_sha256 must be exactly 64 lowercase hexadecimal characters."
        )
    stream_id = _require_non_empty_string(data["stream_id"], f"{label}.stream_id")
    actor_id = _require_non_empty_string(data["actor_id"], f"{label}.actor_id")

    actions_data = data["actions"]
    if not isinstance(actions_data, list) or not actions_data:
        raise ValueError(f"{label}.actions must be a non-empty list.")
    actions = tuple(
        _action_from_dict(action_data, f"{label}.actions[{index}]")
        for index, action_data in enumerate(actions_data)
    )

    return RuntimeActionSessionRegressionCase(
        case_id=case_id,
        expected_relative_path=relative_path,
        expected_path=expected_path,
        expected_sha256=expected_sha256,
        stream_id=stream_id,
        actor_id=actor_id,
        actions=actions,
    )


def _action_from_dict(data: Any, label: str) -> RuntimeActionSessionRegressionAction:
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object.")
    _require_exact_fields(data, {"action_id", "name", "ends_turn"}, label)
    action_id = _require_non_empty_string(data["action_id"], f"{label}.action_id")
    name = _require_non_empty_string(data["name"], f"{label}.name")
    ends_turn = data["ends_turn"]
    if type(ends_turn) is not bool:
        raise ValueError(f"{label}.ends_turn must be a boolean.")
    return RuntimeActionSessionRegressionAction(action_id, name, ends_turn)


def _resolve_repo_relative_path(value: str, label: str) -> Path:
    if "\\" in value:
        raise ValueError(f"{label} must use POSIX separators.")
    pure = PurePosixPath(value)
    if pure.is_absolute():
        raise ValueError(f"{label} must be repository-relative, not absolute.")
    if pure.as_posix() != value or not pure.parts or any(part in {".", ".."} for part in pure.parts):
        raise ValueError(f"{label} must be a canonical repository-relative POSIX path.")

    root = PROJECT_ROOT.resolve()
    resolved = (root / Path(*pure.parts)).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} resolves outside the repository root.") from exc
    if not resolved.is_file():
        raise ValueError(f"{label} does not resolve to an existing file: {resolved}")
    return resolved


def _require_exact_fields(data: dict[str, Any], expected: set[str], label: str) -> None:
    missing = sorted(expected - set(data))
    unknown = sorted(set(data) - expected)
    if missing:
        raise ValueError(f"{label} missing required field(s): {missing}.")
    if unknown:
        raise ValueError(f"{label} has unsupported field(s): {unknown}.")


def _require_non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string.")
    return value


def _is_lower_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )
