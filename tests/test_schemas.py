"""Unit tests for the data contract (the first data-quality gate)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from schemas import WearableEvent


def _base_event(**overrides) -> dict:
    e = {
        "event_id": str(uuid.uuid4()),
        "user_id": "anon_0001",
        "device": "oura",
        "metric": "hrv",
        "value": 65.0,
        "unit": "ms",
        "event_ts": datetime.now(timezone.utc).isoformat(),
    }
    e.update(overrides)
    return e


def test_valid_event_passes():
    event = WearableEvent.model_validate(_base_event())
    assert event.metric.value == "hrv"
    assert event.device == "oura"


def test_value_out_of_range_rejected():
    with pytest.raises(ValidationError):
        WearableEvent.model_validate(_base_event(value=5000))


def test_unknown_device_rejected():
    with pytest.raises(ValidationError):
        WearableEvent.model_validate(_base_event(device="counterfeit_band"))


def test_missing_value_rejected():
    payload = _base_event()
    payload.pop("value")
    with pytest.raises(ValidationError):
        WearableEvent.model_validate(payload)


def test_bad_timestamp_rejected():
    with pytest.raises(ValidationError):
        WearableEvent.model_validate(_base_event(event_ts="not-a-timestamp"))


def test_unknown_metric_rejected():
    with pytest.raises(ValidationError):
        WearableEvent.model_validate(_base_event(metric="blood_pressure"))


def test_validate_from_json_string():
    raw = json.dumps(_base_event())
    event = WearableEvent.model_validate_json(raw)
    assert 5.0 <= event.value <= 250.0
