# Lumen Review — HSR-AXIS-002Q Replacement After Codex

## Decision

**NEEDS FIX — do not start 002R yet.**

The evidence normalization, current-engine gap reproduction, preservation boundaries, deterministic reports, and full regression suite are correct. However, the validator does not strictly preserve several semantic fields that are explicitly classified as unresolved. A readable tampered review can therefore be accepted and rendered as a successful report containing invented release-game assertions.

## Independent gates

- `python -m compileall -q hsr_axis_sim`: PASS
- Complete pytest collection: **649 / 649 passed** across six non-overlapping groups
- Focused replacement-002Q tests: **76 / 76 passed**
- Locked regression: **PASS 20 / 20**
- Trace-evidence-only regression: **PASS 2 / 2**
- Generated Markdown and JSON: byte-identical to committed reports
- Diff against the previous package: only expected 002Q evidence/tool/test/report files plus `LUMEN_RESULT.md`
- No production Timeline, Unit, Buff, Effect, Action, event, trigger, state, binding, registry, manifest, search, or evaluator change

## Correct work

The submitted audit correctly preserves:

- two-turn duration as `source_cross_checked`;
- turn-entry settlement as `accepted_project_domain_correction_pending_independent_frame_verification`;
- the Bilibili page as candidate-only evidence;
- `GAP_TARGET_NORMAL_TURN_TICK_BOUNDARY` as a proven current-engine gap;
- zero-counter lifetime, extra-turn consumption, extra-action consumption, event order, refresh semantics, and global migration impact as unresolved;
- generic binding readiness as `blocked_by_duration_semantics`;
- simulator binding as disallowed.

The synthetic cases reproduce the pinned current engine correctly, including the observed `2 at entry -> 1 at normal-turn end` behavior.

## Blocking issue 1 — unresolved outputs can be invented

The validator checks claim IDs, statuses, and main `claim_value`, but it only applies nullable-string type validation to fields such as:

- `effect_active_during_entered_turn`
- `extra_action_consumes`
- `extra_turn_consumes`
- `refresh_behavior`
- `event_order_relative_to_turn_started`

It does not enforce that these fields remain `null` for unresolved claims.

The following tampered input was accepted by `build_report` and by the CLI:

```json
{
  "zero_counter_effect_lifetime.effect_active_during_entered_turn": "true",
  "extra_action_consumption.extra_action_consumes": "true",
  "extra_turn_consumption.extra_turn_consumes": "true"
}
```

Observed result:

```text
build_report: accepted
CLI exit: 0
traceback: none
rendered report contains all three invented assertions
```

This violates the task requirements that unresolved release-game outputs must not be invented and that extra-action, extra-turn, and zero-counter semantics remain unresolved.

## Blocking issue 2 — locator pins are not actually pinned

The task requires project and supplied sources to be pinned by **path, digest, and locator**.

`REFERENCE_PINS` and `PROJECT_PINS` currently contain only path and digest. `_source_pins` validates `locators` merely as a non-empty string list. Replacing any accepted locator with `"tampered"` is accepted and appears in the successful report.

Therefore the report is path/digest pinned, but not locator pinned.

## Related semantic-integrity gaps to close in the same narrow fix

The same exploratory mutation sweep showed that the validator also accepts:

- changed claim `source_ids` as long as they do not dangle;
- arbitrary replacements in `unresolved_fields`;
- arbitrary boundary-case unresolved-field labels;
- arbitrary claim scope/observable/current-engine descriptions;
- changed `review_id` and `version`.

Not every descriptive string needs a complicated parser. The safest solution for this versioned evidence artifact is an exact, data-driven semantic contract for every claim and boundary case.

## Required resolution

Create **HSR-AXIS-002Q-FIX** as validator/test hardening only:

1. Pin exact locator sets for every supplied and project source.
2. Define exact per-claim contracts for source IDs, status, value, nullable semantic outputs, and unresolved fields.
3. Force all unresolved semantic result fields to remain `null`.
4. Define exact per-boundary-case unresolved-field sets.
5. Lock the review ID and version.
6. Add negative tests for semantic string tampering, not only wrong JSON types.
7. Keep the existing normalized input and generated report bytes unchanged.
8. Preserve all runtime code, bindings, registry, manifest, and regression fixtures.

## Review status

`HSR-AXIS-002Q-REPLACEMENT = FAIL_PENDING_002Q_FIX`
