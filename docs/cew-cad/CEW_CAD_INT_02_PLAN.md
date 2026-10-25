# CEW-CAD-INT-02 — Live Verification and Capability Identity Repair

Base exact SHA: `d8b7c8666b625e8f2a530f355e286ab5a4b836ba`

Origin: CEW-CAD-LAB-005 / Issue #159 — REWORK.

## Observed defects

1. `VerificationService.verify()` emits an inspection request with `handles` and `detail`; `OpenCADStudioAdapter` rejects those fields before calling OCS, producing `OCS_INSPECT_FIELD_NOT_AUTHORIZED`.
2. `OpenCADStudioAdapter.status()` currently computes `CapabilityIdentity.capabilities_sha256` from the whole raw OCS `op=capabilities` payload. LAB-005 observed a digest change on the same OCS build, blocking non-mutating recovery with `CAD_CAPABILITY_IDENTITY_MISMATCH`.

## Repair sequence

### Task A — inspection contract

1. Add a causal RED reproducing the real VerificationService → adapter request.
2. Use the already-governed exact-handle query shape `op=query` + `handle` when exactly one changed entity has been resolved; do not whitelist arbitrary `handles` / `detail` fields.
3. Implement the smallest VerificationService correction.
4. Keep unknown adapter fields fail-closed.
5. Run focused and full CEW-CAD suites.

### Task B — capability identity

1. Add a read-only diagnostic that records two raw `op=capabilities` payloads and their canonical structural diff without mutation.
2. Capture the real LAB environment payloads on the same OCS build.
3. Classify every differing field as authoritative or non-authoritative/volatile from observed contract evidence.
4. Define a canonical semantic capability identity only from validated, security-relevant capability data and governed tool availability.
5. Add RED/GREEN tests proving non-authoritative drift does not change identity.
6. Add counter-tests proving real capability loss/change fails closed or changes identity.
7. Do not weaken executable hash, build, session, document, source-hash, approval, revision, or workspace checks.

### Task C — qualification

1. Full CEW-CAD suite PASS.
2. Compile PASS.
3. Windows durability PASS.
4. Gate Authority Task 9 PASS.
5. Gate Authority Bootstrap PASS.
6. Independent review PASS.
7. Leave PR Draft/unmerged.

## CI qualification note

PR #161 is normally stacked on `feat/cew-cad-int-01-transaction-recovery`. That base is not currently included in the inherited `pull_request.branches` filter. For causal RED/GREEN evidence only, #161 may be temporarily retargeted to `fix/cew-cad-01-live-contract-repair`, which is an enabled base. A new head commit then triggers qualification. After capturing the run, restore the PR to the INT-01 stacked base. Never interpret the temporary expanded diff as the intended merge scope.

## Governance

- LAB-005 remains frozen as REWORK evidence.
- No second `execute` for LAB-005.
- No recovery retry until this repair is qualified and separately authorized.
- No LAB-006 authorization.
- No merge, deploy, OpenCADStudio `ADOPT`, CEW-FEM, or canonical N12 CAD mutation.
- No private signing key exposure.
