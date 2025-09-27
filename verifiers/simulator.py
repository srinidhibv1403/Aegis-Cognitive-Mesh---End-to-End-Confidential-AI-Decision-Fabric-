import json, sys

def simulate(snapshot, plan):
    """
    Compute baseline KPIs from a tiny twin snapshot and compare with plan-provided outcomes.

    Baseline:
    - stockout risk: average over warehouses of max(0, demand-inventory)/demand
    - delay: average latency (minutes) over all routes

    After:
    - risk and delay taken from plan fields (stockout_risk, delay_minutes) for Day 10

    Output:
    - cost_delta: plan cost_usd
    - risk_delta: baseline_risk - after_risk (positive is improvement)
    - delay_delta: baseline_delay - after_delay (positive is improvement)
    """
    warehouses = snapshot.get("warehouses", {})
    routes = snapshot.get("routes", {})

    # Baseline stockout risk (average shortfall ratio across warehouses)
    if warehouses:
        risks = []
        for w in warehouses.values():
            inv = float(w.get("inventory", 0))
            dem = float(w.get("demand", 1)) or 1.0
            shortfall = max(0.0, dem - inv)
            risks.append(shortfall / dem)
        base_risk = sum(risks) / len(risks)
    else:
        base_risk = 0.0

    # Baseline delay (average latency over routes)
    if routes:
        delays = []
        for r in routes.values():
            delays.append(float(r.get("latency_minutes", 0)))
        base_delay = sum(delays) / len(delays)
    else:
        base_delay = 0.0

    # Apply plan “after” values (Day 10: trust plan-provided outcomes)
    after_risk = float(plan.get("stockout_risk", base_risk))
    after_delay = float(plan.get("delay_minutes", base_delay))

    result = {
        "plan_id": plan.get("plan_id", "unknown"),
        "cost_delta": int(plan.get("cost_usd", 0)),
        "risk_delta": round(base_risk - after_risk, 3),
        "delay_delta": round(base_delay - after_delay, 2),
        "baseline": {"risk": round(base_risk, 3), "delay": round(base_delay, 2)},
        "after": {"risk": round(after_risk, 3), "delay": round(after_delay, 2)}
    }
    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python verifiers/simulator.py twin_snapshot.json plan.json")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        snapshot = json.load(f)
    with open(sys.argv[2], "r") as f:
        plan = json.load(f)

    result = simulate(snapshot, plan)
    print(json.dumps(result, indent=2))
