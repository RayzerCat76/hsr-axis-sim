# HSR-RUNTIME-ARCH-042 — ImmediateAction Static Golden Regression Promotion

## 1. Task ID and title

**HSR-RUNTIME-ARCH-042 — ImmediateAction Static Golden Regression Promotion**

## 2. Current confirmed state

- `HSR-RUNTIME-ARCH-041 — PASS — proceed` is accepted on `main`.
- Accepted `main` merge commit before this task: `e8492f8dd35a11b0f47fd1315e871cc5500b335c`.
- Last confirmed post-merge validation:
  - pytest: **1635 passed in 10.25s**;
  - legacy regression: **20/20**;
  - trace evidence: **2/2**;
  - standalone runtime action-session Golden regression: **8/8**.
- Accepted ARCH-041 reviewed static ImmediateAction fixture:
  - `hsr_axis_sim/data/runtime_golden_fixtures/arch_041_reviewed_immediate_action_expected.json`;
  - exactly **2620 bytes**;
  - SHA-256 **`7fd1594362b5bf9a95eec6f6472b2f17afa9dcfe10196d81ec6c970eab86eea1`**.
- Accepted production ImmediateAction observation semantics from ARCH-040 are locked.
- Current standalone runtime action-session regression manifest version is `1.7` with eight reviewed cases.
- Current blocker: none.

## Execution recommendation

- ChatGPT model: **GPT-5.6 Terra**.
- Codex reasoning: **High** if Codex is used.

## 3. Objective

Promote the already accepted ARCH-041 static ImmediateAction Golden expectation into the dedicated standalone runtime action-session regression lane as the ninth locked reviewed case.

Evolve the standalone manifest grammar from v1.7 to v1.8 only as much as needed to declare one explicit `IMMEDIATE_ACTION` setup. Preserve the complete v1.0-v1.7 grammar exactly, preserve all prior case ordering and fixture bytes, and continue delegating actual execution through the existing accepted runtime action-session validation pipeline.

## 4. Required implementation

### Manifest version evolution

In `hsr_axis_sim/runtime_action_session_regression/manifest.py`:

- add `RUNTIME_ACTION_SESSION_REGRESSION_VERSION_1_7 = "1.7"`;
- set current `RUNTIME_ACTION_SESSION_REGRESSION_VERSION = "1.8"`;
- supported versions must be exactly `1.0` through `1.8` in order;
- v1.0-v1.7 syntax must retain its previously accepted meaning.

In particular:

- `ACTION_ADVANCE` remains valid from v1.5 onward;
- `ACTION_DELAY` remains valid from v1.6 onward;
- `CHANGE_SPEED` remains valid in v1.7 and v1.8, and remains invalid in v1.6 and earlier;
- new `IMMEDIATE_ACTION` is valid only in v1.8;
- v1.7 and earlier must reject `IMMEDIATE_ACTION` rather than silently accepting or degrading it.

Do not reinterpret the old meaning of the generic `RUNTIME_ACTION_SESSION_REGRESSION_VERSION` constant inside historical branches. Replace any such implicit v1.7 references with the explicit new `VERSION_1_7` constant where necessary so v1.7 grammar remains frozen.

### Explicit ImmediateAction setup contract

Add a frozen dataclass:

```python
@dataclass(frozen=True)
class RuntimeActionSessionRegressionImmediateActionSetup:
    target_id: str
    target_name: str
    team: str
    base_speed: float
    initial_av: float
    action_index: int
```

Keep it a distinct setup type. Do not introduce a generic action-axis/effect DSL or merge Advance/Delay/ChangeSpeed/ImmediateAction into one polymorphic abstraction.

Add strict parsing for `kind = "IMMEDIATE_ACTION"` with exactly these fields:

- `kind`;
- `target_id`;
- `target_name`;
- `team`;
- `base_speed`;
- `initial_av`;
- `action_index`.

Validation:

- target/name/team are non-empty strings;
- `base_speed` and `initial_av` are finite non-boolean numbers;
- `base_speed > 0`;
- `action_index` is an exact in-range nonnegative integer;
- no lower bound is added to `initial_av`;
- do not add percent/delta/clamp/priority/turn-kind fields.

### Runner integration

In `hsr_axis_sim/runtime_action_session_regression/runner.py`:

- import production `ImmediateAction`;
- import the new ImmediateAction setup type;
- construct one Unit using exact target identity/name/team/base speed/initial AV;
- inject exactly `ImmediateAction(target_ids=[setup.target_id])` only at the declared `action_index`;
- do not introduce dynamic class lookup, generic effect kwargs, importlib, eval/exec, or a generic effect DSL.

All trace generation and Golden comparison must continue through accepted ARCH-016/runtime regression orchestration.

### Locked ninth manifest case

Update `hsr_axis_sim/data/runtime_action_session_regression_manifest.json` to version `1.8` and append exactly one ninth case after the existing eight:

```json
{
  "id": "arch-041-reviewed-static-immediate-action",
  "expected_path": "hsr_axis_sim/data/runtime_golden_fixtures/arch_041_reviewed_immediate_action_expected.json",
  "expected_sha256": "7fd1594362b5bf9a95eec6f6472b2f17afa9dcfe10196d81ec6c970eab86eea1",
  "stream_id": "arch-041-reviewed-axis",
  "actor_id": "immediate-actor",
  "actions": [
    {
      "action_id": "reviewed-immediate-action",
      "name": "reviewed-immediate-action",
      "ends_turn": false
    }
  ],
  "setup": {
    "kind": "IMMEDIATE_ACTION",
    "target_id": "immediate-actor",
    "target_name": "Immediate Actor",
    "team": "ally",
    "base_speed": 100,
    "initial_av": 80,
    "action_index": 0
  }
}
```

Do not modify any static Golden fixture bytes.

## 5. Acceptance criteria

- Current standalone runtime manifest version is exactly `1.8`.
- Explicit historical v1.7 constant is retained.
- Supported versions are exactly `("1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8")`.
- v1.0-v1.7 grammar remains compatible with its previously accepted closed setup kinds.
- `ACTION_ADVANCE` remains v1.5+ syntax.
- `ACTION_DELAY` remains v1.6+ syntax.
- `CHANGE_SPEED` remains v1.7+ syntax and is rejected in v1.6 and earlier.
- `IMMEDIATE_ACTION` parses only in v1.8 and is rejected in v1.7 and earlier.
- ImmediateAction setup is frozen and strictly validates exact fields/types/bounds.
- Runner creates the declared Unit and a real production `ImmediateAction` only at the declared action index.
- Standalone manifest contains exactly nine cases, preserving the first eight in exact accepted order and appending ARCH-041 as ninth.
- ARCH-041 fixture remains exactly 2620 bytes with pinned SHA-256 unchanged.
- Standalone runtime action-session Golden regression passes exactly `9/9`.
- Ninth case produces exactly three runtime records and passes accepted Golden record comparison.
- Controlled harness mutation of only `initial_av` from `80` to `60` produces a Golden mismatch with first divergence at record index `1`, path `/event/payload/immediate_action/before_av`, expected `80`, actual `60`.
- Legacy regression remains `20/20`; trace evidence remains `2/2`.
- Production LIFO compatibility remains unchanged.
- No simulator, runtime observation contract, legacy adapter, trace schema, comparator, divergence, or Golden semantics are changed.

## 6. Required tests

Add focused tests, preferably `hsr_axis_sim/tests/test_runtime_arch_042_immediate_action_regression_promotion.py`, covering:

1. supported version tuple through v1.8 and explicit v1.7 constant;
2. v1.7 rejects `IMMEDIATE_ACTION`;
3. v1.8 accepts exact frozen ImmediateAction setup;
4. malformed/missing/unknown ImmediateAction setup fields are rejected;
5. target/name/team validation;
6. finite non-boolean numeric validation;
7. positive base-speed validation;
8. exact in-range action-index validation;
9. finite zero/negative initial AV remains representable;
10. `CHANGE_SPEED` remains valid in v1.7/v1.8 and invalid in v1.6;
11. current manifest is v1.8 with exactly nine cases, first eight unchanged, ninth exact;
12. runtime lane passes `9/9` with record counts `[4, 3, 3, 3, 3, 3, 3, 3, 3]` and exact expected digests;
13. controlled `initial_av=60` harness mutation surfaces the accepted first divergence;
14. all nine reviewed fixture byte identities remain exact;
15. harness remains closed/explicit with no `GrantExtraTurn` or generic DSL support;
16. legacy `20/20`, trace evidence `2/2`, and LIFO preservation.

Update existing stage-boundary/runtime regression tests only where their accepted current count/version expectations necessarily change from 8/v1.7 to 9/v1.8. Preserve historical-version semantics.

## 7. Files/areas that must remain unchanged

- `hsr_axis_sim/data/regression_manifest.json`;
- all files under `hsr_axis_sim/data/runtime_golden_fixtures/**`, including ARCH-041 bytes;
- `hsr_axis_sim/sim/**`;
- `hsr_axis_sim/runtime_contracts/**`;
- `hsr_axis_sim/runtime_adapters/**`;
- Golden validator/comparator/divergence implementations;
- trace schema/version;
- production Advance/Delay/ChangeSpeed/ImmediateAction semantics and events;
- GrantExtraTurn semantics;
- production extra-turn LIFO behavior.

## 8. Explicit exclusions

- new static fixture generation;
- modifying ARCH-041 expected bytes/digest;
- legacy regression-manifest promotion;
- generic effect/action-axis setup DSL;
- ImmediateAction formula/observation changes;
- GrantExtraTurn observation/regression support;
- automatic action selection;
- priority/action-family/interrupt/extra-turn inference;
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

Update `hsr_axis_sim/LUMEN_RESULT.md` with the final ARCH-042 report only after exact real CI results are known.
