-- Singular data test: every aggregated bucket must contain at least one reading.
-- Returns failing rows (none expected); `dbt test` fails if any are found.
select
    user_id,
    event_date,
    metric,
    readings
from {{ ref('agg_user_daily_metric') }}
where readings <= 0
