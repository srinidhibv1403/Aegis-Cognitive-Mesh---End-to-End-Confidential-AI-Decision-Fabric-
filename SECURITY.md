# Security Posture — Aegis Cognitive Mesh (ACM)

## Overview
ACM enforces prove-then-execute. Actions run only after cryptographic proof conditions are met, and every approved action is immutably logged.

## Threat Model (scope for MVP)
- Adversaries: untrusted workloads, tampered clients, stolen tokens, operator mistakes.
- Assets: secrets/keys, policy definitions + hash, audit integrity, deployment cost controls.
- Trust anchors: Azure Attestation (issuer + type), Key Vault Secure Key Release policy (simulated for now), repo policy lock.
- Out of scope (MVP): end-user PII, cross-tenant data residency enforcement, full supply-chain SBOM.

## Controls (implemented)
- **Attestation gate** (simulated today; SEV-SNP later):  
  - Token is required; gate evaluates issuer + x-ms-attestation-type and returns released:true only on policy match.  
  - Script prints an audit line before release with attestation_type for visibility.  
- **Approved runbook (fail-closed):**  
  - `scripts/runbook.sh` calls the gate; exits if released:false.  
  - Executes a minimal “approved_action” only when released:true.  
- **Immutable audit (hash-chained, one-line JSON):**  
  - `audits/chain.log` appends compact entries: ts, policy_mode, attestation_type, released, action, result, hash (+ prev_hash on subsequent runs).  
  - Each line is canonicalized and hashed; chain can be verified with `jq` + `sha256sum`.  
- **Policy integrity:**  
  - Policy files are hashed; a lock file should match computed hashes. CI can fail if mismatch.  
- **Cost/attack surface guardrails:**  
  - Container App runs with `minReplicas=0` (scale-to-zero).  
  - `stop-all` script enforces `minReplicas=0` post-demo.  
  - Local assistant uses no cloud by default; `ASSIST_MODE=cloud` is off unless explicitly enabled.  

## Controls (planned/upgradable)
- Switch policy to **sevsnpvm** when SEV-SNP quota is available; fetch a real token from a Confidential VM and re-run the gate.  
- Private endpoints for AI/ML if needed later.  
- Signing audit entries or using append-only storage for stronger tamper resistance.  

## Verifiable Procedures (local)
- **Gate proves control:**  
  ```bash
  ./scripts/run_gate.sh
