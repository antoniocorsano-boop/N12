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

6. **eTwin platform programme**  
   `docs/PROGRAM/ETWIN_PLATFORM_EXTENSION_OVER_CEW_v1.md`

7. **eTwin agentic orchestration**  
   `docs/PROGRAM/ETW_AGENTIC_DEVELOPMENT_ORCHESTRATION_v1.md`

## Authority boundaries

### N12 engineering authority

`knowledge/CURRENT_STATE.json` plus governed canonical engineering artifacts.

CEW/eTwin product documentation does not replace or upgrade N12 engineering facts.

### CEW product/runtime authority

`data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json`

This reports current CEW product/runtime maturity and points to governing contracts.

### eTwin programme state

`automation/ETW_PROGRAM_STATUS_v1.json` and the eTwin queue/gate state referenced by `automation/ETW_PROGRAM_MANIFEST_v1.json`.

### Cross-product governance

`automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json`

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

The first CEW B1.7 Acceptance Lab demonstrated that participant work, telemetry, reviewer decision and receipt export must be separated. Future CEW/eTwin HVA instruments must follow the v2 human-centred model.

## Historical documents

Historical documents remain deliberately available. A file with an older version number is not automatically current authority. Use `automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json` and decision records to resolve the current governing document.

## Agent reading order

For cross-cutting product work agents should read, in order:

1. `automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json`;
2. L0 governance docs referenced there;
3. the relevant product/programme plan;
4. current state;
5. selected queue/work item;
6. capability contract(s);
7. decision records and receipts relevant to the change.
