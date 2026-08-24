from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ACTION_SEQUENCE_ONLY_CHECK_MODE = "action_sequence_only"
UNKNOWN_MARKERS = {"unknown", "skip"}
NUMERIC_OBSERVABLE_FIELDS = {
    "skill_points",
    "energy",
    "hp",
    "toughness",
    "damage",
    "forced_rng",
}


def lint_manual_video_trace(replay_data: dict[str, Any]) -> list[str]:
    if _is_action_sequence_only_trace(replay_data):
        return lint_action_sequence_only_trace(replay_data)

    if _is_manual_video_trace_intake(replay_data):
        return lint_manual_video_trace_intake(replay_data)

    if replay_data.get("trace_type") != "manual_video_trace":
        return []

    issues: list[str] = []
    _require_field(replay_data, "name", "top-level", issues)
    _require_field(replay_data, "source", "top-level", issues)
    source = replay_data.get("source")
    if isinstance(source, dict):
        for field_name in ["platform", "video_title", "recorded_by"]:
            _require_field(source, field_name, "source", issues)
    elif "source" in replay_data:
        issues.append("source must be an object.")

    if not isinstance(replay_data.get("assumptions"), list):
        issues.append("assumptions must be a list.")
    if not isinstance(replay_data.get("builds"), dict):
        issues.append("builds must be an object.")
    if not isinstance(replay_data.get("transcription"), dict):
        issues.append("transcription must be an object.")

    steps = replay_data.get("steps")
    if not isinstance(steps, list) or not steps:
        issues.append("steps must be a non-empty list.")
        return issues

    for index, step in enumerate(steps):
        step_label = f"steps[{index}]"
        if not isinstance(step, dict):
            issues.append(f"{step_label} must be an object.")
            continue
        _require_field(step, "step", step_label, issues)
        if not any(field_name in step for field_name in ["skill_id", "action_id", "use_enemy_ai"]):
            issues.append(
                f"{step_label} must include one of skill_id, action_id, or use_enemy_ai."
            )

        step_type = step.get("step_type", "normal")
        if (
            step_type == "normal"
            and "expected_actor" not in step
            and not step.get("allow_missing_expected_actor", False)
        ):
            issues.append(
                f"{step_label} normal step requires expected_actor unless "
                "allow_missing_expected_actor is true."
            )

        if "forced_rng" in step and not isinstance(step["forced_rng"], dict):
            issues.append(f"{step_label}.forced_rng must be an object.")
        if "expect" in step and not isinstance(step["expect"], dict):
            issues.append(f"{step_label}.expect must be an object.")

    return issues


def lint_action_sequence_only_trace(replay_data: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field_name in [
        "name",
        "source",
        "scenario",
        "team",
        "check_mode",
        "unknown_allowed",
        "numeric_expectations",
        "steps",
    ]:
        _require_field(replay_data, field_name, "top-level", issues)

    if replay_data.get("check_mode") != ACTION_SEQUENCE_ONLY_CHECK_MODE:
        issues.append("check_mode must be 'action_sequence_only'.")
    unknown_allowed = replay_data.get("unknown_allowed")
    if unknown_allowed is not True:
        issues.append("unknown_allowed must be true for action_sequence_only traces.")
    if replay_data.get("numeric_expectations") != "skip":
        issues.append("numeric_expectations must be 'skip' for action_sequence_only traces.")

    source = replay_data.get("source")
    if isinstance(source, dict):
        for field_name in ["type", "platform", "url", "title"]:
            _require_field(source, field_name, "source", issues)
        if source.get("type") != "manual_video_trace":
            issues.append("source.type must be 'manual_video_trace'.")
        _check_unknown_marker(source.get("url"), "source.url", unknown_allowed, issues)
        _check_unknown_marker(source.get("title"), "source.title", unknown_allowed, issues)
    elif "source" in replay_data:
        issues.append("source must be an object.")

    scenario = replay_data.get("scenario")
    if isinstance(scenario, dict):
        for field_name in ["game_context", "mode", "floor", "side"]:
            _require_field(scenario, field_name, "scenario", issues)
    elif "scenario" in replay_data:
        issues.append("scenario must be an object.")

    team = replay_data.get("team")
    if not isinstance(team, list) or not team:
        issues.append("team must be a non-empty list.")
    else:
        for index, unit in enumerate(team):
            label = f"team[{index}]"
            if not isinstance(unit, dict):
                issues.append(f"{label} must be an object.")
                continue
            _require_field(unit, "unit_id", label, issues)
            _require_field(unit, "character", label, issues)

    prebattle = replay_data.get("prebattle")
    if prebattle is not None:
        if not isinstance(prebattle, list):
            issues.append("prebattle must be a list when present.")
        else:
            for index, action in enumerate(prebattle):
                label = f"prebattle[{index}]"
                if not isinstance(action, dict):
                    issues.append(f"{label} must be an object.")
                    continue
                _require_field(action, "actor", label, issues)
                _require_field(action, "action", label, issues)

    steps = replay_data.get("steps")
    if not isinstance(steps, list) or not steps:
        issues.append("steps must be a non-empty list.")
        return issues

    for index, step in enumerate(steps):
        label = f"steps[{index}]"
        if not isinstance(step, dict):
            issues.append(f"{label} must be an object.")
            continue
        _require_field(step, "step", label, issues)
        _require_field(step, "actor", label, issues)
        _require_field(step, "action", label, issues)
        _require_field(step, "target", label, issues)
        _require_field(step, "target_confidence", label, issues)
        if step.get("step") != index + 1:
            issues.append(f"{label}.step must be {index + 1}.")

        for field_name in ["video_timestamp", "target", "target_confidence"]:
            _check_unknown_marker(
                step.get(field_name),
                f"{label}.{field_name}",
                unknown_allowed,
                issues,
            )

        observable = step.get("observable")
        if not isinstance(observable, dict):
            issues.append(f"{label}.observable must be an object.")
            continue
        if observable.get("actor_action_sequence") is not True:
            issues.append(f"{label}.observable.actor_action_sequence must be true.")
        for field_name, value in observable.items():
            if field_name == "actor_action_sequence":
                continue
            _check_unknown_marker(
                value,
                f"{label}.observable.{field_name}",
                unknown_allowed,
                issues,
            )
            if field_name in NUMERIC_OBSERVABLE_FIELDS and value not in UNKNOWN_MARKERS:
                issues.append(
                    f"{label}.observable.{field_name} must be 'unknown' or 'skip' "
                    "when numeric_expectations is 'skip'."
                )

        if "expect" in step and step["expect"] not in ({}, "unknown", "skip"):
            issues.append(
                f"{label}.expect must be omitted, empty, 'unknown', or 'skip' "
                "when numeric_expectations is 'skip'."
            )

    return issues


def lint_manual_video_trace_intake(replay_data: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    _require_field(replay_data, "name", "top-level", issues)
    _require_field(replay_data, "status", "top-level", issues)
    _require_field(replay_data, "source", "top-level", issues)

    source = replay_data.get("source")
    if isinstance(source, dict):
        for field_name in ["platform", "url", "title", "scenario"]:
            _require_field(source, field_name, "source", issues)
    elif "source" in replay_data:
        issues.append("source must be an object.")

    team = replay_data.get("team")
    if not isinstance(team, list) or not team:
        issues.append("team must be a non-empty list.")
    else:
        for index, unit in enumerate(team):
            label = f"team[{index}]"
            if not isinstance(unit, dict):
                issues.append(f"{label} must be an object.")
                continue
            _require_field(unit, "unit_id", label, issues)
            _require_field(unit, "display_name", label, issues)

    precombat = replay_data.get("precombat")
    if precombat is not None and not isinstance(precombat, list):
        issues.append("precombat must be a list when present.")

    steps = replay_data.get("steps")
    if not isinstance(steps, list) or not steps:
        issues.append("steps must be a non-empty list.")
        return issues

    for index, step in enumerate(steps):
        label = f"steps[{index}]"
        if not isinstance(step, dict):
            issues.append(f"{label} must be an object.")
            continue
        for field_name in ["step", "expected_actor", "action_kind", "action_label_cn"]:
            _require_field(step, field_name, label, issues)
        if "expect" in step and not isinstance(step["expect"], dict):
            issues.append(f"{label}.expect must be an object.")
        if "forced_rng" in step and not isinstance(step["forced_rng"], dict):
            issues.append(f"{label}.forced_rng must be an object.")

    validation_policy = replay_data.get("validation_policy")
    if not isinstance(validation_policy, dict):
        issues.append("validation_policy must be an object.")
    else:
        if validation_policy.get("include_in_locked_manifest") is not False:
            issues.append("validation_policy.include_in_locked_manifest must be false for intake drafts.")
        if validation_policy.get("allow_missing_expect_fields") is not True:
            issues.append("validation_policy.allow_missing_expect_fields must be true for intake drafts.")

    return issues


def load_and_lint_manual_video_trace(path: str | Path) -> list[str]:
    with Path(path).open(encoding="utf-8") as replay_file:
        return lint_manual_video_trace(json.load(replay_file))


def _require_field(
    data: dict[str, Any],
    field_name: str,
    label: str,
    issues: list[str],
) -> None:
    if field_name not in data:
        issues.append(f"{label} missing required field {field_name!r}.")


def _check_unknown_marker(
    value: Any,
    label: str,
    unknown_allowed: Any,
    issues: list[str],
) -> None:
    if value in UNKNOWN_MARKERS and unknown_allowed is not True:
        issues.append(f"{label} uses {value!r}, but unknown_allowed is not true.")


def _is_action_sequence_only_trace(replay_data: dict[str, Any]) -> bool:
    return (
        replay_data.get("check_mode") == ACTION_SEQUENCE_ONLY_CHECK_MODE
        or "unknown_allowed" in replay_data
        or "numeric_expectations" in replay_data
    )


def _is_manual_video_trace_intake(replay_data: dict[str, Any]) -> bool:
    if replay_data.get("status") == "intake_sequence_confirmed_not_replay_ready":
        return True
    source = replay_data.get("source")
    validation_policy = replay_data.get("validation_policy")
    return (
        isinstance(source, dict)
        and source.get("type") == "manual_video_trace"
        and isinstance(validation_policy, dict)
        and validation_policy.get("include_in_locked_manifest") is False
    )


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("Usage: python -m hsr_axis_sim.sim.replay_lint <replay.json>", file=sys.stderr)
        return 2

    path = args[0]
    try:
        with Path(path).open(encoding="utf-8") as replay_file:
            replay_data = json.load(replay_file)
    except OSError as exc:
        print(f"Failed to load replay: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"Failed to parse replay JSON: {exc}", file=sys.stderr)
        return 2

    issues = lint_manual_video_trace(replay_data)
    replay_name = replay_data.get("name", "<unnamed replay>")
    if issues:
        print(f"FAIL {replay_name}: manual video trace lint found {len(issues)} issue(s).")
        for issue in issues:
            print(f"- {issue}")
        return 1

    if replay_data.get("check_mode") == ACTION_SEQUENCE_ONLY_CHECK_MODE:
        print(
            f"PASS {replay_name}: action-sequence-only manual video trace lint passed."
        )
    elif _is_manual_video_trace_intake(replay_data):
        print(f"PASS {replay_name}: manual video trace intake lint passed.")
    elif replay_data.get("trace_type") == "manual_video_trace":
        print(f"PASS {replay_name}: manual video trace lint passed.")
    else:
        print(f"PASS {replay_name}: not a manual video trace; lint skipped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
