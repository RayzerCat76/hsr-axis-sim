from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from hsr_axis_sim.real_bindings.registry import load_reviewed_binding_registry
from hsr_axis_sim.tools.trace_tingyun_ultimate_damage_buff_magnitude import (
    build_report as build_magnitude_report,
    render_json as render_magnitude_json,
)
from hsr_axis_sim.tools.trace_tingyun_ultimate_damage_buff_review import (
    build_report as build_historical_review,
    render_json as render_historical_json,
)


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "manual_video_traces"
DEFAULT_REVIEW = BASE / "normalized_character_facts" / "tingyun_ultimate_damage_buff_semantic_readiness_v0_1.json"
WARNING = (
    "NON-EXECUTABLE SEMANTIC READINESS REVIEW. This report does not add a buff, "
    "select a target or trace level, or authorize real-video execution."
)
EXPECTED_INPUTS = {
    "historical_fact_review": "data/manual_video_traces/normalized_character_facts/tingyun_ultimate_damage_buff_review_v0_1.json",
    "magnitude_intake": "data/manual_video_traces/normalized_character_facts/tingyun_ultimate_damage_buff_magnitude_intake_v0_1.json",
    "historical_readiness_report": "data/manual_video_traces/real_binding_audits/tingyun_ultimate_damage_buff_readiness_v0_1.json",
    "magnitude_report": "data/manual_video_traces/real_binding_audits/tingyun_ultimate_damage_buff_magnitude_intake_v0_1.json",
    "source_registry": "data/manual_video_traces/source_registry/sources_v0_1.json",
    "reviewed_binding_registry": "real_bindings/registry_v0_2.json",
}
CLAIM_CONTRACTS = {
    "target_scope": ("verified", "selected_single_ally", "target_scope", None),
    "duration_count": ("verified", 2, "integer", "turn"),
    "magnitude_table": ("verified", "validated_levels_1_through_15", "trace_level_table", "percent"),
    "effect_order": ("unresolved", None, "effect_order", None),
    "same_current_turn_duration": ("unresolved", None, "duration_policy", None),
    "accepted_video_target": ("missing", None, "actor_id", None),
    "accepted_video_trace_level": ("missing", None, "trace_level", None),
}
STATUSES = {"verified", "unresolved", "missing"}
RELATIONSHIPS = {"supports", "does_not_resolve", "limits", "conflicts"}
GENERIC_STATUSES = {
    "ready_for_separate_binding_task",
    "blocked_by_effect_order",
    "blocked_by_duration_semantics",
    "blocked_by_both_semantics",
    "blocked_by_invalid_magnitude_evidence",
}
VIDEO_STATUSES = {
    "ready_for_replay_binding",
    "blocked_by_unknown_target",
    "blocked_by_unknown_trace_level",
    "blocked_by_unknown_target_and_trace_level",
}
FORBIDDEN_KEYS = {
    "effects", "effect", "executor", "handlerkey", "bindingdatapath",
    "characterspec", "skillspec", "addbuff", "realtraceexecutable",
}


@dataclass(frozen=True)
class InputArtifact:
    role: str
    path: str
    sha256: str


@dataclass(frozen=True)
class SemanticProvenance:
    provenance_id: str
    artifact_role: str
    locator: str
    relationship: str
    evidence_summary: str


@dataclass(frozen=True)
class SemanticClaim:
    claim_id: str
    semantic_field: str
    status: str
    normalized_value: Any
    value_type: str
    unit: str | None
    evidence_summary: str
    unresolved_notes: str
    provenance: tuple[SemanticProvenance, ...]
    simulator_binding_allowed: bool


@dataclass(frozen=True)
class InteractionProtocol:
    protocol_id: str
    question: str
    preconditions: tuple[str, ...]
    procedure: tuple[str, ...]
    required_observations: tuple[str, ...]
    result_status: str
    observed_result: None
    simulator_binding_allowed: bool


@dataclass(frozen=True)
class SemanticReadinessReport:
    review_id: str
    version: str
    warning: str
    input_artifacts: tuple[InputArtifact, ...]
    semantic_claims: tuple[SemanticClaim, ...]
    magnitude_levels_validated: tuple[int, ...]
    magnitude_percentages: tuple[float, ...]
    selected_magnitude_level: None
    current_engine_assessment: dict[str, Any]
    generic_binding_readiness: str
    accepted_video_binding_readiness: str
    accepted_video_semantic_readiness: str
    generic_blockers: tuple[str, ...]
    accepted_video_blockers: tuple[str, ...]
    interaction_protocols: tuple[InteractionProtocol, ...]
    simulator_binding_allowed: bool


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def build_report(data: Any, root: str | Path = ROOT) -> SemanticReadinessReport:
    issues: list[str] = []
    if not isinstance(data, dict):
        raise ValueError("Tingyun semantic readiness validation failed:\n- review must be an object.")
    _reject_executable_schema(data, "review", issues)
    for field in ("review_id", "version", "status"):
        _string(data.get(field), field, issues)
    if data.get("status") != "non_executable_semantic_readiness_review":
        issues.append("status must be 'non_executable_semantic_readiness_review'.")
    if data.get("simulator_binding_allowed") is not False:
        issues.append("simulator_binding_allowed must be false.")

    inputs = _input_artifacts(data.get("input_artifacts"), Path(root), issues)
    claims = _claims(data.get("semantic_claims"), inputs, issues)
    engine = _engine_assessment(data.get("current_engine_assessment"), issues)
    protocols = _protocols(data.get("interaction_protocols"), issues)

    magnitude_levels: tuple[int, ...] = ()
    magnitude_percentages: tuple[float, ...] = ()
    if all(role in inputs for role in EXPECTED_INPUTS):
        try:
            magnitude = load_json(Path(root) / inputs["magnitude_intake"].path)
            magnitude_report = build_magnitude_report(magnitude)
            if magnitude_report.intake_status != "captured_exact_table":
                issues.append("magnitude intake must remain captured_exact_table.")
            magnitude_levels = tuple(row["normalized_trace_level"] for row in magnitude_report.normalized_table)
            magnitude_percentages = tuple(row["dmg_increase_percent"] for row in magnitude_report.normalized_table)
            if magnitude_levels != tuple(range(1, 16)):
                issues.append("magnitude intake must contain exact normalized levels 1 through 15.")
            committed_magnitude = (Path(root) / inputs["magnitude_report"].path).read_text(encoding="utf-8")
            if committed_magnitude != render_magnitude_json(magnitude_report):
                issues.append("magnitude report does not match validated magnitude intake.")

            source_data = load_json(Path(root) / inputs["source_registry"].path)
            historical_data = load_json(Path(root) / inputs["historical_fact_review"].path)
            historical = build_historical_review(source_data, historical_data)
            committed_historical = (Path(root) / inputs["historical_readiness_report"].path).read_text(encoding="utf-8")
            if committed_historical != render_historical_json(historical):
                issues.append("historical readiness report does not match its accepted inputs.")
            facts = {fact.fact_id: fact for fact in historical.facts}
            if facts.get("tingyun.ultimate.damage_buff.target_scope", None) is None or facts["tingyun.ultimate.damage_buff.target_scope"].normalized_value != "selected_single_ally":
                issues.append("historical review no longer verifies selected-single-ally target scope.")
            if facts.get("tingyun.ultimate.damage_buff.duration_turns", None) is None or facts["tingyun.ultimate.damage_buff.duration_turns"].normalized_value != 2:
                issues.append("historical review no longer verifies a two-turn duration count.")

            registry = load_reviewed_binding_registry(Path(root) / inputs["reviewed_binding_registry"].path)
            if registry.registry_version != "0.2" or len(registry.bindings) != 2:
                issues.append("reviewed binding registry must remain version 0.2 with exactly two entries.")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            issues.append(f"referenced evidence validation failed: {exc}")

    generic = _generic_readiness(claims, bool(magnitude_levels))
    video = _video_readiness(claims)
    _readiness_field(data, "generic_binding_readiness", GENERIC_STATUSES, generic, issues)
    _readiness_field(data, "accepted_video_binding_readiness", VIDEO_STATUSES, video, issues)
    _readiness_field(data, "accepted_video_semantic_readiness", GENERIC_STATUSES, generic, issues)
    generic_blockers = _string_list(data.get("generic_blockers"), "generic_blockers", issues)
    video_blockers = _string_list(data.get("accepted_video_blockers"), "accepted_video_blockers", issues)
    if data.get("selected_magnitude_level") is not None:
        issues.append("selected_magnitude_level must remain null.")
    if issues:
        raise ValueError("Tingyun semantic readiness validation failed:\n" + "\n".join(f"- {item}" for item in issues))
    return SemanticReadinessReport(
        review_id=data["review_id"], version=data["version"], warning=WARNING,
        input_artifacts=tuple(sorted(inputs.values(), key=lambda item: item.role)),
        semantic_claims=tuple(sorted(claims.values(), key=lambda item: item.claim_id)),
        magnitude_levels_validated=magnitude_levels,
        magnitude_percentages=magnitude_percentages,
        selected_magnitude_level=None,
        current_engine_assessment=engine,
        generic_binding_readiness=generic,
        accepted_video_binding_readiness=video,
        accepted_video_semantic_readiness=generic,
        generic_blockers=tuple(sorted(generic_blockers)),
        accepted_video_blockers=tuple(sorted(video_blockers)),
        interaction_protocols=tuple(sorted(protocols, key=lambda item: item.protocol_id)),
        simulator_binding_allowed=False,
    )


def _input_artifacts(value: Any, root: Path, issues: list[str]) -> dict[str, InputArtifact]:
    if not isinstance(value, list):
        issues.append("input_artifacts must be a list.")
        return {}
    result: dict[str, InputArtifact] = {}
    for index, item in enumerate(value):
        label = f"input_artifacts[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{label} must be an object.")
            continue
        role, path, digest = item.get("role"), item.get("path"), item.get("sha256")
        for field, raw in (("role", role), ("path", path), ("sha256", digest)):
            _string(raw, f"{label}.{field}", issues)
        if not all(isinstance(raw, str) and raw for raw in (role, path, digest)):
            continue
        if role in result:
            issues.append(f"duplicate input artifact role {role!r}.")
            continue
        if role not in EXPECTED_INPUTS:
            issues.append(f"unsupported input artifact role {role!r}.")
            continue
        if path != EXPECTED_INPUTS[role]:
            issues.append(f"{label}.path must be {EXPECTED_INPUTS[role]!r}.")
            continue
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            issues.append(f"{label}.sha256 must be a lowercase SHA-256 digest.")
            continue
        file_path = root / path
        try:
            actual = hashlib.sha256(file_path.read_bytes()).hexdigest()
        except OSError as exc:
            issues.append(f"{label} cannot read referenced artifact: {exc}")
            continue
        if actual != digest:
            issues.append(f"{label}.sha256 does not match referenced artifact.")
            continue
        result[role] = InputArtifact(role, path, digest)
    if set(result) != set(EXPECTED_INPUTS):
        issues.append("input_artifacts must contain the exact required artifact roles.")
    return result


def _claims(value: Any, inputs: dict[str, InputArtifact], issues: list[str]) -> dict[str, SemanticClaim]:
    if not isinstance(value, list):
        issues.append("semantic_claims must be a list.")
        return {}
    result: dict[str, SemanticClaim] = {}
    provenance_ids: set[str] = set()
    for index, item in enumerate(value):
        label = f"semantic_claims[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{label} must be an object.")
            continue
        for field in ("claim_id", "semantic_field", "status", "value_type", "evidence_summary", "unresolved_notes"):
            _string(item.get(field), f"{label}.{field}", issues)
        claim_id = item.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id:
            continue
        if claim_id in result:
            issues.append(f"duplicate semantic claim ID {claim_id!r}.")
            continue
        contract = CLAIM_CONTRACTS.get(claim_id)
        if contract is None:
            issues.append(f"unsupported semantic claim ID {claim_id!r}.")
            continue
        status, expected_value, value_type, unit = contract
        if item.get("semantic_field") != claim_id:
            issues.append(f"{label}.semantic_field must be {claim_id!r}.")
        raw_status = item.get("status")
        if not isinstance(raw_status, str) or not raw_status:
            pass
        elif raw_status not in STATUSES or raw_status != status:
            issues.append(f"{label}.status must be {status!r}.")
        if item.get("normalized_value") != expected_value or type(item.get("normalized_value")) is not type(expected_value):
            issues.append(f"{label}.normalized_value must be {expected_value!r} with exact type.")
        if item.get("value_type") != value_type or item.get("unit") != unit:
            issues.append(f"{label} value_type/unit do not match the semantic contract.")
        if item.get("simulator_binding_allowed") is not False:
            issues.append(f"{label}.simulator_binding_allowed must be false.")
        provenance = _provenance(item.get("provenance"), label, inputs, provenance_ids, issues)
        result[claim_id] = SemanticClaim(
            claim_id, claim_id, status, expected_value, value_type, unit,
            item.get("evidence_summary", ""), item.get("unresolved_notes", ""),
            tuple(sorted(provenance, key=lambda row: row.provenance_id)), False,
        )
    if set(result) != set(CLAIM_CONTRACTS):
        issues.append("semantic_claims must contain the exact required claims.")
    return result


def _provenance(value: Any, label: str, inputs: dict[str, InputArtifact], seen: set[str], issues: list[str]) -> list[SemanticProvenance]:
    if not isinstance(value, list) or not value:
        issues.append(f"{label}.provenance must be a non-empty list.")
        return []
    result: list[SemanticProvenance] = []
    for index, item in enumerate(value):
        item_label = f"{label}.provenance[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{item_label} must be an object.")
            continue
        for field in ("provenance_id", "artifact_role", "locator", "relationship", "evidence_summary"):
            _string(item.get(field), f"{item_label}.{field}", issues)
        values = [item.get(field) for field in ("provenance_id", "artifact_role", "locator", "relationship", "evidence_summary")]
        if not all(isinstance(raw, str) and raw for raw in values):
            continue
        provenance_id, role, locator, relationship, summary = values
        if provenance_id in seen:
            issues.append(f"duplicate provenance ID {provenance_id!r}.")
            continue
        seen.add(provenance_id)
        if role not in inputs:
            issues.append(f"{item_label}.artifact_role has no validated input artifact.")
        if relationship not in RELATIONSHIPS:
            issues.append(f"{item_label}.relationship is unsupported.")
        if relationship == "conflicts":
            issues.append(f"{item_label} contains conflicting semantic evidence.")
        result.append(SemanticProvenance(provenance_id, role, locator, relationship, summary))
    return result


def _engine_assessment(value: Any, issues: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        issues.append("current_engine_assessment must be an object.")
        return {}
    expected = {
        "duration_type": "target_normal_turns",
        "duration_count": 2,
        "cast_interrupt_decrements": False,
        "already_active_target_turn_decrements_at_end": True,
        "extra_turn_decrements": False,
        "non_ending_action_decrements": False,
        "game_equivalence_verified": False,
    }
    for field, expected_value in expected.items():
        actual = value.get(field)
        if type(actual) is not type(expected_value) or actual != expected_value:
            issues.append(f"current_engine_assessment.{field} must be {expected_value!r} with exact type.")
    for field in ("expiration_boundary", "assessment_notes"):
        _string(value.get(field), f"current_engine_assessment.{field}", issues)
    return {**expected, "expiration_boundary": value.get("expiration_boundary", ""), "assessment_notes": value.get("assessment_notes", "")}


def _protocols(value: Any, issues: list[str]) -> list[InteractionProtocol]:
    if not isinstance(value, list):
        issues.append("interaction_protocols must be a list.")
        return []
    result: list[InteractionProtocol] = []
    ids: set[str] = set()
    for index, item in enumerate(value):
        label = f"interaction_protocols[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{label} must be an object.")
            continue
        for field in ("protocol_id", "question", "result_status"):
            _string(item.get(field), f"{label}.{field}", issues)
        protocol_id = item.get("protocol_id")
        if not isinstance(protocol_id, str) or not protocol_id:
            continue
        if protocol_id in ids:
            issues.append(f"duplicate protocol ID {protocol_id!r}.")
            continue
        ids.add(protocol_id)
        preconditions = _string_list(item.get("preconditions"), f"{label}.preconditions", issues)
        procedure = _string_list(item.get("procedure"), f"{label}.procedure", issues)
        observations = _string_list(item.get("required_observations"), f"{label}.required_observations", issues)
        if item.get("result_status") != "not_run" or item.get("observed_result") is not None:
            issues.append(f"{label} must remain an unrun evidence protocol.")
        if item.get("simulator_binding_allowed") is not False:
            issues.append(f"{label}.simulator_binding_allowed must be false.")
        result.append(InteractionProtocol(protocol_id, item.get("question", ""), tuple(sorted(preconditions)), tuple(procedure), tuple(sorted(observations)), "not_run", None, False))
    if ids != {"effect_order_controlled_interaction", "same_current_turn_duration_controlled_interaction"}:
        issues.append("interaction_protocols must contain the exact two required protocols.")
    return result


def _generic_readiness(claims: dict[str, SemanticClaim], magnitude_valid: bool) -> str:
    if not magnitude_valid:
        return "blocked_by_invalid_magnitude_evidence"
    order_gap = claims.get("effect_order", None) is None or claims["effect_order"].status != "verified"
    duration_gap = claims.get("same_current_turn_duration", None) is None or claims["same_current_turn_duration"].status != "verified"
    if order_gap and duration_gap:
        return "blocked_by_both_semantics"
    if order_gap:
        return "blocked_by_effect_order"
    if duration_gap:
        return "blocked_by_duration_semantics"
    return "ready_for_separate_binding_task"


def _video_readiness(claims: dict[str, SemanticClaim]) -> str:
    target_missing = claims.get("accepted_video_target", None) is None or claims["accepted_video_target"].status != "verified"
    level_missing = claims.get("accepted_video_trace_level", None) is None or claims["accepted_video_trace_level"].status != "verified"
    if target_missing and level_missing:
        return "blocked_by_unknown_target_and_trace_level"
    if target_missing:
        return "blocked_by_unknown_target"
    if level_missing:
        return "blocked_by_unknown_trace_level"
    return "ready_for_replay_binding"


def _readiness_field(data: dict[str, Any], field: str, vocabulary: set[str], computed: str, issues: list[str]) -> None:
    value = data.get(field)
    if not isinstance(value, str) or not value:
        issues.append(f"{field} must be a non-empty string.")
    elif value not in vocabulary:
        issues.append(f"{field} is unsupported.")
    elif value != computed:
        issues.append(f"{field} must match computed status {computed!r}.")


def _string(value: Any, label: str, issues: list[str]) -> None:
    if not isinstance(value, str) or not value:
        issues.append(f"{label} must be a non-empty string.")


def _string_list(value: Any, label: str, issues: list[str]) -> list[str]:
    if not isinstance(value, list) or not value:
        issues.append(f"{label} must be a non-empty list of non-empty strings.")
        return []
    if any(not isinstance(item, str) or not item for item in value):
        issues.append(f"{label} must contain only non-empty strings.")
        return []
    if len(set(value)) != len(value):
        issues.append(f"{label} must not contain duplicates.")
    return value


def _reject_executable_schema(value: Any, label: str, issues: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z]", "", str(key).lower())
            if normalized in FORBIDDEN_KEYS:
                issues.append(f"{label}.{key} is an executable schema key and is forbidden.")
            _reject_executable_schema(child, f"{label}.{key}", issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_executable_schema(child, f"{label}[{index}]", issues)


def render_json(report: SemanticReadinessReport) -> str:
    return json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n"


def render_markdown(report: SemanticReadinessReport) -> str:
    lines = [
        "# Tingyun Ultimate DMG-Buff Semantic Readiness Review", "", f"> {report.warning}", "",
        "## Readiness Axes", "",
        f"- Generic binding: `{report.generic_binding_readiness}`",
        f"- Accepted video binding: `{report.accepted_video_binding_readiness}`",
        f"- Accepted video semantic readiness: `{report.accepted_video_semantic_readiness}`",
        "- Simulator binding allowed: `false`", "",
        "## Validated Inputs", "", "| Role | Path | SHA-256 |", "|---|---|---|",
    ]
    for item in report.input_artifacts:
        lines.append(f"| {item.role} | `{item.path}` | `{item.sha256}` |")
    lines.extend(["", "## Semantic Claims", "", "| Field | Status | Value |", "|---|---|---|"])
    for claim in report.semantic_claims:
        value = "null" if claim.normalized_value is None else json.dumps(claim.normalized_value, ensure_ascii=False)
        lines.append(f"| {claim.semantic_field} | {claim.status} | {value} |")
    lines.extend(["", "## Magnitude Integration", "",
                  f"- Validated levels: `{', '.join(map(str, report.magnitude_levels_validated))}`",
                  f"- Percentages: `{', '.join(map(str, report.magnitude_percentages))}`",
                  "- Selected magnitude level: `null`", "",
                  "## Current Engine Boundary", ""])
    for key, value in report.current_engine_assessment.items():
        lines.append(f"- {key}: `{json.dumps(value, ensure_ascii=False)}`")
    lines.extend(["", "## Blockers", "", "Generic:"])
    lines.extend(f"- {item}" for item in report.generic_blockers)
    lines.append("")
    lines.append("Accepted video:")
    lines.extend(f"- {item}" for item in report.accepted_video_blockers)
    lines.extend(["", "## Controlled Interaction Protocols", ""])
    for protocol in report.interaction_protocols:
        lines.extend([f"### {protocol.protocol_id}", "", protocol.question, "", "Result: `not_run`", ""])
        lines.extend(f"1. {step}" for step in protocol.procedure)
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate non-executable Tingyun Ultimate DMG-buff semantic readiness.")
    parser.add_argument("--review", default=str(DEFAULT_REVIEW))
    parser.add_argument("--format", choices=["markdown", "json"], required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        data = load_json(args.review)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR Tingyun semantic readiness input failure: {exc}", file=sys.stderr)
        return 2
    try:
        report = build_report(data)
    except ValueError as exc:
        print(f"FAIL Tingyun semantic readiness validation: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR Tingyun semantic readiness could not run: {exc}", file=sys.stderr)
        return 2
    rendered = render_markdown(report) if args.format == "markdown" else render_json(report)
    try:
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except OSError as exc:
        print(f"ERROR Tingyun semantic readiness output failure: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
