# CEW MASTER AMENDMENT — BIMCraft 01

**Data:** 28 ottobre 2026  
**Riferimento:** `CEW MASTER PLAN — Civil Existing Workflow — Canonical Roadmap & External Toolchain`  
**Decisione umana:** `ADOPT_OPTIONAL`  
**Benchmark di supporto:** `CEW-BIMCRAFT-01`  
**Stato:** CANONICAL AMENDMENT — pending integration

## 1. Oggetto dell'emendamento

Il presente emendamento integra la toolchain esterna canonica CEW con **BIMCraft** sulla base del benchmark governato `CEW-BIMCRAFT-01` e della successiva decisione umana di adozione.

La decisione non modifica il principio fondamentale del Master: **CEW resta l'autorità su conoscenza, identità, provenienza e stato dei dati; gli strumenti esterni restano motori sostituibili.**

## 2. BIMCraft

### BIMCraft
**Stato: ADOPT — OPTIONAL BIM PROJECTION / AGENTIC AUTHORING ENGINE**

Versione qualificata per CEW:
- release: `v0.9.0`;
- upstream commit: `c7ba8e2db8d7cc9fbf0847f23c8a56c8e02193f5`;
- asset eseguito: `bimcraft-0.9.0-linux-x86_64.tar.gz`;
- SHA-256: `73ba200369b3f9afa95309ff74c1e873d80f27f2c054ddf6df9a0fdeb5cfccd8`;
- eseguibile: `bin/bimcraft-cli`.

Ruoli adottati:
- motore opzionale di proiezione BIM;
- ambiente opzionale di authoring parametrico agentico;
- motore opzionale di interrogazione/ispezione del modello tramite MCP;
- motore opzionale di proiezione IFC.

Catena autorizzata:

`CEW Canonical Model → CEW/BIMCraft Adapter → BIMCraft → read-back → semantic reconciliation → IFC projection → IfcOpenShell validation`

## 3. Precedenza nella toolchain

L'adozione di BIMCraft **non sostituisce** gli strumenti già adottati nel Master:

- `CEW Canonical Model` resta l'unica autorità del modello CEW;
- `build123d` resta l'**adapter geometrico primario** per la Canonical Geometry;
- `OpenCascade/OCP` resta il kernel geometrico di fondazione;
- `IfcOpenShell` resta il componente adottato per lettura, interrogazione, manipolazione e validazione IFC;
- BIMCraft è un **motore di proiezione sostituibile e opzionale** dietro adapter CEW.

Né i file `.bimcraft` né gli IFC generati da BIMCraft diventano fonte canonica CEW.

## 4. Regola di assurance

Il benchmark ha dimostrato che il piano di comandi CEW→BIMCraft può essere deterministico, mentre gli output nativi possono variare a livello byte per GUID e identificatori generati dal motore.

Per ogni esecuzione CEW con BIMCraft sono quindi obbligatori:

1. input CEW governato;
2. versione e digest dell'asset BIMCraft;
3. digest del command plan;
4. digest degli output della singola esecuzione;
5. read-back del modello;
6. riconciliazione semantica CEW↔BIMCraft;
7. validazione IFC con componente qualificato;
8. receipt finale fail-closed.

Il digest dell'output, da solo, **non costituisce identità semantica del modello**.

## 5. Politica delle versioni

L'adozione è riferita alla versione qualificata `v0.9.0`.

Ogni release successiva di BIMCraft è un **nuovo candidato** e deve superare una regression qualification CEW prima di essere utilizzata nei run governati. Gli aggiornamenti automatici non sono autorizzati nei run CEW.

## 6. Confini di autorità

L'adozione non autorizza:

- scrittura automatica nel Canonical Model;
- promozione autonoma dell'identità strutturale;
- inferenza di geometrie o proprietà N12 non source-bound;
- FEM;
- verifiche NTC;
- ricostruzione automatica delle armature;
- importazione EdiLus-EE considerata automaticamente qualificata;
- progetto o diagnosi professionale autonoma.

Restano quindi:

- `canonical_write_authorized = false`;
- `structural_identity_authorized = false`;
- `fem_authorized = false`;
- `n12_stage_b_authorized = false`.

## 7. N12 Stage B

L'adozione dello strumento **non sblocca Stage B**.

La proiezione della geometria reale N12 attraverso BIMCraft può iniziare soltanto quando il gate CEW-B01 dispone di un piccolo insieme di `StructuralObject` reali:

- source-bound;
- geometricamente espliciti;
- human-reviewed;
- con provenienza e stato epistemico governati.

A quel punto il pilot corretto sarà:

`StructuralObject CEW accettati → CEW/BIMCraft Adapter → BIMCraft → read-back → IFC → IfcOpenShell → reconciliation`

L'eventuale catena successiva:

`IFC BIMCraft → EdiLus-EE`

richiede un **gate professionale separato di conservazione semantica**.

## 8. Effetto sul Master

A integrazione del presente emendamento, BIMCraft deve essere considerato parte della toolchain esterna CEW con stato:

`ADOPT — OPTIONAL BIM PROJECTION / AGENTIC AUTHORING ENGINE`

L'emendamento non cambia il Current Task canonico `CEW-B01` e non apre nuovi fronti FEM o solver.
