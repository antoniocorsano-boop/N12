# SDD ledger — plan: docs/superpowers/plans/2026-11-01-cew-cal01-primary-metric-calibration.md

- Base: `ee23c221118064022fa77b694ff88119530cc454` (qualified CEW-SPIRAL-01 predecessor).
- Execution mode: inline on isolated successor branch `feat/cew-cal01-primary-metric-calibration`.
- Pre-flight: Task 0 produces activation evidence consumed by all later tasks; Tasks 1→2 freeze the anchor contract/inventory consumed by Tasks 3–7; Task 3 split is consumed by Tasks 4–5; Task 4 calibration is consumed by Tasks 5–7; Task 6 projection is consumed by Task 7; Task 8 qualifies all prior outputs; Task 9 consumes the qualification receipt. No interface conflict found.
- Ruling: workflow scaffolding is introduced during Task 0 rather than Task 8 because this remote execution harness requires GitHub Actions to observe the mandatory RED test. Task 8 will expand the same workflow into full exact-source qualification. Cost if wrong: CI structure changes earlier, but no product/engineering authority changes.
