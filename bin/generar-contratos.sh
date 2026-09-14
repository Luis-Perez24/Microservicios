#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Generando contratos en ./pacts desde los tests de consumidores..."
.venv/bin/pytest tests/consumers -q

echo ""
echo "Contratos generados:"
ls -1 pacts/*.json 2>/dev/null || echo "(no hay pacts generados)"