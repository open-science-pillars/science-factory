# Review and attack register

Every review and attack made of this factory, one line per finding: its label, what it was, what became of it, and the test that backs it. What the factory claims today is [WHAT-IS-ENFORCED.md](../WHAT-IS-ENFORCED.md); this page is what was tried against it. The long round-by-round accounts are history, in [docs/history/reviews/](../history/reviews/).

**How to read "fixed".** One author made every fix and wrote its self-test. A fix was checked by an attack only where the table of rounds says so. "Fixed" means the attack as shown, and the author's variations on it, no longer work; it does not mean it cannot be done.

**Labels.** A label is the round's prefix and the label the round gave: `P1-S1` is the statistician's first finding in the first red team pass. The independent attacks are `R1-01` to `R1-12`, `R2-01` to `R2-14`, `R3-01` to `R3-05` and `R4-01` to `R4-15`, with the attacker's own label beside each. A test named as a tool is its self-test (`uv run tools/<tool> selftest`, or `--selftest` for the scripts that take it), with the checks' names in quotes where they carry the attack's words; "none named" means the round named no test, and "none" that none applies.

## The rounds

| Prefix | Round | When | Independent? | Found | Detail | Fixes tested by |
|---|---|---|---|---|---|---|
| P1 | Red team, first pass: a statistician (S), a tester (R), a maintainer (M) | 2026-11-25 | yes, language models | 31 | [RED-TEAM.md](../history/reviews/RED-TEAM.md) | P2 |
| P2 | Red team, second pass: a cold verifier (V) | 2026-11-25 | yes | 15 | RED-TEAM.md | the author |
| SC | Three scientists' reading: how they would ask, and where it loses them | 2026-11-25 | yes | 15 objections, in ten groups | [SCIENTISTS.md](../history/reviews/SCIENTISTS.md) | not attacked |
| P3 | Red team, third round, after the renames: the study tool (A), compute (B), the documents followed by the letter (C) | 2026-11-25 | yes | 62 | RED-TEAM.md | P4 |
| P4 | A verifier of the third round's fixes | 2026-11-25 | yes | 4 | RED-TEAM.md | the author |
| SR | The builder's self-review of the exploring and knowledge tools | 2026-11-26 | no | 11 | [AGENTS-AND-EXPLORING.md](../history/reviews/AGENTS-AND-EXPLORING.md), section 1 | R1 |
| HY | A working hydrologist's review of a run and the tools | 2026-11-26 | yes, a person | 14 | AGENTS-AND-EXPLORING.md, section 2 | R1 |
| AG | Six separate agents, each started from its file, on a real run | 2026-11-26 | separate contexts, one model | 30 | AGENTS-AND-EXPLORING.md, section 3 | R1 |
| R1 | First independent attack on the tools | 2026-11-26 | yes | 12: 2 blockers, 5 serious, 5 minor | AGENTS-AND-EXPLORING.md, section 4 | R2 |
| R2 | Second independent attack on the tools | 2026-11-26 | yes | 14: 2 blockers, 4 serious, 8 minor | section 5 | R3 |
| R3 | Third independent attack, the pull request route included | 2026-11-26 | yes | 5: 1 serious, 4 minor | section 7 | the author only |
| R4 | Fourth independent attack: the three standings, `verify-acts`, the random draw, the exception's gate, the release fence | 2026-11-27 | yes | 15: 2 blockers, 9 serious, 4 minor | below | the author only |
| WR | The first real run, on a public monthly global temperature record, by separate agents from the role files | 2026-11-26 | separate agents, two models | 19 | [the change log](../../factory/change-log.jsonl), definition 0.14.0, parts 1 to 5 | the author only |

A fresh reader's audit of every page (159 findings) was made on 2026-11-26 and applied to the documents as they then stood. It found no fault in the tools beyond R1 to R3 and its own list of false statements, which were corrected.

## What is owed now

- **A fifth independent attack**, on the fixes of R4: the standing asked of the platform at every point of use, the verifier in its own process at a fixed host, the refusal of bytecode and unbound files, the random set aside drawn from the lock's merge commit, the so what required of every study that comes from an exploration, and the reading of dates row by row. Nobody but their author has tested them.
- **A first run on GitHub**: the workflow in `factory/harnesses/github/`, the required check, the recording job, and `verify-acts` asking GitHub itself. None has ever run there. Step 7 of that folder's checklist is that run.
- **A real model run** of the three judges in `factory/scorers/`, and of the agents under the Claude Code harness (`factory/harnesses/claude-code/`), whose per-call check has never been called by Claude Code.

Each is an issue on GitHub, labelled `owed`, once the repository's labels are made (`factory/harnesses/github/README.md`).

## R1: the first independent attack

A reviewer who had not built the tools, on a private copy, every success shown by running the tool.

| Label | Theirs, severity | What was shown | What became of it | Test |
|---|---|---|---|---|
| R1-01 | T-B1, blocker | The fence never read set-aside data named through a folder, a pattern, a tilde path or a word after `=` | Fixed: such a look is refused; a look runs in a scratch folder holding only what it names; on Linux the kernel keeps it from anything else | `explore.py`: "a look that names a folder is refused", "a look that names a pattern", "a look that names a tilde path", the checks under "N4" |
| R1-02 | T-B2, blocker | The per-call check read comments a shell does not, so `X#x; review ...` reached another role's command | Fixed: any shell sign is refused, and one shape of command is taken | `allow.py`: "a second command hidden behind a `#`", "brackets and a semicolon are refused even inside quotes" |
| R1-03 | T-S1, serious | A shortened `--b` got past the name check | Fixed: no parser takes a shortened option; the check reads each tool's own parser | `allow.py`: "a shortened `--by` does not get past the name check"; `sf.py`: "an option is taken only when it is spelled out" |
| R1-04 | T-S2, serious | An exploring agent made its own review from inside a look | Fixed: the tools refuse a command started from inside a look; a reviewer is named before the lead by a name that did none of the work | `explore.py`: "the knowledge tool refuses inside a look too", "a reviewer named after the lead was recorded cannot review that lead" |
| R1-05 | T-S3, serious | The review role could read the author's account kept as flat files | Fixed: both forms of the path are refused to the review role | `allow.py`: "the review role may not read the author's account where a run keeps it as flat files" |
| R1-06 | T-S4, serious | `check-drafts --checker` ran any file and let it say PASS | Fixed: a checker runs only when its checksum is pinned in `factory/checkers.yaml` | `knowledge.py`: the checks of a checker that is not pinned |
| R1-07 | T-S5, serious | `correct` reversed a lead's meaning after its review | Fixed: any correction after a review undoes the review | `explore.py`: "a correction made after the review is taken, and says the lead must be reviewed again" |
| R1-08 | T-M1, minor | The lead's number check was easy to slip with other spellings | Fixed for the forms the tool lists | `explore.py`: "a number no look printed is refused in every form it can be written" |
| R1-09 | T-M2, minor | `import` wrote an unsigned page over a signed one | Fixed: refused whole | `knowledge.py`: the import checks |
| R1-10 | T-M3, minor | A draft's source need not exist | Fixed for paths; an address is declared, not fetched | `knowledge.py`: "a draft whose source is a path with no file there is refused" |
| R1-11 | T-M4, minor | `recheck` missed a file a look read without naming it | Fixed: such a file is declared with `--also-reads` and pinned | `explore.py`: "a recheck is refused when a file the look read without naming it has changed" |
| R1-12 | T-M5, minor | A log rewritten with every hash right checks out alone | Partly fixed: in git a rewrite after a commit fails the log check; finished in R3-05 | `explore.py`: the committed-log checks; see R3-05 |

## R2: the second independent attack

Another reviewer, who built none of the tools and made none of R1's fixes. Of R1's twelve, eight held as fixed, two held as written but were broken by a new route (R1-01 and R1-04), and two were partly closed.

| Label | Theirs, severity | What was shown | What became of it | Test |
|---|---|---|---|---|
| R2-01 | N1, blocker | A fenced look wrote a start-up file into the launcher's cache, and it ran in later tool calls | Fixed in structure where the kernel fence holds: `uv run` builds the script's environment outside the fence, and the script cannot write it | `explore.py`: four checks named "N1" |
| R2-02 | N2, serious | A cache setting above the exploration switched the kernel fence off | Fixed: no caller's setting reaches the fence; a fence that cannot be put up is a refusal | `explore.py`: "N2: on a machine with a kernel fence, a fence that cannot be put up is a refusal" |
| R2-03 | N3, serious | Passed variables put the set-aside folder inside the fence | Fixed: a script gets an environment the tool builds | `explore.py`: "N2, N3, N14" |
| R2-04 | N4, serious | The fence knew one way to write a date | Fixed in structure: a look gets only the exploration's files and the declared working data; dates are a second line | `explore.py`: the checks named "N4" |
| R2-05 | N5, blocker | A rehearsal left a job that later recorded a lock under a person's name, and the data was opened | Fixed three ways: plan steps run fenced, the tools refuse a command with a step above it, and a real lock is a pull request | `sf.py`: "a job a step leaves behind to call the lock later", "a lock typed at a command line with no word of practice is refused" |
| R2-06 | N6, serious | The analysis role could rewrite what the plan holds out | Fixed: the held-out block goes on record when first seen; a change needs a recorded reason the lock shows | `sf.py`: the held-out record checks; `allow.py`: four checks named "N6" |
| R2-07 | N7, minor | A review stood for words the reviewer never read | Fixed: a review names the lead it read by checksum | `explore.py`: two checks named "N7" |
| R2-08 | N8, minor | Four more ways to write an unbacked number; a planted page backed any number | Fixed | `explore.py`, `allow.py`: checks named "N8" |
| R2-09 | N9, minor | The clean-environment refusal ran after the imports | Fixed as far as a process can: every tool restarts itself in a clean Python (the study tool's restart had been pasted into its help text by mistake and did not run until the documents pass found it) | `sf.py`: "the tool's help is words, not its own source", "a file named like a standard module beside the study tool is not imported by it" |
| R2-10 | N10, minor | Leftover ways for the review role to reach the author's account | Fixed for each | `allow.py`: checks named "N10" |
| R2-11 | N11, minor | The role file and the check disagreed on where the analysis role writes | Fixed | `allow.py`: checks named "N11" |
| R2-12 | N12, minor | A folder or any word with a colon counted as a source | Fixed | `knowledge.py`: checks named "N12" |
| R2-13 | N13, minor | In git, the log check compared with the last commit only | Restated in R2; fixed in R3 (R3-05) | see R3-05 |
| R2-14 | N14, minor | A name with a line break was taken; a role could type a person's name; a huge command was slow to refuse | Fixed | `sf.py`, `allow.py`: checks named "N14" |

## R3: the third independent attack

A reviewer who built none of the tools and made none of the fixes, the pull request route included, with no network. Of R2's fourteen, twelve were closed or honestly restated, two lived only in the harness and were not broken again, and N13 was still open.

| Label | Theirs, severity | What was shown | What became of it | Test |
|---|---|---|---|---|
| R3-01 | A3-1, serious | On a clone, an ordinary commit and a hand-written approvals file were recorded as a real lock and signature, and the data opened | Fixed in structure: an act has three standings, and only GitHub's own answer makes one `verified` (asked at every point of use since R4-01). Opening with no network is refused unless the definition allows it (`opening_without_verification`) | `sf.py`: the checks named "A3-1", "the exception for a place with no network is the definition's to allow", "a definition changed after the lock to allow the exception does not open the data"; `verify_acts.py`; `record_act.py` |
| R3-02 | A3-2, minor | A commit with one parent was accepted as the merge | Fixed: a merge has two parents; squash only where the definition allows it; rebase never | `sf.py`: three checks named "A3-2" |
| R3-03 | A3-3, minor | A file's mode, and a symlink in place of a file, were invisible to the definition's checksum | Fixed: the checksum binds the executable bit and a link as a link | `check_factory.py`, `sf.py`: checks named "A3-3" |
| R3-04 | the third minor | (a) The required check's fixtures had no bot and no malformed reviews; (b) a declared working folder that holds data set aside by date leans on the reading of dates | (a) Fixed. (b) Not closed by a tool: restated as an instruction in list 4 of WHAT-IS-ENFORCED | `verify_request.py`, `record_act.py`: the bot and malformed-review checks |
| R3-05 | N13 of R2, minor | A log rewritten and committed again passed the log check | Fixed: every committed version of the log must be a beginning of it; the merged request pins the log's head | `sf.py`: two checks named "N13" |

## R4: the fourth independent attack

A red-team agent that built none of the tools and made none of the earlier fixes, on a plain copy of definition 0.15.0, with no network and no token: a hand-made log entry, planted bytecode, and a stand-in for GitHub on the loopback address. Its lesson: anything written on this machine can be written by an agent sharing the account, the tool's own record that GitHub said yes included. So from definition 0.16.0 no standing comes from the log. These fixes are tested by their author only.

| Label | Theirs, severity | What was shown | What became of it | Test |
|---|---|---|---|---|
| R4-01 | A4-01, blocker | A verification appended to the log by hand made the signature `verified`, the finding SIGNED and the close `finding-signed` | Fixed: the platform is asked wherever a standing decides or is shown; a recorded verification is a note, shown as "verified when last checked; not re-checked now" | `sf.py`: "A4-01" (two checks) |
| R4-02 | A4-02, blocker | Bytecode planted beside the verifier or the validator opened the data with no token, and after the definition was edited to allow the exception | Fixed: every tool runs in a Python that reads no bytecode and loads its neighbours from source; the checksum binds bytecode, the validator refuses it, the lock binds `tools/`, and bytecode or an unbound file is refused at the lock and the opening | `sf.py`: "A4-02" (three checks); `check_factory.py`: "A4-02" (two checks) |
| R4-03 | A4-03, serious | `HTTPS_PROXY` and `SSL_CERT_FILE` sent the verification to a loopback stand-in, and a call replaced in the process opened the data, with nothing shown | Fixed: the verifier runs in its own process with the token alone, at api.github.com only, no proxy unless the definition names one, the system's certificates; the answer records host, proxy and certificates; a stand-in is marked and counts only in self-tests | `verify_acts.py` and `sf.py`: "A4-03" (eight checks) |
| R4-04 | A4-04, serious | A so what recorded from a hand-written comment, then a hand-written verification, read `verified` at the hand-over and the lock | Fixed: the so what's standing is asked of the platform where it is used; the hand-over refuses a comment the platform does not confirm, except in practice, which it marks | `explore.py`: "A4-04" (two checks) |
| R4-05 | A4-05, serious | A study started without the hand-over, naming the exploration's proposal after a person said not-interesting, locked and opened | Fixed: a study that comes from an exploration by its hand-over, its proposal or its data needs a worth-confirming the platform confirms (practice excepted, and marked), at the lock request, the lock and the opening | `explore.py`: "A4-05" (two checks), and the hand-over check after "check-study waits for the plan" |
| R4-06 | A4-06, serious | The members of a random set aside were chosen by redrawing or by searching seeds | Fixed: a proposal draws nothing; the opening draws once from the merge commit the platform confirms; a seed handed in is refused; a practice draw is marked as one that could be chosen | `fresh_data.py`, `sf.py`, `explore.py`: "A4-06" (ten checks) |
| R4-07 | A4-07, serious | Six date forms passed the release fence, and a promoted method kept the release's rows as cases | Fixed: one reader of dates, row by row, over those forms and eleven more; a row it cannot date is refused; promotion leaves out looks on data that is not working data as it stood | `explore.py`: "A4-07" (three checks) |
| R4-08 | A4-08, serious | An opening analysed fresh data with seven rows from before the cut-off | Fixed: the opening reads the fetched rows the same way, refuses an early or undated row, and takes a timestamp at whichever of its own day and its UTC day counts against it | `sf.py`: "A4-08" (three checks) |
| R4-09 | A4-09, serious | A second exploration of the subject explored past the cut-off, with no working window or with a record of its own | Fixed: another exploration's cut-off is applied to the working files themselves, by subject or by file, and a record other than the workspace's is refused | `explore.py`: "A4-09" |
| R4-10 | A4-10, serious | A confirming study's own step read the release before the lock | Fixed: a step is refused when a file the plan binds, other than a Python script, holds a date past a cut-off, or when the working data changed | `sf.py`: "A4-10" |
| R4-11 | A4-11, serious | One word in `factory.yaml` allowed the exception, shown at the lock only as a checksum, and an agent used it | Fixed: a change to the acts by people needs a record of the change log naming them, under a version no other acts were recorded under; the lock request says the exception in capitals; an agent's `--people-not-verified` is refused | `check_factory.py`: "A4-11" (two checks); `sf.py`: "A4-11" (three checks) |
| R4-12 | A4-12, minor | A judging packet's log named absolute paths | Fixed: paths of the machine in a packet's logs are replaced, and the packet says how many | `scorers.py`: "A4-12" |
| R4-13 | A4-13, minor | `TZ` decided whether the last period had ended | Fixed: the date is the UTC date | `sf.py`: "A4-13" |
| R4-14 | A4-14, minor | A study from a release exploration always came out exploratory | Fixed: an exploration that set a release aside explored the data up to the cut-off, also as 0.15.0 wrote its line | `explore.py`: "A4-14" (two checks) |
| R4-15 | A4-15, minor | The contribution statement credited names from a hand-written file as accounts that approved | Fixed: names handed to the tool are shown as handed, with their standing; only an answer asked now names a person as confirmed | `sf.py`: "A4-15" |

## WR: the first real run

Separate agents from the role files, on a public monthly global temperature record. The change log records the findings in five parts, each with its prediction and what it did.

| Label | What it was | What became of it | Test |
|---|---|---|---|
| WR-F1 | The most serious: a release set aside protected nothing in the file it would arrive in | Fixed: a next-release proposal fixes the cut-off; the start binds the working files and refuses a later date; a look past the cut-off is refused | `explore.py`, `fresh_data.py`: the release and cut-off checks |
| WR-F2 to F4, F17 | The metadata form could not describe one long series released monthly | Fixed: `fresh_data.py describe` writes it from the date column, with cadence and checksums; the skill has a worked example | `fresh_data.py` |
| WR-F5 to F12 | Tool faults: a template its own tool refused, flags and refusals on fixed expressions, a question form too narrow, an empty uv setting that broke uv | Fixed, each; uv itself still refuses an empty setting when it is the first program started | `sf.py`, `explore.py`, `record_act.py`, `verify_request.py`; the stand-alone example with the setting set empty |
| WR-F13 to F16 | Role files and skills that disagreed with the work the run had to do | Fixed: who writes what at intake, the reviewer's place, `recheck --variant`, the fit note's timing, a search that lists nothing when nothing applies | `render.py`, `allow.py`, `knowledge.py`, `explore.py` |
| WR-F18, F19 | A lead too long to read before the so what; plan numbers whose checking was unsettled | Fixed: a summary of under 150 words, checked; a plan sentence that names a look quotes it | `explore.py` |
| WR-0.15 | Found after the run: a confirming study did not carry the release's cut-off | Fixed in definition 0.15.0: the study binds it from the start, the lock says it, the opening refuses data on or before it (WHAT-IS-ENFORCED row 1.31) | `sf.py`, `explore.py`, `fresh_data.py`: the cut-off checks |

## SR: the builder's self-review (not independent)

| Label | What it was | What became of it | Test |
|---|---|---|---|
| SR-A1 (blocker) | A look could run the study tool | Fixed: the tools refuse a command started from inside a look (after R1-04) | `explore.py` |
| SR-A2 (blocker) | A second exploration could explore what the first set aside | Fixed: `start` refuses a working window in another exploration's set-aside | `explore.py` |
| SR-A3 | Data with its times under an undeclared key crossed the fence | Fixed for dates in rows; since R4-07 every row is read, and a number in a column not named like a time is not read as a date | `explore.py` |
| SR-A4 | A lead could quote any number | Fixed: a decimal in a lead must be printed by a cited look | `explore.py` |
| SR-A5 | A draft could carry a signature under another spelling | Fixed: any key with "verif" or "sign", and `Signed-by:`, refused | `knowledge.py` |
| SR-A6 | The knowledge search drowned the pages that mattered | Fixed: two shared words, a score near the best, pitfalls always listed | none named |
| SR-A7 | In a three-page wiki every word was generic | Fixed | the stand-alone example, which found it |
| SR-A8 | The role check blocked brackets in a quoted reason | Changed later: R1-02 refuses them outright | `allow.py` |
| SR-A9 (limit) | A lead can be attached to a study as its finding | Stated; `explore.py check-study` refuses it when run, nothing at the attach | none named |
| SR-A10 (limit) | A reviewer is a name | Stated; narrowed by R1-04; one author typing two names in order is not stopped | see R1-04 |
| SR-A11 (limit) | The subject is matched by its text | Stated | none |

## HY: the hydrologist's review

The run reviewed is not rewritten; `examples/baton-rouge/README.md` says what it got wrong.

| Label | What it was | What became of it | Test |
|---|---|---|---|
| HY-H1 | The gain above one is probably geometry (surface slope), and nobody looked | The skill says to plot the residual against every field first; found independently by the second run's reviewer | none (instruction) |
| HY-H2 | The time term was an unrecorded choice | The skills say a model's form is a choice; the lead shows when each was written down | none named |
| HY-H3 | "Unflagged" passes were all flagged suspect | A lead saying "unflagged" is refused; `describe_record.py` counts flag values | `explore.py`, `describe_record.py` |
| HY-H4 | A regression gain with a five percent band is a weak test | The write-up skill asks whether a rule can fail or be met by discarding data; the error percentile is still open | none |
| HY-H5 | A drafted page credited the flag for one pass's effect | Left as drafted and unsigned; the fair yardstick is open, for the steward | none |
| HY-H6 | The fence let a site through under its agency-less number | Fixed: a site is matched in every form people write it | `explore.py`: eight checks |
| HY-H7 | Exploring had no pictures | Fixed: figures are logged by checksum; `plot_xy.py` ships | `explore.py`, `plot_xy.py` |
| HY-H8 | The record is a planned battery, not a mind changing | Partly: the order of looks and choices is logged and shown; what a tool cannot see is instruction | none named |
| HY-H9 | What was set aside was the second-best choice | Partly: `start` names any stretch in neither; a set-aside is never narrowed | none named |
| HY-H10 | The proposed test is not the right test; the hand-over hid that the reviewer was the author | The hand-over names who reviewed and who explored; whether gauge stage may be read before a lock is open | none named |
| HY-H11 | The drafted pages would not be signed; `generated` stamps were round times | `check-drafts` refuses a stamp later than the clock; a round past time is instruction | none named |
| HY-H12 | From the documents alone, stuck at the data (seven parts) | Five fixed or partly (request template, reading enforced, people may drive, launcher warning); finding a reach is the capability's; the network is no fault | `explore.py`; the stand-alone example |
| HY-H13 | Words a hydrologist would misread | The two that mislead are refused; WORDS.md sets the words out | `explore.py` |
| HY-H14 | Smaller points (lag-1 by index, one year is one flood wave) | No change; for whoever writes the plan | none |

## AG: what six separate agents found

| Label | What it was | What became of it | Test |
|---|---|---|---|
| AG-S1 | Role file and skill disagreed on reading before setting aside | Knowledge first, then set aside; one paragraph in both, checked | `check_roles.py`, `explore.py` |
| AG-S2 | "`lead`, then `end`" against "do not end before review" | `end` as a lead refused before review; one paragraph, checked | `check_roles.py`, `explore.py` |
| AG-S3 | Nothing kept the reviewer from the author's account | Each role has its own place; refused by the check and the launcher | `allow.py`, `run_role.py`, `check_roles.py` |
| AG-S4 | Curating resolved notes before the revised lead was reviewed | `resolve` refused until the exploration has ended | `explore.py` |
| AG-S5 | `read --concept` refused the paths `known` prints | Fixed | `explore.py` |
| AG-S6 | The number check matched substrings | Fixed: printed whole | `explore.py` |
| AG-S7 | A number from a knowledge page could not appear in a lead | Fixed: a page read backs it | `explore.py` |
| AG-S8 | A wording fix cost a lead version | `explore.py correct` | `explore.py` |
| AG-S9 | `generated.by` refused the agent's name | Each name has its place (`drafted_from.by`) | `knowledge.py` |
| AG-S10 | All choices logged after the last look | The order is recorded and shown | `explore.py` |
| AG-S11 | The count is of looks, not comparisons | `comparisons: N` is logged and added up; declaring is instruction | `explore.py` |
| AG-S12 | uv's warning in every receipt | Standard error kept apart | `explore.py` |
| AG-S13 | Where to write was unclear | `review/` and `figures/` made; `writes` gives each role its place | none named |
| AG-S14 | The example's page leaked an earlier answer | Partly: the page tells an agent to stop; nothing enforces it | none |
| AG-S15 | `may_call` did not list scripts run through a look | The role file says a look's script is the look's | none |
| AG-S16 | `--subject`, paths and set-aside dates needed guessing | The help and the skill say each | none |
| AG-S17 | The lead template had nowhere for what does not hold | Optional keys added | `explore.py` |
| AG-S18 | No place for "skimmed" | `read --depth skimmed` | `explore.py` |
| AG-S19 | Two spellings of one knowledge path | `read` records the path as given | none |
| AG-S20 | When should a reviewer raise a note? | Said in the role file and skill | none |
| AG-S21 | No check that a footnote's source supports it | Partly: unused and unknown footnotes refused; support is for people | `knowledge.py` |
| AG-S22 | A stale signed page has no route | Not changed: link it and tell the steward | none |
| AG-S23 | `linked` had no form for `--ref` | The help says | none |
| AG-S24 | The search ranks by shared words | Not changed; the skill says so | none |
| AG-S25 | `recheck` cannot see runs outside the log | Not fixable by a tool; instruction | none |
| AG-S26 | The overlap check cannot tell `narrows` from `contradicts` | Not changed; a stated limit | none |
| AG-S27 | Bundle sources resolve only after a merge | The skill says to give path and checksum | none |
| AG-S28 | Residual scatter came out two ways | Not changed; the lead says which | none |
| AG-S29 | Two skill lines pulled against each other | One removed | none |
| AG-S30 | The lead check skips whole numbers and ratios | Said in help and skill; not widened | none |

## P1: the red team's first pass

Dispositions of P1 to P4 and SC are as recorded on 2026-11-25. The files and plans they name (`mvp/`, DESIGN.md, PLAN.md, Part A and Part B) are at the branch `records-2026-11`.

| Label | What it was | What became of it | Test |
|---|---|---|---|
| P1-S1 (blocker) | Degraded low-stage passes steered the gain, unseen by the known-answer tests | A quality screen and a low-stage fault case; unflagged low-stage errors stay undetectable and are stated | the practice run |
| P1-S2 | The false-confirmation check sat where it could not fail | Required right at the difference that matters, both sides | none named |
| P1-S3 | Openings counted per folder; inconclusive not final | A record of openings beside the studies; matching by text remains | `sf.py` |
| P1-S4 | The difference that matters followed what was resolvable | Reported at four sizes; not tied to a requirement (the steward's) | none |
| P1-S5 | One gain hides a relation that bends with stage | Stated as an average; a bending case added | none |
| P1-S6 | An offset step was missing; no processing identifier kept | A processing guard and case; the fetch did not yet keep it | none |
| P1-S7 | Power depended on a quantity nobody could read | Observation metadata defined | none |
| P1-S8 | A refusal by the estimator crashed the opening | Declining is inconclusive | none named |
| P1-S9 | "Cannot fail" overstated | Now "blind to gain" | none |
| P1-S10 | An independent-site repeat needs constraints | Out of the first study | none |
| P1-S11 | Rule form, text and number of cases | Corrected; 2000 cases | none |
| P1-R1 (blocker) | An injected Python path flipped the opening | Removed and refused while visible; a hostile interpreter is a stated limit (see P2-V2) | `sf.py` |
| P1-R2 (blocker) | A block was overridden by a later approval | A block stands until that reviewer approves | none named |
| P1-R3 | An opening with no fetch reached ready | A held-out test names a fetch; the receipt names the data by hash | none named |
| P1-R4 | No defence against a log cut or rewritten | `check-log --anchor` and the committed log; unpushed rewrites remain | `sf.py` |
| P1-R5, R6 | Malformed logs and plans crashed; the change log could be any file | Refusals | none named |
| P1-M1 (blocker) | The claim class was outside the closed vocabulary | Fixed in the plan | none |
| P1-M2 (blocker) | The findings checker ran in no gate | A rehearsal before the lock; gating scheduled | none |
| P1-M3 (blocker) | Third-party handling out of order | A private clone first; disclosure a listed decision | none |
| P1-M4 (blocker) | A wrong fact and an unacknowledged doctrine change | Corrected | none |
| P1-M5 (blocker) | The roadmap block was invalid | Rewritten; since removed | none |
| P1-M6 | An ablation quoted against its caveat | Quoted with it | none |
| P1-M7 | The plan missed knowledge bearing on the window | See P1-S6 | none |
| P1-M8 | The tool could waste the only opening | Rule fields must resolve; a failed fetch may be voided | none named |
| P1-M9 | The acts by people were string checks | Said as recorded, not enforced; since replaced by pull requests (R3-01) | none |
| P1-M10 | The procedure was not code | `sf.py status` derives the stage | none named |
| P1-M11 | Interfaces unspecified | Specified | none |
| P1-M12 | Curating mishandled signed pages | Amendments stay owing a signature | none |
| P1-M13 | Effort understated | The reviewer's estimate adopted | none |
| P1-M14 | Overclaims | Restated | none |
| P1-M15, M16 | Exhibit inconsistencies and writing | Regenerated and corrected | none |

## P2: the red team's second pass

| Label | What it was | What became of it | Test |
|---|---|---|---|
| P2-V1 (blocker) | Part A's commands were missing or wrong | Written command by command and run | none |
| P2-V2 (blocker) | "An injected Python path is refused" was too strong | A tripwire and a stated limit | `sf.py` |
| P2-V3 (blocker) | The system trial could not close as described | Two outcomes, accepted and declined | none named |
| P2-V4 | Unstated preconditions | Stated | none |
| P2-V5 | A missing checkout changed the code identity | Bound as missing | none named |
| P2-V6 | A script the code list omitted was unbound | A named Python file is bound | `sf.py` |
| P2-V7 | The record of openings matched exact text | Spacing and case; meaning is the steward's | `sf.py` |
| P2-V8 | The system trial's seal was not a seal | Sealed from entropy at the opening; a seal by procedure | none named |
| P2-V9 | A receipt about a named product was committed | The trial reads no real record | none |
| P2-V10 | "Adequate power" described the kind case only | The range given; a robust estimator an acceptance criterion | none |
| P2-V11 to V15 | Evidence, timings, terms and an empty section | Corrected in place | none |

## SC: three scientists' reading

| Label | What it was | What became of it | Test |
|---|---|---|---|
| SC-1 | Exploration has no home | Scheduled then; built since as the exploring tool, which sets data aside first | `explore.py` |
| SC-2 | "Read by nobody" is almost never true | The request declares exposure; built since as the fresh-data proposal | `fresh_data.py` |
| SC-3 | One number against one threshold | Rule families and fields scheduled; not built | none |
| SC-4 | The difference that matters was sized to the sample | A line for it and its source in the request; the chance of inconclusive scheduled | none |
| SC-5 | Deadlines against one opening | "By when" in the request; a one-sitting path undecided | none |
| SC-6 | Inconclusive is useless without a consequence | An action per outcome in the request | none |
| SC-7 | Whose idea, whose signature | The plan carries its authors; what the signature attests is said | none |
| SC-8 | The language | The request and the result's first paragraph in the scientist's words | none |
| SC-9 | Known-answer tests written by the agent | The request asks for the scientist's own hard case | none |
| SC-10 | Scale: five limits in the study tool | Confirmed against the code; scheduled, not fixed | none |

## P3: the red team's third round

| Label | What it was | What became of it | Test |
|---|---|---|---|
| P3-A1 (blocker) | With the plan moved aside, every file check was skipped | A missing plan after a lock is a problem | `sf.py` |
| P3-A2 (blocker) | A script run by relative path was not locked | Every named file bound; the lock prints them | `sf.py` |
| P3-A3 (blocker) | What Python loads beside locked code was not hashed | Bound and scrubbed; libraries, the interpreter and a folder with no `__init__.py` are stated limits | `sf.py` |
| P3-A4 | Cutting the log back let the data be opened again | Refused | `sf.py` |
| P3-A5 | A second opening by reusing a name, a link, text or a misspelling | Refused; another parent folder keeps its own record (a stated limit) | `sf.py` |
| P3-A6 | `void-unread` voided an opening that had read its data | Only a failed fetch that changed nothing | `sf.py` |
| P3-A7 | An allowance above one was accepted | Refused | `sf.py` |
| P3-A8 | One variable switched off the committed-lock refusal | git runs with no `GIT_` variable; `lock-committed` check | `sf.py` |
| P3-A9 | Duplicate and unknown plan keys passed | Refused | `sf.py` |
| P3-A10 | `--procedure` took any file | Recorded and labelled; not refused | `sf.py` |
| P3-A11 | Nothing held the finding | The signature binds it by checksum | `sf.py` |
| P3-A12 | The log check copied outcomes from the log | Recomputed from the receipt; hand-appended agreeing events are a stated limit | `sf.py` |
| P3-A13 | A trial sealed through a hook was accepted | Refused unless shown at the lock | `sf.py` |
| P3-A14 | The method saw the answer | Data and answer apart; the sealed answer inside the study is a stated limit | `sf.py` |
| P3-A15 | A parameter file was not locked | Fixed with A2 | `sf.py` |
| P3-A16 | A receipt path could name the log | Refused | `sf.py` |
| P3-A17 | `log-change` could point at other records | Refused | `sf.py` |
| P3-A18 | Two simultaneous openings both passed | The log is held | `sf.py` |
| P3-A19 | Any tool change invalidated opened studies | A remark after an opening | `sf.py` |
| P3-A20 | Eight smaller gaps | Fixed; the rehearsal fetching the window is the first limit | `sf.py` |
| P3-B1 (blocker) | A planted bytecode file flipped a committed opening | Fixed in the tool and the contract | `compute/adapter.py conformance` |
| P3-B2 | The conformance test passed wrong places | 34 checks and a test of the test | `compute/adapter.py conformance --self-check` |
| P3-B3 | Conformance ran only locally | `--place`; only child processes ever tested | none named |
| P3-B4 | The contract did not check the job spec | Checked and recorded; the environment is carried, not checked | conformance |
| P3-B5 | One named opening ran four times | Keyed job ids; a place knows only its own jobs | conformance |
| P3-B6 | The local place trusted its own records | Kept apart; a same-user job can still rewrite them | conformance |
| P3-B7 | Status could not tell dead from running | A supervisor's file lock | conformance |
| P3-B8 | The marker rule was false | `fetch.started` decides; locally it means only the command started | conformance |
| P3-B9 | Cancel stopped nothing | Signals, waits, kills; a process that leaves its session is not found | conformance |
| P3-B10 | Collect copied any path | A regular file in the work folder | conformance |
| P3-B11 | `places.yaml` did not map the contract | One table; three places never exercised | none |
| P3-B12 | The first limit was said to be answered by where the opening runs | Corrected: only an analysis agent with no route to the data answers it, not built | none |
| P3-B13 | Nothing recorded where an opening ran | Host, user and commits recorded; nothing enforces where | `sf.py` |
| P3-B14 | A place would not deliver the tool's guarantees | Requirements written; not built | none |
| P3-B15 | MAAP statements read as verified | "As read", not exercised | none |
| P3-B16 | The scrubbed environment kept credentials | A short list; credentials for the opening alone are a rule | conformance |
| P3-B17 | Sentences read as if tests ran through the contract | Corrected; scheduled | none |
| P3-B18 | Leftover names and small crashes | Refusals in words | none |
| P3-B19 (note) | A job id is 64 bits; no verb removes a job | Stated | none |
| P3-B20 | Two documents said reviews were kept as written | Corrected | none |
| P3-C1 (blocker) | "One window, one opening" was off without `pair` | Fixed with A5 | `sf.py` |
| P3-C2 | "Every rule able to fail" was as strong as the chosen criteria | Four required; refutation power cannot be waived; no floor under values | `sf.py` |
| P3-C3 | The signature did not name the finding | Fixed with A11 | `sf.py` |
| P3-C4 | A second system trial could never be accepted | `study_kind: system_trial` | `sf.py` |
| P3-C5 | Part A did not exercise what it said | Corrected | none |
| P3-C6 | The control for typed names was weaker than stated | Corrected; since replaced by pull requests | none |
| P3-C7 | "A log that cannot be edited" | Corrected; nothing protects a log before its first commit | none |
| P3-C8 | The blind test headline was on kind cases | Said wherever quoted; the blind test still has no hard case | none |
| P3-C9 | The request was not part of the record | Bound by checksum | `sf.py` |
| P3-C10 | A plan could not be written from the templates | A commented template that passes the check | `sf.py` |
| P3-C11 | A fetch that downloaded the data could be voided | Fixed with A6; another name in the folder uses the opening up | `sf.py` |
| P3-C12 | "Try it" could not be followed cold | Corrected; placeholders refused | none named |
| P3-C13 | Present tense for what nothing holds | Each list names its holder | none |
| P3-C14 | "Observation metadata" over-defined | Defined by its test | none |
| P3-C15 | The opening accepted the tests' actor | Refused | `sf.py` |
| P3-C16 | The change-log exhibit lost its order | Remade | none |
| P3-C17 | Twelve contradictions | Corrected | none |
| P3-C18 | Leftover names | Corrected | none |
| P3-C19 | Untraceable numbers | Corrected or removed | none |
| P3-C20 | Words needing a gloss | WORDS.md | none |
| P3-C21 | Small tool behaviours | Fixed; the wording check does not scan `.jsonl` | `sf.py` |
| P3-C22 | Two places forgot the first limit | Corrected | none |

## P4: the check of the third round's fixes

| Label | What it was | What became of it | Test |
|---|---|---|---|
| P4-V1 (blocker) | A script named inside a shell string was hidden from the lock | A command is a known launcher and a bound script | `sf.py` |
| P4-V2 | A method that estimated nothing passed the known-answer tests | The method runs in its own process; the sealed answer inside the study is a stated limit | none named |
| P4-3 | A self-test that tested nothing (voiding after a normal fetch) | Fixed; the other new checks looked through | `sf.py` |
| P4-4 | Two residuals: waivable refutation power, the tool's child environment | Both taken up (`passes_environment`) | none named |
