# HSR-RUNTIME-ARCH-036 — Delay Static Golden Regression Promotion

## 1. Task ID and title

**HSR-RUNTIME-ARCH-036 — Delay Static Golden Regression Promotion**

## 2. Current confirmed state

- HSR-RUNTIME-ARCH-035 — PASS — proceed.
- Accepted main merge commit before this task: `ceaa3fd02ee18d08ac983b733f6acbc85d8d373c`.
- Last confirmed ARCH-035 final-head validation:
  - `1441 passed`;
  - legacy regression `20/20`;
  - trace evidence `2/2`;
  - standalone runtime action-session Golden regression `6/6`.
- Accepted ARCH-035 reviewed static Delay fixture:
  - `hsr_axis_sim/data/runtime_golden_fixtures/arch_035_reviewed_action_delay_expected.json`;
  - exactly 2728 bytes;
  - SHA-256 `9efbb65defb5eacc12150d31d0530d9a94b43a42e2303ebca643911f98094c4d`.
- Accepted production Delay observation semantics from ARCH-034 are locked.
- Current standalone runtime action-session regression manifest version is `1.5` with six reviewed cases.
- Current blocker: none.

## Execution recommendation

- ChatGPT model: GPT-5.6 Terra for the routine manifest/runner implementation and tests; GPT-5.6 Sol remains the architecture reviewer because version compatibility is a deterministic contract.
- Codex reasoning: High if Codex is used.

## 3. Objective

Promote the already accepted ARCH-035 static Delay Golden expectation into the standalone runtime action-session regression lane as the seventh locked reviewed case.

Evolve the standalone manifest grammar from v1.5 to v1.6 only as much as needed to declare one explicit `ACTION_DELAY` setup. Preserve the complete v1.0-v1.5 grammar exactly, preserve all prior case ordering and fixture bytes, and continue delegating actual execution through the existing accepted runtime action-session validation pipeline.

## 4. Required implementation

### Manifest version evolution

In `hsr_axis_sim/runtime_action_session_regression/manifest.py`:

- add `RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_5 = "1.5"`;
- set current `RUNTIME_ACTION_SESSION_REGRESSION_VERSION = "1.6"`;
- supported versions must be exactly `1.0` through `1.6` in order;
- v1.0-v1.5 syntax must retain its previously accepted meaning.

In particular:

- `ACTION_ADVANCE` remains valid in v1.5 and is also valid in v1.6;
- `ACTION_ADVANCE` remains invalid in v1.4 and earlier;
- new `ACTION_DELAY` is valid only in v1.6;
- v1.5 and earlier must reject `ACTION_DELAY` rather than silently accepting or degrading it.

### Explicit Delay setup contract

Add a frozen dataclass:

```python
@dataclass(frozen=True)
class RuntimeActionSessionRegressionActionDelaySetup:
    target_id: str
    target_name: str
    team: str
    base_speed: float
    initial_av: float
    action_index: int
    percent: float
```

Keep it a distinct setup type. Do not introduce a generic action-axis/effect DSL or merge Advance/Delay into one polymorphic setup abstraction.

Add strict parsing for `kind = "ACTION_DELAY"` with exactly these fields:

- `kind`;
- `target_id`;
- `target_name`;
- `team`;
- `base_speed`;
- `initial_av`;
- `action_index`;
- `percent`.

Validation must mirror the accepted explicit Advance setup boundary:

- non-empty target/name/team strings;
- finite non-boolean `base_speed`, `initial_av`, and `percent`;
- positive `base_speed`;
- exact nonnegative integer action index within declared actions;
- no positivity restriction on Delay percent;
- no new lower bound on initial AV.

### Runner integration

In `hsr_axis_sim/runtime_action_session_regression/runner.py`:

- import `DelayAction`;
- import the new Delay setup type;
- construct one Unit for Delay setup using its exact target identity/team/base speed/initial AV;
- inject exactly `DelayAction(target_ids=[setup.target_id], percent=setup.percent)` only at the declared `action_index`;
- do not introduce dynamic class lookup, generic effect kwargs, importlib, eval/exec, or a generic effect DSL.

All resulting runtime trace and Golden comparison semantics must still come from the existing accepted orchestration.

### Locked seventh manifest case

Update `hsr_axis_sim/data/runtime_action_session_regression_manifest.json` to version `1.6` and append exactly one seventh case after the existing six:

```json
{
  "id": "arch-035-reviewed-static-action-delay",
  "expected_path": "hsr_axis_sim/data/runtime_golden_fixtures/arch_035_reviewed_action_delay_expected.json",
  "expected_sha256": "9efbb65defb5eacc12150d31d0530d9a94b43a42e2303ebca643911f98094c4d",
  "stream_id": "arch-035-reviewed-axis",
  "actor_id": "delay-actor",
  "actions": [
    {
      "action_id": "reviewed-action-delay",
      "name": "reviewed-action-delay",
      "ends_turn": false
    }
  ],
  "setup": {
    "kind": "ACTION_DELAY",
    "target_id": "delay-actor",
    "target_name": "Delay Actor",
    "team": "ally",
    "base_speed": 100,
    "initial_av": 30,
    "action_index": 0,
    "percent": 0.25
  }
}
```

Do not modify any static Golden fixture bytes.

## 5. Acceptance criteria

- Current standalone runtime manifest version is exactly `1.6`.
- An explicit v1.5 version constant is retained.
- Supported versions are exactly `("1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.6")`.
- v1.0-v1.5 grammar remains compatible with its previously accepted closed setup kinds.
- `ACTION_ADVANCE` parses in v1.5 and v1.6 and remains rejected in v1.4 and earlier.
- `ACTION_DELAY` parses only in v1.6 and is rejected in v1.5 and earlier.
- Delay setup is frozen and strictly validates exact fields/types/bounds without adding percent or initial-AV range semantics.
- Runner creates the declared Unit and a real production `DelayAction` at only the declared action index.
- Standalone manifest contains exactly seven cases, preserving the first six in exact accepted order and appending the ARCH-035 case as seventh.
- ARCH-035 fixture remains exactly 2728 bytes with the pinned SHA-256 unchanged.
- Standalone runtime action-session Golden regression passes exactly `7/7`.
- Seventh case produces exactly three runtime records and passes the accepted Golden record comparison against the pinned expected fixture.
- Seventh-case `expected_sha256` remains exactly the ARCH-035 fixture digest. `actual_sha256` remains an exposed deterministic identity of the generated actual trace artifact and is not required to equal the expected fixture digest because the accepted comparison permits differing trace/document metadata while comparing the canonical ordered runtime records.
- A controlled Delay setup mutation produces a Golden mismatch with accepted first divergence at record index 1 under `/event/payload/action_delay/...`, proving the harness executes Delay rather than an empty action.
- Legacy regression remains `20/20` and trace evidence remains `2/2`.
- Existing production LIFO compatibility remains unchanged.
- No simulator, runtime observation contract, legacy adapter, trace schema, comparator, divergence, or Golden semantics are changed.

## 6. Required tests

Add focused tests, preferably `hsr_axis_sim/tests/test_runtime_arch_036_action_delay_regression_promotion.py`, covering:

1. exact supported version tuple through v1.6 and explicit v1.5 constant;
2. v1.5 rejects `ACTION_DELAY`;
3. v1.6 accepts exact frozen `RuntimeActionSessionRegressionActionDelaySetup`;
4. malformed/missing/unknown Delay setup fields are rejected;
5. target/name/team must be non-empty strings;
6. numeric fields must be finite non-booleans; base speed must be positive;
7. action index must be an exact in-range nonnegative integer;
8. zero/negative percent and finite zero/negative initial AV remain representable at the manifest layer;
9. `ACTION_ADVANCE` remains valid in v1.5 and v1.6 and invalid in v1.4;
10. current manifest is v1.6 with exactly seven cases; first six identities/order unchanged; seventh case exact;
11. runtime lane passes `7/7` with record counts `[4, 3, 3, 3, 3, 3, 3]`, exact expected digests, and a well-formed deterministic actual artifact digest for the seventh case;
12. controlled Delay percent mutation surfaces a structured Delay divergence;
13. all seven reviewed fixture byte identities remain exact;
14. harness remains closed and explicit with no generic effect DSL or ChangeSpeed/ImmediateAction/GrantExtraTurn support;
15. legacy `20/20`, trace evidence `2/2`, and LIFO preservation.

Update existing stage-boundary/runtime regression tests only where their accepted count/version expectations necessarily change from 6/v1.5 to 7/v1.6. Preserve historical-version tests.

## 7. Files/areas that must remain unchanged

- `hsr_axis_sim/data/regression_manifest.json`;
- all files under `hsr_axis_sim/data/runtime_golden_fixtures/**`, including ARCH-035 bytes;
- `hsr_axis_sim/sim/**`;
- `hsr_axis_sim/runtime_contracts/**`;
- `hsr_axis_sim/runtime_adapters/**`;
- Golden validator/comparator/divergence implementations;
- trace schema/version;
- production Advance and Delay formulas/events;
- ChangeSpeed, ImmediateAction, and GrantExtraTurn semantics;
- production extra-turn LIFO behavior.

`hsr_axis_sim/runtime_action_session_regression/__init__.py` should remain unchanged unless a concrete existing public-export test demonstrates it must change; setup types are currently imported directly from `.manifest`.

## 8. Explicit exclusions

- any new static fixture generation;
- modifying ARCH-035 expected bytes or digest;
- legacy regression-manifest promotion;
- generic effect/action-axis setup DSL;
- Delay formula/observation changes;
- ChangeSpeed observation or regression support;
- ImmediateAction observation or regression support;
- GrantExtraTurn observation or regression support;
- automatic action selection;
- video parsing/scraping;
- unrelated content or UI work.

## 9. Commands to run

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## 10. Final report format

Report:

- task ID;
- implementation summary;
- files added/modified;
- tests added/updated;
- exact commands executed;
- exact pass/fail results;
- warnings/errors;
- unresolved issues;
- confirmation that exclusions and locked files were respected;
- suggested next milestone.

## 11. Completion report requirement

Update `hsr_axis_sim/LUMEN_RESULT.md` with the final ARCH-036 report. Report real command/CI results only; do not invent results before validation completes.
