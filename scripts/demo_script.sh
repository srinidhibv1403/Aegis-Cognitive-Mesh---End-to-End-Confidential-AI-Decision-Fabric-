#!/usr/bin/env bash
set -euo pipefail

echo "=== ACM: 3-minute Demo ==="

echo "[1/6] Demo Up"
./scripts/demo_up.sh

echo "[2/6] Gate + Approved Runbook"
PYTHONPATH=. ./scripts/runbook_resilient.py "acm-demo-ephemeral" audits/day15_token.jwt

echo "[3/6] Proof Viewer (CLI, last 5)"
python3 scripts/proof_viewer.py 5 || true

echo "[4/6] HTML Proof Generation"
python3 scripts/proof_viewer_html.py 10

echo "[5/6] Show HTML location"
echo "Open: audits/proof_view.html"

echo "[6/6] Demo Down (to keep costs ≈0)"
./scripts/demo_down.sh

echo "=== Done ==="
