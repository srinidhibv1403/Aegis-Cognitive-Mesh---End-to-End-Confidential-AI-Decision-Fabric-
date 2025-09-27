#!/usr/bin/env bash
set -euo pipefail

POLICY_FILE="policies/base.yaml"
LOCK_FILE="policies/policy.lock"

# Only run if policy exists in repo
[ -f "$POLICY_FILE" ] || exit 0

# Detect if the policy file is staged or has changes
if ! git diff --quiet --cached -- "$POLICY_FILE"; then
  :
elif ! git diff --quiet -- "$POLICY_FILE"; then
  :
else
  # Policy not changed; no check needed
  exit 0
fi

# Compute fresh hash using the project script
HASH=$(python3 scripts/hash_policy.py 2>/dev/null || true)
if [ -z "$HASH" ]; then
  echo "policy-lock-check: Unable to compute hash. Ensure scripts/hash_policy.py works."
  exit 1
fi

# Extract hash from lock file
if [ ! -f "$LOCK_FILE" ]; then
  echo "policy-lock-check: $LOCK_FILE missing. Run scripts/hash_policy.py and update the lock."
  exit 1
fi

LOCK_HASH=$(awk -F': ' '/policy_sha256/{print $2}' "$LOCK_FILE" | tr -d '[:space:]')

if [ "$HASH" != "$LOCK_HASH" ]; then
  echo "policy-lock-check: Hash mismatch."
  echo "  Expected (recompute): $HASH"
  echo "  In lock file:         $LOCK_HASH"
  echo "Please update $LOCK_FILE:"
  echo "  printf \"policy_sha256: $HASH\\n\" > $LOCK_FILE"
  echo "Then re-stage and commit."
  exit 1
fi

exit 0
