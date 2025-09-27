#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from datetime import datetime

SRC_CANDIDATES = [Path("audits/chain.log"), Path("audit_chain.jsonl")]
OUT = Path("audits/proof_view.html")

def load_records():
    src = None
    for p in SRC_CANDIDATES:
        if p.exists():
            src = p
            break
    if not src:
        print("No audit log found.", file=sys.stderr)
        sys.exit(1)

    recs = []
    with src.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                recs.append(json.loads(s))
            except Exception:
                continue
    return recs

def value(d, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def coalesce(r):
    return {
        "timestamp": r.get("timestamp") or "—",
        "attestation_type": value(r, "audit", "attestation_type", default=r.get("attestation_type","unknown")),
        "policy_hash": r.get("policy_hash") or "—",
        "verdict": r.get("verdict") or "—",
        "released": r.get("released"),
        "secret_name": r.get("secret_name") or "—",
        "token_digest": r.get("token_digest") or "—",
    }

def main():
    k = 10
    if len(sys.argv) >= 2:
        try:
            k = max(1, int(sys.argv[1]))
        except Exception:
            pass

    recs = load_records()
    last = recs[-k:]
    rows = [coalesce(r) for r in last]
    rows.reverse()  # newest first

    html_rows = []
    for r in rows:
        released = "✅" if r.get("released") else ("❌" if r.get("released") is not None else "—")
        html_rows.append(f"""
      <tr>
        <td>{r["timestamp"]}</td>
        <td>{r["attestation_type"]}</td>
        <td><code>{r["policy_hash"]}</code></td>
        <td>{r["verdict"]}</td>
        <td>{released}</td>
        <td>{r["secret_name"]}</td>
        <td><code>{r["token_digest"]}</code></td>
      </tr>
    """)

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Proof Viewer</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; padding: 24px; }}
    h1 {{ margin: 0 0 16px 0; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; font-size: 14px; }}
    th {{ background: #f7f7f7; text-align: left; }}
    code {{ background: #f1f3f5; padding: 2px 4px; border-radius: 3px; }}
    caption {{ text-align: left; margin-bottom: 8px; color: #666; }}
  </style>
</head>
<body>
  <h1>Proof Viewer</h1>
  <p><em>Generated: {datetime.utcnow().isoformat()}Z</em></p>
  <table>
    <caption>Latest entries (newest first)</caption>
    <thead>
      <tr>
        <th>Timestamp</th>
        <th>Attestation Type</th>
        <th>Policy Hash</th>
        <th>Verdict</th>
        <th>Released</th>
        <th>Secret Name</th>
        <th>Token Digest</th>
      </tr>
    </thead>
    <tbody>
      {''.join(html_rows)}
    </tbody>
  </table>
</body>
</html>
"""

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    main()
