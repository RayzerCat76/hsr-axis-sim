# HSR-RUNTIME-ARCH-045 — GrantExtraTurn Static Golden Regression Promotion

## Current confirmed state

- Canonical accepted `main`: `edd8664b6d49ea0d09417ac33c88b569eb16a433`.
- HSR-RUNTIME-ARCH-044 is accepted and merged.
- Post-merge GitHub Actions run #267 passed:
  - pytest: `1721 passed in 7.72s`
  - legacy regression: `20/20`
  - trace evidence: `2/2`
  - runtime action-session Golden regression: `9/9`
- ARCH-044 static fixture is already reviewed and locked:
  - path: `hsr_axis_sim/data/runtime_golden_fixtures/arch_044_reviewed_grant_extra_turn_expected.json`
  - size: `2658` bytes
  - SHA-256: `57eefb521cb5cf1840e49c36e5c9c85a08281a7014c23ece0e3d5df1e6dfefdd`
- Accepted production GrantExtraTurn behavior remains simulator-defined LIFO. This task must not modify production scheduling semantics.

## Objective

Promote the already-reviewed ARCH-044 GrantExtraTurn static Golden fixture into the standalone runtime action-session regression lane as the tenth locked case.

The current v1.8 runtime regression grammar cannot represent GrantExtraTurn. Extend only that regression grammar/runner to v1.9 with one explicit `GRANT_EXTRA_TURN` setup kind, then register the ARCH-044 fixture as case 10.

## Required implementation

### 1. Version the runtime regression grammar to v1.9

In `hsr_axis_sim/runtime_action_session_regression/manifest.py`:

- Freeze a historical constant `RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_8 = "1.8"`.
- Set `RUNTIME_ACTION_SESSION_REGRESSION_VERSION = "1.9"`.
- `RUNTIME_ACTION_SESSION_REGRESSION_SUPPORTED_VERSIONS` must be exactly `1.0` through `1.9` in order.
- Preserve every prior setup kind at every previously accepted version.
- In particular:
  - `IMMEDIATE_ACTION` must remain valid in v1.8 and must also be valid in v1.9.
  - v1.7 must still reject `IMMEDIATE_ACTION` as requiring v1.8 or later.
  - `GRANT_EXTRA_TURN` must be v1.9-only syntax.

### 2. Add one closed GrantExtraTurn setup contract

Add frozen dataclass:

`RuntimeActionSessionRegressionGrantExtraTurnSetup`

with exactly these fields:

- `target_id: str`
- `target_name: str`
- `team: str`
- `base_speed: float`
- `initial_av: float`
- `action_index: int`

Validation must match the already-established axis setup conventions:

- identity fields are non-empty strings;
- `base_speed` and `initial_av` are finite non-boolean numbers;
- `base_speed > 0`;
- `action_index` is an exact nonnegative integer and must address a declared action;
- do not add an invented range restriction for `initial_av`.

The setup parser must accept exactly:

```json
{
  "kind": "GRANT_EXTRA_TURN",
  "target_id": "...",
  "target_name": "...",
  "team": "...",
  "base_speed": 100,
  "initial_av": 80,
  "action_index": 0
}
```

No generic effect-class names, arbitrary kwargs, dynamic import, eval/exec, or reflection grammar is allowed.

### 3. Extend only the standalone runtime regression runner

In `hsr_axis_sim/runtime_action_session_regression/runner.py`:

- import the new setup dataclass;
- import production `GrantExtraTurn` from `hsr_axis_sim.sim.effects`;
- for this setup, create the declared target `Unit` with the setup identity/base-speed/current-AV values;
- on the configured action index, attach exactly:

```python
GrantExtraTurn(target_ids=[setup.target_id])
```

Do not preload the extra-turn stack for the locked regression case. Expected queue observation is therefore `0 -> 1`.

Do not change Timeline or GrantExtraTurn production logic.

### 4. Promote ARCH-044 as the tenth manifest case

Update `hsr_axis_sim/data/runtime_action_session_regression_manifest.json`:

- version becomes `1.9`;
- preserve the existing first nine cases byte-for-byte semantically and in the same order;
- append exactly one tenth case:
  - id: `arch-044-reviewed-static-grant-extra-turn`
  - expected path: `hsr_axis_sim/data/runtime_golden_fixtures/arch_044_reviewed_grant_extra_turn_expected.json`
  - expected SHA-256: `57eefb521cb5cf1840e49c36e5c9c85a08281a7014c23ece0e3d5df1e6dfefdd`
  - stream id: `arch-044-reviewed-axis`
  - actor id: `extra-turn-actor`
  - one action:
    - action id: `reviewed-grant-extra-turn`
    - name: `reviewed-grant-extra-turn`
    - ends_turn: `false`
  - setup:
    - kind: `GRANT_EXTRA_TURN`
    - target_id: `extra-turn-target`
    - target_name: `Extra Turn Target`
    - team: `ally`
    - base_speed: `100`
    - initial_av: `80`
    - action_index: `0`

### 5. Add focused ARCH-045 tests

Add `hsr_axis_sim/tests/test_runtime_arch_045_grant_extra_turn_regression_promotion.py` following the accepted ARCH-042 promotion pattern.

It must cover at minimum:

- supported versions are exactly v1.0 through v1.9;
- v1.8 rejects `GRANT_EXTRA_TURN` as v1.9 syntax;
- v1.9 accepts the exact frozen GrantExtraTurn setup;
- `IMMEDIATE_ACTION` remains accepted in both v1.8 and v1.9 and remains rejected in v1.7;
- exact setup fields;
- non-empty identity validation;
- finite/non-boolean numeric validation;
- positive base speed;
- strict action-index validation;
- no new initial-AV range restriction;
- locked v1.9 manifest has exactly ten cases in the expected order;
- tenth case exact path/digest/stream/actor/action/setup;
- runtime lane passes exactly `10/10`;
- record counts are `[4, 3, 3, 3, 3, 3, 3, 3, 3, 3]`;
- all ten expected fixture byte identities remain exact;
- the first nine accepted actual runtime digests remain exactly:
  1. `452d52be7dec07ddebe0ca5ec0ca3cf58d695bd2312ada684d70aa22891435d0`
  2. `80dda34881d32267ff819e985d7ed95256185e0c539f6e1b313aa67afcab9d3a`
  3. `0004d8947f3b7ce8e692af527f40579db94609e4ed3ae0b63bf40397ec4af043`
  4. `230e21dc23da2c37d89f26903dbd636463f5b0ec9adc7298e99331f3e24efb5f`
  5. `7a945e7016ffa4a6c074f563d7f0edf288239e92f596810cd434922e8fd5c525`
  6. `13d26b8efcb0db450445c036f49b31eec4ca346ca9d714f7e221bc084941a6ca`
  7. `c47754957a756bd03624aafdcd78e14ecbaed059cce0c99fddb0d116c88bde77`
  8. `a75555d3544a27638781a274a01ff8ee031e6394369be5c3c93c32dfed4c6698`
  9. `b41181b9bb09ec516d27f78a99ef455a69c2b5e678d93f8eaa5f94effdde8cb7`
- a controlled regression mismatch by changing the tenth setup target `initial_av` is not suitable because GrantExtraTurn does not observe AV; instead use a safe grammar-visible mismatch that actually changes captured GrantExtraTurn output. Prefer constructing a one-case harness variant whose target id differs consistently in setup but retains the locked expected fixture, then assert the first deterministic typed divergence path and values. Do not mutate production semantics to manufacture a mismatch.
- the regression harness is closed and explicitly targeted: no importlib/eval/exec/generic effect class or kwargs grammar;
- ARCH-044 fixture remains absent from the legacy regression manifest;
- legacy regression remains `20/20`;
- trace evidence remains `2/2`;
- production LIFO compatibility remains unchanged.

### 6. Narrowly update stale historical guards

Only where later authorization makes an older assertion factually stale:

- `test_runtime_arch_042_immediate_action_regression_promotion.py`
  - preserve the historical v1.8 ImmediateAction contract;
  - update assumptions that v1.8 is the latest version;
  - permit the later-authorized `GrantExtraTurn` only in the runtime regression harness while retaining all generic/dynamic-harness prohibitions.
- `test_runtime_arch_044_static_grant_extra_turn_golden_fixture.py`
  - replace the now-stale assertion that ARCH-044 is absent from the runtime regression manifest with an assertion that it is promoted exactly once as the tenth locked case;
  - update its runtime lane expectation from `9/9` to `10/10` while preserving prior-nine identity checks.

If CI reveals another stale source/count/version guard, change it only if the failure is directly caused by this authorized v1.9 promotion. No unrelated cleanup.

### 7. Update `hsr_axis_sim/LUMEN_RESULT.md`

After real tests pass, report:

- task ID;
- implementation summary;
- files added/modified;
- tests added/updated;
- exact commands executed;
- exact pass/fail counts and timings;
- runtime lane `10/10` result;
- first nine actual digest preservation;
- unresolved issues;
- exclusions respected;
- suggested next smallest milestone.

## Acceptance criteria

ARCH-045 passes only when all are true:

1. v1.9 is the current runtime action-session regression grammar and v1.0-v1.8 remain backward compatible.
2. `GRANT_EXTRA_TURN` is explicit, closed, and v1.9-only.
3. ARCH-044 is the tenth and only new runtime regression case.
4. Runtime regression passes `10/10`.
5. First nine case order, expected fixture identities, record counts, and actual runtime digests remain unchanged.
6. Tenth case matches the locked ARCH-044 static Golden exactly.
7. No production simulator file changes.
8. No Timeline changes.
9. No changes to the ARCH-044 static fixture bytes.
10. Legacy regression remains `20/20` and trace evidence remains `2/2`.
11. Full pytest passes.
12. `LUMEN_RESULT.md` is updated with real results only.

## Files/areas that must remain unchanged

Unless an evidence-backed stale test guard requires a narrow test-only update, do not modify:

- `hsr_axis_sim/sim/**`
- `hsr_axis_sim/runtime_contracts/**`
- `hsr_axis_sim/runtime_adapters/**`
- `hsr_axis_sim/runtime_action_sessions/**`
- `hsr_axis_sim/runtime_action_session_validation/**`
- comparator/divergence logic
- trace schema/export/load logic
- `hsr_axis_sim/data/runtime_golden_fixtures/arch_044_reviewed_grant_extra_turn_expected.json`
- `hsr_axis_sim/data/regression_manifest.json`
- any other Golden fixture

## Explicit exclusions

- No changes to production GrantExtraTurn behavior.
- No changes to production extra-turn LIFO ordering.
- No real-HSR scheduling/priority claims.
- No extra-turn priority, interrupt, or queue-policy model.
- No generic regression effect grammar.
- No automatic fixture generation.
- No new Golden fixture.
- No unrelated refactors, docs cleanup, character data, damage work, UI, scraping, video parsing, or optimization.

## Commands to run

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Required final report format

Report exactly:

1. Task ID
2. Implementation summary
3. Files added/modified
4. Tests added/updated
5. Exact commands executed
6. Exact pass/fail results
7. Runtime regression case count/result and actual digests
8. Unresolved issues
9. Confirmation exclusions were respected
10. Suggested next smallest milestone
11. Confirmation `LUMEN_RESULT.md` was updated

## Execution routing

- ChatGPT model: **GPT-5.6 Terra**
- Codex reasoning: **High**

This is a normal deterministic regression-harness extension around already accepted production semantics; it does not require changing core turn-order behavior.