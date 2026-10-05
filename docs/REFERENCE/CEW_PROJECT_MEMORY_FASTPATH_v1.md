# CEW Project Memory Fast Path v1

**Stato:** HUMAN_APPROVED — ACTIVE_DESIGN
**Data:** 2026-10-03

## Scopo

Ridurre il costo di orientamento tra sessioni e agenti senza creare una nuova fonte di verità parallela.

## Decisione

Il sistema di memoria di progetto resta quello già definito da N12:

`AGENTS.md -> KNOWLEDGE_MANIFEST -> CURRENT_STATE -> ARTIFACT_REGISTRY -> gate/receipt`

Viene aggiunto un solo artefatto derivato e rigenerabile:

`knowledge/CONTEXT_PACK_CURRENT.json`

Il pacchetto contiene esclusivamente il contesto minimo per orientarsi: gate, work item, next action, riferimenti correnti, invarianti e fingerprint delle fonti che lo hanno generato.

## Regola di utilizzo

- **Orientamento / ripresa sessione:** leggere il Context Pack e i soli documenti in `docs/REFERENCE/` indicizzati nel pack.
- **Mutazione ingegneristica:** prima di scrivere dati canonici leggere comunque manifest, stato, registry, protocollo e contratti del work item.
- **Mutazione di prodotto/governance:** leggere lo stato CEW e il governance manifest completi.
- **Diagnostica profonda:** `python scripts/agent_bootstrap.py --full` espande il registry effettivo.

Il pacchetto compatto non sostituisce le fonti canoniche e non può promuovere alcun dato.

## Riferimenti importanti

Un documento approvato che deve costituire memoria stabile del programma viene collocato in `docs/REFERENCE/`.
Il generatore indicizza automaticamente:

- percorso;
- titolo;
- stato dichiarato;
- SHA-256.

L'inclusione in `docs/REFERENCE/` rende il documento **riferimento di contesto**, non autorità sui fatti strutturali.

## Aggiornamento automatico

Il workflow `refresh-cew-context.yml` rigenera il Context Pack quando cambiano:

- `knowledge/CURRENT_STATE.json`;
- `knowledge/KNOWLEDGE_MANIFEST.json`;
- `knowledge/ARTIFACT_REGISTRY.csv` o le relative patch;
- `data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json`;
- i documenti in `docs/REFERENCE/`;
- lo script di generazione.

Il controllo `--check` fallisce se il pack persistito non corrisponde alle fonti correnti.

## Obiettivo di costo

Il bootstrap ordinario deve rimanere sotto 16 KiB serializzati nei casi di riferimento, evitando di riversare a ogni sessione centinaia di righe del registry completo.
