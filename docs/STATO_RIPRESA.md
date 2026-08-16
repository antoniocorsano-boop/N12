# Stato di ripresa N12

Data: 2026-08-16

## Fonte di verità

Repository GitHub `antoniocorsano-boop/N12`.

## Gate corrente

`M0-G` — determinazione della geometria globale tridimensionale dell'intero edificio esistente in c.a.

## Acquisito

- protocollo canonico e Registro Master attivi;
- relazione di calcolo parzialmente trascritta e riconciliata;
- Telaio 1 discretizzato: I-L-M-N-O-P-Q-R, 7 campate, G5=C2-C6;
- Telaio 5 discretizzato: S-S'-T-U-V-Z-A'-B'-C', 8 campate, G5=C2-C7;
- famiglie di sezioni di travi documentate;
- famiglie di pilastri corpo principale 40×50 / 40×40 e torrino 30×40 documentate a livello di famiglia;
- fondazioni: 7 catene / 26 segmenti e armature parzialmente consolidate;
- artefatti storici TAV.5/TAV.6/TAV.7 e abachi v11-v25 individuati come sorgenti prioritarie;
- abaco verticale pilastri 27×5 individuato.

## Da chiudere nel gate M0-G

- normalizzazione completa coordinate nodali;
- connettività globale per livello;
- raccordo dei 27 pilastri alle coordinate planimetriche e ai cinque livelli;
- sagome/arretramenti di tutti gli impalcati;
- quote Z definitive;
- raccordo geometrico delle fondazioni;
- controllo indipendente mediante firme metriche dei Telai 1 e 5.

## Gate successivi

`M0-S` sezioni → `M0-A` armature → `M0-M` materiali/LC/FC → `M0-L` carichi/masse → `M0-V` validazione → modello EdiLus-EE.

## Regola di continuità

Ogni avanzamento viene prima registrato nel repository remoto con provenienza e stato di evidenza. Gli ZIP storici sono fonti immutabili; il repository contiene lo stato canonico corrente.
