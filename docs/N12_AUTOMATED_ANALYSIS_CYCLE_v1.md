# N12 — Ciclo automatico di analisi strutturale v1

## Scopo

Trasformare l'analisi delle tavole strutturali N12 da sequenza manuale dipendente dalla conversazione a processo persistente, ripetibile e controllato da gate.

Il sistema usa due livelli:

1. **orchestrazione deterministica**: bootstrap, scelta del prossimo task, verifica dipendenze/input, render, controlli di coerenza, gestione residui, validazione del sistema di conoscenza, report del ciclo;
2. **lettura specialistica agentica**: interpretazione di quote, simboli, sezioni, identità, orientamenti e topologie quando la sorgente grafica richiede giudizio semantico.

L'assenza di un executor agentico non autorizza l'orchestratore a sostituire la lettura della tavola con inferenze.

## Entrypoint

- contratto: `automation/N12_AUTOMATION_CONTRACT_v1.json`
- coda persistente: `automation/N12_WORK_QUEUE_v1.json`
- contratto di ritorno semantico: `automation/N12_AGENT_RESULT_CONTRACT_v1.json`
- runner: `python scripts/n12_orchestrator.py`
- ingestor: `python scripts/n12_ingest_agent_result.py`
- inbox: `automation/inbox/N12_AGENT_RESULT.json`

Comandi:

```bash
python scripts/n12_orchestrator.py validate
python scripts/n12_orchestrator.py status
python scripts/n12_orchestrator.py run
python scripts/n12_ingest_agent_result.py validate
```

`run` produce `analysis/automation/N12_CYCLE_REPORT.json`; in CI il report viene pubblicato come artefatto e non diventa automaticamente dato canonico.

## Ciclo

`S0 bootstrap -> S1 source ready -> S2 specialist reading -> S3 metric/topology checks -> S4 crosscheck -> S5 promotion gate -> result handshake -> S6 state advance -> next item`

### S0 — Bootstrap

Controlla manifest, stato corrente, registri, skill, coda di lavoro e contratto di ritorno dell'agente. Un errore di contratto arresta il ciclo prima di leggere o scrivere dati strutturali.

### S1 — Source ready

Verifica che gli input canonici e le fonti primarie richieste dal work item siano disponibili. Render e crop sono derivati di visualizzazione: non sostituiscono la fonte primaria.

### S2 — Lettura specialistica

L'agente legge la tavola del piano corrente **indipendentemente**. È vietato riempire valori mancanti copiandoli da PT o da un piano adiacente. Ogni claim conserva `DOC/MIS/RIF/INF/INC/ND`.

Ogni esecuzione tratta **un solo work item**. Se la lettura è incompleta, il risultato non viene completato per analogia: la singola claim resta `INC/ND` o viene registrata come residuo.

### S3 — Controlli metrici e topologici

Controlla identità, residui di registrazione, orientamento delle sezioni, well-formedness della struttura intelaiata, presenza/terminazione dei sostegni e regole anti-estrusione.

### S4 — Crosscheck

Confronta piani adiacenti esclusivamente per rilevare continuità, variazioni o conflitti. L'uguaglianza fra due piani non è prova documentale: il valore deve essere leggibile anche sulla tavola corrente oppure restare non documentato.

### S5 — Promotion gate

Un output può diventare canonico solo quando:

- esiste;
- ha provenienza esplicita;
- ha audit/gate richiesti;
- non contiene conflitti bloccanti;
- è registrato con autorità e stato coerenti;
- i controlli semantici richiesti sono superati.

`MIS` non diventa `DOC` per coerenza geometrica o per ripetizione fra piani.

### Result handshake — ritorno controllato dell'agente

L'agente non può avanzare liberamente la coda. Dopo la lettura produce `automation/inbox/N12_AGENT_RESULT.json`, conforme a `N12_AGENT_RESULT_CONTRACT_v1.json`.

Il pacchetto deve riferirsi **esattamente al work item selezionato** e deve dichiarare:

- tavola primaria;
- decisione `PASS / PASS_WITH_WATCH / RESIDUAL / BLOCKED / CONFLICT`;
- stato del gate semantico;
- esattamente gli output previsti dalla coda;
- conteggio/profilo di provenienza `DOC/MIS/RIF/INF/INC/ND`;
- residui;
- audit utilizzati.

Per `PASS` e `PASS_WITH_WATCH` l'ingestor verifica che gli output siano già presenti nel registry effettivo con autorità `CANONICAL` o `DERIVED`, stato non bloccante e `may_feed_canonical` compatibile. L'ingestor **non crea né promuove evidenza**: accerta che i presupposti di promozione esistano e soltanto dopo aggiorna coda e stato.

Dopo l'ingestione il risultato viene archiviato come receipt in `automation/receipts/` e l'inbox viene liberato.

### S6 — Avanzamento

Dopo il PASS si aggiornano coda e `CURRENT_STATE`. Si rilascia soltanto il work item successivo le cui dipendenze sono soddisfatte.

Per `RESIDUAL` il work item resta in revisione. Per `BLOCKED` o `CONFLICT` non avviene promozione; il sistema conserva la causa e si arresta o prosegue soltanto su eventuali rami realmente indipendenti.

## Stati e comportamento

- `PASS_ADVANCE`: può avanzare.
- `PASS_WITH_WATCH_ADVANCE`: avanza mantenendo il WATCH tracciato.
- `READY_FOR_AGENT`: input e contratti sono pronti; serve lettura specialistica.
- `RESIDUAL_REVIEW`: il residuo è isolato e non blocca task indipendenti.
- `BLOCKED_DEPENDENCY`: manca un predecessore.
- `BLOCKED_INPUT`: manca una fonte o un artefatto richiesto.
- `CONFLICT_STOP`: si riapre il claim minimo coinvolto.
- `FAIL_STOP`: errore di contratto/validazione; nessuna promozione.
- `COMPLETE`: coda terminata.

## Pianificazione automatica

GitHub esegue i workflow `schedule` soltanto dal ramo predefinito. Per questo il battito periodico è definito su `main` in:

`.github/workflows/n12-analysis-scheduler.yml`

Il scheduler **non usa `main` come fonte strutturale**: esegue checkout esplicito di `work/m0-global-model`, lancia render, validator, eventuale ingestione di un solo risultato, report e pacchetto del task successivo. Se deve persistere l'avanzamento, effettua il push soltanto verso `work/m0-global-model`.

Il workflow presente sul ramo canonico:

`.github/workflows/n12-analysis-orchestrator.yml`

resta il controllo automatico su push e su avvio manuale. Entrambi condividono lo stesso gruppo di concorrenza, quindi due cicli non possono ingerire simultaneamente lo stesso risultato.

È inoltre configurato un executor specialistico pianificato sul progetto, con cadenza di 6 ore e limite di un work item per esecuzione. Il primo receipt semantico resta il gate di prova del collegamento completo.

## Regole strutturali permanenti

- Nessuna estrusione cieca dei 38 sostegni PT.
- `a-b-c-d` non proseguono sopra G1.
- `1,8,9,16,17,24,31,32,33` non vengono propagati a G5.
- Le sezioni vengono lette indipendentemente su TAV-03S, TAV-04S, TAV-05S e TAV-06S.
- Le travi vengono ricostruite indipendentemente su ogni carpenteria.
- I sostegni estesi mantengono sagoma e facce; il baricentro non sostituisce automaticamente i nodi di attestazione.
- Le quote scritte e gli identificativi espliciti hanno priorità su scala raster, dataset storici e inferenze.
- Un residuo non blocca il resto del modello se è isolabile.
- Una nuova evidenza riapre il **claim minimo**, non l'intero piano o l'intero progetto.
- Un agente non può eseguire più di un work item nello stesso result handshake.

## Coda iniziale

La prima coda verticalizza il lavoro già iniziato:

1. sezioni G2/TAV-03S;
2. sezioni G3/TAV-04S;
3. sezioni G4/TAV-05S;
4. sezioni G5/TAV-06S;
5. travi G2;
6. travi G3;
7. travi G4;
8. travi/copertura G5, comprese travi di colmo e gronda;
9. segmenti verticali dei pilastri;
10. indice topologico travi per piano.

La coda è un contratto operativo: l'agente non deve inventare il prossimo lavoro dalla cronologia della chat.

## Limite dell'automazione

GitHub Actions può eseguire automaticamente la parte deterministica, produrre render/report, ingerire un risultato specialistico già validabile e avanzare lo stato. La lettura semantica delle immagini resta responsabilità di un executor agentico autorizzato.

Se l'executor non è disponibile, il sistema deve fermarsi a `READY_FOR_AGENT`, non degradare i gate e non promuovere inferenze come dati documentali. Se l'executor è disponibile ma la fonte è ambigua, deve restituire `RESIDUAL`, `BLOCKED` o `CONFLICT`, non inventare un `PASS`.
