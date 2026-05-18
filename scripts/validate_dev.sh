#!/usr/bin/env bash
# Dev validation for agents and humans. No camera, Docker, or iMessage required.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .venv/bin/activate ]]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi

echo "==> Python compile (scripts/)"
python3 -m py_compile scripts/*.py

echo "==> Snapshot ingest (MOCK_MODE)"
export MOCK_MODE=true
export SNAPSHOT_URL=
python3 scripts/test_snapshot_url.py

echo "==> Lawn alert one tick (MOCK + dry-run)"
export IMESSAGE_DRY_RUN=true
export IMESSAGE_TARGET=${IMESSAGE_TARGET:-+10000000000}
python3 scripts/lawn_alert.py --once

echo "==> OK: validate_dev.sh passed"
