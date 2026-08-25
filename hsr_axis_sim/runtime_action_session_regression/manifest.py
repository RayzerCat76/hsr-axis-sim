from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


RUNTIME_ACTION_SESSION_REGRESSION_SCHEMA = "hsr_runtime_action_session_regression"
RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_0 = "1.0"
RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_1 = "1.1"
RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_2 = "1.2"
RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_3 = "1.3"
RUNTIME_ACTION_SESSION_REGRESSION_VERSION = "1.4"
RUNTIME_ACTION_SESSION_REGRESSION_LEGACY_VERSION = (
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_0
)
RUNTIME_ACTION_SESSION_REGRESSION_SUPPORTED_VERSIONS = (
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_0,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_1,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_2,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_3,
    RUNTIME_ACTION_SESSION_REGRESSION_VERSION,
)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RuntimeActionSessionRegressionAction:
    action_id: str
    name: str
    ends_turn: bool


@dataclass(frozen=True)
class RuntimeActionSessionRegressionEnergyGainSetup:
    target_id: str
    target_name: str
    team: str
    base_speed: float
    initial_energy: float
    max_energy: float
    action_index: int
    amount: float


@dataclass(frozen=True)
class RuntimeActionSessionRegressionEnergyConsumeSetup:
    target_id: str
    target_name: str
    team: str
    base_speed: float
    initial_energy: float
    max_energy: float
    action_index: int
    amount: float


@dataclass(frozen=True)
class RuntimeActionSessionRegressionSkillPointGainSetup:
    initial_skill_points: int
    max_skill_points: int
    action_index: int
    amount: int


@dataclass(frozen=True)
class RuntimeActionSessionRegressionSkillPointConsumeSetup:
    initial_skill_points: int
    max_skill_points: int
    action_index: int
    amount: int


@dataclass(frozen=True)
class RuntimeActionSessionRegressionCase:
    case_id: str
    expected_relative_path: str
    expected_path: Path
    expected_sha256: str
    stream_id: str
    actor_id: str
    actions: tuple[RuntimeActionSessionRegressionAction, ...]
    setup: (
        RuntimeActionSessionRegressionEnergyGainSetup
        | RuntimeActionSessionRegressionEnergyConsumeSetup
        | RuntimeActionSessionRegressionSkillPointGainSetup
        | RuntimeActionSessionRegressionSkillPointConsumeSetup
        | None
    ) = None


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
    version = data["version"]
    if version not in RUNTIME_ACTION_SESSION_REGRESSION_SUPPORTED_VERSIONS:
        raise ValueError(
            "manifest.version must be one of "
            f"{RUNTIME_ACTION_SESSION_REGRESSION_SUPPORTED_VERSIONS!r}."
        )
    manifest_id = _require_non_empty_string(data["manifest_id"], "manifest.manifest_id")
    cases_data = data["cases"]
    if not isinstance(cases_data, list) or not cases_data:
        raise ValueError("manifest.cases must be a non-empty list.")

    cases: list[RuntimeActionSessionRegressionCase] = []
    seen_ids: set[str] = set()
    for index, case_data in enumerate(cases_data):
        case = _case_from_dict(
            case_data,
            f"manifest.cases[{index}]",
            version=version,
        )
        if case.case_id in seen_ids:
            raise ValueError(f"Duplicate runtime action-session regression case id {case.case_id!r}.")
        seen_ids.add(case.case_id)
        cases.append(case)

    return RuntimeActionSessionRegressionManifest(
        manifest_id=manifest_id,
        path=Path(manifest_path).resolve(),
        cases=tuple(cases),
    )


def _case_from_dict(
    data: Any,
    label: str,
    *,
    version: str,
) -> RuntimeActionSessionRegressionCase:
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
    if version != RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_0:
        expected_fields = expected_fields | {"setup"}
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

    setup = None
    if version != RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_0:
        setup = _setup_from_dict(
            data["setup"],
            f"{label}.setup",
            action_count=len(actions),
            version=version,
        )

    return RuntimeActionSessionRegressionCase(
        case_id=case_id,
        expected_relative_path=relative_path,
        expected_path=expected_path,
        expected_sha256=expected_sha256,
        stream_id=stream_id,
        actor_id=actor_id,
        actions=actions,
        setup=setup,
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


def _setup_from_dict(
    data: Any,
    label: str,
    *,
    action_count: int,
    version: str,
) -> (
    RuntimeActionSessionRegressionEnergyGainSetup
    | RuntimeActionSessionRegressionEnergyConsumeSetup
    | RuntimeActionSessionRegressionSkillPointGainSetup
    | RuntimeActionSessionRegressionSkillPointConsumeSetup
    | None
):
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object.")
    kind = data.get("kind")
    if kind == "EMPTY":
        _require_exact_fields(data, {"kind"}, label)
        return None
    if kind == "ENERGY_GAIN":
        return _energy_gain_setup_from_dict(data, label, action_count=action_count)
    if kind == "SKILL_POINT_GAIN":
        if version not in (
            RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_2,
            RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_3,
            RUNTIME_ACTION_SESSION_REGRESSION_VERSION,
        ):
            raise ValueError(
                f"{label}.kind 'SKILL_POINT_GAIN' requires manifest version "
                f"{RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_2!r} or later."
            )
        return _skill_point_gain_setup_from_dict(data, label, action_count=action_count)
    if kind == "ENERGY_CONSUME":
        if version not in (
            RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_3,
            RUNTIME_ACTION_SESSION_REGRESSION_VERSION,
        ):
            raise ValueError(
                f"{label}.kind 'ENERGY_CONSUME' requires manifest version "
                f"{RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_3!r} or later."
            )
        return _energy_consume_setup_from_dict(data, label, action_count=action_count)
    if kind == "SKILL_POINT_CONSUME":
        if version != RUNTIME_ACTION_SESSION_REGRESSION_VERSION:
            raise ValueError(
                f"{label}.kind 'SKILL_POINT_CONSUME' requires manifest version "
                f"{RUNTIME_ACTION_SESSION_REGRESSION_VERSION!r}."
            )
        return _skill_point_consume_setup_from_dict(
            data, label, action_count=action_count
        )

    allowed = "'EMPTY' or 'ENERGY_GAIN'"
    if version == RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_2:
        allowed = "'EMPTY', 'ENERGY_GAIN', or 'SKILL_POINT_GAIN'"
    elif version == RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_3:
        allowed = (
            "'EMPTY', 'ENERGY_GAIN', 'SKILL_POINT_GAIN', or 'ENERGY_CONSUME'"
        )
    elif version == RUNTIME_ACTION_SESSION_REGRESSION_VERSION:
        allowed = (
            "'EMPTY', 'ENERGY_GAIN', 'SKILL_POINT_GAIN', 'ENERGY_CONSUME', "
            "or 'SKILL_POINT_CONSUME'"
        )
    raise ValueError(f"{label}.kind must be {allowed}.")


def _energy_gain_setup_from_dict(
    data: dict[str, Any],
    label: str,
    *,
    action_count: int,
) -> RuntimeActionSessionRegressionEnergyGainSetup:
    values = _energy_unit_setup_values(data, label, action_count=action_count)
    return RuntimeActionSessionRegressionEnergyGainSetup(*values)


def _energy_consume_setup_from_dict(
    data: dict[str, Any],
    label: str,
    *,
    action_count: int,
) -> RuntimeActionSessionRegressionEnergyConsumeSetup:
    values = _energy_unit_setup_values(data, label, action_count=action_count)
    return RuntimeActionSessionRegressionEnergyConsumeSetup(*values)


def _energy_unit_setup_values(
    data: dict[str, Any],
    label: str,
    *,
    action_count: int,
) -> tuple[str, str, str, float, float, float, int, float]:
    expected_fields = {
        "kind",
        "target_id",
        "target_name",
        "team",
        "base_speed",
        "initial_energy",
        "max_energy",
        "action_index",
        "amount",
    }
    _require_exact_fields(data, expected_fields, label)
    target_id = _require_non_empty_string(data["target_id"], f"{label}.target_id")
    target_name = _require_non_empty_string(data["target_name"], f"{label}.target_name")
    team = _require_non_empty_string(data["team"], f"{label}.team")
    base_speed = _require_finite_number(data["base_speed"], f"{label}.base_speed")
    if base_speed <= 0:
        raise ValueError(f"{label}.base_speed must be greater than zero.")
    initial_energy = _require_finite_number(
        data["initial_energy"], f"{label}.initial_energy"
    )
    max_energy = _require_finite_number(data["max_energy"], f"{label}.max_energy")
    amount = _require_finite_number(data["amount"], f"{label}.amount")
    action_index = _require_action_index(
        data["action_index"], f"{label}.action_index", action_count=action_count
    )
    return (
        target_id,
        target_name,
        team,
        base_speed,
        initial_energy,
        max_energy,
        action_index,
        amount,
    )


def _skill_point_gain_setup_from_dict(
    data: dict[str, Any],
    label: str,
    *,
    action_count: int,
) -> RuntimeActionSessionRegressionSkillPointGainSetup:
    values = _skill_point_setup_values(data, label, action_count=action_count)
    return RuntimeActionSessionRegressionSkillPointGainSetup(*values)


def _skill_point_consume_setup_from_dict(
    data: dict[str, Any],
    label: str,
    *,
    action_count: int,
) -> RuntimeActionSessionRegressionSkillPointConsumeSetup:
    values = _skill_point_setup_values(data, label, action_count=action_count)
    return RuntimeActionSessionRegressionSkillPointConsumeSetup(*values)


def _skill_point_setup_values(
    data: dict[str, Any],
    label: str,
    *,
    action_count: int,
) -> tuple[int, int, int, int]:
    expected_fields = {
        "kind",
        "initial_skill_points",
        "max_skill_points",
        "action_index",
        "amount",
    }
    _require_exact_fields(data, expected_fields, label)
    initial_skill_points = _require_exact_integer(
        data["initial_skill_points"], f"{label}.initial_skill_points"
    )
    max_skill_points = _require_exact_integer(
        data["max_skill_points"], f"{label}.max_skill_points"
    )
    amount = _require_exact_integer(data["amount"], f"{label}.amount")
    action_index = _require_action_index(
        data["action_index"], f"{label}.action_index", action_count=action_count
    )
    return initial_skill_points, max_skill_points, action_index, amount


def _require_action_index(value: Any, label: str, *, action_count: int) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer.")
    if value >= action_count:
        raise ValueError(
            f"{label} must reference a declared action; "
            f"got {value} for {action_count} action(s)."
        )
    return value


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


def _require_finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number.")
    return value


def _require_exact_integer(value: Any, label: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{label} must be an integer.")
    return value


def _is_lower_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )
