# Test Scan2DXF su TAV.7 — Piano Quarto e Piano Copertura

## Fonte

- 12 tile raster persistenti 4×3 in `analysis/source_renders/TAV07/`.
- Dimensione complessiva dei tile: 5.18 MiB.
- Elaborazione geometrica eseguita alla risoluzione originale dei tile, con conversione CAD assunta a 300 DPI.
- Nessun candidato automatico viene promosso a dato validato.

## Risultati quantitativi

- Segmenti Hough candidati: **2685**.
- Famiglie: orizzontali **708**, verticali **1251**, diagonali **726**.
- Lunghezza mediana segmento: **183.0 px**.
- Candidati OCR con confidenza ≥ 40%: **245**.
- Confidenza OCR media: **65.1%**.
- Tile rappresentativo scelto automaticamente: **r1_c3.jpg** (441 segmenti; 39 testi).

## Valutazione del collaudo

- **Raster / provenienza:** PASS — i 12 tile vengono letti direttamente dalla fonte persistente.
- **Geometria candidata:** PASS TECNICO PARZIALE — la catena produce segmenti reali, ma Hough non distingue ancora travi/assi/quote/cartiglio/retini; serve classificazione e fusione delle collinearità prima della promozione CAD.
- **Testo:** REVIEW REQUIRED — Tesseract è soltanto una base per stampatello; il manoscritto tecnico deve restare candidato e richiede HTR dedicato + verifica umana.
- **SVG/DXF di revisione:** PASS — generati con livelli separati e senza promozione automatica dei testi.

## Prime letture OCR ad alta confidenza (non validate)

- `mi` — 96.0%
- `45` — 96.0%
- `45` — 96.0%
- `©` — 95.0%
- `|` — 95.0%
- `È` — 95.0%
- `IN` — 94.0%
- `\` — 93.0%
- `Zio` — 93.0%
- `\` — 93.0%
- `|` — 93.0%
- `=` — 93.0%
- `40` — 93.0%
- `\` — 93.0%
- `\` — 93.0%
- `\` — 92.0%
- `45` — 92.0%
- `\\` — 92.0%
- `\\` — 92.0%
- `>` — 92.0%
- `|` — 91.0%
- `D` — 91.0%
- `/` — 91.0%
- `N` — 90.0%
- `0` — 90.0%
- `a` — 90.0%
- `o` — 90.0%
- `\` — 90.0%
- `N` — 90.0%
- `È` — 90.0%

## Output

- `review_representative.svg`: raster alleggerito incorporato + linee candidate + testi candidati.
- `review_representative.dxf`: geometrie/testi candidati in livelli CAD separati.
- `geometry_representative.json`: segmenti con coordinate, lunghezza, angolo e famiglia.
- `text_candidates_representative.json`: letture OCR con bbox e confidenza.
- `metrics.json`: metriche di tutti i 12 tile.

## Gate successivo suggerito

Prima di usare il DXF come geometria strutturale occorre introdurre: (1) rimozione bordi/cartiglio/pieghe, (2) fusione segmenti collineari, (3) classificazione semantica linea/trave/quota/testo/retino, (4) HTR manoscritto mirato, (5) approvazione visuale per entità o regione.
