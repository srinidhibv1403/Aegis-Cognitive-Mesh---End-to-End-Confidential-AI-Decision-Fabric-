#!/usr/bin/env bash
set -euo pipefail

# Validate prerequisites
if [ ! -f "audits/day15_token.jwt" ]; then
  echo "[error] Missing audits/day15_token.jwt"
  exit 1
fi

# Generate/refresh proof HTML (best-effort)
if [ -f "scripts/proof_viewer_html.py" ]; then
  echo "[info] Generating proof_view.html (last 10 entries)"
  python3 scripts/proof_viewer_html.py 10 >/dev/null || true
fi

echo "[ok] Demo Up ready. Proof HTML at audits/proof_view.html (if generated)"
