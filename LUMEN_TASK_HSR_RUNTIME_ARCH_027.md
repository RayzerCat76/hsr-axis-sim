# HSR-RUNTIME-ARCH-027 — Reviewed Static Skill-Point Consume Observation Golden Fixture

## Current confirmed state

- HSR-RUNTIME-ARCH-026 — PASS — proceed.
- Accepted main merge commit before this task: `30d092d0b943659a2067668dc481f0fc7e052289`.
- Last confirmed final-head validation:
  - `1261 passed`;
  - legacy regression `20/20`;
  - trace evidence `2/2`;
  - standalone runtime action-session Golden regression `4/4`.

## Execution recommendation

- ChatGPT model: GPT-5.6 Sol.
- Codex reasoning: High if Codex is used.

## Objective

Add one manually reviewed static schema-v1 Golden expectation for a successful production `ConsumeSkillPoint` action and validate it through accepted ARCH-016 without changing simulator/runtime implementation or promoting it into a regression manifest yet.

## Required fixture contract

- actor ID: `sp-consume-actor`;
- action ID/name: `reviewed-skill-point-consume`;
- initial team SP: `4`;
- max team SP: `5`;
- one `ConsumeSkillPoint(amount=2)` effect;
- `ends_turn=False`.

Expected trace:

1. `ACTION_START`;
2. `SKILL_POINTS_CHANGED`;
3. `ACTION_END`.

Expected resource observation:

- `resource_kind="SKILL_POINTS"`;
- `scope="TEAM"`;
- `before=4`;
- `after=2`;
- `requested_delta=-2`;
- `applied_delta=-2`;
- `cap=5`;
- `unit_id=null`;
- runtime `target_id=null`.

Expected bytes must be compact canonical UTF-8 JSON, no trailing newline, manually reviewed, and must not be generated at test runtime from simulator/adapter/exporter/canonical serialization helpers.

## Acceptance criteria

- Fixed reviewed byte size and SHA-256 asserted.
- Strict compact-only loader with digest match accepts the artifact.
- Every schema-v1 record has `numeric_values == {}`.
- Accepted ARCH-016 production execution matches the artifact.
- Final team SP is exactly `2`.
- Pending events are `action_started`, `skill_points_changed`, `action_finished`.
- Final capture cursor is `(3, 3)`.
- Controlled actual-only mutation `ConsumeSkillPoint.amount=2 -> 1` produces a normal Golden mismatch on resource record index 1 and proves expected signed values `-2/-2` versus actual `-1/-1`, with actual final SP 3.
- The new fixture remains outside both regression manifests.
- ARCH-017/021/023/025 fixture identities remain unchanged.
- Runtime Golden lane remains `4/4`.
- Legacy regression remains `20/20`; trace evidence `2/2`; LIFO unchanged.

## Required tests

Cover exact bytes/digest/canonicality, trace identity/order/provenance, TEAM resource payload, ARCH-016 production PASS, controlled mismatch, manifest absence, expected-generation AST guard, prior fixture identities, runtime lane 4/4, legacy/trace preservation, and LIFO preservation.

## Files / areas that must remain unchanged

Do not modify:

- `hsr_axis_sim/sim/**`;
- runtime adapters or trace schema;
- loaders/exporters/comparator/divergence/Golden validator;
- either regression manifest;
- existing static fixture bytes;
- AV/timeline/extra-turn mechanics.

## Explicit exclusions

- insufficient-SP failure behavior;
- regression promotion/schema v1.4;
- generic effect DSL;
- Energy changes;
- AV/speed/advance/delay/immediate-action work;
- character/release-game data;
- video automation;
- FIFO/LIFO changes.

## Commands

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Final report

Update `hsr_axis_sim/LUMEN_RESULT.md` with task ID, implementation summary, files, tests, exact commands/results, warnings/errors, unresolved issues, exclusions confirmation, and suggested next milestone.
