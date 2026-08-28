# CEW Machine Document Candidates v1

Status: `B1.5 PREPARATION`  
Program: `CEW-GOAL-01`

## Purpose

Normalize OCR, vector, raster and AI detections into the B1.3 `DocumentFeatureCandidate` review model without creating a second evidence or engineering authority.

## Reused CEW foundations

1. `exp/cew-document-intelligence-foundation-v0`
   - localized observations;
   - detector provenance and confidence;
   - `DETECTED / CANDIDATE / SUPPORTED / VALIDATED / REJECTED`;
   - human-reviewed proposals;
   - no direct canonical promotion.
2. PR #59 / `exp/vector-concordance-g2-g5`
   - independent PyMuPDF/Docling source diagnostics;
   - independent raster detector chains;
   - consensus candidates;
   - visual-review package;
   - explicit `epistemic_effect: NONE` and promotion prohibition.

These are adopted as candidate-generation patterns, not promoted as authority.

## Candidate pipeline

`registered SourceVersion + READY Page -> detector run -> raw detector observation -> normalized DocumentFeatureCandidate -> review queue -> human document-understanding decision`

The pipeline stops if SourceVersion/Page identity cannot be mapped to current CEW F1/F2 identity.

## Required normalized fields

- candidate_id;
- source_version_id;
- page_id;
- feature_type;
- state (`DETECTED`, `CANDIDATE` or `SUPPORTED` for machine output);
- detector_or_author;
- detector_version;
- created_at;
- bbox normalized to `NORMALIZED_0_1` when localized;
- value_text when applicable;
- confidence when supplied;
- source_basis / raw artifact reference;
- transformation/projection note where detector coordinates differ from Page coordinates.

## Detector families

Supported as adapters, not authorities:

- native PDF text extraction;
- OCR text extraction;
- PDF vector/shape extraction;
- raster line/shape detectors;
- independent detector consensus;
- Scan2DXF candidate geometry;
- multimodal/AI document classification or feature suggestions.

## Critical rules

- machine output can never enter `VALIDATED` directly;
- detector confidence is not epistemic state;
- consensus between detectors is stronger machine support but still not structural truth;
- a detected line is not a beam, axis, grid or member;
- a detected intersection is not a node, column or support;
- OCR text is not automatically a claim or engineering property;
- repeated symbols are not a graphic convention until reviewed;
- candidate bbox is not an EvidenceRegion;
- candidates cannot create structural bindings;
- candidates cannot change DOC/MIS/RIF/INF/ND;
- candidates cannot write canonical engineering data.

## Current B1.5 boundary

B1.5 provides adapter contracts, normalization, provenance and review queues. It does not require CEW Production to run heavyweight OCR/raster libraries inside Vercel. Detector execution may occur in isolated workers/CI/local tooling provided outputs are normalized and provenance-bearing.

## Promotion

B1.5 remains non-promotable until upstream HVA gates are satisfied and the machine-candidate review journey itself passes human-factors/authority acceptance.
