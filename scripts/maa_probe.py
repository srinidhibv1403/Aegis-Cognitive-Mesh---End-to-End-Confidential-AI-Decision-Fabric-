# scripts/maa_probe.py
import json, os, datetime as dt, ssl, urllib.request
from typing import Any, Dict
from azure.identity import DefaultAzureCredential
from azure.security.attestation import AttestationClient

ATTEST_URL = os.environ.get("ATTEST_URL", "https://acmattest9427.cin.attest.azure.net")
OIDC_URL = f"{ATTEST_URL}/.well-known/openid-configuration"

def iso(ts: int) -> str:
    # timezone-aware UTC
    return dt.datetime.fromtimestamp(ts, dt.UTC).isoformat() + "Z"

def http_get_json(url: str) -> Dict[str, Any]:
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(url, context=ctx) as r:
        return json.loads(r.read().decode("utf-8"))

def main() -> None:
    # 1) Verify service reachability through SDK auth
    cred = DefaultAzureCredential(exclude_shared_token_cache_credential=True)
    client = AttestationClient(ATTEST_URL, credential=cred)
    _ = client.get_open_id_metadata()  # sanity: should not error

    # 2) Pull OpenID config directly to get jwks_uri reliably
    oidc = http_get_json(OIDC_URL)
    issuer = oidc.get("issuer")
    jwks_uri = oidc.get("jwks_uri")

    jwks = http_get_json(jwks_uri) if jwks_uri else {"keys": []}
    keys = jwks.get("keys", []) or []
    keys_count = len(keys)

    # 3) Simulated attestation summary for Day 15
    now = int(dt.datetime.now(dt.UTC).timestamp())  # timezone-aware UTC
    claims: Dict[str, Any] = {
        "iss": issuer,
        "iat": now,
        "exp": now + 3600,
        "x-ms-attestation-type": "simulated",
        "x-ms-policy-hash": None,
        "measurement": {"mrenclave": None, "mrsigner": None},
        "result": "probed-metadata-ok",
    }

    out = {
        "attestor": ATTEST_URL,
        "issuer": issuer,
        "jwks_keys": keys_count,
        "claims": claims,
        "issuedAt": iso(claims["iat"]),
        "expiresAt": iso(claims["exp"]),
        "signingKeyThumbprint": None,
    }
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
