# CEW Vercel Candidate Deployment Policy v1

Status: REQUIRED DELIVERY / QUOTA GOVERNANCE  
Date: 2026-08-28  
Provider project: `cew-pilot`  
Machine contract: `automation/CEW_VERCEL_DEPLOY_POLICY_v1.json`

## 1. Problem

Vercel Hobby limits deployments within its free-plan quota. The previous Git integration created a Preview deployment for each qualifying Git push/PR revision. In an AI-native development loop this couples implementation frequency to hosting consumption and can exhaust the deployment quota before a human-acceptance candidate exists.

The desired chain is:

`WORKING COMMITS -> GITHUB GATES -> IMMUTABLE CANDIDATE -> GATED PREVIEW REF -> ONE VERCEL PREVIEW -> HUMAN EVALUATION`

not:

`EVERY COMMIT -> VERCEL PREVIEW`.

## 2. Decision

The Vercel Git Integration remains connected, but ordinary branches are disabled in `vercel.json`:

```json
"git": {
  "deploymentEnabled": {
    "**": false,
    "vercel-preview/**": true
  }
}
```

Only refs whose name matches `vercel-preview/**` may cause an automatic Vercel deployment.

GitHub Actions creates such a ref **only after** the exact candidate SHA satisfies the declared same-SHA gate set.

Therefore Vercel still performs the deployment through the existing Git Integration, but it never sees ordinary working branches as deployable candidates.

## 3. Why the preview ref is safe

The preview branch is only a Git reference. It does not create a new commit.

Example:

`vercel-preview/b341bcb53f23-r1 -> b341bcb53f23e8b9d0e8653596b98cec2f5be0e3`

The source revision deployed by Vercel is therefore exactly the already-validated SHA.

The ref does not:

- rewrite history;
- change the candidate;
- create engineering authority;
- satisfy HVA;
- promote B1.

## 4. Candidate rules

Before a gated preview ref may be created:

1. the candidate must be a full immutable SHA;
2. the SHA must be the head of an open pull request;
3. every workflow listed in `CEW_VERCEL_DEPLOY_POLICY_v1.json` must have its latest same-SHA run at `completed/success`;
4. the generated ref must point to that exact SHA;
5. the first automatic generation is `r1`;
6. repeated workflow triggers for the same SHA/generation are idempotent and do not create another push.

The GitHub workflow persists a commit status:

`CEW/Vercel Candidate Trigger`

when the candidate ref has been admitted.

The Vercel integration then supplies its own deployment status on the same commit.

## 5. Automatic trigger

The workflow:

`.github/workflows/deploy-cew-vercel-candidate.yml`

listens for completion of selected late CEW gates.

Every invocation re-checks the complete required gate list. If the set is not fully green, the workflow exits without creating a Vercel ref.

When the complete gate set becomes green, the deterministic `r1` ref is created once.

This converts many intermediate commits into **zero Vercel deployments** and normally converts one accepted technical candidate into **one Preview deployment**.

## 6. Manual retry without changing candidate SHA

The workflow also supports `workflow_dispatch` with:

- `candidate_sha`;
- `retry_generation`.

This is used only for operational recovery, for example after Vercel returns a temporary quota/rate-limit error.

A retry uses a new technical ref such as:

`vercel-preview/<same-sha>-r2`

while still pointing to the **same immutable candidate SHA**.

Therefore a hosting retry does not invalidate the GitHub gate evidence and does not require a code change merely to obtain a new Preview attempt.

## 7. Credentials

No Vercel token is required.

The controlled workflow only creates a Git ref using the built-in GitHub Actions token. The existing Vercel Git Integration performs the deployment.

Consequences:

- no `VERCEL_TOKEN` repository secret;
- no Vercel credential in files, logs or comments;
- no duplicated deployment credential lifecycle;
- the existing Vercel/GitHub trust boundary remains the deployment mechanism.

## 8. Production boundary

This policy deliberately governs **Preview candidates only**.

Ordinary Git branches, including development and product programme branches, remain disabled from automatic Vercel deployment by the catch-all `"**": false` rule.

Production is **not** re-enabled by this policy. A future Production mechanism must remain downstream of:

`HVA -> accessibility -> B1 promotion -> CEW_PROMOTED_BASELINE`

and must have its own explicit production-deployment contract.

Thus:

`Preview != HVA != Production != canonical engineering authority`.

## 9. Existing Production

Adopting this policy does not remove or modify any already-running Production deployment. It changes only which future Git refs are admitted to create deployments.

## 10. Quota effect

Under the new model:

- ordinary working commit: **0 Vercel deployments**;
- additional commit before all gates green: **0 Vercel deployments**;
- first green candidate: normally **1 Preview**;
- external quota failure: no code change; after quota reset an explicit `r2` retry may create **1 additional Preview attempt**;
- actual product rework: new SHA, new gate set, new candidate Preview.

This aligns hosting consumption with product maturity instead of coding frequency.

## 11. Current B1.8 candidate

The already-frozen B1.8 candidate `b341bcb53f23e8b9d0e8653596b98cec2f5be0e3` predates this policy, so its own `vercel.json` still permits ordinary Git integration behavior.

The default-branch orchestrator is designed to support explicit retry of that same SHA after quota reset without creating a new commit. Future candidates created from the policy-admitted CEW baseline will automatically inherit the gated-branch rules.

## 12. Stop rules

Never:

- re-enable ordinary branch previews merely for convenience;
- create a `vercel-preview/**` ref before the same-SHA gate set is green;
- point a candidate ref at a different SHA than the accepted candidate;
- change code merely to retry a hosting quota failure;
- use an older deployment as evidence for a newer SHA;
- interpret a Vercel deployment as HVA or product promotion;
- use this Preview policy to bypass the future Production promotion boundary.
