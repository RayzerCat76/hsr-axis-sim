"""Deterministic build and strict load functions for Golden Replay manifest v1."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from hsr_axis_sim.runtime_contracts.serialization import canonical_json_bytes
from hsr_axis_sim.runtime_golden_batches import GoldenReplayBatchInputError, GoldenReplayBatchPlan
from hsr_axis_sim.runtime_golden_cases import GoldenReplayFileCase, GoldenReplayFileCaseInputError
from hsr_axis_sim.runtime_golden_replays import (
    GoldenReplayValidationConfig,
    GoldenReplayValidationInputError,
)
from hsr_axis_sim.runtime_loaders import TraceCanonicalFormPolicy

from .model import (
    MANIFEST_SCHEMA_NAME,
    MANIFEST_SCHEMA_VERSION,
    GoldenReplayManifestArtifact,
    GoldenReplayManifestCanonicalityError,
    GoldenReplayManifestDecodeError,
    GoldenReplayManifestDigestMismatchError,
    GoldenReplayManifestInputError,
    GoldenReplayManifestSchemaError,
    GoldenReplayManifestSizeLimitError,
)


_TOP_LEVEL_FIELDS = frozenset({"schema_name", "schema_version", "batch_id", "cases"})
_CASE_FIELDS = frozenset(
    {
        "replay_id",
        "expected_sha256",
        "expected_relative_path",
        "actual_relative_path",
        "canonical_form_policy",
        "max_bytes",
    }
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


class _DuplicateKeyError(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_nonstandard_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _require_exact_fields(data: dict[str, Any], expected: frozenset[str], label: str) -> None:
    keys = set(data)
    missing = sorted(expected - keys)
    unknown = sorted(keys - expected)
    if missing:
        raise GoldenReplayManifestSchemaError(f"{label} missing required field(s): {missing}")
    if unknown:
        raise GoldenReplayManifestSchemaError(f"{label} has unknown field(s): {unknown}")


def _plan_to_data(plan: GoldenReplayBatchPlan) -> dict[str, Any]:
    return {
        "schema_name": MANIFEST_SCHEMA_NAME,
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "batch_id": plan.batch_id,
        "cases": [
            {
                "replay_id": case.validation_config.replay_id,
                "expected_sha256": case.validation_config.expected_sha256,
                "expected_relative_path": case.expected_relative_path,
                "actual_relative_path": case.actual_relative_path,
                "canonical_form_policy": case.validation_config.canonical_form_policy.value,
                "max_bytes": case.validation_config.max_bytes,
            }
            for case in plan.cases
        ],
    }


def build_golden_replay_manifest_artifact(
    plan: GoldenReplayBatchPlan,
) -> GoldenReplayManifestArtifact:
    if not isinstance(plan, GoldenReplayBatchPlan):
        raise GoldenReplayManifestInputError("plan must be GoldenReplayBatchPlan")
    payload = canonical_json_bytes(_plan_to_data(plan), pretty=False)
    return GoldenReplayManifestArtifact(
        plan=plan,
        payload_bytes=payload,
        sha256=hashlib.sha256(payload).hexdigest(),
    )


def _plan_from_data(data: Any) -> GoldenReplayBatchPlan:
    if not isinstance(data, dict):
        raise GoldenReplayManifestSchemaError("manifest root must be a JSON object")
    _require_exact_fields(data, _TOP_LEVEL_FIELDS, "manifest")
    if data["schema_name"] != MANIFEST_SCHEMA_NAME:
        raise GoldenReplayManifestSchemaError(
            f"manifest.schema_name must be {MANIFEST_SCHEMA_NAME!r}"
        )
    if data["schema_version"] != MANIFEST_SCHEMA_VERSION:
        raise GoldenReplayManifestSchemaError(
            f"manifest.schema_version must be {MANIFEST_SCHEMA_VERSION!r}"
        )
    cases_data = data["cases"]
    if not isinstance(cases_data, list):
        raise GoldenReplayManifestSchemaError("manifest.cases must be a JSON array")

    cases = []
    for index, case_data in enumerate(cases_data):
        label = f"manifest.cases[{index}]"
        if not isinstance(case_data, dict):
            raise GoldenReplayManifestSchemaError(f"{label} must be a JSON object")
        _require_exact_fields(case_data, _CASE_FIELDS, label)
        policy_value = case_data["canonical_form_policy"]
        if not isinstance(policy_value, str):
            raise GoldenReplayManifestSchemaError(f"{label}.canonical_form_policy must be a string")
        try:
            policy = TraceCanonicalFormPolicy(policy_value)
        except ValueError as exc:
            raise GoldenReplayManifestSchemaError(
                f"{label}.canonical_form_policy is unsupported: {policy_value!r}"
            ) from exc
        try:
            config = GoldenReplayValidationConfig(
                replay_id=case_data["replay_id"],
                expected_sha256=case_data["expected_sha256"],
                canonical_form_policy=policy,
                max_bytes=case_data["max_bytes"],
            )
            cases.append(
                GoldenReplayFileCase(
                    validation_config=config,
                    expected_relative_path=case_data["expected_relative_path"],
                    actual_relative_path=case_data["actual_relative_path"],
                )
            )
        except (GoldenReplayValidationInputError, GoldenReplayFileCaseInputError) as exc:
            raise GoldenReplayManifestSchemaError(f"{label} is invalid: {exc}") from exc

    try:
        return GoldenReplayBatchPlan(batch_id=data["batch_id"], cases=tuple(cases))
    except GoldenReplayBatchInputError as exc:
        raise GoldenReplayManifestSchemaError(f"manifest batch is invalid: {exc}") from exc


def load_golden_replay_manifest_bytes(
    payload_bytes: bytes,
    *,
    max_bytes: int,
    expected_sha256: str | None = None,
) -> GoldenReplayManifestArtifact:
    if not isinstance(payload_bytes, bytes):
        raise GoldenReplayManifestInputError("payload_bytes must be bytes")
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes <= 0:
        raise GoldenReplayManifestInputError("max_bytes must be a positive integer")
    if expected_sha256 is not None and (
        not isinstance(expected_sha256, str) or _SHA256_RE.fullmatch(expected_sha256) is None
    ):
        raise GoldenReplayManifestInputError(
            "expected_sha256 must be None or exactly 64 lowercase hexadecimal characters"
        )
    if len(payload_bytes) > max_bytes:
        raise GoldenReplayManifestSizeLimitError(
            f"manifest byte length {len(payload_bytes)} exceeds max_bytes {max_bytes}"
        )

    computed_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    if expected_sha256 is not None and computed_sha256 != expected_sha256:
        raise GoldenReplayManifestDigestMismatchError(
            f"manifest SHA-256 mismatch: expected {expected_sha256}, actual {computed_sha256}"
        )

    try:
        text = payload_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise GoldenReplayManifestDecodeError(f"manifest is not valid UTF-8: {exc}") from exc
    try:
        data = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonstandard_constant,
        )
    except (_DuplicateKeyError, json.JSONDecodeError, ValueError) as exc:
        raise GoldenReplayManifestDecodeError(f"manifest is not strict JSON: {exc}") from exc

    plan = _plan_from_data(data)
    canonical = build_golden_replay_manifest_artifact(plan)
    if payload_bytes != canonical.payload_bytes:
        raise GoldenReplayManifestCanonicalityError(
            "manifest bytes are valid schema-v1 data but are not exact compact canonical JSON"
        )
    return GoldenReplayManifestArtifact(
        plan=plan,
        payload_bytes=payload_bytes,
        sha256=computed_sha256,
    )
