# Regola canonica — sostegni larghi e collegamento delle travi secondo ETABS

## Campo di applicazione
Elementi verticali larghi che ricevono travi in punti distinti della stessa sezione. Caso pilota TAV-05S: elementi 18, 23, 30 di sezione documentata 30x110 cm.

## Autorita' documentale
Nelle tavole/abachi originari gli elementi 18, 23 e 30 sono identificati come pilastri. La sezione 30x110 non autorizza da sola a riclassificarli come Wall/Shell.

Pertanto:
- geometria fisica e denominazione derivano dalle tavole originali;
- l'idealizzazione analitica ETABS viene scelta successivamente;
- default candidato: Frame Column con sezione 30x110 e corretta posizione/insertion point;
- alternativa Wall/Shell solo se funzione strutturale, continuita' verticale e documentazione la giustificano.

## Regola geometrica
Un sostegno largo non viene ridotto prematuramente a un singolo punto di attacco.

Si conservano:
1. filo fisso documentato/misurato `F`;
2. ingombro reale della sezione;
3. orientamento dell'asse lungo;
4. quattro facce fisiche;
5. per ogni trave convergente, il proprio filo analitico/documentato;
6. il punto di attacco `Patt` come intersezione tra filo della trave e contorno fisico del sostegno.

I vecchi punti A/B alle estremita' dell'asse lungo restano solo riferimenti geometrici storici e NON sono nodi analitici obbligatori.

## Politica ETABS
### Caso Frame Column
- il frame della trave mantiene il proprio filo reale/documentato;
- quando il filo della trave non coincide con il nodo/asse analitico della colonna, usare Frame Insertion Point / Frame Joint Offsets coerenti con la geometria;
- ETABS tratta i Frame Joint Offsets come completamente rigidi;
- non traslare il filo della trave al centro della colonna solo per semplificare il modello.

### Caso Wall/Shell, se successivamente giustificato
- il punto della trave deve corrispondere alla reale intersezione con il bordo del pannello;
- possono essere usati nodi sul bordo/mesh e, dove appropriato, Auto Edge Constraints;
- evitare Auto Edge Constraints lungo bordi co-lineari con frame quando servono risultati locali affidabili del frame, come avverte la documentazione CSI.

## Distinzione da End Length Offsets
I Frame Joint Offsets/Inserting Point definiscono l'eccentricita' geometrica dell'asse analitico rispetto al nodo/cardinal point. Gli End Length Offsets descrivono invece la zona di sovrapposizione/rigid-end lungo l'asse del frame. Non vanno confusi.

## Stati
- identita' e sezione: DOC quando leggibili su tavole/abachi;
- fili e contorni pixel: MIS;
- punto di attacco trave-sostegno: MIS/DOC dopo lettura del filo della trave;
- rappresentazione analitica Frame/Shell: VER solo dopo controllo della funzione strutturale e continuita';
- trasformazione metrica: da validare con quote documentali.

## Caso TAV-05S
P18, P23 e P30 sono 30x110 documentati. I file di geometria conservano F e contorno. I punti di attacco ETABS vengono invece generati dai fili delle travi nel file `data/canonical/tav05_etabs_attachment_points_v1.csv`.
