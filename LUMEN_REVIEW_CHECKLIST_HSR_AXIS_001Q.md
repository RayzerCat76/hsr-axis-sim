# LUMEN REVIEW CHECKLIST — HSR-AXIS-001Q

## Task expected

**HSR-AXIS-001Q: External Data Import Adapter MVP**

This task should create an offline, fixture-based adapter that converts source-neutral raw external character JSON into the existing normalized `CharacterSpec` JSON format.

## Must pass locally

```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q hsr_axis_sim/tests
for f in hsr_axis_sim/data/golden_replays/*.json; do python -m hsr_axis_sim.sim.replay "$f"; done
python -m hsr_axis_sim.adapters.external_import --input hsr_axis_sim/data/raw/external_sample/sample_external_character.json --output /tmp/imported_external_character.json
```

## Required checks

### Scope control

- [ ] No website scraping.
- [ ] No network requests.
- [ ] No Huroka/Yatta/HoneyHunter page-specific code yet.
- [ ] No AI search or beam search.
- [ ] No core combat engine rewrite.
- [ ] Existing replays still pass.

### Adapter structure

- [ ] `hsr_axis_sim/adapters/__init__.py` exists.
- [ ] `hsr_axis_sim/adapters/source_models.py` exists.
- [ ] `hsr_axis_sim/adapters/external_import.py` exists.
- [ ] Offline raw fixture exists under `hsr_axis_sim/data/raw/external_sample/`.
- [ ] Normalized output is compatible with `CharacterSpec.from_dict`.

### Import behavior

- [ ] Raw fixture loads into a source model.
- [ ] Normalizer creates valid normalized character JSON.
- [ ] Unsupported/unknown effects produce warnings.
- [ ] Unsupported/unknown effects are not silently emitted as invalid effects.
- [ ] Source metadata is preserved or reported without making simulator logic depend on it.

### CLI behavior

- [ ] CLI accepts `--input` and `--output`.
- [ ] CLI writes normalized JSON.
- [ ] CLI prints a useful import report.
- [ ] CLI exits nonzero on invalid input if appropriate.

### Tests

- [ ] New tests cover successful import.
- [ ] New tests cover import warnings.
- [ ] New tests build a BattleState with imported character.
- [ ] New tests execute at least one imported skill action.
- [ ] Existing tests are not weakened or removed.

## Expected verdict logic

Pass 001Q only if:

- full tests pass,
- all golden replays pass,
- importer CLI works,
- no network/live scraping was added,
- imported output is valid according to current schema.

If Codex tries to scrape live Huroka/Yatta/HoneyHunter in this task, mark it as scope failure and request a fix.
