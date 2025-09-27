

# 🚀 Aegis Cognitive Mesh (ACM)

Live demo : visit website :(https://cognitivemesh.streamlit.app/)

**Azure-native, secure, AI decision fabric — “prove-then-execute.”**

ACM is a highly secure, **attested decision-making mesh** that ensures all actions are safe, auditable, and resilient. It blends **Confidential Compute, Azure Attestation, Digital Twins, and formal policy checks** into a single fabric for **deterministic, interview-ready demos**.

---

## ✨ Core Capabilities

* 🔒 **Confidential Compute** — protect sensitive operations.
* ✅ **Azure Attestation** — prove environment integrity before execution.
* 🔑 **Secure Key Release (SKR)** — secrets only released after verification.
* 🌐 **Azure Digital Twins (ADT)** — simulate warehouses, routes, and systems before acting.
* 📏 **Policy Verification with Z3** — enforce compliance and prevent unsafe decisions.

---

## 🎯 Goals

* Guarantee decisions are **safe + auditable**.
* Deliver a **resilient, production-suitable demo system**.
* Maintain **cost hygiene** (student credits, minimal Azure usage).
* Keep runs **deterministic and replayable** for interviews.

---

## 💰 Cost Hygiene

* Use **Azure for Students** credits sparingly.
* Run compute **only during tests/demos**.
* Set spend alerts; keep Digital Twins minimal.
* Avoid costly services (Managed HSM, Purview) unless needed.
* Prefer **local simulation** whenever possible.

---

## 🏗️ Architecture

📌 See `ops/architecture-v1.png` (or `architecture-template.txt`)

The mesh integrates:

* **Proof-then-execute pipeline**
* **Policy hashing + lock enforcement**
* **Immutable audit chain**
* **Local + cloud simulation modes**

---

## ⚙️ Development

### 🔗 Git Hooks

Enable policy-lock checks on commit:

```bash
bash scripts/setup_hooks.sh
```

### 📜 Policy Hashing & Locking

* Compute hash: `make policy-hash`
* Update lock: `make policy-lock`
* Commit lock:

  ```bash
  git add policies/policy.lock
  git commit -m "chore: update policy.lock after policy change"
  ```

### 🧪 CI Enforcement

CI verifies that the computed policy hash matches `policies/policy.lock`.
If mismatched → CI fails until updated.

---

## 🧩 Common Tasks

* Compute current policy hash → `make policy-hash`
* Update policy lock → `make policy-lock`
* Fix blocked commits → `make policy-lock && git add policies/policy.lock`

---

## 🖥️ Demos

### 🔹 Day 13 — Mini Demo (First Integrated Run)

```bash
./day13.sh
```

Artifacts → JSON plans, simulations, audit proof chain (`audits/day13_proof.jsonl`).

Tag: **`v0.13-demo`**

---

### 🔹 Day 15–17 — Attested Secret Release

* Simulated (default):

  ```bash
  ./scripts/run_gate.sh
  ```
* Hardware SEV-SNP (Azure CVM):

  ```bash
  ./scripts/run_gate_sevsnp.sh "acm-demo-ephemeral" audits/snp_token.jwt
  ```

Offline validation:

```bash
./scripts/validate_jwt.py audits/day15_token.jwt
```

---

### 🔹 Day 19 — Local Assistant (Zero Cost)

```bash
./scripts/assist.sh "your question"
```

→ Logs deterministic answer to `audits/day19_assistant.log`.

---

### 🔹 Day 21 — Auto-Revision on UNSAT

```bash
PYTHONPATH=. ./scripts/auto_revise.py '{"policy":{...},"plan":{...},"max_attempts":6}'
```

→ Iteratively revises plan until **SAT**. Log: `audits/day21_auto_revise.log`.

---

### 🔹 Day 29 — CLI/API Cheat Sheet

* Full demo: `./scripts/demo_script.sh`
* Demo up/down: `./scripts/demo_up.sh`, `./scripts/demo_down.sh`
* Proof (CLI): `python3 scripts/proof_viewer.py 5`
* Proof (HTML): `python3 scripts/proof_viewer_html.py 10` → `audits/proof_view.html`
* Resilient runbook:

  ```bash
  PYTHONPATH=. ./scripts/runbook_resilient.py "acm-demo-ephemeral" audits/day15_token.jwt
  ```

---

## 📑 Notes

* **Proof HTML:** `audits/proof_view.html`
* **Audit chain:** `audits/chain.log`
* **Cost check:** `./scripts/cost_check.sh`

---

## 🚦 Roadmap

* [x] Day 1–30 MVP complete (**v0.10 Perfect-10 tag**)
* [ ] Extend to hybrid cloud (multi-region proofs)
* [ ] Add cloud-enabled assistant mode
* [ ] Integrate ML-driven policy optimization

---

💡 **Tip for interviews:**
Run → `./scripts/demo_script.sh`
Open → `audits/proof_view.html`
Say → *“ACM proves before it executes — confidential compute, attestation, digital twins, and policy verification all in one deterministic fabric.”*

