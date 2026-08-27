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

## Autorità

La UI, la sessione, il database audit e il deploy non sono fonti di autorità ingegneristica. La decisione entra nel sistema soltanto come receipt umana F7 e deve superare i contratti già esistenti.

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
2. schema `CEW_USER_WEB_PILOT_SUPABASE_v1.sql` applicato;
3. variabili segrete configurate lato server;
4. deploy Vercel completato;
5. `/healthz` riporta storage persistente pronto;
6. smoke autenticato su Control Room e task F7;
7. nessuna receipt reale dell'utente è stata precompilata o sintetizzata durante il collaudo.
