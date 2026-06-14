-- ════════════════════════════════════════════════════════════════════════════
-- AXIOM Real-Time Pipeline — landing (raw) schema
-- Executed by the Postgres container on first boot.
-- The consumer writes validated events here; dbt reads from it downstream.
-- ════════════════════════════════════════════════════════════════════════════

CREATE SCHEMA IF NOT EXISTS landing;

-- Validated wearable telemetry events (raw, append-only)
CREATE TABLE IF NOT EXISTS landing.wearable_events (
    event_id     UUID PRIMARY KEY,
    user_id      TEXT        NOT NULL,
    device       TEXT        NOT NULL,
    metric       TEXT        NOT NULL,
    value        NUMERIC(12, 4) NOT NULL,
    unit         TEXT,
    event_ts     TIMESTAMPTZ NOT NULL,
    ingested_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload      JSONB
);

CREATE INDEX IF NOT EXISTS idx_wearable_event_ts ON landing.wearable_events (event_ts);
CREATE INDEX IF NOT EXISTS idx_wearable_metric   ON landing.wearable_events (metric);

-- Dead-letter store: events that failed schema/quality validation
CREATE TABLE IF NOT EXISTS landing.dead_letter (
    id           BIGSERIAL PRIMARY KEY,
    payload      JSONB,
    error        TEXT,
    ingested_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- dbt builds its models into this schema
CREATE SCHEMA IF NOT EXISTS analytics;

COMMENT ON SCHEMA landing IS 'Raw landing zone for the real-time pipeline';
COMMENT ON TABLE  landing.wearable_events IS 'Validated wearable telemetry (consumer output)';
COMMENT ON TABLE  landing.dead_letter     IS 'Events rejected by ingestion validation (DLQ mirror)';
