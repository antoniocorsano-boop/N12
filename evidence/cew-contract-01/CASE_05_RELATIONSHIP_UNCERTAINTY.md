# CASE 05 — Relationship Uncertainty

**Case:** raccordo Telaio 5 ↔ topologia TAV.5, segmento semantico C5 `V→Z`.  
**Status:** `PASS`.

## Real N12 evidence

`data/canonical/telaio5_tav5_candidate_matrix_v1.csv` conserva due binding concorrenti per lo stesso segmento C5, target 2.90 m:

- `HYP_A_METRICA`: `N049→N001`, misura 2.905 m, delta +0.005 m, stato `CANDIDATO_METRICO_SOLO`;
- `HYP_B_CONNESSA`: `N010→N025`, misura 2.195 m, delta -0.705 m, stato `CANDIDATO_RESPINTO_PARZIALE`, reason `errore eccessivo su C5`.

`tav5_topology_connections_v07.csv` conserva inoltre le relazioni nodo-nodo candidate con stato epistemico `INF_DA_QUOTARE`.

## CEW representation

Fixture logica della Relationship, senza promozione canonica:

- **Relationship semantic target:** `spans_between(V,Z)`;
- **Claim A:** binding candidato `N049→N001`;
- **Claim B:** binding candidato `N010→N025`;
- **Evidence:** candidate matrix + connection registry;
- **epistemic state:** inferenziale/candidato, non `DOC`;
- **Conflict:** due candidate bindings incompatibili per la stessa Relationship semantica;
- **Decision:** HYP_B è `CANDIDATO_RESPINTO_PARZIALE`; HYP_A resta candidato e richiede verifica di continuità, quindi nessun binding viene promosso qui a certezza documentale;
- **version:** gli artefatti sono esplicitamente versionati `v1` / `v07`.

## Qualification conclusion

Il caso dimostra su dati N12 reali che una Relationship può portare Evidence, stato epistemico, Claim concorrenti, Conflict, Decision e versione propri. `C01-T08 = PASS`.
