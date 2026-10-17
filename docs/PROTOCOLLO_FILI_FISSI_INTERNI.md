# Protocollo canonico — fili fissi dei pilastri interni

## Scopo
Evitare due errori opposti nella lettura delle carpenterie storiche:
1. trattare ogni crocicchio locale come filo fisso senza verifica;
2. rifiutare un filo realmente documentato solo perché le scansioni di piani diversi non sono metricamente sovrapponibili con una trasformazione globale.

## Distinzione obbligatoria
Per un pilastro interno si distinguono sempre:

- **IDENTITÀ SEMANTICA DEL FILO**: il simbolo/crocicchio sottile appartiene al medesimo pilastro numerato e rappresenta il riferimento costruttivo verticale;
- **COORDINATA PIXEL LOCALE**: posizione del simbolo nella singola scansione; è MIS della tavola e non si trasferisce mediante una registrazione globale;
- **COORDINATA M0-G**: coordinata analitica unica del filo nel modello globale;
- **FOOTPRINT/OFFSET**: distanze del filo dalle quattro facce della sezione al singolo livello.

Le quattro grandezze non devono essere fuse in un unico dato.

## Criterio di qualificazione per pilastri interni
Il crocicchio sottile può essere qualificato come identità semantica del filo fisso quando sono presenti congiuntamente:

1. pilastro numerato e identificato documentalmente;
2. medesima identità verticale del pilastro fra impalcati;
3. simbolo di riferimento sottile coerente sul pilastro in almeno due carpenterie consecutive, preferibilmente tre;
4. nessuna evidenza documentale di cambio di filo;
5. variazioni di sezione trattate come variazioni del footprint rispetto al riferimento e non come spostamento automatico del joint.

La ricorrenza del simbolo fra tavole è evidenza semantica; NON autorizza il trasferimento delle coordinate pixel con una trasformazione affine globale.

## Registrazioni fra tavole
Le registrazioni geometriche TAV-05S↔TAV-04S, TAV-05S↔TAV-03S e analoghe servono per:
- verificare corrispondenza generale;
- trovare la zona omologa;
- supportare controlli locali.

NON devono essere usate per imporre la coordinata pixel di un filo in una tavola diversa quando la scansione mostra distorsioni locali. Il caso P20 dimostra il rischio: la trasformazione globale G4→G3 porta il riferimento grezzo a circa 39 px dalla linea locale P19–P20 già qualificata, oltre il p95 della registrazione.

## Regola M0-G
Quando l'identità semantica del filo interno è qualificata e non esiste evidenza di cambio di filo, si applica la continuità verticale canonica G-15:
- il joint analitico mantiene la stessa coordinata M0-G X/Y fra i livelli;
- la sezione fisica viene posizionata attorno al joint tramite offset/footprint misurati al singolo piano;
- il baricentro non sostituisce il filo;
- le travi si attestano alle facce fisiche, non necessariamente al joint.

## Stato dei casi P13/P20/P22/P26
Le carpenterie TAV-03S, TAV-04S e TAV-05S mostrano sui medesimi supporti numerati un simbolo/crocicchio sottile ricorrente. Questo consente di trattare la **identità semantica verticale del riferimento** come qualificata, senza usare la registrazione globale per trasferire coordinate pixel.

Restano separati:
- P20: U già qualificata metricamente da linea P19–P20; V e footprint richiedono misura locale della sezione;
- P22: U già qualificata metricamente da linea P22–P22'; V e footprint richiedono misura locale;
- P13 e P26: identità semantica del riferimento qualificata per ricorrenza documentale, mentre gli offset alle facce restano da misurare localmente.

## Evidenza
- TAV-03S / G2 — carpenteria II impalcato;
- TAV-04S / G3 — carpenteria III impalcato;
- TAV-05S / G4 — carpenteria IV impalcato;
- `data/canonical/g2_g3_g4_internal_fixedline_recurrence_v1.csv` come audit di supporto, non come trasformazione metrica;
- `data/canonical/g3_g4_internal_fixedline_gate_v3.csv` come gate metrico locale;
- `docs/GRAMMATICA_DISEGNO_STRUTTURALE_CA.md` G-03, G-15, G-16.
