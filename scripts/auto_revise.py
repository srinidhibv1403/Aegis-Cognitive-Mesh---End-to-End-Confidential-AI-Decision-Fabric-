#!/usr/bin/env python3
import json, sys, time, pathlib
from dataclasses import asdict
from typing import Tuple
from hub.policy_revision import Policy, Plan, Verdict, check_plan


def revise_once(policy: Policy, plan: Plan) -> Tuple[Plan, str]:
    """
    Apply exactly one targeted fix based on the first failing reason.
    """
    v: Verdict = check_plan(policy, plan)
    if v.sat:
        return plan, "no_change"

    reason = v.reason
    p = plan

    if reason == "budget_exceeded":
        # Clamp cost to the cap in one go for demo speed
        over = max(0.0, p.added_cost - policy.budget_cap)
        step = max(200.0, over)  # take a full correction to cap
        new_cost = max(0.0, p.added_cost - step)
        p = Plan(p.route, new_cost, p.expected_delay_minutes, p.data_region, p.pii_used)

    elif reason == "delay_exceeds_limit":
        # Clamp delay to the policy limit in one shot
        new_delay = min(p.expected_delay_minutes, policy.max_delay_minutes)
        p = Plan(p.route, p.added_cost, new_delay, p.data_region, p.pii_used)

    elif reason == "data_egress_non_eu":
        # Enforce EU residency
        p = Plan(p.route, p.added_cost, p.expected_delay_minutes, "EU", p.pii_used)

    elif reason == "pii_used_not_allowed":
        # Disable PII
        p = Plan(p.route, p.added_cost, p.expected_delay_minutes, p.data_region, False)

    else:
        # Unknown reason — leave unchanged with marker
        return plan, f"no_rule_for_{reason}"

    return p, reason


def auto_revise(policy: Policy, plan: Plan, max_attempts: int = 6) -> dict:
    """
    In each attempt, apply up to 4 sequential fixes (budget -> delay -> region -> pii),
    re-checking after each. This converges quickly for demos.
    """
    history = []
    current = plan

    for i in range(1, max_attempts + 1):
        step_log = {"attempt": i, "fixes": []}

        # Try up to 4 fixes in priority order within the same attempt
        for _ in range(4):
            v = check_plan(policy, current)
            step_log.update({"sat": v.sat, "reason": v.reason, "details": v.details})
            if v.sat:
                history.append(step_log)
                return {
                    "final": "SAT",
                    "attempts": i,
                    "plan": asdict(current),
                    "history": history
                }

            # apply one fix
            next_plan, rule = revise_once(policy, current)
            step_log["fixes"].append(rule)
            current = next_plan

        # after up to 4 fixes, record the state for this attempt
        v = check_plan(policy, current)
        step_log.update({"sat": v.sat, "reason": v.reason, "details": v.details})
        history.append(step_log)

        if v.sat:
            return {
                "final": "SAT",
                "attempts": i,
                "plan": asdict(current),
                "history": history
            }

    # If still UNSAT after all attempts
    last = check_plan(policy, current)
    history.append({
        "attempt": max_attempts + 1,
        "sat": last.sat,
        "reason": last.reason,
        "details": last.details
    })
    return {
        "final": "UNSAT",
        "attempts": max_attempts,
        "plan": asdict(current),
        "history": history,
        "counterexample": last.reason
    }


def main():
    # Simple CLI usage:
    # scripts/auto_revise.py '{"policy": {...}, "plan": {...}}'
    if len(sys.argv) < 2:
        print('Usage: scripts/auto_revise.py \'{"policy": {...}, "plan": {...}}\'', file=sys.stderr)
        sys.exit(1)

    payload = json.loads(sys.argv[1])
    pol = payload.get("policy", {})
    pln = payload.get("plan", {})

    policy = Policy(
        budget_cap=float(pol.get("budget_cap", 10000.0)),
        sla_min=float(pol.get("sla_min", 96.0)),
        allow_cross_region=bool(pol.get("allow_cross_region", False)),
        max_delay_minutes=int(pol.get("max_delay_minutes", 60)),
    )
    plan = Plan(
        route=str(pln.get("route", "R7")),
        added_cost=float(pln.get("added_cost", 6400.0)),
        expected_delay_minutes=int(pln.get("expected_delay_minutes", 75)),
        data_region=str(pln.get("data_region", "US")),
        pii_used=bool(pln.get("pii_used", True)),
    )

    result = auto_revise(policy, plan, max_attempts=int(payload.get("max_attempts", 6)))

    # Log a compact audit line
    audits = pathlib.Path("audits")
    audits.mkdir(exist_ok=True, parents=True)
    with (audits / "day21_auto_revise.log").open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "policy": asdict(policy),
            "initial_plan": asdict(plan),
            "result": result.get("final", "n/a"),
            "attempts": result.get("attempts", 0)
        }) + "\n")

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
