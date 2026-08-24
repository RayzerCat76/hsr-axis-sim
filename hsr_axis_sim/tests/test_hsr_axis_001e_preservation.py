from pathlib import Path

from hsr_axis_sim.sim import BattleState, Timeline, Unit


ROOT = Path(__file__).parents[2]
PROTECTED_AREAS = (
    "sim",
    "search",
    "regression",
    "adapters",
    "real_bindings",
    "data",
    "runtime_contracts",
    "runtime_adapters",
    "runtime_exports",
    "runtime_loaders",
    "runtime_comparators",
    "runtime_divergence",
    "runtime_golden_replays",
    "runtime_golden_cases",
    "runtime_golden_batches",
)


def test_manifest_artifact_is_downstream_of_all_accepted_runtime_packages():
    hits = []
    for area in PROTECTED_AREAS:
        for path in (ROOT / "hsr_axis_sim" / area).rglob("*.py"):
            if "runtime_golden_manifests" in path.read_text():
                hits.append(path)
    assert hits == []


def test_manifest_codec_reconstructs_contracts_without_executing_batches():
    source = (ROOT / "hsr_axis_sim" / "runtime_golden_manifests" / "codec.py").read_text()
    assert "GoldenReplayValidationConfig" in source
    assert "GoldenReplayFileCase" in source
    assert "GoldenReplayBatchPlan" in source
    assert "run_golden_replay_batch" not in source
    assert "run_golden_replay_file_case" not in source
    assert "validate_golden_replay_bytes" not in source


def test_production_lifo_compatibility_behavior_remains_unchanged():
    units = [Unit(name, name, "ally", 100) for name in ("first", "second", "third")]
    state = BattleState(units=units, extra_turn_stack=["first", "second", "third"])
    assert [Timeline.next_turn(state).actor_id for _ in range(3)] == ["third", "second", "first"]
