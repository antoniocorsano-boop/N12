# N12 — Edificio esistente in c.a. — Ariano Irpino

Repository canonico per la ricostruzione, modellazione e verifica dell'edificio esistente in cemento armato e per la preparazione del modello EdiLus-EE.

## Obiettivo

Costruire un fascicolo tecnico riproducibile e versionato che colleghi in modo tracciabile:

`fonti originali → evidenze → dati canonici → modello M0 → EdiLus-EE → verifiche → interventi → fascicolo finale`

## Regola di evidenza

Ogni dato strutturale deve riportare uno stato:

- `DOC` — documentale;
- `MIS` — misurato;
- `RIF` — riferito;
- `INF` — inferito;
- `INC` — incerto;
- `ND` — non disponibile.

Un dato `ND`, `INC` o `INF` non viene promosso a `DOC` per analogia o convenienza di modellazione.

## Stato corrente

- obiettivo corrente: **M0-G globale — intero modello tridimensionale**;
- Telai 1 e 5: ricostruzione avanzata dalla relazione di calcolo;
- TAV.5/TAV.6/TAV.7: esistono artefatti DXF storici 1:1;
- topologia storica: 57 nodi / 38 connessioni / 10 componenti, da interpretare come sottoinsieme selezionato e non necessariamente come universo geometrico completo;
- abaco verticale: 27×5 disponibile negli artefatti storici;
- fondazioni: topologia e armature già parzialmente consolidate;
- target applicativo: modello completo EdiLus-EE, non singoli telai isolati.

## Struttura del repository

- `docs/` — protocollo, decisioni, registro master e documentazione tecnica;
- `data/raw/` — inventario e riferimenti alle fonti originali immutabili;
- `data/canonical/` — dataset canonici correnti;
- `cad/` — carpenterie, DXF e artefatti geometrici;
- `model/M0-G/` — geometria globale;
- `model/M0-S/` — sezioni;
- `model/M0-A/` — armature;
- `model/edilus/` — pacchetti di ingresso/controllo EdiLus-EE;
- `evidence/` — matrici di riconciliazione, provenienza e verifiche;
- `archive/` — manifesti dei pacchetti storici;
- `scripts/` — validatori e generatori riproducibili.

## Principio di continuità

Prima di procedere con una nuova informazione utile, aggiornare il patrimonio canonico con provenienza, stato di evidenza e versione. Git è la fonte di verità dello stato consolidato; ZIP e fotografie originali restano fonti/evidenze e non sostituiscono il Registro Master.
