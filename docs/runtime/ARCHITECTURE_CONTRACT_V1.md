# Universal Runtime Architecture Contract v1

## Boundary

`hsr_axis_sim.runtime_contracts` is a sidecar-only interface package. The
existing `hsr_axis_sim.sim` package remains the active MVP runtime, and
HSR-RUNTIME-ARCH-001 performs no behavior migration. Existing lower-case MVP
event strings and execution behavior are unchanged.

The contract hierarchy is explicit:

```text
ActionContext
└── AttackContext (zero or more per Action)
    └── HitContext (zero or more per Attack)
```

An Action describes timeline ownership and priority vocabulary. An Attack
describes one targeting declaration. A Hit identifies one resolved target and
the requests associated with that hit. None of these contracts resolves a
target, consumes RNG, dispatches an event, or executes a formula.

## Event vocabulary

`RuntimeEvent` is an immutable envelope with stable `RuntimeEventType` names
for battle, wave, turn, action, attack, hit, damage, HP, Shield, Toughness,
effect, lethal, lifecycle, and queue boundaries. It is vocabulary only: there
is no dispatcher and no adapter into the MVP runtime in ARCH-001.

## Evidence and binding

- `CONFIRMED` may be `BOUND`, `INTERFACE_ONLY`, or `UNRESOLVED`. A bound
  contract requires at least one source reference.
- `PARTIAL` may only be `INTERFACE_ONLY` or `UNRESOLVED`.
- `UNKNOWN` must be `UNRESOLVED`.
- An `UNRESOLVED` contract cannot select a policy.

`SemanticContract.require_bound()` raises `UnresolvedMechanicError` instead of
selecting a fallback. The checked-in unresolved registry contains every one of
the 12 `UNKNOWN` mechanics from Formula Registry v1.0 and permits no production
binding.

## Deterministic trace data

Canonical serialization sorts mapping keys and supports compact and pretty
JSON. Contract payloads are defensively frozen. Unsupported opaque objects are
rejected; they are never converted with `repr()`.

`TraceNumericValue.raw_value` preserves exact Decimal or rational text.
`displayed_value` is a separate optional field, and its quantization policy is
recorded explicitly. Display rounding must never feed back into raw state.

## Migration boundary

A future adapter may translate existing MVP observations into these envelopes
at the boundary between `hsr_axis_sim.sim` and a universal runtime. That bridge
must be a later milestone and must preserve the evidence gates here. No
production module imports this sidecar in ARCH-001.

The historical MVP uses LIFO extra-turn behavior. Research indicates a
semantic conflict with later evidence, but FIFO versus LIFO remains unresolved.
This contract assigns no numeric priority and selects no FIFO/LIFO default;
production LIFO behavior remains unchanged.
