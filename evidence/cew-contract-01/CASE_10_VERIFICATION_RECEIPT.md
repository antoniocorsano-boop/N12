# CASE 10 — Verification and Receipt

**Local evidence status:** `PASS` per il pattern Verification/Receipt.  
**CEW gate consequence:** `C01-T10 = BLOCKED_INPUT` finché manca la catena reale completa fino a `SolverRun → Result`.

## Real transformation

Artefatto: `data/canonical/N12_G4_HIRES_MACHINE_REVIEW_RECEIPT_v1.json` sulla branch operativa N12.

La trasformazione documentata è una revisione visuale macchina HiRes di una sorgente primaria, con output volutamente non promosso a verità ingegneristica.

## Input

Il Receipt identifica:

- Source `TAV-05A`;
- path nell'archive immutabile;
- archive commit e Git blob SHA;
- pagina 1;
- render a 300 dpi;
- dimensioni del render;
- SHA-256 del render.

## Execution / output

Registra:

- `review_pack_run_id`;
- `review_pack_artifact_id`;
- digest dell'artefatto;
- tre findings con bbox, lettura visuale, entity scope e precisione del binding.

## Verification semantics

Lo stato è `CURRENT_REVIEW_RECEIPT_NOT_ENGINEERING_AUTHORITY`. Ogni finding dichiara `engineering_promotion_authorized=false` e una promotion requirement esplicita.

I guardrail includono:

- machine visual review ≠ human engineering approval;
- recupero di un'etichetta a livello riga ≠ binding a un singolo membro;
- bbox di crop ≠ geometria di modello;
- dimensione mancante non completabile per apparenza;
- il PDF primario resta source authority.

Questo corrisponde a una Verification con esito sostanziale `REVIEW_REQUIRED`, non a un falso PASS tecnico.

## Receipt distinction

Il Receipt prova che il processo di review è tracciato e riproducibile. Non certifica la correttezza ingegneristica del dato né ne autorizza la promozione canonica.

## Why this does not close C01-T10

Il piano di qualifica approvato richiede che `C01-T10` possa essere `PASS` solo con la catena reale completa usata anche per `C01-T02` e `C01-T09`. Poiché `CASE_09_END_TO_END_ASSURANCE.md` è `BLOCKED_INPUT` sull'assenza di un SolverRun/Result autorizzato, questa receipt è **evidenza supplementare del pattern di assurance**, non sostituto di un risultato strutturale reale.

## Qualification conclusion

Il sottocontratto Verification/Receipt è sostenuto da un caso N12 reale. Il test end-to-end `C01-T10` resta `BLOCKED_INPUT` fino al primo SolverRun/Result autorizzato e riproducibile.
