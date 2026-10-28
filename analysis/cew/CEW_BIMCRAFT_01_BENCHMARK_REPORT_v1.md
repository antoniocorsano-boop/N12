# CEW-BIMCRAFT-01 — Benchmark Report v1

**Data:** 28 ottobre 2026  
**Repository:** `antoniocorsano-boop/N12`  
**PR:** `#164` — Draft  
**Canonical task:** `CEW-B01 — External Tool Qualification / N12 Vertical Slice`  
**Decisione proposta:** `ADOPT_CANDIDATE`  
**Stato BIMCraft:** `BENCHMARK / NONCANONICAL / NOT ADOPTED`  
**Master change authorized:** `false`

## 1. Scopo

Il benchmark verifica se BIMCraft può essere utilizzato da CEW come **motore BIM/IFC parametrico e agentico sostituibile**, mantenendo fuori dal tool l'autorità del progetto.

Ruoli candidati qualificati dallo Stage A:

- `BIM_PROJECTION_ENGINE`;
- `AGENTIC_MODEL_INSPECTION_ENGINE`;
- `IFC_PROJECTION_ENGINE`.

Il benchmark non qualifica BIMCraft come:

- fonte documentale;
- Knowledge Engine o Canonical Structural Model CEW;
- motore FEM;
- verificatore NTC;
- ricostruttore autonomo delle armature;
- sostituto di EdiLus-EE;
- autorità professionale.

## 2. Toolchain congelata

### BIMCraft

- repository upstream: `IPedrax/BIMCraft`;
- release: `v0.9.0`;
- tag object: `8b690b6c98a1b365c3524b126f6a3015371b5479`;
- exact commit: `c7ba8e2db8d7cc9fbf0847f23c8a56c8e02193f5`;
- asset eseguito: `bimcraft-0.9.0-linux-x86_64.tar.gz`;
- SHA-256 asset: `73ba200369b3f9afa95309ff74c1e873d80f27f2c054ddf6df9a0fdeb5cfccd8`;
- eseguibile osservato nel pacchetto: `bin/bimcraft-cli`;
- versione osservata dal binario: `bimcraft-cli 0.9.0`.

### Validatore IFC

- package: `ifcopenshell`;
- versione: `0.9.0.post1`;
- ruolo: `READ_QUERY_VALIDATE_IFC`.

## 3. Evidenza di qualificazione di riferimento

Qualificazione completa di riferimento:

- exact CEW candidate SHA: `058b2794bdd3111a0654f9f57f09026fb3b613db`;
- GitHub Actions run: `40749184019`;
- job: `123030962562`;
- risultato: `SUCCESS`;
- artifact: `12843675684`;
- artifact digest: `sha256:49c23fcfd1e21f4c5bd7a14fd73f754d1e19b97d54d537f804e8a9216d48b179`.

Tutti gli step sono risultati PASS:

1. checkout exact candidate;
2. Python 3.12.15;
3. suite CEW-BIMCRAFT-01;
4. installazione e verifica del validatore IFC congelato;
5. lettura del toolchain lock;
6. verifica digest, versione e catalogo comandi BIMCraft;
7. esecuzione Stage A via MCP;
8. read-back semantico;
9. esportazione e validazione IFC;
10. emissione receipt;
11. upload evidence artifact.

## 4. Fixture Stage A

La fixture è sintetica e dichiaratamente non canonica:

`CEW-BIMCRAFT-01-STAGE-A / BENCHMARK_ONLY`

Oggetti richiesti:

| CEW ID | Oggetto | Geometria/ruolo principale |
| --- | --- | --- |
| `SYN-COL-001` | pilastro strutturale | 400×400, BENCH-L1 → BENCH-L2 |
| `SYN-BEAM-001` | trave | 300×600, 5.000 mm |
| `SYN-FOOT-001` | plinto | 1.200×1.200, spessore 500 mm |
| `SYN-SLAB-001` | solaio strutturale | 5.000×4.000 mm |

I livelli di benchmark sono `BENCH-L1 = 6000 mm` e `BENCH-L2 = 9000 mm`; sono separati dai livelli di default osservati in BIMCraft (`0` e `3000 mm`).

Ogni oggetto trasporta:

- `CEW_OBJECT_ID`;
- `CEW_EVIDENCE_ID`;
- `CEW_SOURCE_SHA256`;
- `CEW_EPISTEMIC_STATE`;
- `CEW_REVISION`;
- `CEW_AUTHORITY`.

Per lo Stage A lo stato epistemico è `RIF` e l'autorità è sempre `BENCHMARK_ONLY`.

## 5. Risultati G0–G5

### G0 — Upstream identity: PASS

Il runner scarica esclusivamente l'asset congelato e verifica il SHA-256 prima dell'esecuzione. Versione osservata: `bimcraft-cli 0.9.0`.

### G1 — Capability contract: PASS per le capacità esercitate

Il catalogo live della release espone le operazioni richieste e il server MCP è stato realmente utilizzato. Le capacità osservate dal receipt sono:

`execute`, `inspect_model`, `list_commands`, `new_model`, `open`, `query_elements`, `render`, `save`, `schedule`, `script`.

Sono state **esercitate** in questa qualificazione: creazione modello, esecuzione dei comandi strutturali, interrogazione, ispezione e salvataggio `.bimcraft`/IFC. La sola presenza di altre capacità nel catalogo non equivale a qualificazione funzionale di tali capacità.

### G2 — Deterministic projection: PASS sul piano semantico

Il `BIMCraftCommandPlan` è canonicalizzato e il suo digest è:

`e1a935f5a132c196eb5e984740dccad0da05ffb18f03e63290d655005d825a04`

Il piano è deterministico a parità di fixture.

**Finding G2-F1 — output nativo non byte-deterministico.** Esecuzioni successive producono GUID/identificatori nativi differenti e quindi digest differenti dei file `.bimcraft` e IFC. CEW non deve usare un digest di output atteso fisso come identità semantica. La regola corretta è:

`input governato + command-plan digest + digest output della singola run + reconciliation semantica`.

### G3 — Read-back: PASS

Ricevuta di riferimento:

- `expected_count = 4`;
- `observed_count = 4`;
- `difference_count = 0`;
- `reconciliation_status = PASS`.

La normalizzazione ha verificato per ogni elemento categoria, livelli, geometria/sezione richiesta e tutti i campi di provenienza.

Binding BIMCraft della run di riferimento non viene assunto stabile tra esecuzioni: gli ID vengono acquisiti dal risultato reale del comando e usati soltanto nella sessione corrente.

### G4 — IFC boundary: PASS

L'IFC prodotto è `IFC4` ed è stato aperto e interrogato con IfcOpenShell `0.9.0.post1`.

Corrispondenze verificate:

- `SYN-COL-001` → `IfcColumn`;
- `SYN-BEAM-001` → `IfcBeam`;
- `SYN-FOOT-001` → `IfcFooting`;
- `SYN-SLAB-001` → `IfcSlab`.

Per tutti e quattro gli elementi:

- `LoadBearing = TRUE`;
- i sei parametri CEW sono presenti nel property set di progetto;
- i valori di provenienza coincidono con la fixture governata.

Digest output della run di riferimento:

- `.bimcraft`: `9980c6707dce059d54e4de98bd62316edcf3a8f4e76141c45fb8c6ffee794208`;
- IFC: `3e040988b311c61730043fb3a27d4612b2aacd64de7f7bd20154475e5bc14bff`.

Questi digest identificano **quella specifica esecuzione** e non sono attesi invarianti fra run.

### G5 — N12 authority boundary: PASS

Il benchmark ha mantenuto:

- `canonical_write_authorized = false`;
- `structural_identity_authorized = false`;
- `fem_authorized = false`;
- `master_change_authorized = false`;
- `n12_stage_b_authorized = false`.

Nessuna coordinata, sezione o identità strutturale N12 è stata creata o promossa dal benchmark.

## 6. Cosa è dimostrato

È dimostrato sul binario reale congelato che CEW può:

1. generare un piano di comandi deterministico da input governato;
2. pilotare BIMCraft tramite MCP senza simulazione dell'interfaccia grafica;
3. acquisire gli ID reali restituiti dal motore senza predirli;
4. applicare metadati CEW agli elementi creati;
5. interrogare nuovamente il modello;
6. riconciliare semanticamente modello osservato e fixture;
7. salvare una proiezione `.bimcraft`;
8. esportare IFC4;
9. ritrovare nell'IFC le classi strutturali e la provenance CEW;
10. produrre una receipt fail-closed senza escalation di authority.

Questo rende BIMCraft tecnicamente credibile come **motore BIM/IFC rigenerabile dietro un adapter CEW**.

## 7. Cosa non è dimostrato

Restano fuori dal perimetro e non devono essere inferiti dal PASS:

- ricostruzione del modello N12 reale;
- importazione dell'IFC BIMCraft in EdiLus-EE e qualità della traduzione lato EdiLus;
- armature del cemento armato;
- modello analitico strutturale completo;
- carichi e combinazioni;
- FEM;
- verifiche NTC;
- diagnosi dell'esistente;
- progetto degli interventi;
- capacità di `render` come ambiente Human Visual Review qualificato;
- stabilità a lungo termine del formato `.bimcraft`;
- compatibilità automatica con future release BIMCraft.

Ogni futura release deve essere trattata come nuovo candidato con digest/versione e regression qualification propri.

## 8. Stage B N12

Lo Stage B resta **BLOCKED BY GOVERNANCE**, non da un limite tecnico di BIMCraft.

Il gate CEW-B01 corrente richiede input N12 source-bound e human-reviewed prima di autorizzare la materializzazione di identità/geometrie reali. La memoria della conversazione, i risultati storici non ancora ricondotti all'authority corrente o una somiglianza grafica non possono essere usati per aggirare tale gate.

Quando CEW-B01 disporrà di un piccolo set di `StructuralObject` accettati, il pilot corretto sarà:

`Canonical CEW objects -> CEW/BIMCraft adapter -> BIMCraft -> read-back -> IFC -> IfcOpenShell -> reconciliation`.

Solo dopo potrà essere aperto un gate professionale separato:

`IFC BIMCraft -> EdiLus-EE -> verifica di conservazione semantica`.

## 9. Decisione proposta

**Raccomandazione: `ADOPT_CANDIDATE`.**

Significato rigoroso:

- BIMCraft ha evidenza sufficiente per essere sottoposto a decisione umana come **candidato** della toolchain;
- non è ancora `ADOPT` nel Master;
- non sostituisce `build123d` o IfcOpenShell per decreto del benchmark;
- non acquisisce authority CEW;
- non autorizza Stage B N12;
- non autorizza merge della PR #164;
- non autorizza EdiLus/FEM.

La decisione umana futura potrà scegliere fra:

1. adottarlo come `OPTIONAL BIM PROJECTION / AGENTIC AUTHORING ENGINE` dietro adapter CEW;
2. mantenerlo come benchmark alternativo a OpenCADStudio/FreeCAD;
3. rinviare l'adozione fino allo Stage B N12.

Sulla base dello Stage A, non emerge una ragione tecnica per `REJECT`; la salvaguardia necessaria è mantenere CEW come unica autorità e considerare i file BIMCraft/IFC proiezioni rigenerabili.

## 10. Stato finale del benchmark v1

`STAGE_A = QUALIFIED`  
`G0 = PASS`  
`G1 = PASS_FOR_EXERCISED_CAPABILITIES`  
`G2 = PASS_SEMANTIC / BYTE_OUTPUT_NONDETERMINISTIC`  
`G3 = PASS`  
`G4 = PASS`  
`G5 = PASS`  
`STAGE_B_N12 = BLOCKED_BY_EXISTING_HUMAN_GATE`  
`RECOMMENDATION = ADOPT_CANDIDATE`  
`MASTER_CHANGE_AUTHORIZED = false`  
`MERGE_AUTHORIZED = false`
