# LUMEN REVIEW CHECKLIST — HSR-AXIS-002J

## Required files

- [ ] separate partial real-binding module/data
- [ ] synthetic deterministic fixture
- [ ] focused tests
- [ ] deterministic Markdown audit report
- [ ] deterministic JSON audit report
- [ ] namespace README
- [ ] updated `hsr_axis_sim/LUMEN_RESULT.md`

## Atomic fact discipline

- [ ] only Pela Skill accepted atomic facts used
- [ ] target scope is single enemy
- [ ] SP cost is exactly 1
- [ ] actor energy gain is exactly 30
- [ ] dispel count is exactly 1
- [ ] atomic fact IDs resolve
- [ ] no missing/null fact is bound
- [ ] 002I artifact unchanged

## Partial binding honesty

- [ ] `complete_game_skill: false`
- [ ] partial scope clearly named
- [ ] no damage implementation
- [ ] no toughness implementation
- [ ] no trace/eidolon/build assumptions
- [ ] real-video target remains unknown
- [ ] no claim that complete Pela Skill is implemented

## Execution semantics

- [ ] legal target validation works
- [ ] insufficient SP rejected
- [ ] SP decreases by 1
- [ ] energy increases by 30
- [ ] exactly one removable status dispelled
- [ ] dispel ordering deterministic
- [ ] HP unchanged
- [ ] toughness unchanged
- [ ] normal turn/timeline behavior preserved

## Validation and CLI

- [ ] full-completion claim rejected
- [ ] damage effect rejected
- [ ] toughness effect rejected
- [ ] wrong scope/cost/energy/dispel values rejected
- [ ] dangling/unapproved atomic facts rejected
- [ ] deterministic under input reordering
- [ ] committed reports byte-identical
- [ ] stdout and `--output` work
- [ ] mismatch exits 1
- [ ] unreadable input exits 2 without traceback

## Scope gates

- [ ] no other Pela action implemented
- [ ] no other real character implemented
- [ ] no real trace made executable
- [ ] no target inferred from video
- [ ] no search/evaluator changes
- [ ] locked manifest unchanged
- [ ] no 002K work begun

## Regression gates

- [ ] compileall passes
- [ ] full pytest passes
- [ ] locked regression PASS 20/20
- [ ] trace-evidence-only PASS 2/2
- [ ] manifest counts unchanged
