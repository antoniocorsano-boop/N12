# PT G2 Reference Entity Policy v1

## Scopo

Nella TAV-02S una quota scritta non deve essere interpretata automaticamente come distanza centro-centro tra sostegni. Le linee di estensione possono terminare su assi, facce, bordi di trave o altri riferimenti strutturali.

## Regola

Prima di associare una quota a due `support_id`, identificare i due riferimenti fisici effettivi della linea di quota.

Sono ammessi almeno i seguenti tipi di riferimento:

- `SUPPORT_AXIS`;
- `SUPPORT_FACE`;
- `BEAM_AXIS`;
- `BEAM_FACE`;
- `GRID_OR_CONSTRUCTION_AXIS`;
- `UNBOUND_STRUCTURAL_REFERENCE`.

Una quota con testo leggibile e linee di estensione leggibili resta `DOC` anche quando uno o entrambi gli estremi non sono ancora associati a un sostegno. In questo caso deve essere conservata nella rete dei riferimenti e non eliminata né assegnata per prossimità.

## Artefatti

- `data/canonical/PT_G2_METRIC_REFERENCE_LINES_v1.csv`: registro dei riferimenti fisici osservati;
- `data/canonical/PT_G2_REFERENCE_CONSTRAINT_NETWORK_v1.csv`: quote tra riferimenti;
- `data/canonical/PT_GCP_METRIC_NETWORK_v1.csv`: vincoli già associabili in modo documentato a sostegni o altri oggetti canonici.

## Supporti estesi

Per P18, P23 e P30 il centro fisico può essere definito dall'intersezione degli assi rappresentati, ma ciò non autorizza a interpretare automaticamente una quota vicina come riferita al centro. Ogni quota deve essere tracciata fino alla propria linea di estensione.

## Divieti

- non associare una quota a un pilastro per sola vicinanza del testo;
- non usare la scala raster come sostituto della quota;
- non assumere che una linea di quota termini sul baricentro di un sostegno esteso;
- non confondere richiami di sezione trave (`120`, `25/70`, `65/30`, ecc.) con quote di maglia;
- non trasformare `UNBOUND_STRUCTURAL_REFERENCE` in un supporto senza evidenza grafica diretta.

## Gate

Una quota può diventare hard constraint per i centri dei sostegni solo quando entrambi gli estremi sono associati a riferimenti fisici compatibili con la variabile metrica che si vuole risolvere. In caso contrario resta valida come quota documentale nella rete dei riferimenti, ma non entra nel solve dei centri.
