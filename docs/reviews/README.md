# Review and attack register

Every review and attack made of this factory, in one place: who made it, whether they were independent of the work, what they found, and what became of each finding. The detail of the earlier rounds is in the three files beside this one; the three independent attacks on the tools are set out in full below. What the factory claims as enforced today is in [WHAT-IS-ENFORCED.md](../WHAT-IS-ENFORCED.md); this page records what was tried against it.

**How to read "fixed".** Every fix below was made, and its self-test written, by one author, and checked by an attack only when a later round says so. Read "fixed" as "the attack as shown, and the author's variations on it, no longer work", not as "cannot be done". The column "Tested by" says who tested the fix.

**Labels.** Every finding has a label unique across the register. The independent attacks are `R1-01` to `R1-12`, `R2-01` to `R2-14` and `R3-01` to `R3-05`, with the attacker's own label beside each. In the detail files a finding keeps the label it was given there; to name it uniquely, put the round's prefix from the table below in front (`P1-S1` is the statistician's first finding in RED-TEAM.md; `AG-S1` is the first finding of the separate agents in AGENTS-AND-EXPLORING.md).

## The rounds

| Prefix | Round | When | Independent? | Found | Where | Tested by |
|---|---|---|---|---|---|---|
| P1 | Red team, first pass: a statistician (S1 to S11), a tester (R1 to R5), a maintainer (M1 to M15) | 2026-11-25 | yes, language models | 31 | [RED-TEAM.md](RED-TEAM.md) | P2 |
| P2 | Red team, second pass: a cold verifier (V1 to V15) | 2026-11-25 | yes | 15 | RED-TEAM.md | the author |
| SC | Three scientists' reading: how they would ask, and where it loses them | 2026-11-25 | yes | 15 objections | [SCIENTISTS.md](SCIENTISTS.md) | not attacked |
| P3 | Red team, third round, after the renames: the study tool (A1 to A20), compute (B1 to B20), the documents followed by the letter (C1 to C22) | 2026-11-25 | yes | 62 | RED-TEAM.md | P4 |
| P4 | A verifier of the third round's fixes (V1, V2 and two more) | 2026-11-25 | yes | 4 | RED-TEAM.md | the author |
| SR | The builder's self-review of the exploring and knowledge tools (A1 to A11) | 2026-11-26 | no | 11 | [AGENTS-AND-EXPLORING.md](AGENTS-AND-EXPLORING.md), section 1 | R1 |
| HY | A working hydrologist's review of a run and the tools (H1 to H14) | 2026-11-26 | yes, a person | 14 | AGENTS-AND-EXPLORING.md, section 2 | R1 |
| AG | Six separate agents, each started from its file, on a real run (S1 to S30) | 2026-11-26 | separate contexts, one model | 30 | AGENTS-AND-EXPLORING.md, section 3 | R1 |
| R1 | First independent attack on the tools | 2026-11-26 | yes | 12: 2 blockers, 5 serious, 5 minor | below; detail in AGENTS-AND-EXPLORING.md, section 4 | R2 |
| R2 | Second independent attack on the tools | 2026-11-26 | yes | 14: 2 blockers, 4 serious, 8 minor | below; section 5 | R3 |
| R3 | Third independent attack, the pull request route included | 2026-11-26 | yes | 5: 1 serious, 4 minor | below; section 7 | the author only |
| WR | The first real run, on a public monthly global temperature record, by separate agents from the role files (F1 to F19) | 2026-11-26 | separate agents, two models | 19: the most serious, a release set aside that protected nothing in the file | dispositions in [the change log](../../factory/change-log.jsonl), definition 0.14.0, parts 1 to 5 | the author only |

The review round of the documents themselves (a fresh reader's audit of every page, 159 findings) was made on 2026-11-26 and its findings were applied to the documents as they now stand; it found no fault in the tools beyond the ones R1 to R3 and the audit's own list of false statements, which are corrected.

## What is owed now

- **A fourth independent attack**, on the three standings of an act, on `sf.py verify-acts`, on the fresh-data proposal and its random draw, and on the gate on `--people-not-verified`. Nobody but their author has attacked any of these.
- **A first run on GitHub**: the workflow in `factory/harnesses/github/`, the required check, the recording job, and `verify-acts` asking GitHub itself. None has ever run there. Step 7 of that folder's checklist is that run.
- **A real model run** of the three judges in `factory/scorers/`, and of the agents under the Claude Code harness (`factory/harnesses/claude-code/`), whose per-call check has never been called by Claude Code.

Each is an issue on GitHub, labelled `owed`, once the repository's labels are made (`factory/harnesses/github/README.md`).

## R1: the first independent attack

A reviewer who had not built the tools, on a private copy, every success shown by running the tool. The self-tests named are in the file given; most carry words of the attack in their names.

| Label | Theirs | Severity | What was shown | What became of it | Test that backs it |
|---|---|---|---|---|---|
| R1-01 | T-B1 | blocker | The fence never read set-aside data named through a folder, a pattern, a tilde path or a word after `=` | Fixed: such a look is refused; a look runs in a scratch folder holding only what it names; on Linux the kernel keeps it from anything else | `explore.py selftest`: "a look that names a folder is refused", "a look that names a pattern", "a look that names a tilde path", and the checks under "N4" |
| R1-02 | T-B2 | blocker | The per-call check read a command with comment rules a shell does not have, so `X#x; review ...` reached another role's command | Fixed: any shell sign is refused outright, and one shape of command is taken | `allow.py --selftest`: "a second command hidden behind a `#`", "brackets and a semicolon are refused even inside quotes" |
| R1-03 | T-S1 | serious | A shortened `--b` got past the name check | Fixed: no parser takes a shortened option, and the check reads each tool's own parser | `allow.py --selftest`: "a shortened `--by` does not get past the name check"; `sf.py selftest`: "an option is taken only when it is spelled out" |
| R1-04 | T-S2 | serious | An exploring agent made its own review from inside a look | Fixed: the tools refuse a command started from inside a look; a reviewer is named before the lead by a name that did none of the work | `explore.py selftest`: "the knowledge tool refuses inside a look too", "a reviewer named after the lead was recorded cannot review that lead" |
| R1-05 | T-S3 | serious | The review role could read the author's account kept as flat files | Fixed: both forms of the path are refused to the review role | `allow.py --selftest`: "the review role may not read the author's account where a run keeps it as flat files" |
| R1-06 | T-S4 | serious | `check-drafts --checker` ran any file and let it say PASS | Fixed: a checker runs only when its checksum is pinned in `factory/checkers.yaml` | `knowledge.py selftest`: the checks of a checker that is not pinned |
| R1-07 | T-S5 | serious | `correct` reversed a lead's meaning after its review | Fixed: any correction after a review undoes the review | `explore.py selftest`: "a correction made after the review is taken, and says the lead must be reviewed again" |
| R1-08 | T-M1 | minor | The lead's number check was easy to slip with other spellings | Fixed for the forms the tool lists | `explore.py selftest`: "a number no look printed is refused in every form it can be written" |
| R1-09 | T-M2 | minor | `import` wrote an unsigned page over a signed one | Fixed: refused whole | `knowledge.py selftest`: the import checks |
| R1-10 | T-M3 | minor | A draft's source need not exist | Fixed for paths; an address is declared, not fetched | `knowledge.py selftest`: "a draft whose source is a path with no file there is refused" |
| R1-11 | T-M4 | minor | `recheck` missed a file a look read without naming it | Fixed: such a file is declared with `--also-reads` and pinned | `explore.py selftest`: "a recheck is refused when a file the look read without naming it has changed" |
| R1-12 | T-M5 | minor | A log rewritten with every hash right checks out alone | Partly fixed: in git, a rewrite after a commit fails the log check; finished in R3-05 | `explore.py selftest`: the committed-log checks; see R3-05 |

## R2: the second independent attack

Another reviewer, who built none of the tools and made none of R1's fixes. Of R1's twelve, eight held as fixed, two held as written but were broken by a new route (R1-01 and R1-04), and two were partly closed.

| Label | Theirs | Severity | What was shown | What became of it | Test that backs it |
|---|---|---|---|---|---|
| R2-01 | N1 | blocker | A fenced look wrote a start-up file into the launcher's cache, and it ran in later tool calls | Fixed in structure where the kernel fence holds: `uv run` builds the script's environment outside the fence, and the script cannot write it | `explore.py selftest`: four checks named "N1" |
| R2-02 | N2 | serious | A cache setting above the exploration switched the kernel fence off | Fixed: no caller's setting reaches the fence; a fence that cannot be put up is a refusal | `explore.py selftest`: "N2: on a machine with a kernel fence, a fence that cannot be put up is a refusal" |
| R2-03 | N3 | serious | Passed variables put the set-aside folder inside the fence | Fixed: a script gets an environment the tool builds | `explore.py selftest`: "N2, N3, N14" |
| R2-04 | N4 | serious | The fence knew one way to write a date | Fixed in structure: a look gets only the exploration's files and the declared working data; dates are a second line | `explore.py selftest`: the checks named "N4" |
| R2-05 | N5 | blocker | A rehearsal left a job that later recorded a lock under a person's name, and the data was opened | Fixed three ways: plan steps run fenced, the tools refuse a command with a step above it, and a real lock is a pull request | `sf.py selftest`: "a job a step leaves behind to call the lock later", "a lock typed at a command line with no word of practice is refused" |
| R2-06 | N6 | serious | The analysis role could rewrite what the plan holds out | Fixed: the held-out block goes on record when first seen, and a change needs a recorded reason the lock shows | `sf.py selftest`: the held-out record checks; `allow.py --selftest`: four checks named "N6" |
| R2-07 | N7 | minor | A review stood for words the reviewer never read | Fixed: a review names the lead it read by checksum | `explore.py selftest`: two checks named "N7" |
| R2-08 | N8 | minor | Four more ways to write an unbacked number; a planted page backed any number | Fixed | `explore.py selftest`, `allow.py --selftest`: checks named "N8" |
| R2-09 | N9 | minor | The clean-environment refusal ran after the imports | Fixed as far as a process can: every tool restarts itself in a clean Python (the study tool's restart had been pasted into its help text by mistake and did not run until the documents pass found it) | `sf.py selftest`: "the tool's help is words, not its own source", "a file named like a standard module beside the study tool is not imported by it" |
| R2-10 | N10 | minor | Leftover ways for the review role to reach the author's account | Fixed for each | `allow.py --selftest`: checks named "N10" |
| R2-11 | N11 | minor | The role file and the check disagreed about where the analysis role writes | Fixed | `allow.py --selftest`: checks named "N11" |
| R2-12 | N12 | minor | A folder or any word with a colon counted as a source | Fixed | `knowledge.py selftest`: checks named "N12" |
| R2-13 | N13 | minor | In git, the log check compared with the last commit only | Restated in R2; fixed in R3 (R3-05) | see R3-05 |
| R2-14 | N14 | minor | A name with a line break was taken; a role could type a person's name; a huge command was slow to refuse | Fixed | `sf.py selftest`, `allow.py --selftest`: checks named "N14" |

## R3: the third independent attack

A reviewer who built none of the tools and made none of the fixes, the pull request route included, with no network. Of R2's fourteen, twelve were closed or honestly restated, two lived only in the harness and were not broken again, and N13 was still open.

| Label | Theirs | Severity | What was shown | What became of it | Test that backs it |
|---|---|---|---|---|---|
| R3-01 | A3-1 | serious | On a clone, an ordinary commit and a hand-written approvals file were recorded as a real lock and signature, and the data opened | Fixed in structure: an act has three standings, and only GitHub's own answer to `verify-acts` makes one `verified`; the opening asks GitHub itself. The exception for a place with no network is now refused unless the definition allows it (`opening_without_verification`) | `sf.py selftest`: the checks named "A3-1", "the exception for a place with no network is the definition's to allow", "a definition changed after the lock to allow the exception does not open the data"; `verify_acts.py --selftest`; `record_act.py --selftest` |
| R3-02 | A3-2 | minor | A commit with one parent was accepted as the merge | Fixed: a merge has two parents; squash only where the definition allows it; rebase never | `sf.py selftest`: three checks named "A3-2" |
| R3-03 | A3-3 | minor | A file's mode, and a symlink in place of a file, were invisible to the definition's checksum | Fixed: the checksum binds the executable bit and a link as a link | `check_factory.py --selftest`, `sf.py selftest`: checks named "A3-3" |
| R3-04 | the third minor | minor | (a) The required check's fixtures had no bot and no malformed reviews; (b) a declared working folder that holds data set aside by date leans on the reading of dates | (a) Fixed. (b) Restated as an instruction in list 4 of WHAT-IS-ENFORCED | `verify_request.py --selftest`, `record_act.py --selftest`: the bot and malformed-review checks |
| R3-05 | N13 of R2 | minor | A log rewritten and committed again passed the log check | Fixed: every committed version of the log must be a beginning of it; the merged request pins the log's head | `sf.py selftest`: two checks named "N13" |

## The earlier reviews, in short

**P1 to P4 (RED-TEAM.md).** The first two passes shaped the confirming way: a rule must be able to fail at the difference that matters, the opening is rehearsed, one window has one opening, and the study tool refuses an unbound environment. The third round found that a doctored receipt, code changed after the lock, a second opening and a method that estimates nothing could each reach "ready for the steward's signature"; each was fixed with a self-test, and P4 checked the fixes and found two more. The closing sections of that file, which say names are typed and the control is an approving review, are superseded by the pull request route and the three standings.

**SC (SCIENTISTS.md).** How scientists ask, what they need asked back, the kinds of question, and why "held-out data" is the wrong first word: "Nobody in the field has an unseen record. So the honest question is exposure." That reading is why the factory now asks what you have looked at and has an agent propose the fresh data.

**SR, HY and AG (AGENTS-AND-EXPLORING.md, sections 1 to 3).** The builder's own attack on the exploring tools; a hydrologist who recomputed a run with their own code and found that it "did not think like a hydrologist"; and six separate agents who said where their files and tools got in the way. Each finding has its disposition there.
