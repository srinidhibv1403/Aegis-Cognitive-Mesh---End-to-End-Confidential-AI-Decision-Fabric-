#!/usr/bin/env bash
set -euo pipefail
N="${1:-5}"
tail -n "$N" audit_chain.jsonl | python3 - << 'PY'
import json, sys
for i, line in enumerate(sys.stdin, 1):
    e = json.loads(line)
    print(f"{i}. entry_hash={e.get('entry_hash')[:16]} prev={str(e.get('prev_hash'))[:16]} plan={e.get('lineage',{}).get('plan_id')} status={e.get('lineage',{}).get('verify_status')}")
PY
