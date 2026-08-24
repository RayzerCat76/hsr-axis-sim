# LUMEN Review Checklist — HSR-AXIS-002M

## Scope

- Evidence and normalization only.
- No executable Tingyun damage buff.
- No real-video target or trace-level inference.
- No simulator-core or registry API changes.

## Facts

- Magnitude, duration, target scope, order, and version scope are separate atomic facts.
- Every fact has field-level provenance and verification status.
- Single-source fields are not mislabeled as corroborated.
- Beta and release data are not mixed silently.

## Duration semantics

- Report explicitly covers cast interrupt, current normal turn, extra turn, non-ending action, normal-turn decrement, and expiration boundary.
- Existing engine capability is assessed without changing it.
- Any mismatch remains a blocker, not an invented rule.

## Outputs

- Markdown and JSON reports deterministic.
- CLI stdout/file modes work.
- Invalid schema and malformed data fail cleanly without traceback.
- Regenerated reports are byte-identical to committed reports.

## Regression

- compileall passes.
- full pytest passes.
- locked regression PASS 20/20.
- trace-evidence-only regression PASS 2/2.
- Tingyun/Pela accepted partial bindings remain unchanged.
