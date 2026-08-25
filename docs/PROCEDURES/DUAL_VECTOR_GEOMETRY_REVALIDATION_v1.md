# Dual Vector Geometry Revalidation v1

## Scope

This procedure adds an independent geometric corroboration path for native PDF drawings using **PyMuPDF** and **Docling Parse** in parallel.

It is deliberately **validation-only**. M0-G is frozen. This procedure does not reopen, rewrite, renumber or automatically promote any canonical geometry.

## Epistemic rule

The two extractors are software readers of the same primary source. Their agreement increases confidence in a geometric reading but does not create documentary authority by itself.

Therefore:

- original immutable PDF remains the source authority;
- extractor agreement is `DERIVED_REVIEW_EVIDENCE`;
- no `DOC` or `MIS` promotion is automatic;
- disagreement triggers claim-scoped source review;
- frozen M0-G can only be affected through the formal claim-scoped `M0G-REOPEN` mechanism.

## Initial N12 scope

The first candidate sheets are:

- TAV-03S;
- TAV-04S;
- TAV-05S;
- TAV-06S.

The first high-value claims are the TAV-03S beam/support paths already present in the semantic audit:

- P13-P20;
- P20-P22;
- P22-P26.

These claims are not reopened merely because this procedure exists. The gate is invoked only when a claim has been explicitly selected for revalidation.

## Extraction chain

1. Hash the immutable PDF.
2. Read the same page with PyMuPDF `Page.get_drawings()`.
3. Read the same page with Docling Parse shapes materialized through `ContentConfig`.
4. Reduce both outputs to a common set of line segments in PDF points.
5. Compare page dimensions without allowing scale correction.
6. Test direct and vertical-flip coordinate mappings and record the selected mapping.
7. Match segments by endpoint distance, angle and relative length.
8. Reconstruct line-line intersections and compare their coordinates.
9. Emit a JSON report with extractor versions, source hash, mapping, tolerances, counts, residuals and outcome.
10. Leave canonical data untouched.

## Outcome vocabulary

- `AGREE`
- `PARTIAL`
- `DISAGREE`
- `MISSING_PYMUPDF`
- `MISSING_DOCLING`
- `UNCOMPARABLE`

## Tolerances

The machine-readable contract contains the explicit initial profile. Its status is `PRELIMINARY_CALIBRATION_REQUIRED`.

Current starting values are:

- endpoint distance: 0.75 PDF pt;
- angle difference: 0.5 degrees;
- relative length difference: 0.5%;
- intersection distance: 1.0 PDF pt;
- minimum extracted segment length: 2.0 PDF pt;
- `AGREE`: at least 95% match;
- `PARTIAL`: at least 80% match.

These thresholds are intentionally not an evidence-promotion policy. Before any wider governance use they must be calibrated on N12 regions with already settled source readings.

## Execution

```bash
python scripts/cew_dual_vector_agreement.py --self-test
python scripts/cew_dual_vector_agreement.py \
  --pdf <immutable-source.pdf> \
  --page 1 \
  --output analysis/vector_agreement/<claim-id>.json
```

Required Python packages for source execution:

```text
PyMuPDF
docling-parse>=7.8,<8
```

## Relation to current queue

The active queue item remains `M1E-CALCULATION-MODEL-HANDOFF`. This procedure is an assistive revalidation capability and is not a replacement work item. It must not be used to bypass the six M1E blocking residuals or to manufacture calculation inputs.
