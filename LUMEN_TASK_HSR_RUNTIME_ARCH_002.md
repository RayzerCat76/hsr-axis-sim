# LUMEN_TASK_HSR_RUNTIME_ARCH_002

## Task ID

`HSR-RUNTIME-ARCH-002`

## Title

Event Envelope Adapter Bridge

## Execution recommendation

- ChatGPT model: **GPT-5.6 Sol**
- Codex reasoning: **High**

## Latest completed task

`HSR-RUNTIME-ARCH-001 — PASS`

Independent baseline:

```text
718/718 tests passed
locked regression 20/20 passed
trace-evidence-only 2/2 passed
```

## Objective

Add a manually invoked, one-way adapter from the legacy mutable MVP `Event`
surface to immutable `RuntimeEvent` envelopes.

## Core boundary

Allowed:

```text
legacy Event / iterable[Event]
→ immutable RuntimeEvent envelope(s)
```

Forbidden:

```text
automatic hooks
production dispatch changes
Action/Attack/Hit reconstruction
two-way conversion
lifecycle guessing
FIFO/LIFO changes
RuntimeTraceRecord export
```

## Required package

```text
hsr_axis_sim/runtime_adapters/
```

## Exact known mapping

```text
action_started  -> ACTION_START
action_finished -> ACTION_END
turn_started    -> TURN_START
turn_ended      -> TURN_END
damage_dealt    -> DAMAGE_RESOLVED
weakness_break  -> WEAKNESS_BROKEN
unit_defeated   -> CONTENT_DEFINED / UNRESOLVED
```

## Result

Update:

```text
hsr_axis_sim/LUMEN_RESULT.md
```

Stop after ARCH-002.
