# Grammatica canonica del disegno strutturale in c.a.

## Scopo
Formalizzare le convenzioni grafiche necessarie per leggere carpenterie storiche in c.a. senza confondere simboli geometricamente simili ma semanticamente diversi.

## Principio fondamentale
Prima si determina il significato del simbolo nel linguaggio del disegno tecnico, poi si misura la geometria. La misura non puo' precedere la classificazione semantica.

## Regole canoniche
### G-01 Pilastro o setto numerato
Un rettangolo/quadrato con numero identificativo interno, posto in corrispondenza di un sostegno e coerente con l'abaco dei pilastri, e' un elemento verticale candidato. Deve essere validato con continuita' verticale e sezione documentata.

### G-02 Sezione trasversale di trave
Un rettangolo privo di numero identificativo interno, rappresentato lungo una trave e accompagnato o meno da quote di base/altezza, e' una rappresentazione convenzionale della sezione trasversale della trave. NON genera un nodo, NON genera una catena verticale e NON e' un pilastro.

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

### G-08 Trave a spessore 120x20
Le travi a spessore all'altezza del solaio hanno larghezza reale 120 cm e altezza 20 cm. In pianta devono essere lette come una banda strutturale larga 1.20 m: si individuano i due bordi longitudinali reali e l'asse analitico ETABS e' la loro mezzeria. Una linea sottile locale presso un pilastro non puo' essere assunta come asse della trave senza aver prima riconosciuto entrambi i bordi della banda. Il punto di attestazione sul pilastro deriva dall'intersezione dell'asse della banda 120 cm con il contorno fisico del pilastro; solo dopo si calcola l'eventuale Frame Joint Offset rispetto al joint sul filo fisso del pilastro.

Conseguenza operativa: gli attachment points ricavati senza aver verificato l'intera larghezza della trave a spessore sono da considerare PRELIMINARI/SUPERATI e devono essere rimisurati.

## Caso di test TAV-05S
- Pilastro 18: rettangolo numerato, sezione 30x110 documentata, fili fissi interni visibili -> ELEMENTO_VERTICALE.
- Rettangoli senza numero lungo le travi con quote 25x70, 20x120, 50x120, ecc. -> SEZIONE_TRAVE, non sostegni.
- Forme trapezoidali di bordo nella zona del cornicione -> CORNICIONE, non nodi/elementi verticali/offset.
- Trave a spessore 120x20 -> BANDA_STRUTTURALE_120; asse ETABS = mezzeria tra i due bordi longitudinali della banda, non una singola linea locale.

## Regola di apprendimento
Ogni errore di interpretazione corretto deve produrre una nuova regola canonica o un caso di test. Le regole vengono applicate a tutte le tavole successive prima di qualsiasi estrazione di coordinate.
