#!/usr/bin/env bash
set -euo pipefail

echo "[info] Cost/Free-tier quick checklist"
echo "- Attestation: free (design-time); keep usage within documented limits."
echo "- Digital Twins: keep graph tiny; batch queries; run during short demo windows."
echo "- Compute: use scale-to-zero or short-lived windows; deallocate after demo."
echo "- Budget/alerts: verify Azure Cost Management budget + alerts (portal)."
echo "- Proof-first posture: keep attestation/gate local until needed; avoid idle cloud."
echo "[ok] Cost hygiene checklist surfaced."
