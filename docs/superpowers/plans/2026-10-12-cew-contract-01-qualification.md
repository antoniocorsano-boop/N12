# CEW-CONTRACT-01 Qualification Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dimostrare, su casi N12 reali e senza scegliere ancora database, serializzazione, CAD, IFC o solver, che il contratto logico CEW-CONTRACT-01 rappresenta correttamente provenienza, conoscenza, identità strutturale, conflitti, versionamento, scenari e assurance; quando le evidenze non bastano, il gate deve fallire in modo esplicito e tracciato.

**Architecture:** La specifica approvata resta normativa. La qualifica usa un pacchetto di evidenze Markdown separato dal patrimonio canonico N12: una matrice di conformità guida casi RED→GREEN, ogni caso usa solo dati già presenti nel Registro Master/dataset o fonti originali effettivamente reperite, e nessun artefatto di qualifica modifica `docs/REGISTRO_MASTER.md` o `data/canonical/`. Il risultato finale è `PASS` oppure `NOT_QUALIFIED`, senza promozione implicita di alcuna tecnologia.

**Tech Stack:** Markdown, Git, documenti/dati N12 esistenti; shell/Python standard library solo per controlli di struttura e coerenza testuale. Nessuna dipendenza runtime CEW.

**Spec:** `docs/superpowers/specs/2026-10-12-cew-contract-01-design.md`

## Global Constraints

- Il contratto resta indipendente da database, JSON Schema, RDF, IFC, CAD e solver.
- N12 è caso pilota, non modello concettuale.
- Nessun `ND`, `INC` o `INF` viene promosso a `DOC` per far passare un test.
- Nessun conflitto viene inventato: se manca un caso reale, lo stato è `BLOCKED_SOURCE`.
- Nessun SolverRun/Result fittizio viene presentato come risultato tecnico reale: se manca un artefatto N12 reale, lo stato è `BLOCKED_INPUT`.
- `docs/REGISTRO_MASTER.md` e `data/canonical/` non vengono modificati durante la qualifica, salvo separata decisione esplicita su una correzione fattuale.
- Alias quali `T5`, `G3`, `TAV.5` non diventano tipi o identità CEW.
- Ogni `PASS` deve indicare evidenza e criterio; assenza di evidenza significa `FAIL`/`BLOCKED_*`, non assunzione.

## Review Focus

1. **Dati mancanti (`ND`)** — devono restare mancanti, senza default impliciti.
2. **Stati misti (`DOC/INF`)** — `GEO-005` non deve essere appiattito a uno stato più forte.
3. **Identità fisica vs alias** — lo stesso elemento mantiene un object ID di riferimento anche se cambia rappresentazione/alias.
4. **Conflitto irrisolto** — deve poter restare aperto senza forzare una CanonicalProperty.
5. **Catena end-to-end** — non può essere completata con un run sintetico; serve un artefatto reale oppure `BLOCKED_INPUT`.

---

### Task 1: Baseline RED della matrice di conformità

**Files:**
- Create: `docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md`
- Create: `evidence/cew-contract-01/README.md`

**Interfaces:**
- Consumes: spec §§23–24.
- Produces: undici test `C01-T01`…`C01-T11` e le regole del pacchetto evidenze.

- [ ] **Step 1: Scrivere la matrice in stato RED**

Usare esattamente le colonne:

`| ID | Test | Status | Criterion | Evidence |`

con undici righe, una per ciascun test della spec, tutte inizialmente `NOT_RUN`.

- [ ] **Step 2: Verificare RED**

```bash
python - <<'PY'
from pathlib import Path
import re
p=Path('docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md').read_text()
rows=re.findall(r'^\| (C01-T\d{2}) \| .*? \| (NOT_RUN|PASS|FAIL|BLOCKED_SOURCE|BLOCKED_INPUT|REVIEW_REQUIRED) \|', p, re.M)
assert len(rows)==11, rows
assert all(status=='NOT_RUN' for _,status in rows), rows
print('matrix-red-ok')
PY
```
Expected: `matrix-red-ok`.

- [ ] **Step 3: Scrivere `evidence/cew-contract-01/README.md`**

Definire stati ammessi `NOT_RUN | PASS | FAIL | BLOCKED_SOURCE | BLOCKED_INPUT | REVIEW_REQUIRED`, regola di citazione delle fonti N12 e divieto di inferire dati per far passare i test.

- [ ] **Step 4: Verificare le convenzioni**

```bash
python - <<'PY'
from pathlib import Path
p=Path('evidence/cew-contract-01/README.md').read_text()
for t in ['BLOCKED_SOURCE','BLOCKED_INPUT','REVIEW_REQUIRED','REGISTRO_MASTER.md']:
    assert t in p, t
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
- Consumes: `docs/REGISTRO_MASTER.md`, `docs/PROTOCOLLO_CANONICO.md`, `data/canonical/telaio_5.csv` e ogni fonte originale realmente reperibile.
- Produces: inventario delle Source/Evidence utilizzabili e lista esplicita dei locator mancanti.

- [ ] **Step 1: Registrare almeno `GEO-004`, `GEO-005`, `BEAM-006`, `SEC-002`, `M0G-002`, `MAT-001`**

Per ciascuna voce: fonte dichiarata, file reperibile sì/no, localizzazione interna disponibile sì/no, stato epistemico, limiti.

- [ ] **Step 2: Marcare `UNRESOLVED_LOCATOR` quando pagina/riga/entità/file originale non è verificabile**

Non creare locator fittizi.

- [ ] **Step 3: Verificare l’audit**

```bash
python - <<'PY'
from pathlib import Path
p=Path('evidence/cew-contract-01/N12_SOURCE_SUFFICIENCY.md').read_text()
for t in ['GEO-004','GEO-005','BEAM-006','SEC-002','M0G-002','MAT-001','UNRESOLVED_LOCATOR']:
    assert t in p, t
print('source-audit-ok')
PY
```
Expected: `source-audit-ok`.

- [ ] **Step 4: Aggiornare la matrice solo a `REVIEW_REQUIRED`/`BLOCKED_SOURCE` dove l’audit non consente ancora PASS**

- [ ] **Step 5: Commit**

```bash
git add evidence/cew-contract-01/N12_SOURCE_SUFFICIENCY.md docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md
git commit -m "test: audit N12 source sufficiency for CEW contract"
```

### Task 3: Qualifica del modello epistemico

**Files:**
- Create: `evidence/cew-contract-01/CASE_01_DOCUMENTED_PROPERTY.md`
- Create: `evidence/cew-contract-01/CASE_02_NO_PROMOTION_OF_ND.md`
- Create: `evidence/cew-contract-01/CASE_03_MIXED_EPISTEMIC_STATE.md`
- Modify: `docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md`

**Interfaces:**
- Consumes: `BEAM-006`/`telaio_5.csv`, `SEC-002` o `M0G-002`, `GEO-005`, Task 2.
- Produces: tre casi logici di riferimento; gli ID CEW sono fixture di qualifica e non nuovi ID canonici N12.

- [ ] **Step 1: CASE_01 — catena documentata**

Usare un dato `DOC` solo se Source/Evidence è localizzabile; altrimenti terminare con `BLOCKED_SOURCE`. La catena deve esplicitare `Source → Evidence → Observation → Claim → Decision → CanonicalProperty → StructuralObject`.

- [ ] **Step 2: CASE_02 — nessuna promozione di `ND`**

Usare `SEC-002` o `M0G-002`; mantenere assenza esplicita del valore e dichiarare che non esiste default.

- [ ] **Step 3: CASE_03 — stato misto `GEO-005`**

Separare fatti documentali e deduzione controllata; non trasformare `DOC/INF-controllata` in `DOC` semplice.

- [ ] **Step 4: Verificare gli invarianti**

```bash
python - <<'PY'
from pathlib import Path
c1=Path('evidence/cew-contract-01/CASE_01_DOCUMENTED_PROPERTY.md').read_text()
c2=Path('evidence/cew-contract-01/CASE_02_NO_PROMOTION_OF_ND.md').read_text()
c3=Path('evidence/cew-contract-01/CASE_03_MIXED_EPISTEMIC_STATE.md').read_text()
for t in ['Source','Evidence','Observation','Claim','Decision','CanonicalProperty','StructuralObject']:
    assert t in c1, t
assert 'ND' in c2 and 'no default' in c2.lower()
assert all(t in c3 for t in ['GEO-005','DOC','INF'])
print('epistemic-cases-ok')
PY
```
Expected: `epistemic-cases-ok`.

- [ ] **Step 5: Aggiornare la matrice solo con esiti dimostrati e commit**

```bash
git add evidence/cew-contract-01/CASE_0*.md docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md
git commit -m "test: qualify CEW epistemic invariants on N12"
```

### Task 4: Identità, Relationship, Conflict e storia non distruttiva

**Files:**
- Create: `evidence/cew-contract-01/CASE_04_STRUCTURAL_IDENTITY.md`
- Create: `evidence/cew-contract-01/CASE_05_RELATIONSHIP_UNCERTAINTY.md`
- Create: `evidence/cew-contract-01/CASE_06_REAL_CONFLICT.md`
- Create: `evidence/cew-contract-01/CASE_07_NON_DESTRUCTIVE_UPDATE.md`
- Modify: `docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md`

**Interfaces:**
- Consumes: `BEAM-004`, `BEAM-006`, `GEO-004/GEO-005`, fonti/versioni N12 realmente reperibili.
- Produces: separazione ID/alias, Relationship con stato proprio, Conflict reale se disponibile, sequenza storica non distruttiva se disponibile.

- [ ] **Step 1: CASE_04 — separare fixture object ID da alias `T5`, `G5`, nomi di nodi/campate**

Mostrare che una revisione di proprietà non cambia l’identità dell’elemento fisico.

- [ ] **Step 2: CASE_05 — Relationship incerta**

Usare solo una relazione N12 sostenuta da evidenza localizzabile; altrimenti `BLOCKED_SOURCE`.

- [ ] **Step 3: CASE_06 — Conflict reale**

Accettare il caso solo se esistono due proposizioni incompatibili da fonti reali; `GEO-005` da solo non costituisce automaticamente un conflitto. Se manca, `BLOCKED_SOURCE`.

- [ ] **Step 4: CASE_07 — aggiornamento non distruttivo**

Usare una revisione reale verificabile; dimostrare conservazione dello stato precedente. Se manca, `BLOCKED_SOURCE`.

- [ ] **Step 5: Verificare identità e fail-closed**

```bash
python - <<'PY'
from pathlib import Path
p=Path('evidence/cew-contract-01/CASE_04_STRUCTURAL_IDENTITY.md').read_text()
assert all(t in p for t in ['StructuralObject','alias','T5','G5'])
assert 'type: T5' not in p and 'type: G5' not in p
for f in ['CASE_05_RELATIONSHIP_UNCERTAINTY.md','CASE_06_REAL_CONFLICT.md','CASE_07_NON_DESTRUCTIVE_UPDATE.md']:
    q=Path('evidence/cew-contract-01',f).read_text()
    assert any(s in q for s in ['PASS','BLOCKED_SOURCE','REVIEW_REQUIRED']), f
print('identity-conflict-versioning-ok')
PY
```
Expected: `identity-conflict-versioning-ok`.

- [ ] **Step 6: Aggiornare la matrice e commit**

```bash
git add evidence/cew-contract-01/CASE_04_STRUCTURAL_IDENTITY.md evidence/cew-contract-01/CASE_05_RELATIONSHIP_UNCERTAINTY.md evidence/cew-contract-01/CASE_06_REAL_CONFLICT.md evidence/cew-contract-01/CASE_07_NON_DESTRUCTIVE_UPDATE.md docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md
git commit -m "test: qualify CEW identity conflicts and history"
```

### Task 5: Snapshot, Scenario e assurance end-to-end

**Files:**
- Create: `evidence/cew-contract-01/CASE_08_SNAPSHOT_SCENARIO.md`
- Create: `evidence/cew-contract-01/CASE_09_END_TO_END_ASSURANCE.md`
- Modify: `docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md`

**Interfaces:**
- Consumes: casi già qualificati e un artefatto N12 reale di modello/analisi, se reperibile.
- Produces: Snapshot/Scenario di fixture e, solo con input reale sufficiente, catena `Result → SolverRun → ModelGeneration → CanonicalSnapshot → … → Source`.

- [ ] **Step 1: Costruire un CanonicalSnapshot logico usando esclusivamente dati già qualificati**

Non creare nuovi valori canonici.

- [ ] **Step 2: Definire uno Scenario con override su una incertezza reale e Assumption esplicita**

Il CanonicalSnapshot base resta immutato.

- [ ] **Step 3: Cercare un artefatto N12 reale per ModelGeneration/SolverRun/Result**

Se manca un input sufficiente, CASE_09 è `BLOCKED_INPUT`.

- [ ] **Step 4: Inserire la guardia `NO_SYNTHETIC_ENGINEERING_RESULT`**

Il caso deve contenere esattamente questa stringa e spiegare perché non si accettano run/result fittizi.

- [ ] **Step 5: Verificare fail-closed**

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

- [ ] **Step 6: Aggiornare la matrice e commit**

`C01-T02`, `C01-T09`, `C01-T10` possono essere `PASS` solo con catena reale completa.

```bash
git add evidence/cew-contract-01/CASE_08_SNAPSHOT_SCENARIO.md evidence/cew-contract-01/CASE_09_END_TO_END_ASSURANCE.md docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md
git commit -m "test: exercise CEW snapshot scenario and assurance chain"
```

### Task 6: Minimalità, indipendenza tecnologica e gate finale

**Files:**
- Create: `docs/cew-contract/CEW_CONTRACT_01_MINIMALITY_AUDIT.md`
- Create: `docs/cew-contract/CEW_CONTRACT_01_QUALIFICATION_REPORT.md`
- Modify: `docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md`
- Modify only if PASS: `docs/superpowers/specs/2026-10-12-cew-contract-01-design.md`

**Interfaces:**
- Consumes: tutte le entità della spec e tutti i casi Task 2–5.
- Produces: mapping entità→caso, audit di indipendenza tecnologica e decisione finale `PASS`/`NOT_QUALIFIED`.

- [ ] **Step 1: Mappare ogni entità centrale ad almeno un caso**

Includere almeno: `Source`, `Evidence`, `Observation`, `Claim`, `Decision`, `CanonicalProperty`, `StructuralObject`, `Relationship`, `CanonicalSnapshot`, `Scenario`, `ModelGeneration`, `SolverRun`, `Result`, `Verification`, `Receipt`. Entità senza giustificazione vengono proposte per rinvio.

- [ ] **Step 2: Auditare indipendenza tecnologica**

PostgreSQL, JSON Schema, IFC, OpenSees, EdiLus, CADCraft, build123d possono apparire solo come non-obiettivi/decisioni rinviate, non come requisito del nucleo.

- [ ] **Step 3: Aggiornare `C01-T06` e `C01-T11` in base all’audit**

- [ ] **Step 4: Calcolare l’esito finale leggendo esclusivamente la colonna Status**

```bash
python - <<'PY'
from pathlib import Path
import re
m=Path('docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md').read_text()
rows=re.findall(r'^\| (C01-T\d{2}) \| .*? \| (NOT_RUN|PASS|FAIL|BLOCKED_SOURCE|BLOCKED_INPUT|REVIEW_REQUIRED) \|', m, re.M)
assert len(rows)==11, rows
expected='PASS' if all(status=='PASS' for _,status in rows) else 'NOT_QUALIFIED'
Path('/tmp/cew_contract_gate.txt').write_text(expected)
print('gate-status', expected)
PY
```
Expected: `gate-status PASS` oppure `gate-status NOT_QUALIFIED`.

- [ ] **Step 5: Scrivere il report finale coerente con lo stato calcolato**

Il report deve contenere `**Gate:** PASS` oppure `**Gate:** NOT_QUALIFIED`, distinguere fatti dimostrati, blocker, limiti delle fonti e prossimo passo minimo.

- [ ] **Step 6: Verificare matrice/report**

```bash
python - <<'PY'
from pathlib import Path
expected=Path('/tmp/cew_contract_gate.txt').read_text().strip()
r=Path('docs/cew-contract/CEW_CONTRACT_01_QUALIFICATION_REPORT.md').read_text()
assert f'**Gate:** {expected}' in r
for f in [
'docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md',
'docs/cew-contract/CEW_CONTRACT_01_MINIMALITY_AUDIT.md',
'docs/cew-contract/CEW_CONTRACT_01_QUALIFICATION_REPORT.md',
'evidence/cew-contract-01/N12_SOURCE_SUFFICIENCY.md']:
    assert Path(f).is_file(), f
print('qualification-package-ok', expected)
PY
```
Expected: `qualification-package-ok PASS` oppure `qualification-package-ok NOT_QUALIFIED`.

- [ ] **Step 7: Aggiornare lo stato della spec soltanto se PASS**

Se `NOT_QUALIFIED`, la spec resta approvata ma non qualificata e i blocker vivono nel report. Se `PASS`, aggiornare lo stato a `qualified` e citare il report.

- [ ] **Step 8: Commit**

```bash
git add docs/cew-contract evidence/cew-contract-01 docs/superpowers/specs/2026-10-12-cew-contract-01-design.md
git commit -m "docs: conclude CEW-CONTRACT-01 qualification gate"
```

## Execution Notes

- Questo piano non implementa ancora database o runtime CEW: è intenzionale e coerente con la spec approvata.
- `NOT_QUALIFIED` è un esito valido se individua precisamente fonti o artefatti mancanti; non va trasformato artificialmente in PASS.
- Solo dopo PASS, o dopo una decisione esplicita sui blocker, si apre il piano successivo per la rappresentazione eseguibile del contratto e la comparazione delle tecnologie candidate.
