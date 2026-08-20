# Scheda standard di lettura crop TAV-02S v1

Questa scheda deve essere compilata per ciascuno dei 12 crop prima della promozione di qualsiasi asta.

## Identificazione
- `tile_id`:
- coordinate raster globali `u0,v0,u1,v1`:
- crop sovrapposti da controllare:
- data/revisione:

## A. Quote visibili
Per ogni quota trascrivere esattamente:
- testo letto;
- orientamento;
- estremi grafici della quota;
- riferimenti/nodi ai quali è sicuramente legata;
- stato: `DOC_DIRECT`, `UNCERTAIN`, `CONFLICT`.

Non convertire automaticamente una quota in distanza tra baricentri.

## B. Pilastri / appoggi
Per ogni impronta:
- numero/lettera visibile;
- forma dell'impronta;
- quote di sezione leggibili;
- orientamento;
- lato/i eventualmente coincidenti con filo quotato;
- coordinate raster del simbolo;
- eventuale raccordo al Master.

Distinguere `ID pilastro` da `centro pilastro` e `filo fisso`.

## C. Segni lineari strutturali
Per ogni segno candidato:
- singola linea / doppio bordo / fascia rettangolare / spezzata;
- appoggio iniziale;
- appoggio finale;
- continuità visibile nel crop;
- continuità da verificare nel crop sovrapposto;
- quote/sezioni associate;
- classificazione iniziale: `TRAVE`, `FILO`, `BORDO`, `INCERTO`;
- stato: `TO_VERIFY` finché non supera il gate.

## D. Solai
- delimitazione del campo;
- segno di orditura/direzione;
- eventuale interruzione/apertura;
- rapporto con le travi delimitanti;
- stato evidenza.

## E. Bordi, sbalzi, scala, aperture
Registrare separatamente. Nessun bordo di impalcato diventa trave automaticamente.

## F. Testi e richiami
Trascrivere sigle, numeri, sezioni e note leggibili che aiutano la semantica.

## G. Controllo incrociato
Per ogni elemento vicino al bordo del crop:
- identificare il crop sovrapposto;
- confermare che il segno prosegue/coincide;
- registrare `DOC_CROSS_TILE` soltanto dopo il riscontro.

## H. Output obbligatorio
La scheda produce:
1. righe da aggiungere a `TAV02S_SYMBOL_OBSERVATIONS_v1.csv`;
2. aggiornamento di `TAV02S_CROP_REVIEW_REGISTER_v1.csv`;
3. eventuali promozioni `BEAM_DOC` in un registro aste dedicato;
4. residui espliciti, mai risolti per analogia.

## Gate di chiusura crop
Un crop è `REVIEWED` solo quando:
- quote classificate;
- pilastri identificati o marcati ND;
- tutti i segni lineari classificati o marcati incerti;
- controlli di sovrapposizione eseguiti;
- residui registrati;
- aggiornamenti salvati nel repository.
