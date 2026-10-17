# Pilastri piano terra — protocollo canonico v1

## Scopo
Costruire la pianta dei pilastri del piano terra solo dopo aver verificato, per ogni elemento, posizione planimetrica, coordinate del centro, sezione, orientamento, continuità verticale e provenienza documentale.

## Regola sulle coordinate
Le coordinate presenti in `nodes.csv`, `tav5_topology_nodes_57.csv` e `column_fixed_lines.csv` sono coordinate geometriche/topologiche o di filo fisso. Non devono essere chiamate automaticamente coordinate del baricentro della sezione.

Un pilastro riceve `center_x_mm` e `center_y_mm` solo quando sono verificati:
1. il punto/filo geometrico di riferimento;
2. la sezione del pilastro al piano terra;
3. l'orientamento della sezione;
4. l'eventuale offset del baricentro rispetto al filo fisso.

Fino ad allora il centro resta `ND` e si conserva separatamente `x_ref_mm/y_ref_mm`.

## Gerarchia delle evidenze
- `DOC`: letto direttamente dalla tavola originaria o da altro documento originale;
- `MIS`: misurato su fonte calibrata;
- `RIF`: riferito dall'utente o da altra fonte affidabile ma non ancora ritrovato nel documento;
- `INF`: dedotto da coerenza geometrica/topologica;
- `ND`: non determinato.

Nessuna inferenza sostituisce silenziosamente un dato documentale.

## Pilastri a, b, c, d
I pilastri `a`, `b`, `c`, `d` sono elementi aggiunti per il terrazzo. Sono presenti nelle carpenterie ma non considerati nei calcoli originari. Devono essere inclusi nello stato costruito e mantenuti esplicitamente come `TERRACE_ADDITION`, con `shown_in_carpentry=YES` e `in_original_calculation=NO`.

## Incongruenza da risolvere prima della pianta
Il patrimonio corrente contiene due livelli distinti:
- `tav5_topology_nodes_57.csv`: 57 nodi topologici, stato `PREDOC_TOPOLOGICO`;
- `nodes.csv` / `column_fixed_lines.csv`: 27 catene verticali di pilastri.

Inoltre alcune associazioni `node_id → coordinate/fixed_line` non coincidono tra i file correnti. Prima di promuovere qualunque coordinata a centro pilastro occorre riconciliare questi identificatori usando la tavola originaria come fonte sovraordinata.

## Registro operativo
Il file `data/canonical/pt_pillars_coordinate_status_v1.csv` è il registro corrente del piano terra. Ogni nuova lettura di tavola deve aggiornare quel registro o produrne una nuova versione, mantenendo storico e provenienza.

## Gate per generare la pianta PT
La pianta grafica viene autorizzata solo quando, per ogni pilastro PT:
- identificatore stabile: PASS;
- coordinate di riferimento: PASS;
- sezione PT: PASS;
- orientamento: PASS;
- offset/baricentro: PASS o esplicitamente zero documentato;
- centro definitivo: PASS;
- origine originario/aggetto terrazzo: PASS;
- raccordo con nodo/catena canonica: PASS.
