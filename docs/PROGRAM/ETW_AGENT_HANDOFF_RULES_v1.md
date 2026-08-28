# ETW Agent Handoff Rules v1

1. One promotion-owner work item per result.
2. Support-agent findings are independent evidence and cannot mutate queue state.
3. Owner results must reference the exact candidate revision validated by gates/HVA/smoke.
4. Critical safety findings from support agents block owner PASS.
5. PREP_ONLY work returns PREP_PASS, never PASS, while external promotion blockers remain.
6. Human gates are closed only by explicit human-authority evidence recorded outside agent output.
7. CEW promoted baseline is an external authority dependency and cannot be synthesized by eTwin agents.
8. Any cross-project leakage, cross-discipline leakage, false equivalence, wrong SourceVersion, or Level-C auto-completion is immediate FAIL/stop.
9. Failures found in Z0 are routed to the owning slice; Z0 performs no functional fix.
10. TEST_ONLY data and lifecycle fixtures never enter N12 canonical engineering history.
