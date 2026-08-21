# Stato di ripresa N12

Data: 2026-08-21

## Fonte di verità operativa

Repository GitHub `antoniocorsano-boop/N12`, ramo di lavoro `work/m0-global-model`.

Lo stato macchina autoritativo è:

`knowledge/CURRENT_STATE.json`

Questo documento è la vista umana sintetica e non deve divergere dal file macchina.

## Gate globale

`M0-G` — geometria globale tridimensionale dell'intero edificio esistente in c.a.

## Sotto-gate corrente

`M0-G/PT-RASTER-G1` — registrazione indipendente sul raster TAV-02S dei centri/sagome dei sostegni del piano terra.

## Decisione corrente

Le coordinate geometriche contenute nel precedente `data/canonical/PT_MASTER_CURRENT.csv` sono **SUSPENDED come autorità geometrica**. Restano conservate per provenienza, ma non possono essere usate per confermare sé stesse.

La ricostruzione PT riparte dalle fonti senza perdere il patrimonio validato:

`raster/ID/simbologia -> centri pixel -> quote documentali -> rete metrica -> supporti fisici -> travi documentate -> nodi analitici -> overlay QA -> nuovo Master`.

Le sezioni/orientamenti documentati e gli altri domini indipendenti non vengono annullati dalla sospensione delle coordinate PT.

## Prossima azione autorizzata

Creare e validare:

`data/canonical/PT_PIXEL_SUPPORT_REGISTRY_v1.csv`

registrando direttamente dal raster nativo:

- P1-P33;
- P22';
- a, b, c, d;
- contorni/facce dei sostegni estesi quando leggibili.

È vietato usare come input le coordinate metriche del vecchio Master.

## Skill attive

- `skills/pt-carpentry-reader/SKILL.md`
- `skills/pt-raster-grid-reconstructor/SKILL.md`

## Regola sostegno/nodo

Un sostegno fisico non coincide necessariamente con un solo nodo analitico. Per pilastri-setti o supporti estesi, travi incidenti in punti differenti generano nodi distinti associati allo stesso `support_id`.

## Sistema di continuità

Ogni agente deve iniziare da `AGENTS.md`, quindi leggere:

1. `knowledge/KNOWLEDGE_MANIFEST.json`;
2. `knowledge/CURRENT_STATE.json`;
3. `knowledge/ARTIFACT_REGISTRY.csv`.

Un file non registrato è non autoritativo per impostazione predefinita.

## Validazione

Eseguire prima della chiusura di ogni avanzamento:

`python scripts/validate_knowledge_system.py`

Il gate PT resta aperto finché non sono soddisfatti anche i controlli della skill `pt-raster-grid-reconstructor` e l'overlay semantico sul raster.