# HSR-RUNTIME-ARCH-032 — Reviewed Static Advance Action Observation Golden Fixture

## Current confirmed state

- HSR-RUNTIME-ARCH-031 — PASS — proceed.
- Accepted main merge commit before this task: `f7d243570e75baf973b7c17bb05b56073a51273b`.
- Last confirmed final-head validation:
  - `1340 passed`;
  - legacy regression `20/20`;
  - trace evidence `2/2`;
  - standalone runtime action-session Golden regression `5/5`.
- Accepted ARCH-031 contract:
  - production `AdvanceAction` keeps `max(0, before_av - base_av * percent)`;
  - one post-mutation legacy `action_advanced` event per advanced Unit;
  - typed `RuntimeEventType.ACTION_VALUE_ADVANCED`;
  - validated `payload["action_advance"]` through frozen `RuntimeActionAdvanceObservation`;
  - schema v1 unchanged;
  - Delay/ChangeSpeed/ImmediateAction/GrantExtraTurn remain out of scope.

## Execution recommendation

- ChatGPT model: GPT-5.6 Sol.
- Codex reasoning: High if Codex is used.

## Objective

Add one independently reviewed, manually constructed compact schema-v1 Golden expectation for a deterministic non-clamped production `AdvanceAction`, then prove accepted ARCH-016 end-to-end execution matches those static bytes exactly at the record-comparison boundary.

The expected artifact must not be generated from simulator/runtime adapter/exporter output at test runtime.

## Controlled reviewed scenario

Use exactly:

- fixture id: `arch-032-reviewed-static-action-advance`;
- stream id: `arch-032-reviewed-axis`;
- actor/target Unit id: `advance-actor`;
- action id: `reviewed-action-advance`;
- team: `ally`;
- speed/base speed: `100`;
- starting `current_av`: `80`;
- `AdvanceAction(percent=0.5)`;
- `ends_turn=False`;
- expected final AV: `30`.

Expected action-advance observation:

- `target_id="advance-actor"`;
- `before_av=80`;
- `after_av=30.0`;
- `base_av=100.0`;
- `requested_percent=0.5`;
- `requested_delta_av=-50.0`;
- `applied_delta_av=-50.0`;
- `clamped_to_zero=false`.

Expected legacy event order:

```text
action_started
-> action_advanced
-> action_finished
```

Expected typed record order:

```text
ACTION_START
-> ACTION_VALUE_ADVANCED
-> ACTION_END
```

## Required implementation

### Static expected artifact

Add exactly one compact canonical UTF-8 JSON fixture:

`hsr_axis_sim/data/runtime_golden_fixtures/arch_032_reviewed_action_advance_expected.json`

Requirements:

- schema name `hsr_runtime_trace`;
- schema version `1.0`;
- contiguous sequences `0,1,2`;
- exactly three records;
- trace id `arch-032-reviewed-static-expected`;
- metadata:
  - `construction="manual-reviewed"`;
  - `fixture_id="arch-032-reviewed-static-action-advance"`;
  - `purpose="action-advance-end-to-end-golden"`;
- no trailing newline;
- exact bytes and SHA-256 pinned in tests after construction;
- middle record uses `ACTION_VALUE_ADVANCED` with normalized actor/action/target ids;
- raw `legacy_data` and structured `action_advance` both contain the exact accepted ARCH-031 observation values;
- every record keeps `numeric_values={}`.

Do not create the expected fixture by calling simulator execution, `adapt_legacy_event`, runtime trace builders/exporters, canonical project helpers, or ARCH-016.

Using ordinary text/manual JSON construction and independent digest calculation is allowed.

### Production match

Build the controlled scenario using accepted production objects and call accepted `run_action_session_validation` against the static expected bytes.

Prove:

- result matches;
- final Unit AV is `30`;
- pending event order is exactly the three expected legacy events;
- final session cursor is `(3,3)`;
- Golden expected digest is the pinned static fixture digest;
- no first divergence exists.

### Controlled mismatch

Change production input only:

```text
AdvanceAction.percent = 0.4
```

Keep the same reviewed expected fixture.

Prove normal Golden mismatch:

- actual final AV `40.0`;
- first divergent record index `1`;
- first field path `/event/payload/action_advance/after_av`;
- expected value `30.0`;
- actual value `40.0`;
- requested percent/delta and applied delta differ consistently.

### Manifest isolation

ARCH-032 is fixture-only review work.

The new fixture and fixture id must remain absent from:

- `hsr_axis_sim/data/regression_manifest.json`;
- `hsr_axis_sim/data/runtime_action_session_regression_manifest.json`.

Standalone runtime lane must remain exactly `5/5`.

## Acceptance criteria

- One manually reviewed static compact schema-v1 fixture exists at the exact requested path.
- Fixture byte size and SHA-256 are explicitly pinned and validated.
- Fixture has no trailing newline.
- Strict loader accepts it only with matching pinned digest.
- Exact three-record order is `ACTION_START`, `ACTION_VALUE_ADVANCED`, `ACTION_END`.
- Advance record contains exact target provenance and exact raw/structured ARCH-031 observation values.
- Every record has empty `numeric_values`.
- Accepted ARCH-016 production scenario matches the static expected trace.
- Controlled percent `0.4` mismatch reports record index `1`, path `/event/payload/action_advance/after_av`, expected `30.0`, actual `40.0`.
- New fixture is absent from both regression manifests.
- Existing reviewed static fixture identities remain unchanged.
- Standalone runtime lane remains `5/5`.
- Legacy regression remains `20/20`.
- Trace evidence remains `2/2`.
- Production LIFO remains unchanged.

## Required tests

Add focused ARCH-032 tests covering:

1. exact fixture bytes, size, digest, no trailing newline;
2. strict compact loader + digest match;
3. exact schema/trace identity, record count and sequence;
4. exact event order and actor/action/target provenance;
5. exact `legacy_data` and `action_advance` payload;
6. empty record-level `numeric_values`;
7. ARCH-016 production match and final AV/cursor/events;
8. controlled percent `0.4` first divergence and signed delta differences;
9. AST/source guard against runtime expected-fixture generation;
10. absence from both regression manifests;
11. all prior reviewed static fixture byte identities unchanged;
12. current standalone runtime regression `5/5`;
13. legacy regression `20/20` and trace evidence `2/2`;
14. production LIFO unchanged.

## Must remain unchanged

Do not modify:

- `hsr_axis_sim/sim/**`;
- `hsr_axis_sim/runtime_contracts/**`;
- `hsr_axis_sim/runtime_adapters/**`;
- runtime loaders/exporters/comparators/divergence/Golden validators;
- both regression manifests;
- prior reviewed static fixture bytes;
- Delay/ChangeSpeed/ImmediateAction/GrantExtraTurn semantics;
- AV formula or ARCH-031 event semantics.

## Explicit exclusions

- runtime regression promotion of ARCH-032;
- clamped Advance static Golden fixture;
- Delay observation;
- speed-change observation;
- immediate-action observation;
- extra-turn observation;
- generic action-axis effect DSL;
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

Update `hsr_axis_sim/LUMEN_RESULT.md` with task ID, implementation summary, files, tests, exact commands/results, any initial failures/fixes, warnings/errors, unresolved issues, exclusion confirmation, and suggested next milestone.
