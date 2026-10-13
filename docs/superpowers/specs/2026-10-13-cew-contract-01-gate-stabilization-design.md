# CEW-CONTRACT-01 — Gate Stabilization Design

**Data:** 13 ottobre 2026  
**Stato:** design approvato in chat; specifica scritta in revisione umana  
**PR:** #147  
**Caso pilota:** N12  
**Ambito:** stabilizzazione definitiva del gate CEW-CONTRACT-01 dopo la qualifica funzionale, senza estendere il dominio tecnico, senza anticipare CEW-FEM-01 e senza introdurre nuovi dati ingegneristici.

## 1. Scopo

Questa specifica definisce come trasformare il gate CEW-CONTRACT-01 da una sequenza progressiva di controlli aggiunti dopo review successive a un sistema di qualifica **finito, avversarialmente testato, durevole e con criterio di arresto esplicito**.

L'obiettivo non è aggiungere nuove capacità al contratto CEW. L'obiettivo è rendere chiuso e verificabile il perimetro delle garanzie già necessarie per dichiarare `CEW-CONTRACT-01 = QUALIFIED`.

La stabilizzazione deve impedire il ciclo:

`finding → patch locale → nuova superficie non coperta → nuovo finding → nuova patch`

sostituendolo con:

`invarianti congelati → threat model → mutation suite → replay deterministico → gate fail-closed → review finale rispetto agli invarianti → closure`.

## 2. Autorità e precedenza

Questa specifica integra:

- `docs/superpowers/specs/2026-10-12-cew-contract-01-design.md`;
- `docs/superpowers/specs/2026-10-13-cew-contract-01-closure-design.md`.

Non modifica la semantica del dominio definita da tali specifiche. Prevale solo per:

- architettura del gate di qualifica;
- durabilità delle evidenze di qualifica;
- replay di `ModelGeneration`;
- mutation testing;
- classificazione dei finding di review;
- criterio di arresto della closure.

In caso di conflitto su questi punti, vale l'ordine:

1. presente specifica di stabilizzazione;
2. specifica di chiusura del 13 ottobre 2026;
3. specifica CEW-CONTRACT-01 del 12 ottobre 2026;
4. piani, report, workflow e validator derivati.

## 3. Problema da risolvere

La qualifica ha progressivamente rafforzato il gate con controlli corretti ma scoperti in momenti successivi: exact-head checkout, pinning delle action, digest reali degli input, receipt reconciliation, verifica delle evidenze, guardie epistemiche, identità dello snapshot, verifica dell'output e riconciliazione con fonti reali.

La review finale ha mostrato che, pur essendo il gate molto più forte, restano due rischi sistemici:

1. **scoperta incrementale non delimitata** — ogni reviewer può individuare una nuova assunzione implicita non ancora formalizzata;
2. **dipendenza da evidenze operative effimere** — in particolare artifact GitHub Actions e metadati runtime che non sono appropriati come dipendenze permanenti di un gate canonico.

La risposta non deve essere un'altra serie di patch indipendenti. Deve essere una definizione chiusa degli invarianti e dei relativi failure mode.

## 4. Principi non negoziabili

La stabilizzazione preserva questi principi:

- nessun dato tecnico inventato;
- nessuna promozione epistemica impropria;
- nessun valore mancante trasformato in valore assunto senza regola esplicita;
- nessun `SolverRun` o `Result` sintetico;
- `solver_authorized=false`;
- `calculation_model_ready=false`;
- nessuna scelta di solver nel core CEW-CONTRACT-01;
- nessuna dipendenza permanente da storage con retention finita;
- nessun requisito nuovo introdotto solo perché un reviewer lo suggerisce;
- nessun bypass silenzioso del gate;
- ogni PASS deve essere spiegabile da evidenze e trasformazioni riproducibili.

## 5. Architettura del gate stabilizzato

Il gate stabilizzato è composto da quattro responsabilità separate.

### 5.1 Frozen Authority Profile

Definisce l'autorità congelata della qualifica N12. Deve identificare in modo univoco almeno:

- commit operativo N12 congelato: `d806dcca72779b5a186defe557a7a9b739575a90`;
- `canonical_snapshot_id`;
- builder autorizzato e relativo Git blob;
- insieme esatto dei sei input `ModelGeneration`;
- digest attesi degli input;
- fonte della registration uncertainty;
- identità esatta dei due esempi di registrazione usati dal gate;
- profilo di generazione;
- identità dell'output canonico atteso;
- authority flags che devono restare false;
- riferimenti alle evidenze del gate C01-T01…C01-T11.

Il profilo non crea dati nuovi. Rende machine-checkable l'autorità già congelata nelle evidenze e nei manifest esistenti.

### 5.2 Durable Replay Validator

Verifica la riproducibilità della `ModelGeneration` partendo da oggetti Git immutabili, non da artifact Actions temporanei.

Il replay deve:

1. materializzare dal commit operativo congelato il builder autorizzato;
2. ricalcolarne il Git blob SHA e confrontarlo con l'autorità congelata;
3. materializzare esattamente i sei input autorizzati;
4. ricalcolarne i digest;
5. eseguire il builder in ambiente controllato;
6. rendere deterministica soltanto la componente temporale di esecuzione già registrata come metadato;
7. produrre un output temporaneo;
8. verificarne identità, contenuto e digest contro il riferimento congelato;
9. eliminare l'output temporaneo al termine del gate.

Il replay non modifica il builder storico e non altera dati ingegneristici.

### 5.3 Mutation Suite

La mutation suite costituisce il threat model eseguibile del gate. Ogni mutazione ammessa deve dimostrare che il gate fallisce chiuso.

Le mutazioni non devono essere eseguite sui dati canonici reali. Devono lavorare su copie temporanee/fixture isolate.

### 5.4 Closure Policy

Definisce quando un finding futuro è blocker e quando è soltanto una proposta di estensione o miglioramento.

Questa policy impedisce che la review allarghi indefinitamente il contratto dopo che gli invarianti sono stati congelati.

## 6. Invarianti chiusi della qualifica

Il gate stabilizzato deve garantire esattamente le seguenti famiglie di invarianti.

### I01 — Exact-head identity

La qualifica deve essere eseguita sul vero head della PR. Un merge ref sintetico non può essere qualificato al posto del PR head.

### I02 — Gate non bypassabile

Nessuno step obbligatorio può essere reso opzionale tramite `if`, `continue-on-error`, shell fallback equivalenti o altre condizioni che trasformino un FAIL in PASS.

### I03 — Operational authority identity

Il commit operativo deve essere esattamente `d806dcca72779b5a186defe557a7a9b739575a90`.

### I04 — Exact input set

La `ModelGeneration` deve dipendere esattamente dai sei input autorizzati: nessun input mancante, duplicato o aggiuntivo.

### I05 — Input byte integrity

Ogni input deve esistere nel commit operativo e il relativo SHA-256 deve essere ricalcolato dai byte reali.

### I06 — Builder identity

Il builder deve essere materializzato dal commit operativo, il suo path deve essere quello autorizzato e il Git blob SHA deve essere ricalcolato dai byte reali.

### I07 — Canonical snapshot identity

`canonical_snapshot_id` deve identificare esattamente lo stato congelato autorizzato. `null`, vuoto o un commit diverso falliscono chiuso.

### I08 — Durable deterministic replay

Il gate deve poter ricostruire la `ModelGeneration` senza dipendere dall'esistenza di un artifact GitHub Actions storico.

### I09 — Output integrity

L'output del replay deve avere l'identità prevista e soddisfare il confronto deterministico definito dal profilo congelato.

### I10 — Manifest / Verification / Receipt coherence

Manifest, Verification e Receipt devono concordare su identità di generazione, snapshot, builder, input, output, authority flags e stato della verifica.

### I11 — Registration source provenance

La fonte della registration uncertainty deve provenire dal commit operativo congelato; il suo Git blob deve essere ricalcolato e gli esempi devono essere riconciliati con le righe reali della fonte.

### I12 — Exact registration examples

Il caso N12 deve contenere esattamente i due esempi congelati usati dalla qualifica, identificati dai supporti autorizzati. Devono essere presenti sia il caso `PASS_DIAGNOSTIC` sia il caso `WATCH` previsto dalla fonte.

### I13 — Epistemic guards

Le quattro guardie che vietano nuove misure/promozioni/interval assumptions devono essere presenti ed esplicitamente false.

### I14 — Gate matrix integrity

La matrice deve contenere esattamente `C01-T01`…`C01-T11`, una volta ciascuno. Tutti devono essere `PASS` per qualificare.

### I15 — Evidence existence

Ogni riga `PASS` deve risolvere almeno un riferimento di evidenza valido e realmente presente.

### I16 — Authority boundary

Devono rimanere false almeno:

- `solver_authorized`;
- `calculation_model_ready`;
- `synthetic_solver_result`;
- `solver_run` nella receipt di ModelGeneration;
- `result_entity_created` nella receipt di ModelGeneration.

### I17 — CEW-FEM separation

Il gate deve dichiarare e preservare come debito separato:

`ModelGeneration → SolverRun → Result → Verification → Receipt`.

Nessun controllo di stabilizzazione può anticipare questa catena dentro CEW-CONTRACT-01.

## 7. Replay deterministico e gestione del tempo

Il builder storico usa un timestamp runtime per `generated_at`. Questo campo rende i byte dell'output dipendenti dall'orologio pur non rappresentando un dato ingegneristico.

La stabilizzazione deve rendere il replay deterministico **senza modificare il builder storico e senza alterare contenuti tecnici**.

La soluzione approvata è un replay harness che controlla l'orologio osservato dal builder e usa il timestamp storico già registrato nel manifest di qualifica.

Regole:

- il timestamp usato nel replay deve provenire dal manifest congelato, non da un nuovo valore deciso dal test;
- nessun altro campo può essere sostituito o normalizzato per far coincidere l'output;
- il builder deve eseguire la stessa logica e leggere gli stessi sei input;
- se il replay non riproduce l'output atteso, il gate deve fallire;
- il replay harness è parte del gate e deve avere test negativi propri.

Questa tecnica rende deterministico un metadato volatile senza cambiare l'autorità ingegneristica.

## 8. Evidenza storica vs dipendenza runtime

Il run storico `32955421352` e l'artifact `9601773275` restano importanti come **evidenza storica della generazione originaria**, ma non devono essere prerequisiti permanenti di ogni futura esecuzione del gate.

Durante la transizione alla versione stabilizzata devono essere verificati una volta, finché disponibili:

- workflow atteso;
- path del workflow;
- head SHA `d806...`;
- stato `completed`;
- conclusione `success`;
- identità dell'artifact;
- digest dell'archive;
- digest e dimensione dell'output contenuto.

L'esito di questa verifica deve essere registrato in una ricevuta durevole e versionata nel repository.

Dopo la transizione:

- l'artifact Actions può scadere senza rendere rosso il gate;
- la disponibilità API del vecchio run non è richiesta per la qualifica corrente;
- il gate corrente dimostra la riproducibilità attraverso Git commit + builder + input + replay;
- la ricevuta storica documenta che l'output congelato coincideva con quello prodotto dal run originario quando l'evidenza operativa era ancora interrogabile.

Questa separazione evita di trasformare servizi di retention in autorità probatoria permanente.

## 9. Mutation Suite — categorie obbligatorie

La suite deve coprire almeno le seguenti mutazioni negative.

### 9.1 Workflow / execution

- checkout su merge ref invece del PR head;
- action non pin a SHA;
- credenziali checkout persistenti;
- `if` che salta il validator;
- `continue-on-error` o fallback equivalente;
- mancata esecuzione dello step finale.

### 9.2 Frozen authority

- commit operativo diverso;
- snapshot `null`;
- snapshot vuoto;
- snapshot con commit diverso;
- builder path diverso;
- builder blob SHA diverso.

### 9.3 Input set

- uno dei sei input mancante;
- input duplicato;
- settimo input aggiunto;
- path modificato;
- digest dichiarato diverso;
- byte materializzati diversi.

### 9.4 Replay / output

- timestamp di replay non derivato dal manifest;
- builder alterato;
- output identity diversa;
- output byte diversi;
- output digest diverso;
- replay che omette uno degli input.

### 9.5 Verification / Receipt

- Verification diversa da `PASS`;
- workflow identity incoerente tra manifest e receipt;
- input digest mismatch;
- output digest mismatch;
- `solver_run=true`;
- `result_entity_created=true`;
- `solver_authorized=true`;
- `calculation_model_ready=true`;
- `synthetic_solver_result=true`.

### 9.6 Registration uncertainty

- fonte diversa;
- source blob diverso;
- supporto 1 mancante;
- supporto 19 mancante;
- supporto inatteso aggiunto;
- valore osservato/predetto/residuo modificato;
- stato diagnostico modificato;
- evidence class modificata;
- una guardia epistemica mancante o `true`.

### 9.7 Gate matrix / evidence

- ID duplicato;
- ID mancante;
- ID inatteso;
- stato non PASS;
- evidence vuota;
- evidence inesistente;
- path evidence non sicuro;
- glob senza risultati.

Ogni mutazione deve avere un errore atteso identificabile. Non basta verificare genericamente che "qualcosa fallisce" quando è possibile associare una causa stabile.

## 10. Happy path

Oltre ai test negativi, deve esistere un unico happy path integrato che dimostra:

1. exact PR head;
2. Frozen Authority Profile valido;
3. materializzazione builder e input dal commit operativo;
4. verifica blob/digest;
5. replay deterministico;
6. output conforme;
7. registration uncertainty conforme;
8. Manifest/Verification/Receipt coerenti;
9. 11/11 gate PASS;
10. authority boundary intatto;
11. `CEW-FEM-01` ancora separato.

Il PASS finale deve essere prodotto soltanto dopo la suite positiva e negativa.

## 11. Failure taxonomy

Gli errori del gate devono essere classificabili almeno in:

- `AUTHORITY_IDENTITY_*`;
- `INPUT_SET_*`;
- `INPUT_DIGEST_*`;
- `BUILDER_IDENTITY_*`;
- `REPLAY_*`;
- `OUTPUT_*`;
- `REGISTRATION_*`;
- `RECEIPT_*`;
- `EVIDENCE_*`;
- `GATE_MATRIX_*`;
- `AUTHORITY_BOUNDARY_*`;
- `CI_BYPASS_*`.

La tassonomia serve a rendere leggibile il fallimento e a evitare patch ad hoc non riconducibili a un invariante.

## 12. Finding triage policy

Dopo l'adozione di questa specifica, un finding di review è **blocker di CEW-CONTRACT-01** solo se dimostra almeno una delle seguenti condizioni:

1. un invariante I01–I17 può essere violato e il gate resta verde;
2. un controllo obbligatorio può essere bypassato;
3. il replay usa dati diversi dall'autorità congelata senza fallire;
4. una dipendenza effimera è ancora necessaria al funzionamento permanente del gate;
5. il gate introduce o promuove dati tecnici non autorizzati;
6. il confine CEW-CONTRACT-01 / CEW-FEM-01 viene violato.

Non è blocker, salvo decisione umana esplicita:

- una nuova garanzia non prevista da I01–I17;
- un refactoring estetico;
- un miglioramento di performance non necessario alla correttezza;
- una preferenza di toolchain equivalente;
- una richiesta relativa al solver o ai risultati FEM;
- un'estensione di tassonomia non richiesta dai casi reali del gate.

Questi elementi vanno registrati come backlog o proposta di nuova specifica, non incorporati automaticamente nella closure corrente.

## 13. Criterio di arresto

CEW-CONTRACT-01 Gate Stabilization è concluso quando, sullo stesso exact head:

1. la presente specifica è approvata;
2. il Frozen Authority Profile è machine-checkable;
3. tutti gli invarianti I01–I17 sono coperti da test;
4. tutte le mutazioni obbligatorie producono FAIL con causa prevista;
5. l'happy path produce PASS;
6. nessun artifact Actions storico è richiesto dal gate permanente;
7. il replay ricostruisce l'output dalla sorgente congelata;
8. il gate repository-native completa con successo;
9. non esistono review thread blocker aperti rispetto a I01–I17;
10. una fresh review indipendente sul medesimo exact head non dimostra false-positive rispetto agli invarianti congelati.

Una volta soddisfatti questi criteri, **la closure non viene riaperta da richieste che estendono il perimetro degli invarianti**. Ogni estensione successiva richiede una nuova decisione/spec separata.

## 14. Fuori ambito

Sono esplicitamente fuori ambito:

- implementazione CEW-FEM-01;
- scelta o configurazione di un solver;
- esecuzione di analisi strutturali N12;
- definizione di materiali, carichi, vincoli o parametri geotecnici mancanti;
- introduzione di nuove proprietà ingegneristiche;
- modifica della geometria canonica;
- risoluzione del valore numerico di `ZF_COMMON`;
- promozione di residui geometrici a accuratezza metrologica;
- adozione di nuovi adapter CAD/IFC;
- refactoring generale del repository non necessario alla stabilizzazione.

## 15. Superficie di implementazione prevista

La fase di implementazione successiva dovrà restare confinata, salvo necessità dimostrata, a:

- workflow `CEW-CONTRACT-01 Closure Gate`;
- validator di closure;
- replay harness deterministico;
- Frozen Authority Profile o equivalente machine-checkable;
- mutation suite;
- test del contratto CI;
- receipt durevole della verifica storica di transizione;
- Qualification Report / PR body per riflettere il nuovo modello di assurance.

Non sono autorizzate modifiche ai dati tecnici canonici N12.

## 16. Strategia di implementazione richiesta

L'implementazione dovrà seguire TDD RED → GREEN per blocchi di invarianti, non per finding individuali.

Ordine concettuale:

1. congelare authority e failure taxonomy;
2. introdurre i test di mutazione che dimostrano i false-positive correnti;
3. rendere durevole la verifica storica e rimuovere la dipendenza dall'artifact runtime;
4. introdurre il replay deterministico;
5. completare builder/registration invariants;
6. eseguire l'intera mutation suite;
7. eseguire happy path exact-head;
8. richiedere fresh review indipendente;
9. applicare la finding triage policy;
10. promuovere la PR a Ready for review solo se il criterio di arresto è soddisfatto.

Nessun merge automatico è autorizzato da questa specifica.

## 17. Esito atteso

Il risultato finale deve essere un gate che non sia semplicemente "verde oggi", ma che abbia una superficie di assurance dichiarata e finita:

> CEW-CONTRACT-01 è qualificato perché il gate dimostra, con replay deterministico e mutation testing, che l'autorità congelata, la provenienza, gli stati epistemici, la ModelGeneration, la Verification e la Receipt restano coerenti e fail-closed; il gate non dipende da storage temporaneo, non autorizza il calcolo strutturale e non può essere esteso indefinitamente da review che introducono requisiti fuori dal perimetro approvato.
