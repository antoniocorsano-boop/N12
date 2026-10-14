# CASE 07 — Non-Destructive Update

**Case:** rivalidazione reale di geometria/dimensioni N12.  
**Status:** `PASS`.

## Preserved old/new claim

`data/canonical/CANONICAL_REVALIDATION_LEDGER_v1.csv`, record `CLM-Q01-LOCAL-225`, conserva nello stesso ledger:

- `old_value = 2.25`;
- Observation `OBS-Q01-030`;
- `result = CONFLICT`;
- `new_value = 3.25`;
- `validation_state = REOPENED`;
- decision note: rilettura del crop inferiore; 3.25 è il valore scritto e 2.25 viene revocato.

La vecchia proposizione non è cancellata: resta visibile come `old_value` e come storia della Decision.

## Preserved snapshot

Il repository conserva inoltre separatamente:

- `PT_MASTER_PRE_G1G9_SNAPSHOT_20260821.csv`;
- `PT_MASTER_CURRENT.csv`;
- `PT_MASTER_PROMOTION_AUDIT_v1.csv`.

Il pre-snapshot mantiene lo stato precedente, mentre il master corrente incorpora gli sviluppi successivi. L'audit di promozione documenta la decisione di promuovere con residuali espliciti.

## CEW mapping

`old state → new Observation → Conflict/Decision → new state`, con stato precedente ancora consultabile e snapshot storico separato.

Non esiste ancora un SolverRun reale associato al vecchio snapshot; quel requisito è verificato separatamente da `C01-T09` e non viene simulato qui.

## Qualification conclusion

Sul piano del patrimonio canonico e dello snapshot, N12 dimostra un aggiornamento non distruttivo reale. `C01-T04 = PASS`.
