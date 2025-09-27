#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

AUDIT_FILES = [
    Path("audits/chain.log"),
    Path("audit_chain.jsonl"),
]

CORE_FIELDS = [
    "timestamp",
    "attestation_type",
    "policy_hash",
    "verdict",
    "released",
    "secret_name",
    "token_digest",
    "notes",
]

def load_audit_lines() -> List[Dict[str, Any]]:
    src = None
    for p in AUDIT_FILES:
        if p.exists():
            src = p
            break
    if not src:
        print("No audit log found (looked for audits/chain.log and audit_chain.jsonl)", file=sys.stderr)
        sys.exit(1)

    records = []
    with src.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
                records.append(obj)
            except Exception:
                # Tolerate non-JSON lines
                continue
    return records

def coalesce(record: Dict[str, Any]) -> Dict[str, Any]:
    flat = {}

    # Common top-levels
    for k in ["timestamp", "policy_hash", "verdict", "released", "secret_name", "notes", "token_digest"]:
        if k in record:
            flat[k] = record[k]

    # Nested audit section
    audit = record.get("audit") or {}
    if isinstance(audit, dict):
        if "attestation_type" in audit:
            flat["attestation_type"] = audit["attestation_type"]
        # If claims exist, allow fallback from claim
        if "claims" in audit and isinstance(audit["claims"], dict):
            flat.setdefault("attestation_type", audit["claims"].get("x-ms-attestation-type"))

    flat.setdefault("attestation_type", record.get("attestation_type", "unknown"))
    flat.setdefault("released", record.get("released", None))
    flat.setdefault("secret_name", record.get("secret_name", None))

    return flat

def print_entry(entry: Dict[str, Any], idx: int):
    print(f"# Entry {idx}")
    for k in CORE_FIELDS:
        if k in entry and entry[k] is not None:
            print(f"- {k}: {entry[k]}")
    extras = {k: v for k, v in entry.items() if k not in CORE_FIELDS}
    if extras:
        print("- extra:", json.dumps(extras, ensure_ascii=False))
    print()

def main():
    n = 5
    if len(sys.argv) >= 2:
        try:
            n = max(1, int(sys.argv[1]))
        except Exception:
            pass

    records = load_audit_lines()
    if not records:
        print("No JSON records found in audit log.")
        sys.exit(0)

    last = records[-n:]
    for i, rec in enumerate(reversed(last), 1):
        flat = coalesce(rec)
        print_entry(flat, i)

if __name__ == "__main__":
    main()
