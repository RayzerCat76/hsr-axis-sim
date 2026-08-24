"""Strict JSON decoding with duplicate-key and constant rejection."""

from __future__ import annotations

import json
from typing import Any

from .model import DuplicateJsonKeyError, RuntimeTraceJsonError


def _object_from_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise RuntimeTraceJsonError(f"non-finite JSON constant is forbidden: {value}")


def decode_runtime_trace_json(text: str) -> dict[str, Any]:
    if not isinstance(text, str):
        raise RuntimeTraceJsonError("JSON input must be decoded text")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_from_pairs,
            parse_constant=_reject_constant,
        )
    except DuplicateJsonKeyError:
        raise
    except RuntimeTraceJsonError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise RuntimeTraceJsonError(f"invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeTraceJsonError("runtime trace JSON root must be an object")
    return value
