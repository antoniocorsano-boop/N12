# M0-G — Raccordo Telaio 5 ↔ 57 nodi — Decisione v1

## Obiettivo

Chiudere il residuo `R-v17-01`: associare il percorso planimetrico del Telaio 5

`S–S'–T–U–V–Z–A'–B'–C'`

agli identificatori canonici dei 57 nodi topologici ricostruiti storicamente.

## Evidenza disponibile nel ramo corrente

- `data/canonical/telaio_5.csv` contiene la geometria documentale del Telaio 5:
  - G5: `1–7`, campate `C2–C7`, sviluppo 19.20 m;
  - G4/G3/G2/G1: `C1–C8`, sviluppo 28.60 m;
  - sequenza metrica: 4.70 / 4.05 / 1.20 / 5.80 / 2.90 / 1.20 / 4.05 / 4.70 m.
- `data/canonical/nodes.csv` contiene 27 record relativi alle catene verticali dei pilastri da `CATENE_VERTICALI_PILASTRI_v20.csv`.
- `docs/REGISTRO_MASTER.md` registra il dato storico `57 nodi / 38 connessioni / 10 componenti` e l'abaco `ABACO_TOPOLOGICO_TAV5_v11.csv`, ma il file fisico corrispondente non risulta ancora presente tra i dataset canonici del ramo.

## Decisione

Il raccordo Telaio 5 → 57 nodi non viene promosso a `DOC` né a `VER` in assenza del dataset fisico dei 57 nodi.

Il file `nodes.csv` attuale non deve essere usato come surrogato dell'abaco topologico TAV.5, perché rappresenta i riferimenti geometrici verticali dei pilastri, non l'intera rete topologica di 57 nodi.

## Stato del residuo

`R-v17-01 = BLOCCATO_PARZIALE`

La geometria del Telaio 5 è documentale; il raccordo agli ID topologici rimane non congelato.

## Prossima azione vincolata

Recuperare o ripristinare nel repository uno dei seguenti artefatti:

1. `ABACO_TOPOLOGICO_TAV5_v11.csv`;
2. dataset equivalente contenente i 57 nodi con coordinate;
3. registro delle connessioni associato ai 57 nodi, se separato.

Dopo il recupero, il controllo dovrà usare simultaneamente:

- percorso letterale `S–S'–T–U–V–Z–A'–B'–C'`;
- firma metrica `4.70 / 4.05 / 1.20 / 5.80 / 2.90 / 1.20 / 4.05 / 4.70`;
- continuità di livello G1–G5;
- sezioni e tratti speciali già consolidati;
- connettività TAV.5/TAV.6/TAV.7.

Solo la convergenza di questi elementi può chiudere `R-v17-01`.
