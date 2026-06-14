-- Fact (event grain): one row per validated wearable reading.
select
    event_id,
    user_id,
    device,
    metric,
    value,
    unit,
    event_ts,
    cast(date_trunc('day', event_ts) as date) as event_date
from {{ ref('stg_wearable_events') }}
