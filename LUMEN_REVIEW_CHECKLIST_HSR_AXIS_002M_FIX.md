# LUMEN Review Checklist — HSR-AXIS-002M-FIX

## Core gates

- [ ] compileall passes
- [ ] complete pytest passes
- [ ] locked regression passes 20/20
- [ ] trace-evidence-only regression passes 2/2
- [ ] committed Markdown report is byte-identical to regeneration
- [ ] committed JSON report is byte-identical to regeneration

## Controlled validation

- [ ] enum-like object/list values raise ValueError
- [ ] malformed provenance source IDs raise ValueError
- [ ] malformed provenance release/corroboration statuses raise ValueError
- [ ] malformed declared readiness raises ValueError
- [ ] no TypeError/AttributeError/KeyError escapes direct validation
- [ ] CLI schema failures use controlled validation exit
- [ ] CLI malformed-input stderr contains no Traceback

## Fact-specific schema

- [ ] target scope is exactly selected_single_ally
- [ ] duration is exactly integer 2 and boolean is rejected
- [ ] magnitude v0.1 remains null/missing
- [ ] application order v0.1 remains null/unresolved
- [ ] release scope is a valid accepted string
- [ ] real-video trace level remains null/missing
- [ ] value_type and unit are exact for all six facts
- [ ] duplicate provenance sources are rejected
- [ ] malformed source-catalog report fields are rejected

## Readiness semantics

- [ ] same-current-turn rule remains explicitly unverified
- [ ] engine representability is not confused with verified game equivalence
- [ ] duration uncertainty counts as a duration-semantics gap
- [ ] current status computes to blocked_by_both
- [ ] declared status matches computed status
- [ ] blockers and report wording are internally consistent

## Preservation

- [ ] no executable damage buff
- [ ] no new magnitude or effect-order fact
- [ ] Tingyun Energy binding unchanged
- [ ] Pela binding unchanged
- [ ] registry v0.2 unchanged with exactly two entries
- [ ] simulator/search/evaluator/replay unchanged
- [ ] locked manifest and counts unchanged
- [ ] duration engine behavior unchanged
- [ ] no real-video target or trace-level inference
- [ ] no 002N work
