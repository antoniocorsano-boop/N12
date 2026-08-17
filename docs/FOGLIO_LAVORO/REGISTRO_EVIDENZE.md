# Registro Evidenze N12

Versione: `RE-0001` — 2026-08-17

## Scope

Registro contrattuale delle evidenze strutturali. Ogni riga è un dato strutturale con fonte, stato, e referenza. Aggiornamento: prima di ogni avanzamento del modello.

## Stati ammessi

`DOC` / `DOC-*` · `MIS` · `RIF` · `INF` · `INC` · `ND` · `VER` · `VER-*` · `PLACEHOLDER` · `IN_CORSO` · `PREDOC` · `INF_DA_QUOTARE`

## Registro

### Geometria globale

| ID | Ambito | Dato | Stato | Fonte | Note |
|----|--------|------|-------|-------|------|
| EV-G01 | coordinate | 27 catene verticali: X/Y in mm | VER_GEOMETRIC | CATENE_VERTICALI_PILASTRI_v20.csv | Coordinate geometriche, non baricentro |
| EV-G02 | altezza | Interpiano estradosso-estradosso = 3.20 m | RIF | storey_height_status.csv | Corretta da utente 2026-08-16 |
| EV-G03 | topologia | 57 nodi topologici TAV.5 con X/Y | PREDOC_TOPOLOGICO | ABACO_TOPOLOGICO_TAV5_v11.csv | Sottoinsieme topologico storico, NON universo geometrico completo. Riferimenti a ID > N057 noti |
| EV-G04 | connettività | 141 connessioni candidate TAV.5 | INF_DA_QUOTARE | REGISTRO_CONNessioni_TAV5_v07.csv | Non verificabili come travi strutturali |
| EV-G05 | allineamento | T5 ↔ TAV.5: HYP_A_METRICA | INF | telaio5_tav5_candidate_matrix_v1.csv | Non verificato senza overlay |
| EV-G06 | fondazioni | 7 catene / 26 segmenti | DOC-ARTEFATTO | consolidato fondazioni | Ricostruzione parziale |

### Telai documentati

| ID | Ambito | Dato | Stato | Fonte | Note |
|----|--------|------|-------|-------|------|
| EV-T01 | T1 percorso | I-L-M-N-O-P-Q-R, 7 campate | DOC | relazione di calcolo / consolidato v12 | |
| EV-T02 | T1 campate | 4.70/5.10/3.25/2.40/2.90/5.30/4.70 m | DOC | relazione di calcolo / v12 | |
| EV-T03 | T1 G5 | C2-C6 | DOC | relazione di calcolo / v12 | |
| EV-T04 | T5 percorso | S-S'-T-U-V-Z-A'-B'-C', 8 campate | DOC | relazione di calcolo / v17 | |
| EV-T05 | T5 campate | 4.70/4.05/1.20/5.80/2.90/1.20/4.05/4.70 m | DOC | relazione di calcolo / v17 | |
| EV-T06 | T5 G5 | C2-C7 = 19.20 m | DOC | relazione di calcolo / v17 | |
| EV-T07 | T5 livelli | G1-G4: C1-C8 (28.60 m), G5: C2-C7 (19.20 m) | DOC | telaio_5.csv | Sezioni 25×70+140×20 per C3-C5 |

### Sezioni

| ID | Ambito | Dato | Stato | Fonte | Note |
|----|--------|------|-------|-------|------|
| EV-S01 | travi | 20×45, 25×70, 30×45, 30×65, 120×20, 140×20 cm | DOC | relazione / consolidati | Sezioni note |
| EV-S02 | T1 G2 | Sezione non congelata | ND | stato M0 v18 | |
| EV-S03 | T5 G5 | Sezione 20×45 | DOC | relazione_calcolo_v17 | |
| EV-S04 | T5 G1-G4 | Sezione 25×70 + 140×20 per C3-C5 | DOC | RC-P13_v16 | |
| EV-S05 | pilastri corpo | Famiglie 40×50 e 40×40 | DOC-famiglia | relazione di calcolo | Non assegnate a catene |
| EV-S06 | torrino | Pilastri 30×40 | DOC-famiglia | relazione di calcolo | Non assegnate a catene |

### Materiali e conoscenza

| ID | Ambito | Dato | Stato | Fonte | Note |
|----|--------|------|-------|-------|------|
| EV-M01 | materiali | Calcestruzzo / acciaio | ND | — | Da documentare/indagare |
| EV-M02 | conoscenza | LC / FC | ND | — | Da definire sul quadro conoscitivo |

### Carichi

| ID | Ambito | Dato | Stato | Fonte | Note |
|----|--------|------|-------|-------|------|
| EV-L01 | T5 carichi storici | Carichi lineari G1-G3 | DOC-STORICO | RC-P13 / v16 | Dati storici, non normativi |

### Pilastri

| ID | Ambito | Dato | Stato | Fonte | Note |
|----|--------|------|-------|-------|------|
| EV-P01 | abaco | 27×5 = 135 posizioni | DOC-ARTEFATTO | MATRICE_PILASTRI_27x5_v22.csv | Matrice storica: 27 catene × 5 ordini. Continuità verticale disponibile, assegnazione sezioni NON completa |
| EV-P02 | fili fissi | Coppia asse_X_geom + asse_Y_geom | VER | decisione M0G_FILI_FISSI_v1 | Riferimento geometrico verificato |
| EV-P03 | sezione puntuale | Per catena e livello | ND | — | Da TAV.7 dopo univocità |

### Modelli FEM

| ID | Ambito | Dato | Stato | Fonte | Note |
|----|--------|------|-------|-------|------|
| EV-F01 | M0-OS-0002 | 135 nodi, 108 colonne, 38 travi T5 | PLACEHOLDER | opensees_m0_geometry.py | Geometrico, non di verifica. I 135 nodi FEM = 27 catene × 5 livelli: NON coincidono con i 57 nodi topologici TAV.5 (EV-G03) |
| EV-F02 | sezioni FEM | Col 40×40, Beam T5: 20×45/25×70/140×20 | PLACEHOLDER_GEOMETRY_ONLY | fem_section_placeholders.csv | Materiali placeholder |
| EV-F03 | vincoli | Base incastrata | PLACEHOLDER | opensees_m0_geometry.py | Prova geometrica |

## Livelli epistemici — avvertenza

I valori numerici nel registro NON sono tutti allo stesso livello di affidabilità:

- **27 catene** (EV-G01, EV-P01): riferimento geometrico VER_GEOMETRIC / DOC-ARTEFATTO — dati verificati.
- **57 nodi** (EV-G03): sottoinsieme topologico PREDOC_TOPOLOGICO — storico, non verificato come universo completo.
- **141 connessioni** (EV-G04): candidati INF_DA_QUOTARE — non verificabili come travi strutturali.
- **135 FEM / 108 colonne / 38 travi** (EV-F01): PLACEHOLDER geometrico — generati da script per smoke-test, NON per verifica.
- **135 posizioni** (EV-P01): matrice storica DOC-ARTEFATTO — completa ma senza assegnazione sezioni.

Il raccordo globale dei 57 nodi alle coordinate canoniche rimane un **residuo aperto** (R-1A-01) e non deve apparire come topologia globalmente verificata.

## Regola di aggiornamento

Ogni nuova acquisizione aggiorna questo registro O il dataset canonico collegato PRIMA di essere usata come premessa per il modello. La versione del registro è incrementale (`RE-xxxx`).
