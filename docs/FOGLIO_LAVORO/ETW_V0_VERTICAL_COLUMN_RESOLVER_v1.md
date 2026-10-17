# ETW-V0 — VerticalColumnResolver v1

## Scopo
Risoluzione delle sezioni dei pilastri dell'edificio esistente per ordine/livello senza propagazione automatica della sezione e senza dipendere dalla lettura immagini da parte del modello operativo.

## Principio documentale
Le fonti hanno competenze distinte:
- **Abaco pilastri TAV-07A**: famiglia/tipologia sezionale locale, appartenenza del pilastro al gruppo dell'ordine, armature quando leggibili.
- **Carpenteria del livello**: identità/posizione, filo fisso, orientamento globale e presenza dell'elemento.
- **Crosswalk eTwin**: identità Pxx ↔ Nxxx e continuità verticale.

Nessuna fonte deve essere usata per inferire automaticamente proprietà che appartengono alla competenza di un'altra fonte.

## Regole canoniche

### RULE-COL-LEVEL-01 — Risoluzione per ordine
Ogni istanza `ColumnChain × Order` deve essere risolta nuovamente nell'abaco dell'ordine pertinente. La sezione del livello inferiore NON viene propagata come prova della sezione al livello superiore.

### RULE-COL-ORIENT-01 — Orientamento persistente
L'orientamento globale della catena verticale è persistente salvo evidenza documentale esplicita contraria. Le riseghe dimensionali sono ammesse; una risega non costituisce rotazione.

### RULE-COL-LOCAL-GLOBAL-01 — Sezione locale e sezione globale
La coppia dimensionale dell'abaco è una proprietà della famiglia sezionale locale. La carpenteria determina l'orientamento globale. Pertanto una famiglia locale `110×30` può risultare globalmente `110×30` oppure `30×110` secondo l'orientamento della catena, senza costituire una famiglia differente.

### RULE-COL-FIXEDLINE-01 — Filo fisso
Il filo fisso/posizione XY è proprietà geometrica persistente della catena e partecipa alla risoluzione dell'identità. Una variazione di sezione deve essere interpretata rispetto al filo fisso e non come ricentraggio automatico.

### RULE-COL-ALLOWED-01 — Vocabolario del livello
Ogni pilastro presente a un ordine deve appartenere a una famiglia sezionale documentata per quell'ordine nell'abaco. Una combinazione non documentata produce `SECTION_LEVEL_CONFLICT`, non una correzione automatica.

### RULE-COL-EPISTEMIC-01 — Provenienza
Ogni valore deve conservare almeno: `sourceDocument`, `sourceRegion/evidence`, `order`, `resolverRule`, `epistemicStatus`, `humanValidation`. Una proprietà derivata da una regola non viene promossa automaticamente a `DOC`.

## Stati di transizione verticale
Ammessi/diagnostici:
- `SAME_SECTION`
- `REDUCTION_AXIS_1`
- `REDUCTION_AXIS_2`
- `REDUCTION_BOTH`
- `BECOMES_SQUARE`
- `TERMINATES`

Conflitti/residui:
- `UNEXPECTED_ROTATION`
- `SECTION_NOT_ALLOWED_AT_LEVEL`
- `IDENTITY_MISMATCH`
- `DOCUMENT_CONFLICT`
- `UNRESOLVED`

## Contratto del resolver
Input minimo per catena:
- `columnId` / `Pxx`
- `canonicalId` / `Nxxx` se disponibile
- ordine/livello
- gruppo abaco e dimensioni locali quando strutturati
- posizione/fili fissi da carpenteria
- orientamento globale
- evidenze e stato epistemico

Output per istanza:
- `localSection`
- `globalSection`
- `orientation`
- `fixedLine`
- `transitionFromBelow`
- `resolutionStatus`
- `sourceRefs`
- `resolverRule`
- `residualId` se necessario

## Set di verità manuale iniziale
Usare i casi già verificati nella sessione ETW-V0 come test di regressione; non richiederli nuovamente all'utente. Tra i casi confermati figurano:
- P18: 110×30 con orientamento persistente;
- P23: 110×30 con orientamento persistente;
- P30: 30×110 globale, compatibile con famiglia locale 110×30 orientata ortogonalmente;
- P02: G1 40×50 → G2 40×45;
- P03: G1 40×50 → G2 40×45;
- P05: G1 50×40 → G2 45×40;
- P28: G1 50×40 → G2 45×40;
- P01: G1 50×40 → G2 45×40;
- P26: G1 50×40 → G2 50×35.

Questi dati sono `RIF/HUMAN_VALIDATED` finché non vengono collegati a evidence crop persistente.

## Gate v1
PASS solo se:
1. nessuna sezione è propagata automaticamente tra ordini;
2. `110×30` locale e `30×110` globale sono distinguibili senza falso conflitto;
3. l'orientamento resta persistente salvo evidenza contraria;
4. le riseghe sono classificate separatamente dalle rotazioni;
5. ogni assegnazione conserva provenienza e stato epistemico;
6. i casi del set di verità vengono riprodotti;
7. i casi non risolvibili confluiscono nella coda residui invece di essere forzati;
8. N041 e altri identity gap non vengono promossi automaticamente.

## Strategia operativa
1. Trascrivere una sola volta TAV-07A in una tabella strutturata `order × group × localSection × pillarList × reinforcement` con riferimento all'immagine/crop sorgente.
2. Collegare tale tabella al crosswalk Pxx↔Nxxx.
3. Derivare l'orientamento globale dalla carpenteria e conservarlo sulla catena.
4. Eseguire il resolver su tutte le catene.
5. Produrre `VERTICAL_COLUMN_SECTION_MATRIX` e `UNRESOLVED_QUEUE`.
6. Richiedere intervento umano soltanto sui residui reali.

## Vincolo di processo
Il modello operativo può lavorare esclusivamente sullo strato strutturato. Le immagini originali restano evidenza primaria e devono essere indirizzabili tramite riferimenti persistenti; la mancata capacità del modello di interpretarle direttamente non deve bloccare il resolver.
