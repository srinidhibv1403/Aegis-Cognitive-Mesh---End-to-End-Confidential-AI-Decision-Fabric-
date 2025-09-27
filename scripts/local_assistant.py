#!/usr/bin/env python3
import sys, json, time, pathlib

def respond(question: str) -> dict:
    # Deterministic stub: classify intent and return a safe, fixed answer
    q = (question or "").strip().lower()
    if not q:
        msg = "Ask a question or provide a short instruction."
    elif "attest" in q or "maa" in q or "skr" in q:
        msg = "Attestation/SKR path: use your approved runbook after gate returns released:true."
    elif "twin" in q or "digital twin" in q:
        msg = "Twin tip: keep model small and batch queries to minimize QUs in demos."
    elif "policy" in q or "z3" in q:
        msg = "Policy check: compute policy hash, verify SAT/UNSAT; show counterexample if UNSAT."
    else:
        msg = "Assistant (local) is active. No cloud calls were made."

    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "local-stub",
        "input": question,
        "output": msg
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: ./scripts/local_assistant.py \"<question>\"")
        sys.exit(1)
    question = sys.argv[1]
    ans = respond(question)
    # Append to audits/day19_assistant.log
    log_path = pathlib.Path("audits/day19_assistant.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ans) + "\n")
    print(json.dumps(ans))

if __name__ == "__main__":
    main()
