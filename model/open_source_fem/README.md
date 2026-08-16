# N12 — Modello FEM open source

Target operativo: **OpenSeesPy**.

## Perché OpenSeesPy

OpenSees/OpenSeesPy è il percorso scelto per il modello FEM open source perché è specifico per simulazione strutturale e sismica, consente modellazione 3D a nodi/elementi, materiali non lineari e successive estensioni per telai in cemento armato esistente.

Code_Aster resta utilizzabile come secondo target generale FEM, ma per questo progetto il primo modello eseguibile viene prodotto in OpenSeesPy.

## Stato del modello

Versione corrente: `M0-OS-0001`.

Questo primo modello è una **geometria strutturale 3D preliminare**, non ancora un modello di verifica. Include:

- 27 fili verticali/pilastri da `data/canonical/nodes.csv`;
- quota interpiano estradosso-estradosso `3.20 m`;
- 5 livelli geometrici: `0.00, 3.20, 6.40, 9.60, 12.80 m`;
- elementi colonna tra livelli successivi;
- sezioni elastiche provvisorie marcate `PLACEHOLDER`;
- vincoli di base incastrati per prova geometrica.

Non include ancora come elementi verificabili:

- travi globali TAV.5/TAV.6 non ancora allineate ai nodi definitivi;
- sezioni puntuali pilastri 40x50/40x40/30x40 per catena e livello;
- materiali reali e livello di conoscenza;
- masse, carichi sismici, fondazioni modellate e verifiche normative.

## File

- `requirements.txt` — dipendenze Python.
- `opensees_m0_geometry.py` — costruzione del modello geometrico OpenSeesPy.
- `exports/README.md` — cartella prevista per output CSV/VTK generati localmente.

## Uso locale

```bash
cd N12
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r model/open_source_fem/requirements.txt
python model/open_source_fem/opensees_m0_geometry.py
```

Output atteso:

- `model/open_source_fem/exports/m0_nodes_3d.csv`
- `model/open_source_fem/exports/m0_column_elements.csv`

## Regola

Il modello OpenSeesPy deve seguire i dati canonici del repository. Un valore `ND`, `INC` o `PLACEHOLDER` può servire per generare geometria, ma non può essere usato per diagnosi, verifica o progetto degli interventi.
