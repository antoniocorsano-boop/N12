# CEW-B01 Beam-Hosted Marker Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a bounded, neutral carrier-first pilot that distinguishes hosted rectangular markers with and without a qualifying local transverse-track pair on exact TAV.5 evidence.

**Architecture:** Reconstruct deterministic `LineTrack`s from the complete G1 `LINE_SEGMENT` census, pair those tracks into `LinearCarrierCandidate`s, then bind frozen C5/C7 rectilinear seeds to carriers and compute a purely graphical transverse-track signature. Do not modify qualified G1 or assign beam/slab semantics.

**Tech Stack:** Python 3.12, stdlib only for the experimental module/tests; GitHub Actions for exact-head qualification.

**Spec:** `docs/experiments/2026-10-30-cew-b01-beam-hosted-marker-design.md`

## Global Constraints

- Scope is limited to C5 and C7 frozen seeds on qualified TAV.5 evidence.
- Use all `LINE_SEGMENT` observations; do not depend on G1 `PARALLEL_LINE_PAIR` completeness.
- Preserve every contributing primitive ID.
- Output order must be deterministic under reversed input.
- `semantic_meaning` must remain `None`.
- `structural_identity_authorized`, `canonical_write_authorized`, `g3_authorized`, and `merge_authorized` must remain `False`.
- No full-corpus promotion and no G1 production modification.

## Review Focus

- Duplicate Hough observations of one physical stroke must not count as multiple transverse tracks.
- A marker near but outside a carrier band must not bind to that carrier.
- A single orthogonal track must not qualify as a transverse pair.
- A valid carrier located after hundreds of unrelated line observations must still be found.
- Multiple plausible carriers around one marker must resolve deterministically without losing provenance.

---

### Task 1: Deterministic line-track reconstruction

**Files:**
- Create: `experiments/cew_b01/beam_hosted_markers.py`
- Create: `tests/cew_b01/test_beam_hosted_markers.py`

**Interfaces:**
- Consumes: G1 primitive mappings with `family`, `geometry`, `feature_signature`, `primitive_id`.
- Produces: `build_line_tracks(primitives: list[dict]) -> list[dict]`.

- [ ] **Step 1: Write failing tests** for horizontal/vertical duplicate collapse, provenance union, reversed-input determinism, and a 300-decoy case proving there is no first-220 spatial cap.
- [ ] **Step 2: Run the focused test module and verify RED** because `beam_hosted_markers` does not exist.
- [ ] **Step 3: Implement minimal deterministic line-track reconstruction** using orientation-separated union of near-collinear overlapping/gapped line intervals.
- [ ] **Step 4: Run focused tests and verify GREEN.**
- [ ] **Step 5: Commit.**

### Task 2: Neutral linear carrier candidates

**Files:**
- Modify: `experiments/cew_b01/beam_hosted_markers.py`
- Modify: `tests/cew_b01/test_beam_hosted_markers.py`

**Interfaces:**
- Consumes: `LineTrack` mappings from Task 1.
- Produces: `build_linear_carriers(tracks: list[dict]) -> list[dict]`.

- [ ] **Step 1: Add failing tests** proving two long parallel tracks with substantial overlap form one carrier, near-coincident duplicate edges do not form a carrier, orthogonal tracks do not pair, and output is deterministic.
- [ ] **Step 2: Run tests and verify causal RED.**
- [ ] **Step 3: Implement minimal carrier pairing** with bounded separation, overlap fraction, separation/overlap ratio, canonical IDs, and full primitive provenance.
- [ ] **Step 4: Run tests and verify GREEN.**
- [ ] **Step 5: Commit.**

### Task 3: Hosted marker and transverse-pair signature

**Files:**
- Modify: `experiments/cew_b01/beam_hosted_markers.py`
- Modify: `tests/cew_b01/test_beam_hosted_markers.py`

**Interfaces:**
- Consumes: primitives, tracks, carriers, frozen marker seed IDs.
- Produces: `build_hosted_marker_candidates(primitives, marker_seed_ids) -> list[dict]`.

- [ ] **Step 1: Add failing tests** for `RECT_ALONE_ON_CARRIER`, `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE`, rejection of a marker outside the carrier, rejection of a single transverse track as a pair, deterministic resolution of multiple carriers, and false authority flags.
- [ ] **Step 2: Run tests and verify causal RED.**
- [ ] **Step 3: Implement marker-to-carrier binding and transverse-track search.** A qualifying transverse track is orthogonal to the carrier, intersects the carrier band, and lies within a local longitudinal window of `2.5 ×` the marker longitudinal span; two distinct deduplicated tracks are required.
- [ ] **Step 4: Run focused tests and verify GREEN.**
- [ ] **Step 5: Commit.**

### Task 4: Exact TAV.5 C5/C7 replay and qualification gate

**Files:**
- Create: `governance/cew-b01/BEAM_HOSTED_MARKER_PILOT_RESULT_v1.json`
- Create: `.github/workflows/validate-cew-b01-beam-hosted-marker-pilot.yml`
- Modify: `docs/experiments/2026-10-30-cew-b01-beam-hosted-marker-design.md`

**Interfaces:**
- Consumes: exact `primitive-census.json` from grammar artifact `12918273768` and frozen C5/C7 seed IDs.
- Produces: deterministic two-case result receipt and exact-head unit gate.

- [ ] **Step 1: Run the implementation twice against the exact 5,633-primitive census** and require byte-identical canonical output.
- [ ] **Step 2: Verify both frozen seeds bind to carriers and inspect their neutral graphical states.** Do not change expected semantics to force a match.
- [ ] **Step 3: Record result receipt** including source SHA, primitive count, seed IDs, carrier/track provenance, neutral states, replay digest, and all authority flags false.
- [ ] **Step 4: Add dedicated GitHub Actions gate** running `tests.cew_b01.test_beam_hosted_markers` on exact PR head.
- [ ] **Step 5: Verify exact-head gate plus Repository Memory Gate.**
- [ ] **Step 6: Commit and update the design doc with the observed result and remaining limitations.**
