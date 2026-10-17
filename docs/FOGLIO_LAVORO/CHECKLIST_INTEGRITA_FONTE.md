# Checklist Integrità Fonte N12

Versione: `CI-0001` — 2026-08-17 (R1-B)

## Scope

Verifica sistematica di conformità di ogni file canonico (`data/canonical/`) rispetto alle convenzioni del progetto. Classificazione a tre livelli:

- **C** = Conforme alla convenzione (utf-8-sig BOM, delimiter `,`, colonne `source` + `evidence_status` presenti)
- **L** = Leggibile / tollerato (no BOM, ma leggibile; sniffer gestisce delimiter; colonne presenti con nomi alternativi)
- **NC** = Non conforme ma non bloccante (manca una colonna richiesta, o BOM mancante, o delimiter non standard)

**Nota**: l'assenza del BOM non è automaticamente OK se `AGENTS.md` prescrive `utf-8-sig`. Il lettore Python tollera l'assenza, ma la conformità formale è un concetto diverso.

## Convenzioni richieste (da AGENTS.md)

1. Encoding: `utf-8-sig` (BOM presente)
2. Delimiter: `,` o `;` — il codice usa `csv.Sniffer` con `delimiters=",;"`
3. Colonne richieste: una colonna di provenienza (`source` / `provenienza`) + una colonna di stato di evidenza (`evidence_status` / `stato`)

## Checklist

### CSV con entrambe le colonne richieste

| File | BOM | Delim | Record | Colonne | Source col | Evidence col | Classe | Note |
|------|-----|-------|--------|---------|------------|--------------|--------|------|
| nodes.csv | ✗ | `,` | 27 | 8 | `source` ✓ | `evidence_status` ✓ | **L** | No BOM; entrambe le colonne presenti |
| storey_height_status.csv | ✗ | `,` | 1 | 7 | `source` ✓ | `evidence_status` ✓ | **L** | No BOM; entrambe le colonne presenti |
| telaio_5.csv | ✗ | `,` | 5 | 8 | `provenienza` ✓ | `stato` ✓ | **L** | No BOM; nomi colonne alternativi |

### CSV con solo colonna di stato (mancante source/provenienza)

| File | BOM | Delim | Record | Colonne | Source col | Evidence col | Classe | Note |
|------|-----|-------|--------|---------|------------|--------------|--------|------|
| fem_section_placeholders.csv | ✗ | `,` | 5 | 11 | ✗ (`evidence` ≈ riferimento, non source) | `status` ✓ | **NC** | Mancante colonna provenienza esplicita |
| m0g_topology_status.csv | ✗ | `,` | 4 | 6 | ✗ (`evidence` = nome file, non source) | `status` ✓ | **NC** | Mancante colonna provenienza esplicita |
| pillar_section_assignment_status.csv | ✗ | `,` | 4 | 10 | ✗ (`evidence` = riferimento) | `status` ✓ | **NC** | Mancante colonna provenienza esplicita |
| telaio5_tav5_candidate_matrix_v1.csv | ✗ | `,` | 13 | 12 | ✗ | `evidence_status` ✓ | **NC** | Mancante colonna provenienza esplicita |
| tavole_originali_manifest.csv | ✗ | `,` | 18 | 5 | ✗ | `stato` ✓ | **NC** | Mancante colonna provenienza esplicita |

### CSV con delimiter `;` (sniffer required)

| File | BOM | Delim | Record | Colonne | Source col | Evidence col | Classe | Note |
|------|-----|-------|--------|---------|------------|--------------|--------|------|
| tav5_topology_nodes_57.csv | ✗ | `;` | 57 | 7 | ✗ | `stato` ✓ | **NC** | Delimiter `;` tollerato da sniffer; manca source |
| tav5_topology_connections_v07.csv | ✗ | `;` | 141 | 6 | ✗ | `stato` ✓ | **NC** | Delimiter `;` tollerato da sniffer; manca source |

### CSV senza colonne di evidenza/provenienza

| File | BOM | Delim | Record | Colonne | Source col | Evidence col | Classe | Note |
|------|-----|-------|--------|---------|------------|--------------|--------|------|
| column_fixed_lines.csv | ✗ | `,` | 27 | 14 | ✗ (`source_ref` ≈ riferimento) | ✗ (`fixed_line_status` / `continuity_status` ≈ status) | **NC** | Status e source presenti come metadati, non come colonne canoniche |
| telaio5_raccordo_57_nodi_status.csv | ✗ | `,` | 5 | 6 | ✗ | `stato` ✓ | **NC** | Mancante colonna provenienza esplicita |

## Riepilogo

| Classe | Count | File |
|--------|-------|------|
| **C** (conforme) | 0 | — |
| **L** (leggibile/tollerato) | 3 | nodes.csv, storey_height_status.csv, telaio_5.csv |
| **NC** (non conforme, non bloccante) | 9 | Tutti gli altri |

## Osservazioni

1. **Nessun file ha BOM** nonostante la convenzione `utf-8-sig`. Il codice Python usa `utf-8-sig` in apertura, che tollera l'assenza di BOM. La lettura funziona, ma la conformità formale è NC.
2. **3 file usano `;`** come delimiter. Lo `csv.Sniffer` del codice Python li gestisce correttamente.
3. **Solo 3 file su 12** hanno entrambe le colonne canoniche (`source`/`provenienza` + `evidence_status`/`stato`). Gli altri usano nomi alternativi o colonne strutturali.
4. **Nessuna non-conformità è bloccante**: il codice esistente tollera le variazioni. Tuttavia, per coerenza futura, si raccomanda di aggiungere colonne `source` e `evidence_status` standard ai file mancanti.

## Azioni raccomandate (non bloccanti)

- Aggiungere BOM utf-8-sig a tutti i CSV canonici (opzionale, il codice lo tollera).
- Aggiungere colonna `source` ai CSV che ne mancano (per coerenza di tracciabilità).
- Standardizzare i nomi delle colonne di stato (`evidence_status` vs `stato` vs `status`).
