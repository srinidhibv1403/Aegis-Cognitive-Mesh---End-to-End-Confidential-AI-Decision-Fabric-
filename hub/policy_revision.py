# hub/policy_revision.py
from dataclasses import dataclass, asdict
from typing import Tuple, Dict, Any

@dataclass
class Policy:
    budget_cap: float           # e.g., 10000.0
    sla_min: float              # e.g., 96.0 (% on-time target)
    allow_cross_region: bool    # e.g., False for non-EU egress
    max_delay_minutes: int      # e.g., 60

@dataclass
class Plan:
    route: str                  # e.g., "R7" or "R3_fast"
    added_cost: float           # e.g., 6400.0
    expected_delay_minutes: int # e.g., 45
    data_region: str            # e.g., "EU" or "US"
    pii_used: bool              # e.g., False

@dataclass
class Verdict:
    sat: bool
    reason: str                 # "ok" or first violated constraint
    details: Dict[str, Any]

def check_plan(policy: Policy, plan: Plan) -> Verdict:
    # Ordered checks; return first violation as a counterexample-style reason.
    if plan.added_cost > policy.budget_cap:
        return Verdict(False, "budget_exceeded", {
            "added_cost": plan.added_cost, "cap": policy.budget_cap
        })

    # SLA modeled via delay bound; exceeding delay implies SLA risk.
    if plan.expected_delay_minutes > policy.max_delay_minutes:
        return Verdict(False, "delay_exceeds_limit", {
            "delay": plan.expected_delay_minutes, "limit": policy.max_delay_minutes
        })

    # Data residency: if cross-region not allowed, require EU.
    if not policy.allow_cross_region and plan.data_region != "EU":
        return Verdict(False, "data_egress_non_eu", {"region": plan.data_region})

    # PII handling: disallow any PII use in this simplified MVP.
    if plan.pii_used:
        return Verdict(False, "pii_used_not_allowed", {"pii_used": True})

    # SLA minimum included for completeness; real SLA calc would be richer.
    return Verdict(True, "ok", {"policy": asdict(policy), "plan": asdict(plan)})
