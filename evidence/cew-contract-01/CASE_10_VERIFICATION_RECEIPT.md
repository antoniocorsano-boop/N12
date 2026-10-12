# CASE 10 — Verification and Receipt

**Status:** `PASS`.

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

## Qualification conclusion

Esiste una trasformazione N12 reale con input identificato, hash/versione contestuale, run/artifact, output, stato di Verification e Receipt; include proprio il caso non-PASS richiesto dal contratto. `C01-T10 = PASS`.
