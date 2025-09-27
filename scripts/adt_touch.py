import os, json, sys, time
from datetime import datetime, timezone

# Guard: skip if env not set (so Codespaces doesn't fail)
ADT_INSTANCE_URL = os.getenv("ADT_INSTANCE_URL")  # e.g., https://<your-adt>.api.<region>.digitaltwins.azure.net
RUN_ADT_TOUCH = os.getenv("RUN_ADT_TOUCH", "false").lower() == "true"

PLANS_PATH = "data/plans"
SIM_PATH = "data/sim"
OUT_PATH = "audits/day13_adt_usage.json"

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def latest_file(glob_pat):
    import glob
    files = sorted(glob.glob(glob_pat), key=os.path.getmtime)
    return files[-1] if files else None

def main():
    usage = {
        "ts": utc_now(),
        "attempted": bool(RUN_ADT_TOUCH and ADT_INSTANCE_URL),
        "adt_instance": ADT_INSTANCE_URL or "unset",
        "ops": 0,
        "messages": 0,
        "query_units": 0,
        "notes": []
    }

    if not RUN_ADT_TOUCH:
        usage["notes"].append("RUN_ADT_TOUCH is false; skipping ADT calls.")
        with open(OUT_PATH, "w") as f:
            json.dump(usage, f, indent=2)
        print(f"ADT touch skipped. Wrote {OUT_PATH}")
        return

    if not ADT_INSTANCE_URL:
        usage["notes"].append("ADT_INSTANCE_URL not set; skipping.")
        with open(OUT_PATH, "w") as f:
            json.dump(usage, f, indent=2)
        print(f"ADT touch skipped (no instance). Wrote {OUT_PATH}")
        return

    # Lazy import SDKs only if actually running
    try:
        from azure.identity import DefaultAzureCredential
        from azure.digitaltwins.core import DigitalTwinsClient
    except Exception as e:
        usage["notes"].append(f"SDK import failed: {e}")
        with open(OUT_PATH, "w") as f:
            json.dump(usage, f, indent=2)
        print(f"ADT touch skipped (no SDK). Wrote {OUT_PATH}")
        return

    try:
        cred = DefaultAzureCredential()
        client = DigitalTwinsClient(ADT_INSTANCE_URL, cred)

        # 1) Minimal read query (LIMIT 5)
        query = "SELECT TOP 5 T FROM digitaltwins T"
        start = time.time()
        items = list(client.query_twins(query))
        elapsed = time.time() - start
        usage["ops"] += 1
        usage["query_units"] += 1  # conservative placeholder; exact QUs only visible in metrics
        usage["notes"].append(f"Query returned {len(items)} in {elapsed:.2f}s")

        # 2) Minimal tag update on zero or one twin if present (safe patch)
        if items:
            twin_id = items[0]["$dtId"]
            patch = [
                {"op": "add", "path": "/acm_day13_marker", "value": True},
                {"op": "add", "path": "/acm_day13_ts", "value": utc_now()}
            ]
            client.update_digital_twin(twin_id, patch)
            usage["ops"] += 1
            usage["messages"] += 1
            usage["notes"].append(f"Patched twin {twin_id} with Day13 markers.")
        else:
            usage["notes"].append("No twins to patch; skipped update op.")

    except Exception as e:
        usage["notes"].append(f"ADT call error: {e}")

    with open(OUT_PATH, "w") as f:
        json.dump(usage, f, indent=2)

    print(f"Wrote ADT usage snapshot: {OUT_PATH}")

if __name__ == "__main__":
    main()
