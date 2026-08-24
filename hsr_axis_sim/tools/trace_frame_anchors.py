from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ALLOWED_CONFIDENCE = {"high", "medium", "low"}
FRAME_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
REQUIRED_ANCHOR_FIELDS = {
    "actor", "action", "time_start_seconds", "time_end_seconds",
    "representative_frames", "confidence", "notes",
}
FORBIDDEN_COMBAT_FIELDS = {
    "av", "action_value", "speed", "sp", "skill_points", "energy", "hp",
    "toughness", "damage", "crit", "rng", "advance_percent", "delay_percent",
}


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as json_file:
        data = json.load(json_file)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def validate_frame_anchors(trace_data: dict[str, Any], anchors: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    _require_fields(anchors, ["frame_anchor_id", "source_trace", "status", "version", "timestamp_basis", "policy", "prebattle", "steps"], "frame_anchors", issues)
    for field in ("frame_anchor_id", "version"):
        if not isinstance(anchors.get(field), str) or not anchors[field]:
            issues.append(f"frame_anchors.{field} must be a non-empty string.")
    if anchors.get("status") != "approximate_media_evidence_only":
        issues.append("frame_anchors.status must be 'approximate_media_evidence_only'.")
    if anchors.get("timestamp_basis") != "seconds_from_local_clip_start":
        issues.append(
            "frame_anchors.timestamp_basis must be "
            "'seconds_from_local_clip_start'."
        )
    if anchors.get("source_trace") != trace_data.get("name"):
        issues.append("frame_anchors.source_trace must match source trace name " f"{trace_data.get('name')!r}.")
    if trace_data.get("check_mode") != "action_sequence_only":
        issues.append("source trace must have check_mode 'action_sequence_only'.")

    policy = anchors.get("policy")
    if not isinstance(policy, dict):
        issues.append("frame_anchors.policy must be an object.")
    else:
        for field, expected in (("executable", False), ("media_timestamps_only", True), ("combat_numeric_claims_allowed", False), ("unknowns_allowed", True)):
            if policy.get(field) is not expected:
                issues.append(f"frame_anchors.policy.{field} must be {str(expected).lower()}.")

    _check_forbidden_combat_fields(anchors, "frame_anchors", issues)
    _validate_collection(trace_data.get("prebattle"), anchors.get("prebattle"), "prebattle", ["actor", "action"], issues)
    _validate_collection(trace_data.get("steps"), anchors.get("steps"), "steps", ["step", "actor", "action"], issues)
    _validate_step_order(anchors.get("steps"), issues)
    return issues


def validate_frame_anchor_files(trace_path: str | Path, anchor_path: str | Path) -> list[str]:
    return validate_frame_anchors(load_json(trace_path), load_json(anchor_path))


def _validate_collection(trace_items: Any, anchor_items: Any, label: str, key_fields: list[str], issues: list[str]) -> None:
    if not isinstance(trace_items, list):
        issues.append(f"source trace {label} must be a list.")
        return
    if not isinstance(anchor_items, list):
        issues.append(f"frame_anchors.{label} must be a list.")
        return
    trace_counts = _key_counts(trace_items, key_fields, f"source trace {label}", issues)
    anchor_counts = _key_counts(anchor_items, key_fields, f"frame_anchors.{label}", issues)
    for key, count in sorted(trace_counts.items()):
        actual = anchor_counts.get(key, 0)
        if actual != 1:
            issues.append(f"frame_anchors.{label} must contain exactly one anchor for {key}; found {actual}.")
        if count != 1:
            issues.append(f"source trace {label} has duplicate key {key}.")
    for key in sorted(set(anchor_counts) - set(trace_counts)):
        issues.append(f"frame_anchors.{label} contains extra anchor for {key}.")
    for key, count in sorted(anchor_counts.items()):
        if count != 1:
            issues.append(f"frame_anchors.{label} has duplicate anchor for {key}.")
    for index, item in enumerate(anchor_items):
        if isinstance(item, dict):
            _validate_anchor_shape(item, f"frame_anchors.{label}[{index}]", "step" in key_fields, issues)


def _validate_anchor_shape(item: dict[str, Any], label: str, needs_step: bool, issues: list[str]) -> None:
    required = REQUIRED_ANCHOR_FIELDS | ({"step"} if needs_step else set())
    _require_fields(item, sorted(required), label, issues)
    for field in ("time_start_seconds", "time_end_seconds"):
        value = item.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            issues.append(f"{label}.{field} must be a finite nonnegative number.")
    start, end = item.get("time_start_seconds"), item.get("time_end_seconds")
    if _is_valid_time(start) and _is_valid_time(end) and start > end:
        issues.append(f"{label}.time_start_seconds must be less than or equal to time_end_seconds.")
    frames = item.get("representative_frames")
    if not isinstance(frames, list) or not frames:
        issues.append(f"{label}.representative_frames must be a nonempty list.")
    else:
        for index, frame in enumerate(frames):
            if not isinstance(frame, str) or not frame or Path(frame).suffix.lower() not in FRAME_EXTENSIONS:
                issues.append(f"{label}.representative_frames[{index}] must be a nonempty image filename.")
    if item.get("confidence") not in ALLOWED_CONFIDENCE:
        issues.append(f"{label}.confidence must be one of {sorted(ALLOWED_CONFIDENCE)}.")
    if not isinstance(item.get("notes"), str):
        issues.append(f"{label}.notes must be a string.")


def _validate_step_order(steps: Any, issues: list[str]) -> None:
    if not isinstance(steps, list):
        return
    previous: float | int | None = None
    for index, item in enumerate(steps):
        if not isinstance(item, dict) or not _is_valid_time(item.get("time_start_seconds")):
            continue
        start = item["time_start_seconds"]
        if previous is not None and start < previous:
            issues.append(f"frame_anchors.steps[{index}].time_start_seconds must be nondecreasing.")
        previous = start


def _check_forbidden_combat_fields(value: Any, label: str, issues: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_label = f"{label}.{key}"
            if key.lower() in FORBIDDEN_COMBAT_FIELDS:
                issues.append(f"{child_label} is a forbidden combat-state field.")
            _check_forbidden_combat_fields(child, child_label, issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _check_forbidden_combat_fields(child, f"{label}[{index}]", issues)


def _key_counts(items: list[Any], key_fields: list[str], label: str, issues: list[str]) -> dict[tuple[Any, ...], int]:
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


def _is_valid_time(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0


def _require_fields(data: dict[str, Any], fields: list[str], label: str, issues: list[str]) -> None:
    missing = [field for field in fields if field not in data]
    if missing:
        issues.append(f"{label} missing required field(s): {missing}.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate manual trace frame anchors.")
    parser.add_argument("--trace", required=True)
    parser.add_argument("--anchors", required=True)
    args = parser.parse_args(argv)
    try:
        issues = validate_frame_anchor_files(args.trace, args.anchors)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL frame anchor validation could not run: {exc}")
        return 2
    if issues:
        print(f"FAIL frame anchor validation found {len(issues)} issue(s).")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("PASS frame anchor validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
