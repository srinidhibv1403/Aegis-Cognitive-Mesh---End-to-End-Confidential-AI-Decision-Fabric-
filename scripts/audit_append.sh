#!/usr/bin/env bash
set -euo pipefail

latest=$(ls -t artifacts/lineage_*.json 2>/dev/null | head -n 1 || true)
if [[ -z "${latest:-}" ]]; then
  echo "No lineage files found in artifacts/. Run make lineage-example first."
  exit 1
fi

echo "Appending $latest"
./scripts/append_audit.py "$latest"
