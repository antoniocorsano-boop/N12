# N12 — Edificio esistente in c.a. — Ariano Irpino

Repository canonico per la ricostruzione, modellazione e verifica dell'edificio esistente in cemento armato e per la preparazione del modello EdiLus-EE.

## Avvio obbligatorio

Prima di lavorare sul progetto leggere `AGENTS.md`. La memoria operativa persistente e' in `memory/`:

- `memory/PROJECT_STATE.md` — stato canonico corrente e prossima azione;
- `memory/SOURCE_REGISTRY.csv` — fonti originali con riferimenti Git immutabili;
- `memory/ARTIFACT_INDEX.csv` — indice degli elaborati, posizione e rigenerabilita';
- `memory/OPEN_RESIDUALS.csv` — residui espliciti e non bloccanti.

La chat e il runtime temporaneo non sono memoria canonica. Un elaborato utile deve essere versionato, puntato da un riferimento Git immutabile oppure reso deterministicamente rigenerabile.

Protocollo completo: `docs/REPOSITORY_MEMORY_PROTOCOL.md`.

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

Lo stato operativo dettagliato non viene duplicato qui: usare `memory/PROJECT_STATE.md` come snapshot canonico corrente.

## Struttura del repository

- `memory/` — bootstrap di continuita', stato, fonti, elaborati e residui;
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

Prima di procedere con una nuova informazione utile, aggiornare il patrimonio canonico con provenienza, stato di evidenza e versione. Git e' la fonte di verita' dello stato consolidato; ZIP e fotografie originali restano fonti/evidenze e non sostituiscono il Registro Master.
