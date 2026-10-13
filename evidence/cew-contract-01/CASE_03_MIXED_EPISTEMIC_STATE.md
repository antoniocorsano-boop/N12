# CASE 03 — Mixed Epistemic State

**Case:** `GEO-005` — topologia storica 57 nodi / 38 connessioni / 10 componenti.  
**Status:** `PASS` per la rappresentazione epistemica; la provenienza sorgente completa resta bloccata separatamente.

## Fact vs inference

### Parte documentale — `DOC`

Il Registro Master registra i conteggi storici `57 nodi / 38 connessioni / 10 componenti`; l'inventario storico conferma l'esistenza dell'abaco topologico e di registri/associazioni geometriche nel pacchetto v25.

### Parte inferenziale — `INF`

La proposizione «questo insieme è un sottoinsieme topologico storico e non necessariamente l'universo geometrico completo» è una deduzione controllata, motivata dalla presenza nei registri storici di riferimenti a ID superiori a N057.

## CEW representation

La fixture conserva due proposizioni distinte:

1. `Claim-A`: conteggi storici = 57 / 38 / 10 — stato `DOC`;
2. `Claim-B`: tali conteggi non esauriscono necessariamente l'intera geometria — stato `INF`, con ragionamento inferenziale esplicito.

La proprietà complessiva non viene appiattita a `DOC` semplice. La stringa storica `DOC/INF-controllata` viene quindi interpretata come composizione di conoscenze con origine diversa, non come nuovo stato atomico.

## Source limitation

Le fonti storiche originali non sono presenti nel repository corrente: il locator originario resta `UNRESOLVED_LOCATOR` e la provenienza di `GEO-005` per questa evidenza storica resta `BLOCKED_SOURCE`.

Questo blocco è locale alla provenienza del caso storico `GEO-005`: non viene riassorbito né annullato dal `C01-T02` corrente. Dopo la closure del 13 ottobre 2026, `C01-T02` è qualificato su una distinta catena core end-to-end reale documentata in `CASE_13_CORE_END_TO_END_ASSURANCE.md`; tale qualifica non promuove né completa retroattivamente il locator mancante di `GEO-005`.

La limitazione di fonte non annulla la capacità del contratto di preservare la distinzione `DOC`/`INF` dimostrata da questo caso.

## Qualification conclusion

Il contratto rappresenta senza perdita uno stato epistemico misto e mantiene separata l'inferenza dalla parte documentale. Caso `PASS` limitatamente alla rappresentazione epistemica; la provenienza sorgente di `GEO-005` resta `BLOCKED_SOURCE` come sopra registrato.
