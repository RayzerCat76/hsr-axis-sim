# LUMEN REVIEW CHECKLIST — HSR-AXIS-002I

## Required files

- [ ] atomic-fact normalization tool
- [ ] normalized atomic-facts JSON
- [ ] deterministic Markdown readiness report
- [ ] deterministic JSON readiness report
- [ ] focused tests
- [ ] README
- [ ] updated `hsr_axis_sim/LUMEN_RESULT.md`

## Atomic provenance integrity

- [ ] compound 002H objects are split into atomic facts
- [ ] every atomic field has exact provenance
- [ ] corroborated is not inherited from a compound parent
- [ ] single-source atomic fields are downgraded appropriately
- [ ] source-registry fact IDs resolve
- [ ] source IDs resolve
- [ ] missing facts have null values
- [ ] conflicts remain explicit
- [ ] version applicability is retained
- [ ] all facts keep `simulator_binding_allowed: false`

## Mem semantics

- [ ] 100% Charge threshold is distinct from Charge cost
- [ ] Charge cost is directly sourced or remains partial/missing
- [ ] Mem's own immediate action is distinct from ally action advance
- [ ] ally action advance amount is separately recorded
- [ ] support duration and target scope are separate fields
- [ ] no immediate-action/action-advance conflation

## Toughness normalization

- [ ] source-native values are retained
- [ ] source-native convention/unit is recorded
- [ ] no undocumented 10↔30 or other conversion
- [ ] normalized value is null when conversion is not documented

## Readiness matrix

- [ ] prebattle plus all nine steps covered
- [ ] source blockers are visible
- [ ] trace-observation blockers are visible
- [ ] engine-review blockers are visible
- [ ] no action marked executable
- [ ] readiness vocabulary validated

## Validation and CLI

- [ ] duplicate atomic fact IDs fail
- [ ] unsupported vocabularies fail
- [ ] dangling registry/source references fail
- [ ] invalid field-level corroboration fails
- [ ] missing non-null facts fail
- [ ] simulator-binding permission fails
- [ ] executable schemas fail
- [ ] output deterministic under input reordering
- [ ] committed outputs byte-identical
- [ ] CLI stdout and `--output` work
- [ ] validated mismatch exits 1
- [ ] unreadable input exits 2
- [ ] no expected-failure traceback

## Scope gates

- [ ] no real character kit implemented
- [ ] no CharacterSpec/SkillSpec/Effect/Trigger generated
- [ ] no trace actor IDs renamed
- [ ] no real trace made executable
- [ ] no combat/replay/search/evaluator changes
- [ ] locked manifest unchanged
- [ ] no 002J binding begun

## Regression gates

- [ ] `python -m compileall -q hsr_axis_sim`
- [ ] full pytest passes
- [ ] locked manifest remains PASS 20/20
- [ ] trace-evidence-only remains PASS 2/2
- [ ] manifest counts unchanged
