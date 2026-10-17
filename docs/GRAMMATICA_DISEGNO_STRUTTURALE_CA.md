# Grammatica canonica del disegno strutturale in c.a.

## Scopo
Formalizzare le convenzioni grafiche necessarie per leggere carpenterie storiche in c.a. senza confondere simboli geometricamente simili ma semanticamente diversi.

## Principio fondamentale
Prima si determina il significato del simbolo nel linguaggio del disegno tecnico, poi si misura la geometria. La misura non puo' precedere la classificazione semantica.

## Regole canoniche
### G-01 Pilastro o setto numerato
Un rettangolo/quadrato con numero identificativo interno, posto in corrispondenza di un sostegno e coerente con l'abaco dei pilastri, e' un elemento verticale candidato. Il numero interno e' il discriminante principale. Le dimensioni della sezione del pilastro possono essere riportate all'esterno del simbolo e non devono essere confuse con quote di travi adiacenti. Deve essere validato con continuita' verticale e sezione documentata.

### G-02 Trave priva di numero e quote esterne
La trave non e' identificata da un numero interno come il pilastro. Le sue dimensioni possono essere riportate esternamente al tratto mediante quote o richiami grafici. La classificazione della sezione deve derivare dall'attribuzione delle quote al tratto di trave, non dalla sola forma di un piccolo rettangolo o di due linee locali.

### G-03 Fili fissi
Le linee sottili di riferimento che attraversano un pilastro/setto numerato definiscono i fili fissi documentati. L'intersezione dei fili viene rilevata numericamente in coordinate pagina/raster e mantenuta distinta dal baricentro geometrico della sezione, salvo coincidenza verificata.

### G-04 Sostegni larghi
Un sostegno 30x110 o altra sezione fortemente rettangolare non viene ridotto a un punto. Si registrano: filo fisso X/Y, orientamento, quattro facce, ingombro reale, eventuale eccentricita' fra filo fisso e baricentro, e faccia/punto di attestazione di ogni trave.

### G-05 Attacco trave-sostegno
La trave viene collegata alla faccia fisica documentata del sostegno. Se due travi arrivano su facce o quote planimetriche diverse dello stesso sostegno, tali attacchi restano distinti. L'eventuale condensazione FEM avviene solo successivamente tramite offset/rigid links espliciti.

### G-06 Regola negativa
Una forma non diventa pilastro, setto, trave o nodo per sola somiglianza geometrica. Servono contesto, simbologia, identificativo e coerenza con le altre tavole.

### G-07 Cornicione
Le forme trapezoidali rappresentate sul bordo esterno dell'impalcato, quando inserite nella continuita' del bordo/sbalzo e prive di identificativo di pilastro, sono rappresentazioni del cornicione. NON sono nodi, NON sono shell, NON sono setti, NON sono offset del pilastro e NON devono generare punti di connessione FEM del sostegno. La loro geometria appartiene al sistema di bordo/sbalzo dell'impalcato e va letta separatamente rispetto alla rete pilastri-travi.

### G-08 Trave a spessore — larghezza variabile documentata
Una trave a spessore e' definita dal fatto che la sua altezza e' pari allo spessore strutturale dell'impalcato/solaio; la denominazione NON implica una larghezza planimetrica fissa. La larghezza deve essere letta caso per caso dalle quote esterne associate alla specifica trave o da altra evidenza documentale. Nessun valore puo' essere esteso per analogia.

Le linee ravvicinate che richiamano lo spessore del solaio sono una convenzione grafica simbolica: NON vanno interpretate come i bordi planimetrici reali della trave e la loro distanza sul raster NON determina la larghezza `b` della trave.

Per il modello ETABS la geometria della trave a spessore viene ricostruita solo dopo avere attribuito correttamente la larghezza documentata `b_doc` al tratto. L'asse analitico viene poi definito coerentemente con il filo di riferimento/documentato del tratto e con la posizione reale rispetto ai sostegni; non deriva automaticamente dalla mezzeria di due linee simboliche del solaio.

Conseguenza operativa: qualunque attachment point o larghezza di trave ricavato misurando direttamente piccoli rettangoli, coppie di linee simboliche o distanze locali non esplicitamente quotate e' PRELIMINARE/SUPERATO e deve essere rivalidato.

### G-09 Gerarchia di attribuzione delle quote
Per ogni zona della carpenteria si applica obbligatoriamente questa sequenza:
1. individuare il pilastro tramite il numero interno;
2. attribuire al pilastro le eventuali quote esterne immediatamente riferite al suo rettangolo;
3. individuare il tratto di trave privo di numero che collega i sostegni;
4. attribuire al tratto le quote esterne che seguono il suo orientamento o il suo richiamo grafico;
5. distinguere le linee simboliche dello spessore del solaio dalle quote di base/larghezza della trave;
6. solo dopo formare la sezione `b x h` e promuoverla a DOC.

In caso di ambiguita' la quota resta non attribuita (`ND`) e non viene assegnata per vicinanza geometrica o per analogia con altri tratti.

### G-10 Travi emergenti alte 70 cm — base consolidata 25 cm
Per la TAV-05S e per il modello corrente N.12, quando un tratto e' semanticamente riconosciuto come TRAVE_EMERGENTE e la sua altezza documentata e' `h=70 cm`, la base canonica consolidata e' `b=25 cm`. La sezione viene quindi registrata come `25x70 cm`. Questa regola e' un dato consolidato di progetto (RIF) e non va estesa a travi con altezza diversa o a travi a spessore.

Conseguenza operativa: i precedenti record `NDx70` relativi a travi emergenti della TAV-05S sono SUPERATI e diventano `25x70` mantenendo la provenienza composita `DOC(h=70)+RIF(b=25)`.

### G-11 Sostegni larghi e falsa inclinazione delle travi
Il filo fisso di un sostegno largo 30x110 (P18, P23, P30 nella TAV-05S) NON obbliga l'asse della trave a passare per quel punto. Una trave ortogonale nel disegno non deve diventare inclinata nel modello solo per connettersi al joint del filo fisso.

Nel modello ETABS:
- il pilastro largo mantiene un solo joint analitico sul filo fisso;
- l'asse reale/documentato della trave viene preservato;
- la non concorrenza fra asse trave e joint del sostegno viene rappresentata con Frame Joint Offset, insertion geometry o equivalente offset rigido esplicito;
- due travi incidenti sullo stesso sostegno largo possono avere punti/facce di attestazione diversi;
- e' vietato ruotare artificialmente la trave verso il filo fisso del sostegno.

Questa regola prevale sui precedenti schemi planimetrici che mostravano travi apparentemente oblique presso P18/P23/P30.

### G-12 Continuita' della trave a spessore
La presenza di un richiamo grafico `20`, `50`, `70`, `120` non costituisce da sola la topologia della trave, ma neppure la interrompe. La connettivita' si verifica sulla linea strutturale continua e sui sostegni attraversati/attestati. Il simbolo di sezione puo' essere distaccato dal pilastro e restare comunque riferito al tratto continuo. Non si elimina una trave solo perche' il piccolo simbolo di sezione non tocca il rettangolo del pilastro.

### G-13 Simbolo di sezione trasversale all'asse reale della trave a spessore
Nelle carpenterie storiche il rettangolo quotato `b x h` di una trave a spessore puo' essere disegnato TRASVERSALMENTE alla direzione reale della trave. Il lato lungo del piccolo rettangolo e la quota `b` NON indicano quindi la direzione dell'asse della trave.

L'asse reale deve essere ricostruito seguendo la linea strutturale continua attraverso i sostegni e gli eventuali cambi di direzione. Caso canonico TAV-05S: la trave a spessore `120x20` che parte dalla zona del P09 prosegue lungo la catena fino a P16; i richiami `120/20` sono simboli di sezione trasversali al percorso e non segmenti orizzontali autonomi.

Conseguenza operativa: prima di creare un frame ETABS si determina il percorso della trave; solo dopo si associa la sezione letta dal simbolo trasversale.

### G-14 Termine trave su altra trave e nodi di intersezione non-pilastro
Una trave puo' terminare su un'altra trave senza raggiungere un pilastro numerato. In tal caso il punto di intersezione e' un nodo strutturale trave-trave e deve essere registrato esplicitamente, distinto dai pilastri.

Caso canonico TAV-05S: la trave `50x20` che parte da P05 verso est termina sulla trave a spessore principale che intercetta, in corrispondenza della catena P09-P16; NON va prolungata artificialmente fino a P12 o P04.

Nel modello analitico il nodo di intersezione puo' diventare un joint ETABS, con coordinate MIS e provenienza esplicita, senza essere promosso a pilastro.

### G-15 Continuita' verticale dei fili fissi e riseghe di sezione
Nel rebinding fra impalcati il filo fisso di ciascun pilastro e' il riferimento verticale primario e deve restare sulla stessa coordinata planimetrica X/Y fra i livelli, salvo evidenza documentale esplicita di cambio di filo.

Una variazione di sezione del pilastro NON implica spostamento del filo fisso. Le eventuali riseghe vengono rappresentate come variazioni dell'ingombro fisico rispetto al medesimo filo, registrando per ogni livello:
- sezione `b x h`;
- orientamento della sezione;
- distanza del filo fisso dalle quattro facce (`N`, `S`, `E`, `W`);
- tipo di risega: `NONE`, `MONOLATERALE`, `BILATERALE`, `ROTATION_OR_SECTION_CHANGE`, `ND`;
- eventuale variazione del baricentro fisico rispetto al filo fisso.

Conseguenza ETABS: la linea verticale del pilastro resta sul joint del filo fisso; la diversa posizione delle facce ai vari livelli viene gestita tramite insertion point/offset della sezione e tramite gli attachment delle travi. E' vietato inclinare il pilastro o spostare i joint superiori per inseguire il baricentro della sezione ridotta.

Una riduzione, ad esempio `40x50 -> 40x40`, deve quindi essere classificata prima come risega rispetto al filo fisso: puo' essere centrata, monolaterale o con faccia mantenuta. La scelta NON puo' essere dedotta dalla sola variazione numerica della sezione; va letta dalle carpenterie/particolari.

### G-16 Posizione del filo fisso per pilastri d'angolo e di facciata
La posizione del filo fisso dipende dal ruolo planimetrico del pilastro rispetto al perimetro dell'edificio e NON deve essere assimilata automaticamente al baricentro della sezione.

Per il modello N.12 si assume come regola di lettura, da verificare puntualmente sulle carpenterie:
- PILASTRO D'ANGOLO: il filo fisso coincide con lo SPIGOLO ESTERNO del pilastro, cioe' con l'intersezione dei due bordi esterni di facciata;
- PILASTRO DI FACCIATA: il filo fisso giace sul BORDO ESTERNO della sezione e, lungo quel bordo, passa per la MEZZERIA del lato;
- PILASTRO INTERNO: la posizione del filo fisso non viene dedotta per analogia e resta quella documentata dal reticolo/fili della tavola.

Conseguenze per le riseghe verticali:
- nei pilastri d'angolo, lo spigolo esterno resta invariato in X/Y e la sezione cresce o si riduce verso l'interno, salvo evidenza contraria;
- nei pilastri di facciata, il bordo esterno resta invariato e la risega si sviluppa prevalentemente verso l'interno; se cambia anche la larghezza lungo facciata, va verificato se la mezzeria sul bordo esterno resta fissa oppure se esiste una risega laterale documentata;
- il baricentro della sezione puo' quindi traslare fra i livelli pur restando invariato il filo fisso;
- in ETABS il joint verticale resta sul filo fisso e la sezione viene collocata tramite insertion point/offset coerente con il ruolo ANGOLARE/FACCIATA/INTERNO.

Questa regola prevale su qualunque precedente assunzione di risega centrata o filo baricentrico non documentato.

## Caso di test TAV-05S
- Pilastro 18: rettangolo numerato, sezione 30x110 documentata, fili fissi interni visibili -> ELEMENTO_VERTICALE.
- Pilastri ordinari: numero interno + quote esterne 30/45, 40/40, ecc. -> quote del pilastro solo se chiaramente riferite al rettangolo numerato.
- Trave senza numero con quote esterne -> attribuire le quote al tratto prima di dedurre la sezione.
- Due linee ravvicinate con richiamo `20` in una trave a spessore -> SIMBOLO_SPESSORE_SOLAI0, non bordi planimetrici della trave.
- Trave emergente documentata con `h=70` -> sezione canonica `25x70` per dato consolidato.
- Trave ortogonale incidente su P18/P23/P30 -> mantenere asse trave ortogonale e rappresentare l'eccentricita' mediante offset, non inclinando la trave verso il filo fisso.
- Il simbolo di una trave a spessore puo' essere graficamente separato dal pilastro e trasversale all'asse reale: la topologia deriva dalla continuita' strutturale del percorso.
- Catena P09-P16 -> seguire la trave 120x20 lungo il percorso continuo, introducendo un nodo di cambio/intersezione se necessario fra P12 e P13.
- Trave da P05 verso est -> termina sul nodo trave-trave della catena P09-P16; NON collegare direttamente P12-P04.
- Nel confronto G4->G3 il filo fisso del pilastro resta verticalmente invariato; una sezione diversa viene trattata come risega/variazione di footprint, non come traslazione del joint.
- Pilastro d'angolo -> conservare lo spigolo esterno come filo fisso; la risega si legge rispetto a quello spigolo.
- Pilastro di facciata -> conservare il punto medio del lato sul bordo esterno come filo fisso; la variazione di sezione non va recentrata sul baricentro.
- Forme trapezoidali di bordo nella zona del cornicione -> CORNICIONE, non nodi/elementi verticali/offset.

## Regola di apprendimento
Ogni errore di interpretazione corretto deve produrre una nuova regola canonica o un caso di test. Le regole vengono applicate a tutte le tavole successive prima di qualsiasi estrazione di coordinate.
