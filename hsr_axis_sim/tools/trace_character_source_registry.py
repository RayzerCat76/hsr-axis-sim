from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SOURCE_TYPES = {
    "official_game_text", "official_web", "structured_game_database",
    "manual_video_evidence", "community_mechanics_reference",
}
VERIFICATION_STATUSES = {
    "verified_official", "verified_structured_data", "corroborated",
    "single_source_unverified", "version_ambiguous", "conflicting", "missing",
    "not_applicable",
}
QUALIFYING_VERIFIED = {
    "verified_official": {"official_game_text", "official_web"},
    "verified_structured_data": {"structured_game_database"},
}
FORBIDDEN_SCHEMA_KEYS = {
    "characterspec", "skillspec", "effect", "effects", "triggerspec",
    "actiondefinition", "executableeffects",
}
WARNING = (
    "Non-executable source registry only. Sourced facts are provenance records, not "
    "simulator bindings or character-kit implementations."
)


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    title: str
    publisher: str
    source_type: str
    locator: str
    language: str
    game_version: str | None
    retrieval_date: str
    qualification_notes: str


@dataclass(frozen=True)
class CharacterIdentityRecord:
    internal_actor_id: str
    canonical_chinese_name: str
    canonical_english_name: str
    aliases: list[str]
    character_game_data_id: str | None
    identity_verification_status: str
    source_ids: list[str]


@dataclass(frozen=True)
class FactProvenance:
    source_id: str
    relationship: str
    evidence_summary: str


@dataclass(frozen=True)
class TraceRequirementLink:
    location: str
    step: int | None
    actor: str
    action: str
    gap_categories: list[str]


@dataclass(frozen=True)
class FactRecord:
    fact_id: str
    internal_actor_id: str
    action_scope: str
    field_name: str
    value: Any
    value_type: str
    unit: str | None
    verification_status: str
    provenance: list[FactProvenance]
    game_version_applicability: str
    language: str
    evidence_summary: str
    unresolved_notes: str | None
    links: list[TraceRequirementLink]
    simulator_binding_allowed: bool


@dataclass(frozen=True)
class SourceConflict:
    fact_id: str
    source_ids: list[str]
    summary: str


@dataclass(frozen=True)
class SourceRegistryReport:
    registry_id: str
    version: str
    policy: dict[str, Any]
    sources: list[SourceRecord]
    identities: list[CharacterIdentityRecord]
    facts: list[FactRecord]
    coverage: list[dict[str, Any]]
    conflicts: list[SourceConflict]
    unresolved_source_gaps: list[str]
    recommended_research_actions: list[str]
    fact_counts: dict[str, int]


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as json_file:
        value = json.load(json_file)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def build_source_registry_report(
    evidence: dict[str, Any], gap_inventory: dict[str, Any], sources_data: dict[str, Any], facts_data: dict[str, Any]
) -> SourceRegistryReport:
    _validate_inputs(evidence, gap_inventory, sources_data, facts_data)
    sources = sorted((SourceRecord(**item) for item in sources_data["sources"]), key=lambda item: item.source_id)
    identities = sorted((CharacterIdentityRecord(**item) for item in facts_data["identities"]), key=lambda item: item.internal_actor_id)
    facts = sorted((_fact_model(item) for item in facts_data["facts"]), key=lambda item: item.fact_id)
    coverage = _build_coverage(evidence, facts)
    conflicts = [
        SourceConflict(
            fact_id=fact.fact_id,
            source_ids=sorted(item.source_id for item in fact.provenance if item.relationship == "conflicts"),
            summary=fact.unresolved_notes or "Conflicting provenance remains unresolved.",
        )
        for fact in facts if fact.verification_status == "conflicting"
    ]
    unresolved = sorted(fact.fact_id for fact in facts if fact.verification_status in {"missing", "conflicting", "version_ambiguous"})
    counts = {status: sum(fact.verification_status == status for fact in facts) for status in sorted(VERIFICATION_STATUSES)}
    return SourceRegistryReport(
        registry_id=facts_data["registry_id"], version=facts_data["version"],
        policy={"non_executable": True, "simulator_binding_allowed": False, "warning": WARNING},
        sources=sources, identities=identities, facts=facts, coverage=coverage,
        conflicts=conflicts, unresolved_source_gaps=unresolved,
        recommended_research_actions=sorted(facts_data["recommended_research_actions"]),
        fact_counts=counts,
    )


def report_to_dict(report: SourceRegistryReport) -> dict[str, Any]:
    return asdict(report)


def render_json(report: SourceRegistryReport) -> str:
    return json.dumps(report_to_dict(report), ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def render_markdown(report: SourceRegistryReport) -> str:
    lines = [
        f"# Character Source Registry: {report.registry_id}", "",
        f"> {report.policy['warning']}", "", "## Source Catalog", "",
        "| Source ID | Type | Publisher | Version | Language | Locator |", "|---|---|---|---|---|---|",
    ]
    for source in report.sources:
        lines.append(f"| {source.source_id} | {source.source_type} | {source.publisher} | {source.game_version or 'unknown'} | {source.language} | {source.locator} |")
    lines.extend(["", "## Character Identity and Aliases", "", "| Internal ID | Chinese | English | Aliases | Data ID | Status |", "|---|---|---|---|---|---|"])
    for identity in report.identities:
        lines.append(f"| {identity.internal_actor_id} | {identity.canonical_chinese_name} | {identity.canonical_english_name} | {', '.join(identity.aliases)} | {identity.character_game_data_id or 'unresolved'} | {identity.identity_verification_status} |")
    lines.extend(["", "## Coverage by Trace Item", "", "| Item | Actor | Action | Verified | Partial | Missing/conflicting | Blocker resolution |", "|---|---|---|---:|---:|---:|---|"])
    for item in report.coverage:
        lines.append(f"| {item['location']} | {item['actor']} | {item['action']} | {len(item['verified_fact_ids'])} | {len(item['partial_fact_ids'])} | {len(item['unresolved_fact_ids'])} | {item['blocker_resolution']} |")
    lines.extend(["", "## Field-Level Fact Provenance", ""])
    for fact in report.facts:
        value = "null" if fact.value is None else json.dumps(fact.value, ensure_ascii=False, sort_keys=True)
        lines.extend([
            f"### {fact.fact_id}", "",
            f"- Actor/action: `{fact.internal_actor_id}` / `{fact.action_scope}`",
            f"- Field: `{fact.field_name}` = {value}",
            f"- Status: `{fact.verification_status}`; version: {fact.game_version_applicability}",
            f"- Evidence: {fact.evidence_summary}",
            f"- Provenance: {', '.join(item.source_id for item in fact.provenance) or 'None'}",
            f"- Unresolved notes: {fact.unresolved_notes or 'None'}",
            "- Simulator binding allowed: `false`", "",
        ])
    lines.extend(["## Conflicts and Version Ambiguities", ""])
    ambiguous = [fact for fact in report.facts if fact.verification_status in {"conflicting", "version_ambiguous"}]
    lines.extend(f"- {fact.fact_id}: {fact.unresolved_notes}" for fact in ambiguous)
    if not ambiguous:
        lines.append("- No recorded source conflicts; version-specific missing assumptions remain listed below.")
    lines.extend(["", "## Unresolved Source Gaps", ""])
    lines.extend(f"- {fact_id}" for fact_id in report.unresolved_source_gaps)
    lines.extend(["", "## Recommended Research Actions", ""])
    lines.extend(f"- {item}" for item in report.recommended_research_actions)
    return "\n".join(lines) + "\n"


def _fact_model(item: dict[str, Any]) -> FactRecord:
    return FactRecord(
        fact_id=item["fact_id"], internal_actor_id=item["internal_actor_id"], action_scope=item["action_scope"],
        field_name=item["field_name"], value=item["value"], value_type=item["value_type"], unit=item.get("unit"),
        verification_status=item["verification_status"],
        provenance=[FactProvenance(**entry) for entry in item["provenance"]],
        game_version_applicability=item["game_version_applicability"], language=item["language"],
        evidence_summary=item["evidence_summary"], unresolved_notes=item.get("unresolved_notes"),
        links=[TraceRequirementLink(**entry) for entry in item["links"]],
        simulator_binding_allowed=item["simulator_binding_allowed"],
    )


def _build_coverage(evidence: dict[str, Any], facts: list[FactRecord]) -> list[dict[str, Any]]:
    items = [("prebattle", None, item) for item in evidence["prebattle"]] + [(f"step_{item['step']}", item["step"], item) for item in evidence["steps"]]
    coverage = []
    verified_statuses = {"verified_official", "verified_structured_data", "corroborated"}
    partial_statuses = {"single_source_unverified", "version_ambiguous"}
    for location, step, item in items:
        linked = [fact for fact in facts if any(link.step == step and link.actor == item["actor"] and link.action == item["action"] for link in fact.links)]
        verified = sorted(fact.fact_id for fact in linked if fact.verification_status in verified_statuses)
        partial = sorted(fact.fact_id for fact in linked if fact.verification_status in partial_statuses)
        unresolved = sorted(fact.fact_id for fact in linked if fact.verification_status in {"missing", "conflicting"})
        resolution = "source_resolved" if verified and not partial and not unresolved else "partially_resolved" if verified or partial else "unresolved"
        coverage.append({
            "location": location, "step": step, "actor": item["actor"], "action": item["action"],
            "verified_fact_ids": verified, "partial_fact_ids": partial, "unresolved_fact_ids": unresolved,
            "blocker_resolution": resolution, "simulator_binding_allowed": False,
        })
    return coverage


def _validate_inputs(evidence: dict[str, Any], gap: dict[str, Any], sources_data: dict[str, Any], facts_data: dict[str, Any]) -> None:
    issues: list[str] = []
    _reject_executable_schema(sources_data, "sources", issues)
    _reject_executable_schema(facts_data, "facts", issues)
    sources = sources_data.get("sources")
    facts = facts_data.get("facts")
    identities = facts_data.get("identities")
    if not isinstance(sources, list) or not isinstance(facts, list) or not isinstance(identities, list):
        raise ValueError("Sources, identities, and facts must be lists.")
    source_ids = _unique_ids(sources, "source_id", "source", issues)
    fact_ids = _unique_ids(facts, "fact_id", "fact", issues)
    del fact_ids
    source_types = {item.get("source_id"): item.get("source_type") for item in sources}
    for index, source in enumerate(sources):
        label = f"sources[{index}]"
        if source.get("source_type") not in SOURCE_TYPES:
            issues.append(f"{label}.source_type is unsupported.")
        if not _valid_locator(source.get("locator"), source.get("source_type")):
            issues.append(f"{label}.locator is malformed.")
    evidence_keys = _evidence_keys(evidence)
    gap_keys = _gap_keys(gap)
    if evidence_keys != gap_keys:
        issues.append("Evidence report and gap inventory trace items must match.")
    actor_ids = {key[1] for key in evidence_keys}
    seen_identity_ids: set[str] = set()
    for index, identity in enumerate(identities):
        actor = identity.get("internal_actor_id")
        if actor in seen_identity_ids:
            issues.append(f"Duplicate identity actor ID {actor!r}.")
        seen_identity_ids.add(actor)
        aliases = identity.get("aliases")
        if not isinstance(aliases, list) or len(aliases) != len(set(aliases)):
            issues.append(f"identities[{index}].aliases must be unique.")
        if identity.get("identity_verification_status") not in VERIFICATION_STATUSES:
            issues.append(f"identities[{index}].identity_verification_status is unsupported.")
        for source_id in identity.get("source_ids", []):
            if source_id not in source_ids:
                issues.append(f"identities[{index}] references unknown source {source_id!r}.")
    if actor_ids - seen_identity_ids:
        issues.append(f"Missing identity records for actors: {sorted(actor_ids - seen_identity_ids)}.")
    linked_keys: set[tuple[str, str, str]] = set()
    for index, fact in enumerate(facts):
        label = f"facts[{index}]"
        status = fact.get("verification_status")
        if status not in VERIFICATION_STATUSES:
            issues.append(f"{label}.verification_status is unsupported.")
        if fact.get("simulator_binding_allowed") is not False:
            issues.append(f"{label}.simulator_binding_allowed must be false.")
        if status == "missing" and fact.get("value") is not None:
            issues.append(f"{label} missing fact must have value null.")
        provenance = fact.get("provenance", [])
        for entry in provenance:
            if entry.get("source_id") not in source_ids:
                issues.append(f"{label} references unknown source {entry.get('source_id')!r}.")
        if status in QUALIFYING_VERIFIED and not any(source_types.get(entry.get("source_id")) in QUALIFYING_VERIFIED[status] for entry in provenance):
            issues.append(f"{label} verified status lacks a qualifying source.")
        if status == "corroborated" and len({entry.get("source_id") for entry in provenance}) < 2:
            issues.append(f"{label} corroborated status requires at least two sources.")
        if status == "conflicting" and len({entry.get("source_id") for entry in provenance if entry.get("relationship") == "conflicts"}) < 2:
            issues.append(f"{label} conflicting status requires two conflicting provenance entries.")
        for link in fact.get("links", []):
            key = (link.get("location"), link.get("actor"), link.get("action"))
            step_key = (link.get("step"), link.get("actor"), link.get("action"))
            if step_key not in {(key[0], key[1], key[2]) for key in evidence_keys}:
                issues.append(f"{label} has mismatched trace requirement link {step_key}.")
            linked_keys.add(key)
    expected_linked = {(("prebattle" if step is None else f"step_{step}"), actor, action) for step, actor, action in evidence_keys}
    if expected_linked - linked_keys:
        issues.append(f"Facts do not cover trace item(s): {sorted(expected_linked - linked_keys)}.")
    if issues:
        raise ValueError("Character source registry validation failed:\n" + "\n".join(f"- {issue}" for issue in issues))


def _evidence_keys(data: dict[str, Any]) -> set[tuple[int | None, str, str]]:
    return {(None, item["actor"], item["action"]) for item in data.get("prebattle", [])} | {(item["step"], item["actor"], item["action"]) for item in data.get("steps", [])}


def _gap_keys(data: dict[str, Any]) -> set[tuple[int | None, str, str]]:
    return {(None, item["actor"], item["action"]) for item in data.get("prebattle", [])} | {(item["step"], item["actor"], item["action"]) for item in data.get("steps", [])}


def _unique_ids(items: list[dict[str, Any]], field: str, label: str, issues: list[str]) -> set[str]:
    values = [item.get(field) for item in items]
    if any(not isinstance(value, str) or not value for value in values):
        issues.append(f"Every {label} requires a nonempty {field}.")
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        issues.append(f"Duplicate {label} IDs: {duplicates}.")
    return set(values)


def _valid_locator(locator: Any, source_type: Any) -> bool:
    if not isinstance(locator, str) or not locator:
        return False
    if source_type == "manual_video_evidence":
        return bool(re.fullmatch(r"local://[A-Za-z0-9_./-]+", locator))
    parsed = urlparse(locator)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _reject_executable_schema(value: Any, label: str, issues: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z]", "", key.lower())
            if normalized in FORBIDDEN_SCHEMA_KEYS:
                issues.append(f"{label}.{key} is an executable schema key and is forbidden.")
            _reject_executable_schema(child, f"{label}.{key}", issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_executable_schema(child, f"{label}[{index}]", issues)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a non-executable character source registry.")
    parser.add_argument("--evidence-report", required=True)
    parser.add_argument("--gap-inventory", required=True)
    parser.add_argument("--sources", required=True)
    parser.add_argument("--facts", required=True)
    parser.add_argument("--format", choices=["markdown", "json"], required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        inputs = [load_json(path) for path in [args.evidence_report, args.gap_inventory, args.sources, args.facts]]
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR source registry input failure: {exc}", file=sys.stderr)
        return 2
    try:
        report = build_source_registry_report(*inputs)
    except ValueError as exc:
        print(f"FAIL source registry validation: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR source registry could not run: {exc}", file=sys.stderr)
        return 2
    rendered = render_markdown(report) if args.format == "markdown" else render_json(report)
    try:
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except OSError as exc:
        print(f"ERROR source registry output failure: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
