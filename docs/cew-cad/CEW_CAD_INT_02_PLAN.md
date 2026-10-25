# CEW-CAD-INT-02 — Live Verification and Capability Identity Repair

Base exact SHA: `d8b7c8666b625e8f2a530f355e286ab5a4b836ba`

Origin: CEW-CAD-LAB-005 / Issue #159 — REWORK.

## Observed defects

1. `VerificationService.verify()` emits an inspection request with `handles` and `detail`; `OpenCADStudioAdapter` rejects those fields before calling OCS, producing `OCS_INSPECT_FIELD_NOT_AUTHORIZED`.
2. `OpenCADStudioAdapter.status()` currently computes `CapabilityIdentity.capabilities_sha256` from the whole raw OCS `op=capabilities` payload. LAB-005 observed a digest change on the same OCS build, blocking non-mutating recovery with `CAD_CAPABILITY_IDENTITY_MISMATCH`.

## Repair sequence

### Task A — inspection contract

1. Add a causal RED reproducing the real VerificationService → adapter request.
2. Determine the exact OCS query shape accepted by the real bridge; do not whitelist arbitrary fields without evidence.
3. Implement the smallest adapter/verification translation that permits exact-handle geometry inspection.
4. Keep unknown fields fail-closed.
5. Run focused and full CEW-CAD suites.

### Task B — capability identity

1. Add a read-only diagnostic that records two raw `op=capabilities` payloads and their canonical diff without mutation.
2. Classify every differing field as authoritative or non-authoritative/volatile from observed contract evidence.
3. Define a canonical semantic capability identity only from validated, security-relevant capability data and governed tool availability.
4. Add RED/GREEN tests proving non-authoritative drift does not change identity.
5. Add counter-tests proving real capability loss/change fails closed or changes identity.
6. Do not weaken executable hash, build, session, document, source-hash, approval, revision, or workspace checks.

### Task C — qualification

1. Full CEW-CAD suite PASS.
2. Compile PASS.
3. Windows durability PASS.
4. Gate Authority Task 9 PASS.
5. Gate Authority Bootstrap PASS.
6. Independent review PASS.
7. Leave PR Draft/unmerged.

## Governance

- LAB-005 remains frozen as REWORK evidence.
- No second `execute` for LAB-005.
- No recovery retry until this repair is qualified and separately authorized.
- No LAB-006 authorization.
- No merge, deploy, OpenCADStudio `ADOPT`, CEW-FEM, or canonical N12 CAD mutation.
- No private signing key exposure.
