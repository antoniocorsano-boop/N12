## Scope

CEW-CAD-INT-01 implements deterministic recovery after a confirmed CAD mutation and codifies real OpenCADStudio v2026.42 interoperability learned from CEW-CAD-LAB-004.

Stacked base: `fix/cew-cad-01-live-contract-repair` at `8a509a19efbb410d56beaaad40e1d5f7766ddcda`.

This PR does not authorize merge, deploy, OpenCADStudio adoption, CEW-FEM, canonical N12 CAD mutation, or a new live pilot.

## Current state

- design/spec committed;
- implementation plan committed;
- Task 1 causal RED tests committed for:
  - `entities_create.vertices` live `[x,y]` format;
  - live `result.handles` mutation response;
  - CallToolResult-like `model_dump()` response parsing;
- no Task 1 production patch yet.

## Governance

Future CEW internal AI is limited to inspection, reasoning, evidence binding and Changeset proposal. Raw `ocs_execute`, signing, policy relaxation and canonical writes remain outside model authority.
