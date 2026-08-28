# CEW Document Intelligence v0 → B1.3 Adoption

Status: `ADOPT_AND_CONSTRAIN`  
Program: `CEW-GOAL-01`  
Source branch: `exp/cew-document-intelligence-foundation-v0`  
Source head: `79d64098eeab3c43be10f49500ba4d059798a91c`

## Why this exists

CEW already contains a tested experimental Document Intelligence foundation. B1.3 must reuse that work rather than create a second competing model.

The reusable primitives are:

- immutable source/version identity;
- localized observations with bbox and detector provenance;
- observation states `DETECTED`, `CANDIDATE`, `SUPPORTED`, `VALIDATED`, `REJECTED`;
- graphic conventions with scoped meaning and review state;
- deterministic proposals that require human review;
- explicit prohibition of direct canonical promotion.

## What is adopted

The B1.3 model preserves the semantic sequence:

`SourceVersion -> DocumentFeatureCandidate / GraphicConventionCandidate -> Human Review -> DocumentMap`

and preserves the rule that machine extraction can propose but cannot approve.

## What is not adopted as authority

The experimental SQLite database `.cew/docintel.sqlite3` is reconstructible tooling state only. It does not become a CEW canonical database and it does not replace current F1/F2 registries.

Current authoritative identity remains:

- Source / SourceVersion from current CEW source registries;
- Page from `CEW_PAGE_REGISTRY_v1.csv`;
- PageTransform from `CEW_PAGE_TRANSFORM_REGISTRY_v1.csv`;
- EvidenceRegion from `CEW_EVIDENCE_REGION_REGISTRY_v1.csv`;
- engineering truth from `knowledge/CURRENT_STATE.json` and governed canonical artifacts.

## State semantics

`VALIDATED` in Document Intelligence means only that a document feature or graphic convention has been human-reviewed for the declared document-understanding purpose.

It does **not** mean:

- canonical engineering fact;
- DOC epistemic state;
- structural binding;
- solver eligibility;
- automatic EvidenceRegion creation;
- canonical write authorization.

## B1.3 extension

B1.3 introduces `DocumentMap` as the project-facing aggregation for a drawing/page. It may contain:

- registered metadata already known outside the drawing (source class, project level, source identity);
- human-reviewed document features;
- unresolved/unknown fields;
- links to governed EvidenceRegions;
- candidate machine observations that remain visibly non-authoritative.

No source title, scale, orientation, detail, schedule, exploded reinforcement view, legend, dimension or callout is populated unless supported by a registered source or reviewed observation.

## Anti-drift

- do not infer document semantics from filenames alone;
- do not convert a candidate bbox into an EvidenceRegion automatically;
- do not convert repeated graphic patterns into structural meaning automatically;
- do not treat detector confidence as epistemic authority;
- do not duplicate F1/F2 source/page/evidence identities in a second authority store;
- do not use the experimental SQLite store for Production persistence without a separate migration and security review.
