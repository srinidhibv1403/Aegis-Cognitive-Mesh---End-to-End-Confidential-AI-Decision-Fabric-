import csv, os, subprocess, time

ADT_NAME = "acm-day3-adt-9427"
RG = "acm-day3-rg"
TWIN_ID = "thermo1"
CSV_PATH = os.path.join("data", "signals.csv")

def az(*args):
    cmd = ["az"] + list(args)
    out = subprocess.check_output(cmd, text=True)
    return out

def update_temperature(value: float):
    patch = f'[{{"op":"replace","path":"/temperature","value":{value}}}]'
    az("dt", "twin", "update",
       "-n", ADT_NAME,
       "-g", RG,
       "--twin-id", TWIN_ID,
       "--json-patch", patch)

def main():
    if not os.path.exists(CSV_PATH):
        raise SystemExit(f"❌ Missing {CSV_PATH} — run data_generator.py first!")

    with open(CSV_PATH, newline="") as f:
        rows = list(csv.DictReader(f))

    window = rows[-3:] if len(rows) >= 3 else rows

    for row in window:
        risk = float(row["risk"])
        temp = round(20 + risk * 40, 1)
        update_temperature(temp)
        print(f"🌡 Updated {TWIN_ID}.temperature -> {temp}")
        time.sleep(1)

if __name__ == "__main__":
    main()

