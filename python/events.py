"""
Event generation helpers — pure (no Kafka / DB dependency) so they can be
unit-tested in isolation. Used by the producer.
"""
from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone

from schemas import METRIC_RANGES, VALID_DEVICES

USERS = [f"anon_{i:04d}" for i in range(50)]
METRICS = list(METRIC_RANGES.keys())
DEVICES = list(VALID_DEVICES)


def make_valid_event() -> tuple[dict, str]:
    """Return a (payload, metric) tuple that satisfies the data contract."""
    metric = random.choice(METRICS)
    lo, hi, unit = METRIC_RANGES[metric]
    return {
        "event_id": str(uuid.uuid4()),
        "user_id": random.choice(USERS),
        "device": random.choice(DEVICES),
        "metric": metric,
        "value": round(random.uniform(lo, hi), 3),
        "unit": unit,
        "event_ts": datetime.now(timezone.utc).isoformat(),
    }, metric


def make_invalid_event() -> tuple[dict, str]:
    """Return a deliberately broken event to exercise the dead-letter queue."""
    event, metric = make_valid_event()
    kind = random.choice(["out_of_range", "unknown_device", "missing_field", "bad_timestamp"])
    if kind == "out_of_range":
        event["value"] = METRIC_RANGES[metric][1] * 10
    elif kind == "unknown_device":
        event["device"] = "counterfeit_band"
    elif kind == "missing_field":
        event.pop("value", None)
    elif kind == "bad_timestamp":
        event["event_ts"] = "not-a-timestamp"
    return event, metric
