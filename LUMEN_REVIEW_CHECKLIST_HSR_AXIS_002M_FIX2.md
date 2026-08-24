# LUMEN Review Checklist — HSR-AXIS-002M-FIX2

## Core gates

- [ ] compileall passes
- [ ] complete pytest passes
- [ ] locked regression passes 20/20
- [ ] trace-evidence-only regression passes 2/2
- [ ] committed Markdown report is byte-identical to regeneration
- [ ] committed JSON report is byte-identical to regeneration

## Provenance sort safety

- [ ] malformed provenance values are validated before sorting
- [ ] no raw object/list is stored in a dataclass field declared as string
- [ ] duplicate valid source ID + object locator raises ValueError
- [ ] duplicate valid source ID + list locator raises ValueError
- [ ] two invalid source IDs + mixed locator types raise ValueError
- [ ] malformed evidence summary combined with malformed locator raises ValueError
- [ ] no TypeError/AttributeError/KeyError escapes direct build_report validation
- [ ] malformed CLI exits 1
- [ ] malformed CLI stderr contains no Traceback

## Preservation

- [ ] readiness remains blocked_by_both
- [ ] six fact contracts unchanged
- [ ] no executable damage buff
- [ ] Tingyun Energy binding unchanged
- [ ] Pela binding unchanged
- [ ] reviewed registry remains exactly two entries
- [ ] simulator/search/evaluator/replay unchanged
- [ ] locked manifest and counts unchanged
- [ ] duration behavior unchanged
- [ ] magnitude and effect order remain unresolved
- [ ] real-video target and trace level remain unknown
- [ ] no source research
- [ ] no 002N work
