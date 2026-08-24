# LUMEN Review Checklist — HSR-AXIS-002N

## Source quality

- [ ] exact level-scaling table is captured from release/live structured data, or task blocks honestly
- [ ] exact field locator is recorded
- [ ] source version/snapshot qualification is recorded
- [ ] independent corroboration is recorded where available
- [ ] no values are inferred from memory, interpolation, a single level, or the video
- [ ] current page is not falsely claimed to be byte-identical to version 3.4

## Data normalization

- [ ] raw source level indexes are preserved
- [ ] normalized trace-level mapping is explicit and source-supported
- [ ] values and percent unit are strictly typed
- [ ] booleans are rejected as numbers
- [ ] NaN/infinity are rejected if floats are supported
- [ ] duplicate levels and source IDs are rejected
- [ ] provenance is atomic and exact
- [ ] deterministic ordering and rendering

## Safety

- [ ] malformed direct validation raises controlled ValueError
- [ ] malformed CLI exits 1 without traceback
- [ ] unreadable/missing source input exits 2 without traceback
- [ ] no unsafe set/sort/comparison before validation
- [ ] no executable schema keys
- [ ] simulator_binding_allowed remains false

## Preservation

- [ ] real-video target remains unknown
- [ ] real-video Tingyun trace level remains unknown
- [ ] effect order remains unresolved
- [ ] same-current-turn duration remains unverified
- [ ] no executable DMG buff
- [ ] Tingyun Energy binding unchanged
- [ ] Pela binding unchanged
- [ ] reviewed registry remains exactly two entries
- [ ] simulator/search/evaluator/replay unchanged
- [ ] locked manifest unchanged
- [ ] no 002O work

## Gates

- [ ] compileall passes
- [ ] complete pytest passes
- [ ] locked regression passes 20/20
- [ ] trace-evidence-only regression passes 2/2
- [ ] Markdown and JSON reports are byte-identical to regeneration
