# CASE 01 — Documented Property

**Case:** `BEAM-006` / `T5,G5` — sviluppo 19.20 m, sezione 20×45 cm.  
**Status:** `BLOCKED_SOURCE`

## Why blocked

`docs/REGISTRO_MASTER.md` classifica `BEAM-006` come `DOC` e `data/canonical/telaio_5.csv` contiene il record canonico `T5,G5,1-7,C2-C7,19.20,20x45,DOC,relazione_calcolo_v17`. Tuttavia la **Source originale** dichiarata — relazione di calcolo / v17 — non è presente nel repository corrente e non è disponibile un locator interno verificabile.

Il dataset canonico secondario prova che il dato è già stato consolidato in N12; non viene però promosso artificiosamente a Evidence originale.

## Required CEW chain

`Source → Evidence → Observation → Claim → Decision → CanonicalProperty → StructuralObject`

Fixture prevista, non materializzata oltre il punto verificabile:

- **Source:** relazione di calcolo / v17 — `UNRESOLVED_LOCATOR`;
- **Evidence:** riga/pagina originaria — `UNRESOLVED_LOCATOR`;
- **Observation:** non ricostruita senza Evidence originale;
- **Claim:** non ricostruita come claim originaria;
- **Decision:** esiste un consolidamento N12 di secondo livello, ma la decisione originaria non è localizzata;
- **CanonicalProperty:** presente nel patrimonio N12 secondario (`BEAM-006` / CSV), ma non usata qui per simulare la catena mancante;
- **StructuralObject:** fixture CEW dell'elemento fisico associato a T5/G5, non nuovo ID canonico N12.

## Qualification conclusion

Il contratto sa distinguere il fatto che un dato canonico esista dal fatto che la sua catena sorgente completa sia disponibile. Il caso resta `BLOCKED_SOURCE`; nessun PASS di provenienza end-to-end viene assegnato.
