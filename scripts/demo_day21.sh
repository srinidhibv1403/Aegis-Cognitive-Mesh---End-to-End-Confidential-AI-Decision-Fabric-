#!/usr/bin/env bash
set -euo pipefail

payload='{"policy":{"budget_cap":10000,"sla_min":96,"allow_cross_region":false,"max_delay_minutes":60},"plan":{"route":"R7","added_cost":12000,"expected_delay_minutes":85,"data_region":"US","pii_used":true},"max_attempts":6}'

echo "[info] Running Day 21 auto-revision demo..."
out="$(PYTHONPATH=. python3 scripts/auto_revise.py "$payload")"
echo "$out" | jq -C . || echo "$out"

# Append a short audit note for traceability
mkdir -p audits
ts="$(date -u +%FT%TZ)"
echo "$ts day21 auto-revise demo executed" >> audits/day21_note.log

echo "[done] Day 21 demo complete."
