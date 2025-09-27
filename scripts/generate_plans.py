import os, json, glob, time, hashlib
from datetime import datetime

EVENTS_DIR = "data/events"
PLANS_DIR = "data/plans"
os.makedirs(PLANS_DIR, exist_ok=True)

def latest_event():
    files = sorted(glob.glob(os.path.join(EVENTS_DIR, "*.json")), key=os.path.getmtime)
    if not files:
        raise SystemExit("No events found. Run seed_disruption.py first.")
    with open(files[-1]) as f:
        return json.load(f), files[-1]

event, path = latest_event()

plans = [
    {
        "id": "PlanA",
        "strategy": "reroute_via_R7",
        "assumptions": {"carrier_capacity_buffer_pct": 10},
        "cost_usd": 4800,
        "sla_expected_percent": 97.5,
        "region_data_boundary": "EU",
        "pii_access": False,
        "kpi_expectations": {"stockout_risk_reduction_pct": 22, "delay_reduction_pct": 18},
        "inputs": {"route_id": event["route_id"], "warehouse_id": event["warehouse_id"]},
        "ts": datetime.now().isoformat()
    },
    {
        "id": "PlanB",
        "strategy": "reallocate_inventory_and_surge_carrier",
        "assumptions": {"temp_staff_hours": 12},
        "cost_usd": 6400,
        "sla_expected_percent": 98.2,
        "region_data_boundary": "EU",
        "pii_access": False,
        "kpi_expectations": {"stockout_risk_reduction_pct": 42, "delay_reduction_pct": 31},
        "inputs": {"route_id": event["route_id"], "warehouse_id": event["warehouse_id"]},
        "ts": datetime.now().isoformat()
    }
]

bundle = {
    "event": event,
    "plans": plans,
    "origin_event_file": os.path.basename(path),
    "generated_at": datetime.now().isoformat()
}

payload = json.dumps(bundle, sort_keys=True).encode()
bundle_id = hashlib.sha256(payload).hexdigest()[:16]
out_path = os.path.join(PLANS_DIR, f"{bundle_id}.json")

with open(out_path, "w") as f:
    json.dump(bundle, f, indent=2)

print(f"Wrote plan bundle: {out_path}")
