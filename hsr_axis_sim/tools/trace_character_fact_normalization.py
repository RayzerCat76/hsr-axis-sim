from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ACTION_CATEGORIES = {"technique_attack", "basic_attack", "skill", "ultimate", "summon_skill", "memosprite_skill", "passive_trigger"}
TARGET_SCOPES = {"self", "single_ally", "single_enemy", "all_allies", "all_enemies", "random_enemy", "bounce_from_selected_enemy", "companion_mem", "unknown"}
RESOURCE_KINDS = {"skill_point", "energy", "charge", "none"}
TIMING_CLASSIFICATIONS = {"normal_action", "ultimate_interrupt", "immediate_action_self", "action_advance_target", "additional_skill_cast", "non_recursive_additional_cast", "unknown"}
DURATION_ANCHORS = {"target_turn_end", "target_turn_start", "source_turn_end", "source_turn_start", "fixed_turn_count", "until_target_turn_start", "unknown"}
VERIFICATION_STATUSES = {"verified_official", "verified_structured_data", "corroborated", "single_source_unverified", "version_ambiguous", "conflicting", "missing", "not_applicable"}
READINESS_STATUSES = {"not_ready", "source_ready_trace_blocked", "source_and_trace_ready_engine_review_required"}
RESOLVED_STATUSES = {"verified_official", "verified_structured_data", "corroborated"}
PARTIAL_STATUSES = {"single_source_unverified", "version_ambiguous"}
FORBIDDEN_KEYS = {"characterspec", "skillspec", "effect", "effects", "trigger", "triggerspec", "actiondefinition", "executableaction"}
DEFAULT_ATOMIC_FACTS_PATH = Path(__file__).resolve().parents[1] / "data" / "manual_video_traces" / "normalized_character_facts" / "real_video_trace_001_atomic_facts_v0_1.json"
WARNING = "Non-executable atomic fact normalization only. No record is a character kit, effect, trigger, executable action, or simulator-binding authorization."


@dataclass(frozen=True)
class AtomicFactProvenance:
    source_registry_fact_id: str
    source_id: str
    relationship: str
    evidence_summary: str


@dataclass(frozen=True)
class NormalizedResourceChange:
    resource_kind: str
    amount: int | float | None
    unit: str


@dataclass(frozen=True)
class NormalizedDuration:
    value: int | float | None
    unit: str
    anchor: str


@dataclass(frozen=True)
class NormalizedTimingClassification:
    classification: str


@dataclass(frozen=True)
class NormalizedToughnessValue:
    source_native_value: int | float
    source_native_unit: str
    normalized_value: int | float | None
    normalized_unit: str | None
    conversion_rule: str | None
    ambiguity_note: str


@dataclass(frozen=True)
class AtomicCharacterFact:
    atomic_fact_id: str
    source_registry_fact_ids: list[str]
    internal_actor_id: str
    action_scope: str
    normalized_field_name: str
    normalized_value: Any
    value_type: str
    unit: str | None
    source_native_value: Any
    verification_status: str
    provenance: list[AtomicFactProvenance]
    version_applicability: str
    trace_link: dict[str, Any]
    unresolved_notes: str | None
    simulator_binding_allowed: bool
    action_category: str | None = None
    target_scope: str | None = None
    resource_change: NormalizedResourceChange | None = None
    duration: NormalizedDuration | None = None
    timing: NormalizedTimingClassification | None = None
    toughness: NormalizedToughnessValue | None = None


@dataclass(frozen=True)
class TraceActionBindingReadiness:
    location: str
    step: int | None
    actor: str
    action: str
    required_atomic_fact_ids: list[str]
    source_resolved_atomic_fact_ids: list[str]
    partial_atomic_fact_ids: list[str]
    missing_or_conflicting_atomic_fact_ids: list[str]
    trace_observation_blockers: list[str]
    source_version_blockers: list[str]
    engine_capability_blockers: list[str]
    readiness_status: str
    simulator_binding_allowed: bool


@dataclass(frozen=True)
class CharacterFactNormalizationReport:
    normalization_id: str
    version: str
    policy: dict[str, Any]
    vocabularies: dict[str, list[str]]
    atomic_facts: list[AtomicCharacterFact]
    readiness: list[TraceActionBindingReadiness]
    candidate_later_review_actions: list[str]
    counts: dict[str, int]


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as json_file:
        value = json.load(json_file)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def build_normalization_report(source_registry: dict[str, Any], gap_inventory: dict[str, Any], atomic_data: dict[str, Any]) -> CharacterFactNormalizationReport:
    _validate_inputs(source_registry, gap_inventory, atomic_data)
    atoms = sorted((_atomic_model(item) for item in atomic_data["atomic_facts"]), key=lambda item: item.atomic_fact_id)
    readiness = _build_readiness(source_registry, gap_inventory, atoms)
    counts = {
        "atomic_facts": len(atoms), "readiness_items": len(readiness),
        "source_resolved": sum(item.verification_status in RESOLVED_STATUSES for item in atoms),
        "partial": sum(item.verification_status in PARTIAL_STATUSES for item in atoms),
        "missing_or_conflicting": sum(item.verification_status in {"missing", "conflicting"} for item in atoms),
    }
    return CharacterFactNormalizationReport(
        normalization_id=atomic_data["normalization_id"], version=atomic_data["version"],
        policy={"non_executable": True, "simulator_binding_allowed": False, "warning": WARNING},
        vocabularies={
            "action_categories": sorted(ACTION_CATEGORIES), "target_scopes": sorted(TARGET_SCOPES),
            "resource_kinds": sorted(RESOURCE_KINDS), "timing_classifications": sorted(TIMING_CLASSIFICATIONS),
            "duration_anchors": sorted(DURATION_ANCHORS), "readiness_statuses": sorted(READINESS_STATUSES),
        },
        atomic_facts=atoms, readiness=readiness,
        candidate_later_review_actions=sorted(atomic_data["candidate_later_review_actions"]), counts=counts,
    )


def report_to_dict(report: CharacterFactNormalizationReport) -> dict[str, Any]:
    return asdict(report)


def render_json(report: CharacterFactNormalizationReport) -> str:
    return json.dumps(report_to_dict(report), ensure_ascii=False, indent=2) + "\n"


def render_markdown(report: CharacterFactNormalizationReport) -> str:
    lines = [f"# Atomic Character Fact Binding Readiness: {report.normalization_id}", "", f"> {report.policy['warning']}", "", "## Normalization Vocabularies", ""]
    for name, values in report.vocabularies.items():
        lines.append(f"- {name}: {', '.join(values)}")
    lines.extend(["", "## Atomic Facts", "", "| Fact | Actor | Action | Field | Value | Status | Sources |", "|---|---|---|---|---|---|---|"])
    for fact in report.atomic_facts:
        value = "null" if fact.normalized_value is None else json.dumps(fact.normalized_value, ensure_ascii=False, sort_keys=True)
        lines.append(f"| {fact.atomic_fact_id} | {fact.internal_actor_id} | {fact.action_scope} | {fact.normalized_field_name} | {value} | {fact.verification_status} | {', '.join(item.source_id for item in fact.provenance) or 'None'} |")
    lines.extend(["", "## Exact Field Provenance", ""])
    for fact in report.atomic_facts:
        lines.extend([f"### {fact.atomic_fact_id}", "", f"- Registry fact(s): {', '.join(fact.source_registry_fact_ids)}", f"- Provenance: {'; '.join(f'{item.source_id}: {item.evidence_summary}' for item in fact.provenance) or 'None'}", f"- Version: {fact.version_applicability}", f"- Unresolved: {fact.unresolved_notes or 'None'}", "- Simulator binding allowed: `false`", ""])
    toughness = [fact for fact in report.atomic_facts if fact.toughness]
    lines.extend(["## Toughness Source Conventions", ""])
    for fact in toughness:
        value = fact.toughness
        lines.append(f"- {fact.atomic_fact_id}: native `{value.source_native_value}` in `{value.source_native_unit}`; normalized `{value.normalized_value}`; {value.ambiguity_note}")
    lines.extend(["", "## Mem Timing and Charge Separation", ""])
    for fact in report.atomic_facts:
        if fact.internal_actor_id == "mem":
            lines.append(f"- {fact.atomic_fact_id}: `{fact.normalized_field_name}` = `{fact.normalized_value}` ({fact.verification_status})")
    lines.extend(["", "## Binding Readiness Matrix", "", "| Item | Actor | Action | Resolved | Partial | Missing/conflicting | Status |", "|---|---|---|---:|---:|---:|---|"])
    for item in report.readiness:
        lines.append(f"| {item.location} | {item.actor} | {item.action} | {len(item.source_resolved_atomic_fact_ids)} | {len(item.partial_atomic_fact_ids)} | {len(item.missing_or_conflicting_atomic_fact_ids)} | {item.readiness_status} |")
    lines.extend(["", "## Readiness Blockers", ""])
    for item in report.readiness:
        lines.extend([f"### {item.location}: {item.actor} / {item.action}", "", f"- Trace blockers: {'; '.join(item.trace_observation_blockers) or 'None'}", f"- Source/version blockers: {'; '.join(item.source_version_blockers) or 'None'}", f"- Engine review blockers: {'; '.join(item.engine_capability_blockers)}", "- Simulator binding allowed: `false`", ""])
    lines.extend(["## Candidate Actions for Later Binding Review", ""])
    lines.extend(f"- {item}" for item in report.candidate_later_review_actions)
    return "\n".join(lines) + "\n"


def _atomic_model(item: dict[str, Any]) -> AtomicCharacterFact:
    return AtomicCharacterFact(
        atomic_fact_id=item["atomic_fact_id"], source_registry_fact_ids=list(item["source_registry_fact_ids"]),
        internal_actor_id=item["internal_actor_id"], action_scope=item["action_scope"],
        normalized_field_name=item["normalized_field_name"], normalized_value=item["normalized_value"],
        value_type=item["value_type"], unit=item.get("unit"), source_native_value=item.get("source_native_value"),
        verification_status=item["verification_status"], provenance=[AtomicFactProvenance(**entry) for entry in item["provenance"]],
        version_applicability=item["version_applicability"], trace_link=dict(item["trace_link"]),
        unresolved_notes=item.get("unresolved_notes"), simulator_binding_allowed=item["simulator_binding_allowed"],
        action_category=item.get("action_category"), target_scope=item.get("target_scope"),
        resource_change=NormalizedResourceChange(**item["resource_change"]) if item.get("resource_change") else None,
        duration=NormalizedDuration(**item["duration"]) if item.get("duration") else None,
        timing=NormalizedTimingClassification(**item["timing"]) if item.get("timing") else None,
        toughness=NormalizedToughnessValue(**item["toughness"]) if item.get("toughness") else None,
    )


def _build_readiness(source_registry: dict[str, Any], gap: dict[str, Any], atoms: list[AtomicCharacterFact]) -> list[TraceActionBindingReadiness]:
    gap_items = [("prebattle", item) for item in gap["prebattle"]] + [(f"step_{item['step']}", item) for item in gap["steps"]]
    readiness = []
    for location, gap_item in gap_items:
        linked = [fact for fact in atoms if fact.trace_link.get("step") == gap_item.get("step") and fact.trace_link["actor"] == gap_item["actor"] and fact.trace_link["action"] == gap_item["action"]]
        resolved = sorted(fact.atomic_fact_id for fact in linked if fact.verification_status in RESOLVED_STATUSES)
        partial = sorted(fact.atomic_fact_id for fact in linked if fact.verification_status in PARTIAL_STATUSES)
        missing = sorted(fact.atomic_fact_id for fact in linked if fact.verification_status in {"missing", "conflicting"})
        trace_blockers = sorted(set(gap_item.get("evidence_limitations", []) + gap_item.get("missing_initial_state", [])))
        if "unknown" in gap_item.get("target_status", ""):
            trace_blockers.append(gap_item["target_status"])
        source_blockers = sorted(filter(None, (fact.unresolved_notes for fact in linked if fact.verification_status not in RESOLVED_STATUSES)))
        engine_blockers = ["Character-specific binding and engine capability review have not been performed."]
        status = "not_ready" if missing or partial else "source_ready_trace_blocked" if trace_blockers else "source_and_trace_ready_engine_review_required"
        readiness.append(TraceActionBindingReadiness(
            location=location, step=gap_item.get("step"), actor=gap_item["actor"], action=gap_item["action"],
            required_atomic_fact_ids=sorted(fact.atomic_fact_id for fact in linked), source_resolved_atomic_fact_ids=resolved,
            partial_atomic_fact_ids=partial, missing_or_conflicting_atomic_fact_ids=missing,
            trace_observation_blockers=trace_blockers, source_version_blockers=source_blockers,
            engine_capability_blockers=engine_blockers, readiness_status=status, simulator_binding_allowed=False,
        ))
    return readiness


def _validate_inputs(registry: dict[str, Any], gap: dict[str, Any], atomic_data: dict[str, Any]) -> None:
    issues: list[str] = []
    _reject_forbidden(atomic_data, "atomic_data", issues)
    registry_facts = {item["fact_id"]: item for item in registry.get("facts", [])}
    sources = {item["source_id"]: item for item in registry.get("sources", [])}
    atoms = atomic_data.get("atomic_facts")
    if not isinstance(atoms, list):
        raise ValueError("atomic_data.atomic_facts must be a list.")
    ids = [item.get("atomic_fact_id") for item in atoms]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        issues.append(f"Duplicate atomic fact IDs: {duplicates}.")
    gap_keys = {(item.get("step"), item["actor"], item["action"]) for item in [*gap.get("prebattle", []), *gap.get("steps", [])]}
    linked_keys: set[tuple[Any, str, str]] = set()
    for index, atom in enumerate(atoms):
        label = f"atomic_facts[{index}]"
        status = atom.get("verification_status")
        if status not in VERIFICATION_STATUSES:
            issues.append(f"{label}.verification_status is unsupported.")
        if atom.get("simulator_binding_allowed") is not False:
            issues.append(f"{label}.simulator_binding_allowed must be false.")
        if status == "missing" and atom.get("normalized_value") is not None:
            issues.append(f"{label} missing fact must have normalized_value null.")
        parent_ids = atom.get("source_registry_fact_ids", [])
        if any(parent_id not in registry_facts for parent_id in parent_ids):
            issues.append(f"{label} has dangling source-registry fact reference.")
        provenance = atom.get("provenance", [])
        if any(entry.get("source_id") not in sources for entry in provenance):
            issues.append(f"{label} has dangling source reference.")
        if status == "corroborated" and len({entry.get("source_id") for entry in provenance if entry.get("relationship") == "supports_exact_field"}) < 2:
            issues.append(f"{label} corroborated status requires two exact-field sources.")
        if status == "verified_structured_data" and not any(sources.get(entry.get("source_id"), {}).get("source_type") == "structured_game_database" and entry.get("relationship") == "supports_exact_field" for entry in provenance):
            issues.append(f"{label} structured verification requires exact structured provenance.")
        if status == "conflicting" and len({entry.get("source_id") for entry in provenance if entry.get("relationship") == "conflicts"}) < 2:
            issues.append(f"{label} conflicting status requires two conflicts.")
        for field, allowed in [("action_category", ACTION_CATEGORIES), ("target_scope", TARGET_SCOPES)]:
            if atom.get(field) is not None and atom[field] not in allowed:
                issues.append(f"{label}.{field} is unsupported.")
        if atom.get("resource_change") and atom["resource_change"].get("resource_kind") not in RESOURCE_KINDS:
            issues.append(f"{label}.resource_change.resource_kind is unsupported.")
        if atom.get("timing") and atom["timing"].get("classification") not in TIMING_CLASSIFICATIONS:
            issues.append(f"{label}.timing.classification is unsupported.")
        if atom.get("duration") and atom["duration"].get("anchor") not in DURATION_ANCHORS:
            issues.append(f"{label}.duration.anchor is unsupported.")
        toughness = atom.get("toughness")
        if toughness and toughness.get("normalized_value") is not None and not toughness.get("conversion_rule"):
            issues.append(f"{label} toughness normalization requires a documented conversion rule.")
        link = atom.get("trace_link", {})
        key = (link.get("step"), link.get("actor"), link.get("action"))
        if key not in gap_keys:
            issues.append(f"{label} trace link does not match gap inventory.")
        linked_keys.add(key)
    if gap_keys - linked_keys:
        issues.append(f"Atomic facts do not cover trace items: {sorted(gap_keys - linked_keys)}.")
    if issues:
        raise ValueError("Character fact normalization validation failed:\n" + "\n".join(f"- {issue}" for issue in issues))


def _reject_forbidden(value: Any, label: str, issues: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if re.sub(r"[^a-z]", "", key.lower()) in FORBIDDEN_KEYS:
                issues.append(f"{label}.{key} is an executable schema key and is forbidden.")
            _reject_forbidden(child, f"{label}.{key}", issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden(child, f"{label}[{index}]", issues)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render non-executable atomic character fact readiness.")
    parser.add_argument("--source-registry", required=True)
    parser.add_argument("--gap-inventory", required=True)
    parser.add_argument("--format", choices=["markdown", "json"], required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        registry = load_json(args.source_registry)
        gap = load_json(args.gap_inventory)
        atomic_data = load_json(DEFAULT_ATOMIC_FACTS_PATH)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR character fact normalization input failure: {exc}", file=sys.stderr)
        return 2
    try:
        report = build_normalization_report(registry, gap, atomic_data)
    except ValueError as exc:
        print(f"FAIL character fact normalization validation: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR character fact normalization could not run: {exc}", file=sys.stderr)
        return 2
    rendered = render_markdown(report) if args.format == "markdown" else render_json(report)
    try:
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except OSError as exc:
        print(f"ERROR character fact normalization output failure: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
