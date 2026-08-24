from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from hsr_axis_sim.real_bindings.pela_skill_v0_1 import (
    ATOMIC_FACT_SHA256 as PELA_ATOMIC_FACT_SHA256,
    execute_partial_binding as execute_pela_binding,
    load_json,
    validate_binding as validate_pela_binding,
)
from hsr_axis_sim.real_bindings.tingyun_ultimate_v0_1 import (
    ATOMIC_FACT_SHA256 as TINGYUN_ATOMIC_FACT_SHA256,
    execute_partial_binding as execute_tingyun_binding,
    validate_binding as validate_tingyun_binding,
)
from hsr_axis_sim.sim import BattleState, TurnContext


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = Path(__file__).resolve().parent / "registry_v0_2.json"
SUPPORTED_BINDING_TYPES = {"partial_action_shell"}
SEMANTICS_STATUSES = {"not_implemented"}
STRING_FIELDS = {
    "registry_entry_id", "binding_id", "version", "actor_id", "action_category",
    "binding_scope", "binding_type", "binding_data_path", "handler_key",
    "source_atomic_fact_artifact_path", "accepted_atomic_fact_sha256",
    "damage_semantics_status", "toughness_semantics_status",
}
BOOLEAN_FIELDS = {
    "complete_game_skill", "complete_character_kit", "synthetic_only",
    "real_trace_executable",
}
LIST_FIELDS = {
    "source_atomic_fact_ids", "unresolved_atomic_fact_ids", "unresolved_fields",
}
WARNING = (
    "All reviewed bindings are partial, synthetic-only shells. Raw binding dictionaries "
    "are not the reviewed public execution contract, and the real trace is non-executable."
)


@dataclass(frozen=True)
class ReviewedBindingHandle:
    registry_entry_id: str
    binding_id: str
    version: str
    actor_id: str
    action_category: str
    binding_scope: str
    binding_type: str
    binding_data_path: Path
    handler_key: str
    source_atomic_fact_artifact_path: Path
    accepted_atomic_fact_sha256: str
    source_atomic_fact_ids: tuple[str, ...]
    unresolved_atomic_fact_ids: tuple[str, ...]
    unresolved_fields: tuple[str, ...]
    complete_game_skill: bool
    complete_character_kit: bool
    synthetic_only: bool
    real_trace_executable: bool
    damage_semantics_status: str
    toughness_semantics_status: str


@dataclass(frozen=True)
class ReviewedBindingRegistry:
    registry_version: str
    bindings: tuple[ReviewedBindingHandle, ...]


@dataclass(frozen=True)
class RegistryAuditReport:
    registry_version: str
    reviewed_binding_count: int
    warning: str
    bindings: tuple[dict[str, Any], ...]
    real_trace_executable: bool


BindingExecutor = Callable[
    [dict[str, Any], BattleState, list[str], TurnContext | None],
    tuple[TurnContext, str | None],
]
BindingValidator = Callable[[dict[str, Any], dict[str, Any], str | Path | None], None]


@dataclass(frozen=True)
class ReviewedHandlerSpec:
    executor: BindingExecutor
    validator: BindingValidator
    pinned_atomic_fact_sha256: str


HANDLER_SPECS: dict[str, ReviewedHandlerSpec] = {
    "pela_skill_partial_v0_1": ReviewedHandlerSpec(
        executor=execute_pela_binding,
        validator=validate_pela_binding,
        pinned_atomic_fact_sha256=PELA_ATOMIC_FACT_SHA256,
    ),
    "tingyun_ultimate_partial_v0_1": ReviewedHandlerSpec(
        executor=execute_tingyun_binding,
        validator=validate_tingyun_binding,
        pinned_atomic_fact_sha256=TINGYUN_ATOMIC_FACT_SHA256,
    ),
}


def load_reviewed_binding_registry(path: str | Path = DEFAULT_REGISTRY) -> ReviewedBindingRegistry:
    registry_path = Path(path)
    data = load_json(registry_path)
    if not isinstance(data.get("registry_version"), str) or not data["registry_version"]:
        raise ValueError("registry_version must be a non-empty string.")
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise ValueError("reviewed binding registry entries must be a list.")
    issues: list[str] = []
    for index, entry in enumerate(entries):
        issues.extend(f"entries[{index}]: {issue}" for issue in _entry_shape_issues(entry))
    if issues:
        raise ValueError("Reviewed binding registry validation failed:\n" + "\n".join(f"- {issue}" for issue in issues))
    entry_ids = [entry.get("registry_entry_id") for entry in entries]
    binding_ids = [entry.get("binding_id") for entry in entries]
    _reject_duplicates(entry_ids, "registry entry", issues)
    _reject_duplicates(binding_ids, "binding", issues)
    handles: list[ReviewedBindingHandle] = []
    for index, entry in enumerate(entries):
        try:
            handles.append(_validated_handle(entry))
        except (OSError, ValueError) as exc:
            issues.append(f"entries[{index}]: {exc}")
    if issues:
        raise ValueError("Reviewed binding registry validation failed:\n" + "\n".join(f"- {issue}" for issue in issues))
    return ReviewedBindingRegistry(data["registry_version"], tuple(sorted(handles, key=lambda item: item.binding_id)))


def list_reviewed_bindings(registry: ReviewedBindingRegistry) -> tuple[ReviewedBindingHandle, ...]:
    return registry.bindings


def get_reviewed_binding(binding_id: str, registry: ReviewedBindingRegistry) -> ReviewedBindingHandle:
    for handle in registry.bindings:
        if handle.binding_id == binding_id:
            return handle
    raise ValueError(f"Unknown reviewed binding ID: {binding_id!r}.")


def execute_reviewed_binding(
    binding_id: str,
    state: BattleState,
    target_ids: list[str],
    turn_context: TurnContext | None = None,
    registry: ReviewedBindingRegistry | None = None,
) -> tuple[TurnContext, str | None]:
    active_registry = registry or load_reviewed_binding_registry()
    handle = get_reviewed_binding(binding_id, active_registry)
    validated_handle = _revalidate_handle(handle)
    binding = load_json(validated_handle.binding_data_path)
    atoms = load_json(validated_handle.source_atomic_fact_artifact_path)
    handler_spec = _handler_spec(validated_handle.handler_key)
    actual_digest = hashlib.sha256(
        validated_handle.source_atomic_fact_artifact_path.read_bytes()
    ).hexdigest()
    if (
        actual_digest != validated_handle.accepted_atomic_fact_sha256
        or actual_digest != handler_spec.pinned_atomic_fact_sha256
    ):
        raise ValueError("accepted atomic fact digest mismatch.")
    handler_spec.validator(
        binding, atoms, validated_handle.source_atomic_fact_artifact_path
    )
    _validate_metadata_match(validated_handle, binding)
    return handler_spec.executor(binding, state, target_ids, turn_context)


def build_registry_audit_report(registry: ReviewedBindingRegistry) -> RegistryAuditReport:
    bindings = tuple(
        {
            "registry_entry_id": item.registry_entry_id,
            "binding_id": item.binding_id,
            "version": item.version,
            "actor_id": item.actor_id,
            "action_category": item.action_category,
            "binding_scope": item.binding_scope,
            "binding_type": item.binding_type,
            "handler_key": item.handler_key,
            "accepted_atomic_fact_sha256": item.accepted_atomic_fact_sha256,
            "source_atomic_fact_ids": list(item.source_atomic_fact_ids),
            "unresolved_atomic_fact_ids": list(item.unresolved_atomic_fact_ids),
            "unresolved_fields": list(item.unresolved_fields),
            "complete_game_skill": item.complete_game_skill,
            "complete_character_kit": item.complete_character_kit,
            "synthetic_only": item.synthetic_only,
            "real_trace_executable": item.real_trace_executable,
            "damage_semantics_status": item.damage_semantics_status,
            "toughness_semantics_status": item.toughness_semantics_status,
        }
        for item in registry.bindings
    )
    return RegistryAuditReport(registry.registry_version, len(bindings), WARNING, bindings, False)


def render_json(report: RegistryAuditReport) -> str:
    return json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n"


def render_markdown(report: RegistryAuditReport) -> str:
    lines = [
        "# Reviewed Partial-Binding Registry Audit", "",
        f"Registry version: `{report.registry_version}`  ",
        f"Reviewed bindings: `{report.reviewed_binding_count}`", "",
        f"> {report.warning}", "",
        "| Binding | Actor | Action | Scope | Handler | Complete skill | Complete kit | Synthetic only | Real trace executable | Damage | Toughness |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in report.bindings:
        lines.append(
            f"| {item['binding_id']} | {item['actor_id']} | {item['action_category']} | {item['binding_scope']} | {item['handler_key']} | `{str(item['complete_game_skill']).lower()}` | `{str(item['complete_character_kit']).lower()}` | `{str(item['synthetic_only']).lower()}` | `{str(item['real_trace_executable']).lower()}` | {item['damage_semantics_status']} | {item['toughness_semantics_status']} |"
        )
        lines.extend([
            "", f"## {item['binding_id']}", "",
            f"- Accepted atomic digest: `{item['accepted_atomic_fact_sha256']}`",
            f"- Bound facts: {', '.join(item['source_atomic_fact_ids'])}",
            f"- Unresolved facts: {', '.join(item['unresolved_atomic_fact_ids'])}",
            f"- Unresolved fields: {', '.join(item['unresolved_fields'])}",
        ])
    lines.extend(["", "## Real Trace Status", "", "- Executable: `false`", "- No registry entry authorizes real-video target inference or complete-skill/kit registration."])
    return "\n".join(lines) + "\n"


def _validated_handle(entry: dict[str, Any]) -> ReviewedBindingHandle:
    required = [
        "registry_entry_id", "binding_id", "version", "actor_id", "action_category", "binding_scope",
        "binding_type", "binding_data_path", "handler_key", "source_atomic_fact_artifact_path",
        "accepted_atomic_fact_sha256", "source_atomic_fact_ids", "unresolved_atomic_fact_ids",
        "unresolved_fields", "complete_game_skill", "complete_character_kit", "synthetic_only",
        "real_trace_executable", "damage_semantics_status", "toughness_semantics_status",
    ]
    shape_issues = _entry_shape_issues(entry)
    if shape_issues:
        raise ValueError("; ".join(shape_issues))
    if entry["binding_type"] not in SUPPORTED_BINDING_TYPES:
        raise ValueError(f"unsupported binding type {entry['binding_type']!r}.")
    handler_spec = HANDLER_SPECS.get(entry["handler_key"])
    if handler_spec is None:
        raise ValueError(f"unknown handler key {entry['handler_key']!r}.")
    binding_path = _package_path(entry["binding_data_path"])
    atomic_path = _package_path(entry["source_atomic_fact_artifact_path"])
    if not binding_path.is_file():
        raise ValueError(f"binding file does not exist: {binding_path}.")
    if not atomic_path.is_file():
        raise ValueError(f"atomic fact file does not exist: {atomic_path}.")
    actual_digest = hashlib.sha256(atomic_path.read_bytes()).hexdigest()
    if (
        actual_digest != entry["accepted_atomic_fact_sha256"]
        or actual_digest != handler_spec.pinned_atomic_fact_sha256
    ):
        raise ValueError("accepted atomic fact digest mismatch.")
    for field, expected in {
        "complete_game_skill": False, "complete_character_kit": False, "synthetic_only": True,
        "real_trace_executable": False, "damage_semantics_status": "not_implemented",
        "toughness_semantics_status": "not_implemented",
    }.items():
        if entry[field] != expected:
            raise ValueError(f"partial binding {field} must be {expected!r}.")
    if entry["damage_semantics_status"] not in SEMANTICS_STATUSES or entry["toughness_semantics_status"] not in SEMANTICS_STATUSES:
        raise ValueError("unsupported damage/toughness semantics status.")
    binding = load_json(binding_path)
    atoms = load_json(atomic_path)
    handler_spec.validator(binding, atoms, atomic_path)
    handle = ReviewedBindingHandle(
        registry_entry_id=entry["registry_entry_id"], binding_id=entry["binding_id"], version=entry["version"],
        actor_id=entry["actor_id"], action_category=entry["action_category"], binding_scope=entry["binding_scope"],
        binding_type=entry["binding_type"], binding_data_path=binding_path, handler_key=entry["handler_key"],
        source_atomic_fact_artifact_path=atomic_path, accepted_atomic_fact_sha256=entry["accepted_atomic_fact_sha256"],
        source_atomic_fact_ids=tuple(entry["source_atomic_fact_ids"]), unresolved_atomic_fact_ids=tuple(entry["unresolved_atomic_fact_ids"]),
        unresolved_fields=tuple(entry["unresolved_fields"]), complete_game_skill=entry["complete_game_skill"],
        complete_character_kit=entry["complete_character_kit"], synthetic_only=entry["synthetic_only"],
        real_trace_executable=entry["real_trace_executable"], damage_semantics_status=entry["damage_semantics_status"],
        toughness_semantics_status=entry["toughness_semantics_status"],
    )
    _validate_metadata_match(handle, binding)
    return handle


def _validate_metadata_match(handle: ReviewedBindingHandle, binding: dict[str, Any]) -> None:
    comparisons = {
        "binding_id": handle.binding_id, "version": handle.version, "actor_id": handle.actor_id,
        "action_category": handle.action_category, "binding_scope": handle.binding_scope,
        "complete_game_skill": handle.complete_game_skill, "synthetic_only": handle.synthetic_only,
    }
    for field, expected in comparisons.items():
        if binding.get(field) != expected:
            raise ValueError(f"Registry metadata mismatch for binding field {field!r}.")
    if set(binding.get("source_atomic_fact_ids", [])) != set(handle.source_atomic_fact_ids):
        raise ValueError("Registry metadata mismatch for source atomic fact IDs.")
    if set(binding.get("unresolved_atomic_fact_ids", [])) != set(handle.unresolved_atomic_fact_ids):
        raise ValueError("Registry metadata mismatch for unresolved atomic fact IDs.")
    if set(binding.get("unresolved_fields", [])) != set(handle.unresolved_fields):
        raise ValueError("Registry metadata mismatch for unresolved fields.")


def _package_path(value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("registry path must be a nonempty package-relative string.")
    path = (PACKAGE_ROOT / value).resolve()
    if not path.is_relative_to(PACKAGE_ROOT):
        raise ValueError(f"registry path escapes package root: {value!r}.")
    return path


def _entry_shape_issues(entry: Any) -> list[str]:
    if not isinstance(entry, dict):
        return ["entry must be an object."]
    required = STRING_FIELDS | BOOLEAN_FIELDS | LIST_FIELDS
    missing = sorted(field for field in required if field not in entry)
    issues = [f"missing required fields: {missing}."] if missing else []
    for field in sorted(STRING_FIELDS):
        value = entry.get(field)
        if not isinstance(value, str) or not value:
            issues.append(f"{field} must be a non-empty string.")
    digest = entry.get("accepted_atomic_fact_sha256")
    if isinstance(digest, str) and not re.fullmatch(r"[0-9a-f]{64}", digest):
        issues.append("accepted_atomic_fact_sha256 must be 64 lowercase hexadecimal characters.")
    for field in sorted(BOOLEAN_FIELDS):
        if type(entry.get(field)) is not bool:
            issues.append(f"{field} must be a boolean.")
    for field in sorted(LIST_FIELDS):
        value = entry.get(field)
        if not isinstance(value, list):
            issues.append(f"{field} must be a list of non-empty strings.")
            continue
        if any(not isinstance(item, str) or not item for item in value):
            issues.append(f"{field} must contain only non-empty strings.")
            continue
        duplicates = sorted({item for item in value if value.count(item) > 1})
        if duplicates:
            issues.append(f"{field} contains duplicate values: {duplicates}.")
    return issues


def _revalidate_handle(handle: Any) -> ReviewedBindingHandle:
    if not isinstance(handle, ReviewedBindingHandle):
        raise ValueError("Reviewed execution requires a ReviewedBindingHandle.")
    entry = {
        "registry_entry_id": handle.registry_entry_id,
        "binding_id": handle.binding_id,
        "version": handle.version,
        "actor_id": handle.actor_id,
        "action_category": handle.action_category,
        "binding_scope": handle.binding_scope,
        "binding_type": handle.binding_type,
        "binding_data_path": _handle_path_value(handle.binding_data_path, "binding_data_path"),
        "handler_key": handle.handler_key,
        "source_atomic_fact_artifact_path": _handle_path_value(handle.source_atomic_fact_artifact_path, "source_atomic_fact_artifact_path"),
        "accepted_atomic_fact_sha256": handle.accepted_atomic_fact_sha256,
        "source_atomic_fact_ids": _handle_list_value(handle.source_atomic_fact_ids, "source_atomic_fact_ids"),
        "unresolved_atomic_fact_ids": _handle_list_value(handle.unresolved_atomic_fact_ids, "unresolved_atomic_fact_ids"),
        "unresolved_fields": _handle_list_value(handle.unresolved_fields, "unresolved_fields"),
        "complete_game_skill": handle.complete_game_skill,
        "complete_character_kit": handle.complete_character_kit,
        "synthetic_only": handle.synthetic_only,
        "real_trace_executable": handle.real_trace_executable,
        "damage_semantics_status": handle.damage_semantics_status,
        "toughness_semantics_status": handle.toughness_semantics_status,
    }
    return _validated_handle(entry)


def _handle_path_value(value: Any, field: str) -> str:
    if not isinstance(value, Path):
        raise ValueError(f"Reviewed handle {field} must be a Path.")
    try:
        return str(value.resolve().relative_to(PACKAGE_ROOT))
    except ValueError as exc:
        raise ValueError(f"Reviewed handle {field} escapes package root.") from exc


def _handle_list_value(value: Any, field: str) -> list[str]:
    if not isinstance(value, tuple):
        raise ValueError(f"Reviewed handle {field} must be an immutable tuple.")
    return list(value)


def _handler_spec(handler_key: str) -> ReviewedHandlerSpec:
    handler_spec = HANDLER_SPECS.get(handler_key)
    if handler_spec is None:
        raise ValueError(f"Unknown reviewed binding handler key: {handler_key!r}.")
    return handler_spec


def _reject_duplicates(values: list[Any], label: str, issues: list[str]) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        issues.append(f"duplicate {label} IDs: {duplicates}.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit reviewed partial-binding registry.")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--format", choices=["markdown", "json"], required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        registry = load_reviewed_binding_registry(args.registry)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR reviewed binding registry input failure: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"FAIL reviewed binding registry validation: {exc}", file=sys.stderr)
        return 1
    try:
        rendered = render_markdown(build_registry_audit_report(registry)) if args.format == "markdown" else render_json(build_registry_audit_report(registry))
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except OSError as exc:
        print(f"ERROR reviewed binding registry output failure: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"ERROR reviewed binding registry could not run: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
