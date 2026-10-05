# CEW Open Source Platform Baseline v1

**Stato:** HUMAN_APPROVED — PROGRAM_BASELINE
**Data:** 2026-10-03
**Ambito:** Civil Existing Workflow / CEW-EX
**Scopo:** consolidare una direzione tecnica indipendente da software commerciali obbligatori, mantenendo CEW come autorità su evidenze, identità, provenienza, generazioni, decisioni e tracciabilità.

## 1. Stato verificato del repository

Baseline corrente:

- `main` = `8d2b32a0f7913227b0aa757f27c1ebb7b05180c5`
- merge-base comune delle principali branche sperimentali = `643dc8934ec0c8ac37613ec2880cf9e02f5a9df2`

Riferimenti sperimentali da **riconciliare**, non da fondere integralmente:

- Platform OS: `419ae14f6656875a78eb9dc32c3f11cc5c9b6a8c` — diverged, +1338 / -5 rispetto a `main`;
- Free Review Gate: `b7a25783564c353f0e7aa23775318a3a2d78ea9c` — diverged, +2051 / -5;
- 3D Structural Model Builder: `195a2e4b612f6942630821197ab7a4a2203cfbdb` — diverged, +1101 / -5.

### Decisione di programma

> Le branche sperimentali sono patrimonio tecnico e documentale da inventariare, testare e ricondurre dietro contratti stabili. Non costituiscono automaticamente stato canonico e non devono essere integrate in blocco.

## 2. Principio architetturale

CEW possiede:

- identità strutturali stabili;
- evidenze e provenienza;
- stati epistemici;
- generazioni e versioni;
- decisioni umane;
- contratti di scenario;
- mapping tra entità canoniche e motori esterni;
- ricevute e gate.

I componenti esterni forniscono **motori specialistici sostituibili**:

- parsing/OCR;
- geometria e visione;
- visualizzazione 2D/3D;
- IFC/BIM;
- FEM;
- analisi semantica.

Nessun parser, modello IA, viewer, file IFC o solutore può diventare autorità canonica.

## 3. Politica delle dipendenze

### PERMISSIVE_CORE

Adottabile nel nucleo, previa qualifica tecnica e inventario delle dipendenze:

- Docling / docling-parse — MIT;
- pypdfium2 / PDFium — Apache-2.0 o BSD-3-Clause per pypdfium2; licenze delle dipendenze PDFium da preservare;
- PaddleOCR — Apache-2.0; i modelli vanno verificati singolarmente;
- OpenCV >= 4.5 — Apache-2.0;
- OpenSeadragon — BSD-3-Clause;
- PostgreSQL — PostgreSQL License;
- pgvector — PostgreSQL License;
- NetworkX — BSD-3-Clause;
- Three.js — MIT.

### COPYLEFT_ISOLATED

Utilizzabile dietro confine/adattatore, con verifica delle condizioni di distribuzione:

- IfcOpenShell — LGPL-3.0-or-later;
- Code_Aster — GNU GPL; preferibile come processo/solutore esterno e non come codice incorporato nel nucleo.

### RESTRICTED_OPTIONAL

Non deve essere dipendenza obbligatoria del nucleo:

- PyMuPDF — AGPLv3 oppure licenza commerciale;
- OpenSees / OpenSeesPy — uso non commerciale/ricerca e uso interno consentiti; la distribuzione commerciale richiede verifica/autorizzazione.

### EXTERNAL_COMMERCIAL_OPTIONAL

- EdiLus-EE;
- eventuali CAD/FEM commerciali futuri.

**Regola:** CEW deve restare funzionante nel percorso essenziale senza dipendenze `RESTRICTED_OPTIONAL` o `EXTERNAL_COMMERCIAL_OPTIONAL`.

## 4. Architettura obiettivo

```text
SOURCE
  -> SourceVersion
  -> ProcessingGeneration
  -> Observation / EvidenceRegion
  -> CandidateMeaning / Claim
  -> HumanDecision
  -> CanonicalGeneration
  -> Smart Structural Entity
  -> ScenarioGeneration
  -> SolverAdapter
  -> ResultMapping
  -> Receipt / Dossier
```

Strati funzionali:

1. **Source & Evidence Foundation**
2. **Document Intelligence & Graphic Reconstruction**
3. **Canonical Structural Knowledge / Smart Entity**
4. **2D/3D Evidence Workspace**
5. **IFC Interoperability**
6. **Existing Assessment & Solver Adapters**
7. **Exposure / Degradation / Investigation**
8. **Intervention & Before/After**
9. **Rule Packs / Verifiche normative**
10. **Dossier, reportistica e storico immutabile**

## 5. Cose da non costruire

- un CAD generalista alternativo a SOLIDWORKS;
- un “super-agente” monolitico;
- un database a grafo prima di un bisogno misurato;
- un database vettoriale separato prima di un bisogno misurato;
- un modello IFC come fonte canonica;
- un solutore FEM come fonte canonica;
- assegnazioni automatiche di LC/FC;
- promozioni automatiche da `INF/INC/ND/MOD/POST` a `DOC/MIS`.

## 6. Roadmap di programma

### T0 — CEW-OS-00 · Qualification & Consolidation

**Obiettivo:** congelare la baseline tecnica e legale prima di integrare codice.

Attività:

- inventario delle capability già esistenti nelle branche;
- matrice `capability -> provider -> licenza -> stato -> evidenza -> test`;
- SBOM iniziale;
- classificazione `PERMISSIVE_CORE / COPYLEFT_ISOLATED / RESTRICTED_OPTIONAL / EXTERNAL_OPTIONAL`;
- definizione dei port/adapters stabili;
- selezione dei casi N12 di benchmark;
- piano di estrazione selettiva dalle branche sperimentali.

**Uscita:** stack qualificato e backlog di adozione senza merge massivi.

### T1 — Source -> Evidence vertical slice

Un documento/tavola reale N12 attraversa:

`source -> parse/render -> region -> observation -> candidate -> human review -> approved evidence`

Provider candidati:

- Docling Parse;
- pypdfium2;
- PaddleOCR;
- OpenCV;
- OpenSeadragon.

### T2 — Smart Entity / Canonical Persistence

- ID strutturali stabili;
- proprietà con stato epistemico;
- legami evidence-first;
- PostgreSQL/PostGIS;
- pgvector solo come indice secondario;
- NetworkX per controlli topologici.

### T3 — 3D + IFC

- viewer Three.js;
- selezione oggetto -> evidenza;
- overlay `DOC/MIS/RIF/INF/INC/ND/MOD/POST`;
- export/import IFC tramite IfcOpenShell;
- round-trip degli ID CEW.

### T4 — Open FEM round-trip

Benchmark controllato su N12:

- Code_Aster come solutore open source indipendente;
- OpenSees/OpenSeesPy come adattatore specialistico opzionale;
- eventuale solutore leggero per regressione/smoke test.

Criterio:

`CEW entity -> solver entity -> result -> CEW entity`

senza perdita di identità o provenienza.

### T5 — Existing Assessment / Degradation / Investigation

Consolidare:

- modalità di assessment;
- scenari separati dalla verità canonica;
- degradation registry;
- Investigation Planner / Value of Information;
- uncertainty e sensitivity.

### T6 — Rule Packs & Professional Verification

- NTC/Circolare come rule pack versionati;
- separazione tra output numerico, interpretazione normativa e decisione professionale;
- nessuna “certificazione automatica”.

### T7 — Dossier & Product Release

- fascicolo tecnico riproducibile;
- confronto before/after;
- interventi come nuove generazioni;
- esportazioni verso solutori/CAD commerciali solo opzionali;
- audit trail completo.

## 7. Gate di accettazione

- **G0 License Gate:** nessuna dipendenza obbligatoria con vincoli incompatibili con il modello di distribuzione scelto.
- **G1 Provenance Gate:** ogni dato canonico ha evidenza o regola esplicita.
- **G2 Generation Gate:** una generazione fallita non sostituisce l’ultima valida.
- **G3 Identity Gate:** gli ID CEW sopravvivono a viewer, IFC e solutore.
- **G4 Solver Round-trip Gate:** risultati rimappati senza ambiguità.
- **G5 Reproducibility Gate:** artefatti rigenerabili da input immutabili.
- **G6 Human Authority Gate:** decisioni semantiche e ingegneristiche restano umane.
- **G7 Professional Use Gate:** output di calcolo, normativa e responsabilità professionale restano distinti.

## 8. Prima tranche da specificare

Dopo Human Review di questa baseline, il primo sottoprogetto è:

**CEW-OS-00 — Open Source Capability & License Qualification**

Deve produrre:

1. capability registry machine-readable;
2. license/obligation registry;
3. adapter boundary registry;
4. benchmark matrix N12;
5. decisione motivata per ogni componente;
6. piano di estrazione selettiva dalle branche sperimentali;
7. nessuna promozione automatica di codice o dati canonici.

## 9. Riferimenti verificati da mantenere

### Repository N12

- `main`: `8d2b32a0f7913227b0aa757f27c1ebb7b05180c5`
- Platform OS: `419ae14f6656875a78eb9dc32c3f11cc5c9b6a8c`
- Free Review Gate: `b7a25783564c353f0e7aa23775318a3a2d78ea9c`
- 3D Structural Model Builder: `195a2e4b612f6942630821197ab7a4a2203cfbdb`

### Licenze / fonti ufficiali da riesaminare al gate T0

- PyMuPDF: https://pymupdf.io/licensing
- Docling Parse: https://github.com/docling-project/docling-parse
- pypdfium2: https://github.com/pypdfium2-team/pypdfium2
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- OpenCV: https://opencv.org/license/
- IfcOpenShell: https://github.com/IfcOpenShell/IfcOpenShell
- PostgreSQL: https://www.postgresql.org/about/licence/
- pgvector: https://github.com/pgvector/pgvector
- NetworkX: https://github.com/networkx/networkx
- Three.js: https://github.com/mrdoob/three.js
- OpenSeadragon: https://github.com/openseadragon/openseadragon
- Code_Aster: https://code-aster.org/en/product/main
- OpenSees: https://opensees.berkeley.edu/OpenSees/developer/copyright.php

## 10. Decisioni approvate come baseline di programma

Baseline approvata il 2026-10-03. Restano soggette a verifica tecnica e legale di T0:

- architettura adapter-first;
- divieto di merge massivo delle branche sperimentali;
- classificazione iniziale delle dipendenze;
- priorità `T0 -> T1 -> T2 -> T3 -> T4`;
- mantenimento di EdiLus/SOLIDWORKS come integrazioni opzionali e non come autorità;
- separazione fra motore numerico, regole normative e responsabilità professionale.

## 11. Criterio di arrivo

La soluzione prefigurata è raggiunta quando, su N12, è dimostrato almeno un percorso end-to-end riproducibile e auditabile:

`fonte reale -> evidenza -> Smart Entity -> modello 3D -> proiezione IFC -> scenario FEM -> risultato rimappato -> decisione umana -> fascicolo`

con:

- nessuna dipendenza commerciale obbligatoria;
- nessuna perdita di provenienza;
- nessuna promozione automatica di supposizioni a fatti;
- motori specialistici sostituibili;
- risultati verificabili e rigenerabili.
