# The GitHub harness: the lock and the signature as pull requests

The lock and the steward's signature are the two acts no agent makes. On one machine, where agents and people share one user account, a name typed after `--by` cannot settle who acted: two independent attacks on the tools showed a role reaching the lock command under a person's name. So in a real study each act is a pull request in the repository where the study lives, approved and merged on a protected branch. Who a person is, is then decided by the platform that person signs in to, and the tools on the machine are no part of that decision.

**None of this has run on GitHub.** The two scripts are tested as ordinary programs, on a throwaway repository and on payloads written in the platform's shapes (`fixtures/`). The workflow file is valid YAML and has never been started by GitHub. Read every "the platform does" below as designed, and tested here only as far as the scripts go.

## What is in this folder

| File | What it is |
|---|---|
| `acts.workflow.yml` | the workflow, as a template: copy it to `.github/workflows/acts.yml` of the repository where the studies live |
| `verify_request.py` | the required check on a pull request that touches a study's `lock-request/` or `signature-request/` |
| `record_act.py` | the job after the merge: writes the lock or the signature into the study log, with the people the platform recorded |
| `CODEOWNERS.template` | who must approve a pull request that touches a request, the tools, the definition or the workflows |
| `fixtures/` | event payloads in the platform's shapes, with placeholder logins, which the self-tests fill in and use |
| `harness.yaml` | what this harness holds and what it leaves to the repository's settings |

## How an act goes

1. An assistant, or a person, runs `uv run tools/sf.py request-lock --study studies/<study> --by <name>`. The tool makes every check the lock makes (the tests and rehearsals passed on exactly this plan and code, every rule met its criteria) and writes `studies/<study>/lock-request/EVIDENCE.md`, a summary in plain words of what a person is asked to approve, and `manifest.json`, the checksums of everything the lock would bind. It records nothing as locked.
2. The study is committed on a branch and a pull request is opened against the protected branch.
3. The check `request-check` runs `verify_request.py` with the scripts, the tools and the definition of the protected branch, never those of the pull request. It passes when the manifest matches the files at the head of the pull request, the pull request targets the protected branch, it changes nothing in `tools/`, `factory/` or `.github/`, enough people other than its author approve it, and no commit after an approval changed what the approval covered. It puts the evidence summary on the pull request.
4. The people the definition names read the summary, approve, and merge. The merge is the act.
5. The job `record` runs `record_act.py`: it reads the platform's own record of the merged pull request and of its reviews and has the study tool write `lock.recorded` into the study log under the actor `platform:github`, citing the merge commit, the pull request and the approving reviews. It commits the log under the repository's own identity.
6. `uv run tools/sf.py open-held-out --study studies/<study> --by <name>` then opens the held-out data only when the lock in the log is such a merge: the merge commit exists, lies on the protected branch's own line of commits, is reachable from what is checked out, brought the request in, and its manifest matches the files.

The signature goes the same way, with `sf.py request-signature --decision signed` (or `declined`) and the folder `signature-request/`.

## The checklist, done once for a repository

1. Put the science factory's `tools/` and `factory/` in the repository where the studies live, by a pull request.
2. Copy `acts.workflow.yml` to `.github/workflows/acts.yml`. If the protected branch is not `main`, change `branches:` in the workflow and `protected_branch:` in `factory/factory.yaml` to the same name.
3. Copy the lines of `CODEOWNERS.template` into `.github/CODEOWNERS` and put the real logins or teams in.
4. In the repository's settings, protect the branch: require a pull request before merging; require at least as many approvals as `approvals:` in `factory/factory.yaml`; require review from code owners; dismiss stale approvals when new commits are pushed; require the status check `request-check` to pass; require branches to be up to date; do not allow administrators to bypass; restrict who can push.
5. Let the workflow's own identity push the one commit that records an act: in the branch protection, allow `github-actions[bot]` to bypass the pull request requirement, and nobody else. If that is not acceptable, drop the last step of the `record` job and have it open a pull request with the study log instead; the lock then counts from the merge of that second pull request, which a person approves like any other.
6. Open a pull request that touches nothing in a study and see `request-check` report that there is nothing to check. Then make a practice study, request its lock, and take one pull request through, to see the summary appear and the lock recorded.

## What git alone can show, and what it cannot

From a clone, offline, `sf.py open-held-out` and `sf.py check-log` verify with git that the merge commit a lock cites exists, is one of the protected branch's own commits (its first parents), is an ancestor of what is checked out, brought the request's manifest in, and that the manifest matches the working tree. That much needs no platform.

git cannot show who approved, that an approval was required, or that the branch is protected. A person or an agent with the same account on the same machine can make a local branch called `main` and merge into it. Such a merge cannot be pushed to a protected branch, so a fresh clone from the platform does not have it; but a tool that reads only a local clone cannot tell. The people who approved are in the log entry as the recording job copied them from the platform, and the platform's own record of the pull request is where that claim is checked. An opening that matters is run from a fresh clone of the protected branch.

## Practice

`sf.py lock --local-practice --by human:<id> --evidence <an https link>` records a lock from the command line, as the tool did before this harness existed, and `sf.py signature --local-practice` the same. It is for trying the tools out, for the examples and for the self-tests. A study locked that way says so in `sf.py status`, on its scorecard and in its finding (the tool refuses a finding without the sentence), opens its held-out data only with `open-held-out --local-practice`, and never closes as a signed finding: it closes as `practice-ended`.
