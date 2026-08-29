# M0-G — Allineamento Telaio 5 ↔ TAV.5

Versione: `M0G-T5-ALIGN-0001` — 2026-08-16

## Correzione di metodo

Il Telaio 5 deve esistere nella carpenteria: l'edificio è stato progettato e costruito e il percorso `S–S'–T–U–V–Z–A'–B'–C'` è documentato dalla relazione/pianta dei telai.

Il problema non è quindi stabilire se il telaio esista, ma **allineare correttamente sistemi di riferimento diversi**:

1. schema storico del telaio con nodi letterali;
2. tavola TAV.5 digitalizzata con nodi Nxxx;
3. carpenterie originali PDF ad alta risoluzione;
4. abaco 57 nodi;
5. registro connessioni candidate, che include anche nodi superiori a N057;
6. modello EdiLus, che richiede livelli e fili coerenti.

## Dati fissi

- percorso planimetrico: `S–S'–T–U–V–Z–A'–B'–C'`;
- campate: `4.70 / 4.05 / 1.20 / 5.80 / 2.90 / 1.20 / 4.05 / 4.70 m`;
- G5: `C2–C7 = 19.20 m`, con C1 e C8 assenti;
- altezza interpiano estradosso-estradosso: `3.20 m` come dato riferito corretto.

## Stato della matrice candidati

È stata creata `data/canonical/telaio5_tav5_candidate_matrix_v1.csv`.

La matrice contiene:

- `HYP_A_METRICA`: sequenza metricamente coerente ma non ancora confermata dal registro connessioni e dalla tavola originale;
- `HYP_B_CONNESSA`: sequenza più coerente con alcune connessioni del registro ma metricamente più debole e quindi non promossa.

Nessuna ipotesi è `VER`.

## Regola di promozione

Una corrispondenza parziale può passare a `VER_PARZIALE` soltanto se soddisfa insieme:

1. campata metrica coerente;
2. continuità di percorso C1–C8;
3. orientamento compatibile con la pianta dei telai;
4. riscontro visivo sulla carpenteria originale ad alta risoluzione;
5. coerenza con le sezioni del Telaio 5 nei livelli G1–G5.

## Passo successivo

Produrre una tavola di confronto/overlay tra:

- nodi letterali `S–...–C'`;
- candidati Nxxx TAV.5;
- segmenti C1–C8;
- quote 4.70/4.05/1.20/5.80/2.90/1.20/4.05/4.70;
- indicazione `RIF/INF/VER`.

Questo è il passaggio corretto per allineare bene tutto: non fermarsi davanti a un primo candidato debole, ma convergere sul percorso esistente mediante sovrapposizione dei sistemi.
