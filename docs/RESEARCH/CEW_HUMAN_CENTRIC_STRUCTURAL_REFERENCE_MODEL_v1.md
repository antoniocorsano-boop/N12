# CEW Human-Centred Structural Reference Model v1

Status: RESEARCH / DESIGN BASIS
Date: 2026-08-27

## 1. Important qualification

There is no single recognized standard named “Human-Centred Structural Engineering Development Model” that directly specifies how to build a software product such as CEW.

CEW therefore uses a transparent synthesis of established references, each within its proper scope. The resulting **Human-Centred Structural Engineering Lifecycle** is a CEW product model, not a new technical standard and not a replacement for applicable structural regulations.

## 2. Human-centred development reference

### ISO 9241-210:2019 — Human-centred design for interactive systems

Role in CEW:
- understand context of use;
- specify user requirements;
- produce design solutions;
- evaluate designs against user requirements;
- iterate through the system life cycle.

CEW extension:
Every user requirement is tied to an engineering decision, evidence need, authority boundary and consequence of error.

Official reference:
https://www.iso.org/standard/77520.html

## 3. Existing-structure assessment reference

### ISO 13822:2010 — Assessment of existing structures

Role in CEW:
Provides the general structural-reliability basis for assessment of existing buildings, bridges and other structures, including cases involving deterioration, changes of use and reliability checks.

CEW use:
- explicit assessment objective;
- evidence acquisition;
- uncertainty/residual management;
- model and assessment decision chain.

Official reference:
https://www.iso.org/standard/46556.html

## 4. Italian existing-structure workflow spine

### D.M. 17 January 2018 — NTC 2018, Chapter 8

Role in CEW Italian profile:
The visible project workflow must support the professional information needed for existing structures, including:
- historical-critical analysis;
- survey;
- mechanical characterization of materials;
- knowledge levels and confidence factors;
- actions;
- safety assessment;
- intervention classification/design where applicable.

This is implemented through project phases, InformationRequirements and EngineeringRulePacks rather than hard-coded UI text or solver constants.

Official Gazzetta reference:
https://www.gazzettaufficiale.it/eli/id/2018/2/20/18A00716/sg

Official Chapter 8 PDF source:
https://www.gazzettaufficiale.it/eli/gu/2018/02/20/42/so/8/sg/pdf

### Circolare 21 January 2019 n. 7 C.S.LL.PP.

Role in CEW:
Implementation/interpretation support for NTC project workflows and existing-structure knowledge/assessment.

Official Gazzetta reference:
https://www.gazzettaufficiale.it/atto/serie_generale/caricaArticoloDefault/originario?atto.codiceRedazionale=19A00855&atto.dataPubblicazioneGazzetta=2019-02-11&atto.tipoProvvedimento=CIRCOLARE

## 5. Information requirements and open exchange

### buildingSMART IDS 1.0

Role in CEW:
IDS demonstrates the product pattern that information requirements should be explicit, machine-interpretable and checkable rather than hidden in prose or scripts.

CEW adopts an IDS-inspired `InformationRequirement` primitive even where the canonical CEW graph is not IFC.

Official reference:
https://www.buildingsmart.org/standards/bsi-standards/information-delivery-specification-ids/

Important limitation:
CEW does not equate IDS compliance with engineering correctness. Information presence/shape and engineering authority are separate gates.

### buildingSMART IFC

Role in CEW:
Open model exchange and stable external identity mapping.

CEW policy:
The native canonical structural graph remains authoritative. IFC is an interoperability projection where its semantics support the intended exchange.

Official reference:
https://standards.buildingsmart.org/IFC/

## 6. Condition, maintenance and lifecycle reference

### ISO 16311-2:2024 — Assessment of existing concrete structures

Role in CEW:
Supports the condition/assessment workflow for existing concrete structures, including deterioration and safety/serviceability assessment.

Official reference:
https://www.iso.org/standard/79786.html

### fib existing-structure / Model Code lifecycle concepts

Role in CEW:
Through-life assessment, deterioration, monitoring, intervention and reassessment patterns inform P8, P15 and P16.

CEW keeps observed condition, degradation models, structural effects and intervention generations separate.

## 7. CEW synthesis

The combined model is:

```text
ISO 9241-210
human context / iterative design
        |
        v
CEW ENGINEERING DECISION MODEL
        |
        +------------------------------+
        |                              |
        v                              v
NTC 2018 / ISO 13822             IDS / IFC / CDE patterns
existing assessment              requirements / exchange
        |                              |
        +---------------+--------------+
                        |
                        v
              CEW CANONICAL TWIN
                        |
              condition / investigation
                        |
                        v
                 solver / FEM
                        |
                        v
                  verification
                        |
                        v
               intervention / lifecycle
                        ^
                        |
             ISO 16311 / fib patterns
```

## 8. Expert-board interpretation

The references are reviewed through competency roles rather than a single generic “expert”:

- structural assessment;
- reinforced concrete/materials;
- seismic analysis;
- geotechnics;
- survey/diagnostic testing;
- durability/degradation;
- FEM/computational mechanics;
- BIM/openBIM/information management;
- human factors;
- QA/independent checking;
- field execution;
- asset-owner decisions;
- software/provenance assurance.

The board is a product design/review matrix. It does not replace appointment of licensed/qualified professionals for actual engineering work.

## 9. Design conclusion

CEW should not imitate a CAD/BIM/FEM product and then add provenance afterward.

The product architecture must begin with the professional decision lifecycle and use evidence, canonical models, information requirements, agents and solvers as coordinated services supporting that lifecycle.
