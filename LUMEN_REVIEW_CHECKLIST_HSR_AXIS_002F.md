# LUMEN REVIEW CHECKLIST — HSR-AXIS-002F

## Scope

- [ ] New work is limited to the trace-evidence report model, renderers, CLI, sample reports, tests, and result documentation.
- [ ] Locked regression manifest is unchanged.
- [ ] Combat, replay, search, character, timeline, AV, damage, buff, debuff, and RNG behavior are unchanged.
- [ ] 002G was not started.

## Source validation

- [ ] Source trace is linted as action-sequence-only evidence.
- [ ] Existing semantic-map validator is run.
- [ ] Existing frame-anchor validator is run.
- [ ] Missing, duplicate, extra, or mismatched evidence fails clearly.
- [ ] Report ordering follows the source trace.

## Report content

- [ ] Source video, scenario, team, and policy are present.
- [ ] Prebattle evidence is included.
- [ ] Exactly 9 ordered steps are included.
- [ ] Actor/action sequence matches the accepted trace exactly.
- [ ] Semantic label/category/known/unknown data are preserved.
- [ ] Media ranges, confidence, frame filenames, and notes are preserved.
- [ ] Unknown target/numeric fields remain unknown.
- [ ] Media time is explicitly distinguished from AV and simulator time.

## Determinism

- [ ] Markdown output is deterministic.
- [ ] JSON output is deterministic.
- [ ] Shuffling semantic-map or anchor input order does not change output.
- [ ] Committed sample reports exactly match generated reports.
- [ ] UTF-8 Chinese text is preserved.

## CLI

- [ ] Markdown to stdout passes.
- [ ] JSON to stdout passes.
- [ ] `--output` writes UTF-8 files.
- [ ] Normal validation failure returns 1 without traceback.
- [ ] Invalid/unreadable input returns 2 with a readable error.

## Trust boundary

- [ ] Report is marked evidence-only and non-executable.
- [ ] No action-advance percentage is inferred.
- [ ] Composite actions are not split into executable actions.
- [ ] No unknown target is filled.
- [ ] No SP, energy, HP, toughness, damage, speed, buff, debuff, or RNG claim is added.
- [ ] No OCR, video download, or automatic recognition was added.

## Required gates

- [ ] `python -m compileall -q hsr_axis_sim` passes.
- [ ] Full `python -m pytest -q` passes with zero failures.
- [ ] Locked manifest regression remains PASS 20/20.
- [ ] `--only trace_evidence` remains PASS 2/2.
- [ ] Manifest counts remain 12 / 1 / 2 / 1 / 2.
