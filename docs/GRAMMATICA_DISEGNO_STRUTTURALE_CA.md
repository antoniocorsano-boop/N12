# Grammatica canonica del disegno strutturale in c.a.

## Scopo
Formalizzare le convenzioni grafiche necessarie per leggere carpenterie storiche in c.a. senza confondere simboli geometricamente simili ma semanticamente diversi.

## Principio fondamentale
Prima si determina il significato del simbolo nel linguaggio del disegno tecnico, poi si misura la geometria. La misura non puo' precedere la classificazione semantica.

## Regole canoniche
### G-01 Pilastro o setto numerato
Un rettangolo/quadrato con numero identificativo interno, posto in corrispondenza di un sostegno e coerente con l'abaco dei pilastri, e' un elemento verticale candidato. I pilastri sono riconoscibili primariamente dal NUMERO identificativo; le quote della sezione possono essere poste ESTERNAMENTE al simbolo e quindi non devono essere confuse con quote di travi o con quote planimetriche adiacenti. Deve essere validato con continuita' verticale e sezione documentata.

### G-02 Sezione trasversale di trave
Una trave e' identificata dal suo sviluppo nel reticolo strutturale e dalle quote di sezione poste esternamente o accanto alla rappresentazione simbolica. I piccoli rettangoli/linee che accompagnano la trave possono essere rappresentazioni SIMBOLICHE della sezione e non devono essere interpretati come un contorno planimetrico in scala. NON generano nodi, NON generano catene verticali e NON sono pilastri.

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

### G-08 Trave a spessore — rappresentazione simbolica e larghezza variabile
Una trave a spessore e' definita dal fatto che la sua altezza coincide con lo spessore strutturale dell'impalcato/solaio. La sua larghezza NON e' implicita e deve essere letta dalla quota specifica della trave.

Nelle carpenterie storiche la rappresentazione della trave a spessore puo' essere SIMBOLICA: le linee che indicano lo spessore del solaio o il piccolo rettangolo di sezione servono a comunicare la sezione strutturale, non necessariamente a disegnare in scala la larghezza planimetrica reale della trave. Pertanto NON si deve ricavare la larghezza reale misurando in pixel il piccolo simbolo di sezione.

Per la modellazione si usa la coppia di quote documentata della singola trave: `b_doc x h_doc`, con `h_doc` pari allo spessore strutturale del solaio per le travi a spessore. Solo dopo si ricostruisce la banda planimetrica coerente con `b_doc`, usando fili fissi, assi, attacchi ai pilastri e quote generali della carpenteria. L'asse analitico ETABS deriva dal filo/asse documentato; in assenza di un filo esplicito, la mezzeria della banda ricostruita e' un'inferenza da dichiarare, non un fatto grafico direttamente misurato.

Conseguenza operativa: i precedenti tentativi di dedurre `b` o l'asse della trave dalla distanza in pixel tra le linee del simbolo di sezione sono SUPERATI.

### G-09 Gerarchia di lettura pilastri/travi
1. Se il simbolo contiene un NUMERO identificativo -> candidato PILASTRO/SOSTEGNO.
2. Le quote esterne immediatamente associate al pilastro numerato possono descriverne la sezione.
3. Un elemento lineare senza numero che collega sostegni -> candidato TRAVE.
4. Le quote esterne associate alla trave descrivono la sezione della trave; per le travi a spessore il richiamo allo spessore del solaio e' convenzionale/simbolico.
5. Le quote non vengono associate per sola vicinanza geometrica: devono essere attribuite semanticamente all'oggetto corretto.

## Caso di test TAV-05S
- Pilastro 18: rettangolo numerato, sezione 30x110 documentata anche tramite quote esterne, fili fissi interni visibili -> ELEMENTO_VERTICALE.
- Pilastro numerato con quote esterne -> le quote possono appartenere al pilastro; non promuoverle automaticamente a sezione di una trave vicina.
- Trave senza numero con quote esterne -> le quote descrivono la sezione della trave se il contesto grafico conferma l'associazione.
- Linee/rettangolo simbolico di trave a spessore -> indicazione di sezione e spessore solaio; non contorno planimetrico da misurare in pixel.
- Forme trapezoidali di bordo nella zona del cornicione -> CORNICIONE, non nodi/elementi verticali/offset.

## Regola di apprendimento
Ogni errore di interpretazione corretto deve produrre una nuova regola canonica o un caso di test. Le regole vengono applicate a tutte le tavole successive prima di qualsiasi estrazione di coordinate.
