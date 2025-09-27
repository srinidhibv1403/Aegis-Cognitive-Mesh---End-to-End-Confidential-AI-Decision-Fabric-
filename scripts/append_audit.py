#!/usr/bin/env python3
import json, sys, os, hashlib, time

CHAIN_FILE = "audit_chain.jsonl"
HEAD_FILE = "artifacts/chain_head.json"

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_json(obj) -> str:
    data = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(data)

def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def read_head():
    if not os.path.exists(HEAD_FILE):
        return {"head": None}
    with open(HEAD_FILE, "r") as f:
        return json.load(f)

def write_head(head_hash: str):
    os.makedirs(os.path.dirname(HEAD_FILE), exist_ok=True)
    with open(HEAD_FILE, "w") as f:
        json.dump({"head": head_hash, "updated_at": now_iso()}, f, indent=2)

def append_line(line: str):
    with open(CHAIN_FILE, "a") as f:
        f.write(line)
        if not line.endswith("\n"):
            f.write("\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: append_audit.py <lineage_file>")
        sys.exit(1)

    lineage_path = sys.argv[1]
    if not os.path.exists(lineage_path):
        print(f"Missing lineage file: {lineage_path}")
        sys.exit(1)

    with open(lineage_path, "r") as f:
        lineage = json.load(f)

    head = read_head().get("head")
    entry = {
        "timestamp": now_iso(),
        "prev_hash": head,
        "lineage": lineage
    }
    entry_hash = sha256_json(entry)
    entry["entry_hash"] = entry_hash

    append_line(json.dumps(entry, separators=(",", ":")))
    write_head(entry_hash)
    print(entry_hash)

if __name__ == "__main__":
    main()
