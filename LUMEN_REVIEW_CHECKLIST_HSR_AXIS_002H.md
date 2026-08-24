# LUMEN REVIEW CHECKLIST — HSR-AXIS-002H

## Required files

- [ ] source-registry tool module
- [ ] source catalog JSON
- [ ] required-facts/provenance JSON
- [ ] focused test file
- [ ] accepted Markdown report
- [ ] accepted JSON report
- [ ] research log
- [ ] updated `hsr_axis_sim/LUMEN_RESULT.md`

## Source quality and provenance

- [ ] Every external source has URL/identifier, type, language, retrieval date, and version applicability.
- [ ] Official sources are distinguished from structured databases and community references.
- [ ] Beta/leak/stale/version-ambiguous sources are not silently treated as live verified data.
- [ ] Long copyrighted skill text is not copied; facts are short paraphrases/numerical fields.
- [ ] Rejected sources and reasons are recorded.
- [ ] Conflicting sources remain visibly conflicting.

## Identity integrity

- [ ] Existing internal actor IDs remain unchanged.
- [ ] Canonical Chinese and English names are source-backed.
- [ ] Aliases/transliterations are recorded separately.
- [ ] The compatibility ID `naxia` is preserved even if the canonical English name differs.
- [ ] Character/game-data IDs are only recorded when verified.

## Fact integrity

- [ ] Prebattle and all nine trace steps are covered.
- [ ] Facts link to exact actor/action/step requirements.
- [ ] Verified facts have qualifying provenance.
- [ ] Missing facts use null values.
- [ ] Conflicting facts have at least two conflicting provenance entries.
- [ ] Version and translation ambiguity is explicit.
- [ ] No target, resource, combat state, RNG, or action-advance value is inferred without a verified source.
- [ ] Every fact has `simulator_binding_allowed: false`.

## Validation

- [ ] Duplicate source IDs fail.
- [ ] Duplicate fact IDs fail.
- [ ] Unsupported vocabularies fail.
- [ ] Dangling source references fail.
- [ ] Invalid URL/local evidence identifiers fail.
- [ ] Verified facts without qualifying sources fail.
- [ ] Invalid conflict records fail.
- [ ] Missing facts with non-null values fail.
- [ ] Any simulator-binding permission fails.
- [ ] Executable character/effect schemas are rejected.
- [ ] Mismatched trace links fail.

## Output and CLI

- [ ] Markdown clearly states non-executable provenance-only status.
- [ ] Source catalog and identity tables are readable.
- [ ] Coverage by trace step is clear.
- [ ] Field-level provenance is visible.
- [ ] Conflicts and missing facts are summarized.
- [ ] Output is deterministic and independent of input list order.
- [ ] Committed files match generated output byte-for-byte.
- [ ] CLI stdout and `--output` work.
- [ ] Validated mismatch returns 1.
- [ ] Input/runtime failure returns 2.

## Scope gates

- [ ] No real character kit is implemented.
- [ ] No simulator CharacterSpec/SkillSpec/Effect/Trigger is added.
- [ ] No trace actor ID is renamed.
- [ ] No real trace is made executable.
- [ ] No combat, replay, search, evaluator, or existing character code is changed.
- [ ] Locked manifest remains unchanged.

## Regression gates

- [ ] `python -m compileall -q hsr_axis_sim`
- [ ] full pytest passes
- [ ] locked manifest remains PASS 20/20
- [ ] trace-evidence-only remains PASS 2/2
- [ ] manifest counts remain unchanged
