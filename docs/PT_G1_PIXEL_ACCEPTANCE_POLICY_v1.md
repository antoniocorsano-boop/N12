# PT G1 Pixel Acceptance Policy v1

## Scopo
La fase G1 registra osservazioni pixel riproducibili dei sostegni sulla TAV-02S. Non certifica ancora la geometria metrica: questa viene verificata in G2-G4 mediante rete delle quote e analisi dei residui.

## Classi di accettazione

### Classe A — CROSS_VALIDATED
Usare quando lo stesso sostegno o la stessa sagoma è osservabile in due tile sovrapposti registrati indipendentemente. Registrare tile primario, tile di controllo e scarto pixel.

### Classe B — DIRECT_REGISTERED
Usare quando il sostegno non ricade in una sovrapposizione utile ma sono contemporaneamente soddisfatte tutte le condizioni seguenti:
- identificativo leggibile direttamente sul raster pulito;
- simbolo/contorno completo e non ambiguo;
- centro o sagoma ricavato direttamente dal simbolo, non da quote o dal Master storico;
- tile con `registration_status=DIRECT_SIFT_RANSAC` nel registro `TAV02S_TILE_TO_NATIVE_REGISTRATION_v1.csv`;
- registrazione tile→overview con residuo documentato;
- se disponibile, sezione/simbologia coerente con la lettura documentale;
- nessun conflitto semantico aperto sul supporto.

La Classe B può alimentare `PT_PIXEL_SUPPORT_REGISTRY_v1.csv` perché il registro pixel è un registro di osservazioni raster, non una geometria metrica definitiva.

### Classe C — WORKING_ONLY
Usare quando almeno una delle condizioni della Classe A/B manca: tile con registrazione derivata, simbolo parziale, identificativo ambiguo, contorno incompleto, conflitto semantico o coordinata ottenuta per inferenza.

## Supporti estesi
Per P18/P23/P30 il centro di riferimento non sostituisce la sagoma. La promozione pixel richiede il contorno/facce osservate; i nodi analitici restano vietati fino alla vettorializzazione delle travi e al beam-face binding.

## Terrazzo a-b-c-d
I sostegni aggiunti sono presenti nella carpenteria ma assenti dal modello di calcolo storico. Identità, sezione e coordinate raster sono quindi dati dello stato documentato/costruito; questa evidenza non deve essere reinterpretata come presenza nel calcolo originario.

## Gate successivo
G1 si chiude quando tutti i supporti richiesti hanno una registrazione pixel Classe A o B. Le quote 3.45, 4.70, ecc. non servono a fabbricare le coordinate pixel: entrano in G2 come vincoli metrici indipendenti e in G3-G4 per il controllo dei residui.
