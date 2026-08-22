# M0G-REOPEN — PT B-053 (18–19) e B-054 (23–22′)

Data: 2026-08-22  
Ramo canonico: `work/m0-global-model`  
Ambito: correzione locale della topologia G1/PT già congelata

## Motivo della riapertura

Durante M1-A, la lettura diretta di TAV-02A ha evidenziato un gruppo di armatura con stazioni sovrapposte `23/18 – 22′/19 – 22/20 – 21`. Il dato non è stato usato da solo per modificare M0-G. È stato invece confrontato con la carpenteria primaria TAV-02S sui pixel registrati dei supporti.

La verifica diretta TAV-02S conferma due linee strutturali continue oggi assenti dal reticolo efficace PT:

1. supporto **18 → 19**;
2. supporto **23 → 22′**.

Le altre connessioni riconoscibili nel gruppo erano già presenti nel patrimonio corrente (`19–20`, `22′–22`, `22–21`) e la trave `20–21` è documentata separatamente come 30×65. Pertanto la riapertura riguarda **solo due nuovi membri**.

## Evidenza

Registro puntuale: `data/canonical/M0G_REOPEN_PT_BEAM_EVIDENCE_v1.csv`.

- B-053 18–19: TAV-02S tile `r2_c2`, linea continua diretta tra i due supporti raster registrati; TAV-02A conferma la sequenza 18–19–20.
- B-054 23–22′: TAV-02S tile `r3_c2`, linea continua diretta tra P23 esteso e 22′; TAV-02A conferma la sequenza 23–22′–22–21.
- Il dettaglio TAV-02A associato al gruppo mostra sezione **50×20 cm**; la sezione è trattata come informazione documentale della tavola armature, distinta dalla prova topologica TAV-02S.

## Provenienza metrica

La topologia è `DOC_TAV02S`. Le coordinate analitiche delle facce non sono promosse a DOC: sono derivate dalle sagome fisiche correnti e mantengono la provenienza metrica dei relativi supporti.

Nuove incidenze previste:

- B-053 @18: SOUTH ≈ (7.2384, 4.8500) m;
- B-053 @19: NORTH ≈ (7.6078, 8.7000) m;
- B-054 @23: NORTH ≈ (5.2406, 23.2500) m;
- B-054 @22′: SOUTH ≈ (5.5344, 19.4800) m.

Non è consentita alcuna sostituzione con il centro del pilastro.

## Delta inventariale autorizzato

Stato precedente → stato dopo la correzione:

- travi PT efficaci: **49 → 51**;
- nodi analitici di faccia PT: **98 → 102**;
- travi ordinarie globali: **229 → 231**;
- elementi strutturali ordinari globali: **356 → 358**;
- nodi analitici globali: **623 → 627**;
- link rigidi core→faccia: **458 → 462**;
- pilastri/segmenti verticali: invariati **127**;
- supporti fisici: invariati **38 G1**;
- topologia G2–G5: invariata;
- geometria speciale di copertura: invariata.

## Stato precedente preservato

Il precedente handoff M0-G resta identificabile dal blob `ebac5434f9c9761f6a666d7498c760962e0fe7f6` e il precedente assembly contract dal blob `0a86cb00516acf40fb1222e53d86ef7258cc6239`.

La presente decisione non invalida globalmente M0-G: applica il principio `reopen_smallest_conflicting_claim_only` a due sole connessioni documentate da fonte primaria.

## Gate di richiusura

La riapertura può essere richiusa soltanto dopo:

1. aggiornamento della patch PT e dei quattro nodi a faccia;
2. riallineamento del PT Master e dei QA G7/G9;
3. rigenerazione nodi 3D globali;
4. rigenerazione link rigidi;
5. rigenerazione connettività membri;
6. riesecuzione gate topologico globale;
7. aggiornamento dell'handoff M0-G e dei conteggi M1-S;
8. pass dei validator deterministici.

Esito attuale: **M0G-REOPEN APPROVED — REVALIDATION REQUIRED**.
