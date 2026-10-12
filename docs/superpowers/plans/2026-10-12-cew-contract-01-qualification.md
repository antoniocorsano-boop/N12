# CEW-CONTRACT-01 Qualification Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dimostrare, su casi N12 reali e senza scegliere ancora database/serializzazione/CAD/IFC/solver, che il contratto logico CEW-CONTRACT-01 rappresenta correttamente provenienza, conoscenza, identità strutturale, conflitti, versionamento, scenari e assurance; in mancanza delle evidenze necessarie il gate deve fallire in modo esplicito e tracciato.

**Architecture:** La specifica approvata resta normativa. La qualifica usa un pacchetto di evidenze Markdown separato dal patrimonio canonico N12: una matrice di conformità guida i casi RED→GREEN, ogni caso cita solo dati già presenti nel Registro Master/dataset o fonti originali effettivamente reperite, e nessun artefatto di qualifica modifica `docs/REGISTRO_MASTER.md` o `data/canonical/`. Il risultato finale è un report PASS/NOT_QUALIFIED con blocker verificabili; nessuna tecnologia di persistenza o solver viene promossa implicitamente.

**Tech Stack:** Markdown, Git, dati/documenti N12 esistenti; comandi di verifica con shell/Python standard library soltanto per controlli di struttura e coerenza testuale. Nessuna dipendenza runtime CEW introdotta.

**Spec:** `docs/superpowers/specs/2026-10-12-cew-contract-01-design.md`

## Global Constraints

- Il contratto resta indipendente da database, JSON Schema, RDF, IFC, CAD e solver.
- N12 è caso pilota, non modello concettuale.
- Nessun valore `ND`, `INC` o `INF` viene promosso a `DOC` per completare un caso di test.
- Nessun conflitto N12 viene inventato: se non esiste un caso reale sufficientemente documentato, il test resta `BLOCKED_SOURCE`.
- Nessun SolverRun/Result viene simulato e presentato come risultato tecnico reale: se non è reperibile un artefatto N12 reale, il test end-to-end resta bloccato.
- `docs/REGISTRO_MASTER.md` e `data/canonical/` non vengono modificati durante questa qualifica, salvo una separata decisione esplicita su una correzione fattuale.
- Alias quali `T5`, `G3`, `TAV.5` non diventano tipi o identità primarie CEW.
- Ogni PASS deve indicare evidenza e criterio; assenza di evidenza significa FAIL/BLOCKED, non assunzione.

## Review Focus

1. **Dati mancanti (`ND`)** — devono restare mancanti e non ricevere default impliciti; il caso `SEC-002`/`M0G-002` deve provarlo.
2. **Stati misti (`DOC/INF`)** — `GEO-005` non deve essere appiattito a un unico stato più forte; il caso deve conservare la parte documentale e quella inferenziale.
3. **Identità fisica vs alias/documenti** — lo stesso elemento deve mantenere un CEW object ID di riferimento anche quando è descritto da alias/telaio/livello differenti.
4. **Conflitto irrisolto** — deve poter restare aperto senza forzare una CanonicalProperty; se manca un conflitto N12 reale, il gate deve dichiararlo come blocker.
5. **Catena end-to-end** — non deve essere “completata” con un run fittizio; serve un artefatto N12 reale o lo stato `BLOCKED_INPUT`.

---

### Task 1: Baseline RED della matrice di conformità

**Files:**
- Create: `docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md`
- Create: `evidence/cew-contract-01/README.md`

**Interfaces:**
- Consumes: requisiti e test §§23–24 della spec CEW-CONTRACT-01.
- Produces: elenco normativo dei test `C01-T01`…`C01-T11` con stato, criterio, evidenza richiesta e owner del caso; convenzioni del pacchetto `evidence/cew-contract-01/`.

- [ ] **Step 1: Scrivere la matrice iniziale in stato RED**

Creare undici righe corrispondenti a: rappresentabilità N12, provenienza completa, conflitto reale, aggiornamento non distruttivo, identità strutturale, indipendenza dallo strumento, incertezza, Relationship incerta, riproducibilità, assurance, minima sufficienza. Stato iniziale di ogni riga: `NOT_RUN`.

- [ ] **Step 2: Verificare che nessun test parta già PASS**

Run:
```bash
python - <<'PY'
from pathlib import Path
p=Path('docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md').read_text()
assert p.count('C01-T') == 11
assert '| PASS |' not in p
assert p.count('NOT_RUN') == 11
print('matrix-red-ok')
PY
```
Expected: `matrix-red-ok`.

- [ ] **Step 3: Scrivere il README del pacchetto evidenze**

Definire stati ammessi `NOT_RUN | PASS | FAIL | BLOCKED_SOURCE | BLOCKED_INPUT | REVIEW_REQUIRED`, regola di citazione delle fonti N12 e divieto di inferire dati per far passare i test.

- [ ] **Step 4: Verificare le convenzioni**

Run:
```bash
python - <<'PY'
from pathlib import Path
p=Path('evidence/cew-contract-01/README.md').read_text()
for token in ['BLOCKED_SOURCE','BLOCKED_INPUT','REVIEW_REQUIRED','REGISTRO_MASTER.md']:
    assert token in p, token
print('evidence-rules-ok')
PY
```
Expected: `evidence-rules-ok`.

- [ ] **Step 5: Commit**

```bash
git add docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md evidence/cew-contract-01/README.md
git commit -m "test: establish CEW contract conformance gate"
```

### Task 2: Audit di sufficienza delle fonti N12

**Files:**
- Create: `evidence/cew-contract-01/N12_SOURCE_SUFFICIENCY.md`
- Modify: `docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md`

**Interfaces:**
- Consumes: `docs/REGISTRO_MASTER.md`, `docs/PROTOCOLLO_CANONICO.md`, `data/canonical/telaio_5.csv` e ogni fonte originale realmente reperibile nel repository/archivio accessibile.
- Produces: inventario delle voci usabili come Source/Evidence e lista esplicita dei locator mancanti; nessun nuovo dato canonico.

- [ ] **Step 1: Registrare le fonti candidate dal Registro Master**

Includere almeno `GEO-004`, `GEO-005`, `BEAM-006`, `SEC-002`, `M0G-002`, `MAT-001`, indicando per ciascuna: fonte dichiarata, presenza/reperibilità del file, localizzazione interna disponibile, stato epistemico e limiti.

- [ ] **Step 2: Fallire chiuso sui locator assenti**

Per ogni voce senza pagina/riga/entità/file originale verificabile, usare `UNRESOLVED_LOCATOR`; non costruire una Evidence localizzata fittizia.

- [ ] **Step 3: Verificare che i casi critici siano espliciti**

Run:
```bash
python - <<'PY'
from pathlib import Path
p=Path('evidence/cew-contract-01/N12_SOURCE_SUFFICIENCY.md').read_text()
for token in ['GEO-004','GEO-005','BEAM-006','SEC-002','M0G-002','MAT-001','UNRESOLVED_LOCATOR']:
    assert token in p, token
print('source-audit-ok')
PY
```
Expected: `source-audit-ok`.

- [ ] **Step 4: Aggiornare solo i test che l’audit abilita**

La matrice può passare da `NOT_RUN` a `REVIEW_REQUIRED`/`BLOCKED_SOURCE`; non assegnare `PASS` finché il caso corrispondente non è materializzato e verificato.

- [ ] **Step 5: Commit**

```bash
git add evidence/cew-contract-01/N12_SOURCE_SUFFICIENCY.md docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md
git commit -m "test: audit N12 source sufficiency for CEW contract"
```

### Task 3: Casi epistemici N12 — DOC, ND e stato misto

**Files:**
- Create: `evidence/cew-contract-01/CASE_01_DOCUMENTED_PROPERTY.md`
- Create: `evidence/cew-contract-01/CASE_02_NO_PROMOTION_OF_ND.md`
- Create: `evidence/cew-contract-01/CASE_03_MIXED_EPISTEMIC_STATE.md`
- Modify: `docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md`

**Interfaces:**
- Consumes: `BEAM-006`/`data/canonical/telaio_5.csv`, `SEC-002` o `M0G-002`, `GEO-005` e l’audit fonti Task 2.
- Produces: tre istanze logiche di riferimento che usano IDs CEW **solo come fixture di qualifica**, senza promuoverli nel Registro Master.

- [ ] **Step 1: Scrivere CASE_01 con catena conoscitiva completa fino a CanonicalProperty**

Usare un dato effettivamente documentato solo se la Source/Evidence è localizzabile; altrimenti il caso termina a `BLOCKED_SOURCE`. La catena deve nominare `Source`, `Evidence`, `Observation`, `Claim`, `Decision`, `CanonicalProperty`, `StructuralObject`.

- [ ] **Step 2: Scrivere CASE_02 dimostrando che `ND` non riceve un valore**

Usare `SEC-002` o `M0G-002`; l’esito atteso è una proprietà con stato `ND`/assenza esplicita e nessun valore numerico inventato.

- [ ] **Step 3: Scrivere CASE_03 conservando `DOC/INF` di `GEO-005`**

Separare ciò che è documentato (conteggi/artefatto storico) dalla deduzione controllata (sottoinsieme, non universo geometrico completo). Non trasformare `DOC/INF-controllata` in `DOC` semplice.

- [ ] **Step 4: Verificare i tre invarianti**

Run:
```bash
python - <<'PY'
from pathlib import Path
c1=Path('evidence/cew-contract-01/CASE_01_DOCUMENTED_PROPERTY.md').read_text()
c2=Path('evidence/cew-contract-01/CASE_02_NO_PROMOTION_OF_ND.md').read_text()
c3=Path('evidence/cew-contract-01/CASE_03_MIXED_EPISTEMIC_STATE.md').read_text()
for t in ['Source','Evidence','Observation','Claim','Decision','CanonicalProperty','StructuralObject']:
    assert t in c1, t
assert 'ND' in c2 and 'default' in c2.lower()
assert 'GEO-005' in c3 and 'DOC' in c3 and 'INF' in c3
print('epistemic-cases-ok')
PY
```
Expected: `epistemic-cases-ok`.

- [ ] **Step 5: Aggiornare la matrice soltanto con esiti dimostrati**

Assegnare `PASS` solo ai requisiti effettivamente coperti; mantenere blocker per locator mancanti.

- [ ] **Step 6: Commit**

```bash
git add evidence/cew-contract-01/CASE_0*.md docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md
git commit -m "test: qualify CEW epistemic invariants on N12"
```

### Task 4: Identità strutturale, topologia e Relationship incerta

**Files:**
- Create: `evidence/cew-contract-01/CASE_04_STRUCTURAL_IDENTITY.md`
- Create: `evidence/cew-contract-01/CASE_05_RELATIONSHIP_UNCERTAINTY.md`
- Modify: `docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md`

**Interfaces:**
- Consumes: percorsi e livelli documentati di Telaio 5 (`BEAM-004`, `BEAM-006`, `telaio_5.csv`), topologia `GEO-004/GEO-005`, spec §§8–10.
- Produces: mapping tra alias N12 e StructuralObject IDs di fixture; caso di Relationship con proprio stato epistemico/provenienza senza dipendere da nomi CAD/IFC/FEM.

- [ ] **Step 1: Definire un mapping di identità che separi ID CEW e alias N12**

Il caso deve mostrare che `T5`, `G5`, nodi/campate e nomi storici sono alias/provenienze, non identità primarie.

- [ ] **Step 2: Dimostrare stabilità dell’ID al variare di una proprietà**

Descrivere una revisione di proprietà dello stesso elemento senza cambiare il suo fixture object ID; non modificare il Registro Master.

- [ ] **Step 3: Materializzare una Relationship incerta solo se sostenuta da evidenza N12**

Se non esiste una relazione reale sufficientemente localizzabile, registrare `BLOCKED_SOURCE` invece di costruire un collegamento ipotetico.

- [ ] **Step 4: Verificare assenza di tipi N12-specifici nel nucleo del caso**

Run:
```bash
python - <<'PY'
from pathlib import Path
p=Path('evidence/cew-contract-01/CASE_04_STRUCTURAL_IDENTITY.md').read_text()
for token in ['StructuralObject','alias','T5','G5']:
    assert token in p, token
assert 'type: T5' not in p and 'type: G5' not in p
print('identity-case-ok')
PY
```
Expected: `identity-case-ok`.

- [ ] **Step 5: Aggiornare la matrice con PASS o blocker motivato**

- [ ] **Step 6: Commit**

```bash
git add evidence/cew-contract-01/CASE_04_STRUCTURAL_IDENTITY.md evidence/cew-contract-01/CASE_05_RELATIONSHIP_UNCERTAINTY.md docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md
git commit -m "test: qualify CEW structural identity and relationships"
```

### Task 5: Conflict reale e aggiornamento non distruttivo

**Files:**
- Create: `evidence/cew-contract-01/CASE_06_REAL_CONFLICT.md`
- Create: `evidence/cew-contract-01/CASE_07_NON_DESTRUCTIVE_UPDATE.md`
- Modify: `docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md`

**Interfaces:**
- Consumes: fonti N12 effettivamente reperite; versioni/contraddizioni documentali reali se presenti.
- Produces: un Conflict N12 tracciato e una sequenza old state → new evidence → Decision → new state, oppure blocker espliciti se gli input non esistono.

- [ ] **Step 1: Cercare un conflitto reale tra fonti N12**

Accettare il caso solo se due proposizioni incompatibili possono essere ricondotte a fonti/evidenze reali. `GEO-005` da solo non vale come conflitto se rappresenta soltanto una deduzione controllata.

- [ ] **Step 2: Scrivere CASE_06 senza forzare la risoluzione**

Il caso deve mostrare due Claim, le Evidence, `Conflict`, stato (`OPEN`/altro) e l’eventuale `Decision`. Se il conflitto non è reperibile: documento con esito `BLOCKED_SOURCE` e motivazione.

- [ ] **Step 3: Scrivere CASE_07 usando una revisione reale, se disponibile**

Mostrare che lo stato precedente, lo snapshot logico precedente e i riferimenti storici restano intatti. Se non esiste una revisione reale verificabile, usare `BLOCKED_SOURCE`; non inventare una cronologia.

- [ ] **Step 4: Verificare che nessun blocker sia mascherato da PASS**

Run:
```bash
python - <<'PY'
from pathlib import Path
for f in ['CASE_06_REAL_CONFLICT.md','CASE_07_NON_DESTRUCTIVE_UPDATE.md']:
    p=Path('evidence/cew-contract-01',f).read_text()
    assert any(s in p for s in ['PASS','BLOCKED_SOURCE','REVIEW_REQUIRED']), f
print('conflict-versioning-status-ok')
PY
```
Expected: `conflict-versioning-status-ok`.

- [ ] **Step 5: Aggiornare la matrice secondo l’esito reale**

- [ ] **Step 6: Commit**

```bash
git add evidence/cew-contract-01/CASE_06_REAL_CONFLICT.md evidence/cew-contract-01/CASE_07_NON_DESTRUCTIVE_UPDATE.md docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md
git commit -m "test: qualify CEW conflict and version history"
```

### Task 6: Snapshot, Scenario, ModelGeneration e assurance end-to-end

**Files:**
- Create: `evidence/cew-contract-01/CASE_08_SNAPSHOT_SCENARIO.md`
- Create: `evidence/cew-contract-01/CASE_09_END_TO_END_ASSURANCE.md`
- Modify: `docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md`

**Interfaces:**
- Consumes: casi precedenti e un artefatto N12 reale di modello/analisi, se reperibile; spec §§11–20.
- Produces: prova di rappresentabilità Snapshot/Scenario e, solo se esiste input reale sufficiente, catena `Result → SolverRun → ModelGeneration → CanonicalSnapshot → ... → Source`.

- [ ] **Step 1: Costruire un CanonicalSnapshot logico di fixture esclusivamente da dati già qualificati**

Lo snapshot deve elencare versioni/IDs di fixture e non creare nuovi valori canonici.

- [ ] **Step 2: Definire uno Scenario con override esplicito su una incertezza reale**

L’override deve puntare a una `Assumption`; il CanonicalSnapshot base resta immutato.

- [ ] **Step 3: Cercare un artefatto N12 reale che possa sostenere ModelGeneration/SolverRun/Result**

Sono accettabili solo artefatti realmente presenti e tracciabili. Se manca input sufficiente, CASE_09 deve essere `BLOCKED_INPUT`.

- [ ] **Step 4: Vietare esplicitamente run/result fittizi**

CASE_09 deve contenere la frase normativa `NO_SYNTHETIC_ENGINEERING_RESULT` e spiegare perché il gate resta bloccato, oppure documentare il risultato reale e la sua provenienza.

- [ ] **Step 5: Verificare la regola fail-closed**

Run:
```bash
python - <<'PY'
from pathlib import Path
p=Path('evidence/cew-contract-01/CASE_09_END_TO_END_ASSURANCE.md').read_text()
assert 'NO_SYNTHETIC_ENGINEERING_RESULT' in p
assert any(s in p for s in ['PASS','BLOCKED_INPUT'])
print('end-to-end-fail-closed-ok')
PY
```
Expected: `end-to-end-fail-closed-ok`.

- [ ] **Step 6: Aggiornare la matrice**

`C01-T02`, `C01-T09`, `C01-T10` possono essere `PASS` solo con catena reale completa; altrimenti restano `BLOCKED_INPUT`/`REVIEW_REQUIRED`.

- [ ] **Step 7: Commit**

```bash
git add evidence/cew-contract-01/CASE_08_SNAPSHOT_SCENARIO.md evidence/cew-contract-01/CASE_09_END_TO_END_ASSURANCE.md docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md
git commit -m "test: exercise CEW snapshot scenario and assurance chain"
```

### Task 7: Audit di minima sufficienza e indipendenza tecnologica

**Files:**
- Create: `docs/cew-contract/CEW_CONTRACT_01_MINIMALITY_AUDIT.md`
- Modify: `docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md`

**Interfaces:**
- Consumes: tutte le entità della spec e tutti i casi Task 2–6.
- Produces: mapping `entità → caso che la richiede`, elenco di entità non giustificate e audit di termini technology-specific.

- [ ] **Step 1: Mappare ogni entità V1 ad almeno un caso reale o criterio indispensabile**

Entità senza giustificazione devono essere proposte per rinvio, non mantenute per completezza estetica.

- [ ] **Step 2: Auditare dipendenze specialistiche nel contratto**

I nomi PostgreSQL, JSON Schema, IFC, OpenSees, EdiLus, CADCraft, build123d possono apparire solo in non-obiettivi/decisioni rinviate, non come requisito del modello logico.

- [ ] **Step 3: Verificare presenza del mapping di tutte le entità centrali**

Run:
```bash
python - <<'PY'
from pathlib import Path
p=Path('docs/cew-contract/CEW_CONTRACT_01_MINIMALITY_AUDIT.md').read_text()
for token in ['Source','Evidence','Observation','Claim','Decision','CanonicalProperty','StructuralObject','Relationship','CanonicalSnapshot','Scenario','ModelGeneration','SolverRun','Result','Verification','Receipt']:
    assert token in p, token
print('minimality-audit-ok')
PY
```
Expected: `minimality-audit-ok`.

- [ ] **Step 4: Aggiornare `C01-T06` e `C01-T11`**

Assegnare PASS solo se non emergono dipendenze tecnologiche nel nucleo e ogni entità è giustificata; altrimenti `FAIL` con finding specifici.

- [ ] **Step 5: Commit**

```bash
git add docs/cew-contract/CEW_CONTRACT_01_MINIMALITY_AUDIT.md docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md
git commit -m "test: audit CEW contract minimality and tool independence"
```

### Task 8: Gate finale CEW-CONTRACT-01

**Files:**
- Create: `docs/cew-contract/CEW_CONTRACT_01_QUALIFICATION_REPORT.md`
- Modify only if PASS: `docs/superpowers/specs/2026-10-12-cew-contract-01-design.md`

**Interfaces:**
- Consumes: matrice finale e tutte le evidenze di qualifica.
- Produces: decisione finale `PASS` oppure `NOT_QUALIFIED`, con blocker e prossimo passo canonico; eventuale aggiornamento dello stato della spec solo in caso PASS.

- [ ] **Step 1: Calcolare l’esito senza eccezioni manuali**

Regola: `PASS` solo se tutti gli 11 test obbligatori sono `PASS`. Qualunque `FAIL`, `BLOCKED_SOURCE`, `BLOCKED_INPUT`, `REVIEW_REQUIRED` o `NOT_RUN` produce `NOT_QUALIFIED`.

- [ ] **Step 2: Scrivere il report con stato, evidenze e blocker**

Il report deve distinguere: fatti dimostrati, test non dimostrati, limiti delle fonti N12, decisioni che restano rinviate e prossimo passo minimo.

- [ ] **Step 3: Verificare coerenza matrice/report**

Run:
```bash
python - <<'PY'
from pathlib import Path
m=Path('docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md').read_text()
r=Path('docs/cew-contract/CEW_CONTRACT_01_QUALIFICATION_REPORT.md').read_text()
statuses=['FAIL','BLOCKED_SOURCE','BLOCKED_INPUT','REVIEW_REQUIRED','NOT_RUN']
expected='NOT_QUALIFIED' if any(s in m for s in statuses) else 'PASS'
assert f'**Gate:** {expected}' in r
print('gate-consistency-ok', expected)
PY
```
Expected: `gate-consistency-ok PASS` oppure `gate-consistency-ok NOT_QUALIFIED`, coerente con la matrice.

- [ ] **Step 4: Aggiornare lo stato della spec soltanto se il gate è PASS**

Se `NOT_QUALIFIED`, lasciare la spec nello stato “specifica approvata, qualifica non conclusa” e registrare i blocker soltanto nel report. Se `PASS`, aggiornare lo stato a “qualified” e citare il report.

- [ ] **Step 5: Eseguire la verifica finale dei file**

Run:
```bash
python - <<'PY'
from pathlib import Path
required=[
'docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md',
'docs/cew-contract/CEW_CONTRACT_01_MINIMALITY_AUDIT.md',
'docs/cew-contract/CEW_CONTRACT_01_QUALIFICATION_REPORT.md',
'evidence/cew-contract-01/N12_SOURCE_SUFFICIENCY.md',
]
for f in required:
    assert Path(f).is_file(), f
print('qualification-package-complete')
PY
```
Expected: `qualification-package-complete`.

- [ ] **Step 6: Commit**

```bash
git add docs/cew-contract evidence/cew-contract-01 docs/superpowers/specs/2026-10-12-cew-contract-01-design.md
git commit -m "docs: conclude CEW-CONTRACT-01 qualification gate"
```

## Execution Notes

- Questo piano **non** implementa ancora un database o un runtime CEW. È intenzionale: la spec ha rinviato serializzazione e persistenza, e il primo rischio da ridurre è la correttezza del contratto logico sui dati reali.
- Un esito `NOT_QUALIFIED` è un risultato valido del piano se identifica precisamente le evidenze mancanti; non va “corretto” inventando fixture che sembrino dati reali.
- Solo dopo `PASS` (o dopo una decisione esplicita sui blocker) si apre il piano successivo per la rappresentazione eseguibile del contratto e la comparazione delle tecnologie candidate.
