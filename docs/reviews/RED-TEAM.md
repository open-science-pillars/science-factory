# Science Factory: red team register

*History. Its labels are read with a prefix in the register (docs/reviews/README.md): P1 for the first pass, P2 for the second, P3 for the third round and P4 for the check of its fixes. The records this document cites (practice runs, study and exploration logs, receipts, drafted pages, the demo's runs) were removed from `main` and are at the branch `records-2026-11` of this repository; every path in it is as it was on the day it was written.*

*The first two rounds of this register were written on 2026-11-25 in the package's earlier vocabulary and were put into the present words later the same day; their findings, numbers and dispositions were meant to stay as they were, and the originals are not kept in this package. The third round, at the end, was written in the present words. WORDS.md maps the earlier words to the present ones, for anyone comparing this with older material.*


The first draft of this package (a concept document and an architecture document, both now part of DESIGN.md, a build plan, now PLAN.md, and a working study tool) was given to three independent reviewers at once, each told to break it and to prove every point by running code or citing a file: a statistician attacking the method and the ladder, a tester trying to reach "ready for the steward's signature" while cheating, and a skeptical maintainer of the larger project this was then part of checking facts, doctrine and deliverability against the repositories. They returned 33 findings, 8 of them blockers. A fresh verifier then checked the revised package cold and returned 15 more, 3 of them blockers. Every blocker is fixed in the files or, where the fix is work in another repository, scheduled as a deliverable and held by a planned rehearsal that the lock requires. One is neither: a hostile interpreter environment cannot be refused from inside the process, and is recorded as a limit with its control (R1 and V2). The reviewers were language models, so this is the factory's own review stage applied to itself and carries the same caveat: advisory until a person reads it.

The single most useful finding was the maintainer's: rehearse the finding on working data before the lock, because a run receipt that cannot be cited cannot be repaired after the one opening of the held-out data is spent. (A run receipt is the record a run writes, with its code and inputs by checksum and every number it produced, so anyone can re-check the result without trusting whoever ran it; below, a receipt.) It became a step of the ladder.

## Method and ladder (the statistician)

**S1, blocker. Degraded low-stage passes steer the gain, and the first known-answer tests could not see it.** In the 2024 record one pass flagged degraded, at the year's lowest stage, carried about two thirds of the residual sum of squares; put into known-answer tests built on the real record, such passes cut coverage and inflated error rates right at the difference that matters. *Changed:* a quality screen written into the plan (passes with reach_q at or above 2 are excluded, count reported), a one-signed low-stage fault case among the required cases, and the known-answer tests recalibrated to the screened record. The failure and the fix are on the practice run's study log (that run since removed; the practice run now kept in `mvp/exhibits/` repeats it). *Remains:* low-stage errors the product does not flag are undetectable by this method; the receipt measures that (coverage 0.78) and the analysis plan lists it as a limitation.

**S2, major. The false-confirmation check sat where it could not fail.** It was measured at a gain of 0.80, far from the difference that matters, where it read zero even with a defective interval. *Changed:* false confirmation and false refutation are required to pass right at the difference that matters, on both sides, in every hard case; the power curve is in the receipt.

**S3, major. The openings allowed were counted per directory, and inconclusive had no terminal rule.** A second study with a larger difference that matters on the same window came back supported, and the log check called it ready. *Changed:* a record of what has been opened beside the studies; a later study on the same subject and an overlapping window is exploratory; the analysis plan and the procedure say inconclusive is final for its window. Selftest covers it. *Remains:* the record is a file, protected the same way the study log is, by commits; and it matches subjects by text (normalized for spacing and case), so a reworded subject slips past it. The steward is shown the record at the lock and matches by meaning.

**S4, major. The difference that matters followed what was resolvable, so the opening had little severity.** *Changed:* with the screen the sample resolves five percent, which the draft plan now uses; the receipt reports support rates at four sizes of the difference that matters; the analysis plan states that a supported outcome is temporal replication at one pair and that the interval is the finding. *Remains:* the difference that matters is still not tied to a stated requirement. That is the steward's decision and is listed as one.

**S5, major. One gain hides a relation that bends with stage.** *Changed:* the quantity estimated is stated in the plan as an average over the window's stage distribution; gains for the lower and upper half of stage are reported and used by no rule; a bending case is among the beyond-limits cases (coverage 0.83).

**S6, major. An offset step inside the window was a hard case the known-answer tests did not contain, and the fetch kept no processing identifier.** *Changed:* a processing guard declines a window with mixed identifiers; a processing-change case is required (it must be declined every time); the planned opening requires an identifier for every pass. The hydrology bundle records the baseline change on 2025-04-28, so the plan's window was moved to start there. *Remains:* the fetch does not yet keep the identifier. The opening-path rehearsal cannot pass until it does, which is the intended effect; it is a note and a Part B acceptance criterion.

**S7, major. Power depended on a quantity nobody was allowed to read.** Gauge stage carries nothing about the gain. *Changed:* gauge stage, pass times, quality flags and identifiers are observation metadata; the known-answer tests can be built on real sampling, and the draft does so on the 2024 record until the observation metadata of the plan's window is fetched.

**S8, minor. A refusal by the estimator crashed the opening.** *Changed:* written into the plan: the locked method declining to estimate is an inconclusive result, recorded with its reason. A receipt the rules cannot read is a failed run.

**S9, minor. "Cannot fail" overstated the note on the signed recipe.** The algebra and the 100 percent rate were confirmed independently; the reviewer reports the same at gains of 0.50 and 2.00 and a response only to drift far larger than the noise (those runs are the reviewer's and are not kept here). *Changed:* the documents and the note now say "blind to gain".

**S10, minor. Sites for a repeat at an independent site need constraints.** A gauge whose stage barely moves, or a flashy river with a timing error, is misread. *Changed:* the repeat at an independent site is out of the first study; the constraint is recorded in the architecture document (now part of DESIGN.md) for when it returns.

**S11, minor. Rule form, text and number of cases.** The interval rule is two one-sided tests at 0.025, correct and conservative; the text for the quantity estimated omitted the time term; by the reviewer's computation (not kept here) a coverage criterion on 300 cases passes a defective interval about a third of the time. *Changed:* the text is corrected; required settings run 2000 cases each.

## The study tool (the tester)

**R1, blocker. The execution environment was not bound: an injected Python path laundered the power evidence and flipped the result of the opening.** *Changed:* test commands run with injected Python paths and the user site removed; tests, the acts by people and the log check refuse to run while such a variable is visible; every Python file beside a bound file, and every Python file a command names, is part of the code identity, as is the study tool. Selftests cover a changed neighbour and a visible variable. *Remains:* the refusal holds only while the variable is visible. The second pass loaded a hook at interpreter start that hid it, restored it for child processes and rewrote the receipts, and reached ready (V2). Nothing inside a process survives a hostile process, and the interpreter and its installed packages are not bound. The control is where the opening runs: a clean environment that is not the analysis assistant's.

**R2, blocker. A block was overridden by a later approval.** *Changed:* a review assistant's block stands until that same review assistant approves.

**R3, major. An opening with no fetch, or a command that ignored the fetched data, reached ready.** *Changed:* a held-out test must name a fetch in the plan; an opening's receipt must name the fetched data by hash or the run has no result. *Remains:* hashing does not make the science real. That the known-answer tests are honest tests is the steward's reading at the lock and the review assistant's at review.

**R4, major. The study log had no defence against being cut short or rewritten from its first line.** *Changed:* `sf.py check-log --anchor` checks log fingerprints posted outside the workspace, and a study is not ready until the posted fingerprints for the lock and each opening are supplied and match; in a git work tree the opening is refused until the lock is committed, and a study log that is not a continuation of the committed one is invalid. Selftest covers both. *Remains:* a workspace that rewrites unpushed history and supplies its own fingerprints. Branch protection and the tracking issue are the control; the tool cannot be.

**R5 and R6, minor. Malformed study logs and analysis plans crashed; the change log could be pointed at any file.** *Changed:* malformed input is a refusal; openings allowed, thresholds, paths and tokens are checked at the plan check; the change log must be its own file.

Attacks the first draft already refused, confirmed by the tester: an opening before the lock, after the analysis plan or code changed, past the openings allowed; a test run of the held-out data; a lock by an assistant or without evidence; an edited receipt or verdict; data present before the opening; a review by an assistant that ran the work; a rule that cannot fail; locking again after an opening.

## Facts, doctrine and deliverability (the maintainer)

**M1, blocker. The claim class was outside the organization's closed vocabulary.** *Changed:* written into the plan as `variability`.

**M2, blocker. The findings checker ran in no gate, and the planned receipt could not pass it.** *Changed:* a planned finding-form rehearsal must pass before the lock; landing the method as an attested computation and wiring the checker into a gate are Part B deliverables; the architecture document (now part of DESIGN.md) no longer calls the checker a gate.

**M3, blocker. Third-party handling was out of order.** The first draft signed before delivering and treated the public repository as private. *Changed:* the opening and everything after it run in a private clone; the result is delivered before any public reference and before the steward's signature is made public; the non-affiliation line is required; whether the steward's own affiliations call for review or disclosure is a listed decision. *Remains:* these documents quote 2024 working-data numbers about a named product; whether that needs the same handling is put to the steward.

**M4, blocker. A wrong fact and an unacknowledged doctrine change.** the larger project's ingest loop already has assistants draft a concept at once and open a concept issue; the first draft said there was no channel and had working assistants never touching knowledge. *Changed:* the note is a structured record beside the ingest loop, not a replacement; the curating assistant is the reader across studies; nothing in the doctrine is reversed.

**M5, blocker. The roadmap block was invalid and used retired numbered sessions.** *Changed:* one initiative with eight deliverables (ten after the scientist review) in a roadmap file (since removed), validated against the roadmap schema; the build plan is written against deliverable ids and the larger project's session command.

**M6, major. The ablation was quoted against its own caveat.** *Changed:* quoted with the caveat: it removed concept files, not skills.

**M7, major. The plan stage had missed bundle knowledge bearing on the window.** *Changed:* see S6; the processing change is in the analysis plan with its reason.

**M8, major. The study tool could waste the only opening.** *Changed:* the lock requires every rule field to resolve as a number in the working-data receipt; planned rehearsals exercise the fetch path; an opening whose fetch failed and wrote nothing can be voided by a person on the record.

**M9, major. The acts by people were string checks.** *Changed in wording and in part in code:* the documents say recorded, not enforced; evidence must be a link; in git the lock must be a commit. Reusing the signing tool for the analysis plan would make it a concept type, which is listed as a specification question.

**M10, major. The procedure was not code.** *Changed:* `sf.py status` derives the stage from the procedure; `close`, `resolve`, `attach` and `signature` exist; the blind test of the system is built. The assistant that proposes changes to the procedure and the scheduled re-test are stated as specified, not built.

**M11, major. Subsystem interfaces were unspecified.** *Changed:* every subsystem in the architecture document (now part of DESIGN.md) has parts, interfaces and invariants; the section on the change log with predictions is expanded.

**M12, major. The curating assistant could not draft a validity domain and mishandled signed concepts.** *Changed:* the seeder drafts domains from steward-supplied sources; an amendment to a signed concept keeps it stable and owing a signature.

**M13, major. Effort was understated.** *Changed:* the build plan has two parts and adopts the reviewer's estimate for the second.

**M14, major. Overclaims.** Known-answer testing is not new to the larger project; "cannot fail" and "the blind test the field lacks" were too strong. *Changed:* stated as a generalization of the existing calibration report; the blind test of the system is described as measuring the study tool and the method.

**M15 and M16, minor. Exhibit inconsistencies and writing.** *Changed:* the exhibits were regenerated with assistants as actors and relative paths, with the prediction in the change log written before the run; terms are defined at first use; the wording gate runs clean; tables are narrower. The first practice run was kept as history and labelled (since removed).

## Second pass

A fresh verifier, which saw none of the above, was given the revised package and told to check it cold: run the README's commands as written, trace every number to a file, re-derive the known-answer receipt, attack the study tool again, check ten facts against the repositories, and walk Part A as a newcomer. What passed: the commands ran; the receipt recomputed identically; both exhibit study logs checked out (those exhibits since removed and run again), with every actor an assistant and the change record's prediction preceding the run it predicted; all ten facts held; the roadmap initiative validated; the wording gate was clean. Its verdict on whether Part A could be delivered as written was no. Fifteen findings, and what was done:

**V1, blocker. Part A's commands were missing or wrong.** *Changed:* the build plan (now PLAN.md) carries the run command by command; the whole sequence was then executed as written in a scratch git repository, including the refusal of an opening before the lock was committed, and the seal opened to a right verdict.

**V2, blocker. The claim that an injected Python path is refused was too strong.** *Changed:* stated as a tripwire and a limit in the study tool's docstring, the architecture document (now part of DESIGN.md) and R1 above; a selftest covers the visible case; the build plan runs the production opening in a clean environment.

**V3, blocker. The system trial could not be closed as its description says.** *Changed:* outcomes `system-trial-accepted` and `system-trial-declined`.

**V4, major. Unstated preconditions.** *Changed:* the build plan says to open the tracking issue first, where the checkouts sit, and to commit after the lock; "a reviewed commit" is corrected everywhere to what is true: the lock cites an approved review and is itself committed before any opening.

**V5, major. A missing checkout silently changed the code identity.** *Changed:* a path in the plan that does not exist is bound as missing, and the lock names it; the README says which checkouts each study expects.

**V6, major. A script inside the study that the code list omitted was unbound.** *Changed:* a Python file a command names is bound wherever it lives. Selftest.

**V7, major. The record of what has been opened matched by exact text.** *Changed in part:* matching survives spacing and case (selftest); the steward is shown the record at the lock. *Remains:* S3 above.

**V8, major. The system trial's seal was not a seal.** A hook in the blind test of the system could choose the case, and the answer sits in the data file. *Changed:* the verdict is void unless the case was sealed from entropy at the opening; the study's description calls it a seal by procedure.

**V9, major. Part A committed a 2024 receipt about a named product while claiming nothing was at stake.** *Changed:* the system trial's working data is now a known-answer test case with a published seed; the study reads no real record at all.

**V10, major. "Adequate power" described the kind case only.** The verifier also found that one unflagged pass carries about 70 percent of the residual sum of squares in the screened 2024 record (confirmed here). *Changed:* the build plan gives the range, 0.49 to 0.95; a seventh note is on the practice run's study log (that run since removed; the practice run now kept in `mvp/exhibits/` repeats it); a robust estimator, or an analysis plan that states its power under a gross error, is an acceptance criterion of the method deliverable.

**V11 to V15, minor.** Notes described as each having evidence when four cite files; timings and reviewer-only numbers quoted without a kept file; this section empty; the superseded practice run's human label (that run since removed) and the last deliverable unmentioned; terms undefined at first use; a rehearsal's actor allowed to review. *Changed:* each corrected in place; reviewer-only numbers are marked as such.

## A third reading, from the scientist's chair

After both passes the package was read by three more reviewers, each held to one role: a research scientist who runs a group, an applied scientist who must defend a decision, and a modeler with a large pipeline. They were not asked to break the study tool but to say how they would ask it for work and where it would lose them. Their fifteen objections and what each changes are in SCIENTISTS.md. The ones that reach back into this register: the difference that matters must have a source that is the requester's (S4, now a field in the request); "unseen" is rarely true, so exposure is declared and spatial and prospective holdouts are named (under held-out data in the concept document, now part of DESIGN.md); inconclusive needs a consequence written into the plan; exploration needs a first-class kind of study that fences data before it explores; and five scale limits in the study tool (blocking openings, whole-file hashing, environment identity, one scalar per rule, cheap known-answer tests) are confirmed against the code and scheduled, not fixed.

## What still stood after both passes

*Superseded by the pull request route and the three standings: see docs/WHAT-IS-ENFORCED.md.*

*Kept as it was written. Its first limit names a control that does not answer it, which the third round showed (B12); the section at the end of this register replaces it.*

Four limits, each with a control outside the tool: public data can be read outside the access gate (the opening runs where the analysis assistant is not, and the study log records what was present); actors are asserted (the lock cites an approved review on a protected branch); a study log can be rewritten before it is pushed (commits and posted log fingerprints); and a hostile interpreter can rewrite anything (a clean environment for the opening). Two scientific limits the receipts measure and the finding must state: errors at low stage that the product does not flag, and lost power when an unflagged gross error is present. And one honest gap: the blind test of the system measures the study tool and the method, not assistants.


## Third round, after the revision and the two renames

After the second pass the package gained the scientist's front door (the request and the kinds of question), the compute contract and "one factory per capability", and every name on disk and on the command line was changed twice. None of that had been attacked. Three independent reviewers were given the result, each told to prove every point by running code in a scratch copy: reviewer A to break the study tool; reviewer B to break the compute side and every sentence about where things run; reviewer C to read the documents cold and follow them by the letter, as a working scientist and a data steward with no one to ask. They returned 62 findings: 5 blockers, 38 major, 18 minor and one note.

The headline is in two parts. The renames introduced no regression: the earlier and the present tool agree on all 65 earlier self-test checks and on 16 scenarios run side by side, and every finding below also exists in the earlier tool. But the promise the tool exists for was not kept, before the renames or after: reviewer A reached "confirmatory study, ready for the steward's signature" with a doctored receipt, with code changed after the lock, with the held-out data opened twice and with an opening voided after it had read its data, and passed the system trial and the blind test with a method that estimates nothing.

What was done. The tool findings were fixed in code, each with a self-test check that fails on the behaviour the reviewer showed: the self-test went from 65 checks to 140, and the known-answer numbers and the blind test result did not move. The compute findings were fixed in the contract: its conformance test went from 9 checks to 34, with a test of that test. The documents were corrected and then followed by the letter in a scratch repository. Each entry below ends with what became of it: *fixed* (and how it is tested), *corrected in the documents*, *scheduled* (naming the deliverable), *stated as a limit*, or *not fixed*. The reviewers were language models, so this round carries the same caveat as the first two: advisory until a person reads it.

### The study tool (reviewer A)

**A1, blocker. With the analysis plan moved aside, the log check, the signature and the scorecard skipped every file check and called a tampered study ready.** *Fixed:* once the log holds a lock, a missing or unreadable plan is a problem and no check is skipped for want of it. Self-tests: a missing plan fails the log check, and neither the signature nor the scorecard's chain of custody passes.

**A2, blocker. A script the opening ran by a relative path was not locked, and the code identity depended on the directory the tool was called from.** A script replaced after the lock gave a supported outcome and a ready status. *Fixed:* every word of a command is read from the study directory, every existing file a command names is bound, a command that names what it runs with `-m` or `-c` fails the plan check, and the lock prints the bound files. Self-tests. A check of the fixes, made the same day by an independent verifier, found that a script named inside a shell string (`bash -lc "..."`) was still not bound (V1 below); that is fixed too.

**A3, blocker. What Python loads beside locked code was not what was hashed.** A planted bytecode file, or a new folder named like a standard module, changed the result after the lock with every checksum intact, on the shipped system trial plan. *Fixed:* commands run with every `PYTHON` variable removed and the bytecode cache pointed at a new empty folder; a bound folder's identity covers everything Python could import from it, all the way down; the tool drops its own folder from its import path; the package's `.gitignore` lists bytecode. Self-tests with a planted bytecode file, a planted package and an inherited cache folder. *Not fixed, stated as limits:* installed libraries, the interpreter and a sub-folder with no `__init__.py` are not bound; `uv` is found on `PATH`; a file swapped during a run and put back is not looked for.

**A4, major. Cutting the log back to the committed lock let the tool open the held-out data again, and a self-test claimed a refusal it never tried.** *Fixed:* the opening is refused when the log is not a continuation of the committed log, and when the record of what has been opened holds a line from this directory that the log does not own. The self-test now attempts the opening.

**A5, major. A second confirmatory opening of the same subject and window was available by reusing a directory name, through a symlinked study directory, by writing the window as text, or by misspelling `pair`.** *Fixed:* a line of the record is a study's own only by the fingerprint of its opening; a study directory reached through a symlink is refused; the plan check requires `pair` and a window of two dates; a window that cannot be read counts as overlapping. Self-tests. *Not fixed, stated as a limit:* the same plan under another parent folder still has a record of its own. The record is one file beside one set of studies, by design.

**A6, major. `void-unread` voided an opening that had read its data**, after a process killed between the fetch and the analysis, and after a fetch that wrote under another file name. *Fixed:* an opening can be voided only when it has a finished event, its fetch failed, and no file in the study was new or changed during the fetch; an opening that was started and never finished is used up. Self-tests, with one gap the check of the fixes found: no check isolates the refusal after a fetch that exited without error and wrote nothing.

**A7, major. An allowance of more than one opening was accepted without a word, and the report then showed only the last opening.** *Fixed:* an allowance above one fails the plan check. Self-test.

**A8, major. The refusal to open before the lock is committed was switched off by one environment variable, and the log's own note of it was never read.** *Fixed:* git is called with no `GIT_` variable; an opening without a committed lock is a remark in the log check and fails the new scorecard check `lock-committed`, the blind test harness apart. Self-tests.

**A9, major. The plan check passed plans that did not say what they appeared to say: a key given twice (the last one won), unknown keys, misspelled optional keys.** A second `rules` block that could not fail went through the lock. *Fixed:* a key given twice is refused, unknown keys are refused at every level, and the lock prints each rule, each criterion with its measured rate, and the openings allowed. Self-tests.

**A10, major. `--procedure` took any file, so a doctored procedure made `status` say complete and the scorecard say pass, with no trace of which procedure was used.** *Fixed in part:* the lock records the procedure's checksum; `status` and `scorecard` print the procedure's path and checksum, write them into the scorecard file, and say so when it is not the file beside the tool or not the one the lock recorded. Self-tests. *Not fixed:* a doctored procedure is labelled, not refused.

**A11, major. Nothing held the finding: it could be edited after it was attached, replaced after the review, was not named by the signature, and `close` checked nothing.** *Fixed:* a finding changed after it was attached is a problem; a verdict counts only when it follows the finding in force; the signature records the finding's path and checksum; nothing is attached after a signature; closing a study as signed runs the log check again. Self-tests.

**A12, major. The log check copied outcomes from the log and accepted events appended by hand, while three documents said the log "cannot be edited".** *Fixed:* the log check applies the locked rules to the receipt again and reports a logged outcome that differs, and every opening must have its line in the record of what has been opened. Self-tests. *Corrected in the documents:* they now say that a later edit can be detected once the log is committed and its fingerprints are posted outside the workspace. *Not fixed, stated as a limit:* events appended by hand whose outcome agrees with the receipt cannot be detected without a commit or a posted fingerprint. That is the third limit, which now says so.

**A13, major. A system trial sealed through the harness's hook was accepted by the tool; its verdict was recorded nowhere and believed whatever the data file said.** *Fixed:* no `SF_` variable reaches a command; the seal takes a chosen case only when its command carries `--harness`, where the person locking can read it; the verdict refuses unless the log checks out and the data and the answer are the ones the opening wrote, and it is written to the study log; a trial closes as accepted only on a verdict of right. Self-tests. PLAN.md and the roadmap, which said "right or not wrong", were changed to match: an inconclusive trial is closed as declined and another is run beside it.

**A14, major. The access gate handed the answer to the code under test, so a method that estimates nothing passed the known-answer tests, the system trial and the blind test.** *Fixed:* a test case is two parts; the method is given the data alone, and what was put in goes to a file the method is never passed, tied to the data by checksum. Self-tests; the honest method's numbers did not move. The check of the fixes found the known-answer runner still calling the method inside its own process (V2 below); that is fixed. *Not fixed, stated as a limit:* the sealed answer file sits inside the study, where locked code could open it by its path. Reading the code at the lock is the barrier, and PLAN.md keeps the folder out of every commit until the steward has decided.

**A15, major. A parameter file inside the study that the locked command names was not locked.** *Fixed* with A2. Self-test.

**A16, minor. A receipt path could name the study log, and the next test then deleted the log.** *Fixed:* a declared output cannot name a file the tool or people write. Self-test.

**A17, minor. `log-change` could be pointed at the record of what has been opened or at another study's log, and could leave an event with no record behind it.** *Fixed:* both are refused, the record is written before the event, and `check-log --change-log` checks every change record against the file. Self-tests.

**A18, minor. Two openings started at the same moment both passed the allowance.** *Fixed:* the allowance is decided and the opening started while the log is held. Self-test.

**A19, minor. Any change to the tool, a comment included, made the log check call every opened study invalid.** *Fixed:* after an opening a different tool is a remark that names both checksums; before an opening the refusal stays. Self-test. *Not fixed:* a study locked by an older tool cannot be re-checked when a later plan check is stricter than its plan. No such study exists.

**A20, minor. Eight smaller gaps:** commands that did not refuse an injected Python path; held-out data at a test's own data path; names compared by exact case; a review by the person who locked; an evidence link with no host; a declined signature before any opening; a scorecard listing a test the plan lacks; a lock showing only the last lines of the record. *Fixed;* self-tests cover all but the last. *Not addressed:* the reviewer's suspicion that a rehearsal could fetch the held-out window. That is the first limit.

### The compute side (reviewer B)

**B1, blocker. A bytecode file planted beside a locked source flipped a locked, committed opening, and the log check reported nothing.** *Fixed* in the tool with A3, and in the contract: a job's environment is built from a short list with a new empty bytecode cache. Conformance checks and the test of the test cover it.

**B2, major. The conformance test passed twelve deliberately wrong places, 9 of 9.** *Fixed:* 34 checks, all through the four verbs. Thirty wrong places are kept in the file, and `conformance --self-check` passes only if each fails on the checks written for its defect and every check is failed by at least one of them.

**B3, major. The conformance test could be run against no place but the local one, though three documents made it the acceptance test for the others.** *Fixed:* `conformance --place REF`, using only the four verbs and what collect brings back. *Stated as a limit:* it has only ever run against places that are child processes on one machine.

**B4, major. The contract neither enforced nor recorded most of the job spec, and its run log named an interpreter the job did not run under.** *Fixed:* the spec is checked at submit; the place records, from inside the job's environment, the program, the interpreter, the argv as started, the spec's checksum and the checksum of every file the manifest names, and does not start a job whose manifest differs. Conformance checks. *Stated as a limit:* the declared environment is carried, not checked, and only a time limit is honoured; any other resource is refused at submit.

**B5, major. "The same spec is the same job" did not keep one opening true: one named opening ran four times.** *Fixed:* a spec carries a key, the job id is derived from the key, and a different spec under a used key is refused. Conformance checks. *Stated as a limit:* a place knows only its own jobs. The study log is what limits openings to one, and it does not record jobs yet.

**B6, major. The local place kept its own records in the job's working directory and believed them.** *Fixed:* the records and the work are kept apart, the argv is never read back from disk, and outputs are hashed and kept when the job ends. Test of the test. *Not fixed, stated as a limit:* the job runs as the same user, so a job that goes looking can rewrite the records. The local place is not the place for an opening.

**B7, major. Status could not tell a dead job from a running one, and three kinds of submit left a job stuck for good.** *Fixed:* a file lock held by the job's supervisor tells them apart, a dead job is failed with its reason, and a submit that died half way leaves no job. Conformance checks and test of the test.

**B8, major. The marker rule was false as written: a job stopped after its fetch showed no marker and could be voided.** *Fixed:* the marker that decides is `fetch.started`, written by the place before the job can reach data. Conformance checks. *Stated as a limit:* at the local place nothing is held back before the command starts, so there the marker means only that the command started.

**B9, major. Cancel stopped nothing, and collecting twice gave two answers.** *Fixed:* cancel signals, waits and kills, and reports cancelled only when the job is gone; collect is refused while a job can still change. Conformance checks. *Not fixed, stated as a limit:* a process that leaves its session and drops its tag is not found by a local place without privileges.

**B10, major. Collect copied whatever path an output named (absolute, a parent folder, a symlink) and hashed after copying.** *Fixed:* an output is a regular file inside the working directory, reached without following a symlink, and the checksum is of the bytes kept. Conformance checks.

**B11, major. `places.yaml` did not map the contract it said it mapped.** *Fixed:* one table with the same twelve keys for every place, each cell a mapping or the words "open question". *Stated as a limit:* the three places other than local were written from general knowledge of such systems and were not exercised.

**B12, major. Four documents said the first limit is answered by where the opening runs; for public data it is not.** *Corrected in the documents* and in the tool's own header: where the opening runs answers the fourth limit. The first is answered only by where the analysis assistant runs, an environment with no route to the withheld values, which is not built and not planned for the first two studies.

**B13, major. Nothing enforced, checked or recorded where an opening ran, and the documents disagreed about where it should.** *Fixed in part:* every test, rehearsal and opening event records the host, the user, and the commit of each repository the plan names and whether its work tree was clean. Self-test. *Corrected in the documents:* the system trial's opening runs in the workspace, so the trial accepts the procedure and not a clean place; the first real study's runs from a fresh `git clone` of the merged lock in a fresh container, which is now in the roadmap's acceptance. *Not fixed:* the tool records no container or lockfile digest, and nothing enforces where an opening runs.

**B14, major. As designed, sending an opening through a place would not deliver the tool's guarantees.** *Corrected in the documents:* the reviewer's table is in DESIGN.md as requirements on the design, with who checks each at a place and the intended arrangement (the job at the place is the study tool itself). *Scheduled:* `science-factory-scale-adapter`. *Not built:* a way to remove a job, a bound on outputs, and steps with a check between them.

**B15, minor. The MAAP statements read as verified facts.** *Fixed* in `places.yaml` (four cells "as read", eight "open question", sixteen questions listed) and *corrected in the documents:* as read in the platform's documentation on 2026-11-25, not exercised.

**B16, minor. The scrubbed environment still carried the submitter's credentials and interpreter switches.** *Fixed:* the environment is built from a short list plus the names a spec asks for, and those names are in the run log. Conformance checks. *Not fixed:* "credentials only for the opening" is a rule and a record, not an enforcement.

**B17, minor. Several sentences read as if the tests and the system trial already ran through the contract.** *Corrected in the documents:* "will be" for "is", the two diagram arrows labelled planned, "not yet wired into the tests or the opening". *Scheduled:* running the tests at the opening's place is now a line in `science-factory-scale-adapter`.

**B18, minor. Wording, leftovers from the renames and small crashes.** *Fixed:* the crashes are refusals in words, and the scorecard check `clean-opening` is `no-failed-opening`. *Corrected in the documents:* WORDS.md's tables carry the compute names.

**B19, note. A job id is 64 bits; no verb removes a job; what a job prints stays at the place.** *Stated* in the contract's header and as a rule in `places.yaml`. No fix was asked.

**B20, minor. The two reviews were put into the present words while this round was running, and two documents still said they were kept as written.** *Corrected in the documents:* README.md, WORDS.md and both heads now say one thing: reworded later the same day, originals not kept in the package. *Not decided:* whether to restore the originals is a person's call.

### The documents, read cold and followed by the letter (reviewer C)

**C1, blocker. "One window, one opening" was switched off for any plan without a `pair` key, and no document mentioned that key.** A second study on the same data closed as a signed finding. *Fixed* with A5. Self-tests.

**C2, major. The lock's "every rule has been shown able to fail" was only as strong as the criteria the plan chose to write.** A rule with 17 percent power to refute was locked. *Fixed in part:* four criteria are required of every rule, a waiver needs a reason that the lock prints, and a criterion that cannot fail is refused. Self-tests. After the check of the fixes, the power to refute when the idea is false can no longer be waived. *Not fixed:* there is no floor under the values, and the other three criteria can be waived with a stated reason.

**C3, major. The signature did not say which finding was signed, and a finding attached after the signature closed as signed.** *Fixed* with A11.

**C4, major. A second system trial beside the first could never be accepted.** *Fixed:* a plan says `study_kind: system_trial`, the record stores each trial's sealed case as its own subject, and such a study closes only as a system trial. Self-tests.

**C5, major. Part A did not exercise what the study and the roadmap said it exercises, and one listed command was refused.** *Corrected in the documents:* Part A now raises a note on purpose, writes the curation list, resolves the note, records a change with its prediction and its outcome, and ends with a commit; the study's own page lists what the run does and what it does not.

**C6, major. The control named for "names are typed, not proven" was not in Part A's steps and was weaker than stated.** *Corrected in the documents:* the steward commits the lock as a commit of its own, that commit is merged on a protected branch with an approval of its own, and the opening runs after the merge; the documents say plainly that the tool takes any local commit. *Not fixed:* nothing in the tool can check a merge or an approval.

**C7, major. "A study log that cannot be edited afterwards" was the headline claim in three documents and two diagrams.** *Corrected in the documents* (see A12), labels included. *Not fixed:* nothing protects a log before its first commit or posted fingerprint, the logs kept as exhibits have neither, and the scorecard's chain of custody still reads pass for a log rewritten in a workspace. The procedure file now says what that pass covers.

**C8, major. The blind test headline was a rate measured at a comfortable distance on kind cases.** *Corrected in the documents:* wherever the result is quoted it says what it is (false cases at twice the difference that matters, kind cases only, chosen by the harness), and that the known-answer tests carry the evidence right at the difference that matters and on hard cases. *Not fixed:* the blind test itself still has no hard case and none right at the difference.

**C9, major. The scientist's request was not part of the record.** *Fixed:* `start --request` binds it by checksum, the lock binds it with the plan, and a change after the lock fails the log check. Self-tests. *Corrected in the documents:* what a request should contain is listed as convention, not as something held.

**C10, major. A scientist could not write an analysis plan from the templates and the documents.** *Fixed:* a commented plan template that passes the plan check as written; plan check messages that name the key and what it accepts; a catalog that says what the tool can judge and what is the scientist's to write. Self-tests.

**C11, major. An opening whose fetch downloaded the held-out data could be voided as having read nothing.** *Fixed* with A6; the plan check also requires the planned data path, or its folder, in the fetch command. *Stated as a limit:* a fetch that writes another name into that folder exits without error and so uses the opening up.

**C12, major. "Try it" and Part A could not be followed cold.** *Corrected in the documents:* README.md gives each checkout's address and commit; Part A states the layout, which directory is the repository, every commit line in full, where the two drafts go and where the tracking issue lives. *Fixed in the tool:* the documents' placeholders, and an address with no host, are refused.

**C13, major. Several things were written in the present tense, some under "What always holds", that nothing holds.** *Corrected in the documents:* each such list became "Held today" and names its holder, with the rest under convention or designed; README.md's list of what is not built is complete; the request template says the exploratory study is not built.

**C14, major. "Observation metadata" included measured values of the comparison record, stated as a general rule.** *Corrected in the documents:* the set is defined by its test, whether the independent record qualifies is decided for each plan, and it is out of the workflow adapter's general list. *Not fixed:* STUDY-0001's draft plan lists gauge stage without yet stating the condition under which it qualifies. That is to be written at the plan stage.

**C15, minor. The opening accepted the actor that ran the tests.** *Fixed.* Self-test.

**C16, minor. The change-log exhibit could no longer show that its prediction came first.** *Fixed:* both records were made again by the tool from the kept practice run, the prediction before any test, and are checked against that run's log.

**C17, minor. Twelve contradictions about who does what and what things are called.** *Corrected,* in the documents and in the procedure file.

**C18, minor. Leftover names, and a claim that no earlier word survived.** *Corrected in the documents;* the option `--anchor` is listed as a name that stays. *Not fixed:* "the method builder" stays in the two compute files and is explained in WORDS.md.

**C19, minor. Numbers that could not be traced, or that read stronger than their source.** *Corrected in the documents.* Three could not be made true by rewording and were removed: an effort estimate in sittings, "about a third", and a closing note about another program's archive. *Not fixed:* STUDY-0001's draft plan still says "at least eighty percent power", which is the kind case alone.

**C20, minor. Words that needed a gloss, glosses that disagreed, words with two senses.** *Corrected in the documents;* WORDS.md lists the words that keep more than one sense.

**C21, minor. Small tool behaviours met on the way.** *Fixed:* the status after the signature and after the close, the scorecard's list of openings, a note's words kept in the log, and every command refusing an injected Python path. Self-tests. *Not fixed:* the wording check does not scan `.jsonl` files; it is not part of this package.

**C22, minor. Two places forgot the first limit where a reader would assume protection.** *Corrected in the documents:* a paragraph under Part B's prompt and a sentence in the workflow adapter.

## What still stands after three rounds

*Superseded by the pull request route and the three standings: see docs/WHAT-IS-ENFORCED.md.*

Four limits, as the study tool states them at the top of its file. Public data can be read outside the access gate, and nothing built answers that: only an analysis assistant with no route to the withheld values would. Names are typed, not proven; the control is an approving review and a protected branch, outside the tool. A study log can be rewritten, cut short or added to by hand until it is committed and its fingerprints are posted; the control is those commits and posts. A hostile interpreter can rewrite anything; the control is a clean place for the opening, and none is built.

Left open by this round, each stated where the documents describe the protection it weakens. The required criteria have no floor under their values, and three of the four can be waived. The record of what has been opened is one file beside one set of studies, so a study under another parent folder keeps its own. A system trial's sealed answer sits inside the study, where locked code could look for it by path. A doctored procedure is labelled, not refused. Libraries and the interpreter are not bound. No container or lockfile digest is recorded. Credentials for the opening alone are a rule, not an enforcement. Nothing in the study tool calls the job contract.

Two scientific limits the receipts measure and a finding must state: errors at low stage that the product does not flag, and lost power when an unflagged gross error is present. And one honest gap, wider than first stated: the blind test of the system measures the study tool and the method on kind cases, at twice the difference that matters, not assistants.

## The check of the third round's fixes

An independent verifier, which saw none of the fixing, reran every attack of the third round against the fixed package from the reviewers' descriptions, tried to step around each fix, followed the system trial from start to close, and removed ten fixes one at a time to see whether the self-test noticed. Every blocker and every major finding about code was closed as reproduced. It found two new holes and one check that tested nothing.

**V1, blocker. A script named inside a shell string was hidden from the lock.** A command whose program was a shell bound nothing but the tool; the analysis was swapped after the lock, the opening ran it, and the log check was clean. *Fixed:* a command must be a launcher the tool knows (`{python}`, or `uv run`) followed by a script file that exists and is bound; anything else fails the plan check, and the lock prints which script each command bound. Self-tests.

**V2, major. A method that estimated nothing passed the known-answer tests.** The runner called the method in its own process, where the answer was in memory. *Fixed:* the method runs in a separate process that is given the data and nothing else, in batches; the honest method's numbers did not move. *Not fixed, stated as a limit:* a system trial's sealed answer sits inside the study, where locked code could open it by its path; reading the code at the lock is the barrier.

**A self-test that tested nothing.** The check on voiding an opening whose fetch ended normally passed with its fix removed. *Fixed*, and the other new checks were looked through for the same weakness.

**Two residuals, both taken up.** The power to refute when the idea is false can no longer be waived. The tool's own child processes now get a short list of environment variables, with any others a step needs named in the plan (`passes_environment`) and recorded by name.

The self-test stands at 173 checks after this pass. The known-answer numbers and the 200-case blind test are unchanged.
