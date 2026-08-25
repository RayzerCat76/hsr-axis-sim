# HSR-RUNTIME-ARCH-027 — Reviewed Static Skill-Point Consume Observation Golden Fixture

## Status

PASS — proceed

## Implementation summary

- Added one independently reviewed static schema-v1 Golden expectation for successful production `ConsumeSkillPoint`.
- Static fixture: `hsr_axis_sim/data/runtime_golden_fixtures/arch_027_reviewed_skill_point_consume_expected.json`.
- Exact fixture identity:
  - 2796 bytes;
  - SHA-256 `d0dcf128f3a28f691324f4e9295b7bcd66460598186f6059d4619f55e8ae39ec`;
  - compact canonical UTF-8 JSON;
  - no trailing newline;
  - trace ID `arch-027-reviewed-static-expected`.
- Reviewed scenario:
  - actor `sp-consume-actor`;
  - initial team SP `4`, max `5`;
  - action `reviewed-skill-point-consume`;
  - one `ConsumeSkillPoint(amount=2)`;
  - `ends_turn=False`.
- Expected trace is exactly `ACTION_START -> SKILL_POINTS_CHANGED -> ACTION_END`.
- Resource observation locks:
  - `resource_kind=SKILL_POINTS`;
  - `scope=TEAM`;
  - `before=4`;
  - `after=2`;
  - `requested_delta=-2`;
  - `applied_delta=-2`;
  - `cap=5`;
  - `unit_id=null`;
  - runtime `target_id=null`.
- Accepted ARCH-016 production execution matches the static expected artifact.
- Controlled actual-only mutation `ConsumeSkillPoint.amount=2 -> 1` produces a normal Golden mismatch on record index 1, path `/event/payload/legacy_data/after`, expected `2`, actual `3`; signed deltas change from `-2/-2` to `-1/-1`.
- New fixture remains absent from both regression manifests; standalone runtime lane remains 4/4.
- No simulator/runtime implementation was changed.

## Files added

- `LUMEN_TASK_HSR_RUNTIME_ARCH_027.md`
- `hsr_axis_sim/data/runtime_golden_fixtures/arch_027_reviewed_skill_point_consume_expected.json`
- `hsr_axis_sim/tests/test_runtime_arch_027_static_skill_point_consume_golden_fixture.py`

## Files modified

- `hsr_axis_sim/LUMEN_RESULT.md`

## Tests added

ARCH-027 focused coverage proves:

- exact static byte size/digest/no trailing newline;
- strict compact loader acceptance with required digest match;
- exact schema-v1 trace identity and contiguous sequence policy;
- exact three-record order and actor/action provenance;
- TEAM scope with `unit_id=null` and runtime `target_id=null`;
- exact structured `resource_change` and defensive `legacy_data` payloads;
- every schema-v1 record has `numeric_values == {}`;
- ARCH-016 production Golden PASS;
- final SP `2`, exact pending-event order, cursor `(3,3)`;
- controlled amount `2 -> 1` mismatch and signed resource differences;
- fixture absence from both regression manifests;
- AST guard against runtime expected-artifact generation helpers;
- ARCH-017/021/023/025 byte identities unchanged;
- standalone runtime regression remains `4/4`;
- legacy regression `20/20`, trace evidence `2/2`, LIFO unchanged.

## Exact validation commands and real results

GitHub Actions workflow `HSR Axis Sim Validation`, PR #32, run #146, job `validate` (`97651999408`).

1. `python -m compileall -q hsr_axis_sim`
   - PASS.
2. `python -m pytest -q`
   - PASS: `1269 passed in 8.31s`.
3. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text`
   - PASS legacy locked regression `20/20`.
4. `python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text`
   - PASS `2/2` trace-evidence checks.
5. `python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text`
   - PASS `4/4` runtime action-session Golden checks with record counts `4,3,3,3`.

The first ARCH-027 PR CI was green; no implementation correction was required.

## Warnings / errors

- No compile, fixture-integrity, strict-loader, ARCH-016, comparator/divergence, legacy-regression, trace-evidence, or runtime-regression error was observed.
- Existing GitHub Actions Node 20 deprecation warning remains nonblocking and unrelated to ARCH-027 correctness.

## Acceptance review

- Expected bytes are static, reviewed, compact, and digest-pinned.
- Expected bytes are not generated at test runtime from simulator/adapter/export/canonical helpers.
- Successful Skill-Point consumption is locked as a negative TEAM-resource observation through accepted ARCH-016.
- Insufficient-SP behavior remains deliberately separate.
- Both regression manifests remain unchanged and runtime lane stays 4/4.
- Prior reviewed static fixtures remain unchanged.
- Trace schema v1 and production LIFO compatibility remain unchanged.
- No hidden HSR/release-game values were inferred; fixture values are explicit contract-only inputs.

## Unresolved issues

None blocking HSR-RUNTIME-ARCH-027 acceptance.

The SP-consume fixture is intentionally not yet in the standalone runtime regression lane. Promotion requires one separate narrow manifest version milestone.

Insufficient resource failure semantics remain separate from successful observation semantics.

## Suggested next milestone

`HSR-RUNTIME-ARCH-028 — Skill-Point Consume Static Golden Regression Promotion`

ARCH-028 should promote the accepted ARCH-027 fixture as the fifth standalone runtime Golden case through explicit manifest v1.4. Add only `SKILL_POINT_CONSUME`, preserve v1.0-v1.3 grammars exactly, keep insufficient-SP failure separate, avoid a generic effect DSL, and require runtime regression `5/5`.
