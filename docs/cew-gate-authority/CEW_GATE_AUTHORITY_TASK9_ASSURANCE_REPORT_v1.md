# CEW Gate Authority Task 9 — Assurance Report v1

**Data:** 14 ottobre 2026  
**Stato:** PRE-REVIEW ASSURANCE COMPLETE — FRESH INDEPENDENT REVIEW REQUIRED  
**Repository:** `antoniocorsano-boop/N12`  
**PR:** #149 — `CEW Gate Authority Task 9 — trusted qualification workflow`  
**Baseline main:** `692630b3961bff770273e170181c5e025deafdc4`  
**Certified pre-report head:** `35c8ec4b073631ced1869a8b3351ed39d8c43a3c`  
**Spec:** `docs/superpowers/specs/2026-10-14-cew-gate-authority-task9-trusted-workflow-design.md`  
**Plan:** `docs/superpowers/plans/2026-10-14-cew-gate-authority-task9-trusted-workflow.md`

## 1. Assurance decision boundary

Questo report documenta l'assurance tecnica pre-review di Task 9. Non promuove, non attiva e non integra il control plane.

In particolare NON autorizza:

- merge della PR #149;
- transizione Ready;
- auto-merge;
- attivazione production su `main`;
- CEW-FEM-01;
- solver, `SolverRun` o `Result`;
- modifica, chiusura o supersession della PR #147;
- modifica di G0, A0, I01..I17 o schema Qualification Receipt.

Lo stato finale `TASK9_ASSURANCE_PASS` richiede una fresh independent review sull'exact final head successivo al commit di questo report.

## 2. Scope del delta certificato

Il confronto `692630b3961bff770273e170181c5e025deafdc4...35c8ec4b073631ced1869a8b3351ed39d8c43a3c` è 13 commit ahead / 0 behind.

Il delta è limitato a:

- `.github/workflows/cew-gate-authority.yml`;
- `.github/workflows/validate-cew-gate-authority-task9.yml`;
- `cew_gate_control_plane/`;
- `tests/cew_gate_control_plane/`;
- specifica e piano Task 9.

Non risultano modificati file sotto `cew_gate_authority/`, A0, `G0_MANIFEST.json` o `G0_PROMOTION_RECORD_v1.json`.

## 3. Trust anchor preservato

### G0

- exact reviewed commit: `1f32a24f456e7db18c994096e4c8f5067222a592`;
- source bundle SHA-256: `b56a98461373f59bc54ad3bd88d3047cff45a7f840b862248a99cd33ed3fe766`;
- manifest Git blob: `318a38199e5d7643e654442b9d92cbf41c94dd7f`.

Il blob corrente di `governance/cew-gate-authority/gate-core/G0_MANIFEST.json` sul certified pre-report head è ancora `318a38199e5d7643e654442b9d92cbf41c94dd7f` e dichiara lo stesso source-bundle digest.

### A0

- authority ID: `N12_CEW_CONTRACT_01_A0`;
- Git blob: `d6f71146b5b833650f1943021d956e1a2d742563`;
- SHA-256: `88ab731c986cef0af474bf567a9bb19a12a43dcdbef2de6cb211107b17f92dbb`.

Il blob corrente A0 sul certified pre-report head è ancora `d6f71146b5b833650f1943021d956e1a2d742563`.

### Operational Authority O

- exact commit: `d806dcca72779b5a186defe557a7a9b739575a90`.

### Human promotion record

`governance/cew-gate-authority/G0_PROMOTION_RECORD_v1.json` resta invariato e continua a legare G0/A0/O alle identità sopra, con tutte le cinque authority-boundary flag `false` e `cew_fem_01_required=true`.

## 4. Exact-head certification evidence

Sul certified pre-report head `35c8ec4b073631ced1869a8b3351ed39d8c43a3c`:

- Task 9 Validation run: `38514091852` — SUCCESS;
- `task9-certification` job: `115688865261` — SUCCESS;
- `task9-codeql` job: `115688865451` — SUCCESS;
- Bootstrap run: `38514091866` — SUCCESS.

Fresh results:

- Task 9 control-plane suite: **67/67 PASS**;
- promoted G0 regression suite: **251/251 PASS**;
- `python -m compileall -q cew_gate_control_plane cew_gate_authority`: PASS;
- actionlint `1.7.12`: PASS;
- zizmor `1.30.1`: PASS, no findings; 9 explicit offline suppressions;
- CodeQL Python analysis: PASS.

La validation workflow ha acquisito O prima di eseguire la suite G0.

## 5. Production control-plane contract

La workflow proposta `.github/workflows/cew-gate-authority.yml`:

- espone soltanto `workflow_dispatch`;
- accetta esattamente `pr_number` e `candidate_sha`;
- rigetta repository/ref/ref-type non canonici prima del Candidate fetch;
- acquisisce H da `refs/pull/<PR>/head` in repository bare, senza Candidate checkout/esecuzione;
- verifica metadata PR e exact requested/fetched H;
- materializza e verifica G0/A0/O per identità esatta;
- conserva Receipt sia per G0 exit 0 sia per exit 1;
- usa artifact immutable e consumer per `artifact-id`;
- verifica `run_id`, `run_attempt`, B/G/A/H/O e i due digest Receipt;
- riduce la decisione finale fail-closed;
- non contiene write scope, secret applicativi, OIDC o attestation scope.

Action pin production congelati:

- `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`;
- `actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97`;
- `actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9`;
- `actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333`.

## 6. Mandatory regression matrix — 34/34

1. non-main dispatch → `DispatchContractTests.test_rejects_non_main_branch`
2. tag dispatch → `DispatchContractTests.test_rejects_tag_ref`
3. invalid PR number → `DispatchContractTests.test_rejects_non_positive_or_non_integral_pr_number`
4. noncanonical SHA → `DispatchContractTests.test_rejects_noncanonical_candidate_sha`
5. PR unavailable/non-object → `PrMetadataContractTests.test_rejects_unavailable_or_nonobject_pr_metadata`
6. closed PR → `PrMetadataContractTests.test_rejects_closed_pr`
7. wrong base repository/branch → `PrMetadataContractTests.test_rejects_wrong_base_repository_or_branch`
8. requested H != current PR head → `PrMetadataContractTests.test_rejects_pr_head_mismatch`
9. force-push between metadata/fetch → `CandidateFetchIdentityTests.test_force_push_between_metadata_and_fetch_fails`
10. fetched ref != requested H → `CandidateFetchIdentityTests.test_fetched_ref_must_equal_requested_h`
11. fork PR consumed only as data → `CandidateNoExecTests.test_public_fork_candidate_is_accepted_as_data_via_base_pr_ref`
12. malicious Candidate never executed → `CandidateNoExecTests.test_malicious_candidate_files_are_never_executed` + existing `NoExecIntegrationTests.test_candidate_executables_hooks_actions_packages_and_workflow_never_run`
13. Candidate copies of G/A cannot substitute trusted inputs → `CandidateNoExecTests.test_candidate_copies_of_gate_or_authority_do_not_affect_trusted_inputs`
14. invalid/contradictory promotion record → `PromotionRecordTests.test_rejects_missing_record`, `test_rejects_wrong_schema_version_decision_or_repository`, `test_rejects_contradictory_g_a_o_identity`
15. wrong G0 commit → `MaterializedGateTests.test_rejects_wrong_g0_commit`
16. wrong G0 manifest blob → `MaterializedGateTests.test_rejects_wrong_g0_manifest_blob`
17. wrong source-bundle digest → `MaterializedGateTests.test_rejects_wrong_source_bundle_digest`
18. wrong A0 blob → `MaterializedGateTests.test_rejects_wrong_a0_blob`
19. wrong A0 SHA-256 → `MaterializedGateTests.test_rejects_wrong_a0_sha256`
20. O unavailable → `MaterializedGateTests.test_operational_commit_availability`
21. PASS Receipt survives handoff → `HandoffHappyAndFailReceiptTests.test_pass_receipt_survives_handoff`
22. FAIL Receipt preserved → `HandoffHappyAndFailReceiptTests.test_fail_receipt_survives_handoff`
23. exit 2 / no Receipt fails → `HandoffHappyAndFailReceiptTests.test_exit_2_without_receipt_is_rejected`
24. Receipt transport byte mutation → `HandoffTamperTests.test_receipt_transport_byte_mutation_fails`
25. Receipt newline mutation → `HandoffTamperTests.test_receipt_newline_mutation_fails`
26. canonical digest correct / transport digest wrong → `HandoffTamperTests.test_correct_canonical_but_wrong_transport_digest_fails`
27. wrong run ID → `HandoffTamperTests.test_wrong_run_id_fails`
28. wrong run attempt → `HandoffTamperTests.test_wrong_run_attempt_fails`
29. incoherent B/G/A/H/O → `HandoffTamperTests.test_incoherent_b_g_a_h_o_fails`
30. missing/invalid artifact identity → `ArtifactShapeTests.test_artifact_id_must_be_positive_integer_not_name`
31. verify-handoff never reads/fetches H → `ProductionWorkflowContractTests.test_verify_handoff_job_never_reads_or_fetches_candidate`
32. no write permission → `ProductionWorkflowContractTests.test_jobs_and_permissions_are_minimal`
33. Actions pinned to full SHA → `ProductionWorkflowContractTests.test_action_pins_are_exact_and_no_tag_forms`
34. Action pin identities equal frozen §12 values → `ProductionWorkflowContractTests.test_action_pins_are_exact_and_no_tag_forms`

## 7. Review-focus regressions

1. Duplicate JSON keys fail closed:
   - `PrMetadataContractTests.test_rejects_duplicate_json_keys`;
   - `PromotionRecordTests.test_rejects_duplicate_json_key`;
   - `ArtifactShapeTests.test_duplicate_json_keys_in_receipt_fail`;
   - `ArtifactShapeTests.test_duplicate_json_keys_in_envelope_fail`.
2. Artifact directory exact shape → `ArtifactShapeTests.test_missing_or_extra_artifact_file_fails`.
3. Candidate ref must be Git commit object → `CandidateFetchIdentityTests.test_fetched_ref_must_resolve_to_commit_object`.
4. Run identity type confusion → `HandoffTamperTests.test_run_identity_type_confusion_fails`.
5. Missing/null Candidate head repository → `PrMetadataContractTests.test_rejects_missing_head_repository`.

## 8. Remaining gate

La certificazione sopra copre l'implementazione precedente a questo documento. Dopo il commit del report deve essere eseguita una nuova exact-head certification della PR. Tale run viene conservata come evidenza esterna GitHub per evitare una ricorsione documentale in cui l'aggiornamento del report modificherebbe continuamente lo SHA che il report tenta di registrare.

Dopo la fresh certification del report commit è richiesta una **fresh independent Codex review sul medesimo exact head**.

Solo una review pulita, senza successive modifiche al branch, consente lo stato:

`TASK9_ASSURANCE_PASS — HUMAN MERGE/ACTIVATION DECISION REQUIRED`

Fino ad allora la PR #149 resta Draft e non è autorizzato alcun merge o activation step.
