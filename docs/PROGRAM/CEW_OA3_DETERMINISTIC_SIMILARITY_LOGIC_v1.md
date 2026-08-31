# CEW OA-3 — Deterministic Similarity Logic v1

OA-3 starts only from a `HUMAN_TAUGHT_NON_CANONICAL_PROTOTYPE` produced by OA-2.

`Find Similar` ranks scene objects by a versioned, deterministic and explainable score. Geometry may be used as one similarity signal, but similarity never creates object type, family membership or structural identity.

Signals v1:

- geometry kind;
- dimension ratio;
- orientation;
- topology hint;
- spatial context;
- associated text.

Every candidate carries signal scores and reason codes. Results are proposals for human review only.

The downstream sequence remains:

`OA-3 Find Similar -> OA-4 Human Cluster Review -> OA-5 Structural Resolver`.

OA-3 explicitly forbids automatic cluster confirmation, automatic family promotion, structural identity creation and canonical writes.
