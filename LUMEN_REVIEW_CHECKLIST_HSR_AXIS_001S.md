# LUMEN REVIEW CHECKLIST — HSR-AXIS-001S

Use this checklist after Codex returns HSR-AXIS-001S.

## Basic acceptance

- [ ] `python -m pytest -q` passes.
- [ ] All existing golden replay CLIs pass.
- [ ] Manual video trace lint passes.
- [ ] Manual video trace replay passes.
- [ ] Existing simulator behavior is not broken.

## New files / structure

- [ ] `hsr_axis_sim/search/__init__.py` exists.
- [ ] `hsr_axis_sim/search/node.py` or equivalent exists.
- [ ] `hsr_axis_sim/search/evaluator.py` or equivalent exists.
- [ ] `hsr_axis_sim/search/search_engine.py` or equivalent exists.
- [ ] `hsr_axis_sim/search/beam_search.py` or equivalent exists.
- [ ] Search tests exist.

## State isolation

- [ ] Child branches do not mutate parent states.
- [ ] Sibling branches do not share mutable battle state.
- [ ] Extra turn stack, logs, units, buffs, debuffs, triggers, and RNG state are safely copied or isolated.

## Action expansion

- [ ] Search uses legal action generation rather than hardcoded test-only actions.
- [ ] Invalid targets are not generated.
- [ ] Resource-gated actions are respected.
- [ ] Dead targets are not selected.
- [ ] Enemy AI actions can be applied when next actor is enemy.
- [ ] Ultimate actions, if included, do not incorrectly advance/reset normal AV.

## Terminal conditions

- [ ] all enemies defeated terminal condition works.
- [ ] all allies defeated terminal condition works.
- [ ] max_depth terminal condition works.
- [ ] Optional max_global_av / max_nodes_expanded logic is explicit if implemented.
- [ ] Terminal reason strings are clear.

## Evaluator

- [ ] Evaluator is deterministic.
- [ ] Weights are configurable.
- [ ] The evaluator is clearly labeled MVP and not official scoring.
- [ ] Tests prove the evaluator prefers an obviously better branch.

## Beam search

- [ ] `beam_width` is respected.
- [ ] `max_depth` is respected.
- [ ] `nodes_expanded` is tracked.
- [ ] Tie-breaking is deterministic.
- [ ] SearchResult exposes best node, final beam, depth reached, and status.

## Axis output

- [ ] Best node has readable action records.
- [ ] `format_axis(...)` or equivalent exists.
- [ ] Output includes actor, skill/action, targets, AV, SP, and score or enough debug info.

## Scope discipline

- [ ] No live website scraping.
- [ ] No Bilibili downloading/OCR.
- [ ] No neural network/RL.
- [ ] No UI.
- [ ] No broad real-character import.
- [ ] No unnecessary rewrite of simulator core.

## Gate decision

- [ ] PASS: Continue to 001T Evaluator / Mode-Specific Scoring MVP.
- [ ] FIX: Return a 001S-FIX prompt before 001T.
