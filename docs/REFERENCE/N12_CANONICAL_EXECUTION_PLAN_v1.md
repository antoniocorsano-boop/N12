# N12 — Piano canonico di esecuzione v1

**Stato:** HUMAN_APPROVED — ACTIVE_REFERENCE  
**Data:** 2026-10-09  
**Ambito:** Condominio N.12 / Civil Existing Workflow  
**Baseline di introduzione:** `work/cew-free-review-gate-v1-final@b8e4235a04e52fb58bf1064885384b287f9774a7`

## 1. Scopo

Questo documento fissa il percorso operativo per portare N12 a una soluzione tecnica proponibile, verificabile e professionalmente revisionabile evitando lavoro inutile, duplicazioni e ricostruzioni premature.

Non introduce una nuova fonte di verità strutturale. Opera come riferimento di esecuzione subordinato a:

1. fonti originali e SourceVersion governate;
2. `docs/PROTOCOLLO_CANONICO.md`;
3. `docs/REGISTRO_MASTER.md` e dataset canonici collegati;
4. `knowledge/KNOWLEDGE_MANIFEST.json`, `knowledge/CURRENT_STATE.json`, `knowledge/ARTIFACT_REGISTRY.csv` e relativi gate/receipt;
5. contratti CEW applicabili al work item corrente.

In caso di conflitto, prevale sempre l'autorità più vicina alla fonte e al dato canonico.

## 2. Principio guida

N12 non deve essere completato “per aspetto” o per analogia. Deve essere completato per catene di evidenza verificabili.

Catena canonica:

`EVIDENZE -> BASELINE CONOSCITIVA -> MODELLO GEOMETRICO PARAMETRICO -> CONTROLLO AUTOMATICO -> LIVELLO DI CONOSCENZA -> MODELLO STRUTTURALE -> VERIFICHE -> FASCICOLO TECNICO`

Ogni passaggio è un gate. Il gate successivo si apre solo quando il precedente produce un artefatto tracciabile e verificato.

## 3. Regole anti-spreco

1. **Non rifare ciò che è già verificato.** Ogni artefatto storico utile deve essere classificato come `RIUSA`, `VERIFICA`, `DEPRECATO` o `MANCANTE` prima di produrre un sostituto.
2. **Un dato si determina una volta sola.** Correzioni e revisioni devono propagarsi dai dati canonici verso CAD, viste, IFC/FEM e dossier; non si ridisegna manualmente lo stesso dato in più luoghi.
3. **Nessun dato mancante viene completato per simmetria, analogia o plausibilità.** Restano valide le classi epistemiche canoniche `DOC/MIS/RIF/INF/INC/ND` e gli eventuali stati ulteriori previsti dai contratti CEW.
4. **Geometria e parametri strutturali restano separati.** Un elemento può essere geometricamente certo pur avendo sezione, armatura, materiale o vincolo non ancora determinati.
5. **Il CAD non è fonte canonica.** È una proiezione parametrica dei dati governati CEW.
6. **IFC e FEM non sono fonti canoniche.** Sono rappresentazioni/interpreti downstream con round-trip di identità e provenienza.
7. **L'automazione controlla e propone; non promuove autorità professionale.** Nessun modello IA, parser o solutore assegna automaticamente identità strutturali definitive, LC/FC o giudizi professionali.
8. **Nessuna integrazione massiva di branche storiche.** Le capability sperimentali vengono inventariate, qualificate e recuperate selettivamente dietro contratti stabili.

## 4. Fase 0 — Baseline conoscitiva canonica v1

### Stato

**CHIUSA — PASS.**

L'audit `N12-BASELINE-AUDIT-01` ha classificato il patrimonio esistente e ha eliminato il falso residuo FPEP. Non autorizza nuova ricostruzione globale.

### Output

- `analysis/cew/N12_BASELINE_AUDIT_01_v1.md`;
- `analysis/cew/N12_BASELINE_AUDIT_MATRIX_v1.csv`;
- `analysis/cew/N12_POST_AUDIT_PRIORITY_v1.csv`.

## 5. Fase 1 — Modello geometrico parametrico

### Stato

**RIUSA checkpoint qualificati.** M0-G e la geometria fondazioni FPEP non devono essere ricostruiti senza nuova evidenza primaria e procedura di reopen.

### Requisiti permanenti

- ID CEW stabili per ogni entità rappresentata;
- livelli, assi, nodi, elementi e aperture derivati da fonti tracciate;
- parametri ignoti mantenuti esplicitamente ignoti;
- aggiornamento rigenerabile da dati canonici;
- nessuna dipendenza obbligatoria da CAD commerciale.

### Controlli automatici minimi

- duplicati e sovrapposizioni;
- nodi isolati;
- travi o elementi senza supporto coerente;
- discontinuità verticali non documentate;
- conflitti tra livelli;
- elementi fuori perimetro o fuori tavola;
- incongruenze tra viste e sorgenti;
- completezza delle relazioni tra entità e evidenze.

Il motore CAD è un adattatore sostituibile. La scelta tecnica resta subordinata alla baseline open-source CEW e ai relativi gate di qualifica.

## 6. Fase 2 — Gate di sufficienza conoscitiva

Prima di costruire o aggiornare un modello strutturale di calcolo, CEW deve produrre una matrice di sufficienza che distingua almeno:

- geometria disponibile;
- dettagli costruttivi disponibili;
- sezioni disponibili;
- armature disponibili;
- materiali disponibili;
- fondazioni disponibili;
- carichi disponibili;
- dati geotecnici disponibili;
- dati derivati o ancora incerti.

L'eventuale valutazione di livello di conoscenza e fattore di confidenza è separata dalla mera presenza dei dati e resta soggetta a regole normative versionate e decisione professionale.

## 7. Fase 3 — Modello strutturale

Il modello strutturale può essere prodotto solo dal set di dati che ha superato il gate precedente.

Ogni entità di calcolo deve mantenere un mapping univoco verso l'identità CEW e verso le evidenze da cui derivano proprietà e parametri.

Stati ipotetici o scenari di sensitività sono ammessi soltanto come scenari separati dalla verità canonica.

## 8. Fase 4 — Verifiche e analisi

Le verifiche devono mantenere separate:

- grandezze numeriche prodotte dal solutore;
- regole normative applicate;
- assunzioni e scenari;
- interpretazione tecnica;
- decisione professionale.

Il risultato numerico non costituisce automaticamente giudizio di sicurezza, conformità o idoneità.

## 9. Fase 5 — Fascicolo tecnico riproducibile

Il prodotto finale deve consentire a un professionista di ricostruire:

- quali fonti sono state usate;
- quali dati sono documentati, misurati, riferiti, inferiti, incerti o mancanti;
- quale generazione geometrica e strutturale è stata verificata;
- quali assunzioni sono state adottate;
- quali verifiche sono state eseguite;
- quali residui restano aperti;
- quali decisioni richiedono responsabilità professionale.

Il fascicolo deve essere rigenerabile dai dati canonici senza editing manuale sostanziale.

## 10. Ruolo dei modelli IA e del CAD

Un modello IA può:

- leggere e riconciliare fonti già governate;
- proporre corrispondenze e geometrie candidate;
- generare codice parametrico e adattatori;
- verificare coerenza geometrica e topologica;
- rilevare incongruenze e lacune;
- preparare scenari e report.

Non può, senza il gate umano previsto:

- promuovere `INF/INC/ND` a `DOC/MIS`;
- assegnare automaticamente LC/FC;
- sostituire il professionista nelle decisioni ingegneristiche;
- trasformare un risultato FEM in certificazione o asseverazione.

## 11. Gate di avanzamento

Una fase è chiusa solo quando:

1. l'artefatto di uscita esiste ed è versionato;
2. le fonti usate sono tracciate;
3. i residui sono espliciti;
4. i controlli previsti sono PASS o formalmente classificati come blocchi esterni;
5. non esistono dati promossi oltre la loro evidenza;
6. il prossimo passo deriva dai residui, non da una nuova iniziativa parallela.

## 12. Prossimo passo canonico

**Work item corrente:** `M1E-CALCULATION-MODEL-HANDOFF`.

`N12-BASELINE-AUDIT-01` è chiuso e non deve essere rieseguito.

Ordine operativo corrente:

1. `M1E-B06` — usare esclusivamente `M1E_B06_SUPERSTRUCTURE_REINFORCEMENT_RESIDUAL_REGISTER_v1.csv`; processare le **9** righe `EXISTING_GOVERNED_SOURCE_TARGETED`; le altre **12** richiedono nuova evidenza oppure esclusione tracciabile dello scope;
2. `M1E-B02` — usare esclusivamente il registro finito a 16 righe, senza introdurre Gk/Qk, masse, pesi unitari o fattori non tracciati;
3. `M1E-B04`, `B05`, `B01`, `B07` — trattare solo mediante le evidenze/decisioni richieste dalla matrice post-audit.

**Stop condition:** `CALCULATION_MODEL_READY` resta `false` finché i sei blocker M1E non sono risolti o formalmente esclusi secondo una regola ammessa. Non riaprire M0-G o FPEP senza nuova evidenza primaria.

## 13. Criterio di successo del programma

N12 è proponibile quando un terzo qualificato può esaminare la catena completa:

`fonte -> evidenza -> dato canonico -> entità geometrica -> entità strutturale -> scenario -> risultato -> decisione -> fascicolo`

senza dover ricostruire manualmente come ogni informazione è stata ottenuta e senza confondere ipotesi con fatti documentati.
