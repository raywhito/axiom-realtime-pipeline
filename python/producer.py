"""
Producer — simulates a real-time wearable-telemetry stream into Redpanda.

A configurable share of events is intentionally malformed (out-of-range values,
unknown devices, missing fields, bad timestamps) so the consumer's data-quality
controls and dead-letter queue can be demonstrated end to end.
"""
from __future__ import annotations

import json
import random
import time

from confluent_kafka import Producer
from prometheus_client import Counter, Gauge, start_http_server

import config
from events import make_invalid_event, make_valid_event

PRODUCED = Counter("axiom_events_produced_total", "Events produced", ["metric", "kind"])
TARGET = Gauge("axiom_producer_target_eps", "Target events per second")


def main() -> None:
    producer = Producer({"bootstrap.servers": config.BROKER, "linger.ms": 50})
    start_http_server(config.PRODUCER_METRICS_PORT)
    TARGET.set(config.TARGET_EPS)
    interval = 1.0 / config.TARGET_EPS if config.TARGET_EPS > 0 else 0.05
    print(f"[producer] -> {config.BROKER} topic={config.TOPIC} eps={config.TARGET_EPS}")

    sent = 0
    while True:
        if random.random() < config.INVALID_RATE:
            event, metric = make_invalid_event()
            kind = "invalid"
        else:
            event, metric = make_valid_event()
            kind = "valid"
        producer.produce(
            config.TOPIC,
            key=event.get("user_id", "unknown"),
            value=json.dumps(event).encode("utf-8"),
        )
        PRODUCED.labels(metric=metric, kind=kind).inc()
        sent += 1
        if sent % 200 == 0:
            producer.flush(5)
            print(f"[producer] sent={sent}")
        producer.poll(0)
        time.sleep(interval)


if __name__ == "__main__":
    main()
