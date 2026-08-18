# Regola canonica — sostegni larghi e collegamento delle travi (ETABS-aligned)

## Campo di applicazione
Pilastro/setto con dimensione longitudinale tale da ricevere travi in punti distinti della stessa sezione, con caso pilota TAV-05S: pilastri 18, 23, 30 di sezione documentata 30x110 cm.

## Principio generale
La geometria fisica resta governata dalle tavole originali. La geometria analitica viene costruita secondo la logica ETABS.

Un sostegno largo non viene ridotto a un singolo nodo geometrico e non riceve automaticamente due nodi alle sole estremita'. I nodi analitici sono generati dove richiesto dalla reale connettivita' delle travi e dalla discretizzazione dell'elemento verticale.

Si conservano sempre:
1. filo fisso documentato/misurato `F`;
2. ingombro reale della sezione;
3. orientamento dell'asse lungo;
4. quattro facce fisiche della sezione;
5. per ogni trave convergente, il proprio filo/asse documentale;
6. il punto di attestazione fisica della trave sul sostegno;
7. il nodo analitico ETABS corrispondente e l'eventuale offset/constraint necessario.

## Regola ETABS per i nodi
Per ogni trave convergente:
- si rileva il filo reale/documentato della trave sulla carpenteria;
- si prolunga tale filo fino all'intersezione con la geometria fisica del sostegno;
- il punto cosi' ottenuto e' il `beam_attachment_point`;
- se piu' travi condividono la stessa coordinata di attacco, possono condividere lo stesso nodo analitico;
- se le coordinate di attacco sono distinte, restano nodi analitici distinti;
- non si forza la trave al baricentro del sostegno per comodita' di modellazione.

I punti A/B alle estremita' del lato lungo non sono piu' nodi obbligatori. Possono esistere solo quando coincidono con reali punti di attacco, vertici necessari alla discretizzazione o nodi richiesti dalla mesh.

## Traduzione nel modello ETABS
### Se il sostegno e' modellato come frame/column
ETABS consente Frame Joint Offsets / Insertion Point quando la trave non entra nel centro del pilastro. Gli offset di joint sono trattati come completamente rigidi. Gli End Length Offsets restano concettualmente distinti e servono a rappresentare la dimensione finita/sovrapposizione dei membri lungo l'asse del frame.

### Se il sostegno e' modellato come shell/wall
Le travi che arrivano lungo un bordo dello shell devono essere connesse alla corretta posizione analitica. ETABS dispone di Auto Edge Constraints per collegare elementi che si attestano sul bordo di uno shell anche quando non coincidono con un vertice originario del pannello. La mesh dello shell deve essere compatibile con i punti di attacco rilevanti.

## Politica N12
- TAV-05S e le altre carpenterie definiscono geometria fisica, fili e attacchi;
- ETABS definisce la modalita' di idealizzazione analitica;
- nessun `rigid link`, joint offset o edge constraint viene introdotto prima di avere misurato il punto fisico di attacco;
- il modello analitico deve poter risalire sempre a `tavola -> sostegno -> trave -> filo -> attachment point`;
- eventuale semplificazione successiva deve essere esplicita, versionata e verificata.

## Stati
- identita' e sezione: DOC quando leggibili sulle tavole/abachi;
- filo fisso e attachment point in pixel: MIS;
- trasformazione metrica: da validare con quote documentali;
- connessione analitica ETABS: VER solo dopo controllo della connettivita' e degli offset;
- due nodi A/B predefiniti: SUPERATO come regola generale.

## Caso TAV-05S
P18, P23 e P30 sono 30x110 documentati. Il precedente file `data/canonical/tav05_wide_support_nodes_v1.csv` conserva A/B/F come storico geometrico; A/B non sono piu' nodi obbligatori del modello. I futuri dataset devono registrare i `beam_attachment_point` effettivi derivati dai fili delle travi.