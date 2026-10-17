# ETW-1 GATE REPORT — eTwin Document Engine Core

**Gate:** ETW-1  
**Date:** 2026-08-17  
**Status:** ✅ PASS  
**Baseline:** d521f11  
**Version:** ETW-SPEC v1.1  

---

## 1. Summary

ETW-1 demonstrates the complete document chain from a large-format raster PDF through adaptive tessellation → persistent reading → evidence crops → eTwin entity/candidate binding → multi-criteria verification → exact return to original region.

The terrace region of TAV-05S (carpenteria G4) serves as the proof case.

---

## 2. Source Rendering Fidelity Gate (Task 0)

| Check | Result |
|---|---|
| PDF opens | ✅ PASS |
| Page dimensions valid | ✅ PASS (594×1061mm, A0 format) |
| 300 DPI renders without error | ✅ PASS (7016×12530 px) |
| 600 DPI renders without error | ✅ PASS (14031×24895 px) |
| Crops produce valid images | ✅ PASS |
| Coordinate round-trip | ✅ PASS (pixel ↔ PDF ↔ pixel identical) |
| Quality degradation < 5 LSB | ✅ PASS (mean 0.37 LSB) |

**Engine:** pypdfium2 (Chrome PDFium)  
**Verdict:** PASS — no information loss in rendering pipeline

---

## 3. Document Registry (Task 2)

18 OriginalDocuments loaded from manifest. All SHA256 verified.

| ID | Type | Pages | Size |
|---|---|---|---|
| TAV-01S | carpenteria_strutturale | 1 | 657K |
| TAV-02S | carpenteria_strutturale | 1 | 645K |
| TAV-03S | carpenteria_strutturale | 1 | 547K |
| TAV-04S | carpenteria_strutturale | 1 | 612K |
| TAV-05S | carpenteria_strutturale | 1 | 727K |
| TAV-06S | carpenteria_copertura | 1 | 647K |
| ... | (+ 12 more) | | |

---

## 4. Document Map (Task 3)

**TAV-05S DocumentMap:**
- 2 semantic regions: PLAN + TITLE_BLOCK
- 28 tiles at 300 DPI (~2000px each)
- 10% deterministic overlap between adjacent tiles
- All tiles rendered and persisted as PNG

---

## 5. Persistent Reading State (Tasks 4, 8)

**Proof of non-loss:**
1. Analyze 5 tiles → save state
2. Reload from disk → all 5 observations byte-identical
3. Analyze 3 more tiles → save
4. Reload → all 8 observations present, Phase 1 data untouched

**State file:** `docs/FOGLIO_LAVORO/etwin_crops/TAV-05S/reading_state.json`

---

## 6. Terrace Evidence Crops (Task 5)

15 evidence crops generated from TAV-05S at 300 DPI:

| Evidence ID | Description | Type |
|---|---|---|
| EV-TERRACE-OVERVIEW | Terrace region overview | Region |
| EV-CARTIGLIO | Title block | Reference |
| EV-LEVEL-LABEL | Level/impalcato label | Reference |
| EV-PILLAR-N002 | Pillar N002 annotation | Confirmed |
| EV-PILLAR-N005 | Pillar N005 annotation | Confirmed |
| EV-PILLAR-N039 | Pillar N039 annotation | Confirmed |
| EV-PILLAR-N041 | Pillar N041 annotation | **Candidate** |
| EV-SLAB-TERRACE | Terrace slab region | Region |
| EV-DETAIL-STRUCT | Structural detail | Detail |
| EV-DIM-01..03 | Dimension annotations | Reference |
| EV-BEAM-01..03 | Beam labels | Reference |

All crops have `bboxNative + bboxNormalized + pixelCoords`.

---

## 7. Entity/Candidate Binding (Task 6)

### Confirmed Entities

| Entity | Type | Identity | Position (mm) | Vertical | Termination |
|---|---|---|---|---|---|
| N002 | Column | CONFIRMED | x=36481, y=12234 | G1→G5 | continues_above |
| N005 | Column | CONFIRMED | x=36484, y=7840 | G1→G5 | continues_above |
| N039 | Column | CONFIRMED | x=35456, y=3226 | G1→G5 | continues_above |

### Candidate (NOT StructuralEntity)

| Candidate | Type | Status | Blocking Residual |
|---|---|---|---|
| N041_CANDIDATE | Column | CANDIDATE | R-R1-01 |

**N041 is NOT promoted to StructuralEntity.** Identity gap R-R1-01 is active.

### Chain Demonstration

```
StructuralEntity N002
  → Property: verticalTermination = continues_above
    → Claim: CLM-N002-TERM
      → Evidence: EV-PILLAR-N002
        → Crop: EV_PILLAR_N002_CONFIRMED.png
          → Document: TAV-05S (archive/documentazione_originaria/tavola 5.pdf)
```

---

## 8. Multi-Criteria Verification (Task 7)

### Verification Matrix

| Entity | EVID | SPAT | IDEN | PROP | SOUR | STATUS |
|---|---|---|---|---|---|---|
| N002 | PASS | PASS | PASS | PASS | PASS | **MATCH** |
| N005 | PASS | PASS | PASS | PASS | PASS | **MATCH** |
| N039 | PASS | PASS | PASS | PASS | PASS | **MATCH** |
| N041 | PASS | PASS | **FAIL** | PASS | PASS | **PARTIAL_MATCH** |

**Criteria:**
- EVIDENCE_EXISTS: crop exists on disk
- SPATIAL_ALIGNMENT: crop spatially aligned with entity position
- IDENTITY_MATCH: crop confirms entity identity (N041 FAILS — candidate only)
- PROPERTY_SUPPORT: crop supports claimed property value
- SOURCE_CONSISTENCY: no conflicting claims from other sources

**N041 correctly fails IDENTITY_MATCH** — it is a DocumentEntityCandidate, not a confirmed StructuralEntity.

---

## 9. Knowledge Persistence

| Check | Result |
|---|---|
| Phase 1 data survives reload | ✅ PASS (byte-identical) |
| Phase 3 data appended correctly | ✅ PASS |
| No Phase 1 observations lost | ✅ PASS |
| No Phase 1 claims lost | ✅ PASS |

---

## 10. Residuals

| ID | Status | Note |
|---|---|---|
| R-R1-01 (N041 identity) | ACTIVE | N041 remains CANDIDATE until pillar type resolved |
| R-R1-03 (N005 orphan) | IDENTIFIED | Beams at G1 missing from canonical model |

---

## 11. ETW-1 PASS Criteria Verification

| # | Criterion | Status |
|---|---|---|
| 1 | 1 OriginalDocument loaded with SHA256 | ✅ |
| 2 | DocumentMap persistente with semantic regions | ✅ |
| 3 | At least 1 SemanticRegion | ✅ (2: PLAN + TITLE_BLOCK) |
| 4 | Adaptive tessellazione ad alta risoluzione | ✅ (28 tiles, 300 DPI) |
| 5 | Lettura interrompibile/riprendibile | ✅ (proven in Tasks 4, 8) |
| 6 | Observation recorded with coordinates and method | ✅ |
| 7 | Claim generated from observation | ✅ |
| 8 | EvidenceCrop with bboxNative + bboxNormalized | ✅ (15 crops) |
| 9 | PropertyResolution linking entity → crop → PDF | ✅ (4 resolutions) |
| 10 | eTwin entity/candidate — confirmed + candidate | ✅ (3 + 1) |
| 11 | VerificationResult with multi-criteria | ✅ (5 criteria) |
| 12 | Exact return to original region | ✅ (crop paths trace to PDF) |
| 13 | Knowledge persistence — no loss | ✅ |
| 14 | No automatic promotion — N041 remains candidate | ✅ |
| 15 | Working tree clean | ✅ |
| 16 | Gate report complete | ✅ (this document) |

---

## 12. Verdict

**ETW-1: PASS**

All 16 PASS criteria satisfied. The complete document chain is demonstrated:

```
Large PDF (594×1061mm)
  → DocumentMap (2 regions, 28 tiles)
    → Adaptive tessellation (300 DPI, 10% overlap)
      → Persistent reading state
        → 15 EvidenceCrops
          → 3 StructuralEntities + 1 Candidate
            → 4 PropertyResolutions
              → 4 VerificationResults (3 MATCH, 1 PARTIAL_MATCH)
                → Exact return to original PDF region
```

No canonical data modified. No ND/INF promoted to DOC. N041 remains candidate.

---

## 13. Files Generated

| Path | Purpose |
|---|---|
| `model/etwin/document_engine.py` | Data model (16 dataclasses) |
| `model/etwin/document_registry.py` | Registry loader (18 documents) |
| `model/etwin/document_map.py` | Adaptive map generator |
| `model/etwin/reading_state.py` | Persistent state manager |
| `model/etwin/terrace_probe.py` | Terrace evidence crops |
| `model/etwin/entity_binding.py` | Entity/candidate binding |
| `model/etwin/verification.py` | Multi-criteria verification |
| `model/etwin/persistence_proof.py` | Knowledge persistence proof |
| `docs/FOGLIO_LAVORO/etwin_crops/TAV-05S/` | Document map + tiles + state |
| `docs/FOGLIO_LAVORO/etwin_crops/terrace_evidence/` | 15 evidence crops |
| `docs/FOGLIO_LAVORO/etwin_crops/Task0_fidelity/` | Rendering fidelity results |
