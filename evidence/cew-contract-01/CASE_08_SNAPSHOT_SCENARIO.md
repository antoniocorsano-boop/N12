# CASE 08 — CanonicalSnapshot and Scenario

**Status:** `PASS` per Snapshot/Scenario e indipendenza dallo strumento.

## CanonicalSnapshot fixture

La fixture `SNAP-FIX-N12-D806DCCA` congela il patrimonio operativo N12 all'exact commit:

`work/m0-global-model @ d806dcca72779b5a186defe557a7a9b739575a90`

Riferimenti inclusi:

- `data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json`;
- `data/canonical/M0G_GEOMETRY_HANDOFF_v1.json`;
- `data/canonical/M1E_CALCULATION_MODEL_HANDOFF_v1.json`;
- i relativi canonical ledgers richiamati dagli handoff.

Lo snapshot è una **fixture di qualifica**: non crea un nuovo stato canonico N12 e non sostituisce `CEW_PROJECT_STATE_CURRENT_v1.json`.

## Scenario without canonical mutation

`M1E_CALCULATION_MODEL_HANDOFF_v1.json` mantiene `M1E-B01` aperto perché la resistenza corrente in sito del calcestruzzo, LC e FC sono `ND`. Lo stesso handoff autorizza i valori storici solo come provenance/scenario metadata, non come current solver values.

Scenario fixture `SCN-FIX-HIST-CONCRETE`:

- base: `SNAP-FIX-N12-D806DCCA`;
- Assumption: usare la notazione storica `R'=300 kg/cm²` esclusivamente come scenario metadata/sensitivity placeholder;
- Source: `ORIGINAL_RELATION_PAGE2_EVIDENCE_v1.csv`, claim `ORP2-MAT-001`;
- canonical current concrete strength: **resta ND**;
- `M1E-B01`: **resta BLOCKING**;
- solver execution: **non autorizzata**.

L'override dello Scenario non scrive alcun valore nel patrimonio canonico.

## Two distinct projections from the same frozen state

Lo stesso patrimonio operativo produce già due handoff concettualmente diversi:

1. **Geometry projection:** `M0G_GEOMETRY_HANDOFF_v1.json` — geometria/topologia congelata per costruzione downstream;
2. **Calculation-model preparation:** `M1E_CALCULATION_MODEL_HANDOFF_v1.json` — trasferibilità verso EdiLus-EE o FEM indipendente, con blocchi espliciti sull'esecuzione.

Né l'identità CEW né lo Snapshot dipendono da CAD, IFC, EdiLus, OpenSees, database o formato di serializzazione.

## Qualification conclusion

- `Scenario` applica un'Assumption esplicita senza mutare il canonico: `PASS`.
- Lo stesso Snapshot supporta proiezioni diverse senza inglobare una tecnologia specialistica nel nucleo: `C01-T06 = PASS`.
