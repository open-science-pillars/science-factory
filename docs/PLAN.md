# Science Factory: the build plan

**Open Science Pillars (OSP), a personal project (personal hat) · 2026-11-25 · revised after three rounds of red team, and again on 2026-11-26 when the repository became the factory only. The smallest thing that is the whole thing, in two parts.**

## The plan in one sentence

Part A, the system trial, sends one study through every stage of the factory on a blind test case, with both acts by people (the lock and the steward's signature), no provider's product at stake, no network, and nothing but this repository and a repository of your own; Part B, the first real study, takes a real question to a steward-signed finding or a signed negative result, in the repository where that science lives. The worked example for Part B is a question about SWOT (the Surface Water and Ocean Topography mission) against one river gauge, which belongs to the hydrology capability of this project and not to this repository.

The first draft of this plan had only Part B and called it short. Red team showed it was neither: it needs an attested computation, a signed validity domain, the findings checker in a required check, and a thirty-day private hold under the third-party findings policy. Part A exists so the factory itself can be demonstrated, and accepted, before any of that, by anyone, with no other repository. It is the testbed checkout before the flight article arrives.

Words used below (WORDS.md has the full list): the *steward* is the person who holds a knowledge bundle and signs it; a *run receipt* is the record a run writes, with its code and inputs by checksum and every number it produced, so anyone can re-check the result without trusting whoever ran it (after this, a receipt); a *known-answer test* is synthetic data built on the real sampling with the truth put in by hand (a modeler's twin experiment); a *hard case* is a known-answer test where the idea is true or false as built and something else is also going on (drift, gross errors, autocorrelated noise); a *criterion* is a pass or fail threshold on a rate the known-answer tests measure; *opening the held-out data* is what some fields call unblinding; *power* is how often a test reaches the right firm answer when there is one to reach; an *attested computation* is one that ships with its own checker and a stored reference result (the organization calls them an attester and a golden); a *validity domain* is a signed statement of the scope in which a class of claim may be made; the *findings checker* is the organization's script that checks a finding's form and that every number in it is in a receipt; a *required check* is one a repository runs before it lets a change merge (the organization calls it a gate, which is why one deliverable is named `findings-checker-in-gate`); `reach_q` and `crid` are the names the built-in method's input keeps for a record's quality flag and its processing identifier (they come from the satellite product of the worked example). An assistant is always an AI agent, and people are named as people.

## Every component, and what represents it

| Component | Represented by | State |
|---|---|---|
| A study, and starting one | `sf.py start`, which makes a study wherever `--study` points and binds a request by checksum when given one; the system trial's plan, `examples/stand-alone/system-trial` | built; no study is kept here, and the stand-alone example starts two on every run |
| The procedure as a file | `factory/procedure.yaml`, read by `sf.py status` and `scorecard`; the lock records its checksum | built |
| Assistants | four roles (coordinating, analysis, review, curating); four task prompts below, three in Part A and one in Part B | prompts for part of the work; no prompt of its own for the review or the curating assistant; nothing is scheduled |
| Consulting shared knowledge, ending early | the plan stage's search of the bundles (a prompt, in Part B); `sf.py close` with a citation | the early exits are built and exercised in the self-test; the search is an assistant's task |
| Analysis plan | `analysis-plan.yaml`; `templates/analysis-plan.yaml`; `sf.py check-plan` (the plan check) | the system trial's plan passes the plan check, and so does the template as written (the study tool's self-test checks both) |
| The method | `methods/gain/` (`gain.py`, `confront.py`) with `methods/built-in-pairing/`, the built-in method, as prototypes; a real study's method is landed as an attested computation in its own repository (Part B) | prototype |
| Tests and the opening | `test_cases.py`, `known_answer_tests.py` (known-answer tests); working data; `sf.py rehearse`; `sf.py open-held-out`; the record of what has been opened | built; the system trial's known-answer tests, working data and rehearsal run on every run of the stand-alone example |
| Study log | `sf.py`: the log, the lock, log fingerprints, the log check | built; 175 of 175 self-tests (`uv run tools/sf.py selftest`) |
| Review | `sf.py attach`, `review`; the findings checker (Part B) | built; wiring the checker is Part B |
| Acts by people | `sf.py lock`, `void-unread`, `signature` | built; never yet used by a person. That a person made them is held by a protected branch, outside the tool |
| Notes into shared knowledge | `sf.py note`, `curation-list`, `resolve`; the curating assistant | the three commands are built; the curating assistant is a role file, and nothing schedules it |
| Process scorecard | `procedure.yaml`, `sf.py scorecard` | built; eight checks |
| Blind test of the system | `system_trial.py blind-test` | built; its result on 200 cases, with the command, below |
| Change log with predictions | `sf.py log-change`, `change-log.jsonl`, `sf.py check-log --change-log` | built; four records, two changes each with a prediction and its observed outcome, all written by the tool (the first pair from a practice run, historical, `records-2026-11`; the second pair from a scratch study that is not kept) |
| Proposing changes to the procedure | a rule in `procedure.yaml` | written as a rule; no assistant does it |
| Scheduled re-test | `scheduled_retest:` in the analysis plan | written in the plan; not automated |
| The request | `templates/request.md`, `kinds-of-question.yaml`; two worked requests in `examples/baton-rouge/`; `sf.py start --request` | binding the request by checksum is built; its fields are convention, and checking them is scheduled |
| Exploratory study | `study_kinds` in the procedure | designed, not built |
| One factory per capability | the `capability` block in `procedure.yaml`, filled in for the built-in example; a copy filled in for one discipline is in `examples/baton-rouge/capability.yaml` | declared; nothing has landed in any capability |
| Where it runs | `compute/adapter.py`, `compute/places.yaml` | contract and local place built (34 of 34 conformance checks, and the test of that test passes); scheduler, cloud and MAAP written down, not built; not yet wired into the tests or the opening |

## What is built, and what it measured

Every number in this section but those of its last paragraph is made by a command that runs today from a bare clone of this repository, with nothing beside it; README.md, under "Try it", has the commands in one place. No held-out data of any real record has been read, and neither the lock nor the steward's signature has been recorded by a person.

**The study tool.** `uv run tools/sf.py selftest` passes 175 of 175. The scenarios include the attacks from all three review rounds that a tool can refuse: an opening before the lock; after the plan, the code, a file a command names or anything Python could import beside them changed; with bytecode planted beside a locked source; past the one opening allowed; with data or a receipt put in place early; in a git tree before the lock is in a commit; from a log cut back behind its opening. A plan with a key given twice, an unknown key, no subject, or a criterion that cannot fail. A void of an opening that had read its data. A review assistant's block overridden by someone else; a finding swapped after the review or after the signature. An opening added to the log by hand whose receipt the locked rules judge otherwise. A second study opening the same window. A system trial accepted on a verdict that is not right. What it cannot refuse, it says: the four limits in README.md. A check of the fixes found three more gaps that are still there; README.md lists them. One of them was shown by red team: a hook loaded when the interpreter starts that hides itself and rewrites what the process does. The control for that one is where the opening runs.

**The blind test of the system.** Two hundred blind test cases go through the whole study tool, unattended:

```
uv run methods/gain/system_trial.py blind-test \
  --template examples/stand-alone/system-trial --n 200
```

It takes about six minutes. Of 100 cases where the idea was false, none was supported (94 refuted, 6 inconclusive). Of 100 where it was true, 82 were supported and 18 were inconclusive, none refuted. No wrong verdict. Read that with three things in mind. The false cases sit at gains of 0.90 and 1.10, twice the five percent difference that matters. Every case is a kind one, with no trouble put in. And the cases were chosen by the test harness (the script that drives the test), not sealed from it; the lock and the signature were recorded by the harness too, so this measures the study tool and the method, not people or assistants. Zero false supports in 100 still allows a true rate of up to about 3.6 percent. The evidence right at the difference that matters, and on hard cases, is in the known-answer tests (the table below), not in the blind test.

**The system trial, as far as an assistant may take it.** `uv run examples/stand-alone/run.py` starts a study on the system trial's plan in a scratch folder and takes it through the plan check, the known-answer tests, the working data and the rehearsal; `sf.py status` then reports the stage as `lock`, waiting on a person, and the run checks that the tool refuses the lock to an assistant. It reads no real record: its working data is a known-answer test case too.

**The known-answer tests of the built-in method.** 2000 synthetic records in each required setting, on an invented river:

```
uv run methods/gain/known_answer_tests.py \
  --executor methods/built-in-pairing/pair_records.py \
  --plan examples/stand-alone/system-trial/analysis-plan.yaml \
  --out /tmp/known-answers.json
```

| Known-answer tests (the criterion in parentheses) | Measured |
|---|---|
| Coverage, kind case (at least 0.90) | 0.93 |
| Coverage, worst hard case (at least 0.90) | 0.93 |
| False confirmation right at the difference that matters, worst (at most 0.05) | 0.0405 |
| False refutation right at that difference, worst (at most 0.05) | 0.0405 |
| Idea true, supported (at least 0.80) | 0.8405 |
| Idea false (gain 0.90 or 1.10), refuted (at least 0.80) | 0.9175 |
| Idea false, confirmed (at most 0.01) | 0.0 |

The same output gives the lowest rate at which a true idea is supported across the hard cases that must pass, 0.4205: a study planned on this method should expect to come back inconclusive often when the record holds gross errors its flag does not mark. The receipt written to `--out` lists the beyond-limits cases too, those the method is known not to survive.

**Historical: the practice run of a first real study.** Before the repository became the factory only, a practice run of the first real study that was planned (the worked example of Part B) was kept here, made with the hydrology capability's own pairing script on the pass times and gauge record of one real year. Its numbers are not reproduced by any check in this repository; the record is at the branch `records-2026-11`, under `studies/exhibits/`. In short: with the method as it stood before red team, the known-answer tests failed on that real sampling (one-signed faults on degraded low-stage passes cut interval coverage to 67 percent and raised false refutation right at the difference that matters to 34 percent); a quality screen written into the plan brought both back inside their criteria (coverage 0.92, false refutation 0.04); the screened working-data estimate was a gain of 1.012 with a 95 percent interval of 0.986 to 1.038 on 47 pairs, which is working data and not a result; a true gain of exactly one would have been supported 43 percent of the time at a difference that matters of three percent and 95 percent at five, in the kind case, and 49 percent in the worst hard case that must pass; and seven notes were raised for the steward, none resolved. The blind test of 200 was first made with that same script and gave the counts above, case for case.

## Part A: the system trial

This is deliverable `science-factory-system-trial`. It needs this repository and a git repository of your own, and nothing else: the plan is the one in `examples/stand-alone/system-trial`, with this repository's own method. Nothing in this study reads a real record, so its pull requests carry no statement about any provider's product. The whole run below was walked once in a scratch folder when this page was revised, with a placeholder standing in for the person, and gave the outputs it says to expect; no person has yet run it.

**What it accepts, and what it does not.** In this trial the opening runs in the workspace where the tests ran, as the same user. So an accepted system trial accepts the procedure: every stage, both acts by people, a note from raising to resolution, the scorecard, the change log, and a verdict that turned out right. It does not exercise the two controls that depend on where things run: a clean place for the opening (the fourth limit) and an analysis assistant with no route to the withheld values (the first). Neither is built.

**How often it comes back inconclusive.** The trial is accepted only when its verdict is right: the tool refuses to close it as accepted on any other verdict. An inconclusive trial exercised the procedure and did not show a right answer. It is closed as declined, and another trial is run beside it, which the tool allows. Expect that about one time in eight: in the blind test above 24 of 200 cases were inconclusive (18 of the 100 where the idea was true, 6 of the 100 where it was false), and the seal draws true and false cases in the same proportion.

### What you need

- **The layout.** One folder, `<root>`, holding two repositories side by side: `science-factory` (a clone of this repository, at a commit you write down) and `my-science` (your own repository, the one where the science lives; any name will do). The study is made in `my-science/studies/STUDY-0000`, and its plan finds the method by the `roots:` lines `../../../science-factory/methods/gain` and `../../../science-factory/methods/built-in-pairing`, which is that layout. No study is ever made inside `science-factory`.
- **The repository.** `my-science` has to be on a host where `main` is protected: a pull request and an approving review before any merge, and approvals dismissed when new commits are pushed. Every command below is typed in `<root>`; git is always `git -C my-science`, so nothing is ever staged in the factory's clone. The lock records the commit of the `science-factory` clone and whether its work tree was clean, so leave that clone alone for the length of the trial.
- **A tracking issue**, opened first, in that same repository. The two log fingerprints are posted there as comments, and so is the steward's decision.
- **A folder for drafts** outside the repository, `/tmp/STUDY-0000` below, for the write-up and the review assistant's verdict. The tool copies each into the study (`finding/`, `verdicts/`), and the copy is what it binds by checksum.
- **Tools.** `git` 2.28 or later, `uv`, bash or zsh.

**What the tool checks here, and what it cannot.** In a git work tree the opening is refused until the lock is in a commit, and the study is not ready for the steward until both posted fingerprints are passed back with `--anchor`. The tool accepts any local commit, on any branch, as the lock being committed: it cannot tell a merged commit from one that was never pushed. That the lock's commit was reviewed and merged before the opening is held by the host's branch protection and by the steward following the steps below.

### The run, as three prompts and two acts

An assistant's session is started by pasting the prompt.

```
Follow science-factory/factory/procedure.yaml for
my-science/studies/STUDY-0000, on a new branch
system-trial of my-science. Make the study's plan
from science-factory/examples/stand-alone/
system-trial as docs/PLAN.md says. Use sf.py status after every
step and do what it says is still needed.
1. sf.py selftest must pass.
2. Start the study as agent:coordinating, with the
   question exactly as the analysis plan has it. I
   am the steward and I ask it; never type a
   human: name yourself. Record the change-log
   prediction with sf.py log-change.
3. Check the plan; run the known-answer tests, the
   working-data test and the opening-path
   rehearsal as agent:analysis.
4. Raise one note on purpose with sf.py note, and
   one more for anything odd. Run sf.py
   curation-list.
5. Commit, push, open a pull request into main.
Stop there and show me status, the summary of the
known-answer tests and the pull request. Do not
lock: the lock is mine.
```

Then the steward reads the evidence, approves the pull request with an approving review, locks, posts the log fingerprint the lock prints on the tracking issue, and commits and pushes the lock as a commit of its own. That commit needs its own approving review before the pull request is merged: the approval the lock cites was given before the lock existed and cannot cover it. The second prompt, once the merge is done:

```
The lock is recorded and its commit is merged into
main. On a new branch system-trial-result from the
merged main, as the coordinating assistant: sf.py
open-held-out --study
my-science/studies/STUDY-0000, once.
Report the outcome exactly; change nothing. Post
the log fingerprint it prints on the tracking
issue. Commit everything except the study's
sealed/ folder.
Then, as the analysis assistant, draft a one-page
write-up from fields of receipts/held-out.json
only, and sf.py attach it.
Then a fresh subagent as the review assistant,
which did none of this study and reads only the
analysis plan, the receipts, the write-up, the
study log and the bundles: write a verdict file
and record it with sf.py review --verdict approve
(or block).
Then run sf.py check-log with both posted
fingerprints as --anchor and the change log as
--change-log; commit, again without sealed/; push;
open a second pull request. Stop for my decision.
Never read anything under sealed/, and do not run
system_trial.py verdict: both wait for my decision.
```

The steward writes the decision as a comment on the tracking issue and records it (`sf.py signature --decision signed` or `declined`, with the two fingerprints; for this study signed means "I accept this trial if the sealed answer shows the factory was right"). Only then does the steward reveal the sealed answer with `system_trial.py verdict`, which writes the verdict into the study log. The third prompt:

```
I have decided and the verdict is in the study log.
As the curating assistant, resolve every note with
sf.py resolve. As the coordinating assistant: run
sf.py scorecard; record what was observed with
sf.py log-change --observed; close the study with
the outcome the verdict allows; commit everything,
sealed/ included; push.
```

Done when `sf.py status` reports the stage as `closed` with all nine steps done, the verdict in the study log is `right`, the outcome is `system-trial-accepted`, and the second pull request is merged.

### The same run, command by command

Lines under "YOU" are the steward's; everything else is an assistant's. Three things have to be replaced: `human:YOU` (your own id, such as `human:jdoe`), every address that starts `https://...` (the real one), and the two fingerprints `LOCKSEQ:HASH` and `OPENSEQ:HASH` (copied from the tracking issue, where they were posted). Left as written, the tool refuses `human:YOU` and any `https://...` address given as evidence, and the log check reports that the study log does not contain such a fingerprint.

Once, to get the factory and to make the repository the study will live in (skip the `init` and `commit` lines if `my-science` is already a repository):

```
cd <root>
git clone \
  https://github.com/open-science-pillars/science-factory
git init -b main my-science
git -C my-science commit --allow-empty -m "start"
git -C my-science remote add origin \
  https://.../YOUR-REPOSITORY.git
git -C my-science push -u origin main
#   on the host: protect main, open the tracking issue
```

In every shell you use for the rest:

```
cd <root>
sf() { uv run science-factory/tools/sf.py "$@"; }
st() { uv run science-factory/methods/gain/system_trial.py "$@"; }
g()  { git -C my-science "$@"; }
T=science-factory/examples/stand-alone/system-trial
W=my-science/studies/STUDY-0000
C=my-science/factory/change-log.jsonl
D=/tmp/STUDY-0000
mkdir -p $D
ME=human:YOU
```

Two more variables, `LOCK` and `OPEN`, hold the two posted fingerprints. They are set in block 3 once the fingerprints exist, and the blocks after it set them again, because the steward may be in another shell by then.

**1. An assistant: the tests, on a branch.**

```
g switch -c system-trial
mkdir -p $W my-science/factory
sed -e 's/^study: .*/study: STUDY-0000/' \
  -e 's|\.\./\.\./\.\./methods|../../../science-factory/methods|' \
  $T/analysis-plan.yaml > $W/analysis-plan.yaml
sf start --study $W --id STUDY-0000 \
  --by agent:coordinating \
  --question "In the blind test case, is the gain \
that was put in within five percent of one?"
sf log-change --study $W --by agent:coordinating \
  --log $C \
  --problem "the factory has not run end to end \
with a person's lock and signature" \
  --change "The system trial: STUDY-0000 through \
every stage." \
  --rationale "No run has gone past the lock." \
  --predicted "A firm outcome that the sealed \
answer confirms, and every scorecard check \
passing. About one trial in eight is inconclusive."
sf check-plan --study $W
sf test known-answers --study $W --by agent:analysis
sf test working-data --study $W --by agent:analysis
sf rehearse --study $W --id opening-path \
  --by agent:analysis
sf note --study $W --by agent:analysis \
  --kind method \
  --about "the system trial: the notes path" \
  --text "Raised on purpose, so that the trial \
takes one note from raising to resolution." \
  --evidence $W/receipts/known-answers.json
sf curation-list --study $W
sf status --study $W
g add -A
g commit -m "STUDY-0000: tests and rehearsal passed"
g push -u origin system-trial
#   on the host: open pull request 1, into main
```

The `sed` line copies the system trial's plan, gives it this study's id, and points its two roots at the factory's clone beside your repository. What to expect: `started STUDY-0000`; `change recorded under ...`; `plan check: the analysis plan is complete`; `known-answer tests: pass (exit 0)` after about a minute and a half; `working data: pass (exit 0)`; `rehearsal opening-path: pass (exit 0)`; `note NOTE-001 recorded`; `curation list: 1 open note(s) across 1 subject(s)`; and `status` prints `"stage": "lock"` with `NOTE-001` under `open_notes`.

**2. YOU: read, approve, lock.** Read pull request 1, the summary the known-answer tests printed, and the status. Approve the pull request with an approving review and copy that review's address. Then, on the same branch in the same clone:

```
sf lock --study $W --by $ME \
  --evidence https://.../pull/1#pullrequestreview-N
g add -A
g commit -m "STUDY-0000: the lock"
g push
#   on the host: an approving review of this
#   commit, then merge pull request 1
```

The lock prints what it binds (the plan, the study tool and the six method files by checksum, the rule with each criterion and the rate measured beside it, one opening allowed), then `The lock: plan and code locked`, then how many openings are already on record, then a line that ends in a log fingerprint of the form `SEQ:HASH`. Post that fingerprint as a comment on the tracking issue. The commit holds one changed file, the study log: the lock event and nothing else.

**3. An assistant: the opening, the write-up, the review.** After the merge:

```
LOCK=LOCKSEQ:HASH
g switch main
g pull
g switch -c system-trial-result
sf open-held-out --study $W --by agent:coordinating
#   post the fingerprint it prints on the tracking
#   issue, then:
OPEN=OPENSEQ:HASH
g add -A -- . ':(exclude)studies/*/sealed/*'
g commit -m "STUDY-0000: the opening"
#   the analysis assistant writes $D/writeup.md,
#   from fields of receipts/held-out.json only
sf attach --study $W --by agent:analysis \
  --file $D/writeup.md
#   a fresh review assistant writes $D/verdict.md
sf review --study $W --by agent:review \
  --verdict approve --file $D/verdict.md
sf check-log --study $W \
  --anchor $LOCK --anchor $OPEN --change-log $C
g add -A -- . ':(exclude)studies/*/sealed/*'
g commit -m "STUDY-0000: the write-up and the review"
g push -u origin system-trial-result
#   on the host: open pull request 2, into main
```

What to expect: the opening prints `held-out data opened (held-out, opening 1); outcomes {'gain-equivalence': ...}` with `supported`, `refuted` or `inconclusive`, and its fingerprint; `finding attached: finding/...-writeup.md`; `review: approve`; and the log check prints `"status": "confirmatory study, ready for the steward's signature"` with empty `problems` and `remarks`. The sealed answer is in `sealed/blind_test_answer.json`, inside the study, and both commits leave that folder out: the pull request the steward reads does not hold it. Nothing but the instruction stops anyone in the workspace opening that file; see the limits under stage 4 in DESIGN.md.

**4. YOU: decide, then reveal the answer.** Read pull request 2. Write your decision as a comment on the tracking issue and copy the comment's address.

```
LOCK=LOCKSEQ:HASH
OPEN=OPENSEQ:HASH
sf signature --study $W --by $ME --decision signed \
  --evidence https://.../issues/N#issuecomment-N \
  --anchor $LOCK --anchor $OPEN
st verdict --study $W --by $ME \
  --anchor $LOCK --anchor $OPEN
```

The signature prints `the steward's signature: signed` with the finding it names by path and checksum. The verdict prints the gain that was put in, what the factory said, and `"verdict"`: `right`, `not wrong (inconclusive)` or `WRONG`; it writes that into the study log.

**5. Assistants: learn and close.** When the verdict is `right`:

```
LOCK=LOCKSEQ:HASH
OPEN=OPENSEQ:HASH
sf resolve --study $W --by agent:curating \
  --note NOTE-001 --disposition declined \
  --comment "raised on purpose; nothing to route"
sf scorecard --study $W --anchor $LOCK --anchor $OPEN
sf log-change --study $W --by agent:coordinating \
  --log $C \
  --problem "the factory has not run end to end \
with a person's lock and signature" \
  --change "The system trial: STUDY-0000 through \
every stage." \
  --rationale "No run has gone past the lock." \
  --predicted "A firm outcome that the sealed \
answer confirms, and every scorecard check \
passing. About one trial in eight is inconclusive." \
  --observed "The verdict was right and every \
scorecard check passed."
sf close --study $W --by agent:coordinating \
  --outcome system-trial-accepted \
  --anchor $LOCK --anchor $OPEN
sf status --study $W
g add -A
g commit -m "STUDY-0000: the decision and the close"
g push
#   on the host: approve and merge pull request 2
```

What to expect: `NOTE-001: declined` (a note raised for something real is resolved with `--disposition accepted` or `linked` and `--ref`, once per note); the scorecard prints eight checks, each `"pass"`; `change recorded under ...`; `closed: system-trial-accepted`; `status` prints `"stage": "closed"`. Write `--observed` in your own words if something else happened. This last commit takes `sealed/` in.

**When the verdict is not `right`.** An inconclusive outcome at the opening already tells you the verdict cannot be `right`. The tool then refuses `system-trial-accepted`. The steward records the decision as declined (again, if step 4 recorded it as signed):

```
LOCK=LOCKSEQ:HASH
OPEN=OPENSEQ:HASH
sf signature --study $W --by $ME --decision declined \
  --evidence https://.../issues/N#issuecomment-N \
  --anchor $LOCK --anchor $OPEN \
  --comment "the verdict was not right"
```

Then block 5 runs as written, with two changes: `--observed` says what happened, and the `close` line reads

```
sf close --study $W --by agent:coordinating \
  --outcome system-trial-declined
```

A verdict of `WRONG` is a defect in the factory: raise a note for it before the close, and do not start the next deliverable until it is understood. After an inconclusive verdict, and once pull request 2 is merged, run another trial beside this one as a new study:

```
g switch main
g pull
N=my-science/studies/STUDY-0002
mkdir $N
sed 's/^study: STUDY-0000/study: STUDY-0002/' \
  $W/analysis-plan.yaml > $N/analysis-plan.yaml
```

Then repeat the shell setup and blocks 1 to 5 with `STUDY-0002` wherever a line says `STUDY-0000`, with new branch names (`system-trial-2` and `system-trial-2-result`) and a new tracking issue. The tool stores each system trial's sealed case as its own subject in the record of what has been opened, so the second trial is not marked exploratory.

## Part B: the first real study

**Where this part lives.** A real study belongs in the repository where the science lives, and so does most of this part. It is kept here as the worked example of what a first real study needs beyond Part A: a question about a satellite record of river height against one river gauge, planned for the hydrology capability of this project. Nothing in this repository depends on it. Its draft plan and worked request, and the practice run that measured the numbers quoted from it, were taken out with the other records and are at the branch `records-2026-11` (under `studies/STUDY-0001` and `studies/exhibits/`); every number in this part is historical in that sense. In the long run this part belongs in the hydrology repository's own plan.

Five deliverables, in the order their dependencies allow (a sixth, `science-factory-specification`, proposes the study as a specification revision once this part has closed; two more, from the scientist review in `reviews/SCIENTISTS.md`, make the factory something a scientist can ask in their own words and fit a large pipeline into). The acceptance criteria are in `roadmap-initiative.yaml`.

| Deliverable | Repository | What it settles |
|---|---|---|
| `hydrology-gain-computation` | hydrology | the method as an attested computation; the fetch keeps the processing identifier and can fetch observation metadata alone |
| `hydrology-variability-domain` | hydrology | a signed validity domain, drafted by the seeder from sources the steward supplies, or a decision to hold findings at draft |
| `findings-checker-in-gate` | nasa-daac-knowledge | the checker runs in a required check; a rehearsal finding from the 2024 receipt passes it |
| `swot-gauge-recipe-amendment` | hydrology | the signed recipe says what its interval cannot see, and is re-signed |
| `science-factory-first-finding` | hydrology | STUDY-0001 from its request to the steward's decision |

The last one follows the procedure as Part A did, with five differences that matter.

1. It starts from a request (`examples/baton-rouge/request-1.md` shows the form), bound with `sf.py start --request`. The design has the scientist who asked approve the plan at the lock with the steward; the tool records one person's name at the lock, so until `science-factory-scientist-intake` lands, the scientist's approval is an approving review on the lock's pull request.
2. The plan stage fetches observation metadata for the plan's window alone and re-runs the known-answer tests on them.
3. Both rehearsals the plan requires must pass before the lock: the opening path (the fetch, the identifier, the receipt) and the finding's form (a rehearsal finding drafted from the 2024 receipt passes the checker). The tool refuses the lock until they have.
4. The opening and everything after it run from a fresh `git clone` of the merged lock, in a private repository, in a fresh container: never from a copy of the workspace where the method was built. It is run there by hand with `sf.py open-held-out`; nothing sends it through the job contract. The tool records, in the opening's event, the host, the user, and the commit of every repository the plan names and whether its work tree was clean. It does not record a container or lockfile digest; that is written into the pull request by hand. The known-answer tests and both rehearsals are run in that same container image before the lock, because a fresh container resolves the fetch's libraries anew.
5. The result is delivered to the product's team before any public reference.

A clean place for the opening answers the fourth limit. It does not answer the first: this study's data is public, and nothing but instruction and evidence keeps the analysis assistant from the withheld values at any point.

```
Do the plan stage for STUDY-0001 per procedure.yaml.
Search every installed bundle for findings,
validity domains, dead-ends, field-states and
gotchas bearing on a SWOT reach against a gauge;
close early if one answers the question. Fetch
OBSERVATION METADATA ONLY for the plan's window:
pass times, reach_q, crid, gauge readings. Never
request, print or save wse or wse_u: the held-out
data has not been opened. Point the known-answer
tests at that metadata, re-run them and the
working-data test, fill in the independence
statement with a source, and stop with the diff
of the analysis plan and a note per gap.
```

Two things about that prompt. It gives the analysis assistant the network and a public archive, so only the instruction stands between it and the withheld values. And it cannot be followed today: the fetch script as it stands always requests `wse` and `wse_u` and keeps no `crid`; a fetch of observation metadata alone is part of `hydrology-gain-computation` and is not built. Gauge readings are on that list because of a decision made for this plan, not in general: the gain needs both series, so the gauge alone cannot move it once every choice in the analysis is fixed (DESIGN.md, "Observation metadata is defined by a test").

**Third-party handling, in order.** Before the lock the steward decides where the private repository lives and whether the steward's own affiliations call for any review or disclosure. After the opening, public surfaces carry only that the held-out data was opened and that its result is held, plus the log fingerprint, which reveals nothing. The scientist who asked receives the result privately at once. It goes to the product's team privately for the policy's stated window (no less than thirty days), or until they opt in in writing. The finding carries the non-affiliation line and is written as an offer of help. Only then does anything reach a public branch.

## Decisions that are the steward's

**Who approves what, and under which account.** Part A needs two approving reviews on the first pull request (one on the evidence, one on the lock's commit) and one on the second. GitHub does not let the account that opened a pull request approve it. If the assistant's session pushes under the steward's own account, someone else has to give those reviews, or the assistant needs an account of its own. Decide before Part A, and write the answer on the tracking issue.

**The difference that matters.** Five percent in the draft (a statistician would call it the equivalence margin). It is what one year at this reach resolves, not a requirement anyone has stated: at five percent a true gain of one is supported 95 percent of the time in the kind case and 49 percent of the time in the worst hard case that must pass. A tighter one tied to a stated requirement would make the opening mostly inconclusive.

**The window.** The draft plan names the first full year of forward processing (2025-04-28 to 2026-04-27), because the hydrology bundle records a change of processing baseline on 2025-04-28 and a calendar 2025 window would straddle it.

**What a supported outcome is worth.** Predicted from 2024 alone, the opening returns supported more often than not and refuted almost never. That makes it temporal replication at one pair, and the interval, not the verdict, is the finding.

**The 2024 numbers in these documents.** They are statements about a named product, derived from a public fixture, and all of them are now marked historical. Whether they need the third-party handling is a judgment for the steward of the repository where the first real study is run, to be made before that study's first pull request, which commits a 2024 receipt. Part A does not touch it.

**The recipe.** What becomes of the mean-change-error score in the signed recipe: amended to say what it cannot detect, or replaced.

**The validity domain.** Which authoritative sources it rests on, or an explicit decision to hold the finding at draft.

**The study tool's home.** Decided on 2026-11-25: its own repository, with each capability's studies kept in that capability's repository; an analysis plan is treated as a record of a study, not a concept type. The second is stated so it can be overruled. Decided on 2026-11-26: this repository stands on its own and keeps no runs, so the first half is now true of the files and not only of the plan.

## What this costs

Part A has no other dependencies: the study tool is landed, and what remains is to run the system trial with a person. Its computing is minutes (the known-answer tests take about a minute and a half); the rest is the steward's reading, two pull requests and three approving reviews. Part B is real work: five deliverables in two repositories, each needing the steward at least once, followed by the thirty-day hold. The first draft called it short and the red team's maintainer showed it was not (M13 in the register). No count of sittings is given here: the reviewer's estimate was not kept. A repeat at an independent site was cut from the first study.

## Deliberately not included

The blind test of the system with assistants in the loop, and across runtimes and models. The adoption rule for changes to the procedure. More than one opening of the same data, which needs sequential statistics the tool does not have. An analysis assistant confined where it has no route to the withheld values, so for public data the barrier stays instruction and evidence through both studies. The opening as a job sent to a place, a protected CI job included: both openings are run by hand with `sf.py open-held-out`. Automation of the scheduled re-test and of proposing changes to the procedure. A repeat at an independent site. Any second real study. Each has a place in DESIGN.md and none is needed to show the loop closing once.
