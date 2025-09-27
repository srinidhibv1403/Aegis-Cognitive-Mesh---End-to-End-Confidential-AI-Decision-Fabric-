#!/usr/bin/env python3
import sys
import json
import base64
import pathlib

# Ensure repo root (parent of scripts/) is on sys.path so hub/* imports resolve
repo_root = pathlib.Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Import the gate (ensure hub/__init__.py and hub/secret_gate.py exist)
try:
    from hub.secret_gate import get_secret_if_attested
except Exception as e:
    print(json.dumps({"error": "import_failed", "detail": str(e), "repo_root": str(repo_root)}))
    sys.exit(5)


def _peek_attestation_type(compact: str) -> str:
    """
    Best-effort extractor for x-ms-attestation-type from the JWT payload.
    - Does not verify signature.
    - Tolerates empty signature.
    - Returns "unknown" on any parsing issue.
    """
    try:
        parts = compact.strip().split(".")
        if len(parts) != 3 or not parts:
            return "unknown"
        seg = parts[1]  # payload segment only
        # Base64URL padding
        pad = "=" * (-len(seg) % 4)
        payload_b = base64.urlsafe_b64decode((seg + pad).encode("ascii", errors="ignore"))
        payload_txt = payload_b.decode("ascii", errors="ignore")
        data = json.loads(payload_txt)
        return data.get("x-ms-attestation-type", "unknown")
    except Exception:
        return "unknown"


def main():
    if len(sys.argv) != 3:
        print("Usage: scripts/attested_get_secret.py <secret_name> <jwt_file>", file=sys.stderr)
        sys.exit(1)

    secret_name = sys.argv[1]
    jwt_file = sys.argv[2]

    # Read the JWT file
    try:
        with open(jwt_file, "r", encoding="utf-8") as f:
            maa_jwt = f.read().strip()
    except Exception as e:
        print(json.dumps({
            "secret_name": secret_name,
            "released": False,
            "error": f"Read error: {e}"
        }))
        sys.exit(2)

    # Print audit line first (attestation type visibility)
    att_type = _peek_attestation_type(maa_jwt)
    print(json.dumps({"audit": {"attestation_type": att_type}}))

    # Call the gate and print the release result
    try:
        val = get_secret_if_attested(secret_name, maa_jwt)
        print(json.dumps({
            "secret_name": secret_name,
            "released": val is not None,
            "value": val if val is not None else None
        }))
        sys.exit(0 if val is not None else 3)
    except Exception as e:
        print(json.dumps({
            "secret_name": secret_name,
            "released": False,
            "error": f"Secret gate error: {e}"
        }))
        sys.exit(4)


if __name__ == "__main__":
    main()
