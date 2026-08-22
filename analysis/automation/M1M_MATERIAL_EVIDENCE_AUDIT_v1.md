# M1-M Material Evidence Audit v1

Date: 2026-08-22
Work item: `M1M-MATERIAL-EVIDENCE`

## Evidence search

Reviewed the current GitHub knowledge state, previous project file-library artifacts and the newly supplied original calculation-relation page 2 image.

Primary page-2 image fingerprint: `sha256:8728e4d09d5dd3b9c5ce34a5a75bd52dd889e9c55d28991d2b6a35dabdb1a66b`.

### Direct primary evidence recovered

The original calculation relation page 2 directly states:

- structural system made of reinforced-concrete frames arranged longitudinally and transversely, supporting mixed-type slabs;
- frames fixed into inverted foundation beams forming meshes;
- seismic effects evaluated through static analysis;
- frame calculation with KANI data using an Olivetti 652 minicomputer;
- foundation bearing level at 1.00 m below ground level;
- healthy Pliocene soil with historical allowable bearing pressure 1.6 kg/cm²;
- historical foundation coefficient `ε = 1`;
- concrete with characteristic source notation `R' = 300` in the historical kg/cm² material-stress context;
- cement dosage `q.li 3.00`, cement class `425`;
- source-reported concrete tension value `95 kg/cm²`, retained with semantic watch because the historical parameter meaning must not be silently mapped to a modern solver property;
- reinforcing steel `Fe B38k`;
- historical allowable steel stress `2200 kg/cm²`;
- steel described as `controllato in stabilimento`.

Canonical transcription: `data/canonical/ORIGINAL_RELATION_PAGE2_EVIDENCE_v1.csv`.

### Superseded / retained provenance

- The derived preliminary report had previously stated **Rck 250 kg/cm²**. This remains in the evidence ledger only as `RIF / SUPERSEDED_BY_DIRECT_PRIMARY_SOURCE` because the original relation now directly states `R' = 300`.
- The preliminary report also states that original cube tests are reported present and conforming. No numerical cube-test certificate/result has yet been recovered, therefore this remains `RIF`.
- The user confirmation of `FeB38k` is superseded in authority by the direct original-relation designation; the grade is now `DOC`.

### Still unresolved

- Current/in-situ concrete verification strength remains `ND`.
- LC remains `ND` until documentary/investigation coverage is assessed.
- FC remains `ND` as a consequence of the LC decision.
- The normative `fyk = 375 MPa` association with FeB38k remains an `INF/SUPPORTED` historical mapping, not text directly written on this page and not a measured present-state result.
- The exact modern parameter correspondence of the page-2 concrete `95 kg/cm²` statement remains a semantic watch.

## Provenance decision

- Historical concrete primary source notation `R' = 300`: `DOC`.
- Historical cement dosage `q.li 3.00` and cement class `425`: `DOC`.
- Historical concrete source-reported tension `95 kg/cm²`: `DOC_SEMANTIC_WATCH`.
- Reinforcing-steel grade `FeB38k`: `DOC`.
- Historical allowable steel stress `2200 kg/cm²`: `DOC`.
- Steel plant-control statement: `DOC`.
- Reported existence/conformity of original cube tests: `RIF`.
- Existing/in-situ concrete verification strength: `ND`.
- LC: `ND`.
- FC: `ND`.

## Gate decision

`PASS_WITH_WATCH` remains appropriate for the material-evidence inventory. The three calculation-readiness residuals currently carried are current concrete verification strength, LC and FC. Historical source stresses and strength notations remain separated from modern solver properties until an explicit historical-to-current modeling reconciliation is performed.
