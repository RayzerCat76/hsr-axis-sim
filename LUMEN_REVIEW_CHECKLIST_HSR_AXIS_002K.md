# LUMEN REVIEW CHECKLIST — HSR-AXIS-002K

## Required files

- [ ] typed reviewed-binding registry/handle
- [ ] registry JSON or equivalent deterministic data source
- [ ] static handler allow-list
- [ ] public list/get/execute API
- [ ] focused tests
- [ ] deterministic Markdown audit
- [ ] deterministic JSON audit
- [ ] updated real-binding README
- [ ] updated `hsr_axis_sim/LUMEN_RESULT.md`

## Registry integrity

- [ ] registry entry IDs unique
- [ ] binding IDs unique
- [ ] binding type supported
- [ ] handler key allow-listed
- [ ] no arbitrary dynamic import from registry JSON
- [ ] binding path exists
- [ ] paths cannot escape project/package root
- [ ] registry metadata matches binding JSON
- [ ] atomic artifact digest matches accepted SHA-256
- [ ] source fact IDs resolve and are approved
- [ ] normalized registry output independent of input ordering

## Partial-binding safety

- [ ] `complete_game_skill: false`
- [ ] `complete_character_kit: false`
- [ ] `synthetic_only: true`
- [ ] `real_trace_executable: false`
- [ ] damage semantics not implemented
- [ ] toughness semantics not implemented
- [ ] immutable validated handle
- [ ] public reviewed execution path validates before execution
- [ ] partial shell cannot register as complete skill or kit

## Pela compatibility

- [ ] exactly one existing Pela binding registered
- [ ] no second binding added
- [ ] registry execution removes `alpha_guard`
- [ ] SP `3 -> 2`
- [ ] Energy `10 -> 40`
- [ ] HP unchanged
- [ ] toughness unchanged
- [ ] normal turn ends
- [ ] insufficient SP behavior unchanged
- [ ] invalid/dead target behavior unchanged
- [ ] existing 002J CLI/report behavior preserved

## Reports and CLI

- [ ] registry version and count included
- [ ] binding safety flags included
- [ ] atomic digest included
- [ ] bound/unresolved facts included
- [ ] partial/synthetic warning included
- [ ] real trace remains non-executable
- [ ] deterministic Markdown and JSON
- [ ] committed reports byte-identical
- [ ] stdout and `--output` work
- [ ] mismatch exits 1
- [ ] unreadable input exits 2 without traceback

## Scope gates

- [ ] no Tingyun Ultimate implementation
- [ ] no other real binding
- [ ] no complete character kit
- [ ] no real trace execution
- [ ] no accepted trace changes
- [ ] no search/evaluator changes
- [ ] no locked manifest changes
- [ ] no generic engine changes without documented reproducible defect

## Regression gates

- [ ] compileall passes
- [ ] full pytest passes
- [ ] locked regression PASS 20/20
- [ ] trace-evidence-only PASS 2/2
- [ ] manifest counts unchanged
- [ ] 002I atomic artifact digest unchanged
