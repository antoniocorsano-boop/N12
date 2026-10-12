# CASE 04 — Structural Identity

**Case:** Telaio 5, livello G5, voce `BEAM-006`.  
**Status:** `PASS` per l'invariante identità/alias.

## Real N12 anchors

- `BEAM-004` identifica il percorso storico del Telaio 5;
- `BEAM-006` identifica al livello G5 le campate C2–C7 con sviluppo 19.20 m;
- `data/canonical/telaio_5.csv` usa alias storici `T5`, `G5`, nodi `1-7`, campate `C2-C7`.

Questi riferimenti descrivono la stessa porzione fisica attraverso viste/alias differenti.

## CEW fixture

- **StructuralObject:** `OBJ-FIX-BEAM-T5-G5-C2-C7`;
- **alias:** `T5`, `G5`, `C2-C7`, `BEAM-006`;
- **tipo strutturale:** `Beam`;
- `T5` è un alias storico, non un tipo CEW;
- `G5` è un alias di livello, non un tipo CEW.

Gli alias restano metadati/provenienze e non diventano l'identità primaria CEW.

## Property revision rule

Per esercitare l'invariante senza inventare storia N12, si usa una revisione **puramente contrattuale** della fixture:

- property version A: riferimento a una proprietà della trave;
- property version B: stessa proprietà revisionata;
- `StructuralObject ID` resta `OBJ-FIX-BEAM-T5-G5-C2-C7`.

La revisione non afferma che una specifica proprietà N12 sia realmente cambiata; dimostra solo che, quando cambia una proprietà dello stesso elemento fisico, l'identità non cambia.

## Qualification conclusion

Il contratto separa correttamente identità fisica e alias/documenti/software. Caso `PASS` per `C01-T05`.
