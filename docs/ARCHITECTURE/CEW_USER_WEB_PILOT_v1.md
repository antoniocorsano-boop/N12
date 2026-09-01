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
- backend persistente Neon, Supabase o Netlify secondo il runtime autorizzato;
- Vercel/Render/Netlify soltanto come runtime, mai come autorità ingegneristica.

## Regola fail-closed

In produzione, se l'autenticazione o lo storage audit persistente non sono configurati, CEW non accetta receipt. Non è consentito usare il filesystem effimero di una funzione serverless come archivio delle decisioni umane.

Per il percorso OAR G4, la sola presenza della tabella audit non è sufficiente: la transizione revisionale deve essere serializzata dal database e la ricostruzione dello storico deve osservare una snapshot coerente. Per Supabase il provisioning governato resta:

1. `automation/CEW_USER_WEB_PILOT_SUPABASE_v1.sql` — crea e protegge lo storage append-only `cew_human_receipt_audit`;
2. `sql/CEW_OAR_G4_ATOMIC_APPEND_v1.sql` — crea `cew_oar_region_revision_heads`, installa il replay governato `cew_oar_replay_region_head_v1`, esegue il backfill delle head mancanti, crea la RPC CAS `cew_oar_append_region_receipt_v1` e la RPC snapshot `cew_oar_read_region_receipts_v1`.

### Replay revisionale prima del CAS

Un ambiente può contenere receipt legacy `CEW_OAR_REGION_GEOMETRY_RECEIPT_v1` create prima dell'introduzione della tabella `cew_oar_region_revision_heads`. In questo caso il CAS non può assumere `UNBOUND`: deve prima riallineare il revision head allo **stesso stato prodotto dalla macchina anchored-transition governata**.

È vietato derivare la head con euristiche del tipo “ultimo proposal” o “ultima confirmation per timestamp”. In particolare la sequenza:

`P0 -> replacement P1 -> delayed CONFIRM(P0)`

deve restare `P1 / PROPOSED`, perché la conferma tardiva del predecessore è una transizione concorrente stale/non-mutating. Una head `P0 / GEOMETRY_CONFIRMED` sarebbe incompatibile con `aggregate()` e renderebbe il CAS inutilizzabile.

Il replay/backfill deve quindi:

- ordinare e validare lo storico governato con gli stessi anchor e stati del dominio OAR;
- preservare le replacement proposal che hanno già avanzato la revisione;
- classificare come stale/non-mutating le confirmation legate a un predecessore quando una replacement ha già vinto;
- fallire chiuso su history malformed, duplicate decision ID, authority divergence, bbox invalide o anchor incompatibili;
- usare **`ON CONFLICT (binding_id, support_id) DO NOTHING`** per non sovrascrivere head già gestite dal CAS;
- non cancellare né modificare receipt legacy: la head è soltanto una proiezione runtime del registro append-only;
- lasciare invariati `canonical_write_authorized=false`, `structural_identity_authorized=false`, `oar_human_confirmation=false`, `engineering_authority_effect=NONE`.

La regola vale per **ogni backend atomico**:

- **Supabase/PostgreSQL**: `cew_oar_replay_region_head_v1(binding_id,support_id)` esegue il replay server-side; la migration lo usa per il backfill iniziale e la RPC CAS lo richiama sotto `pg_advisory_xact_lock` quando trova una head mancante.
- **Neon/PostgreSQL**: sotto lo stesso advisory lock della write, il runtime legge lo storico OAR e deriva la head tramite `cew_oar_g4_revision_head.py`, che delega direttamente a `cew_oar_g4_region_binding.aggregate()`; una history non valida blocca la write.
- **Netlify Database**: `cew-oar-replay.mjs` riproduce le anchored transitions; il seed della head entra nello stesso statement CAS soltanto se il `receipt_count` del database coincide ancora con quello dello snapshot appena replayed. Se lo storico cambia, la write fallisce con revision conflict e richiede refresh invece di usare una head stale.

Un runtime con receipt legacy e head mancanti che non dispone di questo replay è **non provisionato per OAR** e deve fallire chiuso.

### Snapshot OAR Supabase

La RPC di lettura OAR deve attraversare PostgREST come **un solo valore JSON aggregato**, contenente almeno `receipt_count` e `receipts`; non deve restituire una riga API per receipt. In questo modo il limite `Max Rows` di PostgREST non può troncare silenziosamente lo storico OAR. Il client deve verificare `receipt_count == len(receipts)` e fallire chiuso in caso di incoerenza.

### Upgrade della RPC di lettura

Le revisioni precedenti della migration OAR hanno creato `cew_oar_read_region_receipts_v1()` con return type `TABLE(receipt_json jsonb)`. PostgreSQL non consente di cambiare quel return type a `jsonb` mediante `CREATE OR REPLACE FUNCTION` sulla stessa signature. La migration governata deve quindi eseguire **`DROP FUNCTION IF EXISTS public.cew_oar_read_region_receipts_v1();` prima della nuova `CREATE FUNCTION`**. L'assenza di questo passaggio rende l'upgrade non valido. Il drop riguarda esclusivamente una RPC runtime-audit read-only e non modifica receipt persistite, revision heads o authority ingegneristica.

La lettura OAR non deve ricostruire una snapshot tramite timestamp applicativi, watermark temporali o più richieste `LIMIT/OFFSET` su stati database differenti.

## Autorità

La UI, la sessione, il database audit e il deploy non sono fonti di autorità ingegneristica. La decisione entra nel sistema soltanto come receipt umana e deve superare i contratti già esistenti.

Le RPC e le revision head OAR sono esclusivamente boundary di concorrenza e audit runtime: non confermano la classificazione OAR, non creano identità strutturale, non materializzano EvidenceRegion canoniche e non autorizzano scritture canoniche.

Sono vietati dal pilot:

- scrittura canonica diretta;
- chiusura automatica di un residuo;
- modifica di F2;
- riapertura M0-G;
- sintesi automatica di una lettura umana non espressa;
- perdita della distinzione fra armatura superiore e inferiore.

## Attivazione

Il codice può essere integrato prima del provisioning. Lo stato `USER_WEB_RUNTIME` resta `PENDING_EXTERNAL_PROVISIONING` finché non sono soddisfatti tutti i seguenti punti:

1. database audit CEW isolato e append-only;
2. schema audit del backend applicato;
3. migration OAR atomica applicata quando il runtime usa Supabase;
4. se sono presenti receipt legacy OAR e mancano revision head, replay governato completato **con semantica anchored-transition**, senza overwrite di head esistenti;
5. per Neon, verifica che il missing-head path derivi la revisione dallo stesso `aggregate()` governato prima del CAS;
6. per Netlify, verifica del replay module e del seed protetto da `receipt_count` nello statement CAS;
7. per Supabase, verifica presenza `cew_oar_replay_region_head_v1`, `cew_oar_append_region_receipt_v1`, `cew_oar_read_region_receipts_v1` e `cew_oar_region_revision_heads`;
8. verifica che `cew_oar_read_region_receipts_v1` ritorni un singolo JSON aggregato con `receipt_count` coerente con `receipts`;
9. per upgrade da una revisione table-returning, verifica del `DROP FUNCTION IF EXISTS` prima della ricreazione scalar-jsonb;
10. variabili segrete configurate lato server;
11. `/healthz` riporta storage persistente pronto;
12. smoke autenticato su Control Room e task governati;
13. smoke OAR prova una transizione revisionale atomica, una lettura snapshot coerente e il regression legacy `P0 -> P1 -> delayed CONFIRM(P0) = P1/PROPOSED`;
14. nessuna receipt reale dell'utente è stata precompilata o sintetizzata durante il collaudo.
