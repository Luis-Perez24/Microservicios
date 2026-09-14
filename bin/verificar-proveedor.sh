#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

export PACT_STATES_ENABLED=1
BASE_URL="http://127.0.0.1:8001"
PID=""

cleanup() {
  if [ -n "$PID" ]; then
    kill "$PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

echo "Levantando el Servicio de Reservas en $BASE_URL..."
.venv/bin/uvicorn services.reservas.app.main:app --host 127.0.0.1 --port 8001 &
PID=$!

for _ in $(seq 1 30); do
  if curl -sf "$BASE_URL/docs" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -sf "$BASE_URL/docs" >/dev/null 2>&1; then
  echo "El proveedor no respondio en $BASE_URL" >&2
  exit 1
fi

echo "Proveedor listo. Corriendo la verificacion de contratos..."
.venv/bin/pytest tests/provider -m proveedor -q