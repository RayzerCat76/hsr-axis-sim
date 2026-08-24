from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


INVENTORY_VERSION = "0.1"
ALLOWED_STATUSES = {
    "generic_primitive_available",
    "missing_character_binding",
    "missing_target_evidence",
    "missing_initial_state",
    "unresolved_composite_action",
    "unresolved_action_advance",
    "video_insufficient",
    "blocked",
}
BLOCKER_STATUSES = ALLOWED_STATUSES - {"generic_primitive_available"}
WARNING = (
    "Planning inventory only, not an executable replay. Generic engine support does "
    "not verify a real-character binding. No combat values or semantics are inferred."
)
LIST_FIELDS = [
    "generic_primitives", "missing_character_kit_semantics", "missing_initial_state",
    "unresolved_behavior", "evidence_limitations",
]


@dataclass(frozen=True)
class BindingAssessment:
    step: int | None
    actor: str
    action: str
    semantic_label: str
    semantic_category: str
    binding_statuses: list[str]
    generic_primitives: list[str]
    missing_character_kit_semantics: list[str]
    target_status: str
    missing_initial_state: list[str]
    unresolved_behavior: list[str]
    evidence_limitations: list[str]
    minimum_future_work: list[dict[str, str]]
    executable_now: bool
    binding_explanation: str


@dataclass(frozen=True)
class BindingGapInventory:
    inventory_id: str
    version: str
    source_evidence_report_id: str
    source_evidence_report_path: str | None
    policy: dict[str, Any]
    global_blockers: list[str]
    prebattle: list[BindingAssessment]
    steps: list[BindingAssessment]
    future_work_summary: dict[str, list[str]]


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as json_file:
        value = json.load(json_file)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def build_binding_gap_inventory(
    evidence_report: dict[str, Any],
    assessment: dict[str, Any],
    source_evidence_report_path: str | None = None,
) -> BindingGapInventory:
    _validate_inputs(evidence_report, assessment)
    prebattle_by_key = _index_assessments(assessment["prebattle"], ["actor", "action"])
    steps_by_key = _index_assessments(assessment["steps"], ["step", "actor", "action"])
    prebattle = [
        _assessment_model(prebattle_by_key[(item["actor"], item["action"])], item)
        for item in evidence_report["prebattle"]
    ]
    steps = [
        _assessment_model(
            steps_by_key[(item["step"], item["actor"], item["action"])], item
        )
        for item in evidence_report["steps"]
    ]
    return BindingGapInventory(
        inventory_id=assessment["inventory_id"],
        version=assessment["version"],
        source_evidence_report_id=evidence_report["report_id"],
        source_evidence_report_path=source_evidence_report_path,
        policy={
            "planning_inventory_only": True,
            "executable": False,
            "combat_numeric_claims_allowed": False,
            "warning": WARNING,
        },
        global_blockers=list(assessment["global_blockers"]),
        prebattle=prebattle,
        steps=steps,
        future_work_summary=_future_work_summary([*prebattle, *steps]),
    )


def build_binding_gap_inventory_files(
    evidence_report_path: str | Path, assessment_path: str | Path
) -> BindingGapInventory:
    return build_binding_gap_inventory(
        load_json(evidence_report_path),
        load_json(assessment_path),
        source_evidence_report_path=str(evidence_report_path),
    )


def inventory_to_dict(inventory: BindingGapInventory) -> dict[str, Any]:
    return asdict(inventory)


def render_json(inventory: BindingGapInventory) -> str:
    return json.dumps(inventory_to_dict(inventory), ensure_ascii=False, indent=2) + "\n"


def render_markdown(inventory: BindingGapInventory) -> str:
    lines = [
        f"# Simulator Binding Gap Inventory: {inventory.source_evidence_report_id}",
        "",
        f"Inventory ID: `{inventory.inventory_id}`  ",
        f"Version: `{inventory.version}`  ",
        f"Source evidence report: `{inventory.source_evidence_report_path or inventory.source_evidence_report_id}`",
        "",
        "## Planning Boundary",
        "",
        f"> {inventory.policy['warning']}",
        "",
        "## Global Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in inventory.global_blockers)
    lines.extend(["", "## Ordered Binding Assessments", "", "| Step | Actor | Action | Statuses | Executable now |", "|---:|---|---|---|---|"])
    for item in inventory.steps:
        lines.append(
            f"| {item.step} | {item.actor} | {item.action} | {', '.join(item.binding_statuses)} | `{str(item.executable_now).lower()}` |"
        )
    lines.extend(["", "## Prebattle Assessment", ""])
    for item in inventory.prebattle:
        lines.extend(_markdown_details(item, f"{item.actor} / {item.action}"))
    lines.extend(["## Step Details", ""])
    for item in inventory.steps:
        lines.extend(_markdown_details(item, f"Step {item.step}: {item.actor} / {item.action}"))
    lines.extend(["## Deduplicated Minimum Future Work", ""])
    for category in sorted(inventory.future_work_summary):
        lines.append(f"### {category}")
        lines.append("")
        lines.extend(f"- {item}" for item in inventory.future_work_summary[category])
        lines.append("")
    return "\n".join(lines) + "\n"


def _markdown_details(item: BindingAssessment, heading: str) -> list[str]:
    lines = [f"### {heading}", ""]
    if item.step is not None:
        lines.append(f"- Target status: {item.target_status}")
    lines.extend(
        [
            f"- Semantic: {item.semantic_label} (`{item.semantic_category}`)",
            f"- Binding statuses: {', '.join(item.binding_statuses)}",
            f"- Executable now: `{str(item.executable_now).lower()}`",
            f"- Generic engine primitives: {'; '.join(item.generic_primitives) or 'None'}",
            f"- Missing verified character-kit semantics: {'; '.join(item.missing_character_kit_semantics) or 'None'}",
            f"- Missing initialization/resource data: {'; '.join(item.missing_initial_state) or 'None'}",
            f"- Unresolved trigger/composite behavior: {'; '.join(item.unresolved_behavior) or 'None'}",
            f"- Evidence limitations: {'; '.join(item.evidence_limitations) or 'None'}",
            f"- Binding explanation: {item.binding_explanation}",
            "- Minimum future work:",
        ]
    )
    lines.extend(f"  - {work['category']}: {work['item']}" for work in item.minimum_future_work)
    lines.append("")
    return lines


def _assessment_model(data: dict[str, Any], evidence: dict[str, Any]) -> BindingAssessment:
    return BindingAssessment(
        step=data.get("step"), actor=evidence["actor"], action=evidence["action"],
        semantic_label=evidence["semantic_label"], semantic_category=evidence["semantic_category"],
        binding_statuses=list(data["binding_statuses"]),
        generic_primitives=list(data["generic_primitives"]),
        missing_character_kit_semantics=list(data["missing_character_kit_semantics"]),
        target_status=data["target_status"], missing_initial_state=list(data["missing_initial_state"]),
        unresolved_behavior=list(data["unresolved_behavior"]),
        evidence_limitations=list(data["evidence_limitations"]),
        minimum_future_work=[dict(item) for item in data["minimum_future_work"]],
        executable_now=data["executable_now"], binding_explanation=data["binding_explanation"],
    )


def _future_work_summary(items: list[BindingAssessment]) -> dict[str, list[str]]:
    grouped: dict[str, set[str]] = {}
    for assessment in items:
        for work in assessment.minimum_future_work:
            grouped.setdefault(work["category"], set()).add(work["item"])
    return {category: sorted(items) for category, items in sorted(grouped.items())}


def _validate_inputs(evidence: dict[str, Any], assessment: dict[str, Any]) -> None:
    issues: list[str] = []
    _require_fields(evidence, ["report_id", "prebattle", "steps"], "evidence_report", issues)
    _require_fields(assessment, ["inventory_id", "version", "source_evidence_report_id", "global_blockers", "prebattle", "steps"], "assessment", issues)
    if assessment.get("source_evidence_report_id") != evidence.get("report_id"):
        issues.append("assessment.source_evidence_report_id must match evidence_report.report_id.")
    _validate_collection(evidence.get("prebattle"), assessment.get("prebattle"), "prebattle", ["actor", "action"], issues)
    _validate_collection(evidence.get("steps"), assessment.get("steps"), "steps", ["step", "actor", "action"], issues)
    if issues:
        raise ValueError("Binding gap inventory validation failed:\n" + "\n".join(f"- {issue}" for issue in issues))


def _validate_collection(evidence_items: Any, assessment_items: Any, label: str, key_fields: list[str], issues: list[str]) -> None:
    if not isinstance(evidence_items, list) or not isinstance(assessment_items, list):
        issues.append(f"evidence_report.{label} and assessment.{label} must be lists.")
        return
    evidence_keys = _key_counts(evidence_items, key_fields, f"evidence_report.{label}", issues)
    assessment_keys = _key_counts(assessment_items, key_fields, f"assessment.{label}", issues)
    for key, count in sorted(evidence_keys.items()):
        actual = assessment_keys.get(key, 0)
        if actual != 1:
            issues.append(f"assessment.{label} must contain exactly one assessment for {key}; found {actual}.")
        if count != 1:
            issues.append(f"evidence_report.{label} has duplicate key {key}.")
    for key in sorted(set(assessment_keys) - set(evidence_keys)):
        issues.append(f"assessment.{label} contains extra assessment for {key}.")
    for index, item in enumerate(assessment_items):
        if isinstance(item, dict):
            _validate_assessment_shape(item, f"assessment.{label}[{index}]", "step" in key_fields, issues)


def _validate_assessment_shape(item: dict[str, Any], label: str, needs_step: bool, issues: list[str]) -> None:
    fields = ["actor", "action", "binding_statuses", "generic_primitives", "missing_character_kit_semantics", "target_status", "missing_initial_state", "unresolved_behavior", "evidence_limitations", "minimum_future_work", "executable_now", "binding_explanation"]
    if needs_step:
        fields.append("step")
    _require_fields(item, fields, label, issues)
    statuses = item.get("binding_statuses")
    if not isinstance(statuses, list) or not statuses:
        issues.append(f"{label}.binding_statuses must be a nonempty list.")
    elif any(status not in ALLOWED_STATUSES for status in statuses):
        issues.append(f"{label}.binding_statuses contains unsupported status values.")
    for field in LIST_FIELDS:
        value = item.get(field)
        if not isinstance(value, list) or any(not isinstance(entry, str) for entry in value):
            issues.append(f"{label}.{field} must be a list of strings.")
    if not isinstance(item.get("target_status"), str):
        issues.append(f"{label}.target_status must be a string.")
    work = item.get("minimum_future_work")
    if not isinstance(work, list) or any(not isinstance(entry, dict) or set(entry) != {"category", "item"} or not all(isinstance(value, str) and value for value in entry.values()) for entry in work):
        issues.append(f"{label}.minimum_future_work must be category/item objects.")
    if not isinstance(item.get("executable_now"), bool):
        issues.append(f"{label}.executable_now must be a boolean.")
    if not isinstance(item.get("binding_explanation"), str) or not item.get("binding_explanation"):
        issues.append(f"{label}.binding_explanation must be a nonempty string.")
    if item.get("executable_now") is True:
        blocker_lists = [item.get(field, []) for field in LIST_FIELDS if field != "generic_primitives"]
        if any(blocker_lists) or any(status in BLOCKER_STATUSES for status in statuses or []):
            issues.append(f"{label}.executable_now cannot be true while blockers remain.")


def _index_assessments(items: list[dict[str, Any]], fields: list[str]) -> dict[tuple[Any, ...], dict[str, Any]]:
    return {tuple(item[field] for field in fields): item for item in items}


def _key_counts(items: list[Any], fields: list[str], label: str, issues: list[str]) -> dict[tuple[Any, ...], int]:
    counts: dict[tuple[Any, ...], int] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            issues.append(f"{label}[{index}] must be an object.")
            continue
        missing = [field for field in fields if field not in item]
        if missing:
            issues.append(f"{label}[{index}] missing key field(s): {missing}.")
            continue
        key = tuple(item[field] for field in fields)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _require_fields(data: dict[str, Any], fields: list[str], label: str, issues: list[str]) -> None:
    missing = [field for field in fields if field not in data]
    if missing:
        issues.append(f"{label} missing required field(s): {missing}.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a non-executable simulator binding gap inventory.")
    parser.add_argument("--evidence-report", required=True)
    parser.add_argument("--assessment", required=True)
    parser.add_argument("--format", choices=["markdown", "json"], required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        evidence = load_json(args.evidence_report)
        assessment = load_json(args.assessment)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR binding gap inventory input failure: {exc}", file=sys.stderr)
        return 2
    try:
        inventory = build_binding_gap_inventory(evidence, assessment, args.evidence_report)
    except ValueError as exc:
        print(f"FAIL binding gap inventory validation: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR binding gap inventory could not run: {exc}", file=sys.stderr)
        return 2
    rendered = render_markdown(inventory) if args.format == "markdown" else render_json(inventory)
    try:
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except OSError as exc:
        print(f"ERROR binding gap inventory output failure: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
