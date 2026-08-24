# AGENTS.md — HSR Axis Sim Tool

## Sources of truth
- `docs/HSR_AXIS_SIM_MASTER_BIBLE.md` = canonical design truth.
- GitHub `main` = canonical accepted implementation truth.
- `docs/DECISION_LOG.md` = durable decision history.

## Required workflow
Before editing: read this file, the Master Bible, the task scope, then inspect the repository.
Use one milestone per branch/PR. Implement only authorized scope. Preserve passing behavior.
Run real tests and report real results. Do not start future milestones early.

## Core rules
Priority: correctness > determinism > validation > test coverage > trace inspectability > usability > visual polish > automation.

Never invent hidden HSR values. Unknown mechanics remain `UNKNOWN`, `PARTIAL`, optional, unresolved, or explicit extension hooks. **Unknown > Guess.**

Do not silently correct invalid ownership, SP, energy, or state transitions when strict validation requires rejection.
Do not branch universal runtime behavior on character names.
Do not silently reinterpret semantic contracts.

## Evidence
- `CONFIRMED`: sufficiently supported for the current contract.
- `PARTIAL`: direction supported, material details unresolved.
- `UNKNOWN`: insufficient evidence.

Separate visible observation, structured data, inferred semantic rule, and implementation reference.
Research is not automatic authorization to change production semantics.

## Locked behavior
Unless a dedicated accepted task authorizes change:
- accepted production behavior is protected;
- locked regression fixtures are protected;
- production LIFO extra-turn behavior is protected;
- actual HSR FIFO/LIFO game semantics remain separate and unresolved;
- accepted trace schemas and accepted research/reference files are protected.

## Validation
Default implementation validation:
```bash
python -m compileall -q hsr_axis_sim
python -m pytest -q
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --format text
python -m hsr_axis_sim.regression.runner --manifest hsr_axis_sim/data/regression_manifest.json --only trace_evidence --format text
```

## Milestone review
Luman returns exactly one:
- `PASS — proceed`
- `PARTIAL — fixes required`
- `BLOCKED — exact blocker`
- `FAIL — acceptance criteria not met`

Codex is optional, not mandatory.
