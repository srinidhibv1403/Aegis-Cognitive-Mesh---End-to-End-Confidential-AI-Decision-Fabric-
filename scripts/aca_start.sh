#!/usr/bin/env bash
set -euo pipefail
RG="${RG_NAME:-acm-aca-rg}"
APP="${ACA_APP:-acm-hello}"

# Ensure minReplicas allows a warm pod
az containerapp update -g "$RG" -n "$APP" \
  --set properties.template.scale.minReplicas=1 >/dev/null

# Get URL and trigger a wake
URL="$(az containerapp show -g "$RG" -n "$APP" --query properties.configuration.ingress.fqdn -o tsv)"
echo "[info] App URL: https://$URL/"
echo "[info] Warming..."
curl -sS "https://$URL/" | head -c 200 || true
echo

# Return to scale-to-zero default
az containerapp update -g "$RG" -n "$APP" \
  --set properties.template.scale.minReplicas=0 >/dev/null
echo "[done] Start helper finished (returned to minReplicas=0)."

