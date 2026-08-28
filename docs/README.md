# N12 / CEW / eTwin Documentation Index

Status: CANONICAL NAVIGATION INDEX  
Authority source: `automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json`

This index makes the repository readable without reconstructing product policy from chat history, file timestamps or branch chronology.

## Start here

1. **How the product agency operates**  
   `docs/GOVERNANCE/AI_NATIVE_PRODUCT_AGENCY_OPERATING_MODEL_v1.md`

2. **How documentation authority works**  
   `docs/GOVERNANCE/DOCUMENTATION_AUTHORITY_MODEL_v1.md`

3. **Current CEW product programme**  
   `docs/PROGRAM/CEW_PRODUCT_COMPLETION_PROGRAM_v1.md`

4. **Current CEW development model**  
   `docs/PROGRAM/CEW_CODE_DEVELOPMENT_MODEL_v2.md`

5. **Current CEW human-centred / GOV.UK model**  
   `docs/PROGRAM/CEW_HUMAN_CENTRED_GOVUK_MODEL_v2.md`

6. **Current eTwin platform promotion programme**  
   `docs/PROGRAM/ETWIN_PLATFORM_EXTENSION_OVER_CEW_v2.md`

7. **Current eTwin agentic promotion orchestration**  
   `docs/PROGRAM/ETW_AGENTIC_DEVELOPMENT_ORCHESTRATION_v2.md`

## Historical preparation contracts

The following remain authoritative **for understanding how the already-prepared ETW-A0 evidence was produced**, but not for future promotion policy:

- `docs/PROGRAM/ETWIN_PLATFORM_EXTENSION_OVER_CEW_v1.md`
- `docs/PROGRAM/ETW_AGENTIC_DEVELOPMENT_ORCHESTRATION_v1.md`

The prepared ETW-A0 head is preserved as historical preparation evidence and must be revalidated under current promotion/human governance before A0 promotion.

## Authority boundaries

### N12 engineering authority

`knowledge/CURRENT_STATE.json` plus governed canonical engineering artifacts.

CEW/eTwin product documentation does not replace or upgrade N12 engineering facts.

### CEW product/runtime authority

`data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json`

This reports current CEW product/runtime maturity and points to governing contracts.

### eTwin programme state

`automation/ETW_PROGRAM_STATUS_v1.json` and the eTwin queue/gate state referenced by `automation/ETW_PROGRAM_MANIFEST_v1.json`.

These execution-state files may retain references to the v1 preparation contract while the already-prepared A0 branch remains unpromoted. Future promotion is governed by the cross-product manifest and v2 programme.

### Cross-product governance

`automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json`

This is the first machine-readable file agents should consult for current product/documentation authority.

## Directory map

| Directory | Role |
|---|---|
| `docs/GOVERNANCE/` | cross-product operating and authority rules |
| `docs/PROGRAM/` | product/programme delivery models |
| `docs/ARCHITECTURE/` | system/product architecture |
| `docs/PRODUCT/` | bounded capability contracts |
| `docs/ACCEPTANCE/` | acceptance/evaluation plans and reports |
| `docs/AUDIT/` | independent audit/assurance |
| `docs/DECISIONI/` | material decisions and supersession evidence |
| `docs/MIGRATION/` | migration/adoption boundaries |
| `automation/` | machine-readable contracts, queues and state |
| `automation/receipts/` | observed execution evidence |
| `data/canonical/` | declared canonical product/runtime data |
| `knowledge/` | N12 engineering knowledge authority |

## Current Human Factors decision

`docs/DECISIONI/PRODUCT_HF_001_PARTICIPANT_REVIEWER_SEPARATION_v1.md`

The first CEW B1.7 Acceptance Lab demonstrated that participant work, telemetry, reviewer decision and receipt export must be separated. Future CEW/eTwin HVA instruments follow the v2 human-centred model.

Current B1 machine contract:

`automation/CEW_B1_HUMAN_ACCEPTANCE_CONTRACT_v2.json`

Historical B1.7 instrument contract:

`automation/CEW_B1_USABILITY_ACCEPTANCE_CONTRACT_v1.json`

The v1 instrument remains evidence of what was implemented and observed; it is not silently rewritten.

## Historical documents

Historical documents remain deliberately available. A file with an older version number is not automatically current authority. Use `automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json` and decision records to resolve the current governing document.

## Agent reading order

For cross-cutting product work agents read, in order:

1. `automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json`;
2. L0 governance docs referenced there;
3. the relevant current product/programme plan;
4. current state;
5. selected queue/work item;
6. capability contract(s);
7. applicable decision records;
8. relevant receipts/evidence.

Agents do not infer current policy from chat history or modification timestamps.
