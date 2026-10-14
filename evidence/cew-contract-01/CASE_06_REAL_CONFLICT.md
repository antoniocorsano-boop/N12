# CASE 06 — Real Conflict

**Case:** supporto 24 al livello G5, armatura/identità geometrica.  
**Status:** `PASS`.

## Real N12 conflict

`data/canonical/M1A_G5_COLUMN_REINFORCEMENT_SOURCE_CONFLICT_v1.csv` registra `M1A-G5C-001`:

- **Source fact A — TAV-07A:** V-order 40×40 include supporto 24 con 4×14 longitudinali, 4×16 monconi e staffe φ6/15;
- **Source fact B — TAV-06S:** la scansione completa della carpenteria di copertura documenta supporto 24 come `NOT_PRESENT_ON_ROOF_CARPENTRY`.

Il record è classificato `DOC_SOURCE_CONFLICT`.

## Decision without erasing either source

La decisione corrente è:

- escludere supporto 24 dal binding corrente dell'armatura G5;
- preservare la riga TAV-07A come conflitto documentale;
- non creare/estrudere un supporto G5-24;
- riaprire la geometria solo se una nuova fonte primaria indipendente contraddice il risultato TAV-06S.

## CEW mapping

- `Claim A` e `Claim B` restano entrambi registrati;
- `Conflict` è esplicito;
- `Decision` non cancella nessuna Source fact;
- `reopen_rule` rende la decisione revisionabile da nuova evidenza.

## Qualification conclusion

Il contratto rappresenta un conflitto documentale reale senza scelta prematura o cancellazione della fonte perdente. `C01-T03 = PASS`.
