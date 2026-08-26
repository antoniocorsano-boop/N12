# CEW Document Intelligence Foundation v0

Modulo sperimentale, non promotivo, nato dal commit canonico `232338a24363a14ddcecc25bb331762870e010f7`.

Scopo: rendere operativa in un unico punto la gestione di originali, versioni immutabili, osservazioni indicizzate, convenzioni grafiche e proposte agentiche, senza autorizzare F3/F5 e senza trasformare automaticamente un candidato in dato canonico.

## Avvio rapido

```bash
python tools/cew_docintel/cli.py init
python tools/cew_docintel/cli.py ingest analysis/source_renders/TAV07/r1_c3.jpg --source-id TAV07-R1C3 --label "TAV.7 tile r1_c3"
python tools/cew_docintel/cli.py status
```

Il database locale predefinito è `.cew/docintel.sqlite3` ed è ricostruibile. Gli originali non vengono copiati né modificati: vengono registrati percorso, dimensione, SHA-256 e versione.

## Registrare una lettura

```bash
python tools/cew_docintel/cli.py observe \
  --source-version-id <id> \
  --page 1 \
  --kind symbol \
  --bbox 100,200,160,260 \
  --value "rect|grid-intersection" \
  --confidence 0.88 \
  --detector scan2dxf-v0.2
```

Stati ammessi: `DETECTED`, `CANDIDATE`, `SUPPORTED`, `VALIDATED`, `REJECTED`. Il comando `observe` crea sempre `CANDIDATE` salvo richiesta esplicita di uno stato inferiore; non crea mai `CANONICAL`.

## KB convenzioni grafiche

```bash
python tools/cew_docintel/cli.py convention-add \
  --name COLUMN_PLAN_MARKER \
  --meaning structural_column_candidate \
  --scope '{"project":"N12","drawing_type":"carpenteria"}'
```

La KB conserva definizione, significato, scope e stato. Una convenzione nasce `CANDIDATE`.

## Agente-curatore deterministico v0

```bash
python tools/cew_docintel/cli.py curate --min-occurrences 3
python tools/cew_docintel/cli.py proposals
```

Il curatore raggruppa osservazioni candidate ricorrenti per `kind + value` e produce proposte `PROPOSED`. Non approva nulla.

Per una decisione umana:

```bash
python tools/cew_docintel/cli.py proposal-review <proposal-id> --decision VALIDATED --reviewer human
```

La decisione aggiorna la proposta; non modifica dati canonici N12 e non avanza milestone CEW.

## Indici disponibili v0

- SHA-256 e identità fonte/versione;
- indice testuale su `kind`, `value_text`, `detector`;
- coordinate `x0,y0,x1,y1` interrogabili in SQLite;
- stato e confidenza;
- convenzioni grafiche per nome/significato/scope;
- proposte agentiche con conteggio delle evidenze.

## Gate

```bash
python tools/cew_docintel/cli.py validate
python -m unittest discover -s tools/cew_docintel/tests -v
```

Principio obbligatorio: `SourceVersion -> Observation -> Proposal/Convention`. Nessuna promozione automatica a `VALIDATED` o `CANONICAL`.