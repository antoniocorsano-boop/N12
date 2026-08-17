# Residui N12

Versione: `RS-0001` — 2026-08-17 (R1-B)

## Scope

Registro di tutti i residui aperti con stato, responsabilità, dipendenze e collegamento alle evidenze.

## Stati residui

| Stato | Significato |
|-------|-------------|
| APERTO | Residuo identificato, non avviato |
| IN CORSO | Lavoro in corso |
| BLOCCATO | Bloccato da dipendenza non soddisfatta |
| CHIUSO | Residuo risolto |

## Residui strutturali (M0-G)

| ID | Tipo | Front | Descrizione | Stato | Evidenze collegate | Dipendenze |
|----|------|-------|-------------|-------|-------------------|------------|
| R-1A-01 | BLOCCANTE | F3 | Raccordo 57 nodi topologici a coordinate canoniche | BLOCCATO | EV-G03, EV-G04 | ABACO_TOPOLOGICO_TAV5_v11.csv verificato |
| R-1A-02 | BLOCCANTE | F3 | Quote Z definitive per tutti i livelli | APERTO | — | Sezioni/prospetti/tavole originali |
| R-1A-03 | BLOCCANTE | F3 | Connettività globale per impalcato | BLOCCATO | EV-G04 | R-1A-01 |
| R-1A-04 | BLOCCANTE | F3 | Sagome/arretramenti impalcati | APERTO | — | Tavole architettoniche |
| R-1A-05 | BLOCCANTE | F3 | Raccordo geometrico fondazioni | BLOCCATO | EV-G06 | R-1A-01, R-1A-03 |
| R-1A-06 | BLOCCANTE | F4 | Sezioni puntuali pilastri 40×50/40×40/30×40 per catena e livello | BLOCCATO | EV-S05, EV-S06, EV-P03 | TAV.7 estratto e verificato |
| R-1A-07 | BLOCCANTE | F5 | Materiali calcestruzzo/acciaio | APERTO | EV-M01 | Indagini o documentazione |
| R-1A-08 | BLOCCANTE | F5 | Livello di conoscenza LC/FC | APERTO | EV-M02 | Quadro conoscitivo |
| R-1A-09 | RISCHIO | F3 | Allineamento T5 ↔ TAV.5 non verificato | APERTO | EV-G05 | Overlay documentale TAV.5 |
| R-1A-10 | RISCHIO | F2 | Topologia 57 nodi: riferimenti a ID > N057 | APERTO | EV-G03 | Verifica completezza abaco |

## Residui R1-A (workspace)

| ID | Tipo | Front | Descrizione | Stato | Note |
|----|------|-------|-------------|-------|------|
| R-1A-11 | OPERATIVO | — | PR Draft creata | CHIUSO | PR #9 aperta |
| R-1A-12 | OPERATIVO | — | File FOGLIO_LAVORO committati | CHIUSO | 16 file tracciati |

## Residui R1-B (evidence integration)

| ID | Tipo | Front | Descrizione | Stato | Note |
|----|------|-------|-------------|-------|------|
| R-1B-01 | CONFORMITA | F1 | BOM mancante in tutti i CSV canonici | APERTO | Non bloccante; codice tollera |
| R-1B-02 | CONFORMITA | F1 | 9/12 CSV mancano colonna `source`/`provenienza` | APERTO | Non bloccante; tracciabilità parziale |
| R-1B-03 | CONFORMITA | F1 | Nomi colonne stato non standardizzati (`stato`/`status`/`evidence_status`) | APERTO | Non bloccante; sniffer tollera |
| R-1B-04 | CONFORMITA | F1 | 2 CSV usano delimiter `;` | APERTO | Non bloccante; sniffer gestisce |

## Mappa dipendenze

```
R-1A-01 (57 nodi) ← R-1A-03 (connettività) ← R-1A-05 (fondazioni)
                 ← R-1A-09 (allineamento T5)
R-1A-06 (sezioni pilastri) ← TAV.7 estratto
R-1A-07 (materiali) ← indagini
R-1A-08 (LC/FC) ← quadro conoscitivo
```

## Prossime azioni per residui bloccanti

| Residuo | Azione | Bloccato da |
|---------|--------|-------------|
| R-1A-01 | Recuperare/verificare ABACO_TOPOLOGICO_TAV5_v11.csv | Nessuno (avviabile) |
| R-1A-02 | Definire quote Z da sezioni/prospetti/tavole | Nessuno (avviabile) |
| R-1A-06 | Estrarre TAV.7 e verificare univocità pilastro ↔ catena | Nessuno (avviabile) |
| R-1A-07 | Raccogliere dati materiali | Nessuno (avviabile) |
| R-1A-08 | Definire LC/FC | R-1A-07 (materiali prima) |
