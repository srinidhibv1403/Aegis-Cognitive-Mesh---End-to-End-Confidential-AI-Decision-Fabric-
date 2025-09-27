#!/usr/bin/env bash
set -euo pipefail

OUT="audits/snp_token.jwt"

need() { command -v "$1" >/dev/null 2>&1 || { echo "[error] Missing dependency: $1"; exit 2; }; }
need curl
need jq
need base64

# Detect SNP environment
SNP_DEV="/dev/sev-guest"
if [[ ! -e "$SNP_DEV" ]]; then
  echo "[error] Not a SEV-SNP environment: ${SNP_DEV} not found."
  echo "[hint] Run this script inside an Azure Confidential VM (SEV-SNP)."
  exit 3
fi

# Create a temporary workdir
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1) Request an SNP report from the guest device
get_report() {
  if command -v az-snp-report >/dev/null 2>&1; then
    az-snp-report > "$TMP/report.bin"
    return
  fi
  if command -v snpguest-report >/dev/null 2>&1; then
    snpguest-report > "$TMP/report.bin"
    return
  fi
  if command -v sev-tool >/dev/null 2>&1; then
    sev-tool --of "$TMP/report.bin" --platform_status || true
  fi
  echo "[error] Could not obtain SNP report. Install one of: az-snp-report or snpguest-report."
  echo "[hint] On Azure SNP VM: sudo apt-get update && sudo apt-get install -y azguestattestation || sudo rpm -q azguestattestation"
  exit 4
}

echo "[info] Fetching SNP report from guest device..."
get_report
if [[ ! -s "$TMP/report.bin" ]]; then
  echo "[error] Empty SNP report."
  exit 5
fi

# 2) Base64url-encode the raw report for MAA
REPORT_B64URL="$(base64 -w0 "$TMP/report.bin" | tr '+/' '-_' | tr -d '=')"

# 3) Exchange the report at MAA for a JWT
ATTEST_URL="${MAA_URL%/}/attest/SnpVm?api-version=2023-04-01"
echo "[info] Exchanging report with MAA: ${ATTEST_URL}"

BODY="$(jq -n --arg evidence "$REPORT_B64URL" '{ report: $evidence }')"

RESP="$(curl -sS -X POST \
  -H "Content-Type: application/json" \
  -d "$BODY" \
  "$ATTEST_URL")" || { echo "[error] MAA request failed"; exit 6; }

TOKEN="$(echo "$RESP" | jq -r '.token // empty')"
if [[ -z "$TOKEN" ]]; then
  echo "[error] MAA did not return a token:"
  echo "$RESP"
  exit 7
fi

# 4) Save token
printf "%s" "$TOKEN" > "$OUT"
echo "[ok] Saved JWT to $OUT"
