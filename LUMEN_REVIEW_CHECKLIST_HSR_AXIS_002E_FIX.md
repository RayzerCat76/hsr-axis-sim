# LUMEN REVIEW CHECKLIST — HSR-AXIS-002E-FIX

## Scope

- [ ] Only the stale test and result documentation were changed, unless another directly related test defect was proven.
- [ ] No production manifest/runner behavior was changed merely to satisfy the stale assertion.
- [ ] No combat, search, replay, character, damage, AV, buff, or RNG code changed.
- [ ] 002F was not started.

## Test repair

- [ ] The action-sequence-only test checks the action-sequence group rather than the entire future-extensible manifest dictionary.
- [ ] The action-sequence trace count remains 1.
- [ ] The action-sequence entry still requires both `lint` and `action_sequence`.
- [ ] Dedicated 002E tests still lock `trace_evidence == 2`.
- [ ] Semantic-map and frame-anchor entries remain separately validated.

## Required gates

- [ ] `python -m compileall -q hsr_axis_sim` passes.
- [ ] Full `python -m pytest -q` passes with zero failures.
- [ ] Locked manifest regression passes 20/20.
- [ ] `--only trace_evidence` passes 2/2.
- [ ] Manifest counts remain 12 / 1 / 2 / 1 / 2 for the five ordered groups.

## Trust boundary

- [ ] Trace evidence remains non-executable.
- [ ] Media timestamps remain media evidence only.
- [ ] Semantic placeholders remain non-character-kit metadata.
- [ ] No hidden combat numbers were introduced.

## Decision rule

Accept HSR-AXIS-002E only after the complete pytest suite is green. A passing custom harness or manifest runner does not substitute for the required full-suite gate.
