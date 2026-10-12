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

Le fonti storiche originali non sono presenti nel repository corrente: il locator originario resta `UNRESOLVED_LOCATOR`. Questa limitazione è già coperta da `C01-T02` e non annulla la capacità del contratto di preservare la distinzione `DOC`/`INF`.

## Qualification conclusion

Il contratto rappresenta senza perdita uno stato epistemico misto e mantiene separata l'inferenza dalla parte documentale. Caso `PASS`.
