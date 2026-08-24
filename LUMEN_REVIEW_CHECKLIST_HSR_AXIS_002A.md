# LUMEN REVIEW CHECKLIST — HSR-AXIS-002A

Use this checklist after Codex attempts the first real manual video trace fixture.

## Input integrity

- [ ] The trace is a real manually recorded trace, not synthetic filler.
- [ ] Codex did not browse, scrape, download, or invent video data.
- [ ] Source metadata includes platform, URL, title, uploader if known, recorder, and date.
- [ ] Assumptions and uncertainties are explicitly recorded.

## Fixture placement

- [ ] Real trace is stored under `hsr_axis_sim/data/manual_video_traces/real/`.
- [ ] Filename is stable and snake_case.
- [ ] Existing synthetic sample trace remains unchanged unless there is a clear bugfix.

## Lint / replay

- [ ] Manual trace lint passes, or issues are clearly reported.
- [ ] Replay validator passes, or exact mismatches are reported.
- [ ] Forced RNG is explicit for crits, target choices, effect hit/resist, or other observed randomness.
- [ ] Expected SP, energy, HP, AV, toughness, and buff/debuff states are checked where observable.

## Manifest

- [ ] If the trace passes, `regression_manifest.json` includes it under `groups.manual`.
- [ ] Manifest manual count increases from 1 to 2.
- [ ] Manifest regression passes.
- [ ] If replay fails, the failing trace is not silently added to the locked passing baseline.

## Code boundaries

- [ ] No combat-core files changed unless explicitly authorized.
- [ ] No timeline, damage, break, buff/debuff, target legality, enemy AI, action generation, ultimate window, or beam search changes.
- [ ] No Huroka/Yatta live import.
- [ ] No web scraping.

## Tests

- [ ] `python -m pytest -q` passes.
- [ ] Manifest runner passes in text/json mode.
- [ ] If replay mismatches, LUMEN_RESULT documents why 002B is blocked.

## Acceptance decision

- [ ] PASS: trace imported, lint/replay pass, manifest updated, full tests pass.
- [ ] CONDITIONAL: trace imported but replay mismatch requires mechanism diagnosis.
- [ ] FAIL/BLOCKED: no real trace input, fake trace invented, or core behavior changed without authorization.
