# LUMEN REVIEW CHECKLIST — HSR-AXIS-002E

## Required gates

- [ ] Full pytest passes.
- [ ] Compileall passes.
- [ ] Existing four regression groups pass unchanged.
- [ ] No combat core mechanics changed.
- [ ] No hidden combat numbers were added to real trace evidence.

## Frame-anchor pre-flight hardening

- [ ] Wrong `status` is rejected.
- [ ] Wrong `timestamp_basis` is rejected.
- [ ] Empty/non-string `frame_anchor_id` is rejected.
- [ ] Empty/non-string `version` is rejected.
- [ ] Existing accepted frame-anchor fixture still passes.

## Manifest schema

- [ ] `trace_evidence` is a supported ordered group.
- [ ] Every evidence entry has an evidence path and explicit source-trace path.
- [ ] Supported checks are limited to `semantic_map` and `frame_anchors`.
- [ ] Unsupported checks fail clearly.
- [ ] Missing source-trace paths fail clearly.
- [ ] Older manifests remain backward compatible.
- [ ] Manifest counts show `trace_evidence=2`.

## Runner

- [ ] Semantic map validator is called for semantic-map entries.
- [ ] Frame-anchor validator is called for frame-anchor entries.
- [ ] Invalid evidence becomes a failed result rather than an uncaught crash.
- [ ] `--only trace_evidence` works with the locked manifest.
- [ ] Text report contains a separate trace-evidence summary.
- [ ] Markdown report contains the group.
- [ ] JSON report contains the group and count.
- [ ] Fail-fast behavior remains correct.

## Trust boundary

- [ ] Evidence is not treated as a replay.
- [ ] Media timestamps are not converted to AV or simulator time.
- [ ] Semantic placeholders remain non-executable.
- [ ] No exact Mem pull percentage is asserted.
- [ ] No exact internal timing for composite actions is asserted.

## Decision rule

Accept 002E only if the semantic map and frame anchors are formally locked as evidence while remaining completely separate from executable combat validation.
