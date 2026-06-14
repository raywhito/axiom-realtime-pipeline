"""Centralised configuration (read from environment)."""
from __future__ import annotations

import os

# Redpanda / Kafka
BROKER = os.getenv("REDPANDA_BROKER", "redpanda:9092")
TOPIC = os.getenv("TOPIC", "wearable.telemetry")
DLQ_TOPIC = os.getenv("DLQ_TOPIC", "wearable.deadletter")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "axiom-consumer")

# Postgres (landing + warehouse)
PG_HOST = os.getenv("PG_HOST", "postgres")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB = os.getenv("PG_DB", "axiom")
PG_USER = os.getenv("PG_USER", "axiom")
PG_PASSWORD = os.getenv("PG_PASSWORD", "axiom")

DB_DSN = f"host={PG_HOST} port={PG_PORT} dbname={PG_DB} user={PG_USER} password={PG_PASSWORD}"

# Producer
TARGET_EPS = float(os.getenv("TARGET_EPS", "20"))          # events per second
INVALID_RATE = float(os.getenv("INVALID_RATE", "0.05"))    # share of intentionally bad events

# Prometheus exporter ports
PRODUCER_METRICS_PORT = int(os.getenv("PRODUCER_METRICS_PORT", "8001"))
CONSUMER_METRICS_PORT = int(os.getenv("CONSUMER_METRICS_PORT", "8002"))
