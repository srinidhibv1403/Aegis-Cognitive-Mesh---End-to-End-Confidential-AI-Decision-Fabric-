#!/usr/bin/env python3
import json
import os
import sys
import subprocess
import hashlib
import time
import pathlib
from scripts.lib_retry import retry
from scripts.adt_usage import summarize  # ADT usage snapshot

def call_gate(secret_name: str, token_path: str):
    """
    Ask the gate if the secret can be released.
    Returns (ok: bool, msg: str, attestation_type: Optional[str]).
      - ok=True only if the final JSON line has released:true
      - attestation_type is parsed from the first JSON line when present
    """
    try:
        # Call the gate script with a clean argv list and controlled env
        cmd = ["python3", "scripts/attested_get_secret.py", secret_name, token_path]
        env = os.environ.copy()
        env["PYTHONPATH"] = env.get("PYTHONPATH") or "."
        p = subprocess.run(cmd, capture_output=True, text=True, env=env)
        out = p.stdout.strip()

        if p.returncode != 0:
            return False, f"gate_error:{(p.stderr or out).strip()}", None

        lines = [l for l in out.splitlines() if l.strip()]
        if not lines:
            return False, "gate_empty_output", None

        # Parse audit line (first) for attestation_type
        attestation_type = None
        try:
            audit_obj = json.loads(lines[0])
            if isinstance(audit_obj, dict):
                audit = audit_obj.get("audit")
                if isinstance(audit, dict):
                    attestation_type = audit.get("attestation_type")
        except Exception:
            attestation_type = None

        # Parse release decision (last)
        try:
            release = json.loads(lines[-1])
        except Exception as e:
            return False, f"gate_parse_error:{e}", attestation_type

        if release.get("released") is True:
            return True, "released:true", attestation_type
        return False, "released:false", attestation_type
    except Exception as e:
        return False, f"gate_exception:{e}", None

def main():
    if len(sys.argv) != 3:
        print("Usage: scripts/runbook_resilient.py <secret_name> <token_path>", file=sys.stderr)
        sys.exit(1)

    secret_name = sys.argv[1]
    token_path = sys.argv[2]

    # Retry the gate to tolerate transient failures
    attestation_cache = {"type": None}

    def try_gate():
        ok, msg, att_type = call_gate(secret_name, token_path)
        if att_type:
            attestation_cache["type"] = att_type
        return ok, msg

    ok, msg = retry(try_gate, attempts=5, base_delay=0.3, max_delay=2.0, jitter=0.3)
    if not ok:
        print(f"[deny] Runbook blocked after retries: {msg}")
        sys.exit(2)

    # Approved: write a structured audit entry with real attestation_type and token digest
    try:
        token_txt = pathlib.Path(token_path).read_text(encoding="utf-8").strip()
        token_dig = hashlib.sha256(token_txt.encode("utf-8")).hexdigest()[:12]
    except Exception:
        token_dig = None

    # Day 25: include a short ADT usage snapshot in the audit entry
    usage_totals = summarize()  # {"operation": X, "message": Y, "query_unit": Z}

    audit_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "audit": {"attestation_type": attestation_cache["type"] or "unknown"},
        "released": True,
        "secret_name": secret_name,
        "token_digest": token_dig,
        "adt_usage": usage_totals,
    }

    ap = pathlib.Path("audits/chain.log")
    ap.parent.mkdir(parents=True, exist_ok=True)
    with ap.open("a", encoding="utf-8") as f:
        f.write(json.dumps(audit_entry, ensure_ascii=False) + "\n")

    # Delegate to the existing runbook to perform the approved action
    p = subprocess.run(["bash", "scripts/runbook.sh", secret_name, token_path], text=True)
    sys.exit(p.returncode)

if __name__ == "__main__":
    main()
