from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_policy_hash():
    r = client.get("/policy/hash")
    assert r.status_code == 200
    body = r.json()
    assert "hash" in body and isinstance(body["hash"], str) and len(body["hash"]) == 64

def test_version():
    r = client.get("/version")
    assert r.status_code == 200
    body = r.json()
    assert "commit" in body and "policy_hash" in body
    assert isinstance(body["policy_hash"], str) and len(body["policy_hash"]) == 64
