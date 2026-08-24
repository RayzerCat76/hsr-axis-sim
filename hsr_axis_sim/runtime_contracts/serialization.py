"""Defensive freezing and canonical JSON serialization helpers."""

from dataclasses import fields, is_dataclass
from enum import Enum
import json
import math
from types import MappingProxyType
from typing import Any, Mapping


_JSON_SCALARS = (str, int, bool, type(None))


def freeze_json(value: Any, *, path: str = "value") -> Any:
    """Validate and deeply freeze a JSON-compatible value."""
    if isinstance(value, _JSON_SCALARS):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} contains a non-finite float")
        return value
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key in sorted(value):
            if not isinstance(key, str):
                raise TypeError(f"{path} mapping keys must be strings")
            frozen[key] = freeze_json(value[key], path=f"{path}.{key}")
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(
            freeze_json(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        )
    raise TypeError(f"{path} contains unsupported object {type(value).__name__}")


def freeze_mapping(value: Mapping[str, Any], *, path: str) -> Mapping[str, Any]:
    frozen = freeze_json(value, path=path)
    if not isinstance(frozen, Mapping):  # defensive; the annotation is runtime-optional
        raise TypeError(f"{path} must be a mapping")
    return frozen


def to_canonical_data(value: Any) -> Any:
    """Convert supported contracts and JSON values to JSON-native data."""
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: to_canonical_data(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key in sorted(value):
            if not isinstance(key, str):
                raise TypeError("canonical JSON mapping keys must be strings")
            result[key] = to_canonical_data(value[key])
        return result
    if isinstance(value, (list, tuple)):
        return [to_canonical_data(item) for item in value]
    if isinstance(value, _JSON_SCALARS):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("canonical JSON does not support non-finite floats")
        return value
    raise TypeError(f"unsupported canonical JSON object: {type(value).__name__}")


def canonical_json_dumps(value: Any, *, pretty: bool = False) -> str:
    """Return deterministic compact or pretty JSON without lossy coercion."""
    options = {
        "ensure_ascii": False,
        "allow_nan": False,
        "sort_keys": True,
    }
    if pretty:
        return json.dumps(to_canonical_data(value), indent=2, **options) + "\n"
    return json.dumps(to_canonical_data(value), separators=(",", ":"), **options)


def canonical_json_bytes(value: Any, *, pretty: bool = False) -> bytes:
    return canonical_json_dumps(value, pretty=pretty).encode("utf-8")
