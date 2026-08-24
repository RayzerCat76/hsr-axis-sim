# LUMEN REVIEW CHECKLIST — HSR-AXIS-001C

Use this when reviewing Codex's 001C output.

## Must pass

- Full pytest suite passes.
- Existing 001A/001B tests still pass.
- `bronya_seele_multistep_mvp.json` exists.
- Multi-step replay has exactly 3 meaningful steps.
- Step 1 selects Seele-like unit first.
- Step 2 selects Bronya-like unit next.
- Step 2 Bronya-like action sets Seele-like unit's `current_av` to 0.
- Step 3 selects Seele-like unit again with zero elapsed AV.
- SP, energy, HP, and AV expectations are checked at each step.
- Numeric tolerance is used, not exact float equality.
- Duplicate unit IDs are rejected clearly.
- Step-level target override is explicitly tested.
- `forced_rng` can appear in replay steps without causing failure.
- CLI runner works:
  `python -m hsr_axis_sim.sim.replay <path>`
- README explains Python and CLI replay validation usage.

## Must not happen

- No Huroka scraping.
- No Bilibili scraping.
- No real HSR character kits.
- No full damage formula.
- No enemy AI.
- No beam search / AI axis search.
- No breaking changes to 001A timeline semantics.

## Special things to inspect

- Does the multistep replay math match the hand-audited expected AV values?
- Does `ImmediateAction` differ correctly from 100% `AdvanceAction`?
- Does Bronya-like action reset Bronya's own normal turn AV after ending the turn?
- Does Seele-like immediate action happen without advancing global AV on step 3?
- Does the validator continue to produce useful mismatch messages?
- Does CLI return nonzero exit code on failed replay?

## Gate decision after 001C

If 001C passes, the next recommended task is likely:

`HSR-AXIS-001D — Buff/Debuff Duration and Turn-Context Semantics MVP`

Do not begin data import until buff duration and turn-context semantics are stable.
