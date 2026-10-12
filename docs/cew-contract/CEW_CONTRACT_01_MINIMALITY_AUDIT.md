# CEW-CONTRACT-01 — Minimality and Technology-Independence Audit

**Date:** 12 ottobre 2026  
**Qualification basis:** `docs/superpowers/specs/2026-10-12-cew-contract-01-design.md` + casi `evidence/cew-contract-01/CASE_01…CASE_10` + branch operativa N12 `work/m0-global-model@d806dcca72779b5a186defe557a7a9b739575a90`.

## 1. Regola di audit

Una entità del contratto V1 è giustificata quando almeno un caso N12 reale o una fixture strettamente ancorata a dati reali dimostra perché CEW deve poterla rappresentare. La presenza nella specifica non vale da sola come prova.

Stati usati qui:

- `JUSTIFIED_REAL` — caso N12 reale disponibile;
- `JUSTIFIED_FIXTURE` — necessità dimostrata con fixture ancorata a patrimonio N12, senza inventare dati tecnici;
- `BLOCKED_INPUT` — concetto necessario ma non ancora esercitabile per mancanza di input tecnico autorizzato;
- `REVIEW_FOR_V1` — tipo/specializzazione non dimostrato come necessario nel gate corrente.

## 2. Entità centrali

| Entity | Audit state | N12 evidence / case | Decision |
|---|---|---|---|
| Source | JUSTIFIED_REAL | `CEW_SOURCE_IDENTITY_REGISTRY_v1.csv`; TAV-05A/TAV-06A con SHA, archive commit e blob | Mantieni V1. |
| Evidence | JUSTIFIED_REAL | `CEW_EVIDENCE_REGION_REGISTRY_v1.csv`; regioni BBOX localizzate | Mantieni V1. |
| Observation | JUSTIFIED_REAL | `CEW_OBSERVATION_REGISTRY_v1.csv`; leggibile/unreadable preservato | Mantieni V1. |
| Claim | JUSTIFIED_REAL | `CANONICAL_REVALIDATION_LEDGER_v1.csv`; CASE_06/07 | Mantieni V1. |
| Conflict | JUSTIFIED_REAL | CASE_06, conflitto TAV-07A ↔ TAV-06S sul supporto 24 | Mantieni V1. |
| Assumption | JUSTIFIED_FIXTURE | CASE_08, scenario storico R'=300 senza promozione canonica | Mantieni V1: necessario per separare scenario da canonico. |
| Decision | JUSTIFIED_REAL | CASE_06/07; decision/reopen rules e rivalidazione | Mantieni V1. |
| CanonicalProperty | JUSTIFIED_REAL | CASE_02/03/07; ND, DOC/INF e revisione di proprietà | Mantieni V1. |
| StructuralObject | JUSTIFIED_REAL | CASE_04; master/geometry ledgers N12 | Mantieni V1. |
| Relationship | JUSTIFIED_REAL | CASE_05; binding topologico concorrente e stati inferenziali | Mantieni V1. |
| CanonicalSnapshot | JUSTIFIED_REAL | `PT_MASTER_PRE_G1G9_SNAPSHOT_20260821.csv` separato da `PT_MASTER_CURRENT.csv`; CASE_07/08 | Mantieni V1. |
| Scenario | JUSTIFIED_FIXTURE | CASE_08; override storico consentito solo come scenario metadata | Mantieni V1. |
| ModelGeneration | JUSTIFIED_FIXTURE | CASE_08; `M0G_GEOMETRY_HANDOFF_v1.json` e `M1E_CALCULATION_MODEL_HANDOFF_v1.json` dimostrano necessità di legare derivati a uno stato congelato, ma non esiste ancora un evento CEW formalizzato con quel nome | Mantieni concetto; forma eseguibile da definire dopo il gate. |
| Projection | JUSTIFIED_REAL | Geometry handoff e calculation-model handoff sono due proiezioni/derivati distinti dallo stesso patrimonio | Mantieni V1. |
| SolverRun | BLOCKED_INPUT | R5 Solver Round Trip `PLANNED`; `calculation_model_ready=false` | Concetto necessario per la catena futura, ma **non qualificato**. |
| Result | BLOCKED_INPUT | nessun risultato strutturale corrente autorizzato | Concetto necessario per l'obiettivo CEW, ma **non qualificato**. |
| Verification | JUSTIFIED_REAL | CASE_10; machine review con esito non autoritativo/REVIEW_REQUIRED | Mantieni V1. |
| Receipt | JUSTIFIED_REAL | `N12_G4_HIRES_MACHINE_REVIEW_RECEIPT_v1.json` | Mantieni V1. |

## 3. StructuralObject subtypes

| Type | Evidence N12 | Audit |
|---|---|---|
| Building | progetto N12 | giustificato |
| StructuralUnit | distinzione corpo principale / torrino scala già presente nel patrimonio documentale | giustificato, ma tassonomia fisica da formalizzare successivamente |
| Level | G1…G5 in `M0G_GEOMETRY_HANDOFF_v1.json` | giustificato |
| Node | analytical node registries / M0-G | giustificato |
| Column | pilastri/vertical column segments | giustificato |
| Beam | telai, beam registries, CASE_04 | giustificato |
| Wall | nessun caso N12 specifico esercitato in questa qualifica | `REVIEW_FOR_V1`: non usarlo per dichiarare minima sufficienza; valutare tipo estensibile o rinvio |
| Slab | `ORIGINAL_RELATION_PAGE2_EVIDENCE_v1.csv`: “Solai del tipo misto” | giustificato come oggetto concettuale, dettaglio rinviato |
| FoundationElement | M1F/M1E foundation topology/handoff | giustificato |
| Section | sezioni di travi/pilastri e section gates | giustificato |
| Material | evidenza storica materiali + blocker M1E-B01 | giustificato |
| Reinforcement | M1A ledgers e CASE_06 | giustificato |
| LoadObject | M1L load model/gates; dati correnti numerici ancora incompleti | giustificato come dominio, non come input solver completo |

## 4. Technology independence

Il contratto logico **non richiede** nessuna delle seguenti tecnologie per esistere o per soddisfare le invarianti già dimostrate:

- PostgreSQL/PostGIS;
- JSON Schema;
- RDF/W3C PROV come serializzazione fisica;
- IFC/IfcOpenShell;
- OpenSees/OpenSeesPy;
- EdiLus-EE;
- Code_Aster;
- CADCraft;
- ezdxf;
- build123d/OpenCascade.

Nel materiale di qualifica tali nomi compaiono solo come strumenti/candidati/proiezioni o decisioni rinviate. Gli ID logici e i casi di Source, Evidence, Conflict, Snapshot, Scenario e Decision restano comprensibili senza di essi.

**Esito indipendenza tecnologica:** `PASS` — conferma `C01-T06`.

## 5. Orfani e incompletezze che impediscono C01-T11 PASS

La minima sufficienza **non è ancora dimostrata integralmente** per tre ragioni:

1. `SolverRun` e `Result` sono entità centrali ma non hanno ancora un caso N12 reale autorizzato; sono `BLOCKED_INPUT`.
2. `Wall` è elencato tra i tipi minimi V1 ma non è esercitato da un caso N12 in questo gate; va deciso se resta tipo core, diventa estensione o viene rinviato.
3. `ModelGeneration` è giustificato concettualmente dagli handoff reali, ma non esiste ancora un evento formalizzato che consenta di provare tutti gli attributi richiesti dalla spec.

Perciò **C01-T11 = REVIEW_REQUIRED**, non PASS.

## 6. Decisione di audit

Il nucleo concettuale è molto più piccolo e sostenuto di quanto sembrasse dalla sola baseline di ricerca: quasi tutte le entità epistemiche, strutturali, di conflitto/versionamento e assurance hanno già analoghi reali nel patrimonio N12 operativo.

Non è però corretto dichiarare il contratto “minimamente sufficiente e completamente qualificato” finché gli orfani sopra non vengono risolti. Nessuna entità viene eliminata automaticamente da questo audit: le decisioni di rinvio/modifica della spec richiedono un successivo atto esplicito.
