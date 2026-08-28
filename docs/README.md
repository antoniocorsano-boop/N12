# N12 / CEW / eTwin Documentation Index

Status: CANONICAL NAVIGATION INDEX  
Authority source: `automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json`

This index makes the repository readable without reconstructing product policy from chat history, file timestamps or branch chronology.

## Start here

1. **How the product agency operates**  
   `docs/GOVERNANCE/AI_NATIVE_PRODUCT_AGENCY_OPERATING_MODEL_v1.md`

2. **How documentation authority works**  
   `docs/GOVERNANCE/DOCUMENTATION_AUTHORITY_MODEL_v1.md`

3. **Who owns which capability across eTwin / CEW / N12**  
   `docs/GOVERNANCE/CEW_ETWIN_PRODUCT_FAMILY_CAPABILITY_MAP_v1.md`

4. **Current CEW product programme**  
   `docs/PROGRAM/CEW_PRODUCT_COMPLETION_PROGRAM_v1.md`

5. **Current CEW development model**  
   `docs/PROGRAM/CEW_CODE_DEVELOPMENT_MODEL_v2.md`

6. **Current CEW human-centred / GOV.UK model**  
   `docs/PROGRAM/CEW_HUMAN_CENTRED_GOVUK_MODEL_v2.md`

7. **Current CEW Candidate/HVA runtime policy**  
   `docs/GOVERNANCE/CEW_CANDIDATE_RUNTIME_POLICY_v1.md`

8. **Current eTwin platform promotion programme**  
   `docs/PROGRAM/ETWIN_PLATFORM_EXTENSION_OVER_CEW_v2.md`

9. **Current eTwin agentic promotion orchestration**  
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

### CEW Candidate/HVA runtime

Primary provider for the current phase:

`Render / cew-hva-candidate`

Machine policy:

`automation/CEW_CANDIDATE_RUNTIME_POLICY_v1.json`

Runtime state:

`automation/CEW_CANDIDATE_RUNTIME_STATE_v1.json`

Infrastructure definition:

`render.yaml`

Render is an operational Candidate/HVA runtime only. Deployment does not imply HVA, promotion or engineering authority. Vercel remains a controlled Preview fallback under `automation/CEW_VERCEL_DEPLOY_POLICY_v1.json`.

### eTwin programme state

`automation/ETW_PROGRAM_STATUS_v1.json` and the eTwin queue/gate state referenced by `automation/ETW_PROGRAM_MANIFEST_v1.json`.

These execution-state files retain v1 compatibility references for the already-prepared A0 branch. Future promotion is governed by the cross-product manifest and v2 programme.

### Cross-product governance

`automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json`

This is the first machine-readable file agents consult for current product/documentation authority.

### Cross-product agent rules

`automation/AI_NATIVE_AGENT_OPERATING_CONTRACT_v1.json`

Agents are a bounded workforce with least authority. Read does not imply write; proposal does not imply approval; implementation does not imply promotion.

### Product decisions

`automation/PRODUCT_DECISION_REGISTER_v1.json`

Material product/governance changes are persisted here and linked to durable decision records.

## Directory map

| Directory | Role |
|---|---|
| `docs/GOVERNANCE/` | cross-product operating, authority, runtime and capability-boundary rules |
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

## Candidate runtime rule

The HVA runtime is deployed only after one immutable SHA is selected and has passed the declared automated gates. The runtime must expose the exact SHA and pass `/readyz` before participant observation begins.

Working commits do not require Candidate/HVA deployment.

Render Free may cold-start after inactivity; the service is warmed and `/readyz` is verified before a session. The warm-up itself is operational preparation and does not count as HVA evidence.

## Historical documents

Historical documents remain deliberately available. A file with an older version number is not automatically current authority. Use `automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json` and decision records to resolve the current governing document.

## Agent reading order

For cross-cutting product work agents read, in order:

1. `automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json`;
2. L0 governance docs referenced there;
3. the product-family capability map;
4. the cross-product agent operating contract;
5. the Candidate Runtime policy when work affects deployed human evaluation;
6. the relevant current product/programme plan;
7. current state;
8. selected queue/work item;
9. capability contract(s);
10. product decision register and applicable decision records;
11. relevant receipts/evidence.

Agents do not infer current policy from chat history or modification timestamps.
