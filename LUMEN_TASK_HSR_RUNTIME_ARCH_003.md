# LUMEN_TASK_HSR_RUNTIME_ARCH_003

## Task ID

`HSR-RUNTIME-ARCH-003`

## Title

Read-Only Runtime Trace Export

## Execution recommendation

- ChatGPT model: **GPT-5.6 Sol**
- Codex reasoning: **High**

## Latest completed task

`HSR-RUNTIME-ARCH-002 — PASS`

Confirmed baseline:

```text
746/746 tests passed
locked regression 20/20 passed
trace-evidence-only 2/2 passed
```

## Objective

Convert an explicitly supplied iterable of immutable RuntimeEvents into:

```text
RuntimeTraceRecord[]
→ immutable RuntimeTraceDocument
→ deterministic JSON bytes
→ exact-byte SHA-256
→ optional explicit file write
```

## Strict boundary

No:

```text
automatic simulator observation
BattleState access
pending_events access
production hooks
Action/Attack/Hit inference
numeric extraction
trace loading
trace comparison
JSONL
FIFO/LIFO changes
```

## Result

Update:

```text
hsr_axis_sim/LUMEN_RESULT.md
```

Stop after ARCH-003.
