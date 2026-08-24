# Lumen Review Checklist — HSR-AXIS-002Q Replacement

## Supersession and scope

- [ ] old end-turn dual-policy 002Q is explicitly obsolete
- [ ] replacement task is evidence/tool/test only
- [ ] no production duration behavior changes
- [ ] no executable Tingyun DMG buff or registry entry
- [ ] no 002R implementation

## Evidence integrity

- [ ] two-turn duration remains source-cross-checked
- [ ] turn-entry boundary is recorded as an accepted project-domain correction
- [ ] it is not mislabeled as independently frame verified
- [ ] Bilibili BV/title/URL are preserved as candidate evidence only
- [ ] no timestamp, uploader, or frame observation is fabricated
- [ ] community simulator is implementation corroboration only

## Current engine gap

- [ ] all required engine files are path/digest/locator pinned
- [ ] normal and extra `turn_started` paths are captured
- [ ] current end-turn target-normal-turn tick is captured
- [ ] no entry tick exists in the pinned engine
- [ ] Buff has no application-boundary marker
- [ ] refresh directly resets remaining turns
- [ ] `GAP_TARGET_NORMAL_TURN_TICK_BOUNDARY` is proven

## Unresolved semantics

- [ ] 1→0 effect lifetime remains unresolved
- [ ] extra-turn duration consumption remains unresolved
- [ ] extra-action duration consumption remains unresolved
- [ ] ordering relative to `turn_started` remains unresolved
- [ ] same-ID active-turn refresh remains unresolved
- [ ] global migration impact remains unresolved

## Synthetic matrix

- [ ] pre-next-normal-turn application
- [ ] interrupt application in active target turn
- [ ] same-ID refresh in active target turn
- [ ] non-ending extra action
- [ ] granted extra turn
- [ ] action advance into next normal turn
- [ ] evidence-model 2→1 and 1→0 boundaries
- [ ] nontrivial unrelated state
- [ ] no unresolved release output is invented

## Validation hardening

- [ ] exact schemas, IDs, statuses, gaps, paths, and digests validated
- [ ] type checks precede membership/hash/sort/path/numeric operations
- [ ] stale digests and inconsistent conclusions rejected
- [ ] every scalar object/list/bool/number/null mutation is controlled
- [ ] no native exception leakage
- [ ] readable invalid CLI exits 1 without traceback
- [ ] missing/unreadable/invalid JSON exits 2 without traceback
- [ ] reversed unordered input produces byte-identical output

## Preservation

- [ ] accepted 002O/002P bytes preserved
- [ ] existing Tingyun/Pela bindings preserved
- [ ] registry and locked manifest unchanged
- [ ] replay/search/evaluator behavior unchanged

## Conclusion

- [ ] exact conclusion is `turn_entry_claim_normalized_current_engine_gap_confirmed_runtime_change_blocked`
- [ ] generic readiness remains `blocked_by_duration_semantics`
- [ ] accepted-video readiness remains `blocked_by_unknown_target_and_trace_level`
- [ ] simulator binding remains false

## Gates

- [ ] compileall passes
- [ ] complete pytest collection passes
- [ ] focused replacement-002Q tests pass
- [ ] locked regression passes 20/20
- [ ] trace-evidence-only regression passes 2/2
- [ ] generated Markdown/JSON are byte-identical to regeneration
