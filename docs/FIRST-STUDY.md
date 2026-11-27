# Your first confirming study

A confirming study tests one claim, stated in advance, once, on fresh data. Your first one should be the **system trial**: every stage, both acts by people as real pull requests on GitHub, on a blind test case that the tool makes and seals at the opening, so that nobody knows the answer until after the steward has decided. It tests the factory, not a claim about the world, and it needs no data of your own. After it, the last section shows what changes in a study of your own: the fresh data, proposed by an agent and approved at the lock.

**What has been run, and what has not.** The set-up and block 1 were run in a scratch repository, with a local clone standing in for GitHub, and gave the outputs this page says to expect. Everything from the push on needs GitHub (the pull requests, the workflow, the opening and `verify-acts` asking GitHub) and has never been run by anybody: this page is that first run.

## What you need

- **A repository of your own on GitHub**, the one where the science lives, here called `my-science`, cloned beside a clone of this repository in one folder. It holds its own copy of `tools/`, `factory/`, `methods/` and the system trial's plan (one layout for every study; [CREATE-A-FACTORY.md](CREATE-A-FACTORY.md) says why).
- **The checklist done once**, in [factory/harnesses/github/README.md](../factory/harnesses/github/README.md): the workflow copied, code owners, the branch protected, the check `request-check` required.
- **A tracking issue** in that repository, opened from the request form or blank. The two log fingerprints are posted there.
- **A read token** for the opening and the verification: a fine-grained token for this one repository, with read access to Contents and Pull requests, given as `GH_TOKEN` for those commands only.
- `git`, `uv`, and bash or zsh.

## Set up, once

```
git clone https://github.com/open-science-pillars/science-factory
git clone https://github.com/OWNER/REPO my-science
cp -r science-factory/tools science-factory/factory science-factory/methods my-science/
mkdir -p my-science/examples/stand-alone
cp -r science-factory/examples/stand-alone/system-trial my-science/examples/stand-alone/
cd my-science
sed 's|example-org/example-studies|OWNER/REPO|' factory/factory.yaml > factory.yaml.new
mv factory.yaml.new factory/factory.yaml
uv run tools/check_factory.py
```

Put your repository's owner/name in place of `OWNER/REPO` in both lines. The system trial's plan is copied too, because the shipped benchmarks name it. The validator ends with `check-factory: VALID`. Commit these files by a pull request, as the checklist says, before the first study.

In every shell you use for the study:

```
sf() { uv run tools/sf.py "$@"; }
st() { uv run methods/gain/system_trial.py "$@"; }
T=examples/stand-alone/system-trial
W=studies/TRIAL-1
C=factory/change-log.jsonl
D=$(mktemp -d)
ME=human:YOUR-ID
M=THE-MODEL
```

`ME` is your own id; you type it in one place only, the reveal in block 4. `M` is the name of the model the agents run as; every command an agent runs carries it, and a person's carries none. Lines marked "agent" below are an agent's; with no agent at hand, a person may type them under the agent's name, which the log then records.

## 1. Agent: the tests, on a branch

```
git switch -c trial-1
mkdir -p $W
sed -e 's/^study: .*/study: TRIAL-1/' -e 's|\.\./\.\./\.\./methods|../../methods|' \
  $T/analysis-plan.yaml > $W/analysis-plan.yaml
sf start --study $W --id TRIAL-1 --by agent:coordinating --model $M \
  --question "In the blind test case, is the gain that was put in within five percent of one?"
sf fit --study $W --by agent:coordinating --model $M --file fit.yaml
sf log-change --study $W --by agent:coordinating --model $M --log $C \
  --problem "the factory has not run end to end with a person's lock and signature" \
  --change "The system trial: TRIAL-1 through every stage." \
  --rationale "No run has gone past the lock." \
  --predicted "A firm outcome that the sealed answer confirms, and every check passing."
sf check-plan --study $W
sf test known-answers --study $W --by agent:analysis --model $M
sf test working-data --study $W --by agent:analysis --model $M
sf rehearse --study $W --id opening-path --by agent:analysis --model $M
sf note --study $W --by agent:analysis --model $M --kind method \
  --about "the system trial: the notes path" \
  --text "Raised on purpose, so that the trial takes one note from raising to resolution."
sf curation-list --study $W
sf request-lock --study $W --by agent:coordinating --model $M
git add -A
git commit -m "TRIAL-1: tests passed, lock requested"
git push -u origin trial-1
```

`fit.yaml` is the coordinating agent's fit note, from `factory/agents/coordinating/skills/note-the-fit/fit-template.yaml` (for a system trial, `good-fit`: the answer is exact). What to expect: `started TRIAL-1`; `fit note recorded`; `change recorded under ...`; `plan check: the analysis plan is complete`; `known-answer tests: pass (exit 0)` after a minute or two; `working data: pass (exit 0)`; `rehearsal opening-path: pass (exit 0)`; `note NOTE-001 recorded`; `curation list: 1 open note(s) across 1 subject(s)`; and `lock request written`. Then open a pull request from `trial-1` into `main` on GitHub.

## 2. You: read, approve, merge. That is the lock.

Read the pull request: the evidence summary the check posts on it (also in `$W/lock-request/EVIDENCE.md`). It shows the question, each rule with each criterion and the rate measured beside it, the fresh data (for a system trial, a blind case made at the opening), what is held out and every change to it, every figure (the exploration's, and any a test or rehearsal declares under `figures:` in the plan) as a picture with its caption, the code by checksum, the definition and the models it declares, and the open notes. Look at each figure yourself: a table can agree with a claim that a picture shows is wrong. Approve and merge. Nothing is typed.

The workflow's `record` job then writes the lock into the study log on `main`, has GitHub asked, and prints a log fingerprint of the form `SEQ:HASH`: post it on the tracking issue. `GH_TOKEN=YOUR-READ-TOKEN sf status --study $W` gives the lock's standing, asked of GitHub then (without the token it can say no more than `merge found, people not verified`); it must be `verified` before the opening.

## 3. Agent: the opening, the write-up, the review

```
git switch main
git pull
git switch -c trial-1-result
LOCK=LOCKSEQ:HASH
GH_TOKEN=YOUR-READ-TOKEN uv run tools/sf.py open-held-out --study $W --by agent:coordinating --model $M
OPEN=OPENSEQ:HASH
git add -A -- . ':(exclude)studies/*/sealed/*'
git commit -m "TRIAL-1: the opening"
```

Put the two fingerprints in place of `LOCKSEQ:HASH` and `OPENSEQ:HASH`: the first from the tracking issue, the second as the opening prints it (post it there too). The opening asks GitHub whether the lock is a merge people approved, and refuses without a token or a network: it is not used up by the refusal. It prints `held-out data opened (held-out, opening 1)` and the outcome under the locked rule: `supported`, `refuted` or `inconclusive`.

Then the analysis agent writes `$D/writeup.md` from fields of `$W/receipts/held-out.json` only, and a fresh review agent, which did none of this, writes `$D/verdict.md`:

```
sf attach --study $W --by agent:analysis --model $M --file $D/writeup.md
sf review --study $W --by agent:review --model $M --verdict approve --file $D/verdict.md
sf check-log --study $W --anchor $LOCK --anchor $OPEN --change-log $C
sf request-signature --study $W --by agent:coordinating --model $M --decision signed \
  --anchor $LOCK --anchor $OPEN
git add -A -- . ':(exclude)studies/*/sealed/*'
git commit -m "TRIAL-1: the write-up, the review, signature requested"
git push -u origin trial-1-result
```

The log check prints `confirmatory study, ready for the steward's signature`. Open a second pull request. The sealed answer stays in `$W/sealed/`, out of both commits; nothing but this instruction stops anyone in the workspace opening it.

## 4. You: decide, then reveal the answer

Read the second pull request: the outcome under the locked rules, the figures the opening drew, the write-up that would be signed, and the review. For a system trial, signed means "I accept this trial if the sealed answer shows the factory was right". Approve and merge it; that is the signature, and the workflow records and verifies it. Then:

```
git switch main
git pull
git switch -c trial-1-close
st verdict --study $W --by $ME --anchor $LOCK --anchor $OPEN
```

The verdict prints the gain that was put in, what the factory said, and `right`, `not wrong (inconclusive)` or `WRONG`, and writes it into the study log.

## 5. Agents: learn and close

```
sf resolve --study $W --by agent:curating --model $M --note NOTE-001 --disposition declined \
  --comment "raised on purpose; nothing to route"
GH_TOKEN=YOUR-READ-TOKEN sf scorecard --study $W --anchor $LOCK --anchor $OPEN
sf log-change --study $W --by agent:coordinating --model $M --log $C \
  --problem "the factory has not run end to end with a person's lock and signature" \
  --change "The system trial: TRIAL-1 through every stage." \
  --rationale "No run has gone past the lock." \
  --predicted "A firm outcome that the sealed answer confirms, and every check passing." \
  --observed "The verdict was right and every check passed."
GH_TOKEN=YOUR-READ-TOKEN sf close --study $W --by agent:coordinating --model $M --outcome system-trial-accepted \
  --anchor $LOCK --anchor $OPEN
git add -A
git commit -m "TRIAL-1: the verdict and the close"
git push -u origin trial-1-close
```

Done when `sf status --study $W` says `closed` (the close asked GitHub about both acts, with the token), the verdict is `right`, and a third pull request with this commit is merged. `sf contribution --study $W` then writes who did each step, from the logs, as a paragraph you can paste into a paper's contribution section; the finding already carries it from the moment it was attached. Write `--observed` in your own words if something else happened.

**When the verdict is not `right`.** About one trial in eight comes back inconclusive, which cannot be `right`. Close the second pull request unmerged, have the agent write the request again with `--decision declined`, merge that, and close with `--outcome system-trial-declined`. Then run a second trial beside it, as `TRIAL-2`, with new branch names. A `WRONG` verdict is a defect in the factory: raise a note before the close.

## A study of your own: the fresh data proposed

A real study differs in its plan and its fresh data. The analysis agent writes the plan from `factory/templates/analysis-plan.yaml`, with your method. Before the first test it proposes the fresh data from metadata only, with the skill `propose-fresh-data`:

```
uv run tools/fresh_data.py propose --metadata YOUR-METADATA.yaml --kind later-period --from 2025-01-01 \
  --what "WHICH DATA" --why "WHY IT SUITS THE QUESTION" --unfair "WHAT WOULD MAKE IT UNFAIR" \
  --by agent:analysis --model $M --out studies/STUDY-1-fresh-data.yaml --studies studies
```

and the plan names it under `data.held_out` as `fresh_data: ../STUDY-1-fresh-data.yaml`. A study that came from an exploration names the copy in its hand-over instead ([FIRST-EXPLORATION.md](FIRST-EXPLORATION.md)). The other kinds are `--kind next-release --release NAME`, `--kind another-site --sites A,B` and `--kind random --fraction 0.2`; for a random set aside the tool draws nothing yet: the opening draws the members from the lock's merge commit. The next release is proposed before the study starts and given to the start with the data as it stands, `sf start ... --fresh-data studies/STUDY-1-fresh-data.yaml --working-data <the file>`, so the cut-off and the file's checksum are bound from the first event; a study from a hand-over takes both from the exploration's start. The opening then refuses a working file changed since the lock, says `waiting` with the cut-off and the periods the plan needs until the release can be out, and does not analyse fresh data with any date on or before the cut-off. Rehearse the fetch so that it keeps only the release's own rows: an opening refused for an old date is used up. At the lock, the evidence summary shows the proposal in words under "The fresh data that will check the idea, and why it was chosen", with a random draw said to be made at the opening, and approving the pull request approves that choice. The review agent checks the choice is fair before you are asked.
