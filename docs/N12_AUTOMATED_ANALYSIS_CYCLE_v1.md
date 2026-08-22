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
- runner: `python scripts/n12_orchestrator.py`

Comandi:

```bash
python scripts/n12_orchestrator.py validate
python scripts/n12_orchestrator.py status
python scripts/n12_orchestrator.py run
```

`run` produce `analysis/automation/N12_CYCLE_REPORT.json`; in CI il report viene pubblicato come artefatto e non diventa automaticamente dato canonico.

## Ciclo

`S0 bootstrap -> S1 source ready -> S2 specialist reading -> S3 metric/topology checks -> S4 crosscheck -> S5 promotion gate -> S6 state advance -> next item`

### S0 — Bootstrap

Controlla manifest, stato corrente, registri, skill e coda di lavoro. Un errore di contratto arresta il ciclo prima di leggere o scrivere dati strutturali.

### S1 — Source ready

Verifica che gli input canonici e le fonti primarie richieste dal work item siano disponibili. Render e crop sono derivati di visualizzazione: non sostituiscono la fonte primaria.

### S2 — Lettura specialistica

L'agente legge la tavola del piano corrente **indipendentemente**. È vietato riempire valori mancanti copiandoli da PT o da un piano adiacente. Ogni claim conserva `DOC/MIS/RIF/INF/INC/ND`.

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

### S6 — Avanzamento

Dopo il PASS si aggiornano l'artefatto specialistico, il registro di autorità, la coda e `CURRENT_STATE`. Si rilascia soltanto il work item successivo le cui dipendenze sono soddisfatte.

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

GitHub Actions può eseguire automaticamente la parte deterministica e produrre render/report. La lettura semantica autonoma delle immagini richiede un executor agentico autorizzato. Finché tale executor non è collegato, il sistema deve fermarsi a `READY_FOR_AGENT`, non degradare i gate e non promuovere inferenze come dati documentali.
