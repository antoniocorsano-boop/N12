# eTwin — Platform Specification Index

**Stato:** specifica di piattaforma in consolidamento  
**Branch:** `docs/etwin-system-spec-v1`  
**Baseline iniziale:** `dd5b48e64cb63eb5556d8bcc033b63cdc2bb302e`

## Documenti correnti

1. [`ETWIN_SYSTEM_SPECIFICATION_v1.md`](./ETWIN_SYSTEM_SPECIFICATION_v1.md)  
   Contratto di piattaforma: boundary, authority, project isolation, ruoli, discipline, fonti, agenti, stati, UX invariants, red-team e regole di evoluzione.

2. [`ETWIN_IMPLEMENTATION_PLAN_v1.md`](./ETWIN_IMPLEMENTATION_PLAN_v1.md)  
   Piano governato SP-0 → SP-8: genealogia, conformità, discovery, modello operativo, verticali A0/A1, agenti, HVA e baseline controllata.

## Authority

Questi documenti **non sostituiscono**:

- `docs/STATO_RIPRESA.md`;
- `docs/REGISTRO_MASTER.md`;
- `docs/PROTOCOLLO_CANONICO.md`;
- `docs/DECISIONI/*`;
- dataset/gate strutturali N12;
- contratti CEW/P0–P16 quando applicabili.

N12 resta una verticale/caso reale di prova. Gli artefatti storici `.asw/plans/etw*`, `model/etwin/*`, `docs/FOGLIO_LAVORO/ETW_*` e dashboard/read-model sono genealogia o sperimentazione finché una matrice di conformità non li classifica diversamente.

## Regola di evoluzione

Le specifiche distinguono:

- `INVARIANT` — boundary da non aggirare;
- `SPECIFIED` — scelta corrente evolvibile in modo compatibile;
- `OPEN` — decisione da non anticipare;
- `EXPERIMENTAL` — soluzione sostituibile;
- `DOMAIN_OWNED` — materia dell'authority disciplinare.

La piattaforma può quindi evolvere senza congelare prematuramente forma, interfaccia o implementazione, ma non può usare la flessibilità per indebolire authority, isolamento, provenienza o responsabilità.

## Prossimo gate

**SP-0 — Baseline & Genealogy**.

Prima di nuovo codice di piattaforma va creato il registro genealogico e va chiarita la posizione degli artefatti eTwin storici rispetto alla nuova specifica. Subito dopo SP-1 produrrà la matrice `KEEP / ADAPT / ISOLATE_AS_DOMAIN_TOOL / EXPERIMENT / DEPRECATE / BLOCKED_BY_OPEN_SPEC`.
