# CASE 09 — End-to-End Solver Assurance

**Status:** `BLOCKED_INPUT`.

## Required chain

Il test richiede un artefatto N12 reale che permetta:

`Source → Evidence → Observation → Claim → Decision → CanonicalProperty → CanonicalSnapshot → ModelGeneration → SolverRun → Result`

## What exists

Sono disponibili registri Source/Evidence/Observation reali e handoff di geometria/calcolo. In particolare:

- `M0G_GEOMETRY_HANDOFF_v1.json` congela geometria/topologia;
- `M1E_CALCULATION_MODEL_HANDOFF_v1.json` congela ciò che è trasferibile verso un solver shell.

## Blocking fact

`M1E_CALCULATION_MODEL_HANDOFF_v1.json` dichiara:

- `status = RESIDUAL_NOT_CALCULATION_MODEL_READY`;
- `calculation_model_ready = false`;
- sei domini bloccanti;
- `not_authorized_now`: non eseguire/validare un calcolo strutturale corrente usando proprietà, carichi, quota fondazione o parametri geotecnici inventati.

`CEW_PROJECT_STATE_CURRENT_v1.json` dichiara inoltre `R5 Solver Round Trip = PLANNED`.

## Qualification decision

Non viene creato un SolverRun sintetico, non viene inventato un Result e non viene reinterpretato un gate geometrico come risultato FEM.

La parte fino a ModelGeneration/handoff è rappresentabile; la prova reale di `SolverRun → Result` resta `BLOCKED_INPUT` fino all'esistenza di un run autorizzato e riproducibile.

Conseguenze:

- `C01-T02 Provenienza completa = BLOCKED_INPUT` per la catena fino a un Result tecnico;
- `C01-T09 Riproducibilità = BLOCKED_INPUT` per la porzione SolverRun/Result.
