import csv, os, random, hashlib
from datetime import datetime, timezone, timedelta

# Output file path
OUT = os.path.join("data", "signals.csv")
# Fixed seed for deterministic reproducible outputs
SEED = int(hashlib.sha256(b"ACM-day5-seed").hexdigest(), 16) % (2**32)

def main():
    random.seed(SEED)
    rows = []
    t0 = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    # 6 ticks, 5‑minute spacing
    for i in range(6):
        ts = (t0 + timedelta(minutes=5*i)).isoformat()
        warehouse = "W3"
        route = "R7"
        risk = max(0.0, min(1.0, round(random.uniform(0.55, 0.68), 2)))
        delay = int(random.uniform(10, 22))
        cost = int(random.uniform(5800, 6800))
        rows.append([ts, warehouse, route, risk, delay, cost])

    # CSV header
    header = ["timestamp", "warehouse", "route", "risk", "delay_minutes", "cost_delta"]
    write_header = not os.path.exists(OUT)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(header)
        w.writerows(rows)

    print(f"✅ Wrote {len(rows)} rows to {OUT}")

if __name__ == "__main__":
    main()
