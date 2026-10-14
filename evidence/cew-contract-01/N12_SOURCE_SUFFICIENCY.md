# N12 — Source Sufficiency Audit for CEW-CONTRACT-01

**Purpose:** verificare quali sorgenti reali N12 sono disponibili alla qualifica del contratto senza inventare locator o promuovere derivati a fonte primaria.

## Correzione di perimetro dell'audit

La prima passata aveva ispezionato soltanto la branch documentale della PR. Il workflow N12 corrente richiama però esplicitamente `work/m0-global-model`; questa branch operativa è quindi parte dell'archivio tecnico accessibile e va inclusa nell'audit.

Branch operativa ispezionata: `work/m0-global-model` @ `d806dcca72779b5a186defe557a7a9b739575a90`.

Questa scoperta **supersede** le precedenti conclusioni `BLOCKED_SOURCE` quando il dato richiesto è effettivamente presente nella branch operativa.

## Fonti/evidenze ora verificate

### Source identity

`data/canonical/CEW_SOURCE_IDENTITY_REGISTRY_v1.csv` registra sorgenti primarie con:

- source/version ID;
- SHA-256;
- locator immutabile su commit di archivio;
- Git blob SHA;
- ruolo e authority.

Sono verificati almeno `TAV-05A` e `TAV-06A`, entrambi `PRIMARY` e `READY`.

### Evidence localizzata

`CEW_EVIDENCE_REGION_REGISTRY_v1.csv` localizza regioni BBOX sulla pagina primaria; `CEW_OBSERVATION_REGISTRY_v1.csv` collega osservazioni a Source version ed Evidence region e conserva esplicitamente contenuti leggibili e `UNREADABLE`.

### Relazioni/topologia

`tav5_topology_connections_v07.csv` contiene connessioni nodo-nodo con stato `INF_DA_QUOTARE`. `telaio5_tav5_candidate_matrix_v1.csv` conserva alternative concorrenti per gli stessi segmenti metrici e decisioni di non-promozione/rifiuto parziale.

### Conflict reale

`M1A_G5_COLUMN_REINFORCEMENT_SOURCE_CONFLICT_v1.csv` registra un conflitto documentale reale su supporto 24 fra TAV-07A e TAV-06S, con decisione corrente e reopen rule.

### Aggiornamento/versionamento

`CANONICAL_REVALIDATION_LEDGER_v1.csv` conserva `old_value`, Observation, esito, `new_value`, validation state e decision note. In particolare `CLM-Q01-LOCAL-225` conserva 2.25 → 3.25 con stato `REOPENED` e revoca esplicita del valore precedente. Inoltre `PT_MASTER_PRE_G1G9_SNAPSHOT_20260821.csv` è conservato separatamente da `PT_MASTER_CURRENT.csv`.

### Assurance reale

`N12_G4_HIRES_MACHINE_REVIEW_RECEIPT_v1.json` registra sorgente primaria, archive commit/blob, pagina, parametri di render, hash, run/artifact ID, findings, status e guardrail. È una ricevuta di revisione, **non** un'approvazione ingegneristica.

## Input tuttora non disponibile

Il progetto dichiara in `CEW_PROJECT_STATE_CURRENT_v1.json`:

- `R5 Solver Round Trip = PLANNED`;
- più calculation blockers aperti.

`M1E_CALCULATION_MODEL_HANDOFF_v1.json` dichiara `calculation_model_ready=false` e vieta l'esecuzione di una verifica numerica corrente con dati inventati.

Di conseguenza la qualifica di una catena reale `ModelGeneration → SolverRun → Result` resta `BLOCKED_INPUT`, non `BLOCKED_SOURCE`.

## Regola fail-closed

La presenza di dati più ricchi nella branch operativa non autorizza retroattivamente alcun PASS. Ogni stato viene aggiornato soltanto quando un caso concreto cita l'artefatto che soddisfa il criterio.
