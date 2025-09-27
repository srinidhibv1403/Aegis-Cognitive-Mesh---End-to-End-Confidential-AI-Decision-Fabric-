import hashlib
import json
from pathlib import Path

def stable_policy_bytes(policy_path: str) -> bytes:
    """
    Load YAML or JSON policy, canonicalize deterministically, and return bytes.
    - Sort keys
    - No whitespace differences
    """
    p = Path(policy_path)
    if not p.exists():
        raise FileNotFoundError(policy_path)

    text = p.read_text(encoding="utf-8")
    # Try YAML first, fall back to JSON
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(text)
    except Exception:
        data = json.loads(text)

    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return canonical.encode("utf-8")

def policy_hash(policy_path: str) -> str:
    """
    Return hex SHA256 over canonicalized policy bytes.
    """
    b = stable_policy_bytes(policy_path)
    return hashlib.sha256(b).hexdigest()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = "policies/base.yaml"
    print(policy_hash(path))
