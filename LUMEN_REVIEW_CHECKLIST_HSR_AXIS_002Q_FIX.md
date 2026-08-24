# Lumen Review Checklist — HSR-AXIS-002Q-FIX

## Scope

- [ ] validator and focused tests only
- [ ] no production duration behavior change
- [ ] no executable Tingyun damage buff
- [ ] no registry or manifest change
- [ ] no 002R implementation

## Exact identity and source pins

- [ ] review ID locked to `tingyun_ultimate_turn_entry_duration_gap_v0_1`
- [ ] version locked to `0.1`
- [ ] supplied-reference path/digest/locators all exact
- [ ] project-source path/digest/locators all exact
- [ ] changed, missing, extra, or duplicate locators rejected

## Claim semantic contracts

- [ ] all eight claim IDs exact
- [ ] exact claim values and types
- [ ] exact verification statuses
- [ ] exact source-ID sets
- [ ] exact unresolved-field sets
- [ ] exact nullable semantic outputs
- [ ] unresolved outputs cannot be filled with invented strings
- [ ] simulator binding remains false

## Confirmed blocker reproductions

- [ ] zero-counter `effect_active_during_entered_turn = "true"` rejected
- [ ] extra-action `extra_action_consumes = "true"` rejected
- [ ] extra-turn `extra_turn_consumes = "true"` rejected
- [ ] event order assertion rejected
- [ ] active-turn refresh assertion rejected
- [ ] locator replacement rejected
- [ ] source-ID removal/addition rejected
- [ ] unresolved-field replacement rejected
- [ ] changed review ID/version rejected

## Boundary and gap contracts

- [ ] exact seven boundary-case contracts
- [ ] exact per-case unresolved fields
- [ ] exact seven gap IDs/statuses
- [ ] gap semantic summaries cannot be arbitrarily replaced

## Error handling and determinism

- [ ] all invalid JSON-compatible mutations produce controlled `ValueError`
- [ ] no TypeError/AttributeError/KeyError leakage
- [ ] readable invalid CLI exits 1 without traceback
- [ ] missing/unreadable/invalid JSON exits 2 without traceback
- [ ] reversed unordered collections remain byte-identical

## Preservation

- [ ] normalized input meaning unchanged
- [ ] Markdown report byte-identical
- [ ] JSON report byte-identical
- [ ] 002O/002P digests unchanged
- [ ] reviewed registry unchanged
- [ ] locked manifest unchanged
- [ ] only expected tool/test/LUMEN_RESULT changes

## Gates

- [ ] compileall PASS
- [ ] complete pytest collection PASS
- [ ] focused replacement-002Q tests PASS
- [ ] locked regression PASS 20/20
- [ ] trace-evidence-only regression PASS 2/2
- [ ] report digests remain JSON `af9aed...` and Markdown `6568ff...`
