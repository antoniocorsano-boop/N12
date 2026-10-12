# CEW-CONTRACT-01 — Evidence Package Rules

Questo percorso contiene **solo artefatti di qualifica** del contratto logico CEW-CONTRACT-01. Non costituisce né sostituisce il patrimonio canonico N12.

## Stati ammessi

- `NOT_RUN` — caso non ancora eseguito;
- `PASS` — criterio soddisfatto con evidenza sufficiente e verificabile;
- `FAIL` — criterio eseguito e non soddisfatto;
- `BLOCKED_SOURCE` — fonte/evidenza necessaria non reperibile o non localizzabile;
- `BLOCKED_INPUT` — manca un input tecnico reale necessario al caso, per esempio un SolverRun/Result N12;
- `REVIEW_REQUIRED` — esistono elementi sufficienti per la revisione ma non per una conclusione deterministica.

## Regola sulle fonti N12

Ogni caso deve citare una voce di `docs/REGISTRO_MASTER.md`, un dataset canonico già esistente oppure una fonte originale realmente reperita e localizzata. Una citazione di secondo livello al Registro Master non viene trasformata in Evidence localizzata se la fonte originale o il locator interno non sono verificabili.

## Divieti

1. Non inferire valori mancanti per far passare un test.
2. Non promuovere `ND`, `INC` o `INF` a `DOC` senza nuova evidenza.
3. Non inventare un Conflict, una Relationship o una revisione storica.
4. Non costruire SolverRun/Result sintetici e presentarli come risultato tecnico N12.
5. Non modificare `docs/REGISTRO_MASTER.md` o `data/canonical/` come effetto collaterale della qualifica.
6. Gli ID CEW usati nei casi sono **fixture di qualifica**, non nuovi identificatori canonici N12.

## Fail closed

Se un locator, una fonte o un input reale non è disponibile, il caso chiude con `BLOCKED_SOURCE` o `BLOCKED_INPUT`. L'assenza di evidenza non viene compensata con una supposizione.
