# CEW Exposure & Condition Research v1

Date: 2026-08-24
Status: RESEARCH_BASELINE
Purpose: preserve the technical basis used to design the CEW Project Exposure & Condition Model. This document is not a project evidence source and does not authorize engineering values.

## Source hierarchy reviewed

1. **ISO 16311-1:2024 — Maintenance and repair of concrete structures — Part 1: General principles.** ISO describes a through-life framework for maintenance and repair of existing concrete structures and explicitly distinguishes time-dependent deterioration from short-duration damage.
2. **ISO 16311-2:2024 — Part 2: Assessment of existing concrete structures.** ISO identifies deterioration from time-dependent actions such as reinforcement corrosion as a trigger for assessment and provides a general assessment framework.
3. **fib Model Code for Concrete Structures 2020.** fib extends the model-code framework to existing structures, including durability, structural monitoring, through-life assessment and interventions.
4. **fib Bulletin 109 (2023), Existing concrete structures life management, testing and structural health monitoring.** Organizes through-life management around data acquisition/testing and monitoring, condition assessment, performance prediction/modelling and decision making.
5. **fib Bulletin 112 (2024), fib MC(2020) complementary guidance on concrete durability.** Provides technical background for durability of new and existing structures, including transport processes and durability-related properties.
6. **fib Bulletin 102, Guide for Protection and Repair of Concrete Structures.** Provides a repair/protection background relevant to later intervention generations; it is not used here to infer current condition.
7. **Eurocode 2 / JRC material.** Confirms durability is a core design requirement and that exposure classes and concrete cover are linked to deterioration mechanisms. Exposure-class labels are not automatically assigned to an existing element without project evidence.
8. **Research on Bayesian updating of carbonation deterioration models using in-situ inspection data.** Supports the CEW principle that model priors may be updated with inspection evidence; simulation remains distinct from measurement.

## CEW conclusions adopted

- Exposure and condition are separate concepts. Exposure describes environmental/action context; condition describes observed or measured state.
- Deterioration and accidental/short-duration damage must remain distinct claim classes.
- A structural element may have multiple exposed faces with different protection/wetting histories; exposure therefore belongs at face/zone level when evidence permits.
- No EN/Eurocode exposure class is inferred merely from geography, age or visual appearance.
- No deterioration mechanism is activated solely because it exists in the model registry.
- Observed damage may update mechanism plausibility but cannot by itself define hidden material parameters.
- Project observations, measurements and model-derived states retain separate epistemic states.
- Through-life history is generation based: original/as-built, observed current, modeled scenario, intervention and post-intervention states remain separately queryable.

## Minimum Project Exposure & Condition data model

Each exposure-zone or element-face record should be capable of carrying:
- target entity / face / zone;
- location class: INTERNAL / EXTERNAL / BURIED / SHELTERED_EXTERNAL / WET_ZONE / ND;
- direct rain exposure state;
- wetting-drying state;
- ground/contact-water state;
- chloride relevance decision;
- freeze-thaw relevance decision;
- chemical-attack relevance decision;
- protection system type and condition;
- cover evidence, if measured/documented;
- observed crack/spall/rust/exposed-rebar condition;
- carbonation/chloride/corrosion measurement refs when available;
- source/evidence state and observation date;
- mechanism-screening outputs, never automatic activation.

## Safety rule

This research document supports schema and workflow design only. Numerical deterioration parameters require a separately registered technical model/reference, project applicability decision, parameter provenance, uncertainty model and human review before execution.

## Web sources consulted
- ISO 16311-1:2024: https://www.iso.org/standard/86446.html
- ISO 16311-2:2024: https://www.iso.org/standard/79786.html
- fib Model Code 2020: https://shop.fib-international.org/publications/model-codes/model-code-2020/
- fib Bulletin 109: https://www.fib-international.org/publications/fib-bulletins/existing-concrete-structures-life-management-testing-and-structural-health-monitoring-em-pdf-em-detail.html
- fib Bulletin 112: https://www.fib-international.org/component/virtuemart/model-code-supporting-documents/i-fib-i-mc-2020-complementary-guidance-on-concrete-durability-pdf-detail.html
- fib Bulletin 102: https://www.fib-international.org/component/virtuemart/model-code-supporting-documents/guide-for-protection-and-repair-of-concrete-structures-pdf-detail.html
- JRC Eurocode 2 overview: https://eurocodes.jrc.ec.europa.eu/EN-Eurocodes/eurocode-2-design-concrete-structures
