# AXIOM Real-Time Pipeline — convenience targets
# Requires Docker Desktop (Docker Engine + Compose plugin).

COMPOSE = docker compose -f docker/docker-compose.yml

.PHONY: help up down clean ps logs topics test dbt unpause trigger health demo

help:
	@echo "Targets:"
	@echo "  make up       - build & start the full stack"
	@echo "  make topics   - create the Kafka topics (idempotent)"
	@echo "  make dbt      - run dbt models + tests now"
	@echo "  make trigger  - unpause & trigger the Airflow DAG"
	@echo "  make demo     - up + topics + dbt + trigger (one-shot)"
	@echo "  make test     - run the Python unit tests (containerised)"
	@echo "  make health   - probe all endpoints"
	@echo "  make logs     - follow logs"
	@echo "  make down     - stop the stack    |    make clean - stop & wipe volumes"

up:
	$(COMPOSE) up -d --build
	@echo "Redpanda Console http://localhost:8080"
	@echo "Airflow UI       http://localhost:8085  (admin/admin)"
	@echo "Grafana          http://localhost:3000  (admin/admin)"
	@echo "Prometheus       http://localhost:9090"

down:
	$(COMPOSE) down

clean:
	$(COMPOSE) down -v

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f

topics:
	$(COMPOSE) exec -T redpanda rpk topic create wearable.telemetry wearable.deadletter -p 1 -r 1 || true
	$(COMPOSE) exec -T redpanda rpk topic list

dbt:
	$(COMPOSE) exec -T airflow bash -c "cd /opt/airflow/dbt && dbt run --profiles-dir . --project-dir . && dbt test --profiles-dir . --project-dir ."

unpause:
	$(COMPOSE) exec -T airflow airflow dags unpause axiom_realtime_pipeline

trigger: unpause
	$(COMPOSE) exec -T airflow airflow dags trigger axiom_realtime_pipeline

test:
	docker run --rm -v "$(PWD)":/w -w /w python:3.12-slim \
		bash -c "pip install -q -r python/requirements.txt pytest && pytest -q tests"

health:
	bash scripts/healthcheck.sh

demo: up
	@echo "Waiting for services to come up..."
	@sleep 40
	$(MAKE) topics
	@echo "Letting the stream fill the landing zone..."
	@sleep 20
	$(MAKE) dbt
	$(MAKE) trigger
	@echo ""
	@echo "Demo ready:"
	@echo "  Grafana          http://localhost:3000"
	@echo "  Airflow UI       http://localhost:8085"
	@echo "  Redpanda Console http://localhost:8080"
