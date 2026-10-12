# CASE 07 — Non-Destructive Update

**Target:** dimostrare su una revisione reale N12 che il nuovo stato non sovrascrive il precedente.  
**Status:** `BLOCKED_SOURCE`

## Available traces

Il Registro Master cita versioni/consolidamenti storici (`v12`, `v16`, `v17`, `v18`, ecc.) e il protocollo vieta di sovrascrivere una correzione senza conservare provenienza e stato precedente. Tuttavia nel repository corrente non sono disponibili, per una stessa proprietà, due versioni storiche complete e localizzabili che permettano di ricostruire una sequenza `old state → new evidence → Decision → new state`.

## Why blocked

Una dimostrazione reale richiede almeno:

1. proprietà precedente identificabile;
2. Evidence successiva;
3. Decision di revisione;
4. nuova CanonicalProperty;
5. conservazione della proprietà precedente per lo snapshot storico.

Le sole etichette di versione nel Registro Master non bastano a ricostruire questa catena senza inferenze.

## Qualification conclusion

Il requisito è coerente con il protocollo N12 ma non ancora qualificato su una sequenza storica completa. Esito `BLOCKED_SOURCE` per `C01-T04`.
