"""
Consumer — reads the telemetry stream, validates each event against the data
contract (Pydantic), and:
  • valid   -> landing.wearable_events  (Postgres)
  • invalid -> wearable.deadletter topic  +  landing.dead_letter  (Postgres)

Exposes Prometheus metrics so throughput and the valid/invalid ratio are
observable in real time.
"""
from __future__ import annotations

import json
import time

import psycopg2
from confluent_kafka import Consumer, Producer
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from pydantic import ValidationError

import config
from schemas import WearableEvent

CONSUMED = Counter("axiom_events_consumed_total", "Events consumed")
VALID = Counter("axiom_events_valid_total", "Events passing validation")
INVALID = Counter("axiom_events_invalid_total", "Events sent to the DLQ", ["reason"])
PROC = Histogram("axiom_event_processing_seconds", "Per-event processing time")
LANDING_ROWS = Gauge("axiom_landing_rows", "Rows currently in landing.wearable_events")
DLQ_ROWS = Gauge("axiom_dead_letter_rows", "Rows currently in landing.dead_letter")


def connect_db() -> psycopg2.extensions.connection:
    for attempt in range(30):
        try:
            conn = psycopg2.connect(config.DB_DSN)
            conn.autocommit = True
            return conn
        except Exception as exc:  # noqa: BLE001
            print(f"[consumer] waiting for db ({attempt}): {exc}")
            time.sleep(2)
    raise RuntimeError("database never became available")


def refresh_gauges(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM landing.wearable_events")
        LANDING_ROWS.set(cur.fetchone()[0])
        cur.execute("SELECT count(*) FROM landing.dead_letter")
        DLQ_ROWS.set(cur.fetchone()[0])


def main() -> None:
    start_http_server(config.CONSUMER_METRICS_PORT)
    conn = connect_db()
    refresh_gauges(conn)

    consumer = Consumer({
        "bootstrap.servers": config.BROKER,
        "group.id": config.CONSUMER_GROUP,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })
    consumer.subscribe([config.TOPIC])
    dlq = Producer({"bootstrap.servers": config.BROKER})
    print(f"[consumer] <- {config.BROKER} topic={config.TOPIC}")

    processed = 0
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"[consumer] kafka error: {msg.error()}")
            continue

        CONSUMED.inc()
        raw = msg.value().decode("utf-8", errors="replace")
        with PROC.time():
            try:
                event = WearableEvent.model_validate_json(raw)
            except (ValidationError, ValueError) as exc:
                reason = "validation_error"
                INVALID.labels(reason=reason).inc()
                dlq.produce(config.DLQ_TOPIC, value=raw.encode("utf-8"))
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO landing.dead_letter (payload, error) VALUES (%s, %s)",
                        (raw, str(exc)[:500]),
                    )
                continue

            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO landing.wearable_events
                        (event_id, user_id, device, metric, value, unit, event_ts, payload)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (event_id) DO NOTHING
                    """,
                    (str(event.event_id), event.user_id, event.device, event.metric.value,
                     event.value, event.unit, event.event_ts, raw),
                )
            VALID.inc()

        processed += 1
        if processed % 100 == 0:
            refresh_gauges(conn)
            dlq.poll(0)
            print(f"[consumer] processed={processed}")


if __name__ == "__main__":
    main()
