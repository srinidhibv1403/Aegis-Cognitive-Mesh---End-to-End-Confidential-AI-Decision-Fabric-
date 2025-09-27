from fastapi import FastAPI
from hub.policy_hash import policy_hash
import subprocess

app = FastAPI(title="ACM Hub")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/policy/hash")
def get_policy_hash():
    return {"hash": policy_hash("policies/base.yaml")}

def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"

@app.get("/version")
def version():
    return {"commit": git_sha(), "policy_hash": policy_hash("policies/base.yaml")}
