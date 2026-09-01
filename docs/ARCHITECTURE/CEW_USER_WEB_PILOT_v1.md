# CEW User Web Pilot v1

## Obiettivo

Rendere CEW utilizzabile dal tecnico come applicazione browser, senza download/upload manuale dei pacchetti di revisione e senza trasformare la UI in autorità ingegneristica.

Percorso utente previsto:

`Login -> Project Control Room -> Residuo F7 -> Revisione fonte -> Invia a CEW -> validazione receipt -> promotion gate -> semantic gate -> patch candidate`

La catena termina sempre prima di qualunque scrittura canonica automatica.

## Pilot

Il pilot è `SINGLE_OPERATOR_PILOT` e utilizza:

- FastAPI come shell web coerente con il runtime Python CEW;
- sessione browser HttpOnly;
- password e session secret configurati esclusivamente nell'ambiente di deploy;
- audit delle receipt append-only;
- filesystem append-only soltanto in sviluppo locale;
- Supabase append-only obbligatorio nel deploy serverless;
- Vercel come target di pubblicazione del runtime FastAPI.

## Regola fail-closed

In produzione, se l'autenticazione o lo storage audit persistente non sono configurati, CEW non accetta receipt. Non è consentito usare il filesystem effimero di una funzione serverless come archivio delle decisioni umane.

Per il percorso OAR G4, la sola presenza della tabella audit non è sufficiente: la transizione revisionale deve essere serializzata dal database e la ricostruzione dello storico deve osservare una vera snapshot MVCC server-side. Il runtime Supabase è quindi considerato correttamente provisionato per OAR soltanto quando sono stati applicati, in questo ordine:

1. `automation/CEW_USER_WEB_PILOT_SUPABASE_v1.sql` — crea e protegge lo storage append-only `cew_human_receipt_audit`;
2. `sql/CEW_OAR_G4_ATOMIC_APPEND_v1.sql` — crea `cew_oar_region_revision_heads`, esegue il **backfill governato delle head mancanti dalle receipt legacy OAR già presenti**, poi crea la RPC `cew_oar_append_region_receipt_v1` per il compare-and-set revisionale e la RPC `cew_oar_read_region_receipts_v1` che materializza l'intero storico OAR visibile in una singola statement/snapshot MVCC.

### Backfill revisionale prima del CAS

Un ambiente può contenere receipt legacy `CEW_OAR_REGION_GEOMETRY_RECEIPT_v1` create prima dell'introduzione della tabella `cew_oar_region_revision_heads`. In questo caso il CAS non può assumere `UNBOUND`: deve prima riallineare il revision head allo stato ricostruibile dallo storico append-only già persistito.

La migration governata deve quindi, **prima di creare/abilitare la RPC CAS**:

- considerare soltanto receipt OAR con invarianti di authority coerenti (`engineering_authority_effect=NONE`, `canonical_write_authorized=false`, `structural_identity_authorized=false`, `oar_human_confirmation=false`);
- ricostruire `GEOMETRY_CONFIRMED` quando esiste una conferma governata che riferisce un proposal governato dello stesso `binding_id/support_id`, mantenendo come `current_proposal_decision_id` il proposal confermato;
- in assenza di conferma, ricostruire `PROPOSED` dall'ultimo proposal governato disponibile;
- usare **`ON CONFLICT (binding_id, support_id) DO NOTHING`**, così un head già gestito dal CAS non viene mai sovrascritto dal backfill;
- non cancellare né modificare le receipt legacy: il documento append-only resta l'autorità di audit e la head è solo stato revisionale runtime.

L'assenza del backfill rende non valido l'upgrade di un ambiente con receipt legacy e il runtime OAR deve essere considerato **non provisionato**. Il backfill non autorizza classificazione OAR, identità strutturale o scritture canoniche.

La RPC di lettura OAR deve attraversare PostgREST come **un solo valore JSON aggregato**, contenente almeno `receipt_count` e `receipts`; non deve restituire una riga API per receipt. In questo modo il limite `Max Rows` di PostgREST non può troncare silenziosamente lo storico OAR. Il client deve verificare `receipt_count == len(receipts)` e fallire chiuso in caso di incoerenza.

### Upgrade della RPC di lettura

Le revisioni precedenti della migration OAR hanno creato `cew_oar_read_region_receipts_v1()` con return type `TABLE(receipt_json jsonb)`. PostgreSQL non consente di cambiare quel return type a `jsonb` mediante `CREATE OR REPLACE FUNCTION` sulla stessa signature. La migration governata deve quindi eseguire **`DROP FUNCTION IF EXISTS public.cew_oar_read_region_receipts_v1();` prima della nuova `CREATE FUNCTION`**. L'assenza di questo passaggio rende l'upgrade non valido e il runtime OAR deve essere considerato non provisionato. Il drop riguarda esclusivamente una RPC runtime-audit read-only e non modifica receipt persistite, revision heads o authority ingegneristica.

La seconda migration dipende dalla prima e non la sostituisce. Un deploy che abilita il backend Supabase per OAR senza entrambe le RPC è **non provisionato** per il percorso OAR e deve fallire chiuso. La lettura OAR non deve ricostruire una snapshot tramite timestamp applicativi, watermark temporali o più richieste `LIMIT/OFFSET` su stati database differenti.

## Autorità

La UI, la sessione, il database audit e il deploy non sono fonti di autorità ingegneristica. La decisione entra nel sistema soltanto come receipt umana F7 e deve superare i contratti già esistenti.

Le RPC OAR sono esclusivamente boundary di concorrenza e audit runtime: non confermano la classificazione OAR, non creano identità strutturale, non materializzano EvidenceRegion canoniche e non autorizzano scritture canoniche.

Sono vietati dal pilot:

- scrittura canonica diretta;
- chiusura automatica di un residuo;
- modifica di F2;
- riapertura M0-G;
- sintesi automatica di una lettura umana non espressa;
- perdita della distinzione fra armatura superiore e inferiore.

## Attivazione

Il codice può essere integrato prima del provisioning. Lo stato `USER_WEB_RUNTIME` resta `PENDING_EXTERNAL_PROVISIONING` finché non sono soddisfatti tutti i seguenti punti:

1. database audit CEW isolato;
2. schema `automation/CEW_USER_WEB_PILOT_SUPABASE_v1.sql` applicato;
3. migration `sql/CEW_OAR_G4_ATOMIC_APPEND_v1.sql` applicata quando il runtime espone il Workbench OAR G4 su Supabase;
4. se sono presenti receipt legacy OAR e mancano revision head, verifica del backfill governato prima dell'abilitazione CAS, senza overwrite di head esistenti (`ON CONFLICT DO NOTHING`);
5. verifica presenza RPC `cew_oar_append_region_receipt_v1`, RPC `cew_oar_read_region_receipts_v1` e tabella `cew_oar_region_revision_heads` prima di abilitare write o read OAR;
6. verifica che `cew_oar_read_region_receipts_v1` ritorni un singolo JSON aggregato con `receipt_count` coerente con `receipts`;
7. per upgrade da una revisione table-returning, verifica che la migration abbia eseguito `DROP FUNCTION IF EXISTS` prima della ricreazione scalar-jsonb e che il return type attivo sia `jsonb`;
8. variabili segrete configurate lato server;
9. deploy Vercel completato;
10. `/healthz` riporta storage persistente pronto;
11. smoke autenticato su Control Room e task F7;
12. smoke OAR, se il percorso OAR è esposto nel deploy, prova una transizione revisionale atomica e una lettura snapshot MVCC senza alcuna promozione di authority;
13. nessuna receipt reale dell'utente è stata precompilata o sintetizzata durante il collaudo.
