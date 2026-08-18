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

## Caso di test TAV-05S
- Pilastro 18: rettangolo numerato, sezione 30x110 documentata, fili fissi interni visibili -> ELEMENTO_VERTICALE.
- Pilastri ordinari: numero interno + quote esterne 30/45, 40/40, ecc. -> quote del pilastro solo se chiaramente riferite al rettangolo numerato.
- Trave senza numero con quote esterne -> attribuire le quote al tratto prima di dedurre la sezione.
- Due linee ravvicinate con richiamo `20` in una trave a spessore -> SIMBOLO_SPESSORE_SOLAI0, non bordi planimetrici della trave.
- Forme trapezoidali di bordo nella zona del cornicione -> CORNICIONE, non nodi/elementi verticali/offset.

## Regola di apprendimento
Ogni errore di interpretazione corretto deve produrre una nuova regola canonica o un caso di test. Le regole vengono applicate a tutte le tavole successive prima di qualsiasi estrazione di coordinate.
