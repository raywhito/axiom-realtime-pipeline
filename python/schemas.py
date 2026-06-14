"""
Pydantic schema for a wearable telemetry event — the data contract enforced at
ingestion. Anything that fails validation is routed to the dead-letter queue.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

# Plausible physiological ranges per metric — first line of data-quality defence.
METRIC_RANGES: dict[str, tuple[float, float, str]] = {
    "hrv":        (5.0, 250.0, "ms"),     # heart-rate variability
    "resting_hr": (30.0, 120.0, "bpm"),   # resting heart rate
    "sleep_hours": (0.0, 16.0, "h"),
    "steps":      (0.0, 60000.0, "count"),
    "spo2":       (70.0, 100.0, "%"),     # blood oxygen saturation
}

VALID_DEVICES = {"oura", "apple_watch", "whoop"}


class Metric(str, Enum):
    hrv = "hrv"
    resting_hr = "resting_hr"
    sleep_hours = "sleep_hours"
    steps = "steps"
    spo2 = "spo2"


class WearableEvent(BaseModel):
    """One telemetry reading from a wearable device."""

    event_id: str = Field(..., min_length=8)
    user_id: str = Field(..., min_length=3)
    device: str
    metric: Metric
    value: float
    unit: str
    event_ts: datetime

    @field_validator("device")
    @classmethod
    def _device_known(cls, v: str) -> str:
        if v not in VALID_DEVICES:
            raise ValueError(f"unknown device '{v}'")
        return v

    @field_validator("value")
    @classmethod
    def _value_in_range(cls, v: float, info) -> float:
        metric = info.data.get("metric")
        if metric is not None:
            lo, hi, _ = METRIC_RANGES[metric.value]
            if not (lo <= v <= hi):
                raise ValueError(f"{metric.value}={v} out of plausible range [{lo}, {hi}]")
        return v
