# Legacy Event Adapter v1

## Scope

`hsr_axis_sim.runtime_adapters` is a manually invoked, one-way observation
bridge. It converts an existing mutable `hsr_axis_sim.sim.events.Event` into an
immutable `RuntimeEvent`; the adapter itself does not hook production dispatch
and cannot send an envelope back into the simulator.

The exact mappings are:

| Legacy event | Runtime event | Status | Normalized IDs |
|---|---|---|---|
| `action_finished` | `ACTION_END` | bound | `actor_id`, `action_id` |
| `action_started` | `ACTION_START` | bound | `actor_id`, `action_id` |
| `damage_dealt` | `DAMAGE_RESOLVED` | bound | `source_id`, `target_id` |
| `energy_changed` | `ENERGY_CHANGED` | bound | `actor_id`, `action_id`, `target_id <- unit_id` |
| `skill_points_changed` | `SKILL_POINTS_CHANGED` | bound | `actor_id`, `action_id` |
| `turn_ended` | `TURN_END` | bound | `actor_id` |
| `turn_started` | `TURN_START` | bound | `actor_id` |
| `unit_defeated` | `CONTENT_DEFINED` | ambiguous | `target_id` |
| `weakness_break` | `WEAKNESS_BROKEN` | bound | `source_id`, `target_id` |

Unknown and ambiguous events each require an explicit caller policy: preserve
as `CONTENT_DEFINED` or reject with a controlled error. Neither choice has a
default. `unit_defeated` does not distinguish Downed, Knocked Down, Death,
pending revive, or lethal interception, so its lifecycle remains unresolved.
Its `killer_id` remains only in raw payload data and is never promoted to
`source_id`.

Every envelope ID is exactly `legacy:{stream_id}:{sequence}`. Stream adaptation
preserves input order and uses contiguous caller-based sequences. The full
legacy mapping is defensively snapshotted under `payload.legacy_data`; adapter
identity, mapping status, binding status, and semantic gaps are stored under
`payload.adapter`.

For `energy_changed` and `skill_points_changed`, the adapter additionally
constructs an ARCH-019 `RuntimeResourceChangeObservation` from the exact raw
legacy fields. Invalid resource kind/scope/data, missing fields, non-finite
numeric values, inconsistent `applied_delta`, or wrong SP integer types are
rejected as `LegacyEventSchemaError`; they are not repaired. The validated
`to_payload()` result is preserved under `payload.resource_change`.

Resource values remain event payload data. They are not rounded or promoted to
schema-v1 `RuntimeTraceRecord.numeric_values`; schema v1 still requires that
record-level mapping to remain empty.

The legacy surface exposes no reliable Attack or Hit identity and insufficient
Action hierarchy semantics. The adapter therefore creates no ActionContext,
AttackContext, or HitContext and infers no turn kind, priority, action family,
attack ID, hit ID, or source from `killer_id`.

ARCH-020 independently instruments only the existing production energy and
skill-point effects to emit normal `energy_changed` / `skill_points_changed`
events after successful mutation. Those events use the existing
`BattleState.emit_event` trigger-visible dispatch path. The adapter remains a
manual downstream observation boundary; it does not own production mutation,
rollback, retry, event retention, or trigger lifecycle semantics.

All non-resource simulator formulas, timeline behavior, lifecycle behavior,
and the existing LIFO extra-turn stack remain unchanged by this adapter
contract.
