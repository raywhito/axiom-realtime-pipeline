# Demo video script (3–5 min, Loom screencast)

Goal: show a real-time pipeline running end-to-end — ingestion, transformation,
loading, and monitoring / data quality.

## Before recording
```bash
cd axiom-realtime-pipeline
cp .env.example .env
make up           # wait until `make ps` shows all containers up/healthy (~1-2 min)
make topics
```
Open tabs: Grafana (`:3000`), Airflow (`:8085`), Redpanda Console (`:8080`).

---

## 0:00 — Intro (20s)
> "This is the AXIOM real-time pipeline. Wearable telemetry streams through
> Redpanda, gets validated, landed in Postgres, transformed by dbt on an Airflow
> schedule, with data-quality checks and full monitoring."

Show the repo tree (`dags/ python/ dbt/ sql/ tests/`).

## 0:20 — Ingestion (40s)
Open **Redpanda Console → Topics → wearable.telemetry**. Show messages flowing in
live, and the `wearable.deadletter` topic receiving the bad ones.
> "The producer emits ~20 events/sec, about 5% intentionally malformed."

## 1:00 — Transformation + loading (60s)
```bash
make ps           # all services up
make dbt          # dbt run + dbt test
```
> "dbt builds the staging and marts models and runs its data-quality tests —
> not_null, unique, accepted_values, plus a freshness check."

Show a query:
```bash
docker compose -f docker/docker-compose.yml exec postgres \
  psql -U axiom -d axiom -c "select metric, count(*) from analytics.fct_wearable_metric group by 1;"
```

## 2:00 — Automation (40s)
Open **Airflow UI** (`:8085`, admin/admin) → DAG `axiom_realtime_pipeline`.
Show the schedule (`*/5`), the `dbt_run → dbt_test → source_freshness` graph,
and a green run. Trigger it live:
```bash
make trigger
```

## 2:40 — Monitoring & data quality (70s)
Open **Grafana → AXIOM Real-Time Pipeline — Overview**. Point out live:
- Throughput: produced vs consumed
- Data quality: valid vs rejected (DLQ) + valid-ratio gauge
- Dead-letter rows climbing, landing zone growing
- Consumer p95 latency

> "Bad data never silently disappears — it's quarantined in the dead-letter
> queue and visible here in real time."

## 3:50 — Close (20s)
```bash
make test         # green unit tests on the data contract
```
> "Quality is enforced at ingestion and in transformation, the flow is
> orchestrated and scheduled by Airflow, and everything is observable."

---

### Handy commands
| Action | Command |
|---|---|
| Start everything | `make demo` |
| Topics | `make topics` |
| Run dbt now | `make dbt` |
| Trigger DAG | `make trigger` |
| Health probe | `make health` |
| Tear down | `make clean` |
