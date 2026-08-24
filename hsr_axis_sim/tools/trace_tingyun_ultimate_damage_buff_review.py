from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "manual_video_traces"
DEFAULT_FACTS = BASE / "normalized_character_facts" / "tingyun_ultimate_damage_buff_review_v0_1.json"
DEFAULT_SOURCES = BASE / "source_registry" / "sources_v0_1.json"
VERIFICATION_STATUSES = {"corroborated", "missing", "unresolved"}
RELEASE_STATUSES = {
    "release_structured_data",
    "release_community_reference",
    "accepted_manual_evidence",
}
CORROBORATION_STATUSES = {
    "supports_exact_field",
    "supports_context_only",
    "does_not_distinguish",
}
READINESS_STATUSES = {
    "ready_for_separate_binding_task",
    "blocked_by_source_gap",
    "blocked_by_duration_semantics_gap",
    "blocked_by_both",
}
EXPECTED_FACT_IDS = {
    "tingyun.ultimate.damage_buff.target_scope",
    "tingyun.ultimate.damage_buff.duration_turns",
    "tingyun.ultimate.damage_buff.magnitude_by_trace_level",
    "tingyun.ultimate.damage_buff.application_order",
    "tingyun.ultimate.damage_buff.release_scope",
    "tingyun.ultimate.damage_buff.real_video_trace_level",
}
SOURCE_BLOCKING_FACT_IDS = {
    "tingyun.ultimate.damage_buff.magnitude_by_trace_level",
    "tingyun.ultimate.damage_buff.application_order",
}
FACT_CONTRACTS = {
    "tingyun.ultimate.damage_buff.target_scope": {
        "field_name": "damage_buff_target_scope",
        "normalized_value": "selected_single_ally",
        "value_type": "target_scope",
        "unit": None,
        "verification_status": "corroborated",
    },
    "tingyun.ultimate.damage_buff.duration_turns": {
        "field_name": "damage_buff_duration_turns",
        "normalized_value": 2,
        "value_type": "integer",
        "unit": "turn",
        "verification_status": "corroborated",
    },
    "tingyun.ultimate.damage_buff.magnitude_by_trace_level": {
        "field_name": "damage_increase_percent_by_trace_level",
        "normalized_value": None,
        "value_type": "trace_level_table",
        "unit": "percent",
        "verification_status": "missing",
    },
    "tingyun.ultimate.damage_buff.application_order": {
        "field_name": "damage_buff_relative_to_target_energy_restore",
        "normalized_value": None,
        "value_type": "effect_order",
        "unit": None,
        "verification_status": "unresolved",
    },
    "tingyun.ultimate.damage_buff.release_scope": {
        "field_name": "release_and_version_scope",
        "normalized_value": "v1.0_release_core_applicable_to_3.4_with_current_structured_page_version_ambiguity",
        "value_type": "version_qualifier",
        "unit": None,
        "verification_status": "corroborated",
    },
    "tingyun.ultimate.damage_buff.real_video_trace_level": {
        "field_name": "observed_real_video_trace_level",
        "normalized_value": None,
        "value_type": "trace_level",
        "unit": None,
        "verification_status": "missing",
    },
}
FORBIDDEN_KEYS = {
    "effects",
    "effect",
    "executor",
    "handlerkey",
    "bindingdatapath",
    "characterspec",
    "skillspec",
    "realtraceexecutable",
}
WARNING = (
    "NON-EXECUTABLE EVIDENCE REVIEW. This report does not apply Tingyun's DMG buff, "
    "select a real-video target or trace level, or authorize simulator binding."
)


@dataclass(frozen=True)
class FactProvenance:
    source_id: str
    source_title: str
    source_locator: str
    field_locator: str
    source_type: str
    game_version: str
    release_status: str
    corroboration_status: str
    evidence_summary: str


@dataclass(frozen=True)
class AtomicFact:
    fact_id: str
    field_name: str
    normalized_value: Any
    value_type: str
    unit: str | None
    verification_status: str
    version_applicability: str
    provenance: tuple[FactProvenance, ...]
    unresolved_notes: str
    trace_step: int
    trace_actor: str
    trace_action: str
    simulator_binding_allowed: bool


@dataclass(frozen=True)
class DurationSemanticsAssessment:
    verified_duration_turns: int
    engine_duration_type_reviewed: str
    duration_starts: str
    cast_interrupt_decrements: bool
    current_target_normal_turn_decrements_at_end_if_already_applied: bool
    extra_turn_decrements: bool
    non_ending_action_decrements: bool
    expiration_boundary: str
    engine_representation_status: str
    verified_game_equivalence: bool
    assessment_notes: str


@dataclass(frozen=True)
class DamageBuffReadinessReport:
    review_id: str
    version: str
    warning: str
    readiness_status: str
    source_catalog: tuple[dict[str, Any], ...]
    facts: tuple[AtomicFact, ...]
    duration_semantics: DurationSemanticsAssessment
    blockers: tuple[str, ...]
    recommended_research_actions: tuple[str, ...]
    research_limitations: tuple[str, ...]
    simulator_binding_allowed: bool


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def build_report(
    source_catalog_data: Any, review_data: Any
) -> DamageBuffReadinessReport:
    issues: list[str] = []
    review = review_data if isinstance(review_data, dict) else {}
    if not isinstance(review_data, dict):
        issues.append("review must be an object.")
    _reject_executable_schema(review, "review", issues)
    sources = _validated_sources(source_catalog_data, issues)
    facts = _validated_facts(review, sources, issues)
    duration = _validated_duration(review.get("duration_semantics"), issues)
    declared = review.get("declared_readiness_status")
    computed = _computed_readiness(facts, duration)
    if not isinstance(declared, str) or not declared:
        issues.append("declared_readiness_status must be a non-empty string.")
    elif declared not in READINESS_STATUSES:
        issues.append("declared_readiness_status is unsupported.")
    elif declared != computed:
        issues.append(
            f"declared_readiness_status must match computed status {computed!r}."
    )
    for field in ("blockers", "recommended_research_actions", "research_limitations"):
        _validated_string_list(review.get(field), field, issues)
    if review.get("status") != "non_executable_evidence_review":
        issues.append("status must be 'non_executable_evidence_review'.")
    for field in ("review_id", "version"):
        if not isinstance(review.get(field), str) or not review[field]:
            issues.append(f"{field} must be a non-empty string.")
    if issues:
        raise ValueError(
            "Tingyun Ultimate damage-buff review validation failed:\n"
            + "\n".join(f"- {issue}" for issue in issues)
        )

    used_source_ids = sorted(
        {item.source_id for fact in facts for item in fact.provenance}
    )
    source_rows = tuple(
        {
            "source_id": source_id,
            "title": sources[source_id]["title"],
            "locator": sources[source_id]["locator"],
            "source_type": sources[source_id]["source_type"],
            "language": sources[source_id]["language"],
            "game_version": sources[source_id]["game_version"],
        }
        for source_id in used_source_ids
    )
    return DamageBuffReadinessReport(
        review_id=review["review_id"],
        version=review["version"],
        warning=WARNING,
        readiness_status=computed,
        source_catalog=source_rows,
        facts=tuple(sorted(facts, key=lambda item: item.fact_id)),
        duration_semantics=duration,
        blockers=tuple(sorted(review["blockers"])),
        recommended_research_actions=tuple(
            sorted(review["recommended_research_actions"])
        ),
        research_limitations=tuple(sorted(review["research_limitations"])),
        simulator_binding_allowed=False,
    )


def _validated_sources(data: Any, issues: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        issues.append("source catalog must be an object with a sources list.")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for index, source in enumerate(data["sources"]):
        if not isinstance(source, dict):
            issues.append(f"sources[{index}] must be an object.")
            continue
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            issues.append(f"sources[{index}].source_id must be a non-empty string.")
            continue
        if source_id in result:
            issues.append(f"duplicate source_id {source_id!r}.")
            continue
        for field in ("title", "locator", "source_type", "language", "game_version"):
            if not isinstance(source.get(field), str) or not source[field]:
                issues.append(f"sources[{index}].{field} must be a non-empty string.")
        result[source_id] = source
    return result


def _validated_facts(
    data: dict[str, Any], sources: dict[str, dict[str, Any]], issues: list[str]
) -> list[AtomicFact]:
    raw_facts = data.get("facts")
    if not isinstance(raw_facts, list):
        issues.append("facts must be a list.")
        return []
    ids = [fact.get("fact_id") for fact in raw_facts if isinstance(fact, dict)]
    if len(ids) != len(raw_facts) or any(not isinstance(item, str) or not item for item in ids):
        issues.append("every fact must be an object with a non-empty string fact_id.")
        return []
    if len(set(ids)) != len(ids):
        issues.append("fact IDs must be unique.")
    if set(ids) != EXPECTED_FACT_IDS:
        issues.append("facts must contain the exact required Tingyun damage-buff fields.")
    result: list[AtomicFact] = []
    for index, fact in enumerate(raw_facts):
        label = f"facts[{index}]"
        fact_id = fact["fact_id"]
        contract = FACT_CONTRACTS.get(fact_id)
        status = fact.get("verification_status")
        if not isinstance(status, str) or status not in VERIFICATION_STATUSES:
            issues.append(f"{label}.verification_status is unsupported.")
        if isinstance(status, str) and status in {"missing", "unresolved"} and fact.get("normalized_value") is not None:
            issues.append(f"{label} unresolved facts must have normalized_value null.")
        if fact.get("simulator_binding_allowed") is not False:
            issues.append(f"{label}.simulator_binding_allowed must be false.")
        link = fact.get("trace_link")
        if link != {"step": 1, "actor": "tingyun", "action": "ultimate"}:
            issues.append(f"{label}.trace_link must match Tingyun Ultimate step 1.")
            link = {"step": 0, "actor": "", "action": ""}
        provenance = _validated_provenance(fact.get("provenance"), sources, label, issues)
        if status == "corroborated" and len(
            {item.source_id for item in provenance if item.corroboration_status == "supports_exact_field"}
        ) < 2:
            issues.append(f"{label} corroborated facts require two exact-field sources.")
        for field in ("field_name", "value_type", "version_applicability", "unresolved_notes"):
            if not isinstance(fact.get(field), str) or not fact[field]:
                issues.append(f"{label}.{field} must be a non-empty string.")
        _validate_fact_contract(fact, contract, label, issues)
        result.append(
            AtomicFact(
                fact_id=fact_id,
                field_name=fact.get("field_name", ""),
                normalized_value=fact.get("normalized_value"),
                value_type=fact.get("value_type", ""),
                unit=fact.get("unit") if isinstance(fact.get("unit"), str) else None,
                verification_status=status if isinstance(status, str) and status in VERIFICATION_STATUSES else "unresolved",
                version_applicability=fact.get("version_applicability", ""),
                provenance=tuple(sorted(provenance, key=lambda item: (item.source_id, item.field_locator))),
                unresolved_notes=fact.get("unresolved_notes", ""),
                trace_step=link["step"],
                trace_actor=link["actor"],
                trace_action=link["action"],
                simulator_binding_allowed=False,
            )
        )
    return result


def _validate_fact_contract(
    fact: dict[str, Any], contract: dict[str, Any] | None, label: str, issues: list[str]
) -> None:
    if contract is None:
        return
    for field in ("field_name", "value_type", "verification_status"):
        if fact.get(field) != contract[field]:
            issues.append(f"{label}.{field} must be {contract[field]!r}.")
    expected_value = contract["normalized_value"]
    actual_value = fact.get("normalized_value")
    if fact["fact_id"] == "tingyun.ultimate.damage_buff.duration_turns":
        if type(actual_value) is not int or actual_value != expected_value:
            issues.append(f"{label}.normalized_value must be the integer 2.")
    elif actual_value != expected_value:
        issues.append(f"{label}.normalized_value must be {expected_value!r}.")
    if fact.get("unit") != contract["unit"]:
        issues.append(f"{label}.unit must be {contract['unit']!r}.")


def _validated_provenance(
    value: Any,
    sources: dict[str, dict[str, Any]],
    label: str,
    issues: list[str],
) -> list[FactProvenance]:
    if not isinstance(value, list) or not value:
        issues.append(f"{label}.provenance must be a non-empty list.")
        return []
    result: list[FactProvenance] = []
    source_ids: list[str] = []
    for index, item in enumerate(value):
        item_label = f"{label}.provenance[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{item_label} must be an object.")
            continue
        raw_source_id = item.get("source_id")
        source_id = raw_source_id if isinstance(raw_source_id, str) and raw_source_id else None
        if source_id is None:
            issues.append(f"{item_label}.source_id must be a non-empty string.")
        else:
            source_ids.append(source_id)
        source = sources.get(source_id) if source_id is not None else None
        if source is None:
            issues.append(f"{item_label} has a dangling source reference.")
        release_status = item.get("release_status")
        corroboration = item.get("corroboration_status")
        release_valid = isinstance(release_status, str) and release_status in RELEASE_STATUSES
        corroboration_valid = (
            isinstance(corroboration, str) and corroboration in CORROBORATION_STATUSES
        )
        if not release_valid:
            issues.append(f"{item_label}.release_status is unsupported.")
        if not corroboration_valid:
            issues.append(f"{item_label}.corroboration_status is unsupported.")
        field_locator = item.get("locator")
        evidence_summary = item.get("evidence_summary")
        locator_valid = isinstance(field_locator, str) and bool(field_locator)
        summary_valid = isinstance(evidence_summary, str) and bool(evidence_summary)
        if not locator_valid:
            issues.append(f"{item_label}.locator must be a non-empty string.")
        if not summary_valid:
            issues.append(f"{item_label}.evidence_summary must be a non-empty string.")
        source_fields_valid = source is not None and all(
            isinstance(source.get(field), str) and source[field]
            for field in ("title", "locator", "source_type", "game_version")
        )
        if not source_fields_valid:
            continue
        if not all((source_id is not None, release_valid, corroboration_valid, locator_valid, summary_valid)):
            continue
        result.append(
            FactProvenance(
                source_id=source_id,
                source_title=source["title"],
                source_locator=source["locator"],
                field_locator=field_locator,
                source_type=source["source_type"],
                game_version=source["game_version"],
                release_status=release_status,
                corroboration_status=corroboration,
                evidence_summary=evidence_summary,
            )
        )
    if len(set(source_ids)) != len(source_ids):
        issues.append(f"{label}.provenance must not contain duplicate source IDs.")
    return result


def _validated_duration(value: Any, issues: list[str]) -> DurationSemanticsAssessment:
    if not isinstance(value, dict):
        issues.append("duration_semantics must be an object.")
        value = {}
    expected = {
        "verified_duration_turns": 2,
        "engine_duration_type_reviewed": "target_normal_turns",
        "cast_interrupt_decrements": False,
        "current_target_normal_turn_decrements_at_end_if_already_applied": True,
        "extra_turn_decrements": False,
        "non_ending_action_decrements": False,
        "engine_representation_status": "representable_with_source_unverified_same_turn_edge",
        "verified_game_equivalence": False,
    }
    for field, expected_value in expected.items():
        actual = value.get(field)
        if isinstance(expected_value, bool) and type(actual) is not bool:
            issues.append(f"duration_semantics.{field} must be a boolean.")
        elif actual != expected_value:
            issues.append(f"duration_semantics.{field} must be {expected_value!r}.")
    for field in ("duration_starts", "expiration_boundary", "assessment_notes"):
        if not isinstance(value.get(field), str) or not value[field]:
            issues.append(f"duration_semantics.{field} must be a non-empty string.")
    return DurationSemanticsAssessment(
        verified_duration_turns=value.get("verified_duration_turns", 0),
        engine_duration_type_reviewed=value.get("engine_duration_type_reviewed", ""),
        duration_starts=value.get("duration_starts", ""),
        cast_interrupt_decrements=value.get("cast_interrupt_decrements", False),
        current_target_normal_turn_decrements_at_end_if_already_applied=value.get(
            "current_target_normal_turn_decrements_at_end_if_already_applied", False
        ),
        extra_turn_decrements=value.get("extra_turn_decrements", False),
        non_ending_action_decrements=value.get("non_ending_action_decrements", False),
        expiration_boundary=value.get("expiration_boundary", ""),
        engine_representation_status=value.get("engine_representation_status", ""),
        verified_game_equivalence=value.get("verified_game_equivalence", False),
        assessment_notes=value.get("assessment_notes", ""),
    )


def _computed_readiness(
    facts: list[AtomicFact], duration: DurationSemanticsAssessment
) -> str:
    statuses = {fact.fact_id: fact.verification_status for fact in facts}
    source_gap = any(statuses.get(fact_id) in {"missing", "unresolved", None} for fact_id in SOURCE_BLOCKING_FACT_IDS)
    duration_gap = not duration.verified_game_equivalence
    if source_gap and duration_gap:
        return "blocked_by_both"
    if source_gap:
        return "blocked_by_source_gap"
    if duration_gap:
        return "blocked_by_duration_semantics_gap"
    return "ready_for_separate_binding_task"


def _validated_string_list(value: Any, field: str, issues: list[str]) -> None:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
        issues.append(f"{field} must be a non-empty list of non-empty strings.")
    elif len(set(value)) != len(value):
        issues.append(f"{field} must not contain duplicates.")


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


def render_json(report: DamageBuffReadinessReport) -> str:
    return json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n"


def render_markdown(report: DamageBuffReadinessReport) -> str:
    duration = report.duration_semantics
    lines = [
        "# Tingyun Ultimate Damage-Buff Fact and Duration Review",
        "",
        f"> {report.warning}",
        "",
        f"Readiness: `{report.readiness_status}`  ",
        f"Review version: `{report.version}`",
        "",
        "## Source Catalog",
        "",
        "| Source | Type | Version | Locator |",
        "|---|---|---|---|",
    ]
    for source in report.source_catalog:
        lines.append(
            f"| {source['source_id']} | {source['source_type']} | {source['game_version']} | {source['locator']} |"
        )
    lines.extend([
        "",
        "## Atomic Facts",
        "",
        "| Fact | Value | Status | Version scope |",
        "|---|---|---|---|",
    ])
    for fact in report.facts:
        value = "null" if fact.normalized_value is None else json.dumps(fact.normalized_value, ensure_ascii=False)
        lines.append(
            f"| {fact.fact_id} | {value} | {fact.verification_status} | {fact.version_applicability} |"
        )
    lines.extend(["", "## Field-Level Provenance", ""])
    for fact in report.facts:
        lines.extend([f"### {fact.fact_id}", ""])
        for provenance in fact.provenance:
            lines.append(
                f"- `{provenance.source_id}` ({provenance.release_status}, {provenance.corroboration_status}): {provenance.field_locator}. {provenance.evidence_summary}"
            )
        lines.append(f"- Unresolved: {fact.unresolved_notes}")
        lines.append("")
    lines.extend([
        "## Duration-Semantics Review",
        "",
        f"- Verified duration: `{duration.verified_duration_turns}` turns.",
        f"- Engine duration type: `{duration.engine_duration_type_reviewed}`.",
        f"- Start: {duration.duration_starts}",
        f"- Cast interrupt decrements: `{str(duration.cast_interrupt_decrements).lower()}`.",
        f"- Current target normal turn decrements at end if already applied: `{str(duration.current_target_normal_turn_decrements_at_end_if_already_applied).lower()}`.",
        f"- Extra turns decrement: `{str(duration.extra_turn_decrements).lower()}`.",
        f"- Non-ending actions decrement: `{str(duration.non_ending_action_decrements).lower()}`.",
        f"- Expiration boundary: {duration.expiration_boundary}",
        f"- Representation: `{duration.engine_representation_status}`.",
        f"- Verified game equivalence: `{str(duration.verified_game_equivalence).lower()}`.",
        f"- Assessment: {duration.assessment_notes}",
        "",
        "## Binding Readiness",
        "",
        f"- Status: `{report.readiness_status}`.",
        "- Simulator binding allowed: `false`.",
        "- Blockers:",
        *(f"  - {item}" for item in report.blockers),
        "- Recommended research actions:",
        *(f"  - {item}" for item in report.recommended_research_actions),
        "- Research limitations:",
        *(f"  - {item}" for item in report.research_limitations),
    ])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review non-executable Tingyun Ultimate damage-buff evidence and duration semantics.")
    parser.add_argument("--facts", default=str(DEFAULT_FACTS))
    parser.add_argument("--sources", default=str(DEFAULT_SOURCES))
    parser.add_argument("--format", choices=["markdown", "json"], required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        sources = load_json(args.sources)
        review = load_json(args.facts)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR Tingyun damage-buff review input failure: {exc}", file=sys.stderr)
        return 2
    try:
        report = build_report(sources, review)
    except ValueError as exc:
        print(f"FAIL Tingyun damage-buff review validation: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR Tingyun damage-buff review could not run: {exc}", file=sys.stderr)
        return 2
    rendered = render_markdown(report) if args.format == "markdown" else render_json(report)
    try:
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except OSError as exc:
        print(f"ERROR Tingyun damage-buff review output failure: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
