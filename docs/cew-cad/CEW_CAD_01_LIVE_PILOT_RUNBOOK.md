# CEW-CAD-01 — Live Pilot Runbook

**Status:** READY FOR OPERATOR REVIEW — LIVE PILOT NOT EXECUTED  
**Scope:** disposable laboratory DWG only  
**Forbidden:** canonical N12 drawings, baseline/issued paths, overwrite, direct model access to `ocs_execute`, private signing key inside the MCP/agent process.

## 1. Purpose

This runbook executes the first real OpenCADStudio benchmark for CEW-CAD-01 without promoting OpenCADStudio to an adopted CEW component.

The live sequence is intentionally split into two processes:

1. `prepare` — read-only preflight + governed Changeset creation;
2. human `approve` — external Ed25519 signature using a private key unavailable to the agent;
3. `execute` — exact approved Changeset only, technical verification, then new verified copy.

No live step is authorized merely because this document exists.

## 2. Preconditions

All items below are mandatory before `prepare`:

- Windows workstation with Python 3.12;
- repository checked out at the exact qualified CEW-CAD-01 head selected for the pilot;
- dependencies installed from `requirements/cew-cad.lock`;
- OpenCADStudio executable present locally;
- SHA-256 of the OpenCADStudio executable calculated independently and recorded;
- one **disposable lab DWG copy** placed strictly under the configured `02_working/` root;
- SHA-256 of that lab DWG calculated before opening it;
- lab DWG is not an N12 canonical, baseline or issued artifact;
- OpenCADStudio has exactly one usable MCP session;
- the active OpenCADStudio document is exactly that lab copy;
- no CAD command/dialog is waiting for user input;
- CEW workspace zones exist exactly as required by `CEW_CAD_POLICY_v1.json`;
- Ed25519 public key is available to the Gateway process;
- Ed25519 private key is stored outside the agent/MCP process and outside the repository;
- at least one lab-only Evidence ref, Claim ref and Decision ref have been allocated;
- the operator has reviewed the intended polyline points and confirms they are disposable pilot geometry.

## 3. Absolute stop conditions

Stop immediately and do not retry permissively if any of the following occurs:

- OpenCADStudio executable hash mismatch;
- lab DWG hash mismatch;
- active CAD document differs from the governed `02_working/...` lab ref;
- multiple/ambiguous OpenCADStudio sessions;
- required MCP capability missing;
- CAD interactive command/dialog active;
- Changeset digest differs from the signed approval;
- session, document ID, source hash, capability digest or revision changed after proposal;
- requested path escapes the governed workspace;
- an output path already exists;
- any unrelated entity changes;
- geometry/kernel verification fails;
- audit indicates target incompatibility or loss;
- verified save fails semantic verification;
- original lab DWG SHA-256 changes;
- any step asks for a private signing key inside `serve`, MCP, OpenCode, ChatGPT, Codex or another agent process.

A stop condition means **FAIL / investigate**. It never authorizes changing policy to make the run pass.

## 4. Install exact dependencies

From the repository root:

```powershell
py -3.12 -m pip install -r requirements/cew-cad.lock
```

Do not upgrade individual packages during the pilot.

## 5. Establish trusted hashes

Record independently:

```powershell
Get-FileHash "C:\Path\OpenCADStudio.exe" -Algorithm SHA256
Get-FileHash "C:\CivilExisting\02_working\cew-cad-lab.dwg" -Algorithm SHA256
```

Use lowercase hexadecimal values in CEW-CAD commands.

The original lab hash is a hard invariant throughout the pilot.

## 6. Phase A — read-only prepare

Example only; replace paths, hashes and lab governance references with the reviewed values:

```powershell
py -3.12 scripts\cew_cad_lab_acceptance.py prepare `
  --workspace-root "C:\CivilExisting" `
  --policy "governance\cew-cad\CEW_CAD_POLICY_v1.json" `
  --ocs-executable "C:\Path\OpenCADStudio.exe" `
  --ocs-sha256 "<64-hex>" `
  --approval-public-key "C:\CEW-keys\cew-cad-public.pem" `
  --lab-dwg-ref "02_working/cew-cad-lab.dwg" `
  --expected-source-sha256 "<64-hex>" `
  --target-version "2018" `
  --changeset-id "CEW-CAD-LAB-001" `
  --evidence-ref "LAB-E-001" `
  --claim-ref "LAB-C-001" `
  --decision-ref "LAB-D-001" `
  --point "0,0" `
  --point "4000,0" `
  --point "4000,3000" `
  --point "0,3000"
```

Expected state:

- no CAD mutation;
- source hash unchanged;
- status/audit/capture acquired;
- a `cew.cad.changeset.v1` stored under the governed Changeset area;
- `target/cew-cad-01/<timestamp>/pilot-result.json` records `PREPARED_READ_ONLY`;
- next gate is `HUMAN_SIGNED_APPROVAL_REQUIRED`.

Do **not** proceed if the observed Changeset is not exactly the intended lab action.

## 7. Phase B — human-only approval

Run this separately from the agent/MCP process. The private key must not be supplied to `serve` or to `cew_cad_lab_acceptance.py`.

```powershell
py -3.12 -m cew_cad_gateway.cli approve `
  --workspace-root "C:\CivilExisting" `
  --policy "governance\cew-cad\CEW_CAD_POLICY_v1.json" `
  --changeset-id "CEW-CAD-LAB-001" `
  --private-key "C:\CEW-keys-private\cew-cad-private.pem" `
  --approval-id "CEW-CAD-APP-LAB-001" `
  --approved-by "human-operator"
```

Before signing, the human operator must review the exact Changeset digest and current CAD state.

Approval is short-lived and single-use. If the CAD revision/session changes, generate a new Changeset and a new approval rather than reusing the old one.

## 8. Phase C — execute, verify, verified save

Execution requires the literal confirmation `CEW-LAB-ONLY`:

```powershell
py -3.12 scripts\cew_cad_lab_acceptance.py execute `
  --workspace-root "C:\CivilExisting" `
  --policy "governance\cew-cad\CEW_CAD_POLICY_v1.json" `
  --ocs-executable "C:\Path\OpenCADStudio.exe" `
  --ocs-sha256 "<64-hex>" `
  --approval-public-key "C:\CEW-keys\cew-cad-public.pem" `
  --lab-dwg-ref "02_working/cew-cad-lab.dwg" `
  --expected-source-sha256 "<64-hex>" `
  --target-version "2018" `
  --changeset-id "CEW-CAD-LAB-001" `
  --approval-id "CEW-CAD-APP-LAB-001" `
  --confirm-lab-mutation "CEW-LAB-ONLY"
```

The runner must:

1. bind to the exact current session/document/revision;
2. re-check the lab file hash and OpenCADStudio executable hash;
3. load the stored Changeset and externally signed Approval;
4. execute one CEW-LAB polyline operation only;
5. use the deterministic request ID/retry policy;
6. resolve the new concrete CAD entity from `NEW:Polyline`;
7. verify geometry with the CAD kernel;
8. detect unrelated entity changes;
9. capture visual evidence and run target-aware audit;
10. call `save_verified` only after technical PASS;
11. create a **new** file under `06_verified/`;
12. verify the original lab SHA-256 is unchanged;
13. emit the complete receipt chain.

## 9. Evidence to retain

Retain together:

- exact repository commit SHA;
- OpenCADStudio executable path and SHA-256;
- reported OpenCADStudio build/version;
- capability digest;
- original lab DWG path and SHA-256;
- Inspection Receipt;
- Changeset and digest;
- signed Approval Receipt and digest;
- Change Receipt;
- Technical Verification Receipt;
- capture/diff evidence;
- target-aware audit evidence;
- Verified Copy Receipt;
- verified-copy SHA-256;
- final original lab SHA-256;
- `target/cew-cad-01/<timestamp>/pilot-result.json` from prepare and execute.

Do not commit private keys or disposable DWG files.

## 10. Post-pilot decision

A technically successful run does **not** automatically:

- promote OpenCADStudio from `BENCHMARK CANDIDATE` to `ADOPT`;
- promote the verified copy to CEW baseline or issued artifact;
- authorize use on N12 canonical drawings;
- reopen CEW-B01 or change the WIP without a separate governance decision.

After the run, update `CEW_CAD_TOOLCHAIN_v1.json` with exact observed identities and complete the qualification report against all 17 acceptance criteria.
