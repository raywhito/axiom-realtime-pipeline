"""The producer's 'valid' events must pass and its 'invalid' events must fail."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from events import make_invalid_event, make_valid_event
from schemas import WearableEvent


def test_producer_valid_events_pass():
    for _ in range(50):
        payload, _ = make_valid_event()
        WearableEvent.model_validate(payload)  # must not raise


def test_producer_invalid_events_are_rejected():
    rejected = 0
    for _ in range(50):
        payload, _ = make_invalid_event()
        try:
            WearableEvent.model_validate(payload)
        except (ValidationError, ValueError):
            rejected += 1
    assert rejected == 50
