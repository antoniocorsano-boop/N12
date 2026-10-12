# CASE 02 — No Promotion of ND

**Case:** `SEC-002` — Telaio 1 G2, sezione non congelata.  
**Status:** `PASS`

## Evidence available

`docs/REGISTRO_MASTER.md` registra:

- `SEC-002` — Telaio 1 G2;
- sezione non congelata;
- evidenza dichiarata: stato M0 v18;
- stato epistemico: `ND`.

## CEW representation

Fixture logica:

- **StructuralObject:** elemento fisico di Telaio 1 / G2;
- **CanonicalProperty:** `section = unavailable`;
- **epistemic_state:** `ND`;
- **value:** assente;
- **unit:** non applicabile finché il valore non esiste;
- **default:** **no default**;
- **Decision:** mantenere l'assenza esplicita; nessuna promozione a `DOC`, `MIS` o `INF`.

## Invariant exercised

`ND` non significa zero e non autorizza un valore sostitutivo per convenienza di modellazione. Una futura Assumption può vivere in uno Scenario, ma non modifica questa proprietà canonica.

## Qualification conclusion

Il contratto rappresenta correttamente un dato mancante senza inventare il valore. Il caso specifico è `PASS`.
