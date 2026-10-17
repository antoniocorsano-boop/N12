# M0-G — Stato corrente

**Gate:** M0-G — geometria globale dell'intero edificio.

## Baseline documentale

Il pacchetto M0 v18 classificava `M0-G-01` (coordinate planimetriche / raccordo ID nodi) come bloccante e prescriveva di non ricostruire da zero l'artefatto storico. Il successivo recupero del pacchetto DXF strutturale v25 rende disponibile la sorgente geometrica storica da validare e normalizzare.

## Artefatti sorgente da normalizzare

- `TAV5_CARPENTERIA.dxf`
- `TAV6_TRAVI.dxf`
- `TAV7_PILASTRI.dxf`
- `ABACO_TOPOLOGICO_TAV5_v11.csv`
- `ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv`
- `MATRICE_PILASTRI_27x5_v22.csv`
- `ABACO_TRAVI_TAV6_v23.csv`
- `ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv`

## Regole

1. Le coordinate dell'abaco topologico sono la base geometrica storica da verificare contro il DXF.
2. I 57 nodi storici non sono assunti automaticamente come universo geometrico completo: registri precedenti contengono riferimenti a ID superiori.
3. Le associazioni TAV.5↔TAV.6 delle travi restano geometriche finché non ricevono un secondo discriminante documentale.
4. I Telai 1 e 5 della relazione sono vincoli indipendenti di controllo metrico/sezionale.
5. Le quote Z restano `ND/INC` finché non congelate documentalmente.
6. Nessun dato `INF/INC/ND` viene promosso per rendere il modello apparentemente completo.

## Criterio di chiusura M0-G

M0-G sarà chiuso quando saranno disponibili e validati:

- catalogo globale dei nodi planimetrici con coordinate;
- connettività strutturale per impalcato;
- continuità verticale dei pilastri;
- sagoma di ciascun livello e arretramenti;
- raccordo dei Telai 1 e 5 con la carpenteria;
- quote Z documentate o esplicitamente approvate come ipotesi di modello;
- fondazioni raccordate allo stesso sistema geometrico.

## Prossima azione

Estrarre/normalizzare `ABACO_TOPOLOGICO_TAV5_v11.csv` e `MATRICE_PILASTRI_27x5_v22.csv`, quindi costruire il dataset canonico `nodes.csv` + `vertical_columns.csv` e verificarlo contro TAV.5/TAV.7.
