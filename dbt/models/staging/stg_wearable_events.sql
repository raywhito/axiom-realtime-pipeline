-- Staging: clean + de-duplicate raw telemetry (idempotent on event_id).
with src as (
    select
        event_id::text                       as event_id,
        user_id,
        device,
        metric,
        value::numeric                       as value,
        unit,
        event_ts,
        ingested_at,
        row_number() over (
            partition by event_id order by ingested_at
        )                                    as rn
    from {{ source('landing', 'wearable_events') }}
)

select
    event_id,
    user_id,
    device,
    metric,
    value,
    unit,
    event_ts,
    ingested_at
from src
where rn = 1
