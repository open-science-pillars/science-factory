# Proposal: an act attested by the workflow's own identity

**Science factory · 2026-11-26 · proposed; nothing here is built or tested.**

## What is missing

A lock or a signature is `verified` when `sf.py verify-acts` has asked the platform and the platform has confirmed the pull request, its approvals and the branch (`docs/WHAT-IS-ENFORCED.md`, the three standings). That rests on whoever ran the verification and on the machine it ran on. The answer is recorded in the study log, and a log entry can be written by hand; a request sent through a proxy with its own certificates is answered by that proxy. The remedy today is that anybody can ask the platform again. That works while the repository exists, the pull request has not been deleted and the reader has a token. It does not give a reader a thing they can check alone, later, with no trust in whoever verified.

## The proposal

After the merge, the `record` job of `factory/harnesses/github/acts.workflow.yml` already holds everything a verification asks for, from the platform's own side. It would write one small file for each act, the act statement:

- the study, the act (lock or signature), the repository, the protected branch and the merge commit;
- the sha256 of the request's `manifest.json` and of `EVIDENCE.md` as they are in the merge commit;
- the pull request's number and address, its author, who merged it and when;
- each approval that counts, as `verify_acts.py` counts them: the account, the commit it approved, when, and the checksum of the request at that commit;
- the branch's rules as the job's token was shown them, and what it was not shown.

The job would then have GitHub's artifact attestations sign that file (the `actions/attest` action, which signs through Sigstore with the short-lived certificate the workflow run is issued, and records the signature in a public transparency log). The certificate names the repository, the workflow file, the branch and the commit the run was started from. Nobody holds a signing key: the identity is the workflow run's own, given by the platform to that run and to nothing else. The job needs `id-token: write` and `attestations: write` for this and nothing more than it has now otherwise.

Verification would check, with `gh attestation verify` or any Sigstore client and no token:

1. that the signature over the act statement is valid and is in the transparency log;
2. that the signing identity is the workflow `acts.yml` of the repository the definition names, run from the protected branch (and not a workflow of a fork, or another workflow file);
3. that the statement's merge commit, manifest checksum and evidence checksum are the ones in the clone;
4. that the approvals in it meet what the definition asks.

An act that passes would have a fourth footing beside the three standings, or would be `verified` with the words "by attestation": the choice of word belongs to the build.

## What it would prove, and what it would not

It would prove that a run of that workflow, in that repository, on that branch, stated those approvals for that merge. An agent with a shell on a clone cannot make such a signature: it has no way to be issued the workflow's certificate. It would no longer matter who ran the verification, on which machine, through which proxy.

It would not prove that the workflow file was the reviewed one unless the identity check pins the workflow's own commit to the protected branch; that the people who can change the workflow are the right people (the code owners of `.github/`); or that the approving accounts are the right people. It moves the trust from "whoever verified" to "the platform's identity service, the transparency log, and whoever may merge a change to the workflow".

## Why it is not built in this round

It cannot be built and tested honestly from a machine that makes no request to the platform. The signing happens only inside a workflow run, and the verification has to be tried against a real attestation, a forged one, one from a fork and one from another workflow file. Writing the step into the workflow template without ever having seen it run would ship half of it, and the template already carries one thing that has never run. The statement's contents are a subset of what `verify_acts.py` gathers, so the first step of a build is small: have the job write the statement and commit it beside the request, then add the signing, then the check.

## What would have to be decided

- Whether an attested act needs the live verification as well, or replaces it at the opening (the opening would then need no token, only the attestation and a way to read the transparency log).
- Where the attestation lives so that a clone carries it: GitHub keeps attestations beside the repository; a bundle file committed beside the request would travel with the clone.
- Private repositories: their attestations are not in the public log, and verifying them needs access to the repository again.
