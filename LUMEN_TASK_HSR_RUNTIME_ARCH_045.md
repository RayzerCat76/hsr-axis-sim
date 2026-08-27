# HSR-RUNTIME-ARCH-045 — GrantExtraTurn Static Golden Regression Promotion

## Current confirmed state

- Accepted `main`: `edd8664b6d49ea0d09417ac33c88b569eb16a433`.
- HSR-RUNTIME-ARCH-044 is accepted and merged.
- Canonical post-merge CI run #267: `1721 passed in 7.72s`, legacy regression `20/20`, trace evidence `2/2`, runtime action-session Golden regression `9/9`.
- ARCH-044 reviewed static fixture is locked at:
  - `hsr_axis_sim/data/runtime_golden_fixtures/arch_044_reviewed_grant_extra_turn_expected.json`
  - 2658 bytes
  - SHA-256 `57eefb521cb5cf1840e49c36e5c9c85a08281a7014c23ece0e3d5df1e6dfefdd`
- Existing production `GrantExtraTurn` observation and accepted simulator LIFO behavior are already covered by ARCH-043/044 and are out of scope for change here.

Recommended execution routing:
- ChatGPT: **GPT-5.6 Terra**
- Codex reasoning: **High**

## Objective

Promote the accepted ARCH-044 reviewed static `GrantExtraTurn` Golden into the standalone runtime action-session regression lane as the tenth deterministic case, using the smallest closed grammar extension required to reconstruct the accepted runtime input.

## Required implementation

1. Extend `hsr_axis_sim/runtime_action_session_regression/manifest.py` from current grammar v1.8 to v1.9.
2. Preserve explicit support for historical versions v1.0 through v1.8.
3. Add one frozen setup contract dedicated to `GRANT_EXTRA_TURN` with only fields required to reconstruct the deterministic target and action effect:
   - `target_id`
   - `target_name`
   - `team`
   - `base_speed`
   - `action_index`
4. `GRANT_EXTRA_TURN` must be valid only in v1.9. v1.8 must explicitly reject it.
5. `IMMEDIATE_ACTION` remains valid in both v1.8 and v1.9. All earlier setup kinds retain their existing historical version boundaries and remain valid in later supported versions.
6. Extend `hsr_axis_sim/runtime_action_session_regression/runner.py` only enough to:
   - build the target `Unit` for the new setup;
   - inject `GrantExtraTurn(target_ids=[setup.target_id])` at the declared action index.
7. Update `hsr_axis_sim/data/runtime_action_session_regression_manifest.json` to version `1.9` and append, without reordering earlier cases, exactly one tenth case:
   - id `arch-044-reviewed-static-grant-extra-turn`
   - expected fixture `arch_044_reviewed_grant_extra_turn_expected.json`
   - expected SHA-256 `57eefb521cb5cf1840e49c36e5c9c85a08281a7014c23ece0e3d5df1e6dfefdd`
   - stream id `arch-044-reviewed-axis`
   - actor id `extra-turn-actor`
   - one action id/name `reviewed-grant-extra-turn`, `ends_turn=false`
   - setup kind `GRANT_EXTRA_TURN`, target `extra-turn-target`, target name `Extra Turn Target`, team `ally`, base speed `100`, action index `0`.
8. Add focused ARCH-045 tests. Update only historical source/version guards that are made stale specifically by the authorized v1.9 grammar extension.
9. Update `hsr_axis_sim/LUMEN_RESULT.md` only after real CI evidence is available.

## Acceptance criteria

- Runtime action-session manifest loads as v1.9 and contains exactly 10 cases in the prior nine-case order plus ARCH-044 as case 10.
- `GRANT_EXTRA_TURN` setup is frozen and strictly validates exact fields, non-empty identity strings, positive finite non-boolean `base_speed`, and exact nonnegative in-range `action_index`.
- v1.8 rejects `GRANT_EXTRA_TURN`; v1.9 accepts it.
- v1.8 and v1.9 both accept `IMMEDIATE_ACTION`; historical setup version boundaries are preserved.
- Runner reconstruction uses the existing production `GrantExtraTurn`; no duplicate/fake event generation is added to the harness.
- Tenth case passes against the locked ARCH-044 static expected bytes.
- Runtime regression becomes exactly `10/10`.
- First nine runtime regression cases retain these exact accepted actual SHA-256 digests from canonical run #267, in order:
  1. `452d52be7dec07ddebe0ca5ec0ca3cf58d695bd2312ada684d70aa22891435d0`
  2. `80dda34881d32267ff819e985d7ed95256185e0c539f6e1b313aa67afcab9d3a`
  3. `0004d8947f3b7ce8e692af527f40579db94609e4ed3ae0b63bf40397ec4af043`
  4. `230e21dc23da2c37d89f26903dbd636463f5b0ec9adc7298e99331f3e24efb5f`
  5. `7a945e7016ffa4a6c074f563d7f0edf288239e92f596810cd434922e8fd5c525`
  6. `13d26b8efcb0db450445c036f49b31eec4ca346ca9d714f7e221bc084941a6ca`
  7. `c47754957a756bd03624aafdcd78e14ecbaed059cce0c99fddb0d116c88bde77`
  8. `a75555d3544a27638781a274a01ff8ee031e6394369be5c3c93c32dfed4c6698`
  9. `b41181b9bb09ec516d27f78a99ef455a69c2b5e678d93f8eaa5f94effdde8cb7`
- All ten reviewed expected fixture byte sizes and SHA-256 identities remain exact.
- Legacy regression remains `20/20`; trace evidence remains `2/2`.
- Full pytest passes.

## Required tests

Add `hsr_axis_sim/tests/test_runtime_arch_045_grant_extra_turn_regression_promotion.py` covering at minimum:

- supported versions are exactly v1.0 through v1.9;
- v1.8 rejects `GRANT_EXTRA_TURN`;
- v1.9 accepts exact frozen `GRANT_EXTRA_TURN` setup;
- exact-field rejection;
- invalid identity fields;
- invalid/nonpositive/nonfinite/bool `base_speed`;
- invalid/out-of-range `action_index`;
- v1.8 and v1.9 both accept `IMMEDIATE_ACTION`;
- locked manifest exact 10-case order and exact tenth setup;
- runtime lane `10/10` and expected record counts `[4,3,3,3,3,3,3,3,3,3]`;
- first nine accepted actual digests pinned exactly to run #267 values above;
- tenth expected fixture identity `2658` bytes and locked SHA-256;
- all prior nine expected fixture identities unchanged;
- harness uses `GrantExtraTurn` explicitly and contains no reflection/dynamic effect loading;
- ARCH-044 fixture remains absent from legacy regression manifest;
- legacy `20/20` and trace evidence `2/2`;
- production LIFO compatibility remains unchanged.

## Files/areas that must remain unchanged

Do not modify:

- `hsr_axis_sim/sim/**`
- `hsr_axis_sim/runtime_contracts/**`
- `hsr_axis_sim/runtime_adapters/**`
- `hsr_axis_sim/runtime_action_sessions/**`
- runtime capture/export/loader/comparator/divergence code
- `hsr_axis_sim/data/regression_manifest.json`
- any reviewed Golden fixture bytes, including ARCH-044
- existing production extra-turn scheduling/LIFO semantics

Historical tests may be changed only where an assertion is stale solely because v1.9 is now an authorized later grammar version.

## Explicit exclusions

- No change to real HSR semantic claims.
- No new priority/interrupt semantics.
- No Timeline or action-value behavior changes.
- No change to extra-turn stack ordering.
- No new video parsing or trace extraction.
- No damage/character database/UI work.
- No unrelated refactor.

## Commands to run

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
python -m hsr_axis_sim.runtime_action_session_regression.runner --manifest hsr_axis_sim/data/runtime_action_session_regression_manifest.json --format text
```

## Final report format

Report:

- task ID;
- implementation summary;
- files added/modified;
- tests added/updated;
- exact commands executed;
- exact pass/fail results;
- all 10 runtime case results and actual digests;
- unresolved issues;
- confirmation that exclusions and locked areas were respected;
- suggested smallest next milestone;
- updated `hsr_axis_sim/LUMEN_RESULT.md`.

Do not report PASS from plausible code alone. Require real GitHub Actions evidence before final acceptance.
