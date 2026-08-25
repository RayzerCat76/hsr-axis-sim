# HSR-RUNTIME-ARCH-039 — ChangeSpeed Static Golden Regression Promotion

## 1. Task ID and title

**HSR-RUNTIME-ARCH-039 — ChangeSpeed Static Golden Regression Promotion**

## 2. Current confirmed state

- HSR-RUNTIME-ARCH-038 — PASS — proceed.
- Accepted `main` merge commit before this task: `7496e2c577e43c3061f97f91f83b7d74bb3db4f0`.
- Last confirmed post-merge validation:
  - `1538 passed in 9.52s`;
  - legacy regression `20/20`;
  - trace evidence `2/2`;
  - standalone runtime action-session Golden regression `7/7`.
- Accepted ARCH-038 reviewed static ChangeSpeed fixture:
  - `hsr_axis_sim/data/runtime_golden_fixtures/arch_038_reviewed_change_speed_expected.json`;
  - exactly `2604` bytes;
  - SHA-256 `c23b34e0afffdfe4bee53d028e5ff21d946623300b169ba57e5ddfb69478df2a`.
- Accepted production ChangeSpeed observation semantics from ARCH-037 are locked.
- Current standalone runtime action-session regression manifest version is `1.6` with seven reviewed cases.
- Current blocker: none.

## Execution recommendation

- ChatGPT model: **GPT-5.6 Terra** for routine manifest/runner implementation and tests; **GPT-5.6 Sol** remains the architecture reviewer because version compatibility and deterministic replay boundaries are acceptance-critical.
- Codex reasoning: **High** if Codex is used.

## 3. Objective

Promote the already accepted ARCH-038 static ChangeSpeed Golden expectation into the dedicated standalone runtime action-session regression lane as the eighth locked reviewed case.

Evolve the standalone manifest grammar from v1.6 to v1.7 only as much as needed to declare one explicit `CHANGE_SPEED` setup. Preserve the complete v1.0-v1.6 grammar exactly, preserve all prior case ordering and fixture bytes, and continue delegating actual execution through the existing accepted runtime action-session validation pipeline.

## 4. Required implementation

### Manifest version evolution

In `hsr_axis_sim/runtime_action_session_regression/manifest.py`:

- add `RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_6 = "1.6"`;
- set current `RUNTIME_ACTION_SESSION_REGRESSION_VERSION = "1.7"`;
- supported versions must be exactly `1.0` through `1.7` in order;
- v1.0-v1.6 syntax must retain its previously accepted meaning.

In particular:

- `ACTION_ADVANCE` remains valid in v1.5, v1.6, and v1.7;
- `ACTION_DELAY` remains valid in v1.6 and v1.7, and remains invalid in v1.5 and earlier;
- new `CHANGE_SPEED` is valid only in v1.7;
- v1.6 and earlier must reject `CHANGE_SPEED` rather than silently accepting or degrading it.

### Explicit ChangeSpeed setup contract

Add a frozen dataclass:

```python
@dataclass(frozen=True)
class RuntimeActionSessionRegressionChangeSpeedSetup:
    target_id: str
    target_name: str
    team: str
    base_speed: float
    initial_av: float
    action_index: int
    new_speed: float
```

Keep it a distinct setup type. Do not introduce a generic action-axis/effect DSL or merge Advance/Delay/ChangeSpeed into one polymorphic abstraction.

Add strict parsing for `kind = "CHANGE_SPEED"` with exactly these fields:

- `kind`;
- `target_id`;
- `target_name`;
- `team`;
- `base_speed`;
- `initial_av`;
- `action_index`;
- `new_speed`.

Validation:

- target/name/team are non-empty strings;
- `base_speed`, `initial_av`, and `new_speed` are finite non-boolean numbers;
- `base_speed > 0`;
- `new_speed > 0`, matching the already accepted production ChangeSpeed success boundary;
- `action_index` is an exact in-range nonnegative integer;
- no new lower bound is added to `initial_av`.

### Runner integration

In `hsr_axis_sim/runtime_action_session_regression/runner.py`:

- import production `ChangeSpeed`;
- import the new ChangeSpeed setup type;
- construct one Unit for ChangeSpeed setup using exact target identity/name/team/base speed/initial AV;
- inject exactly `ChangeSpeed(target_ids=[setup.target_id], new_speed=setup.new_speed)` only at the declared `action_index`;
- do not introduce dynamic class lookup, generic effect kwargs, importlib, eval/exec, or a generic effect DSL.

All trace generation and Golden comparison must continue through accepted ARCH-016/runtime regression orchestration.

### Locked eighth manifest case

Update `hsr_axis_sim/data/runtime_action_session_regression_manifest.json` to version `1.7` and append exactly one eighth case after the existing seven:

```json
{
  "id": "arch-038-reviewed-static-change-speed",
  "expected_path": "hsr_axis_sim/data/runtime_golden_fixtures/arch_038_reviewed_change_speed_expected.json",
  "expected_sha256": "c23b34e0afffdfe4bee53d028e5ff21d946623300b169ba57e5ddfb69478df2a",
  "stream_id": "arch-038-reviewed-axis",
  "actor_id": "speed-actor",
  "actions": [
    {
      "action_id": "reviewed-change-speed",
      "name": "reviewed-change-speed",
      "ends_turn": false
    }
  ],
  "setup": {
    "kind": "CHANGE_SPEED",
    "target_id": "speed-actor",
    "target_name": "Speed Actor",
    "team": "ally",
    "base_speed": 100,
    "initial_av": 80,
    "action_index": 0,
    "new_speed": 200
  }
}
```

Do not modify any static Golden fixture bytes.

## 5. Acceptance criteria

- Current standalone runtime manifest version is exactly `1.7`.
- Explicit historical v1.6 constant is retained.
- Supported versions are exactly `("1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7")`.
- v1.0-v1.6 grammar remains compatible with its previously accepted closed setup kinds.
- `ACTION_ADVANCE` remains v1.5+ syntax.
- `ACTION_DELAY` remains v1.6+ syntax.
- `CHANGE_SPEED` parses only in v1.7 and is rejected in v1.6 and earlier.
- ChangeSpeed setup is frozen and strictly validates exact fields/types/bounds.
- Runner creates the declared Unit and a real production `ChangeSpeed` only at the declared action index.
- Standalone manifest contains exactly eight cases, preserving the first seven in exact accepted order and appending ARCH-038 as eighth.
- ARCH-038 fixture remains exactly 2604 bytes with pinned SHA-256 unchanged.
- Standalone runtime action-session Golden regression passes exactly `8/8`.
- Eighth case produces exactly three runtime records and passes accepted Golden record comparison.
- Controlled `new_speed=160` harness mutation produces a Golden mismatch with first divergence at record index `1`, path `/event/payload/legacy_data/after_av`, matching accepted comparator ordering.
- Legacy regression remains `20/20`; trace evidence remains `2/2`.
- Production LIFO compatibility remains unchanged.
- No simulator, runtime observation contract, legacy adapter, trace schema, comparator, divergence, or Golden semantics are changed.

## 6. Required tests

Add focused tests, preferably `hsr_axis_sim/tests/test_runtime_arch_039_change_speed_regression_promotion.py`, covering:

1. supported version tuple through v1.7 and explicit v1.6 constant;
2. v1.6 rejects `CHANGE_SPEED`;
3. v1.7 accepts exact frozen ChangeSpeed setup;
4. malformed/missing/unknown ChangeSpeed setup fields are rejected;
5. target/name/team validation;
6. finite non-boolean numeric validation;
7. positive base/new speed validation;
8. exact in-range action index validation;
9. finite zero/negative initial AV remains representable;
10. `ACTION_DELAY` remains valid in v1.6/v1.7 and invalid in v1.5;
11. current manifest is v1.7 with exactly eight cases, first seven unchanged, eighth exact;
12. runtime lane passes `8/8` with record counts `[4, 3, 3, 3, 3, 3, 3, 3]` and exact expected digests;
13. controlled `new_speed` mutation surfaces the accepted structured divergence;
14. all eight reviewed fixture byte identities remain exact;
15. harness remains closed/explicit with no ImmediateAction/GrantExtraTurn/generic DSL support;
16. legacy `20/20`, trace evidence `2/2`, and LIFO preservation.

Update existing stage-boundary/runtime regression tests only where their accepted current count/version expectations necessarily change from 7/v1.6 to 8/v1.7. Preserve historical-version semantics.

## 7. Files/areas that must remain unchanged

- `hsr_axis_sim/data/regression_manifest.json`;
- all files under `hsr_axis_sim/data/runtime_golden_fixtures/**`, including ARCH-038 bytes;
- `hsr_axis_sim/sim/**`;
- `hsr_axis_sim/runtime_contracts/**`;
- `hsr_axis_sim/runtime_adapters/**`;
- Golden validator/comparator/divergence implementations;
- trace schema/version;
- production Advance/Delay/ChangeSpeed formulas and events;
- ImmediateAction and GrantExtraTurn semantics;
- production extra-turn LIFO behavior.

## 8. Explicit exclusions

- new static fixture generation;
- modifying ARCH-038 expected bytes/digest;
- legacy regression-manifest promotion;
- generic effect/action-axis setup DSL;
- ChangeSpeed formula/observation changes;
- ImmediateAction observation/regression support;
- GrantExtraTurn observation/regression support;
- automatic action selection;
- video parsing/scraping;
- unrelated refactors/UI/content work.

## 9. Commands to run

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## 10. Final report format

Report task ID, implementation summary, files added/modified, tests added/updated, exact commands, exact results, warnings/errors, unresolved issues, exclusion confirmation, and suggested next milestone.

## 11. Completion report requirement

Update `hsr_axis_sim/LUMEN_RESULT.md` with the final ARCH-039 report only after exact real CI results are known.