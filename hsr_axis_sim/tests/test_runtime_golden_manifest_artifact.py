from dataclasses import FrozenInstanceError
import hashlib
import json

import pytest

from hsr_axis_sim.runtime_contracts.serialization import canonical_json_bytes
from hsr_axis_sim.runtime_golden_batches import GoldenReplayBatchPlan
from hsr_axis_sim.runtime_golden_cases import GoldenReplayFileCase
from hsr_axis_sim.runtime_golden_manifests import (
    MANIFEST_SCHEMA_NAME,
    MANIFEST_SCHEMA_VERSION,
    GoldenReplayManifestArtifact,
    GoldenReplayManifestCanonicalityError,
    GoldenReplayManifestDecodeError,
    GoldenReplayManifestDigestMismatchError,
    GoldenReplayManifestInputError,
    GoldenReplayManifestSchemaError,
    GoldenReplayManifestSizeLimitError,
    build_golden_replay_manifest_artifact,
    load_golden_replay_manifest_bytes,
)
from hsr_axis_sim.runtime_golden_replays import GoldenReplayValidationConfig
from hsr_axis_sim.runtime_loaders import TraceCanonicalFormPolicy


def file_case(replay_id, *, policy=TraceCanonicalFormPolicy.EITHER_CANONICAL, max_bytes=100_000):
    digest = hashlib.sha256(f"expected:{replay_id}".encode()).hexdigest()
    config = GoldenReplayValidationConfig(replay_id, digest, policy, max_bytes)
    return GoldenReplayFileCase(
        config,
        f"cases/{replay_id}/expected.json",
        f"cases/{replay_id}/actual.json",
    )


def plan():
    return GoldenReplayBatchPlan(
        "batch-001",
        (
            file_case("case-a", policy=TraceCanonicalFormPolicy.COMPACT_ONLY, max_bytes=12345),
            file_case("case-b", policy=TraceCanonicalFormPolicy.EITHER_CANONICAL, max_bytes=67890),
        ),
    )


def decoded(artifact):
    return json.loads(artifact.payload_bytes.decode("utf-8"))


def test_build_is_deterministic_compact_canonical_and_sha256_addressed():
    first = build_golden_replay_manifest_artifact(plan())
    second = build_golden_replay_manifest_artifact(plan())

    assert first == second
    assert first.payload_bytes == second.payload_bytes
    assert first.sha256 == hashlib.sha256(first.payload_bytes).hexdigest()
    assert first.byte_count == len(first.payload_bytes)
    assert b"\n" not in first.payload_bytes
    data = decoded(first)
    assert data["schema_name"] == MANIFEST_SCHEMA_NAME
    assert data["schema_version"] == MANIFEST_SCHEMA_VERSION
    assert [case["replay_id"] for case in data["cases"]] == ["case-a", "case-b"]


def test_strict_load_round_trips_to_accepted_batch_plan_and_preserves_order():
    source_plan = plan()
    artifact = build_golden_replay_manifest_artifact(source_plan)
    loaded = load_golden_replay_manifest_bytes(
        artifact.payload_bytes,
        max_bytes=artifact.byte_count,
        expected_sha256=artifact.sha256,
    )

    assert loaded == artifact
    assert loaded.plan == source_plan
    assert [case.replay_id for case in loaded.plan.cases] == ["case-a", "case-b"]
    assert loaded.plan.cases[0].validation_config.canonical_form_policy is TraceCanonicalFormPolicy.COMPACT_ONLY
    assert loaded.plan.cases[0].validation_config.max_bytes == 12345


def test_noncanonical_whitespace_and_pretty_json_are_rejected_without_repair():
    artifact = build_golden_replay_manifest_artifact(plan())
    data = decoded(artifact)
    with pytest.raises(GoldenReplayManifestCanonicalityError):
        load_golden_replay_manifest_bytes(b" " + artifact.payload_bytes, max_bytes=100_000)
    with pytest.raises(GoldenReplayManifestCanonicalityError):
        load_golden_replay_manifest_bytes(canonical_json_bytes(data, pretty=True), max_bytes=100_000)


def test_duplicate_keys_invalid_json_invalid_utf8_and_nan_are_decode_errors():
    payloads = (
        b'{"x":1,"x":2}',
        b'{"x":',
        b"\xff",
        b'{"x":NaN}',
    )
    for payload in payloads:
        with pytest.raises(GoldenReplayManifestDecodeError):
            load_golden_replay_manifest_bytes(payload, max_bytes=100_000)


def test_digest_mismatch_and_size_limit_are_checked_on_exact_input_bytes():
    artifact = build_golden_replay_manifest_artifact(plan())
    with pytest.raises(GoldenReplayManifestDigestMismatchError):
        load_golden_replay_manifest_bytes(
            artifact.payload_bytes,
            max_bytes=100_000,
            expected_sha256="0" * 64,
        )
    with pytest.raises(GoldenReplayManifestSizeLimitError):
        load_golden_replay_manifest_bytes(
            artifact.payload_bytes,
            max_bytes=artifact.byte_count - 1,
        )


def test_manifest_api_input_validation_is_strict():
    artifact = build_golden_replay_manifest_artifact(plan())
    with pytest.raises(GoldenReplayManifestInputError):
        build_golden_replay_manifest_artifact(object())
    with pytest.raises(GoldenReplayManifestInputError):
        load_golden_replay_manifest_bytes(bytearray(artifact.payload_bytes), max_bytes=100_000)
    with pytest.raises(GoldenReplayManifestInputError):
        load_golden_replay_manifest_bytes(artifact.payload_bytes, max_bytes=0)
    with pytest.raises(GoldenReplayManifestInputError):
        load_golden_replay_manifest_bytes(artifact.payload_bytes, max_bytes=True)
    with pytest.raises(GoldenReplayManifestInputError):
        load_golden_replay_manifest_bytes(artifact.payload_bytes, max_bytes=100_000, expected_sha256="BAD")


def test_top_level_schema_name_version_missing_and_unknown_fields_are_rejected():
    artifact = build_golden_replay_manifest_artifact(plan())
    base = decoded(artifact)

    variants = []
    wrong_name = dict(base)
    wrong_name["schema_name"] = "other"
    variants.append(wrong_name)
    wrong_version = dict(base)
    wrong_version["schema_version"] = "2.0"
    variants.append(wrong_version)
    missing = dict(base)
    del missing["batch_id"]
    variants.append(missing)
    unknown = dict(base)
    unknown["metadata"] = {}
    variants.append(unknown)

    for data in variants:
        with pytest.raises(GoldenReplayManifestSchemaError):
            load_golden_replay_manifest_bytes(canonical_json_bytes(data), max_bytes=100_000)


def test_case_schema_unknown_missing_policy_and_downstream_contract_errors_are_rejected():
    artifact = build_golden_replay_manifest_artifact(plan())
    base = decoded(artifact)
    variants = []

    unknown = json.loads(json.dumps(base))
    unknown["cases"][0]["extra"] = 1
    variants.append(unknown)

    missing = json.loads(json.dumps(base))
    del missing["cases"][0]["expected_sha256"]
    variants.append(missing)

    bad_policy_type = json.loads(json.dumps(base))
    bad_policy_type["cases"][0]["canonical_form_policy"] = 1
    variants.append(bad_policy_type)

    bad_policy_value = json.loads(json.dumps(base))
    bad_policy_value["cases"][0]["canonical_form_policy"] = "UNKNOWN"
    variants.append(bad_policy_value)

    bad_path = json.loads(json.dumps(base))
    bad_path["cases"][0]["expected_relative_path"] = "../escape.json"
    variants.append(bad_path)

    bad_max = json.loads(json.dumps(base))
    bad_max["cases"][0]["max_bytes"] = True
    variants.append(bad_max)

    for data in variants:
        with pytest.raises(GoldenReplayManifestSchemaError):
            load_golden_replay_manifest_bytes(canonical_json_bytes(data), max_bytes=100_000)


def test_empty_cases_duplicate_replay_ids_and_invalid_batch_id_are_rejected_by_accepted_batch_contract():
    artifact = build_golden_replay_manifest_artifact(plan())
    base = decoded(artifact)

    empty = json.loads(json.dumps(base))
    empty["cases"] = []
    duplicate = json.loads(json.dumps(base))
    duplicate["cases"][1]["replay_id"] = duplicate["cases"][0]["replay_id"]
    invalid_batch = json.loads(json.dumps(base))
    invalid_batch["batch_id"] = ""

    for data in (empty, duplicate, invalid_batch):
        with pytest.raises(GoldenReplayManifestSchemaError):
            load_golden_replay_manifest_bytes(canonical_json_bytes(data), max_bytes=100_000)


def test_artifact_is_frozen_and_rejects_incorrect_digest():
    artifact = build_golden_replay_manifest_artifact(plan())
    with pytest.raises(FrozenInstanceError):
        artifact.sha256 = "0" * 64
    with pytest.raises(GoldenReplayManifestInputError):
        GoldenReplayManifestArtifact(artifact.plan, artifact.payload_bytes, "0" * 64)
