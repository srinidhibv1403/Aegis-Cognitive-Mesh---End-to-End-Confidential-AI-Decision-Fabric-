#!/usr/bin/env python3
import sys, json, hashlib
from pathlib import Path
import yaml

def get_by_path(obj, path):
    cur = obj
    for part in path.split('.'):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise KeyError(f"Path not found: {path}")
    return cur

def main():
    policy_path = Path("policies/base.yaml")
    if not policy_path.exists():
        print("Policy file not found at policies/base.yaml", file=sys.stderr)
        sys.exit(1)

    with policy_path.open("r") as f:
        doc = yaml.safe_load(f)

    includes = doc.get("hash_include", [])
    if not includes:
        print("hash_include is empty or missing", file=sys.stderr)
        sys.exit(2)

    # Build a deterministic minimal structure
    material = {}
    for path in includes:
        try:
            value = get_by_path(doc, path)
        except KeyError as e:
            print(str(e), file=sys.stderr)
            sys.exit(3)
        material[path] = value

    # Canonical JSON: sorted keys, no spaces, stable types
    canonical = json.dumps(material, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    print(digest)

if __name__ == "__main__":
    main()
