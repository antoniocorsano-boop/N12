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

## 5. Orfani e incompletezze che impedivano C01-T11 PASS nella qualifica iniziale

La qualifica del 12 ottobre 2026 registrava tre residui:

1. `SolverRun` e `Result` non esercitabili perché `calculation_model_ready=false`;
2. `Wall` elencato tra i tipi minimi senza caso N12 autonomo;
3. `ModelGeneration` giustificato concettualmente ma non formalizzato come evento riproducibile.

Per questo la qualifica iniziale conservava **C01-T11 = REVIEW_REQUIRED**.

## 6. Decisione di audit iniziale

Il nucleo concettuale risultava sostenuto da molti casi N12 reali, ma la minima sufficienza non era ancora dichiarabile. Nessuna entità era stata eliminata automaticamente.

## 7. Closure audit — 13 ottobre 2026

Autorità aggiuntiva: `docs/superpowers/specs/2026-10-13-cew-contract-01-closure-design.md`.

La closure separa il contratto logico dalla futura estensione FEM:

- `CEW-CONTRACT-01` qualifica il core fino a `ModelGeneration → Projection → Verification → Receipt`;
- `CEW-FEM-01` resta obbligatorio per `ModelGeneration → SolverRun → Result → Verification → Receipt`.

Questa separazione non elimina `SolverRun` o `Result` dal lessico CEW; elimina soltanto la dipendenza circolare che li rendeva requisito operativo del gate C01 prima della qualifica del solver.

### 7.1 Tassonomia macchina

La classificazione corrente è congelata in:

`evidence/cew-contract-01/CEW_STRUCTURAL_TYPE_MINIMALITY_v1.csv`

Regole:

- `CORE_REQUIRED` — subtype effettivamente istanziato e necessario nel caso N12 del gate;
- `SUPPORTED_EXTENSION` — subtype legittimo del contratto, ma non necessario per il PASS del gate corrente;
- `DEFERRED` — subtype non ancora definito/qualificato.

Nel gate corrente sono `CORE_REQUIRED` soltanto:

- `Node`;
- `Column`;
- `Beam`;
- `FoundationElement`.

Sono provati dal grafo strutturale reale di CASE_12; `Beam` è inoltre esercitato indipendentemente da CASE_04.

`Wall = SUPPORTED_EXTENSION`: non viene rimosso dalla tassonomia CEW e non viene fittiziamente istanziato in N12.

Gli altri subtype della specifica restano `SUPPORTED_EXTENSION` quando il patrimonio N12 ne dimostra la legittimità concettuale ma questa closure non necessita di una loro identità StructuralObject autonoma.

### 7.2 ModelGeneration

CASE_12 sostituisce la precedente giustificazione puramente concettuale con una prova reale:

- source commit `d806dcca72779b5a186defe557a7a9b739575a90`;
- workflow run `32955421352` PASS;
- artifact `9601773275`;
- output JSON SHA-256 `4e1c3f341093e9b60670099802bdee0c5fcdc174b12aedb63922f49301a965b2`;
- sei input con SHA-256 registrati;
- receipt di qualificazione separata da qualsiasi risultato ingegneristico;
- `solver_authorized=false` e `calculation_model_ready=false`.

`ModelGeneration` è quindi `JUSTIFIED_REAL` nel perimetro CEW-CONTRACT-01.

### 7.3 Esito minimalità aggiornato

I tre residui del paragrafo 5 sono ora trattati senza artifici:

- SolverRun/Result → debito esplicito e obbligatorio di CEW-FEM-01, non requisito operativo C01;
- Wall → `SUPPORTED_EXTENSION`;
- ModelGeneration → caso reale CASE_12.

**Esito closure minimality:** idoneo a `C01-T11 = PASS`, subordinatamente al validator exact-head e al gate finale 11/11.
