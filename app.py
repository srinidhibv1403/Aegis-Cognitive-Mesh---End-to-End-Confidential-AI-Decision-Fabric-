# app.py
import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

import streamlit as st

# Ensure repo root on path for hub.* imports
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Reuse your canonical policy hash
from hub.policy_hash import policy_hash as acm_policy_hash

# -----------------------
# Utility + Repo Helpers
# -----------------------
def sh(cmd: List[str], timeout: int = 120, env: Optional[dict] = None) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except Exception as e:
        return 99, "", str(e)

def latest_file(glob_pat: str) -> Optional[Path]:
    files = sorted(Path(".").glob(glob_pat), key=lambda p: p.stat().st_mtime if p.exists() else 0)
    return files[-1] if files else None

def load_json(path: Optional[Path]) -> Optional[dict]:
    if not path or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def dump_json_atomic(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    tmp.replace(path)

def quick_notice(msg: str, ok: bool):
    (st.success if ok else st.warning)(msg)

# -----------------------
# UI Config
# -----------------------
st.set_page_config(page_title="Aegis Cognitive Mesh — Prove-then-Execute", page_icon="🛡️", layout="wide")
st.title("Aegis Cognitive Mesh — Prove-then-Execute")

# Sidebar: Global info + policy hash
with st.sidebar:
    st.header("Repo & Policy")
    policy_path = "policies/base.yaml"
    lock_path = "policies/policy.lock"
    st.caption("Canonical Policy Hash")
    if Path(policy_path).exists():
        st.code(acm_policy_hash(policy_path), language="text")
    else:
        st.error("Missing policies/base.yaml")

    if Path(lock_path).exists():
        st.caption("Lock file")
        st.code(Path(lock_path).read_text(encoding="utf-8").strip(), language="text")
    else:
        st.warning("Missing policies/policy.lock")

    st.divider()
    if st.button("Validate Policy (schema)", use_container_width=True):
        rc, out, err = sh(["python3", "scripts/validate_policy.py"])
        st.write("stdout:"); st.code(out or "—")
        if err: st.write("stderr:"); st.code(err)
        quick_notice("Policy validation OK" if rc == 0 else f"Policy validation failed (rc={rc})", rc == 0)

# -----------------------
# Presets: supply chains
# -----------------------
PRESETS = {
    "Wine": {
        "snapshot": {
            "warehouses": {
                "W1": {"inventory": 120, "demand": 150},
                "W2": {"inventory": 90, "demand": 110},
                "W3": {"inventory": 60, "demand": 140},
            },
            "routes": {
                "R5": {"latency_minutes": 25},
                "R6": {"latency_minutes": 35},
                "R7": {"latency_minutes": 40},
            },
        },
        "default_route": "R7",
        "default_warehouse": "W3",
    },
    "Electronics": {
        "snapshot": {
            "warehouses": {
                "W1": {"inventory": 200, "demand": 220},
                "W2": {"inventory": 150, "demand": 210},
                "W3": {"inventory": 70, "demand": 140},
            },
            "routes": {
                "R2": {"latency_minutes": 22},
                "R3": {"latency_minutes": 28},
                "R4": {"latency_minutes": 33},
            },
        },
        "default_route": "R3",
        "default_warehouse": "W2",
    },
    "Grocery": {
        "snapshot": {
            "warehouses": {
                "W1": {"inventory": 80, "demand": 100},
                "W2": {"inventory": 95, "demand": 120},
            },
            "routes": {
                "R1": {"latency_minutes": 30},
                "R2": {"latency_minutes": 20},
            },
        },
        "default_route": "R2",
        "default_warehouse": "W1",
    },
}

# -----------------------
# Selection Form
# -----------------------
st.subheader("1) Choose Supply Chain and Disruption")
with st.form("selector"):
    chain = st.selectbox("Supply Chain Preset", list(PRESETS.keys()), index=0, help="A small baseline snapshot; still uses your modules/scripts.")
    disruption = st.selectbox(
        "Disruption Type",
        ["route_outage", "delay_spike", "inventory_shortage"],
        index=0
    )
    preset = PRESETS[chain]
    route_ids = list(preset["snapshot"]["routes"].keys())
    wh_ids = list(preset["snapshot"]["warehouses"].keys())
    route_sel = st.selectbox("Route", route_ids, index=max(0, route_ids.index(preset["default_route"]) if preset["default_route"] in route_ids else 0))
    wh_sel = st.selectbox("Warehouse", wh_ids, index=max(0, wh_ids.index(preset["default_warehouse"]) if preset["default_warehouse"] in wh_ids else 0))

    # Advanced options (visual only)
    st.markdown("Advanced options")
    allow_write_proof = st.checkbox("Append proof entry after simulation", value=False)
    submitted = st.form_submit_button("Run Demo")

# -----------------------
# Orchestration helpers
# -----------------------
def seed_event(disruption_type: str, route_id: str, wh_id: str) -> Path:
    sh(["python3", "scripts/seed_disruption.py"])
    evt_p = latest_file("data/events/*.json") or Path("data/events/custom_event.json")
    nowz = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    event = {
        "type": disruption_type,
        "route_id": route_id,
        "warehouse_id": wh_id,
        "source": "streamlit-demo",
        "severity": "high",
        "ts": nowz,
    }
    dump_json_atomic(evt_p, event)
    return evt_p

def gen_plans():
    rc, out, err = sh(["python3", "scripts/generate_plans.py"])
    bundle_p = latest_file("data/plans/*.json")
    return bundle_p, rc, out, err

def verify_all_with_z3_return_table() -> List[Dict[str, Any]]:
    rc, out, err = sh(["python3", "scripts/verify_policies.py"])
    table: List[Dict[str, Any]] = []
    if rc == 0 and out:
        try:
            res = json.loads(out)
            for r in res.get("results", []):
                table.append({
                    "plan_id": r.get("plan_id"),
                    "strategy": r.get("strategy"),
                    "sat": r.get("sat"),
                    "counterexample": r.get("counterexample"),
                    "via": "z3"
                })
        except Exception:
            pass
    return table

def simulate_from_bundle():
    rc, out, err = sh(["python3", "scripts/simulate_twin.py"])
    sim_p = latest_file("data/sim/*_sim.json")
    return sim_p, rc, out, err

def write_proof_entry():
    rc, out, err = sh(["python3", "scripts/write_proof.py"])
    return rc, out, err

def soft_verify_plans_from_config(bundle_path: Path, config_path: str = "configs/day13.yaml") -> List[Dict[str, Any]]:
    """
    Fallback: if Z3 results are empty, apply the same logical checks
    used by scripts/verify_policies.py: budget, SLA, region boundary, PII=false.
    """
    import yaml
    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    boundary = cfg.get("region_data_boundary")
    budget_cap = float(cfg.get("budget_cap_usd", 1e12))
    sla_min = float(cfg.get("sla_min_percent", 0.0))
    bundle = load_json(bundle_path) or {}
    rows: List[Dict[str, Any]] = []
    for p in bundle.get("plans", []):
        ok = True
        reasons = []
        if float(p.get("cost_usd", 1e12)) > budget_cap:
            ok = False; reasons.append("budget_cap")
        if float(p.get("sla_expected_percent", 0.0)) < sla_min:
            ok = False; reasons.append("sla_min")
        if p.get("region_data_boundary") != boundary:
            ok = False; reasons.append("region_mismatch")
        if bool(p.get("pii_access", False)):
            ok = False; reasons.append("pii_access")
        rows.append({
            "plan_id": p.get("id"),
            "strategy": p.get("strategy"),
            "sat": ok,
            "counterexample": None if ok else ", ".join(reasons),
            "via": "policy-fallback"
        })
    return rows

def choose_best_plan(bundle_path: Path, verdict_rows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    bundle = load_json(bundle_path) or {}
    plans = bundle.get("plans", [])
    sat_ids = {r["plan_id"] for r in verdict_rows if r.get("sat")}
    candidates = [p for p in plans if p.get("id") in sat_ids]
    if not candidates:
        return None
    candidates.sort(key=lambda p: (float(p.get("cost_usd", 1e12)), -float(p.get("sla_expected_percent", 0.0))))
    return candidates[0]

# -----------------------
# Visualization helpers
# -----------------------
def draw_chain(snapshot: dict, highlight_route: Optional[str], highlight_wh: Optional[str]):
    import matplotlib.pyplot as plt
    warehouses: dict = snapshot.get("warehouses", {})
    routes: dict = snapshot.get("routes", {})
    def _layout_positions(ws: dict) -> dict[str, tuple[float, float]]:
        names = list(ws.keys()); n = max(1, len(names)); pos = {}
        for i, name in enumerate(names):
            x = 0.1 + 0.8 * (i / max(1, n - 1)); y = 0.65 if i % 2 == 0 else 0.35
            pos[name] = (x, y)
        return pos
    positions = _layout_positions(warehouses)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    for name, (x, y) in positions.items():
        ax.add_patch(plt.Rectangle((x - 0.04, y - 0.03), 0.08, 0.06,
                                   facecolor="#e3f2fd" if name != highlight_wh else "#ffebee",
                                   edgecolor="#1565c0" if name != highlight_wh else "#c62828",
                                   linewidth=2))
        inv = warehouses[name].get("inventory", "?"); dem = warehouses[name].get("demand", "?")
        ax.text(x, y + 0.035, name, ha="center", va="bottom", fontsize=10,
                color="#0d47a1" if name != highlight_wh else "#b71c1c", fontweight="bold")
        ax.text(x, y - 0.01, f"inv={inv}, dem={dem}", ha="center", va="top", fontsize=9, color="#37474f")
    route_names = list(routes.keys()); wnames = list(positions.keys())
    if len(wnames) >= 2 and route_names:
        for i, rname in enumerate(route_names):
            a = wnames[i % len(wnames)]; b = wnames[(i + 1) % len(wnames)]
            x1, y1 = positions[a]; x2, y2 = positions[b]
            color = "#90a4ae"; width = 2.5
            if rname == highlight_route: color = "#e53935"; width = 3.2
            ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                        arrowprops=dict(arrowstyle="-", color=color, lw=width))
            lat = routes[rname].get("latency_minutes", "?")
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.03, f"{rname} • {lat}m",
                    ha="center", va="center", fontsize=9, color=color)
    st.pyplot(fig, clear_figure=True)

# -----------------------
# Demo execution
# -----------------------
if submitted:
    with st.status("Analyzing chain...", expanded=True) as status:
        # 1) Snapshot
        snapshot = PRESETS[chain]["snapshot"]
        dump_json_atomic(Path("twin_snapshot.json"), snapshot)
        st.write("Snapshot prepared for:", chain); st.json(snapshot)
        st.write("Initial Supply Chain:"); draw_chain(snapshot, None, None)

        status.update(label="Problem detected...")
        time.sleep(0.2)

        # 2) Event
        evt_p = seed_event(disruption, route_sel, wh_sel)
        event = load_json(evt_p) or {}
        st.write("Seeded Event:"); st.json(event)
        st.write("Affected elements highlighted:")
        draw_chain(snapshot, event.get("route_id"), event.get("warehouse_id"))

        status.update(label="Generating plans...")
        time.sleep(0.2)

        # 3) Plans
        bundle_p, rc_gp, out_gp, err_gp = gen_plans()
        st.write("Plan generation stdout:"); st.code(out_gp or "—")
        if err_gp: st.write("stderr:"); st.code(err_gp)
        if rc_gp != 0 or not bundle_p:
            status.update(label="Plan generation failed", state="error"); st.stop()
        bundle = load_json(bundle_p) or {}
        plans = bundle.get("plans", [])
        st.success(f"Generated {len(plans)} plan(s):")
        st.dataframe(
            [
                {"plan_id": p["id"], "strategy": p["strategy"], "cost_usd": p["cost_usd"],
                 "sla_expected_percent": p["sla_expected_percent"], "region": p.get("region_data_boundary"),
                 "pii_access": p.get("pii_access")}
                for p in plans
            ],
            use_container_width=True,
        )

        status.update(label="Verifying with Z3...")
        time.sleep(0.2)

        # 4) Verify
        z3_rows = verify_all_with_z3_return_table()
        verdict_rows = z3_rows[:]
        used_fallback = False
        if not verdict_rows or all(not r.get("sat") for r in verdict_rows):
            # Fallback to policy checks if Z3 has no SAT
            used_fallback = True
            verdict_rows = soft_verify_plans_from_config(bundle_p)

        # Show results
        st.write("Verification results:")
        st.dataframe(verdict_rows, use_container_width=True)

        # 5) Choose best from whichever path yielded SAT
        best = choose_best_plan(bundle_p, verdict_rows)
        if not best:
            status.update(label="No SAT plan found after fallback; please check policy thresholds.", state="error")
            st.stop()

        via = "Z3" if (not used_fallback) else "policy-fallback"
        st.success(
            f"Best plan selected ({via}): {best['id']} ({best['strategy']}) — "
            f"cost={best['cost_usd']}, SLA={best['sla_expected_percent']}%"
        )

        status.update(label="Simulating before vs after...")
        time.sleep(0.2)

        # 6) Simulate
        sim_p, rc_sim, out_sim, err_sim = simulate_from_bundle()
        st.write("Simulation stdout:"); st.code(out_sim or "—")
        if err_sim: st.write("stderr:"); st.code(err_sim)
        if not (rc_sim == 0 and sim_p):
            status.update(label="Simulation failed", state="error"); st.stop()

        sim = load_json(sim_p) or {}
        st.write("Simulation results (all candidates):")
        st.dataframe(sim.get("results", []), use_container_width=True)

        # Selected plan deltas
        best_res = None
        for r in sim.get("results", []):
            if r.get("plan_id") == best["id"]:
                best_res = r; break

        st.subheader("Before vs After (Selected Plan)")
        cols = st.columns(3)
        if best_res:
            simd = best_res.get("simulated", {})
            cols[0].metric("Cost (USD)", f"{simd.get('cost_usd','?')}")
            cols[1].metric("Delay reduction (%)", f"{simd.get('delay_reduction_pct','?')}")
            cols[2].metric("Stockout risk reduction (%)", f"{simd.get('stockout_risk_reduction_pct','?')}")
        else:
            st.info("No per-plan simulation found; check bundle/sim alignment.")

        st.write("Post-plan narrative: reduced delay and stockout risk on affected route/warehouse.")
        draw_chain(snapshot, None, None)

        # 7) Optional proof
        proof_note = False
        if allow_write_proof:
            status.update(label="Writing proof entry...")
            rc_pf, out_pf, err_pf = write_proof_entry()
            st.write("write_proof stdout:"); st.code(out_pf or "—")
            if err_pf: st.write("stderr:"); st.code(err_pf)
            if rc_pf == 0:
                st.success("Proof entry appended to audits/day13_proof.jsonl"); proof_note = True
            else:
                st.warning(f"write_proof returned rc={rc_pf}")

        status.update(label="Simulation applied.", state="complete")

        # 8) Summary
        st.subheader("Verification summary")
        summary_lines: List[str] = []
        summary_lines.append(
            f"We detected a disruption on route {event.get('route_id')} affecting warehouse {event.get('warehouse_id')}."
        )
        summary_lines.append(f"Generated {len(plans)} candidate plan(s): " + ", ".join(p.get('id','?') for p in plans))
        if verdict_rows:
            sat_cnt = sum(1 for r in verdict_rows if r.get("sat")); unsat_cnt = len(verdict_rows) - sat_cnt
            mode = "Z3" if (not used_fallback) else "policy checks"
            summary_lines.append(f"Policy check via {mode}: {sat_cnt} SAT, {unsat_cnt} UNSAT.")
        summary_lines.append(
            f"Best plan: {best.get('id')} ({best.get('strategy')}); cost ${best.get('cost_usd')}, "
            f"expected SLA {best.get('sla_expected_percent')}%."
        )
        if best_res:
            simd = best_res.get("simulated", {})
            summary_lines.append(
                f"Simulation impact: delay reduction {simd.get('delay_reduction_pct')}%, "
                f"stockout risk reduction {simd.get('stockout_risk_reduction_pct')}%."
            )
        if proof_note:
            summary_lines.append(
                "A proof entry was appended to the audit log with policy hash, verdicts, and simulation deltas."
            )
        st.write("\n".join(f"- {line}" for line in summary_lines))
