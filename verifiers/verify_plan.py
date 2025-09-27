import json, sys, yaml, hashlib
from z3 import Int, Real, Bool, Solver, sat

BASE_YAML_PATH = "policies/base.yaml"
LOCK_PATH = "policies/policy.lock"

def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_lock(path):
    with open(path, "r") as f:
        doc = f.read().strip()
    key, val = doc.split(":", 1)
    return {key.strip(): val.strip()}

def compute_policy_hash(base):
    include = base.get("hash_include", [])
    def get_by_path(obj, path):
        cur = obj
        for p in path.split("."):
            cur = cur[p]
        return cur
    material = [f"{p}={get_by_path(base, p)}" for p in include]
    text = "\n".join(material).encode("utf-8")
    return hashlib.sha256(text).hexdigest()

def verify(plan, base):
    c = base["constraints"]
    s = Solver()

    # Z3 variables
    cost_usd = Int("cost_usd")
    sla_pct = Int("sla_pct")
    latency_ms = Int("latency_ms")
    is_eu = Bool("is_eu")
    endpoint_private = Bool("endpoint_private")
    stockout_risk = Real("stockout_risk")
    delay_minutes = Int("delay_minutes")

    # Bind plan inputs
    s.add(cost_usd == int(plan["cost_usd"]))
    s.add(sla_pct == int(plan["sla_pct"]))
    s.add(latency_ms == int(plan["latency_ms"]))
    s.add(is_eu == (plan["region"] == "EU"))
    s.add(endpoint_private == (plan["endpoint"] == "private"))
    s.add(stockout_risk == float(plan["stockout_risk"]))
    s.add(delay_minutes == int(plan["delay_minutes"]))

    # Constraints from policy
    s.add(cost_usd <= int(c["budget_cap_usd"]))
    s.add(sla_pct >= int(c["min_sla_percent"]))
    s.add(latency_ms <= int(c["max_latency_ms"]))

    # Jurisdiction: region must be in allowed_jurisdictions
    allowed = set(c["allowed_jurisdictions"])
    # Note: we model this with a post-check for clarity and keep Z3 for the other constraints

    # Data egress rules
    non_eu_allowed = bool(c["data_egress_rules"]["non_eu_egress_allowed"])
    s.add((is_eu == True) | (non_eu_allowed == True))

    s.add(endpoint_private == ("private" in c["data_egress_rules"]["permitted_endpoints"]))

    # Risk thresholds
    s.add(stockout_risk <= float(c["risk_thresholds"]["max_stockout_risk"]))
    s.add(delay_minutes <= int(c["risk_thresholds"]["max_delay_minutes"]))

    # Evaluate
    if s.check() == sat:
        # Still validate jurisdiction list explicitly
        if plan["region"] not in allowed:
            violation_map = {
                "jurisdiction_not_allowed": {
                    "policy_path": "constraints.allowed_jurisdictions",
                    "message": f"Region {plan['region']} not in {c['allowed_jurisdictions']}"
                }
            }
            return {"status": "FAIL", "violations": [ {"code": "jurisdiction_not_allowed", **violation_map["jurisdiction_not_allowed"]} ]}
        return {"status": "PASS"}
    else:
        # Build violation list from simple checks for clear messages
        violations = []

        if plan["cost_usd"] > c["budget_cap_usd"]:
            violations.append("budget_cap_usd")
        if plan["sla_pct"] < c["min_sla_percent"]:
            violations.append("min_sla_percent")
        if plan["latency_ms"] > c["max_latency_ms"]:
            violations.append("max_latency_ms")
        if plan["region"] not in allowed:
            violations.append("jurisdiction_not_allowed")
        if plan["region"] != "EU" and not non_eu_allowed:
            violations.append("non_eu_egress_not_allowed")
        if plan["endpoint"] != "private":
            violations.append("endpoint_not_permitted")
        if float(plan["stockout_risk"]) > float(c["risk_thresholds"]["max_stockout_risk"]):
            violations.append("max_stockout_risk")
        if int(plan["delay_minutes"]) > int(c["risk_thresholds"]["max_delay_minutes"]):
            violations.append("max_delay_minutes")

        violation_map = {
            "budget_cap_usd": {
                "policy_path": "constraints.budget_cap_usd",
                "message": f"Cost {plan['cost_usd']} exceeds cap {c['budget_cap_usd']}"
            },
            "min_sla_percent": {
                "policy_path": "constraints.min_sla_percent",
                "message": f"SLA {plan['sla_pct']}% below minimum {c['min_sla_percent']}%"
            },
            "max_latency_ms": {
                "policy_path": "constraints.max_latency_ms",
                "message": f"Latency {plan['latency_ms']}ms exceeds max {c['max_latency_ms']}ms"
            },
            "jurisdiction_not_allowed": {
                "policy_path": "constraints.allowed_jurisdictions",
                "message": f"Region {plan['region']} not in {c['allowed_jurisdictions']}"
            },
            "non_eu_egress_not_allowed": {
                "policy_path": "constraints.data_egress_rules.non_eu_egress_allowed",
                "message": "Non‑EU egress not allowed while region is non‑EU"
            },
            "endpoint_not_permitted": {
                "policy_path": "constraints.data_egress_rules.permitted_endpoints",
                "message": f"Endpoint {plan['endpoint']} not permitted; require 'private'"
            },
            "max_stockout_risk": {
                "policy_path": "constraints.risk_thresholds.max_stockout_risk",
                "message": f"Stockout risk {plan['stockout_risk']} exceeds max {c['risk_thresholds']['max_stockout_risk']}"
            },
            "max_delay_minutes": {
                "policy_path": "constraints.risk_thresholds.max_delay_minutes",
                "message": f"Delay {plan['delay_minutes']}min exceeds max {c['risk_thresholds']['max_delay_minutes']}min"
            },
        }

        details = [ { "code": v, **violation_map.get(v, {"policy_path": "unknown", "message": v}) } for v in violations ]
        return {"status": "FAIL", "violations": details}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verifiers/verify_plan.py <plan.json>")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        plan = json.load(f)

    base = load_yaml(BASE_YAML_PATH)
    lock = load_lock(LOCK_PATH)
    recomputed = compute_policy_hash(base)
    locked = lock.get("policy_sha256")

    if locked and recomputed != locked:
        print(json.dumps({
            "status": "FAIL",
            "reason": "policy_hash_mismatch",
            "recomputed": recomputed,
            "locked": locked
        }, indent=2))
        sys.exit(2)

    verdict = verify(plan, base)
    verdict["policy_sha256"] = locked or recomputed
    print(json.dumps(verdict, indent=2))
