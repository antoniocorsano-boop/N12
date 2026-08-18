# Regola canonica — sostegni larghi e collegamento delle travi

## Campo di applicazione
Pilastro/setto con dimensione longitudinale tale da ricevere travi in punti distinti della stessa sezione, con caso pilota TAV-05S: pilastri 18, 23, 30 di sezione documentata 30x110 cm.

## Regola
Un sostegno largo non viene ridotto a un singolo nodo geometrico.

Si conservano contemporaneamente:
1. filo fisso documentato/misurato `F`;
2. ingombro reale della sezione;
3. orientamento dell'asse lungo;
4. due nodi di collegamento `A` e `B` alle estremita' dell'asse lungo, posti sulle mezzerie delle due facce corte;
5. quattro facce fisiche della sezione;
6. per ogni trave convergente, faccia di attestazione e nodo A/B/F appropriato.

## Politica di collegamento
- trave che termina presso una estremita' del sostegno largo -> nodo A oppure B coerente con l'estremita' documentata;
- trave che attraversa o si attesta nella zona centrale -> collegamento al riferimento F solo se la tavola lo documenta geometricamente;
- nessuna trave viene traslata al centro del sostegno per sola comodita' FEM;
- eventuali rigid links/eccentricita' vengono introdotti soltanto nella successiva idealizzazione FEM, conservando la geometria documentale originaria.

## Stati
- identita' e sezione: DOC quando leggibili sulle tavole/abachi;
- coordinate pixel: MIS;
- trasformazione metrica: da validare con quote documentali;
- collegamento trave-sostegno: DOC/MIS solo dopo lettura dell'attacco sulla carpenteria.

## Caso TAV-05S
P18, P23 e P30 sono 30x110 documentati. Il file `data/canonical/tav05_wide_support_nodes_v1.csv` contiene F, ingombri e nodi A/B misurati sul raster nativo.
