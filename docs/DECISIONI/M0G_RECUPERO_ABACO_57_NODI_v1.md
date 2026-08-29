# M0-G — Recupero abaco topologico TAV.5 a 57 nodi

Versione: `M0G-57N-0001` — 2026-08-16

## Origine

Il residuo `R-v17-01` richiedeva il raccordo tra il percorso planimetrico del Telaio 5 `S–S'–T–U–V–Z–A'–B'–C'` e gli identificatori dei 57 nodi già ricostruiti storicamente.

Nel repository era presente il dataset dei 27 fili verticali dei pilastri, ma non era ancora presente come file fisico canonico l'abaco topologico TAV.5 a 57 nodi.

## Azione eseguita

Sono stati recuperati dal pacchetto fisico `Ariano_Irpino_DXF_strutturale_v25.zip`:

- `ABACO_TOPOLOGICO_TAV5_v11.csv` → salvato come `data/canonical/tav5_topology_nodes_57.csv`;
- `REGISTRO_CONNessioni_TAV5_v07.csv` → salvato come `data/canonical/tav5_topology_connections_v07.csv`.

## Stato del dato

- `tav5_topology_nodes_57.csv`: 57 nodi topologici, stato sorgente `PREDOC_TOPOLOGICO`.
- `tav5_topology_connections_v07.csv`: 141 connessioni candidate, stato sorgente `INF_DA_QUOTARE`.

Il recupero sblocca il residuo precedente, ma non chiude ancora il raccordo Telaio 5 → 57 nodi.

## Cautela tecnica

Il registro delle connessioni contiene riferimenti a nodi oltre N057. Di conseguenza i 57 nodi rappresentano il sottoinsieme topologico consolidato, mentre la rete completa delle connessioni richiede una fase ulteriore di ricostruzione/riconciliazione delle entità N058 e successive.

La geometria del Telaio 5 resta documentale per livelli, campate e sezioni, ma non viene ancora proiettata sugli ID TAV.5 senza secondo discriminante.

## Decisione

`R-v17-01` passa da `BLOCCATO_PARZIALE` a `SBLOCCATO_DATI_RECUPERATI`, con nuovo residuo operativo:

`R-v17-01B — associare il percorso S–S'–T–U–V–Z–A'–B'–C' agli ID TAV.5 usando firma metrica + connettività + carpenterie originali.`

## Prossima azione

Costruire la matrice di confronto:

`Telaio 5 C1–C8 / G1–G5 → candidati TAV.5 → distanze → orientamento → nodi mancanti → stato`

Sarà ammessa soltanto associazione `VER` con almeno due elementi coerenti: firma metrica e posizione/topologia, oppure firma metrica e riscontro sulla carpenteria originale.