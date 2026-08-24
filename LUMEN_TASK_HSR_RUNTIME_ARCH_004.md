# LUMEN_TASK_HSR_RUNTIME_ARCH_004

## Task ID

`HSR-RUNTIME-ARCH-004`

## Title

Trace Document Loader and Integrity Validator

## Execution recommendation

- ChatGPT model: **GPT-5.6 Sol**
- Codex reasoning: **High**

## Latest completed task

`HSR-RUNTIME-ARCH-003 — PASS`

Confirmed baseline:

```text
766/766 tests passed
locked regression 20/20 passed
trace-evidence-only 2/2 passed
```

## Objective

Strictly load exact ARCH-003 trace schema v1 from explicit bytes or an explicit
file and validate:

```text
SHA-256 policy
UTF-8 / BOM
duplicate JSON keys
exact schema and enums
immutable reconstruction
sequence and event-ID integrity
counts and semantic-gap summary
canonical compact/pretty bytes
```

## Strict boundary

No:

```text
repair
migration
expected-vs-actual comparison
first divergence
automatic simulator observation
Action/Attack/Hit inference
numeric extraction
FIFO/LIFO changes
```

## Result

Update:

```text
hsr_axis_sim/LUMEN_RESULT.md
```

Stop after ARCH-004.
