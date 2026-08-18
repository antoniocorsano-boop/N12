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

### G-08 Trave a spessore — larghezza variabile documentata
Una trave a spessore e' definita dal fatto che la sua altezza e' pari allo spessore strutturale dell'impalcato/solaio; la denominazione NON implica una larghezza planimetrica fissa. La larghezza deve essere letta caso per caso dalle quote, dalle sezioni trasversali o da altra evidenza documentale della specifica trave. Sulla TAV-05S sono possibili travi a spessore di larghezza 120 cm ma anche di larghezza diversa: nessun valore puo' essere esteso per analogia.

In pianta ogni trave a spessore deve essere trattata come una banda strutturale di larghezza `b_doc`: si individuano i due bordi longitudinali reali coerenti con la larghezza documentata e l'asse analitico ETABS e' la loro mezzeria, salvo filo di riferimento esplicitamente documentato. Una linea sottile locale presso un pilastro non puo' essere assunta come asse della trave prima di aver identificato la banda e la sua larghezza.

Il punto di attestazione sul pilastro deriva dall'intersezione dell'asse della banda con il contorno fisico del pilastro. Solo dopo si determina l'eventuale Frame Joint Offset rispetto al joint della colonna sul filo fisso.

Conseguenza operativa: qualunque attachment point di una trave a spessore ricavato assumendo automaticamente `b=120 cm`, oppure senza aver verificato la larghezza specifica della trave, e' PRELIMINARE/SUPERATO e deve essere rimisurato.

## Caso di test TAV-05S
- Pilastro 18: rettangolo numerato, sezione 30x110 documentata, fili fissi interni visibili -> ELEMENTO_VERTICALE.
- Rettangoli senza numero lungo le travi con quote 25x70, 20x120, 50x120, ecc. -> SEZIONE_TRAVE, non sostegni.
- Forme trapezoidali di bordo nella zona del cornicione -> CORNICIONE, non nodi/elementi verticali/offset.
- Trave a spessore con sezione documentata 120x20 -> banda strutturale `b=120 cm`; asse ETABS = mezzeria tra i due bordi longitudinali della specifica banda.
- Trave a spessore con larghezza diversa -> usare la larghezza documentata della singola trave; non promuovere 120 cm per analogia.

## Regola di apprendimento
Ogni errore di interpretazione corretto deve produrre una nuova regola canonica o un caso di test. Le regole vengono applicate a tutte le tavole successive prima di qualsiasi estrazione di coordinate.
