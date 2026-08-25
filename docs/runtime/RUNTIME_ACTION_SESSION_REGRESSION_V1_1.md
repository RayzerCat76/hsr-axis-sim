# Runtime Action-Session Regression Manifest v1.1

## Purpose

`hsr_axis_sim/data/runtime_action_session_regression_manifest.json` is the locked standalone regression lane for reviewed production action-session Runtime Trace Golden fixtures.

Version 1.1 promotes the reviewed ARCH-021 clamped-Energy fixture while keeping the regression harness deliberately narrower than the simulator's general effect model.

## Version compatibility

The loader accepts two manifest versions:

- `1.0`: the original ARCH-018 schema. Case objects contain exactly `id`, `expected_path`, `expected_sha256`, `stream_id`, `actor_id`, and `actions`. A `setup` field is rejected.
- `1.1`: the same case fields plus one required strict `setup` object.

Unknown versions remain rejected. Version 1.1 is not a permissive extension of v1.0; each version retains its own exact field contract.

## v1.1 setup contract

`setup.kind` is a closed discriminator with exactly two accepted values.

### `EMPTY`

Exact form:

```json
{"kind":"EMPTY"}
```

The runner constructs `BattleState([])` and every declared action remains effect-free. This reproduces the accepted ARCH-017 regression behavior.

### `ENERGY_GAIN`

Exact fields:

```text
kind
target_id
target_name
team
base_speed
initial_energy
max_energy
action_index
amount
```

The runner constructs exactly one `Unit` using the declared target identity/team/speed/Energy values. The action at `action_index` receives exactly one production `GainEnergy(target_ids=[target_id], amount=amount)` effect. All other actions remain effect-free.

Validation is intentionally narrow:

- string fields must be non-empty strings;
- `base_speed`, `initial_energy`, `max_energy`, and `amount` must be finite numbers and must not be booleans;
- `base_speed` must be greater than zero because that is an existing `Unit` constructor requirement;
- `action_index` must be an exact nonnegative integer and must identify a declared action.

No new Energy range/sign policy is introduced by the manifest layer. Production `Unit`/`GainEnergy` behavior remains authoritative.

## Locked cases

The v1.1 locked manifest contains exactly two reviewed cases in declared order:

1. `arch-017-reviewed-static-action-session` using `EMPTY`, preserving the original four-record action-only Golden fixture.
2. `arch-021-reviewed-static-clamped-energy` using `ENERGY_GAIN`, preserving the three-record `ACTION_START -> ENERGY_CHANGED -> ACTION_END` Golden fixture and its requested-versus-applied clamp observation.

## Explicit non-goals

Version 1.1 does not provide:

- arbitrary effect lists or effect names;
- reflection/import paths;
- free-form constructor kwargs;
- character/skill databases;
- scripts or expression evaluation;
- SP setup cases;
- AV/timeline setup cases;
- fixture generation;
- video extraction.

A future regression case that needs another simulator primitive must receive its own reviewed narrow schema evolution rather than turning this manifest into a generic combat DSL.
