# AXIOM Real-Time Pipeline — Block 3

A complete, automated and monitored **real-time data pipeline** for the AXIOM
preventive-health platform. It streams continuous **wearable telemetry**
(HRV, resting HR, sleep, steps, SpO₂) through Redpanda, validates every event,
lands it in PostgreSQL, transforms it with dbt on an Airflow schedule, enforces
data quality with dbt tests + a dead-letter queue, and exposes the whole flow in
Prometheus + Grafana.

> Fictional project for the Block 3 "Real-Time Data Pipelines" assessment.
> Extends the AXIOM data platform (Block 2) with a streaming layer.

---

## 1. Pipeline architecture

```
 Producer (Python)                Redpanda (Kafka API)            Consumer (Python)
 wearable telemetry  ──produce──▶  topic: wearable.telemetry ──▶  validate (Pydantic)
 (+ ~5% bad events)                                                │
                                                       valid ──────┼─────▶ Postgres  landing.wearable_events
                                                       invalid ────┘  ┌──▶ topic: wearable.deadletter
                                                                      └──▶ Postgres landing.dead_letter
                                                                                  │
                                   Airflow DAG (every 5 min, retries) ────────────┘
                                       dbt run ▶ dbt test ▶ source freshness
                                                   │
                                       analytics.stg_* / fct_* / agg_*  (star-style marts)
                                                   │
   Observability:  Prometheus ◀ producer · consumer · Redpanda     Grafana dashboards
                   Airflow UI (orchestration)      Redpanda Console (topics/lag)
```

Diagrams: [`docs/architecture.png`](docs/architecture.png),
[`docs/pipeline_flow.png`](docs/pipeline_flow.png).

---

## 2. Repository structure

```
axiom-realtime-pipeline/
├── dags/        # Airflow DAG (orchestration & scheduling)
├── python/      # producer, consumer, Pydantic schemas, config
├── dbt/         # dbt project: staging + marts models, tests
├── sql/         # landing-zone schema (auto-applied on Postgres boot)
├── tests/       # pytest unit tests (data-contract / DQ)
├── docker/      # docker-compose + Dockerfiles + Prometheus/Grafana
├── scripts/     # healthcheck
├── docs/        # diagrams + demo script
├── Makefile
└── README.md
```

---

## 3. Data flow (ingestion → transformation → loading → monitoring)

1. **Ingestion** — `producer.py` emits telemetry to Redpanda at a configurable rate
   (`TARGET_EPS`), deliberately injecting ~5% malformed events.
2. **Validation** — `consumer.py` validates every message against the `WearableEvent`
   Pydantic contract.
3. **Loading** — valid events → `landing.wearable_events`; invalid events → the
   `wearable.deadletter` topic **and** `landing.dead_letter` (full audit trail).
4. **Transformation** — Airflow runs dbt every 5 minutes: `staging` (clean/dedupe)
   → `marts` (`fct_wearable_metric`, `agg_user_daily_metric`).
5. **Monitoring** — Prometheus scrapes producer/consumer/Redpanda; Grafana shows
   throughput, valid/rejected ratio, DLQ, latency; Airflow UI shows DAG runs.

---

## 4. Technologies & justification

| Concern | Choice | Why |
|---|---|---|
| Streaming | **Redpanda** | Kafka-compatible, single binary, no Zookeeper — light to run/demo |
| Ingestion | **Python + confluent-kafka** | High-performance Kafka client; Pydantic for the data contract |
| Storage | **PostgreSQL 16** | Landing zone + analytics marts + Airflow metadata in one engine |
| Transformation | **dbt (dbt-postgres)** | Versioned SQL models, lineage, built-in tests |
| Orchestration | **Airflow** | Scheduling, retries, dependencies, observable DAG runs |
| Monitoring | **Prometheus + Grafana** | Real-time metrics + dashboards |
| Quality gate | **Pydantic + DLQ + dbt tests** | Defence in depth: at ingestion *and* in transformation |

---

## 5. Automation

- **Airflow DAG** `axiom_realtime_pipeline` runs `dbt run → dbt test → source freshness`
  on a `*/5 * * * *` schedule, with `retries=2` and a 2-minute retry delay.
- Streaming services (`producer`, `consumer`) run continuously with
  `restart: unless-stopped`.

## 6. Data-quality control & error handling

- **Contract validation** at ingestion (Pydantic): type, enum, and physiological
  range checks per metric.
- **Dead-letter queue** — rejected events are never dropped silently; they go to a
  topic *and* an auditable table with the error reason.
- **dbt tests** — `not_null`, `unique`, `accepted_values`, a custom singular test,
  and **source freshness** checks.
- **Idempotency** — `ON CONFLICT DO NOTHING` on `event_id` + dedupe in staging.

## 7. Monitoring & observability

| Surface | URL | Shows |
|---|---|---|
| Grafana | http://localhost:3000 | throughput, valid/rejected, DLQ, p95 latency |
| Airflow | http://localhost:8085 | DAG runs, task status, retries |
| Redpanda Console | http://localhost:8080 | topics, partitions, consumer lag |
| Prometheus | http://localhost:9090 | raw metrics & targets |

---

## 8. Quickstart (local — zero cost)

Prerequisites: **Docker Desktop**. Allocate ~6–8 GB RAM to Docker (Airflow + Redpanda).

> Run only one AXIOM stack at a time — this pipeline reuses ports 3000 / 9090 / 8080,
> so stop the Block 2 stack first (`make clean` there) to avoid port clashes.

```bash
cd axiom-realtime-pipeline
cp .env.example .env
make demo        # build, start, create topics, run dbt, trigger the DAG
```

Credentials: Grafana & Airflow are both `admin` / `admin`.

Step-by-step:
```bash
make up        # start the stack
make topics    # create Kafka topics
make health    # probe endpoints
make dbt       # run dbt models + tests
make trigger   # unpause & trigger the Airflow DAG
make test      # run the Python unit tests
make clean     # tear down + wipe volumes
```

---

## 9. Tests

```bash
make test      # containerised pytest (data-contract & DLQ logic)
```

dbt tests run inside the pipeline (`make dbt`) and on every Airflow schedule.
