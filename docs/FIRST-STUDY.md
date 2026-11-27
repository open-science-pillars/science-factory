# Your first confirming study

A confirming study tests one claim, stated in advance, once, on fresh data. Make your first the **system trial**: every stage, both acts as real GitHub pull requests, on a blind test case the tool seals at the opening, so nobody knows the answer until the steward has decided. It tests the factory, not the world, and needs no data of your own; the last section says what changes in a study of your own.

**What has been run.** The set-up and block 1 gave the outputs below in a scratch repository, with a local clone standing in for GitHub. Everything from the push on needs GitHub and has never been run: this page is that first run.

## What you need

- **Your own GitHub repository**, where the science lives (here `my-science`), cloned beside this one. It holds its own copy of `tools/`, `factory/`, `methods/` and the trial's plan ([CREATE-A-FACTORY.md](CREATE-A-FACTORY.md) says why).
- **The checklist done once** ([factory/harnesses/github/README.md](../factory/harnesses/github/README.md)): workflow, code owners, protected branch, `request-check` required.
- **A tracking issue** there, for the two log fingerprints.
- **A read token**: fine-grained, this repository only, read access to Contents and Pull requests, given as `GH_TOKEN` only to the commands below that carry it.
- `git`, `uv`, and bash or zsh.

## Set up, once

```
git clone https://github.com/open-science-pillars/science-factory
git clone https://github.com/OWNER/REPO my-science
cp -r science-factory/tools science-factory/factory science-factory/methods my-science/
mkdir -p my-science/examples/stand-alone
cp -r science-factory/examples/stand-alone/system-trial my-science/examples/stand-alone/
cd my-science
sed -e 's|example-org/example-studies|OWNER/REPO|' -e 's|^version: 0\.17\.0 |version: 0.17.0+local.1 |' \
  factory/factory.yaml > factory.yaml.new
mv factory.yaml.new factory/factory.yaml
uv run tools/sf.py log-change --study studies/SETUP --by human:YOUR-ID --log factory/change-log.jsonl \
  --problem "the definition names the example repository" \
  --change "repository: under both acts names OWNER/REPO, as version 0.17.0+local.1" \
  --rationale "the acts are verified on the repository where the studies live" \
  --predicted "check_factory.py says VALID"
uv run tools/check_factory.py
uv run tools/factory_update.py pin --repo . --source ../science-factory
```

Put your repository's owner/name for `OWNER/REPO` in all three places, and your id for `YOUR-ID` (the trial's plan is copied because the shipped benchmarks name it). Naming the repository changes the acts by people, so the validator wants a new version and a change-log record that names the acts; `log-change` writes it. Expect `check-factory: VALID`; the pin (`factory-pin.yaml`) names the commit you copied, so the copy can be updated later. Commit these, `studies/SETUP/` and the pin included, by a pull request before the first study.

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

`ME` is your id, typed only at the reveal in block 4. `M` is the agents' model, carried by an agent's commands only. With no agent at hand a person may type the agent's lines under its name; the log records that.

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

`fit.yaml` is the coordinating agent's fit note, from `factory/agents/coordinating/skills/note-the-fit/fit-template.yaml` (`good-fit`: the answer is exact). Expect `started TRIAL-1`, `fit note recorded`, `change recorded under ...`, `plan check: the analysis plan is complete`, `known-answer tests: pass (exit 0)` after a minute or two, `working data: pass (exit 0)`, `rehearsal opening-path: pass (exit 0)`, `note NOTE-001 recorded`, `curation list: 1 open note(s) across 1 subject(s)` and `lock request written`. Open a pull request from `trial-1` into `main`.

## 2. You: read, approve, merge. That is the lock.

Read the evidence summary the check posts (also `$W/lock-request/EVIDENCE.md`): the question, each rule with its criteria and measured rates, the fresh data (here a blind case made at the opening), what is held out and every change to it, every figure with its caption, the code by checksum, the definition and its models, the open notes. Look at each figure yourself: a table can agree with a claim a picture shows is wrong. Approve and merge; nothing is typed.

The workflow's `record` job writes the lock into the log on `main`, asks GitHub, and prints a fingerprint `SEQ:HASH`: post it on the tracking issue. `GH_TOKEN=YOUR-READ-TOKEN sf status --study $W` asks GitHub for the lock's standing (without the token it can say no more than `merge found, people not verified`); it must be `verified` before the opening.

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

For `LOCKSEQ:HASH` put the fingerprint from the tracking issue; for `OPENSEQ:HASH` the one the opening prints (post it too). The opening asks GitHub whether people approved the lock's merge, and refuses, unspent, without a token or network. It prints `held-out data opened (held-out, opening 1)` and the outcome: `supported`, `refuted` or `inconclusive`.

The analysis agent writes `$D/writeup.md` from `$W/receipts/held-out.json` only; a fresh review agent that did none of this writes `$D/verdict.md`:

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

Expect `confirmatory study, ready for the steward's signature`; open a second pull request. The sealed answer stays in `$W/sealed/`, out of both commits; only this instruction stops anyone in the workspace opening it.

## 4. You: decide, then reveal the answer

Read the outcome, the opening's figures, the write-up and the review. Here signed means "I accept this trial if the sealed answer shows the factory was right". Approving and merging is the signature; the workflow records and verifies it. Then:

```
git switch main
git pull
git switch -c trial-1-close
st verdict --study $W --by $ME --anchor $LOCK --anchor $OPEN
```

It prints the gain put in, what the factory said, and `right`, `not wrong (inconclusive)` or `WRONG`, into the log.

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

Done when `sf status --study $W` says `closed` (the close asked GitHub about both acts, with the token), the verdict is `right`, and a third pull request with this commit is merged. `sf contribution --study $W` writes who did each step as a paragraph for a paper; the finding already carries it. If something else happened, write `--observed` in your words.

**When the verdict is not `right`.** About one trial in eight is inconclusive. Close the second pull request unmerged, have the agent request again with `--decision declined`, merge that, close with `--outcome system-trial-declined`, and run `TRIAL-2` beside it with new branch names. `WRONG` is a defect in the factory: raise a note before the close.

## A study of your own: the fresh data proposed

A real study differs in its plan, written from `factory/templates/analysis-plan.yaml` with your method, and in its fresh data, which the analysis agent proposes from metadata before the first test (skill `propose-fresh-data`):

```
uv run tools/fresh_data.py propose --metadata YOUR-METADATA.yaml --kind later-period --from 2025-01-01 \
  --what "WHICH DATA" --why "WHY IT SUITS THE QUESTION" --unfair "WHAT WOULD MAKE IT UNFAIR" \
  --by agent:analysis --model $M --out studies/STUDY-1-fresh-data.yaml --studies studies
```

The plan names it under `data.held_out` as `fresh_data: ../STUDY-1-fresh-data.yaml`; a study from an exploration names the hand-over's copy ([FIRST-EXPLORATION.md](FIRST-EXPLORATION.md)) and needs the person's `worth-confirming` at the lock request, the lock and the opening. Other kinds: `--kind next-release --release NAME`, `--kind another-site --sites A,B`, `--kind random --fraction 0.2` (the tool draws nothing yet: the opening draws the members from the lock's merge commit). A next release is proposed before the start and given to it with the data as it stands, `sf start ... --fresh-data studies/STUDY-1-fresh-data.yaml --working-data <the file>`, binding the cut-off and the file's checksum from the first event (a hand-over brings both from the exploration's start). The opening then refuses a working file changed since the lock, says `waiting` with the cut-off and the periods the plan needs until the release can be out, and does not analyse data dated on or before the cut-off. Rehearse the fetch to keep only the release's own rows: an opening refused for an old date is used up. The evidence summary shows the proposal under "The fresh data that will check the idea, and why it was chosen" (a random draw is said to be made at the opening); the review agent checks it is fair first, and approving the pull request approves it.
