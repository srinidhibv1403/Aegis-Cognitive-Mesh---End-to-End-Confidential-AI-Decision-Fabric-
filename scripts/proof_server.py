#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any
from flask import Flask, render_template, request, Response

AUDIT_FILES = [Path("audits/chain.log"), Path("audit_chain.jsonl")]

# Flask app with template/static folders under ui/
app = Flask(__name__, template_folder="../ui/templates", static_folder="../ui/static")
# Ensure Unicode characters (like em dashes) are not escaped in JSON
app.config["JSON_AS_ASCII"] = False


def load_records() -> List[Dict[str, Any]]:
    """Load JSONL audit records from the first available audit file."""
    src = next((p for p in AUDIT_FILES if p.exists()), None)
    if not src:
        return []
    recs: List[Dict[str, Any]] = []
    with src.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                recs.append(json.loads(s))
            except Exception:
                # Tolerate non-JSON lines in chain.log
                continue
    return recs


def value(d: Dict[str, Any], *keys, default=None):
    """Safely extract nested keys from a dict."""
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def coalesce(r: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a record into the fields the UI expects."""
    u = r.get("adt_usage") or {}
    usage_str = f'op:{u.get("operation",0)} msg:{u.get("message",0)} qu:{u.get("query_unit",0)}' if u else "—"
    return {
        "timestamp": r.get("timestamp") or "—",
        # prefer nested "audit.attestation_type", fall back to top-level
        "attestation_type": value(
            r, "audit", "attestation_type",
            default=r.get("attestation_type", "unknown")
        ),
        "policy_hash": r.get("policy_hash") or "—",
        "verdict": r.get("verdict") or "—",
        "released": r.get("released"),
        "secret_name": r.get("secret_name") or "—",
        "token_digest": r.get("token_digest") or "—",
        "adt_usage": usage_str,
    }


@app.route("/api/audit")
def api_audit():
    """Return latest N normalized audit entries as JSON, with unicode preserved."""
    try:
        n = max(1, int(request.args.get("n", "20")))
    except Exception:
        n = 20
    recs = load_records()
    rows = [coalesce(x) for x in recs[-n:]]
    rows.reverse()  # newest first
    payload = {
        "count": len(rows),
        "generated": datetime.now(timezone.utc).isoformat(),
        "entries": rows,
    }
    # Ensure em dashes (—) are not escaped to \u2014
    return Response(
        json.dumps(payload, ensure_ascii=False, separators=(",", ": ")),
        mimetype="application/json; charset=utf-8",
    )


@app.route("/")
def home():
    """Render the proof viewer HTML with latest N entries."""
    try:
        n = max(1, int(request.args.get("n", "20")))
    except Exception:
        n = 20
    recs = load_records()
    rows = [coalesce(x) for x in recs[-n:]]
    rows.reverse()
    generated = datetime.now(timezone.utc).isoformat()
    return render_template("proof.html", rows=rows, generated=generated, count=len(rows))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5057, debug=True)
