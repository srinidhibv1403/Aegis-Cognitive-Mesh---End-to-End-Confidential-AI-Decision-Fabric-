#!/usr/bin/env bash
set -euo pipefail

echo "[Day13] Seeding disruption..."
python scripts/seed_disruption.py

echo "[Day13] Generating plans..."
python scripts/generate_plans.py

echo "[Day13] Verifying policies..."
python scripts/verify_policies.py | tee /tmp/day13_verify.json

echo "[Day13] Simulating twin locally..."
python scripts/simulate_twin.py

echo "[Day13] Writing proof entry..."
python scripts/write_proof.py

echo "[Day13] Optional ADT touch..."
python scripts/adt_touch.py || true

echo "[Day13] Creating run summary..."
python scripts/run_summary.py

echo "[Day13] SUCCESS"
