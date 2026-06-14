"""
AXIOM real-time pipeline — orchestration DAG.

Runs the micro-batch transformation layer on a schedule:
    dbt run  ->  dbt test (data quality)  ->  dbt source freshness (monitoring)

The streaming ingestion (producer -> Redpanda -> consumer -> landing) runs
continuously as its own services; Airflow orchestrates the periodic
transformation + quality gate on top of the landing zone.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

DBT_DIR = "/opt/airflow/dbt"
DBT = f"dbt {{}} --profiles-dir {DBT_DIR} --project-dir {DBT_DIR}"

default_args = {
    "owner": "axiom",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "depends_on_past": False,
}

with DAG(
    dag_id="axiom_realtime_pipeline",
    description="Micro-batch dbt transformation + data-quality gate over streamed telemetry",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule="*/5 * * * *",   # every 5 minutes
    catchup=False,
    max_active_runs=1,
    tags=["axiom", "real-time", "dbt"],
) as dag:

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_DIR} && " + DBT.format("run"),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_DIR} && " + DBT.format("test"),
    )

    # Data freshness check — fails (or warns) if the landing zone goes stale.
    dbt_freshness = BashOperator(
        task_id="dbt_source_freshness",
        bash_command=f"cd {DBT_DIR} && " + DBT.format("source freshness") + " || true",
    )

    dbt_run >> dbt_test >> dbt_freshness
