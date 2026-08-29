# F3 — Modello globale M0-G

Stato: `IN CORSO`

## Scope

Costruzione della geometria globale tridimensionale dell'intero edificio esistente. Gate M0-G: coordinate,拓撲, livelli, quote, raccordi.

## Evidenze disponibili

| Fonte | Stato | Contenuto |
|-------|-------|-----------|
| model/M0-G/STATUS.md | IN CORSO | Stato M0-G corrente e criteri di chiusura |
| model/open_source_fem/README.md | DOC | M0-OS-0002: geometria FEM 3D preliminare |
| data/canonical/nodes.csv | VER_GEOMETRIC | 27 fili verticali geometrici |
| data/canonical/storey_height_status.csv | RIF | Altezza interpiano 3.20 m |
| data/canonical/telaio5_tav5_candidate_matrix_v1.csv | INF | Matrice candidati T5, HYP_A_METRICA |
| data/canonical/tav5_topology_nodes_57.csv | PREDOC | 57 nodi topologici |
| data/canonical/tav5_topology_connections_v07.csv | INF_DA_QUOTARE | 141 connessioni candidate |
| docs/DECISIONI/M0G_FILI_FISSI_v1.md | DOC | Riferimento geometrico 27 catene |
| docs/DECISIONI/M0G_CORREZIONE_ALTEZZA_INTERPIANO_320_v1.md | RIF | Altezza corretta a 3.20 m |
| docs/DECISIONI/M0G_RECUPERO_ABACO_57_NODI_v1.md | RECUPERATO | Abaco 57 nodi recuperato |
| docs/REGISTRO_MASTER.md (M0G-001..004) | IN_CORSO/ND | Stato avanzamento M0-G |

## Completato (R0 / fasi precedenti)

- 27 catene verticali con coordinate planimetriche.
- Altezza interpiano 3.20 m congelata (estradosso-estradosso).
- Primo modello FEM OpenSeesPy (M0-OS-0002): 135 nodi, 108 colonne, 38 travi T5.
- Ipotesi HYP_A_METRICA per T5 registrata e documentata.
- Criteri di chiusura M0-G definiti.
- Prossima azione estratta/normalizzare ABACO_TOPOLOGICO_TAV5_v11.csv.

## Mancante

- Normalizzazione completa coordinate nodali globali.
- Connettività strutturale per livello (57 nodi → rete globale).
- Raccordo几何 dei 27 pilastri alle 5 quote Z.
- Sagome/arretramenti di tutti gli impalcati.
- Quote Z definitive (ND/INC per livelli superiori).
- Raccordo geometrico delle fondazioni.
- Controllo indipendente firme metriche T1 e T5.
- Verifica T5 ↔ TAV.5/TAV.6/TAV.7 (overlay documentale).

## Residui

| ID | Tipo | Descrizione |
|----|------|-------------|
| R-1A-01 | BLOCCANTE | Raccordo 57 nodi topologici a coordinate canoniche |
| R-1A-02 | BLOCCANTE | Quote Z definitive per tutti i livelli |
| R-1A-03 | BLOCCANTE | Connettività globale per impalcato |
| R-1A-04 | BLOCCANTE | Sagome/arretramenti impalcati |
| R-1A-05 | BLOCCANTE | Raccordo geometrico fondazioni |
| R-1A-09 | RISCHIO | Allineamento T5 ↔ TAV.5 non verificato |

## Prossima azione

**R-1A-01**: Recuperare/verificare `ABACO_TOPOLOGICO_TAV5_v11.csv`, costruire `nodes.csv` + `vertical_columns.csv` e verificarlo contro TAV.5/TAV.7. Solo dopo: costruire rete globale e assegnare quote Z.

## Criteri di chiusura M0-G

M0-G sarà chiuso quando disponibili e validati:
- catalogo globale nodi planimetrici con coordinate;
- connettività strutturale per impalcato;
- continuità verticale pilastri;
- sagoma di ciascun livello e arretramenti;
- raccordo Telai 1 e 5 con carpenteria;
- quote Z documentate o approvate come ipotesi;
- fondazioni raccordate allo stesso sistema geometrico.
