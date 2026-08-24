# LUMEN Review — HSR-AXIS-002L After Codex

## Verdict

**NEEDS FIX — do not begin 002M yet.**

The intended Tingyun Ultimate partial resource/interrupt shell works, the reviewed registry v0.2 architecture is directionally correct, and all normal tests/regressions pass. However, the new handler-specific validation boundary can still raise an uncaught `TypeError` and print a traceback when a reviewed binding JSON contains a list item of the wrong type.

Because the reviewed-binding registry is the controlled gateway from source evidence into executable simulator behavior, malformed package-contained binding data must fail as a controlled validation error rather than crash the registry CLI.

## Independent results

- `python -m compileall -q hsr_axis_sim`: **PASS**
- `python -m pytest -q`: **381 passed in 39.46s**
- locked regression: **PASS 20/20**
- trace-evidence-only regression: **PASS 2/2**
- registry v0.2 Markdown/JSON reports: **byte-identical**
- Tingyun binding Markdown/JSON reports: **byte-identical**
- historical v0.1 registry and Pela reports: protected by passing hash tests

## What is correct

- Registry v0.2 contains exactly two reviewed, partial, synthetic-only bindings.
- Handler dispatch remains a static in-code allow-list.
- Each handler specification pins an executor, validator, and accepted atomic-fact SHA-256.
- Registry JSON cannot provide a Python module or callable.
- Execution revalidates the immutable handle, binding, metadata, artifact path, digest, and selected handler.
- Tingyun Ultimate partial shell correctly:
  - targets one living ally;
  - consumes 130 Energy from Tingyun before target mutation;
  - restores 50 Energy to the selected ally with max-Energy clamping;
  - executes as an interrupt;
  - does not change SP, global AV, normal timeline AV, HP, toughness, or buffs;
  - does not end a normal turn.
- The damage buff, real-video target, and initial real-video combat state remain unresolved and non-executable.

## Blocking defect

A malformed Tingyun binding with:

```json
{
  "source_atomic_fact_ids": [{"bad": "value"}]
}
```

reaches:

```python
set(source_ids)
```

and raises:

```text
TypeError: unhashable type: 'dict'
```

Running the reviewed registry CLI with such a package-contained binding produces a Python traceback instead of a controlled validation result.

The same class of problem exists in the older Pela validator because it also converts unvalidated list contents to sets. The new multi-handler registry must not preserve a crash path in either handler.

## Required correction

Before any `set(...)`, dict-key construction, union, sorting, or comparison:

- validate that fact-ID and unresolved-field containers are lists;
- validate every member is a non-empty string;
- reject duplicates deterministically;
- validate `atomic_facts` is a list of objects with unique, non-empty string `atomic_fact_id` values;
- ensure malformed Tingyun and Pela binding data raises `ValueError` with a controlled message;
- ensure registry CLI returns validation failure without traceback;
- preserve every accepted execution result and all historical artifacts.

Do not implement any part of 002M in this fix.
