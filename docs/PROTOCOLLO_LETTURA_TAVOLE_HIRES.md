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
8. Leggere geometria prima del testo: assi, nodi, travi, pilastri, bordi, campate, sezioni.
9. Leggere quote e sigle separatamente e collegarle agli oggetti geometrici gia' individuati.
10. Registrare ogni evidenza nel registro di lettura con sorgente, tassello, coordinate e stato.
11. Eseguire controlli topologici: continuita', grado dei nodi, chiusura delle catene, assenza di nodi fuori pianta.
12. Eseguire controlli metrici: somme campate, quote concatenate, simmetrie dichiarate, compatibilita' con altri elaborati.
13. Costruire overlay della geometria ricostruita sulla sorgente originale.
14. Se overlay o controlli falliscono, mantenere il dato come residuo INF/ND; non forzare la chiusura.
15. Solo dopo validazione trasformare (u,v) -> coordinate metriche -> M0-G globale.

## Sistema di coordinate
Il sistema M0-G e' unico per fondazioni, pilastri, travi, impalcati e copertura. Nessuna tavola possiede un proprio sistema strutturale definitivo. Le coordinate pagina (u,v) restano sempre conservate come provenienza e vengono trasformate tramite una trasformazione esplicita e versionata.

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

## Regole di non perdita
- mai cancellare una lettura precedente: marcare SUPERATO e indicare il sostituto
- nessuna inferenza silenziosa
- ogni residuo ha id e motivo
- ogni trasformazione geometrica ha versione e parametri
- ogni output grafico deve essere rigenerabile dalla sorgente + registro
- ogni dato M0-G deve poter risalire alla zona esatta della tavola originale

## Gate per promozione a geometria canonica
Un nodo/asta puo' entrare nel M0-G canonico solo se:
1. posizione riconosciuta sulla tavola originale;
2. connessioni compatibili con la topologia documentale;
3. quote sufficienti o trasformazione metrica verificata;
4. overlay entro tolleranza definita;
5. nessun conflitto documentale aperto di priorita' superiore.

## Sorgenti fondazioni attuali
- TAV-01S `tavola1-2.pdf`: carpenteria strutturale, DOC
- TAV-01A `tavola1-3.pdf`: armature travi, DOC
- topologia F5-R 7 catene / 26 segmenti: derivata, usata come controllo indipendente ma non come planimetria

## Stato operativo
La TAV-01S e' stata identificata come PDF raster puro; il raster incorporato e' 6624 x 9436 px, JPEG2000. La lettura geometrica ad alta risoluzione deve avvenire su tale matrice nativa o su render equivalente senza ricampionamento distruttivo.
