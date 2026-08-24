# LUMEN REVIEW CHECKLIST — HSR-AXIS-002G

## Required files

- [ ] `hsr_axis_sim/tools/trace_binding_gap_inventory.py`
- [ ] declarative binding-assessment JSON
- [ ] focused test file
- [ ] accepted Markdown inventory
- [ ] accepted JSON inventory
- [ ] updated `hsr_axis_sim/LUMEN_RESULT.md`

## Evidence integrity

- [ ] Source evidence report ID/path is validated.
- [ ] One prebattle item and exactly nine steps are present.
- [ ] Actor/action/step keys exactly match the accepted evidence report.
- [ ] Output order follows the evidence report, not assessment-list order.
- [ ] Unknown targets remain unknown.
- [ ] No numeric combat values are added.
- [ ] Naxia composite actions remain unresolved placeholders.
- [ ] Mem action advance remains unresolved; no percentage or immediate-action claim is added.

## Capability classification

- [ ] Generic engine primitives are separated from real-character bindings.
- [ ] Existing generic support does not make a real step executable by itself.
- [ ] Missing character semantics are explicitly listed.
- [ ] Missing initial state/resources are explicitly listed.
- [ ] Video-insufficient evidence is distinguished from engineering gaps.
- [ ] All first-trace items remain non-executable unless fully justified.

## Validation

- [ ] Unsupported statuses fail clearly.
- [ ] Missing step assessment fails.
- [ ] Duplicate step assessment fails.
- [ ] Mismatched actor/action/step fails.
- [ ] Wrong source report ID fails.
- [ ] Invalid `executable_now: true` fails.

## Output and CLI

- [ ] Markdown is readable and prominently non-executable.
- [ ] JSON is clearly structured and deterministic.
- [ ] CLI stdout works for both formats.
- [ ] CLI `--output` writes UTF-8.
- [ ] Validation mismatch returns 1.
- [ ] Input/runtime failure returns 2.
- [ ] Committed sample outputs match generated output byte-for-byte.

## Regression gates

- [ ] `python -m compileall -q hsr_axis_sim`
- [ ] full pytest passes
- [ ] locked manifest remains PASS 20/20
- [ ] trace-evidence-only remains PASS 2/2
- [ ] manifest counts remain unchanged
- [ ] no combat-engine, search, replay, or character-kit code is changed
