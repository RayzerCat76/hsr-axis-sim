# LUMEN REVIEW CHECKLIST — HSR-AXIS-001P

Use this checklist when reviewing Codex output for 001P.

## Basic acceptance

- [ ] `python -m compileall -q hsr_axis_sim` passes.
- [ ] `python -m pytest hsr_axis_sim/tests -q` passes.
- [ ] All golden replay JSON files pass via `python -m hsr_axis_sim.sim.replay <file>`.
- [ ] `hsr_axis_sim/LUMEN_RESULT.md` is updated with exact test results.

## Scope control

- [ ] No Huroka/Yatta/HoneyHunter scraper was added.
- [ ] No full official character database was imported.
- [ ] No AI search / beam search was added.
- [ ] No UI was added.
- [ ] No large exact-character implementation was attempted.
- [ ] Placeholder numbers are clearly labeled as MVP placeholders.

## Data-driven character kit

- [ ] New kit directory exists: `hsr_axis_sim/data/character_kits/kit_001_mechanic_representatives/`.
- [ ] Character specs load through the existing data loader or minimal schema extension.
- [ ] The kit does not depend on hard-coded unit instance IDs.
- [ ] Skills use semantic target refs and target types correctly.
- [ ] Triggers use the generic trigger system.

## Required representative mechanics

### Kill-chain carry

- [ ] Has basic / skill / ultimate.
- [ ] Can deal HP damage and toughness damage.
- [ ] Uses an on-kill trigger to grant extra turn.
- [ ] Extra turn behavior is generic, not hard-coded.

### Turn-pull support

- [ ] Skill targets a legal ally / other ally.
- [ ] Skill applies immediate action or equivalent action advance.
- [ ] Skill applies a buff to the selected ally.
- [ ] Ultimate applies a team/offensive buff without corrupting turn boundary semantics.

### Energy battery support

- [ ] Ultimate consumes support energy.
- [ ] Ultimate grants ally energy and caps at max energy.
- [ ] Target legality rejects invalid enemy targets.
- [ ] Buff semantics are tested.

### Break support

- [ ] Provides break-related buff(s).
- [ ] If a new toughness damage stat is added, it is isolated and tested.
- [ ] Existing toughness / break damage tests still pass.
- [ ] Break support does not accidentally alter all toughness damage globally.

## Golden replay

- [ ] New `character_kit_001_mvp.json` exists.
- [ ] It is short and deterministic, around 3–5 steps.
- [ ] It checks actor, action, SP, energy, and at least one status or HP/toughness value.
- [ ] It passes through the replay CLI.
- [ ] Existing replays still pass.

## Red flags

- [ ] Codex scraped a website or added network dependency.
- [ ] Codex hard-coded specific unit IDs inside generic skills.
- [ ] Codex bypassed target legality.
- [ ] Codex added character-specific Python if/else branches instead of effects/triggers.
- [ ] Codex broke old replays but only updated expected outputs without explanation.
- [ ] Codex implemented too many characters or too much official detail.
- [ ] Codex changed timeline / ultimate / extra-turn semantics without regression tests.

## Pass condition

001P passes only if the representative character kit is data-driven, tests pass, all golden replays pass, and no scope creep occurred.
