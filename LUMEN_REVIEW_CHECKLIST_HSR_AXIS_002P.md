# Lumen Review Checklist — HSR-AXIS-002P

## Scope and source pinning

- [ ] 002P is non-executable evidence only
- [ ] all required simulator source files are pinned by path and SHA-256
- [ ] 002O evidence/report is pinned and not rewritten
- [ ] stale source digest invalidates a positive conclusion
- [ ] release-game order remains explicitly unknown

## Current-contract audit

- [ ] action start/effect loop/action finish boundaries are documented
- [ ] `GainEnergy` mutation and event behavior are documented
- [ ] `AddBuff` mutation and event behavior are documented
- [ ] trigger visibility before/between/after effects is proven
- [ ] target resolution and turn-context behavior are included
- [ ] exception/invalid-configuration scope is explicitly excluded

## Synthetic equivalence cases

- [ ] Energy below cap
- [ ] Energy near cap
- [ ] Energy at cap
- [ ] no prior probe buff
- [ ] same-ID refresh case
- [ ] unrelated buffs/debuffs
- [ ] non-target units with nontrivial state
- [ ] action-started trigger boundary
- [ ] action-finished trigger boundary
- [ ] interrupt context and non-ending action

## Observable comparison

- [ ] every unit field compared
- [ ] complete buff/debuff metadata compared
- [ ] Energy, HP, toughness, AV, SP compared
- [ ] extra-turn stack compared
- [ ] logs compared
- [ ] pending events and event order/data compared
- [ ] trigger counters and dispatch count compared
- [ ] enemy AI state compared
- [ ] every TurnContext field compared
- [ ] no unexplained comparison exclusion

## Conclusion consistency

- [ ] positive conclusion only if every case passes
- [ ] positive conclusion is limited to pinned current simulator contract
- [ ] generic readiness becomes `blocked_by_duration_semantics` only if proof passes
- [ ] otherwise generic readiness remains `blocked_by_both_semantics`
- [ ] accepted-video readiness remains blocked by unknown target and trace level
- [ ] duration semantics remain unresolved
- [ ] simulator binding remains disallowed

## Validation hardening

- [ ] type checks occur before membership/hash/sort/path/numeric operations
- [ ] malformed object/list/bool/number/null inputs produce controlled `ValueError`
- [ ] no native exception leakage
- [ ] duplicate IDs and stale digests rejected
- [ ] inconsistent positive claims rejected
- [ ] invalid CLI exits 1 without traceback
- [ ] missing/unreadable/invalid JSON exits 2 without traceback
- [ ] reversed unordered valid input is deterministic

## Preservation

- [ ] no executable DMG buff
- [ ] no registry change
- [ ] no Tingyun Energy-binding change
- [ ] no Pela-binding change
- [ ] no target or trace-level inference
- [ ] no duration-policy change
- [ ] no simulator/event/trigger/effect core change
- [ ] no replay/search/evaluator/manifest change
- [ ] no 002Q implementation

## Gates

- [ ] compileall passes
- [ ] complete pytest collection passes
- [ ] focused 002P tests pass
- [ ] locked regression passes 20/20
- [ ] trace-evidence-only regression passes 2/2
- [ ] 002P Markdown is byte-identical to regeneration
- [ ] 002P JSON is byte-identical to regeneration
- [ ] all 002O artifact/report bytes remain unchanged
