# M1-M Material Evidence Audit v1

Date: 2026-08-22
Work item: `M1M-MATERIAL-EVIDENCE`

## Evidence search

Reviewed the current GitHub knowledge state and previous project file-library artifacts for explicit concrete, reinforcing-steel, LC and FC information.

### Positive evidence

- Derived project report `Relazione_preliminare_edificio_CA_Ariano_Irpino.pdf` states that the original calculation relation is reported to specify **Rck 250 kg/cm² (about 24.5 MPa)**.
- The same report states that original cube tests are reported as present and conforming to the design value.
- The preliminary investigation plan treats sclerometry as a future/comparative investigation; no numerical in-situ strength result is available in the reviewed evidence.

### Negative / unresolved evidence

- No explicit original-source steel class/type or `fyk` was found in the reviewed repository/text-search evidence.
- A generated illustrative graphic mentioning FeB grades is explicitly excluded from evidentiary use.
- LC and FC remain undefined until the effective documentary/investigation coverage is assessed.
- The older EdiLus input workbook also records concrete/steel/LC/FC as unresolved and prohibits completion by analogy.

## Provenance decision

- Historical design concrete Rck 250 kg/cm²: `RIF`, not `DOC`.
- Reported existence/conformity of original cube tests: `RIF`, not numerical material characterization.
- Existing/in-situ concrete verification strength: `ND`.
- Reinforcing-steel class and fyk: `ND`.
- LC: `ND`.
- FC: `ND`.

## Gate decision

`PASS_WITH_WATCH` for the **evidence-inventory work item**, with residuals carried forward. This decision does **not** declare materials ready for structural verification; it only permits unrelated M1-A reinforcement mapping to proceed. All unresolved material claims remain mandatory before `CALCULATION_MODEL_READY`.
