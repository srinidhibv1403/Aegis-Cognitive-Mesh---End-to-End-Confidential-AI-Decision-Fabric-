import os
from hub.policy_hash import policy_hash

def main():
    h1 = policy_hash("policies/base.yaml")
    h2 = policy_hash("policies/base.yaml")
    assert isinstance(h1, str) and len(h1) == 64, "Hash should be 64-char hex"
    assert h1 == h2, "Hash must be deterministic"
    print("OK policy_hash:", h1)

if __name__ == "__main__":
    main()
