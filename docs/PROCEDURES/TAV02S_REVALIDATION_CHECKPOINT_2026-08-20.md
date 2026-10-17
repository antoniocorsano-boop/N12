# TAV-02S — checkpoint rivalidazione crop

Data: 2026-08-20
Stato: WORKING CHECKPOINT

## Evidenze persistenti

I 12 crop PNG della TAV-02S sono persistenti nel ramo `work/m0g-source-recovery` sotto `evidence/hires/TAV-02S/tiles/` e sono indicizzati da `hires_index.json`.

Il manifesto di provenienza che collega crop ed esiti è:

`data/canonical/TAV02S_EVIDENCE_PROVENANCE_MANIFEST_v1.csv`

## Esiti persistenti

Registri correnti:

- `data/canonical/TAV02S_SYMBOL_OBSERVATIONS_v1.csv`
- `data/canonical/CANONICAL_REVALIDATION_LEDGER_v1.csv`
- `data/canonical/TAV02S_CROP_REVIEW_REGISTER_v1.csv`
- `data/canonical/TAV02S_READING_RESIDUALS_v1.csv`
- `data/canonical/TAV02S_BEAMS_DOC_CURRENT_v1.csv`

## Gerarchia dell'evidenza

Priorità operativa:

1. misure scritte;
2. numeri/lettere/ID;
3. testi e sigle dimensionali;
4. simboli;
5. geometria grafica;
6. inferenza.

I dataset storici sono ipotesi da rivalidare e non possono prevalere sul crop.

## Claim direttamente letti finora

Quote/catene direttamente lette o rivalidate:

- 4.70
- 5.10
- 4.15
- 4.15
- 5.60
- 5.50
- 1.90
- 3.25
- 2.40
- 2.90

La precedente lettura 2.25 è revocata e riaperta in favore di 3.25.

Pilastri/ID con sezione direttamente letta:

- 1 = 40x50
- 2 = 50x40
- 3 = 60x40
- 4 = 40x50 — CROSS_VALIDATED
- 5 = 40x50 — CROSS_VALIDATED
- 6 = 50x40 — CROSS_VALIDATED
- 9 = 40x50
- 10 = 50x40
- 11 = 50x40
- 12 = 40x50 — CROSS_VALIDATED
- 13 = 50x40 — CROSS_VALIDATED
- 14 = 50x40 — CROSS_VALIDATED
- 18 = ID leggibile, sezione ancora ND
- 19 = 40x50
- 20 = 50x40

Richiami dimensionali di elementi, da NON trattare come campate:

- 70x25 — CROSS_VALIDATED come richiamo dimensionale
- 120x20 — CROSS_VALIDATED come richiamo dimensionale
- 65 — significato ancora aperto
- 50 isolato — significato locale variabile, non usare automaticamente

## Vincoli correnti

- Nessuna coordinata nuova deve essere generata dai claim soltanto `SUPPORTED`.
- Le coordinate storiche conflittuali restano aperte finché quote e riferimenti non sono raccordati sui crop.
- Nessuna linea viene promossa a `BEAM_DOC` finché non è chiusa la continuità grafica e il raccordo con gli estremi.
- `a-d` restano da rileggere direttamente dalle evidenze pertinenti.

## Prossimo lavoro

1. Legare le osservazioni `UNBOUND_*` ai tile HiRes effettivi.
2. Leggere sistematicamente i settori che contengono 15-17 e 21-33.
3. Cercare le lettere a-d come testo prioritario.
4. Rivalidare le catene di quota prima di rigenerare il reticolo.
5. Solo dopo passare alle connessioni/travi.
