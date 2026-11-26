# Science Factory: the build plan

**Open Science Pillars (OSP), a personal project (personal hat) · 2026-11-25 · revised after three rounds of red team. The smallest thing that is the whole thing, in two parts.**

## The plan in one sentence

Part A, the system trial, sends one study through every stage of the factory on a blind test case, with both acts by people (the lock and the steward's signature), no provider's product at stake and no network; Part B, the first real study, takes a question about SWOT (the Surface Water and Ocean Topography mission) against the Baton Rouge river gauge to OSP's first steward-signed finding or a signed negative result.

The first draft of this plan had only Part B and called it short. Red team showed it was neither: it needs an attested computation, a signed validity domain, the findings checker in a required check, and a thirty-day private hold under the third-party findings policy. Part A exists so the factory itself can be demonstrated, and accepted, before any of that. It is the testbed checkout before the flight article arrives.

Words used below (WORDS.md has the full list): the *steward* is the person who holds a knowledge bundle and signs it; a *run receipt* is the record a run writes, with its code and inputs by checksum and every number it produced, so anyone can re-check the result without trusting whoever ran it (after this, a receipt); a *known-answer test* is synthetic data built on the real sampling with the truth put in by hand (a modeler's twin experiment); a *hard case* is a known-answer test where the idea is true or false as built and something else is also going on (drift, gross errors, autocorrelated noise); a *criterion* is a pass or fail threshold on a rate the known-answer tests measure; *opening the held-out data* is what some fields call unblinding; *power* is how often a test reaches the right firm answer when there is one to reach; an *attested computation* is one that ships with its own checker and a stored reference result (the organization calls them an attester and a golden); a *validity domain* is a signed statement of the scope in which a class of claim may be made; the *findings checker* is the organization's script that checks a finding's form and that every number in it is in a receipt; a *required check* is one a repository runs before it lets a change merge (the organization calls it a gate, which is why one deliverable is named `findings-checker-in-gate`); `reach_q` is the product's quality flag for a reach and `crid` is its processing identifier. An assistant is always an AI agent, and people are named as people.

## Every component, and what represents it

| Component | Represented by | State |
|---|---|---|
| A study, and starting one | `studies/STUDY-0000`, `STUDY-0001`; `sf.py start`, which binds a request by checksum when given one | drafted, not started |
| The procedure as a file | `mvp/procedure.yaml`, read by `sf.py status` and `scorecard`; the lock records its checksum | built |
| Assistants | four roles (coordinating, analysis, review, curating); four task prompts below, three in Part A and one in Part B | prompts for part of the work; no prompt of its own for the review or the curating assistant; nothing is scheduled |
| Consulting shared knowledge, ending early | the plan stage's search of the bundles (a prompt, in Part B); `sf.py close` with a citation | the early exits are built and exercised in the self-test; the search is an assistant's task |
| Analysis plan | `analysis-plan.yaml`; `templates/analysis-plan.yaml`; `sf.py check-plan` (the plan check) | both drafted; both pass the plan check, and so does the template as written |
| The method | `gain.py`, `confront.py` as prototypes; to be landed as an attested computation in Part B | prototype |
| Tests and the opening | `test_cases.py`, `known_answer_tests.py` (known-answer tests); working data; `sf.py rehearse`; `sf.py open-held-out`; the record of what has been opened | built; known-answer tests and working data run here for both studies; the system trial's rehearsal run here; the first real study's two rehearsals not run |
| Study log | `sf.py`: the log, the lock, log fingerprints, the log check | built; 173 of 173 self-tests |
| Review | `sf.py attach`, `review`; the findings checker (Part B) | built; wiring the checker is Part B |
| Acts by people | `sf.py lock`, `void-unread`, `signature` | built; never yet used by a person. That a person made them is held by a protected branch, outside the tool |
| Notes into shared knowledge | `sf.py note`, `curation-list`, `resolve`; the curating assistant | the three commands are built; seven real notes are on the practice run's curation list, none resolved; the curating assistant is a role, not built |
| Process scorecard | `procedure.yaml`, `sf.py scorecard` | built; eight checks |
| Blind test of the system | `system_trial.py blind-test` | built; first run below |
| Change log with predictions | `sf.py log-change`, `change-log.jsonl`, `sf.py check-log --change-log` | built; two records, a prediction and its observed outcome, both written by the tool from the practice run |
| Proposing changes to the procedure | a rule in `procedure.yaml` | written as a rule; no assistant does it |
| Scheduled re-test | `scheduled_retest:` in the analysis plan | written in the plan; not automated |
| The request | `templates/request.md`, `kinds-of-question.yaml`; a worked request beside STUDY-0001; `sf.py start --request` | binding the request by checksum is built; its fields are convention, and checking them is scheduled |
| Exploratory study | `study_kinds` in the procedure | designed, not built |
| One factory per capability | the `capability` block in `procedure.yaml`, filled in for hydrology | declared; nothing has landed in any capability |
| Where it runs | `compute/adapter.py`, `compute/places.yaml` | contract and local place built (34 of 34 conformance checks, and the test of that test passes); scheduler, cloud and MAAP written down, not built; not yet wired into the tests or the opening |

## What is built, and what it measured

All of this ran in the build environment against the hydrology code at the commit README.md names. No held-out data was read, neither the lock nor the steward's signature was recorded, and every study log in `mvp/exhibits/` was written by assistants. Both practice runs and the change log were made again from the start on the tool as it stands after the third review round: a study log is hash-chained to its names, and each test event carries the tool's own checksum.

**The study tool.** `sf.py selftest` passes 173 of 173. The scenarios include the attacks from all three review rounds that a tool can refuse: an opening before the lock; after the plan, the code, a file a command names or anything Python could import beside them changed; with bytecode planted beside a locked source; past the one opening allowed; with data or a receipt put in place early; in a git tree before the lock is in a commit; from a log cut back behind its opening. A plan with a key given twice, an unknown key, no subject, or a criterion that cannot fail. A void of an opening that had read its data. A review assistant's block overridden by someone else; a finding swapped after the review or after the signature. An opening added to the log by hand whose receipt the locked rules judge otherwise. A second study opening the same window. A system trial accepted on a verdict that is not right. What it cannot refuse, it says: the four limits in README.md. A check of the fixes found three more gaps that are still there; README.md lists them. One of them was shown by red team: a hook loaded when the interpreter starts that hides itself and rewrites what the process does. The control for that one is where the opening runs.

**The blind test of the system.** Two hundred blind test cases went through the whole study tool, unattended (`exhibits/blind-test-200.json`). Of 100 cases where the idea was false, none was supported (94 refuted, 6 inconclusive). Of 100 where it was true, 82 were supported and 18 were inconclusive, none refuted. No wrong verdict. Read that with three things in mind. The false cases sit at gains of 0.90 and 1.10, twice the five percent difference that matters. Every case is a kind one, with no trouble put in. And the cases were chosen by the test harness (the script that drives the test), not sealed from it; the lock and the signature were recorded by the harness too, so this measures the study tool and the method, not people or assistants. Zero false supports in 100 still allows a true rate of up to about 3.6 percent. The evidence right at the difference that matters, and on hard cases, is in the known-answer tests (the table below), not in the blind test.

**The system trial.** STUDY-0000 was taken as far as an assistant may take it (`exhibits/system-trial-ready-STUDY-0000/`, 4 events): plan check, known-answer tests and working data all passing, rehearsal passed, and `sf.py status` reports the stage as `lock`, waiting on a person. It reads no real record: its working data is a known-answer test case too.

**The first real study, practice run.** STUDY-0001's practice run (`exhibits/practice-run-STUDY-0001/`, 13 events) records the inner loop working. The study is started from its request, which the tool binds by checksum. A change-log record is written with its prediction before any test. With the method as it stood before red team, the known-answer tests fail on the real 2024 pass times and gauge record: one-signed faults on degraded low-stage passes cut interval coverage to 67 percent and raised false refutation right at the difference that matters to 34 percent. That failure raises a note. The quality screen (drop passes flagged degraded or worse) is written into the plan and the tests pass. Six more notes follow, and a second change-log record says what was observed.

| Known-answer tests, 2000 synthetic datasets in each required setting (the criterion in parentheses) | Without the screen | With it |
|---|---|---|
| Coverage, worst hard case (at least 0.90) | 0.67 | 0.92 |
| False confirmation right at the difference that matters, worst (at most 0.05) | 0.09 | 0.04 |
| False refutation right at that difference, worst (at most 0.05) | 0.34 | 0.04 |
| Idea true, supported (at least 0.80) | 0.98 | 0.95 |
| Idea false (gain 0.90 or 1.10), refuted (at least 0.80) | 0.99 | 0.97 |

On the 2024 working data the screened estimate is a gain of 1.012 with a 95 percent interval of 0.986 to 1.038, on 47 pairs after three flagged passes are excluded. That is working data and is not a result.

**What the sample resolves.** The same synthetic datasets say how often a true gain of exactly one would be supported at different sizes of the difference that matters: 43 percent at three percent, 95 percent at five, and essentially always at eight or ten. The draft plan uses five percent. That 95 percent is the kind case; across the hard cases that must pass it runs from 0.49 (gross errors the product does not flag) to 0.95, and the screened 2024 record contains one such pass, so the lower end is realistic. The first draft's ten percent was an artifact of noise from one degraded pass.

**What it cannot see.** The receipt lists the method's known limits, the beyond-limits cases, each measured on 500 synthetic datasets: low-stage errors the product leaves unflagged (coverage 0.78), residual autocorrelation near 0.9 (0.90, just under the criterion), a relation that bends with stage (0.83). A finding from this method has to say so.

**Seven notes are on the practice run's curation list for the steward**, none yet resolved, three with receipts as evidence and four citing the repository files they concern: the candidate method's sensitivity to degraded passes (fixed, recorded); the signed recipe's mean-change-error interval, which is blind to gain; the missing validity domain; the confrontation not being an attested computation; the fetch not keeping the processing identifier; the findings checker running in no required check; and the method's loss of power when one unflagged gross error is present, which the second review pass found in the 2024 record.

## Part A: the system trial

This is deliverable `science-factory-system-trial`, after `science-factory-study-tool` lands the files. Nothing in this study reads a real record, so its pull requests carry no statement about any provider's product.

**What it accepts, and what it does not.** In this trial the opening runs in the workspace where the tests ran, as the same user. So an accepted system trial accepts the procedure: every stage, both acts by people, a note from raising to resolution, the scorecard, the change log, and a verdict that turned out right. It does not exercise the two controls that depend on where things run: a clean place for the opening (the fourth limit) and an analysis assistant with no route to the withheld values (the first). Neither is built.

**How often it comes back inconclusive.** The trial is accepted only when its verdict is right: the tool refuses to close it as accepted on any other verdict. An inconclusive trial exercised the procedure and did not show a right answer. It is closed as declined, and another trial is run beside it, which the tool allows. Expect that about one time in eight: in the blind test 24 of 200 cases were inconclusive (18 of the 100 where the idea was true, 6 of the 100 where it was false), and the seal draws true and false cases in the same proportion.

### What you need

- **The layout.** One folder, `<root>`, holding `science-factory` (this package) and `hydrology` (the checkout README.md names) side by side. Both analysis plans find hydrology by the `roots:` line `../../../../hydrology`, which is that layout. STUDY-0000 does not use nasa-daac-knowledge.
- **The repository.** The git repository is `<root>/science-factory`: the package is the repository's root. As delivered the package is not a git repository; the first block below makes it one. It has to be pushed to a host where `main` is protected: a pull request and an approving review before any merge, and approvals dismissed when new commits are pushed. Every command below is typed in `<root>`; git is always `git -C science-factory`, so nothing is ever staged from the hydrology checkout. If `science-factory-study-tool` lands the files anywhere but a repository's root, that deliverable has to restate this layout, the `roots:` lines of both plans and these commands, and the tests are run again.
- **A tracking issue**, opened first, in that same repository. The two log fingerprints are posted there as comments, and so is the steward's decision.
- **A folder for drafts** outside the repository, `/tmp/STUDY-0000` below, for the write-up and the review assistant's verdict. The tool copies each into the study (`finding/`, `verdicts/`), and the copy is what it binds by checksum.
- **Tools.** `git` 2.28 or later, `uv`, bash or zsh.

**What the tool checks here, and what it cannot.** In a git work tree the opening is refused until the lock is in a commit, and the study is not ready for the steward until both posted fingerprints are passed back with `--anchor`. The tool accepts any local commit, on any branch, as the lock being committed: it cannot tell a merged commit from one that was never pushed. That the lock's commit was reviewed and merged before the opening is held by the host's branch protection and by the steward following the steps below.

### The run, as three prompts and two acts

An assistant's session can be started with `/osp-session science-factory-system-trial` (the organization's session command, which lives in build-kit and is not part of this package), or by pasting the prompt.

```
Follow science-factory/mvp/procedure.yaml for
science-factory/mvp/studies/STUDY-0000, on a new
branch system-trial. Use sf.py status after every
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
science-factory/mvp/studies/STUDY-0000, once.
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

Once, to make the repository (skip the `init`, `add` and `commit` lines if the package is already in one):

```
cd <root>
git -C science-factory init -b main
git -C science-factory add -A
git -C science-factory commit -m "the package"
git -C science-factory remote add origin \
  https://.../YOUR-REPOSITORY.git
git -C science-factory push -u origin main
#   on the host: protect main, open the tracking issue
```

In every shell you use for the rest:

```
cd <root>
sf() { uv run science-factory/mvp/sf.py "$@"; }
st() { uv run science-factory/mvp/system_trial.py "$@"; }
g()  { git -C science-factory "$@"; }
W=science-factory/mvp/studies/STUDY-0000
C=science-factory/mvp/change-log.jsonl
D=/tmp/STUDY-0000
mkdir -p $D
ME=human:YOU
```

Two more variables, `LOCK` and `OPEN`, hold the two posted fingerprints. They are set in block 3 once the fingerprints exist, and the blocks after it set them again, because the steward may be in another shell by then.

**1. An assistant: the tests, on a branch.**

```
g switch -c system-trial
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
  --rationale "Every earlier run stopped at the \
lock." \
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

What to expect: `started STUDY-0000`; `plan check: the analysis plan is complete`; `known-answer tests: pass (exit 0)` after about a minute and a half; `working data: pass (exit 0)`; `rehearsal opening-path: pass (exit 0)`; `note NOTE-001 recorded`; `curation list: 1 open note(s) across 1 subject(s)`; and `status` prints `"stage": "lock"` with `NOTE-001` under `open_notes`.

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

The lock prints what it binds (the plan, nine files by checksum, the rule with each criterion and the rate measured beside it, one opening allowed), then `The lock: plan and code locked`, then how many openings are already on record, then a line that ends in a log fingerprint of the form `SEQ:HASH`. Post that fingerprint as a comment on the tracking issue. The commit holds one changed file, the study log: the lock event and nothing else.

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
g add -A -- . ':(exclude)mvp/studies/*/sealed/*'
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
g add -A -- . ':(exclude)mvp/studies/*/sealed/*'
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
  --rationale "Every earlier run stopped at the \
lock." \
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

What to expect: `NOTE-001: declined` (a note raised for something real is resolved with `--disposition accepted` or `linked` and `--ref`, once per note); the scorecard prints eight checks, each `"pass"`; `closed: system-trial-accepted`; `status` prints `"stage": "closed"`. Write `--observed` in your own words if something else happened. This last commit takes `sealed/` in.

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
N=science-factory/mvp/studies/STUDY-0002
mkdir $N
cp $W/study.md $N/
sed 's/^study: STUDY-0000/study: STUDY-0002/' \
  $W/analysis-plan.yaml > $N/analysis-plan.yaml
```

Then repeat the shell setup and blocks 1 to 5 with `STUDY-0002` wherever a line says `STUDY-0000`, with new branch names (`system-trial-2` and `system-trial-2-result`) and a new tracking issue. Change the title in the copied `study.md` by hand. The tool stores each system trial's sealed case as its own subject in the record of what has been opened, so the second trial is not marked exploratory.

## Part B: the first real study

Five deliverables, in the order their dependencies allow (a sixth, `science-factory-specification`, proposes the study as a specification revision once this part has closed; two more, from the scientist review in `reviews/SCIENTISTS.md`, make the factory something a scientist can ask in their own words and fit a large pipeline into). Each is run with `/osp-session <id>`; the acceptance criteria are in `roadmap-initiative.yaml`, which validates against the roadmap schema.

| Deliverable | Repository | What it settles |
|---|---|---|
| `hydrology-gain-computation` | hydrology | the method as an attested computation; the fetch keeps the processing identifier and can fetch observation metadata alone |
| `hydrology-variability-domain` | hydrology | a signed validity domain, drafted by the seeder from sources the steward supplies, or a decision to hold findings at draft |
| `findings-checker-in-gate` | nasa-daac-knowledge | the checker runs in a required check; a rehearsal finding from the 2024 receipt passes it |
| `swot-gauge-recipe-amendment` | hydrology | the signed recipe says what its interval cannot see, and is re-signed |
| `science-factory-first-finding` | hydrology | STUDY-0001 from its request to the steward's decision |

The last one follows the procedure as Part A did, with five differences that matter.

1. It starts from a request (`studies/STUDY-0001/request.md` is the worked example), bound with `sf.py start --request`. The design has the scientist who asked approve the plan at the lock with the steward; the tool records one person's name at the lock, so until `science-factory-scientist-intake` lands, the scientist's approval is an approving review on the lock's pull request.
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

**The 2024 numbers in these documents.** They are statements about a named product, derived from a public fixture. Whether they need the third-party handling before these documents reach a public repository is a judgment for the steward, to be made before the first real study's first pull request, which commits a 2024 receipt. Part A does not touch it.

**The recipe.** What becomes of the mean-change-error score in the signed recipe: amended to say what it cannot detect, or replaced.

**The validity domain.** Which authoritative sources it rests on, or an explicit decision to hold the finding at draft.

**The study tool's home.** Decided on 2026-11-25: its own repository, open-science-pillars/science-factory, with each capability's studies kept in that capability's repository; an analysis plan is treated as a record of a study, not a concept type. The second is stated so it can be overruled.

## What this costs

Part A is two deliverables with no other dependencies: land the study tool, run the system trial. Its computing is minutes (the known-answer tests take about a minute and a half); the rest is the steward's reading, two pull requests and three approving reviews. Part B is real work: five deliverables in two repositories, each needing the steward at least once, followed by the thirty-day hold. The first draft called it short and the red team's maintainer showed it was not (M13 in the register). No count of sittings is given here: the reviewer's estimate was not kept. A repeat at an independent site was cut from the first study.

## Deliberately not included

The blind test of the system with assistants in the loop, and across runtimes and models. The adoption rule for changes to the procedure. More than one opening of the same data, which needs sequential statistics the tool does not have. An analysis assistant confined where it has no route to the withheld values, so for public data the barrier stays instruction and evidence through both studies. The opening as a job sent to a place, a protected CI job included: both openings are run by hand with `sf.py open-held-out`. Automation of the scheduled re-test and of proposing changes to the procedure. A repeat at an independent site. Any second real study. Each has a place in DESIGN.md and none is needed to show the loop closing once.
