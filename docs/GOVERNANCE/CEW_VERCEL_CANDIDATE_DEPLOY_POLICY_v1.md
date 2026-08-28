# CEW Vercel Candidate Deployment Policy v1

Status: REQUIRED DELIVERY / QUOTA GOVERNANCE  
Date: 2026-08-28  
Provider project: `cew-pilot`  
Machine contract: `automation/CEW_VERCEL_DEPLOY_POLICY_v1.json`

## 1. Problem

Vercel Hobby limits deployments within a rolling/free-plan quota. The previous Git integration created a Preview deployment for each qualifying Git push/PR revision. In an AI-native development loop this couples implementation frequency to hosting consumption and can exhaust the deployment quota before a human-acceptance candidate exists.

This is the wrong lifecycle relationship.

The desired chain is:

`WORKING COMMITS -> GITHUB GATES -> IMMUTABLE CANDIDATE -> ONE VERCEL PREVIEW -> HUMAN EVALUATION`

not:

`EVERY COMMIT -> VERCEL PREVIEW`.

## 2. Decision

Automatic Vercel Git deployments are disabled in `vercel.json`:

`git.deploymentEnabled = false`

A Vercel deployment is instead created by the controlled GitHub Actions workflow:

`.github/workflows/deploy-cew-vercel-candidate.yml`

The workflow checks out an **exact immutable SHA**, verifies the declared GitHub gates on that same SHA and deploys only after the candidate gate is green.

## 3. Preview rules

A Preview candidate must satisfy all of the following:

1. SHA is a full immutable Git commit SHA;
2. SHA is the head of an open pull request;
3. all workflows listed in `CEW_VERCEL_DEPLOY_POLICY_v1.json` have a latest same-SHA run with `completed/success`;
4. there is no already-successful `CEW/Vercel Candidate Preview` status for that SHA;
5. CI has access to the Vercel credential through GitHub Actions secret `VERCEL_TOKEN`;
6. the deployment targets `cew-pilot` under scope `antonios-projects-051b8d71`.

The Preview status is persisted on the commit as:

`CEW/Vercel Candidate Preview`.

This status is deployment evidence only. It does not satisfy HVA, accessibility, engineering authority or product promotion.

## 4. Automatic trigger

The candidate-deploy workflow listens for completion of selected late/aggregate CEW gates. Every invocation re-checks the full required gate list.

Therefore an early trigger exits without deployment while other required gates are still incomplete. Once the same SHA has the full green set, one controlled Preview may be emitted.

A SHA-scoped GitHub Actions concurrency group plus the commit deployment status prevent repeated deployments of the same accepted candidate.

## 5. Manual trigger

The same workflow supports `workflow_dispatch` for an explicitly supplied `candidate_sha`.

This does **not** bypass the Preview gate: Preview mode still requires an open PR head and the complete declared same-SHA gate set.

Manual dispatch exists for operational recovery, for example after an external Vercel quota reset, without requiring a new Git commit and therefore without invalidating the candidate's automated evidence.

## 6. Production boundary

Disabling Git auto-deploy also deliberately removes automatic Production publication from Git pushes.

Production may be requested only through controlled dispatch and only when:

- `automation/CEW_PROMOTED_BASELINE_v1.json` exists;
- the requested SHA is explicitly contained in that promoted-baseline artifact;
- the deployment is manually requested as `production`.

Until CEW promotion creates that baseline artifact, the workflow fails closed for Production.

This preserves:

`Preview != HVA != Production != canonical engineering authority`.

## 7. Credential boundary

The repository never stores a Vercel token.

One GitHub Actions secret is required:

`VERCEL_TOKEN`

The secret must be configured in repository Actions secrets. Missing credentials cause the workflow to stop before deployment.

The project and scope identifiers are non-secret deployment configuration and remain declared in the machine policy.

## 8. Existing Production

Adopting this policy does not delete or modify an existing Production deployment. It changes only the creation path for **future** deployments.

## 9. Quota effect

With this model, ten or twenty commits inside one slice consume GitHub CI but normally consume **zero Vercel deployments** until a green immutable candidate emerges.

A candidate should normally consume:

- one Preview deployment for HVA;
- later, one Production deployment after promotion.

New deployments caused by actual rework are deliberate because the candidate SHA has changed and the acceptance evidence must be regenerated.

## 10. Stop rules

Never:

- re-enable automatic Git previews merely to obtain a convenient URL;
- deploy a SHA whose declared candidate gates are not all green;
- create another Preview for a SHA that already has successful candidate deployment evidence;
- change the SHA only to work around a hosting quota;
- use an older deployment as evidence for a newer candidate;
- deploy Production without the promoted-baseline boundary;
- store `VERCEL_TOKEN` in repository files, comments or logs.
