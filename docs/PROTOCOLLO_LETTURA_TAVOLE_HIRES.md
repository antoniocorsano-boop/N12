# Protocollo canonico di lettura tavole ad alta risoluzione

## Scopo
Questo protocollo governa la lettura dei PDF/raster originali del Condominio N.12 e la loro trasformazione in dati strutturali tracciabili per il modello M0-G.

## Principio di autorita' delle fonti
Ordine di precedenza:
1. PDF/raster originale immutabile (DOC)
2. misura diretta da raster calibrato o quota leggibile (MIS/DOC secondo il caso)
3. informazione riferita (RIF)
4. ricostruzione/inferenza geometrica (INF)
5. dato non disponibile (ND)

DXF, abachi, CSV e topologie derivate non possono sovrascrivere una sorgente originale. Ogni promozione INF -> DOC richiede evidenza documentale verificabile.

## Grammatica canonica del disegno strutturale
La lettura non deve classificare le forme geometriche isolate dal contesto grafico. Prima si identifica la funzione convenzionale del simbolo, poi si rilevano geometria e coordinate.

### Rettangoli e sezioni
Regola canonica verificata sulle carpenterie del progetto:
- rettangolo con numero identificativo interno, collocato nella posizione di un sostegno verticale: candidato pilastro/setto; la classificazione definitiva richiede riscontro con abaco pilastri/tavola pertinente;
- rettangolo senza numero identificativo interno, collocato lungo lo sviluppo di una trave: rappresentazione convenzionale della sezione trasversale della trave, non pilastro;
- il rettangolo-sezione della trave e' informazione locale di sezione e non genera un nodo strutturale né una catena verticale;
- posizione, orientamento e dimensioni grafiche del rettangolo-sezione non devono essere utilizzati per dedurre automaticamente posizione o ingombro di un pilastro;
- una forma simile puo' avere significato diverso in tavole diverse: prevalgono numerazione, richiami, continuita' grafica, legenda, quote e relazione con gli elementi adiacenti.

### Pilastri e setti
Un sostegno verticale non e' ridotto automaticamente a un punto. Per ciascun elemento, quando documentabile, registrare:
- identificativo;
- filo fisso/i di riferimento;
- sezione reale e orientamento;
- facce geometriche;
- eventuale asse baricentrico, distinto dal filo fisso;
- attacchi delle travi alle singole facce e relativi offset/eccentricita'.

Per sezioni allungate, ad esempio 30x110 cm, e' vietato collassare l'elemento in un unico nodo prima di aver determinato fili fissi, facce e modalita' di attestazione delle travi.

### Travi
Per ogni trave distinguere:
- asse o linea di riferimento;
- larghezza e altezza di sezione;
- eventuale rettangolo di sezione rappresentato in mezzeria o in altra posizione convenzionale;
- estremita' geometrica reale;
- faccia del sostegno sulla quale la trave si attesta;
- eventuale eccentricita' rispetto al filo fisso o all'asse del sostegno.

### Regola anti-falso-nodo
Nessun simbolo grafico diventa nodo, pilastro o setto per sola somiglianza geometrica. La classificazione richiede almeno due segnali coerenti fra: numero identificativo, posizione nel reticolo, continuita' verticale, richiamo di sezione, abaco pilastri, quote, fili fissi, connessioni di trave.

## Identificazione sorgente
Per ogni tavola registrare almeno:
- id canonico tavola
- nome file originale
- percorso Git storico
- commit sorgente
- SHA256
- dimensione file
- classe documentale
- dimensioni raster native
- codec/filtri PDF

## Pipeline di lettura
1. Acquisire il PDF originale dal commit storico senza modificarlo.
2. Verificare hash rispetto al manifest.
3. Ispezionare struttura PDF e dimensioni del raster nativo.
4. Estrarre/renderizzare senza perdita, preferendo il raster nativo quando il PDF contiene una sola immagine.
5. Generare una vista generale di orientamento.
6. Suddividere la pagina in tasselli regolari con sovrapposizione minima del 10-15%.
7. Conservare per ogni tassello le coordinate nel sistema pagina/raster (u,v).
8. Applicare prima la grammatica canonica del disegno: distinguere simboli di sezione, sostegni, travi, quote, fili fissi e richiami.
9. Leggere quindi la geometria strutturale: fili fissi, facce dei sostegni, assi/linee delle travi, bordi, campate.
10. Leggere quote, numeri e sigle separatamente e collegarli agli oggetti gia' classificati.
11. Registrare ogni evidenza nel registro di lettura con sorgente, tassello, coordinate e stato.
12. Eseguire controlli topologici: continuita', grado dei nodi, chiusura delle catene, assenza di nodi fuori pianta.
13. Eseguire controlli metrici: somme campate, quote concatenate, simmetrie dichiarate, compatibilita' con altri elaborati.
14. Costruire overlay della geometria ricostruita sulla sorgente originale.
15. Se overlay o controlli falliscono, mantenere il dato come residuo INF/ND; non forzare la chiusura.
16. Solo dopo validazione trasformare (u,v) -> coordinate metriche -> M0-G globale.

## Sistema di coordinate
Il sistema M0-G e' unico per fondazioni, pilastri, travi, impalcati e copertura. Nessuna tavola possiede un proprio sistema strutturale definitivo. Le coordinate pagina (u,v) restano sempre conservate come provenienza e vengono trasformate tramite una trasformazione esplicita e versionata.

La trasformazione geometrica deve riferirsi prioritariamente a fili fissi e quote documentate, non ai centri apparenti dei simboli grafici.

## Tassellazione standard
Per tavole raster di grandi dimensioni:
- livello L0: pagina completa, solo orientamento
- livello L1: griglia 3x3, overlap 12.5%
- livello L2: ulteriori ritagli locali sui nodi/quote critiche
- nessun OCR massivo come fonte geometrica
- OCR solo selettivo per sigle/quote dopo la lettura visuale

Ogni tassello riceve id stabile: `TAV-<id>_L<livello>_R<riga>C<colonna>`.

## Registro evidenze
Campi minimi:
`evidence_id, tavola_id, source_commit, source_sha256, tile_id, u0, v0, u1, v1, object_type, object_id, value, unit, status, confidence, crosscheck, notes`

Per sostegni e attacchi trave aggiungere, quando applicabile:
`fixed_line_x, fixed_line_y, face_id, section_b, section_h, rotation, beam_end_u, beam_end_v, eccentricity_x, eccentricity_y`.

## Regole di non perdita
- mai cancellare una lettura precedente: marcare SUPERATO e indicare il sostituto
- nessuna inferenza silenziosa
- ogni residuo ha id e motivo
- ogni trasformazione geometrica ha versione e parametri
- ogni output grafico deve essere rigenerabile dalla sorgente + registro
- ogni dato M0-G deve poter risalire alla zona esatta della tavola originale
- ogni errore di interpretazione grafica corretto deve diventare una regola o un caso di test della grammatica canonica

## Gate per promozione a geometria canonica
Un sostegno/asta puo' entrare nel M0-G canonico solo se:
1. la funzione del simbolo e' stata classificata secondo la grammatica del disegno;
2. posizione o filo fisso sono riconosciuti sulla tavola originale;
3. connessioni compatibili con la topologia documentale;
4. quote sufficienti o trasformazione metrica verificata;
5. per sostegni larghi, facce e attestazioni delle travi sono rappresentate correttamente;
6. overlay entro tolleranza definita;
7. nessun conflitto documentale aperto di priorita' superiore.

## Sorgenti fondazioni attuali
- TAV-01S `tavola1-2.pdf`: carpenteria strutturale, DOC
- TAV-01A `tavola1-3.pdf`: armature travi, DOC
- topologia F5-R 7 catene / 26 segmenti: derivata, usata come controllo indipendente ma non come planimetria

## Stato operativo
La TAV-01S e' stata identificata come PDF raster puro; il raster incorporato e' 6624 x 9436 px, JPEG2000. La lettura geometrica ad alta risoluzione deve avvenire su tale matrice nativa o su render equivalente senza ricampionamento distruttivo.

Correzione canonica acquisita: i rettangoli senza numero interno rappresentati lungo le travi nelle carpenterie sono sezioni trasversali convenzionali della trave e non devono essere classificati come pilastri. Le precedenti letture che li trattavano come sostegni sono SUPERATE.
