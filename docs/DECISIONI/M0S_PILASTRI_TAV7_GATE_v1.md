# M0-S — Gate attribuzione pilastri da TAV.7 v1

## Esito della verifica diretta

Sono stati interrogati direttamente gli artefatti v25 relativi a TAV.7.

### Evidenza documentale disponibile

- `ABACO_TIPI_DOCUMENTALI_TAV7_v22.csv`: tipo TD-P01, sezione 40x40 cm, 4 Ø14 completi + 4 Ø14 monconi, staffe Ø8; stato DOC_PARZIALE.
- `ABACO_TIPI_PILASTRO_DOC_v19.csv`: P-DOC-01 = 40x40; P-DOC-02 = 40x50; entrambi tipi documentali, non associazioni puntuali.
- `TRASCRIZIONE_TAV7_v18.csv`: armatura ricorrente leggibile sui cinque ordini; non associa il tipo a una singola catena.
- `MATRICE_PILASTRI_27x5_v22.csv`: 135 record, ma `sezione` resta ND e `tipo_TAV7` non associato.
- `CATENE_VERTICALI_PILASTRI_v20.csv`: 27 fili geometrici; `sezione_base=ND`; riduzione 40x40 all'ultimo piano dei pilastri d'angolo soltanto come RIF.
- `TAV7_PILASTRI.dxf`: contiene esplicitamente la regola «Associare solo quando sigla/sezione/dettaglio sono inequivoci» e schede L01 ancora prive di sigla/sezione compilata.

## Decisione

Non è documentariamente lecito assegnare 40x40 o 40x50 alle 27 catene sulla sola base del tipo grafico TAV.7. Di conseguenza non è lecito calcolare gli offset EdiLus delle sezioni rettangolari finché non è noto quale catena porti il 40x50 e quale faccia/angolo costituisca il filo fisso.

Questo NON riapre M0-G: i 27 fili verticali X/Y restano validi come riferimenti geometrici. Blocca soltanto la materializzazione sezionale definitiva M0-S.

## Modellazione ammessa

Per la costruzione geometrica preliminare 3D è ammesso utilizzare i 27 fili verticali come linee di riferimento senza attribuire una sezione fisica definitiva. Una eventuale sezione provvisoria di visualizzazione deve essere marcata `INF/PLACEHOLDER` e non può essere utilizzata per verifiche, rigidezze, masse o progetto degli interventi.

## Prossima risoluzione

1. ricercare negli altri consolidati/relazione eventuale tabella o richiamo che discrimini i pilastri 40x40/40x50 per posizione;
2. identificare i pilastri d'angolo del livello V dalla sagoma di impalcato, mantenendo comunque RIF finché non c'è riscontro documentale;
3. mantenere `offset_x/offset_y=ND` per il 40x50 fino alla determinazione del lato fisso;
4. proseguire in parallelo M0-G con connettività e sagome, che non dipendono dalla sezione puntuale.
