#!/usr/bin/env bash
set -euo pipefail
RG="${RG_NAME:-acm-aca-rg}"
APP="${ACA_APP:-acm-hello}"

echo "[info] Scaling $APP to 0 in $RG ..."
az containerapp update -g "$RG" -n "$APP" \
  --set properties.template.scale.minReplicas=0 >/dev/null
echo "[ok] Min replicas set to 0."

echo "[info] Disabling traffic to latest revision ..."
az containerapp ingress traffic set -g "$RG" -n "$APP" \
  --revision-weight latest=0 >/dev/null || true
echo "[ok] Traffic weight set to 0."

echo "[done] Stop-all complete."
