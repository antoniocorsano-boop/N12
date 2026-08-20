# Archivio tavole originali ad alta risoluzione

Stato: **CANONICAL_SOURCE_ARCHIVE**

Questo ramo conserva in modo stabile i 18 PDF originali ad alta risoluzione del progetto N12.

## Regole

- I PDF in `archive/documentazione_originaria/` sono **fonti documentali primarie immutabili**.
- Non vanno sovrascritti, normalizzati, compressi o sostituiti con raster/DXF derivati.
- Ogni elaborazione deve citare l'ID tavola canonico, il percorso remoto e l'hash SHA-256 registrato nel manifesto.
- Raster, crop, OCR, DXF e annotazioni sono artefatti derivati e devono essere conservati altrove con provenienza esplicita.
- Per il piano terra: `TAV-02S = archive/documentazione_originaria/tavola2-2.pdf` (Carpenteria I impalcato).
- Per le fondazioni: `TAV-01S = archive/documentazione_originaria/tavola1-2.pdf`.

## Integrita'

I 18 PDF caricati nuovamente dall'utente il 2026-08-20 sono stati confrontati mediante SHA-256 con il manifesto esistente: **18/18 corrispondenze esatte**. Non esistono quindi versioni concorrenti.

L'indice operativo e' mantenuto sul ramo di lavoro in `data/canonical/tavole_originali_remote_index_v1.csv`.
