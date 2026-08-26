# CEW Agent Communication Protocol v0

Status: EXPERIMENTAL
Purpose: make agent communication concise, actionable and evidence-backed while preserving engineering rigor.

## 1. Default communication shape

For substantial repository work, agents communicate in this order:

**STATE** — repository/branch/head and active work item.

**DONE** — concrete outputs actually produced.

**EVIDENCE** — gates, receipts, counts, source/version IDs or failing facts.

**HUMAN DECISION** — only when a genuine semantic/engineering decision remains. Present alternatives and consequences compactly.

**NEXT EXECUTION** — one action that the system can execute next; do not dump a long roadmap unless explicitly requested.

## 2. Action-first rule

Do not respond with a plan when the authorized work can be executed in the current cycle.

Bad:

`Ora analizzerò la tavola e poi preparerò un classificatore.`

Required behavior:

Execute the authorized analysis, create the artifact, run its gates, then report the result.

## 3. Completion language

Use `COMPLETE` only when:
- required outputs exist;
- provenance is recorded;
- required tests/gates ran;
- the current head/receipt is identified;
- no mandatory human gate is being hidden.

Use `BLOCKED_HUMAN_DECISION` only when mechanical/technical work is complete and the remaining choice is genuinely professional or semantic.

Use `BLOCKED_EVIDENCE` when required authoritative evidence is missing.

Use `FAIL_STOP` when a gate demonstrates that the tranche cannot safely continue.

Never call work complete merely because a document, branch or candidate exists.

## 4. Brevity contract

Default progress update: maximum 5 compact bullets or equivalent short paragraphs.

Do not repeat:
- the full project history;
- already accepted architecture;
- long lists of unchanged modules;
- generic explanations of AI/agents;
- previously resolved decisions.

Expand only when the user asks for analysis, design rationale or audit detail.

## 5. Engineering uncertainty

Never hide uncertainty behind fluent prose.

State uncertainty as machine-relevant status:
- `CANDIDATE`;
- `SUPPORTED`;
- `VALIDATED`;
- `CONFLICT`;
- `ND`;
- `BLOCKED_EVIDENCE`.

When presenting alternatives, include the evidence that differentiates them.

## 6. Human decision package

A human gate should fit this structure:

| Option | Evidence | Consequence | Agent recommendation |
|---|---|---|---|
| A | ... | ... | ... |
| B | ... | ... | ... |

Then request exactly one decision.

The agent may recommend but may not silently convert recommendation into approval.

## 7. Repository communication

Every repository update should identify only the information needed to resume safely:
- branch;
- head SHA;
- work item;
- gate result;
- residual/blocker;
- next eligible action.

Conversation memory is not authority; repository state and receipts are.

## 8. Anti-stall rule

An agent must not stop merely because one sub-step failed if the failure is technically repairable inside scope.

Expected loop:

`execute -> observe failure -> diagnose -> repair -> rerun -> finish`

Escalate only when:
- the fix would cross an authorization/promotion boundary;
- authoritative evidence is missing;
- multiple valid engineering meanings require human choice;
- a safety/governance gate explicitly requires human approval.

## 9. Final response template

For ordinary implementation work:

```text
STATE — <branch/head/work item>
DONE — <what now exists>
GATES — <PASS/FAIL evidence>
DECISION — <only if needed>
NEXT — <one executable next action>
```

This protocol governs tone and communication; it does not weaken technical documentation or audit records stored in the repository.
