# ETW TAV-06S Roof Support Graph Correction Audit v1

## Purpose
Prevent propagation of a first-pass visual label-reading error in the G5 roof support graph.

## Authoritative support-presence basis
`ETW_TAV06S_ROOF_SUPPORT_INVENTORY_v1.csv` remains the authoritative direct-reading inventory for numbered roof supports. It records 25 supports as PRESENT and nine as ABSENT/TERMINATES_BELOW_ROOF.

## Correction
The first visual graph pass incorrectly used `P17` and `P21` as G5 support nodes. This contradicted the verified inventory, where both are ABSENT at roof level.

The graph has therefore been corrected:
- `P17` removed from all G5 roof edges; it remains a G4 termination (`S` on Telaio 5).
- `P21` removed from all G5 roof edges; it remains a G4 termination (`V` on Telaio 5).
- compressed labels were rebound against the verified present-support set before any further topology use.

## Current rule
No support may enter the G5 roof graph unless:
1. it is PRESENT in `ETW_TAV06S_ROOF_SUPPORT_INVENTORY_v1.csv`; and
2. the local TAV-06S line trace supports the proposed edge.

The inventory therefore dominates any isolated visual reading of a compressed numeral.

## Consequence
No analytical/FEM roof member was generated from the superseded P17/P21 edges. The correction occurred before model release.
