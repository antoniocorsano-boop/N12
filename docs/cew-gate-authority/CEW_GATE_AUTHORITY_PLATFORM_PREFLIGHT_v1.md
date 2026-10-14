# CEW Gate Authority — Platform Preflight v1

**Data:** 2026-10-13  
**Repository:** `antoniocorsano-boop/N12`  
**Scopo:** fissare le capacità GitHub realmente osservabili prima del bootstrap G0/A0, senza modificare Settings e senza attivare il production control plane.

## Decisione trigger

`PREFERRED_TRIGGER=workflow_dispatch`

Motivo: la disponibilità/configurazione specifica delle nuove Actions Policies necessarie ad autorizzare in modo ristretto `pull_request_target` non è osservabile attraverso gli strumenti API disponibili in questa esecuzione. La specifica impone `pull_request_target` soltanto dopo verifica esplicita della policy; in caso contrario il fallback canonico è `workflow_dispatch` trusted.

Questa decisione è reversibile. Il passaggio futuro a `pull_request_target` richiede una verifica umana dei Settings e una revisione del workflow/policy; non può essere inferito da CI verde.

## Fatti repository verificati via GitHub API

- Repository: pubblico.
- Ownership: user-owned (`antoniocorsano-boop`), non organization-owned.
- Default branch: `main`.
- `main` head al preflight: `91529683753f36cc4fb70e2d6326531ccf3740f9`.
- Branch protection su `main`: disabilitata.
- Required status checks su `main`: nessuno.
- Repository rulesets rilevati: nessuno.
- Auto-merge repository: disabilitato.
- Il branch di bootstrap parte da `main`; PR #147 non è usata come base e resta read-only audit source.

## Capacità non dimostrabili tramite gli strumenti API disponibili

Le seguenti voci NON sono assunte come disponibili:

| Capacità | Stato preflight | Conseguenza |
|---|---|---|
| Actions Policy specifica per `pull_request_target` | `HUMAN_VERIFICATION_REQUIRED` | usare `workflow_dispatch` fino a verifica esplicita |
| Artifact Attestations nel repository/account | `HUMAN_VERIFICATION_REQUIRED` | qualification può essere sviluppata; promotion con attestazione resta subordinata a Task 10 |
| UI repository-level ruleset creation | `HUMAN_VERIFICATION_REQUIRED` | nessuna modifica Settings in Task 1; target documentato per Task 11 |
| source-app binding / required-check semantics per eventuale Promotion Publisher | `HUMAN_VERIFICATION_REQUIRED` | nessun publisher viene assunto necessario o sufficiente |

## Target governance minimo, non ancora applicato

Per `main`, prima dello stato `OPERATIONAL`, il target è:

- pull request obbligatoria;
- force-push bloccato;
- deletion bloccata;
- required checks soltanto dove la semantica del commit H è stata verificata;
- bypass minimizzato e documentato;
- auto-merge non autorizzato.

Nessuna di queste modifiche viene applicata da questo task.

## Trigger fallback contract

Con `workflow_dispatch`:

1. l'input include PR number e exact requested H;
2. il Gate Core verifica che H sia il current head della PR prevista prima di creare la CandidateIdentity;
3. il Candidate viene letto esclusivamente come Git objects/blobs;
4. il check generato non viene assunto come required PR check;
5. la prova CEW canonica resta la Qualification Receipt B/G/A/H/O;
6. eventuale promotion automation è un problema separato e non viene anticipato nel bootstrap.

## Precondizioni umane future

Prima di attivare un eventuale `pull_request_target` o modificare la governance repository occorre verificare nei Settings:

1. disponibilità delle Actions Policies;
2. possibilità di autorizzare specificamente il CEW Gate Authority senza liberalizzare genericamente eventi privilegiati;
3. disponibilità delle Artifact Attestations;
4. disponibilità/configurabilità di repository rulesets;
5. bypass actors effettivi.

## Esito Task 1

`PLATFORM_PREFLIGHT=PASS_WITH_HUMAN_SETTINGS_VERIFICATION`

Nessun production workflow è stato attivato. Nessuna impostazione repository è stata modificata. Nessun merge è stato eseguito.
