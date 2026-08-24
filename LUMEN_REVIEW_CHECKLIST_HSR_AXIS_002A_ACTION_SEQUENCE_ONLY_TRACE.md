# Lumen Review Checklist — HSR-AXIS-002A-SEQ

Use this after Codex completes the action-sequence-only real video trace task.

## Must Pass

- Existing pytest suite passes.
- Existing regression manifest passes.
- The new real video trace fixture passes lint.
- The fixture contains real metadata for the Bilibili source.
- The confirmed 9-step opening sequence is present and in the correct order.
- Unknown numeric fields are explicitly unknown or skipped.
- No SP/energy/HP/toughness/RNG values are invented.
- The locked numeric baseline is not silently changed.

## Verify Trace Content

Confirmed sequence must be:

1. Tingyun ultimate
2. Pela skill
3. Remembrance Trailblazer skill
4. Tingyun skill
5. Pela ultimate
6. Naxia ultimate
7. Naxia basic + extra skill
8. Mem advances Naxia
9. Naxia skill + extra skill

Prebattle:

- Pela technique engage.

Team:

- Naxia / Tingyun / Pela / Remembrance Trailblazer.

## Red Flags

- Codex invents exact SP values.
- Codex invents exact enemy HP/toughness.
- Codex invents forced RNG.
- Codex changes battle core to make this trace run.
- Codex adds this trace to numeric replay validation even though the numbers are unknown.
- Codex treats composite actions as real simulator semantics before we explicitly design them.

## Acceptable MVP

It is acceptable if the new trace is lint-only or action-sequence-check-only.

It is acceptable if target is unknown except Mem → Naxia.

It is acceptable if composite actions are represented as trace-intake labels, not executable simulator actions yet.
