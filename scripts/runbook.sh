#!/usr/bin/env bash
set -euo pipefail

# Config
SECRET_NAME="${1:-acm-demo-ephemeral}"
JWT_FILE="${2:-audits/day15_token.jwt}"
POLICY_MODE="${ACM_POLICY:-simulated}"  # simulated|sevsnp

mkdir -p audits

# 1) Call the gate and capture two JSON lines (audit + release)
OUT="$(PYTHONPATH=. scripts/attested_get_secret.py "$SECRET_NAME" "$JWT_FILE")" || true
echo "$OUT"

# Parse fields with jq
ATT_TYPE="$(echo "$OUT" | sed -n '1p' | jq -r '.audit.attestation_type // "unknown"')"
RELEASED="$(echo "$OUT" | sed -n '2p' | jq -r '.released // false')"
VALUE="$(echo "$OUT" | sed -n '2p' | jq -r '.value // empty')"

# 2) Fail closed if not released
if [[ "$RELEASED" != "true" ]]; then
  echo "[deny] Runbook blocked: secret not released."
  exit 3
fi

# 3) Minimal approved action (placeholder)
ACTION="approved_action"
ACTION_RESULT="ok"
echo "[ok] Approved action executed."

# 4) Hash-chained audit entry (robust append)
# 4) Hash-chained audit entry (compact, one line per entry)
CHAIN_FILE="audits/chain.log"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
mkdir -p "$(dirname "$CHAIN_FILE")"

# Read previous hash safely (only if last line is valid JSON)
if [[ -s "$CHAIN_FILE" ]]; then
  LAST="$(tail -n 1 "$CHAIN_FILE" || true)"
  if echo "$LAST" | jq -e . >/dev/null 2>&1; then
    PREV_HASH="$(echo "$LAST" | jq -r '.hash // empty')"
  else
    PREV_HASH=""
  fi
else
  PREV_HASH=""
fi

# Build entry without hash
ENTRY="$(jq -n \
  --arg ts "$TS" \
  --arg policy "$POLICY_MODE" \
  --arg att "$ATT_TYPE" \
  --arg released "$RELEASED" \
  --arg action "$ACTION" \
  --arg result "$ACTION_RESULT" \
  --arg prev "$PREV_HASH" \
  '{
    ts:$ts,
    policy_mode:$policy,
    attestation_type:$att,
    released:($released=="true"),
    action:$action,
    result:$result
  } + ( $prev|length>0 | if . then {prev_hash:$prev} else {} end )' \
)"

# Compute hash over the canonical compact JSON
CANON="$(printf "%s" "$ENTRY" | jq -c '.')"
HASH="$(printf "%s" "$CANON" | sha256sum | awk '{print $1}')"
FINAL="$(echo "$CANON" | jq -c --arg h "$HASH" '. + {hash:$h}')"

# Append exactly one compact JSON line with newline
printf "%s\n" "$FINAL" >> "$CHAIN_FILE"
echo "[ok] Audit appended to $CHAIN_FILE"

