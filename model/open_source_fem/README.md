# N12 — Modello FEM open source

Target operativo: **OpenSeesPy**, con fallback geometrico puro senza dipendenze native.

## Perché OpenSeesPy

OpenSees/OpenSeesPy è il percorso scelto per il modello FEM open source perché è specifico per simulazione strutturale e sismica, consente modellazione 3D a nodi/elementi, materiali non lineari e successive estensioni per telai in cemento armato esistente.

Code_Aster resta utilizzabile come secondo target generale FEM, ma per questo progetto il primo modello eseguibile viene prodotto in OpenSeesPy.

## Stato del modello

Versione corrente: `M0-OS-0002` + `M0-G-EXPORT-FALLBACK`.

Questo modello è una **geometria strutturale 3D preliminare con primo telaio candidato**, non ancora un modello di verifica. Include:

- 27 fili verticali/pilastri da `data/canonical/nodes.csv`;
- quota interpiano estradosso-estradosso `3.20 m`;
- 5 livelli geometrici: `0.00, 3.20, 6.40, 9.60, 12.80 m`;
- elementi colonna tra livelli successivi;
- primo inserimento del **Telaio 5** secondo `HYP_A_METRICA` da `data/canonical/telaio5_tav5_candidate_matrix_v1.csv`;
- travi Telaio 5 ai livelli G1-G4 su C1-C8 e al livello G5 soltanto su C2-C7;
- sezioni geometriche documentali del Telaio 5: `20x45`, `25x70`, `140x20`;
- sezioni/materiali elastiche provvisorie per smoke-test;
- vincoli di base incastrati per prova geometrica.

Non include ancora come elementi verificabili:

- raccordo definitivo Telaio 5 ↔ TAV.5/TAV.6/TAV.7;
- travi globali di tutti gli altri telai;
- sezioni puntuali pilastri 40x50/40x40/30x40 per catena e livello;
- materiali reali e livello di conoscenza;
- masse, carichi sismici, fondazioni modellate e verifiche normative.

## File

- `requirements.txt` — dipendenze Python per OpenSeesPy.
- `opensees_m0_geometry.py` — costruzione del modello geometrico OpenSeesPy.
- `generate_m0_geometry_exports.py` — fallback senza OpenSeesPy: genera CSV 3D e riepilogo anche se le DLL native OpenSeesPy non sono disponibili.
- `exports/README.md` — cartella prevista per output CSV/VTK generati localmente.
- `data/canonical/fem_section_placeholders.csv` — sezioni geometriche provvisorie/documentali usate dagli script.

## Uso locale — OpenSeesPy

```bash
cd N12
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r model/open_source_fem/requirements.txt
python model/open_source_fem/opensees_m0_geometry.py
```

Console attesa:

```text
N12 M0-OS-0002
Storey height: 3.20 m
OpenSees nodes: 135
Column elements: 108
Telaio 5 beam elements: 38
Telaio 5 hypothesis: HYP_A_METRICA
Status: GEOMETRY_PLUS_T5_CANDIDATE / NOT_FOR_VERIFICATION
```

## Uso locale — fallback senza OpenSeesPy

Se su Windows OpenSeesPy non carica le DLL native, usare il fallback puro Python:

```bash
python model/open_source_fem/generate_m0_geometry_exports.py
```

Questo comando non richiede `pip install` e produce comunque:

- `model/open_source_fem/exports/m0_nodes_3d.csv`
- `model/open_source_fem/exports/m0_column_elements.csv`
- `model/open_source_fem/exports/m0_telaio5_beam_elements.csv`
- `model/open_source_fem/exports/m0_model_summary.txt`

Console attesa:

```text
N12 M0-G export fallback
Storey height: 3.20 m
3D nodes: 135
Column elements: 108
Telaio 5 candidate beam elements: 38
Telaio 5 hypothesis: HYP_A_METRICA
Status: GEOMETRY_EXPORT_ONLY / NOT_FOR_VERIFICATION
```

## Regola

Il modello deve seguire i dati canonici del repository. Un valore `ND`, `INC` o `PLACEHOLDER` può servire per generare geometria, ma non può essere usato per diagnosi, verifica o progetto degli interventi.
