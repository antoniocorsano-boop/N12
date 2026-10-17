# PT G2 — Politica di completamento metrico MIS

## Scopo
Completare le coordinate dei sostegni che non dispongono di una quota documentale sufficiente senza usare il Master storico e senza trasformare la scala raster in evidenza DOC.

## Autorità
La rete metrica documentale già risolta resta prioritaria. La trasformazione affine raster è esclusivamente diagnostica/misurativa ed è congelata dalla soluzione G2 sui 30 sostegni con X/Y documentali.

## Regola
1. Si mantiene fissa ogni coordinata già determinata da quota o allineamento documentale.
2. Per la sola coordinata mancante si usa il centro pixel G1 registrato e la trasformazione affine diagnostica congelata.
3. Per gruppi sullo stesso asse si impone l'uguaglianza dell'asse osservato e si stima un unico valore metrico comune.
4. L'output è `MIS`, mai `DOC`.
5. Il residuo raster viene conservato. Non si sposta la rete documentale per minimizzarlo.
6. I sostegni estesi P18/P23/P30 mantengono centro fisico e facce separati; il valore MIS del centro non crea nodi analitici di trave.
7. Un valore MIS può alimentare la soluzione geometrica di lavoro e il successivo audit G3, ma non promuove la provenienza documentale.

## Trasformazione diagnostica congelata
- `u = 157.539621*x - 0.491217*y + 1264.31457`
- `v = 0.607656*x + 157.303931*y + 2811.95479`

Questa trasformazione deriva esclusivamente dai 30 sostegni già risolti documentariamente e non dal Master storico.

## Classificazione residui
- `SUPPORTED_MIS`: residuo compatibile con la dispersione già osservata della scansione.
- `SUPPORTED_MIS_WATCH`: valore utilizzabile in lavoro ma con residuo locale superiore alla dispersione ordinaria; richiede controllo nel successivo overlay.
