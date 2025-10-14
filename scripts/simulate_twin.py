import os, json, glob, sys
from datetime import datetime

PLANS_DIR = "data/plans"
SIM_DIR = "data/sim"
os.makedirs(SIM_DIR, exist_ok=True)

def latest_bundle():
    files = sorted(glob.glob(os.path.join(PLANS_DIR, "*.json")), key=os.path.getmtime)
    if not files:
        print("No plan bundles found. Run generate_plans.py first.")
        sys.exit(1)
    with open(files[-1]) as f:
        return json.load(f), files[-1]

bundle, bundle_file = latest_bundle()
event = bundle["event"]

sim_results = []
for p in bundle["plans"]:
    # Use plan's own expectations as the simulated result (deterministic and local)
    kpi = p["kpi_expectations"]
    sim_results.append({
        "plan_id": p["id"],
        "strategy": p["strategy"],
        "inputs": p["inputs"],
        "simulated": {
            "stockout_risk_reduction_pct": kpi["stockout_risk_reduction_pct"],
            "delay_reduction_pct": kpi["delay_reduction_pct"],
            "cost_usd": p["cost_usd"],
            "sla_expected_percent": p["sla_expected_percent"]
        },
        "ts": datetime.utcnow().isoformat() + "Z"
    })

out = {
    "origin_bundle": os.path.basename(bundle_file),
    "event_type": event["type"],
    "route_id": event["route_id"],
    "warehouse_id": event["warehouse_id"],
    "results": sim_results,
    "generated_at": datetime.utcnow().isoformat() + "Z"
}

out_path = os.path.join(SIM_DIR, os.path.splitext(os.path.basename(bundle_file))[0] + "_sim.json")
with open(out_path, "w") as f:
    json.dump(out, f, indent=2)

print(f"Wrote simulation results: {out_path}")
