# LUMEN Review Checklist — HSR-AXIS-002O

## Artifact architecture

- [ ] historical 002M and 002N artifacts remain unchanged
- [ ] new 002O normalized semantic-readiness artifact exists
- [ ] deterministic Markdown and JSON reports exist
- [ ] referenced input paths and digests are validated
- [ ] generic and accepted-video readiness are separate

## Magnitude integration

- [ ] 002N intake must be `captured_exact_table`
- [ ] exact levels 1–15 are consumed without selecting a video level
- [ ] two corroborating raw tables remain independently represented
- [ ] invalid digest/status/table conflict blocks readiness

## Effect order

- [ ] order is resolved only by exact behavior evidence, or remains unresolved
- [ ] prose listing is not treated as order evidence
- [ ] no order is inferred from animation or current engine order
- [ ] provenance and version scope are explicit

## Duration semantics

- [ ] same-current-turn edge is separately represented
- [ ] current engine behavior is not treated as proof of game behavior
- [ ] controlled test protocol, if added, contains no fabricated result
- [ ] no simulator duration behavior is changed in this task

## Safety

- [ ] no executable AddBuff
- [ ] no selected ally inferred for the accepted video
- [ ] no video trace level inferred
- [ ] Tingyun Energy binding unchanged
- [ ] Pela binding unchanged
- [ ] registry remains exactly two entries
- [ ] simulator/search/evaluator/replay/manifest unchanged
- [ ] no 002P work

## Validation

- [ ] malformed scalar types are rejected with ValueError
- [ ] duplicate/conflicting provenance is rejected
- [ ] wrong input path/digest is rejected
- [ ] deterministic ordering tests pass
- [ ] CLI invalid input is exit 1 without traceback
- [ ] CLI missing input is exit 2 without traceback

## Gates

- [ ] compileall passes
- [ ] complete pytest collection passes
- [ ] locked regression passes 20/20
- [ ] trace-evidence-only regression passes 2/2
- [ ] Markdown report is byte-identical to regeneration
- [ ] JSON report is byte-identical to regeneration
