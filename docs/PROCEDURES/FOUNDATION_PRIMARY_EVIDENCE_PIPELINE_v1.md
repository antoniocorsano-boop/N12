# FPEP v1 — Foundation Primary Evidence Pipeline

Stato: WORKING CONTRACT — da integrare nel ciclo N12 prima di `M1F-FOUNDATION-MODEL`.

## 1. Scopo

Ricostruire e rivalidare la geometria delle fondazioni partendo dalla carpenteria fondazioni primaria, impedendo che topologie pregresse, armature, PT, M0-G o modello storico condizionino la lettura iniziale. Gli artefatti M1-F già prodotti restano checkpoint protetti e vengono usati solo dopo il gate della geometria primaria come regressione, binding o cross-check.

## 2. Fonte e ruoli

Il ruolo corrente delle tre fonti Tavola 1 è registrato separatamente:

- `tavola1.pdf` — architettura / controllo;
- `tavola1-2.pdf` — `TAV-01S`, carpenteria fondazioni, autorità geometrica primaria;
- `tavola1-3.pdf` — `TAV-01A`, sezioni e armature fondazioni.

La pipeline deve verificare nuovamente identità, hash e cartiglio della fonte prima della lettura. Il nome file non è da solo prova sufficiente.

## 3. Separazione epistemica

Lettura primaria e verifica regressiva sono fasi diverse.

Prima di `FPEP-P07-PRIMARY-GEOMETRY-GATE` è vietato fornire ai reader, al solver metrico o al topology builder:

- topologia fondazioni corrente;
- conteggi 38 supporti / 58 membri;
- coordinate del `PT_MASTER_CURRENT`;
- geometria M0-G;
- gruppi di armatura TAV-01A;
- topologia dei telai di calcolo storici.

Dopo P07 tali dati possono essere usati solo per binding e cross-check.

## 4. Gerarchia dell'evidenza

All'interno della fonte primaria:

`QUOTE/TESTO ESPLICITO -> ID ALFANUMERICO -> SIMBOLO INEQUIVOCO -> CONTINUITÀ GRAFICA CROSS-VALIDATED -> CONTROLLO CON ALTRA FONTE ORIGINALE -> DATASET CANONICO VALIDATO -> DATASET STORICO -> MISURA RASTER -> INFERENZA`.

La scala raster non sostituisce una quota scritta. La coincidenza grafica non sostituisce un'identificazione strutturale.

## 5. Ciclo specialistico

La coda macchina è `automation/N12_FOUNDATION_WORK_QUEUE_v1.json`.

Sequenza:

1. `P00 STATE CONSISTENCY` — verifica manifest/stato/queue/registry/riferimenti.
2. `P01 SOURCE IDENTITY` — identifica la carpenteria fondazioni primaria da fonte immutabile.
3. `P02 HIRES EVIDENCE` — overview, regioni, tile, crop e overlap con parent hash.
4. `P03A/P03B BLIND READ` — due letture indipendenti.
5. `P04 METRIC NETWORK` — quote, fili/riferimenti, catene e chiusure.
6. `P05 TOPOLOGY CANDIDATE` — grafo fondale costruito solo da osservazioni primarie cross-validate.
7. `P06 CONFLICT ADJUDICATION` — conflitti claim-by-claim e rilettura locale.
8. `P07 PRIMARY GEOMETRY GATE` — promozione K2->K3.
9. `P08 TAV01A BINDING REVIEW` — verifica sezioni/armature esistenti sulla nuova geometria.
10. `P09 HISTORICAL CALC CROSSCHECK` — delta carpenteria vs modello storico.
11. `P10 M0G REGRESSION CROSSCHECK` — confronto con PT/M0-G e checkpoint fondazioni precedente.
12. `P11 FOUNDATION INTERFACE CHECK` — quota simbolica, PT, geotecnica restano domini separati.
13. `P12 RELEASE AUDIT` — lineage, residui, receipt e release verso M1F.

## 6. Regola delle due letture

Reader A e Reader B ricevono la stessa evidenza primaria ma non vedono l'output dell'altro finché entrambe le letture non sono chiuse.

Il loro accordo non costituisce una seconda fonte indipendente e non trasforma automaticamente un claim in `DOC`. Serve a ridurre l'errore di lettura. La promozione dipende sempre dalla forza dell'evidenza primaria e dai gate del claim.

## 7. Unità di lavoro

La pipeline non rivalida file interi in blocco. Rivalida claim atomici, per esempio:

- `dimension segment D17 equals 4.05 m`;
- `support label is 22-prime`;
- `beam contour joins support X to support Y`;
- `support X and support Y are distinct`;
- `beam changes direction at support X`;
- `foundation member passes continuously through crop boundary`.

Per ogni claim devono essere conservati source id, evidence anchor, osservazioni, stato di evidenza, stato di validazione, versioni precedenti e residui.

## 8. Promozione della geometria

Un claim geometrico usato per derivare coordinate o topologia deve essere almeno `CROSS_VALIDATED` e privo di conflitti bloccanti.

Una trave può essere promossa solo quando:

1. estremi/raccordi sono identificati;
2. la continuità grafica è direttamente osservabile e, se attraversa un tile, verificata sull'overlap;
3. il segno è escluso come quota, filo, bordo, armatura o proiezione;
4. quote/ID leggibili non la contraddicono;
5. esiste un evidence anchor riproducibile.

È vietata la regola `due nodi vicini -> asta`.

## 9. Conflitti e residui

Esiti ammessi per confronto osservazioni/claim:

- `MATCH`;
- `PARTIAL_MATCH`;
- `CONFLICT`;
- `NOT_VISIBLE`.

Il Conflict Adjudicator può ordinare una rilettura locale o una nuova evidenza, ma non può inventare il valore risolutivo e non può applicare voto di maggioranza.

Un residuo deve indicare claim, evidence region, alternative compatibili, causa, evidenza richiesta e blocking flag. I residui non correlati non bloccano il resto della pipeline.

## 10. Checkpoint preesistente

La topologia M1-F corrente a 38 supporti / 58 membri è preservata integralmente come checkpoint di regressione.

Non viene fornita come target ai reader o al topology builder. Dopo P07:

- coincidenza -> `REVALIDATED`;
- differenza locale -> riapertura del claim minimo;
- contraddizione primaria che influenza M0-G -> richiesta formale `M0G-REOPEN`, mai modifica diretta.

## 11. TAV-01A

TAV-01A può associare sezioni, armature, gruppi e transizioni soltanto dopo P07. Non può creare, cancellare o spostare un membro fondale per rendere coerente uno schema di armatura.

Le lacune documentali restano `ND_DOCUMENTARY_COVERAGE`; simmetria, ricorrenza o analogia non autorizzano promozione.

## 12. Stato storico, costruito e modello corrente

Devono restare distinti:

- `HISTORICAL_CALCULATION_MODEL`;
- `DOCUMENTED_AS_BUILT`;
- `CURRENT_SURVEYED_STATE`;
- `ANALYTICAL_CHECK_MODEL`.

Il cross-check storico registra omissioni e semplificazioni senza retro-inserire elementi nel modello di calcolo originario.

## 13. Interfaccia PT / quota / geotecnica

Il passaggio del gate geometrico non assegna automaticamente:

- quota Z numerica delle fondazioni;
- stratigrafia del piano terra;
- carichi permanenti del pacchetto PT;
- rigidezza o resistenza del terreno;
- parametri di interazione terreno-struttura.

Questi restano claim separati con gate separati.

## 14. Contratto risultato

Ogni agente produce un solo risultato conforme a `automation/N12_FOUNDATION_AGENT_RESULT_CONTRACT_v1.json`. Il pacchetto deve dichiarare input e hash, fonti primarie, target, provenance, residuals, audit e attestazione delle information barriers.

L'agent confidence non è uno stato di evidenza.

## 15. Gate finale

`data/canonical/M1F_FPEP_RELEASE_GATE_v1.csv` può essere prodotto soltanto quando:

- P07 è PASS/PASS_WITH_WATCH;
- i cross-check P08-P11 sono persistiti;
- nessun conflitto geometrico bloccante è nascosto;
- lineage e residui sono completi;
- nessun flusso informativo vietato è stato usato;
- i validatori macchina sono PASS.

Solo questo release gate abilita `M1F-FOUNDATION-MODEL` nella coda principale.
