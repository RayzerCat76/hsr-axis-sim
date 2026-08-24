from dataclasses import FrozenInstanceError
import hashlib
from pathlib import Path

import pytest

from hsr_axis_sim.runtime_golden_batches import GoldenReplayBatchPlan
from hsr_axis_sim.runtime_golden_cases import GoldenReplayFileCase
from hsr_axis_sim.runtime_golden_manifest_files import (
    GoldenReplayManifestFileInputError,
    GoldenReplayManifestFileLoadResult,
    GoldenReplayManifestFileReadError,
    GoldenReplayManifestFileSpec,
    load_golden_replay_manifest_file,
    render_golden_replay_manifest_file_text,
)
from hsr_axis_sim.runtime_golden_manifests import (
    GoldenReplayManifestCanonicalityError,
    GoldenReplayManifestDigestMismatchError,
    GoldenReplayManifestSizeLimitError,
    build_golden_replay_manifest_artifact,
)
from hsr_axis_sim.runtime_golden_replays import GoldenReplayValidationConfig
from hsr_axis_sim.runtime_loaders import TraceCanonicalFormPolicy


def _case(replay_id: str) -> GoldenReplayFileCase:
    digest = hashlib.sha256(f"expected:{replay_id}".encode()).hexdigest()
    return GoldenReplayFileCase(
        GoldenReplayValidationConfig(
            replay_id,
            digest,
            TraceCanonicalFormPolicy.EITHER_CANONICAL,
            100_000,
        ),
        f"cases/{replay_id}/expected.json",
        f"cases/{replay_id}/actual.json",
    )


def _artifact():
    return build_golden_replay_manifest_artifact(
        GoldenReplayBatchPlan("batch-file-001", (_case("case-a"), _case("case-b")))
    )


def _write_manifest(tmp_path: Path, payload: bytes, relative: str = "manifests/golden.json") -> Path:
    target = tmp_path.joinpath(*relative.split("/"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return target


def test_loads_explicit_manifest_with_resolved_provenance_and_pinned_digest(tmp_path):
    artifact = _artifact()
    target = _write_manifest(tmp_path, artifact.payload_bytes)
    spec = GoldenReplayManifestFileSpec(
        "manifests/golden.json",
        artifact.byte_count,
        artifact.sha256,
    )

    result = load_golden_replay_manifest_file(spec, base_directory=tmp_path)

    assert result.spec == spec
    assert result.base_directory == str(tmp_path.resolve())
    assert result.manifest_path == str(target.resolve())
    assert result.artifact == artifact
    assert result.artifact.plan.batch_id == "batch-file-001"
    assert result.artifact.plan.case_count == 2


def test_optional_digest_none_still_preserves_computed_manifest_identity(tmp_path):
    artifact = _artifact()
    _write_manifest(tmp_path, artifact.payload_bytes)
    spec = GoldenReplayManifestFileSpec("manifests/golden.json", 100_000)

    result = load_golden_replay_manifest_file(spec, base_directory=tmp_path)

    assert result.artifact.sha256 == artifact.sha256
    assert result.artifact.payload_bytes == artifact.payload_bytes


def test_text_is_deterministic_and_does_not_execute_or_render_batch_results(tmp_path):
    artifact = _artifact()
    target = _write_manifest(tmp_path, artifact.payload_bytes)
    result = load_golden_replay_manifest_file(
        GoldenReplayManifestFileSpec("manifests/golden.json", 100_000, artifact.sha256),
        base_directory=tmp_path,
    )

    first = render_golden_replay_manifest_file_text(result)
    second = render_golden_replay_manifest_file_text(result)

    assert first == second
    assert first.startswith("GOLDEN_REPLAY_MANIFEST_FILE_LOADED\n")
    assert f"manifest_path=\"{target.resolve()}\"" in first
    assert f"manifest_sha256={artifact.sha256}" in first
    assert f"manifest_byte_count={artifact.byte_count}" in first
    assert 'batch_id="batch-file-001"' in first
    assert "case_count=2" in first
    assert "GOLDEN_REPLAY_BATCH_" not in first
    assert "GOLDEN_REPLAY_FILE_CASE_" not in first


@pytest.mark.parametrize(
    "value",
    ["", "/absolute.json", "../escape.json", "a/../escape.json", "a\\b.json", "a//b.json", "a/./b.json", "a/"],
)
def test_spec_rejects_noncanonical_or_unbounded_manifest_paths(value):
    with pytest.raises(GoldenReplayManifestFileInputError):
        GoldenReplayManifestFileSpec(value, 100)


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "100"])
def test_spec_requires_positive_integer_max_bytes(value):
    with pytest.raises(GoldenReplayManifestFileInputError):
        GoldenReplayManifestFileSpec("manifest.json", value)


def test_spec_rejects_invalid_optional_sha256():
    for value in ("BAD", "A" * 64, "0" * 63):
        with pytest.raises(GoldenReplayManifestFileInputError):
            GoldenReplayManifestFileSpec("manifest.json", 100, value)


def test_missing_or_non_directory_base_and_missing_or_directory_manifest_are_read_errors(tmp_path):
    artifact = _artifact()
    spec = GoldenReplayManifestFileSpec("manifest.json", 100_000)

    with pytest.raises(GoldenReplayManifestFileReadError):
        load_golden_replay_manifest_file(spec, base_directory=tmp_path / "missing")

    base_file = tmp_path / "base-file"
    base_file.write_text("not a directory")
    with pytest.raises(GoldenReplayManifestFileReadError):
        load_golden_replay_manifest_file(spec, base_directory=base_file)

    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(GoldenReplayManifestFileReadError):
        load_golden_replay_manifest_file(spec, base_directory=base)

    manifest_dir = base / "manifest.json"
    manifest_dir.mkdir()
    with pytest.raises(GoldenReplayManifestFileReadError):
        load_golden_replay_manifest_file(spec, base_directory=base)

    assert artifact.byte_count > 0


def test_symlink_escape_is_rejected_after_resolution(tmp_path):
    artifact = _artifact()
    base = tmp_path / "base"
    outside = tmp_path / "outside"
    base.mkdir()
    outside.mkdir()
    outside_manifest = outside / "golden.json"
    outside_manifest.write_bytes(artifact.payload_bytes)
    (base / "link.json").symlink_to(outside_manifest)

    with pytest.raises(GoldenReplayManifestFileReadError, match="escapes base directory"):
        load_golden_replay_manifest_file(
            GoldenReplayManifestFileSpec("link.json", 100_000),
            base_directory=base,
        )


def test_size_digest_and_canonicality_failures_are_delegated_to_001e(tmp_path):
    artifact = _artifact()
    target = _write_manifest(tmp_path, artifact.payload_bytes)

    with pytest.raises(GoldenReplayManifestSizeLimitError):
        load_golden_replay_manifest_file(
            GoldenReplayManifestFileSpec("manifests/golden.json", artifact.byte_count - 1),
            base_directory=tmp_path,
        )

    with pytest.raises(GoldenReplayManifestDigestMismatchError):
        load_golden_replay_manifest_file(
            GoldenReplayManifestFileSpec("manifests/golden.json", 100_000, "0" * 64),
            base_directory=tmp_path,
        )

    target.write_bytes(b" " + artifact.payload_bytes)
    with pytest.raises(GoldenReplayManifestCanonicalityError):
        load_golden_replay_manifest_file(
            GoldenReplayManifestFileSpec("manifests/golden.json", 100_000),
            base_directory=tmp_path,
        )


def test_spec_and_result_are_frozen_and_result_contract_is_strict(tmp_path):
    artifact = _artifact()
    target = _write_manifest(tmp_path, artifact.payload_bytes)
    spec = GoldenReplayManifestFileSpec("manifests/golden.json", 100_000)
    result = load_golden_replay_manifest_file(spec, base_directory=tmp_path)

    with pytest.raises(FrozenInstanceError):
        spec.max_bytes = 1
    with pytest.raises(FrozenInstanceError):
        result.manifest_path = "other"
    with pytest.raises(GoldenReplayManifestFileInputError):
        GoldenReplayManifestFileLoadResult(
            spec,
            "relative",
            str(target.resolve()),
            artifact,
        )
    with pytest.raises(GoldenReplayManifestFileInputError):
        GoldenReplayManifestFileLoadResult(
            spec,
            str(tmp_path.resolve()),
            str((tmp_path.parent / "outside.json").resolve()),
            artifact,
        )


def test_loader_and_renderer_reject_wrong_input_types(tmp_path):
    with pytest.raises(GoldenReplayManifestFileInputError):
        load_golden_replay_manifest_file(object(), base_directory=tmp_path)
    with pytest.raises(GoldenReplayManifestFileInputError):
        render_golden_replay_manifest_file_text(object())
