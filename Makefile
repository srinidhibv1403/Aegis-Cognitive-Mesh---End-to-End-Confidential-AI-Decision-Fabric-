# ACM Makefile

.PHONY: policy-hash policy-lock policy-validate verify pass fail clean simulate simulate-example verify-sim verify-sim-example

# Policy utilities
policy-hash:
	@python3 scripts/hash_policy.py

policy-lock:
	@HASH=$$(python3 scripts/hash_policy.py); \
	printf "policy_sha256: $$HASH\n" > policies/policy.lock; \
	echo "Updated policies/policy.lock to $$HASH"

policy-validate:
	@python3 scripts/validate_policy.py

# Z3 verifier shortcuts (Day 9)
verify:
	@./scripts/verify_plan.sh $(PLAN)

pass:
	@./scripts/verify_plan.sh plan_pass.json

fail:
	@./scripts/verify_plan.sh plan_fail.json

# Simulator shortcuts (Day 10)
simulate:
	@./scripts/simulate_plan.sh $(SNAPSHOT) $(PLAN)

simulate-example:
	@./scripts/simulate_plan.sh twin_snapshot.json plan_example.json

# Verify → Simulate chain (Day 10)
verify-sim:
	@./scripts/verify_then_simulate.sh $(PLAN) $(SNAPSHOT)

verify-sim-example:
	@./scripts/verify_then_simulate.sh plan_pass.json twin_snapshot.json

# Housekeeping
clean:
	@find . -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true

.PHONY: artifact artifact-example

artifact:
	@./scripts/verify_then_simulate_json.py $(PLAN) $(SNAPSHOT)

artifact-example:
	@./scripts/verify_then_simulate_json.py plan_pass.json twin_snapshot.json

.PHONY: lineage-example lineage

lineage-example:
	@./scripts/verify_then_simulate_json.py plan_pass.json twin_snapshot.json > artifacts/_tmp_artifact.json
	@./scripts/write_lineage.py artifacts/_tmp_artifact.json plan_pass.json

lineage:
	@./scripts/verify_then_simulate_json.py $(PLAN) $(SNAPSHOT) > artifacts/_tmp_artifact.json
	@./scripts/write_lineage.py artifacts/_tmp_artifact.json $(PLAN)

.PHONY: audit-append audit-verify

# Append the newest lineage file into the chain
audit-append:
	@latest=$$(ls -t artifacts/lineage_*.json | head -n 1); \
	echo "Appending $$latest"; \
	./scripts/append_audit.py $$latest

# Verify the entire chain integrity
audit-verify:
	@python - <<'EOF'
import json, hashlib, sys

CHAIN_FILE = "audit_chain.jsonl"

def sha256_json(obj):
    data = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

prev = None
ok = True
with open(CHAIN_FILE) as f:
    for i, line in enumerate(f, 1):
        entry = json.loads(line)
        entry_hash = entry.get("entry_hash")
        expect = sha256_json({k:v for k,v in entry.items() if k!="entry_hash"})
        if entry_hash != expect:
            print(f"Line {i}: hash mismatch!")
            ok = False
        if entry["prev_hash"] != prev:
            print(f"Line {i}: prev_hash mismatch!")
            ok = False
        prev = entry_hash
print("Chain OK, head =", prev if ok else "BROKEN")
EOF



