# LUMEN REVIEW CHECKLIST — HSR-AXIS-001Z

## Task

**HSR-AXIS-001Z — Regression Manifest / Baseline Lock MVP**

## Primary goal

Confirm that the current regression baseline is explicitly registered in a manifest and that the regression runner can validate exactly that baseline.

## Must pass

- [ ] `python -m pytest -q` passes.
- [ ] Existing discovery-mode regression runner still works.
- [ ] Manifest-mode regression runner works.
- [ ] Manifest-mode `--only replays` works.
- [ ] Manifest-mode `--only manual` works.
- [ ] Manifest-mode `--only scenarios` works.
- [ ] Text report includes manifest metadata when run with manifest.
- [ ] Markdown report includes manifest metadata when run with manifest.
- [ ] JSON report includes manifest metadata when run with manifest.

## Manifest file checks

- [ ] `hsr_axis_sim/data/regression_manifest.json` exists.
- [ ] Manifest has a stable `manifest_id`.
- [ ] Manifest lists all 12 golden replays.
- [ ] Manifest lists the manual video sample trace.
- [ ] Manifest lists the 2 search scenario fixtures.
- [ ] Paths are relative to project root and resolve correctly.
- [ ] Manifest is human-editable and not over-engineered.

## Validation checks

- [ ] Duplicate fixture ids are rejected.
- [ ] Missing fixture paths are rejected.
- [ ] Invalid group names are rejected.
- [ ] Error messages are clear enough for a future user to fix the manifest.

## Scope control

- [ ] No combat-core changes.
- [ ] No timeline semantics changes.
- [ ] No damage formula changes.
- [ ] No break logic changes.
- [ ] No buff/debuff duration changes.
- [ ] No target legality changes.
- [ ] No enemy AI changes.
- [ ] No beam search ordering changes.
- [ ] No scraping or external network logic.
- [ ] No real video trace intake yet.

## Review notes to write after inspection

- Test count and pass/fail result.
- Regression manifest pass/fail result.
- Whether 001Z cleanly closes the 001 MVP baseline.
- Whether 002A can begin.

## Expected verdicts

### Pass

001Z passes if manifest-mode and discovery-mode regression both work and no combat-core behavior was changed.

### Fix required

Ask for a fix if:

- manifest mode breaks discovery mode;
- manifest paths depend on current working directory;
- manifest validation silently ignores bad paths or duplicate ids;
- JSON/Markdown reports omit manifest metadata;
- combat-core files were changed unnecessarily.
