# CEW OA-4 — Human Cluster Review Logic v1

OA-4 consumes only `DETERMINISTIC_SIMILARITY_CANDIDATES` produced by OA-3.

The similarity score is a review aid, not authority. Every candidate that is accepted, rejected, moved, marked ambiguous or deferred must receive an explicit human decision.

Allowed decisions:

- `CONFIRM_AS_FAMILY_CANDIDATE`;
- `REJECT`;
- `MOVE_TO_OTHER_FAMILY`;
- `MARK_AMBIGUOUS`;
- `DEFER_NEEDS_SOURCE`.

Batch review is allowed only for an explicit candidate selection. There is no implicit whole-cluster acceptance.

A confirmation creates a `HUMAN_REVIEWED_FAMILY_CANDIDATES` proposal. It does not create structural identity, canonical engineering data or project-material readiness.

The Workbench should focus the human on contrast and exceptions: highest-ranked candidate, weak/dissimilar case, ambiguous cases and explicit blockers.

Downstream remains:

`OA-4 Human Cluster Review -> OA-5 Structural Resolver -> OA-6 Project Material Gate`.
