import pytest

from hsr_axis_sim.runtime_loaders import DuplicateJsonKeyError, RuntimeTraceJsonError, decode_runtime_trace_json


def test_valid_object_and_invalid_roots():
    assert decode_runtime_trace_json('{"a":1,"nested":{"b":true}}') == {"a": 1, "nested": {"b": True}}
    for text in ("", "[]", "null", "{bad"):
        with pytest.raises(RuntimeTraceJsonError):
            decode_runtime_trace_json(text)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_constants_rejected(constant):
    with pytest.raises(RuntimeTraceJsonError):
        decode_runtime_trace_json('{"value":' + constant + "}")


def test_duplicate_keys_rejected_at_every_depth():
    with pytest.raises(DuplicateJsonKeyError):
        decode_runtime_trace_json('{"a":1,"a":2}')
    with pytest.raises(DuplicateJsonKeyError):
        decode_runtime_trace_json('{"outer":{"a":1,"a":2}}')
