from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ALLOWED_CATEGORIES = {
    "prebattle_technique",
    "normal_skill",
    "ultimate_interrupt",
    "summon_or_companion_action",
    "composite_action_placeholder",
    "action_advance_placeholder",
    "unknown_or_unbound",
}
REQUIRED_MAPPING_FIELDS = {
    "actor",
    "action",
    "semantic_label",
    "category",
    "simulator_binding",
    "known",
    "unknown",
}
NUMERIC_CLAIM_PATTERN = re.compile(r"(?<![A-Za-z_])\d+(?:\.\d+)?")


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as json_file:
        data = json.load(json_file)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def validate_semantic_map(
    trace_data: dict[str, Any],
    semantic_map: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    _require_fields(
        semantic_map,
        [
            "semantic_map_id",
            "source_trace",
            "status",
            "version",
            "policy",
            "prebattle",
            "steps",
        ],
        "semantic_map",
        issues,
    )

    trace_name = trace_data.get("name")
    if semantic_map.get("source_trace") != trace_name:
        issues.append(
            "semantic_map.source_trace must match source trace name "
            f"{trace_name!r}."
        )

    if trace_data.get("check_mode") != "action_sequence_only":
        issues.append("source trace must have check_mode 'action_sequence_only'.")

    policy = semantic_map.get("policy")
    numeric_claims_allowed = True
    if not isinstance(policy, dict):
        issues.append("semantic_map.policy must be an object.")
    else:
        numeric_claims_allowed = policy.get("numeric_claims_allowed") is not False
        if policy.get("executable") is not False:
            issues.append("semantic_map.policy.executable must be false.")
        if policy.get("unknowns_allowed") is not True:
            issues.append("semantic_map.policy.unknowns_allowed must be true.")
        if policy.get("do_not_use_for_damage_or_av_validation") is not True:
            issues.append(
                "semantic_map.policy.do_not_use_for_damage_or_av_validation must be true."
            )

    _validate_mapping_collection(
        trace_items=trace_data.get("prebattle", []),
        map_items=semantic_map.get("prebattle"),
        label="prebattle",
        required_key_fields=["actor", "action"],
        numeric_claims_allowed=numeric_claims_allowed,
        issues=issues,
    )
    _validate_mapping_collection(
        trace_items=trace_data.get("steps", []),
        map_items=semantic_map.get("steps"),
        label="steps",
        required_key_fields=["step", "actor", "action"],
        numeric_claims_allowed=numeric_claims_allowed,
        issues=issues,
    )

    category_reference = semantic_map.get("category_reference", [])
    if category_reference:
        if not isinstance(category_reference, list):
            issues.append("semantic_map.category_reference must be a list when present.")
        else:
            missing_categories = sorted(ALLOWED_CATEGORIES - set(category_reference))
            if missing_categories:
                issues.append(
                    "semantic_map.category_reference missing supported category "
                    f"name(s): {missing_categories}."
                )

    return issues


def validate_semantic_map_files(
    trace_path: str | Path,
    semantic_map_path: str | Path,
) -> list[str]:
    return validate_semantic_map(load_json(trace_path), load_json(semantic_map_path))


def _validate_mapping_collection(
    trace_items: Any,
    map_items: Any,
    label: str,
    required_key_fields: list[str],
    numeric_claims_allowed: bool,
    issues: list[str],
) -> None:
    if not isinstance(trace_items, list):
        issues.append(f"source trace {label} must be a list.")
        return
    if not isinstance(map_items, list):
        issues.append(f"semantic_map.{label} must be a list.")
        return

    trace_counts = _key_counts(trace_items, required_key_fields, f"source trace {label}", issues)
    map_counts = _key_counts(map_items, required_key_fields, f"semantic_map.{label}", issues)

    for key, count in sorted(trace_counts.items()):
        map_count = map_counts.get(key, 0)
        if map_count != 1:
            issues.append(
                f"semantic_map.{label} must contain exactly one mapping for {key}; "
                f"found {map_count}."
            )
        if count != 1:
            issues.append(f"source trace {label} has duplicate key {key}.")

    for key in sorted(set(map_counts) - set(trace_counts)):
        issues.append(f"semantic_map.{label} contains extra mapping for {key}.")
    for key, count in sorted(map_counts.items()):
        if count != 1:
            issues.append(f"semantic_map.{label} has duplicate mapping for {key}.")

    for index, item in enumerate(map_items):
        item_label = f"semantic_map.{label}[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{item_label} must be an object.")
            continue
        _validate_mapping_shape(item, item_label, issues)
        if not numeric_claims_allowed:
            _check_no_numeric_claims(item, item_label, issues)


def _validate_mapping_shape(
    item: dict[str, Any],
    label: str,
    issues: list[str],
) -> None:
    _require_fields(item, sorted(REQUIRED_MAPPING_FIELDS), label, issues)
    category = item.get("category")
    if category not in ALLOWED_CATEGORIES:
        issues.append(f"{label}.category must be one of {sorted(ALLOWED_CATEGORIES)}.")

    for field_name in ["actor", "action", "semantic_label", "simulator_binding"]:
        if field_name in item and not isinstance(item[field_name], str):
            issues.append(f"{label}.{field_name} must be a string.")

    for field_name in ["known", "unknown"]:
        value = item.get(field_name)
        if not isinstance(value, list):
            issues.append(f"{label}.{field_name} must be a list.")
            continue
        for index, entry in enumerate(value):
            if not isinstance(entry, str):
                issues.append(f"{label}.{field_name}[{index}] must be a string.")


def _check_no_numeric_claims(
    item: dict[str, Any],
    label: str,
    issues: list[str],
) -> None:
    for field_name in ["known", "unknown"]:
        entries = item.get(field_name, [])
        if not isinstance(entries, list):
            continue
        for index, entry in enumerate(entries):
            if isinstance(entry, str) and NUMERIC_CLAIM_PATTERN.search(entry):
                issues.append(
                    f"{label}.{field_name}[{index}] contains a numeric claim while "
                    "numeric_claims_allowed is false."
                )

    for key, value in item.items():
        if key == "step" or isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            issues.append(
                f"{label}.{key} contains a numeric value while "
                "numeric_claims_allowed is false."
            )


def _key_counts(
    items: list[Any],
    key_fields: list[str],
    label: str,
    issues: list[str],
) -> dict[tuple[Any, ...], int]:
    counts: dict[tuple[Any, ...], int] = {}
    for index, item in enumerate(items):
        item_label = f"{label}[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{item_label} must be an object.")
            continue
        missing = [field for field in key_fields if field not in item]
        if missing:
            issues.append(f"{item_label} missing required key field(s): {missing}.")
            continue
        key = tuple(item[field] for field in key_fields)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _require_fields(
    data: dict[str, Any],
    fields: list[str],
    label: str,
    issues: list[str],
) -> None:
    missing = [field for field in fields if field not in data]
    if missing:
        issues.append(f"{label} missing required field(s): {missing}.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a manual trace semantic map.")
    parser.add_argument("--trace", required=True)
    parser.add_argument("--semantic-map", required=True)
    args = parser.parse_args(argv)

    try:
        issues = validate_semantic_map_files(args.trace, args.semantic_map)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL semantic map validation could not run: {exc}")
        return 2

    if issues:
        print(f"FAIL semantic map validation found {len(issues)} issue(s).")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("PASS semantic map validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
