# M0-G — Fili fissi dei pilastri — Decisione v1

## Evidenza fisica verificata

Sono stati aperti direttamente gli artefatti del pacchetto v25 presenti nel patrimonio di lavoro:

- `CATENE_VERTICALI_PILASTRI_v20.csv`: 27 catene geometriche con ID, coordinate X/Y e coppia di assi geometrici;
- `MATRICE_PILASTRI_27x5_v22.csv`: 135 righe = 27 catene × 5 ordini;
- `TAV19_CATENE_VERTICALI_PILASTRI.dxf`: 27 entità `S-PIL`, 27 entità `S-CHAIN`, griglia e testi;
- `TAV7_PILASTRI.dxf`: sorgente documentale per i tipi di pilastro;
- `TAV21_TIPO_PILASTRO_40x40_v22.dxf`: tipo documentale 40×40 separato dalla localizzazione delle singole catene.

## Decisione

La coppia `asse_X_geom` + `asse_Y_geom` e le coordinate X/Y di `CATENE_VERTICALI_PILASTRI_v20.csv` vengono assunte come **riferimento geometrico verticale verificato** delle 27 catene, non come baricentro documentale della sezione.

Questa distinzione è necessaria perché la matrice 27×5 mantiene la sezione puntuale `ND` e gli abachi TAV.7 documentano tipi di sezione senza dimostrare ancora l'associazione a ogni singolo pilastro.

## Conseguenza per EdiLus

Per ciascun pilastro saranno mantenuti separati:

1. riferimento geometrico verticale della catena;
2. punto di allineamento/filo fisso della sezione;
3. ingombro e orientamento della sezione;
4. asse analitico/baricentro risultante.

Non verrà applicato automaticamente l'allineamento al centro.

La documentazione ACCA relativa all'inserimento dei pilastri usa esplicitamente i concetti di allineamento/filo fisso, rotazione della sezione e traslazione/punto sensibile; pertanto il dataset di premodellazione deve conservare questi gradi di libertà.

## Stato

- 27/27 catene: riferimento geometrico verticale `VER_GEOMETRIC`;
- 135/135 posizioni catena-livello: continuità disponibile nella matrice 27×5;
- sezione puntuale: `ND` finché TAV.7 non consente l'associazione;
- rotazione: `ND` finché non derivata dalla sagoma documentale;
- offset asse: `ND` finché non sono noti sezione + orientamento + punto di allineamento.

## Gate successivo

Estrarre dal DXF TAV.7 le sagome documentali e verificare se esiste una corrispondenza univoca tra gruppi/tipi e le 27 catene. Solo i casi univoci possono essere promossi a `DOC`; gli altri restano `ND/INC`.
