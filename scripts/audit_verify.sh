#!/usr/bin/env bash
set -euo pipefail

python3 - << 'PY'
import json, hashlib, sys, os
CHAIN_FILE = "audit_chain.jsonl"

def sha256_json(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",",":")).encode()
    ).hexdigest()

if not os.path.exists(CHAIN_FILE):
    print("[OK] No chain yet (file missing).")
    sys.exit(0)

prev = None
i = 0
with open(CHAIN_FILE, "r") as f:
    for line in f:
        i += 1
        entry = json.loads(line)
        eh = entry.get("entry_hash")
        ph = entry.get("prev_hash")
        payload = dict(entry)
        payload.pop("entry_hash", None)
        recomputed = sha256_json(payload)
        if eh != recomputed:
            print(f"[FAIL] Line {i}: entry_hash mismatch")
            sys.exit(2)
        if ph != prev:
            print(f"[FAIL] Line {i}: prev_hash mismatch (expected {prev}, got {ph})")
            sys.exit(3)
        prev = eh

print("[OK] Chain verified. Head:", prev)
PY
