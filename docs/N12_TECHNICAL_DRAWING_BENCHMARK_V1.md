# N12 Technical Drawing Benchmark v1

## Scopo

Valutare estrattori open source per PDF tecnici e tavole strutturali N12 senza alterare la catena canonica del progetto.

La gerarchia resta:

`SourceVersion -> Page/EvidenceRegion -> raw extractor output -> CandidateObservation/CandidateGeometry -> human validation -> canonical data`

Nessun estrattore può produrre direttamente identità strutturali, nodi canonici, sezioni accettate o modifiche M0-G/M0-S/M0-A.

## Baseline e candidati

- `pymupdf`: baseline primaria per accesso PDF, coordinate, testo, primitive vettoriali e rendering.
- `pdf-vector-normalizer`: candidato per ricostruzione CAD delle primitive (linee, archi, cerchi, testo ruotato, livelli/OCG, scala). Implementazione da selezionare/integrare dopo verifica licenza e API; il benchmark non assume FreeCAD come ambiente utente.
- `edocr2`: candidato specializzato per quote, sigle, simboli e annotazioni di disegni tecnici.
- `paddleocr-vl`: secondo osservatore per testo/quote/sigle su regioni dense o degradate.
- `raster-vectorizer`: percorso di riserva solo per SourceVersion prive di vettori utili.

## Casi benchmark v1

### B01 — TAV-05S / sezioni supporti G4

Obiettivo: riconoscimento combinato di simbolo geometrico, identificatore e dimensioni scritte.

Verità già validata: esempi comprendono `40x40`, `45x30`, `30x45`, `30x110`, `110x30`; il registro di audit disponibile documenta 34 identità con decisione PASS.

Misure: precisione testo, associazione testo-oggetto, orientamento, bounding box, falsi accoppiamenti tra supporti vicini.

### B02 — TAV.1A / armature e quote fondazioni

Obiettivo: lettura di catene, quote, diametri, lunghezze barre e staffe in una tavola densa.

Verità già validata: catena `12-5-4 = 3.70 + 2.00 m`; sezione A `45/90/120`, H `90+20=110 cm`, staffe `Ø10/15`; altra catena con `4.70+4.05+6.25+4.65 m` e barre `2Ø14 L=970`, `3Ø14 L=1040`, `2Ø18 L=1180`, `3Ø18 L=1260`.

Misure: CER/WER tecnico, correttezza di Ø e moltiplicatori, separazione quota/armatura, coordinate dell'osservazione, omissioni e allucinazioni.

### B03 — Telaio 5 / firma geometrica

Obiettivo: verificare estrazione e normalizzazione della sequenza geometrica senza creare identità strutturale automaticamente.

Verità già consolidata: asse `4.70-4.05-1.20-5.80-2.90-1.20-4.05-4.70 m`, sviluppo 28.60 m; livelli G1-G4 completi C1-C8 e G5 tronco C2-C7.

Misure: numero segmenti, lunghezze relative, continuità, ordine, errore metrico dopo calibrazione, preservazione delle interruzioni.

### B04 — TAV-05S / distinzione geometria-semantica

Obiettivo: verificare che un estrattore geometrico non trasformi rettangoli e sezioni grafiche in pilastri per sola forma/prossimità.

Criterio: l'output ammesso è `CandidateGeometry`; qualsiasi promozione autonoma a `column`, `beam`, `node` o identità canonica è fallimento di governance.

## Metriche minime

Ogni esecuzione deve produrre almeno:

- identificatore caso ed estrattore;
- versione esatta del software/modello;
- SourceVersion/hash e locator della regione;
- tempo di esecuzione e memoria, quando misurabili;
- output grezzo immutato;
- output normalizzato separato;
- conteggio true positive / false positive / false negative;
- errore di posizione in coordinate pagina;
- errore geometrico dopo eventuale calibrazione;
- decisione `PASS`, `WATCH`, `FAIL`.

## Gate di adozione

Un candidato è adottabile solo se:

1. migliora la baseline su almeno un asse N12 rilevante senza peggioramenti critici sugli altri;
2. conserva coordinate e provenienza ricostruibili dalla SourceVersion;
3. non richiede crop manuali non provenienziati come fonte di verità;
4. produce output serializzabile e ripetibile;
5. non crea automaticamente identità strutturali;
6. può essere eseguito localmente o in ambiente controllato compatibile con il progetto;
7. supera revisione umana sui casi B01-B04.

## Ordine di esecuzione

1. PyMuPDF baseline su B01-B04.
2. Normalizzatore vettoriale contro PyMuPDF su B03-B04.
3. eDOCr2 contro baseline OCR su B01-B02.
4. PaddleOCR-VL contro eDOCr2 su B01-B02.
5. Raster vectorizer solo su un caso aggiuntivo se viene identificata una SourceVersion realmente raster.

Il benchmark non autorizza modifiche a `data/canonical/`.