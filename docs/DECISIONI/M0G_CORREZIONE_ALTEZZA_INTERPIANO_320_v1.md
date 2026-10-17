# M0-G — Correzione altezza interpiano estradosso-estradosso

Versione: `M0G-Z-320-0001` — 2026-08-16

## Dato corretto

L'altezza di piano **estradosso-estradosso** da utilizzare nel modello preliminare è:

```text
h_piano = 3,20 m = 3200 mm
```

## Stato di evidenza

`RIF_UTENTE_CORRETTO`.

Il dato corregge una precedente informazione fornita erroneamente. Non viene classificato come `DOC` finché non viene riscontrato sulle sezioni, prospetti o tavole originali.

## Effetto operativo

- sostituisce ogni precedente assunzione diversa sull'altezza interpiano;
- consente l'impostazione preliminare dei livelli M0-G/M0-EdiLus;
- non chiude le quote Z assolute dell'edificio;
- non modifica le geometrie planimetriche dei telai;
- deve essere evidenziato nel Registro Master come dato riferito corretto.

## Regola di modellazione

Per cinque impalcati con altezza costante, il modello preliminare potrà usare incrementi verticali successivi di 3,20 m, mantenendo però separati:

1. quota relativa di modello;
2. quota assoluta documentale;
3. eventuale quota architettonica o altimetrica esterna.
