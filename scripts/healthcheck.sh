#!/usr/bin/env bash
# Quick health probe for the AXIOM real-time pipeline (run from the host).
set -uo pipefail

check() {
  local name="$1" url="$2"
  if curl -fsS -o /dev/null --max-time 5 "$url"; then
    printf "  OK   %-22s %s\n" "$name" "$url"
  else
    printf "  DOWN %-22s %s\n" "$name" "$url"
  fi
}

echo "AXIOM Real-Time Pipeline — health check"
check "Producer metrics"  "http://localhost:8001/metrics"
check "Consumer metrics"  "http://localhost:8002/metrics"
check "Redpanda metrics"  "http://localhost:9644/public_metrics"
check "Redpanda Console"  "http://localhost:8080"
check "Airflow UI"        "http://localhost:8085/health"
check "Prometheus"        "http://localhost:9090/-/healthy"
check "Grafana"           "http://localhost:3000/api/health"
echo "Done."
