# LUMEN Review Checklist — HSR-AXIS-002O-FIX

## Defect correction

- [ ] `semantic_claims[*].status` is type-checked before set membership
- [ ] status object produces controlled `ValueError`
- [ ] status list produces controlled `ValueError`
- [ ] no broad exception wrapper is used as the primary fix
- [ ] exact per-claim status contracts remain enforced

## Adversarial validation

- [ ] every scalar semantic-claim field has malformed JSON-compatible coverage
- [ ] object/list/bool/number/null cases are handled deliberately
- [ ] no `TypeError`, `AttributeError`, or `KeyError` leaks from `build_report`
- [ ] duplicate/conflicting provenance protections still pass
- [ ] reversed unordered input remains deterministic

## CLI behavior

- [ ] readable invalid status object returns exit 1
- [ ] readable invalid status list returns exit 1
- [ ] invalid CLI cases contain no traceback
- [ ] missing/unreadable input remains exit 2

## Semantic preservation

- [ ] generic binding remains `blocked_by_both_semantics`
- [ ] accepted-video binding remains `blocked_by_unknown_target_and_trace_level`
- [ ] accepted-video semantic readiness remains `blocked_by_both_semantics`
- [ ] effect order remains unresolved
- [ ] same-current-turn duration remains unresolved
- [ ] exact levels 1–15 remain validated
- [ ] selected magnitude level remains null
- [ ] protocols remain unrun with no fabricated observation

## Safety preservation

- [ ] no executable DMG buff
- [ ] no target or trace-level inference
- [ ] no Tingyun Energy-binding change
- [ ] no Pela-binding change
- [ ] registry remains exactly two entries
- [ ] no simulator/search/evaluator/replay/manifest change
- [ ] no HSR-AXIS-002P work

## Gates

- [ ] compileall passes
- [ ] complete pytest collection passes
- [ ] focused 002O tests pass
- [ ] locked regression passes 20/20
- [ ] trace-evidence-only regression passes 2/2
- [ ] Markdown report is byte-identical to regeneration
- [ ] JSON report is byte-identical to regeneration
