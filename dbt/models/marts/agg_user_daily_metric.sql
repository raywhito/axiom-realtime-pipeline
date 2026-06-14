-- Aggregate (user × day × metric): powers near-real-time readiness trends.
select
    user_id,
    cast(date_trunc('day', event_ts) as date) as event_date,
    metric,
    count(*)      as readings,
    avg(value)    as avg_value,
    min(value)    as min_value,
    max(value)    as max_value
from {{ ref('stg_wearable_events') }}
group by 1, 2, 3
