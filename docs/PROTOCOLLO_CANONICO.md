# Protocollo canonico N12

## 1. Scopo

Evitare dispersione, duplicazioni e ricostruzioni non verificabili durante la determinazione del modello strutturale dell'edificio esistente.

## 2. Fonti e stati

Ogni informazione entra nel Registro Master con:

- identificatore stabile;
- oggetto strutturale;
- valore;
- unità;
- fonte;
- posizione nella fonte;
- stato `DOC/MIS/RIF/INF/INC/ND`;
- versione di introduzione;
- eventuale versione di correzione;
- nota tecnica.

## 3. Gerarchia

1. fonte originale;
2. estrazione grezza;
3. riconciliazione;
4. dato canonico;
5. oggetto del modello;
6. verifica nel modello;
7. eventuale revisione del dato canonico.

## 4. Divieti

- non completare dati mancanti per simmetria o analogia senza registrarli come `INF`;
- non sovrascrivere una correzione senza conservare provenienza e stato precedente;
- non usare uno ZIP storico come stato canonico corrente;
- non confondere carichi storici della relazione con i carichi normativi da adottare nelle verifiche;
- non assegnare automaticamente materiali, LC o FC senza evidenza.

## 5. Modello

Il modello è articolato in gate:

- `M0-G` geometria globale;
- `M0-S` sezioni;
- `M0-A` armature;
- `M0-M` materiali, conoscenza e fattori;
- `M0-L` carichi e masse;
- `M0-V` validazione del modello;
- `M1` verifiche dello stato di fatto;
- `M2` interventi.

## 6. Stato corrente

Gate corrente: `M0-G`.

Vincolo operativo: costruire l'intero edificio tridimensionale. Telai e carpenterie sono evidenze/viste del medesimo organismo strutturale, non modelli indipendenti.
