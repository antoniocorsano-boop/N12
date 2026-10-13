# CASE 11 — N12 registration uncertainty

**Gate:** C01-T07  
**Fonte congelata:** `work/m0-global-model@d806dcca72779b5a186defe557a7a9b739575a90:data/canonical/PT_METRIC_NETWORK_RESIDUALS_v1.csv`  
**Fixture:** `fixtures/N12_REGISTRATION_UNCERTAINTY_v1.json`

## Scopo

Dimostrare che CEW-CONTRACT-01 sa rappresentare una discrepanza/incertezza associata a una registrazione reale senza trasformare un residuo diagnostico in una tolleranza o in una dichiarazione metrologica non presente nella fonte.

## Osservazioni congelate

La fixture conserva due righe reali della fonte:

- supporto `1`: osservato `(4096.63, 2823.61) px`, previsto `(4100.03, 2822.89) px`, `du=3.40 px`, `dv=-0.72 px`, `residual_px=3.47`, stato `PASS_DIAGNOSTIC`, classe `DOC_METRIC_OR_AXIS`;
- supporto `19`: osservato `(2458.56, 4200.73) px`, previsto `(2462.23, 4224.46) px`, `du=3.67 px`, `dv=23.73 px`, `residual_px=24.01`, stato `WATCH`, classe `MIS_AFFINE_WATCH`.

Il campo `derived_bound` resta `null`: la fonte non fornisce una tolleranza `±x` e questa qualifica non ne inventa una.

## Interpretazione CEW

La classe logica è `REGISTRATION_UNCERTAINTY`. Il residuo quantifica la discrepanza osservata tra riferimento registrato e posizione prevista dalla trasformazione; non è, per questo solo fatto, errore standard, incertezza standard, accuratezza certificata o tolleranza normativa.

La classe di evidenza della coordinata di base resta quella della fonte. Il residuo non costituisce una nuova misura autonoma e non può essere promosso a `DOC` o `MIS` per effetto della sola elaborazione.

## Esito

Il caso soddisfa il criterio aggiornato di C01-T07 perché contiene valore/coordinate reali, provenienza, metodo, residuo vettoriale e scalare, stato diagnostico e guardia epistemica, mantenendo separata l'eventuale costruzione futura di un bound diagnostico derivato.
