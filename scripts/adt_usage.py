#!/usr/bin/env python3
import json, time, pathlib, threading

_lock = threading.Lock()
USAGE_FILE = pathlib.Path("audits/adt_usage.jsonl")

def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def log_op(kind: str, count: int = 1, note: str = ""):
    """
    kind: one of ["operation", "message", "query_unit"]
    count: integer increment
    note: optional short string
    """
    assert kind in ("operation", "message", "query_unit"), "invalid kind"
    rec = {
        "ts": _now(),
        "kind": kind,
        "count": int(count),
        "note": note[:80] if note else ""
    }
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        with USAGE_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")

def summarize(last_n: int = 200):
    """
    Read the last N entries and reduce to totals.
    Returns dict like {"operation": X, "message": Y, "query_unit": Z}
    """
    totals = {"operation": 0, "message": 0, "query_unit": 0}
    if not USAGE_FILE.exists():
        return totals
    lines = USAGE_FILE.read_text(encoding="utf-8").splitlines()[-last_n:]
    for s in lines:
        try:
            obj = json.loads(s)
            k = obj.get("kind")
            c = int(obj.get("count", 0))
            if k in totals:
                totals[k] += c
        except Exception:
            continue
    return totals

if __name__ == "__main__":
    # quick manual test
    log_op("operation")
    print(json.dumps(summarize(), indent=2))
