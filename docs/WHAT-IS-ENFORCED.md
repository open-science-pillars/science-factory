# What is enforced, and by what

This is the one statement of what the factory enforces. Every other page links here instead of saying it again. It sorts each protection into one of four lists: what a tool enforces on any machine; what holds only with the kernel fence or inside a harness's per-call check; what people and GitHub hold; and what is only an instruction to an agent. Each row of the first two lists is backed by self-tests, named at the foot of its list; the labels (R1-01 and so on) are those of the [register](reviews/README.md).

Two words first. **Fresh data** is data nobody working on the question has looked at; the tools call it **held-out data**, and in an exploration they say it is **set aside**. An **act** is one of the two things only people do: the lock and the steward's signature.

**Read the first two lists with this in mind.** The limits the tools set slow a careless agent and catch honest mistakes. They are not a security boundary against a determined agent, or person, that shares the user's account on the machine. A defence that matches patterns loses to the next spelling, and a name typed on a command line cannot say who acted. So the two acts do not rest on the first two lists. Each is a pull request on GitHub, approved and merged on a protected branch, where GitHub decides who a person is.

## The three standings of an act

A clone cannot prove that people acted, so the tools never say they did on local evidence. Every lock and signature has one of three standings, shown wherever the act is shown (`sf.py status`, the scorecard, `check-log`, the signature request, the first line the tool puts on a finding, and the curation list that drafted knowledge is made from).

| Standing | What it rests on | What it does not show |
|---|---|---|
| `practice` | the act was typed at a command line (`--local-practice`) | anything about anybody |
| `merge found, people not verified` | git on this machine finds a merge of the request on a branch with the protected branch's name, with a manifest that matches the files | that any person approved, that there was a pull request, or that the branch is protected: a clone can make all of it, and a file of approvals on the same machine is a file anybody there can write |
| `verified` | GitHub, asked over https with a token from the environment (`sf.py verify-acts`; the opening asks for itself), said the commit is the merge of a pull request into the protected branch of the repository the definition names, approved on the request as merged by enough accounts other than its author, none a bot | that the approving accounts are the right people, or that whoever ran the verification ran it honestly: the answer is a log entry, and its worth is that anybody can ask again |

![An act by people: a tool writes the request, people approve and merge the pull request, it is recorded as a merge found, and only GitHub's answer makes it verified.](diagrams/acts-and-standings.svg)

Nothing in the work tree moves an act past the second standing. A study whose lock or signature is not `verified` is "awaiting verification": not signed in its status, its record or the first line of its finding, and it does not close as a signed finding.

**The exception for a place with no network.** `open-held-out --people-not-verified REASON` opens fresh data on a lock that is a merge found with git, when GitHub cannot be asked. It is refused unless the definition allows it: `opening_without_verification: allowed-with-a-reason` under the lock in `factory.yaml`. The shipped definition says `refused`. The lock binds the definition by checksum and a changed definition blocks the opening, so allowing it is a change people approve and lock, not something typed at the opening. Where it is allowed, the opening is logged with the reason, the finding must say so in its first line, and the study stays unsigned until a verification succeeds. An answer from GitHub that refutes the lock is never waived.

## The so what: a person's answer to a lead, lighter than an act

After a review, a person answers whether a lead is worth confirming (`worth-confirming`, `try-instead`, `not-interesting`, `needs-an-expert`). We made it a comment on the tracking issue, not a pull request review. The two acts are pull requests because each guards something scarce: the lock spends fresh data, the signature makes a finding. The so what spends nothing, and a lead it lets through still meets people at the lock, which shows it. It must be cheap enough to give on every lead and be a person's; a comment is both, and GitHub can be asked who wrote it. Its standings: `practice` (typed, `--local-practice`), `comment recorded, person not verified` (written under `platform:github` by the workflow's `so-what` job) and `verified` (`explore.py verify-so-what` asked GitHub: the comment is in the named repository, by that account, a user who belongs to it, unedited).

## 1. Enforced by the tools, on any machine

These hold wherever Python runs: the tool refuses or records, and nothing else is needed.

| # | What holds |
|---|---|
| 1.1 | A lock or a signature typed at a command line is refused unless it says it is practice. A practice study says so everywhere, and never closes as a signed finding. |
| 1.2 | The tools call no act more than `merge found, people not verified` on anything in the work tree; names handed to `--record-merge` are shown as handed, never as people who approved. |
| 1.3 | Without GitHub's answer, no fresh data is opened on a lock recorded from a merge; the attempt is logged as `not checked` and the opening is not used up. `--people-not-verified` is refused unless the definition allows it. |
| 1.4 | A merge found with git is a commit on the named branch's own line, reachable from what is checked out, with two parents and the request brought in from the second, whose manifest matches the files. An ordinary commit is refused; a squash merge is taken only where the definition lists it; a rebase merge never. |
| 1.5 | A definition changed between the lock and the opening blocks the opening and says what changed. Its checksum binds each file's bytes, whether it is executable, and a symlink as a link. |
| 1.6 | A plan, a bound file, or anything new that Python could import beside one, changed after the lock, blocks the opening. Each test on fresh data opens once, and the opening is logged before it fetches. |
| 1.7 | What a plan holds out goes on record the first time a tool sees it. A plan whose block differs is refused until the coordinating step records the change with a reason; whoever ran the tests cannot record it; the lock shows every change, including one with no record. |
| 1.8 | A proposal of the fresh data is made by `tools/fresh_data.py` from one metadata file, which is refused if it carries any field that is not metadata. Each proposal goes on a record beside the studies. A random set aside is drawn by the tool from a seed it makes; the proposal keeps only the seed's sha256, and the lock request reveals the seed and draws again. |
| 1.9 | An exploration sets aside exactly the proposal it names, and a random set aside cannot start without one. A lock request refuses a proposal that is not on the record byte for byte, a random draw its seed does not give, or a plan window outside a proposed later period, and it shows the proposal in words. A plan that names no proposal is told so in plain words at the lock. |
| 1.10 | A study log rewritten and committed again fails the log check and blocks the opening. The merged request pins the log's head as it was at the request. |
| 1.11 | Every command of the study tool, the exploring tool, the fresh-data tool and the knowledge tool refuses to run from inside a look or a step of a plan. |
| 1.12 | A command of a plan, and a look, runs in a scratch copy that holds no log, with an environment the tool builds; the receipt lists the environment by name. A step that rewrites the plan or a log in its copy changes neither, and fails. |
| 1.13 | A look is given the exploration's own files and the working data it declared at its start, and nothing else. A look that names a folder, a pattern, a tilde path, a variable or several paths in one word is refused. Every look is logged with its inputs and output by checksum. |
| 1.14 | As a second line, what a look would be given, prints or leaves is read for set-aside names and for dates in the window, in the forms `tools/explore.py` lists; a hit refuses the look or spoils the exploration. |
| 1.15 | A review is recorded only for the lead the reviewer read, by checksum, from a reviewer named before the lead existed who did none of the work. |
| 1.16 | A decimal number in a lead, in the forms the tool lists, was printed whole by a look the lead cites or stands in a page of a listed wiki. |
| 1.17 | A draft's source is a file that exists, an https address with a host, or a doi. A draft carries no signature. |
| 1.18 | An agent's event names its model (`--model`), or it is refused; an actor's name is matched whole; `platform:<host>` writes nothing but a merged act and its verification. |
| 1.19 | Every tool restarts itself in a Python that reads no `PYTHON` variable, no user site, no start-up file and not its own folder. |
| 1.20 | The validator refuses a definition with an unknown key, a dangling name, a judge that reads anything written after an opening, `selfImprovement: true` on a check that does, an act declared as a pull request without a harness, branch, approvals, repository or merge method, a rebase merge, and an unknown value for `opening_without_verification`. |
| 1.21 | A judging packet holds the material its scorer declares, each file by a checksum recorded before any opening (a plan's packet includes its bound code), nothing written after an opening, and no path outside itself. A verdict is recorded beside the packet, and the answer file leaves it. |
| 1.22 | The acceptance set of blind cases gives nothing without its seed, which is not in the repository. |
| 1.23 | Every command shown in an agent file, a skill or AGENTS.md parses under its tool's options as they are now, and passes `--model` where it acts as an agent. |
| 1.24 | No exploration ends as a lead, and no lead is handed over, without a person's `worth-confirming` on the lead as it stands, after its latest review. An agent's so what is refused, a typed one unless it says practice (and then the hand-over must say so), and a comment only from a user of the named repository naming this lead. |
| 1.25 | A lock request shows, as pictures with captions, every figure the exploration's looks kept (bound when the study starts) and every figure the plan's steps declare; a signature request shows the opening's. A declared figure not drawn fails its step, a changed one refuses the request, and both manifests bind them. |
| 1.26 | An attached finding carries who did each kind of work, drawn from the study's log and its exploration's, with each agent's declared model and what the logs cannot show. A draft from an exploration or a study is refused without a **Who did what.** paragraph. |
| 1.27 | Leads, findings and their reviews are read for the phrases of `scorers/overclaiming-in-leads/phrases.yaml` and for numbers finer than their uncertainty (`confirms` unless the rules gave `supported`); each flag names the phrase and the line, at `lead`, `review` and `attach`, in status, on the scorecard and in the signature request. It warns, never blocks. |
| 1.28 | A fit note is complete or refused, and refused once the first look or test has run; status, the hand-over and the lock request show it, or say there is none. It never blocks work. |
| 1.29 | A method is promoted only from a look that passed, with its README's three parts, its runs as cases and every checksum; the validator refuses it changed or absent from the change log. A plan that binds one needs a rehearsal running its tests, and its tests, other rehearsals and lock wait until that rehearsal passed on the code as it stands. |

Tests, by row (each command is `uv run tools/<tool>`, or the harness script named):

1. `sf.py selftest`: "a lock typed at a command line with no word of practice is refused", "a practice study never closes as a signed finding" (R2-05).
2. `sf.py selftest`: the checks named "A3-1"; `record_act.py --selftest` (R3-01).
3. `sf.py selftest`: "A3-1: the held-out data is not opened on a merge found with git", "the exception for a place with no network is the definition's to allow", "a definition changed after the lock to allow the exception does not open the data" (R3-01).
4. `sf.py selftest`: "no merge", "wrong branch", the checks named "A3-2" (R3-02).
5. `sf.py selftest`: "a definition changed between the lock and the opening blocks the opening", checks named "A3-3"; `check_factory.py --selftest`: checks named "A3-3" (R3-03).
6. `sf.py selftest`: the lock and opening checks.
7. `sf.py selftest`: the held-out record checks (R2-06).
8. `fresh_data.py selftest`: "the proposing step opens one file to read, the metadata", "a random set aside holds only the seed's sha256", "the draw is reproducible from the revealed seed".
9. `explore.py selftest`: "a random set aside cannot be typed", "a random set aside with one site swapped"; `sf.py selftest`: "a plan that names the agent's proposal of the fresh data shows it at the lock in words", "a proposal edited by hand after the tool wrote it is refused at the lock".
10. `sf.py selftest`: the checks named "N13" (R3-05).
11. `sf.py selftest`: "the mark a step's environment carries is enough on its own to refuse"; `explore.py selftest`: "the knowledge tool refuses inside a look too" (R1-04, R2-05).
12. `sf.py selftest`: "a command of a plan runs in a scratch copy", "a step that rewrites the analysis plan" (R2-03).
13. `explore.py selftest`: "a look that names a folder is refused", "N4, the structure" (R1-01, R2-04).
14. `explore.py selftest`: "N4, the second line" (R2-04).
15. `explore.py selftest`: checks named "N7" (R1-04, R2-07).
16. `explore.py selftest`: "a number no look printed is refused in every form it can be written", checks named "N8" (R1-08, R2-08).
17. `knowledge.py selftest`: checks named "N12" (R1-10, R2-12).
18. `sf.py selftest`, `explore.py selftest`: "an agent that names no model", "an actor with a line break after the name" (R2-14).
19. `sf.py selftest`: "the tool's help is words, not its own source", "a file named like a standard module beside the study tool is not imported by it" (R2-09).
20. `check_factory.py --selftest`: one case for each rule it names.
21. `scorers.py selftest`: the firewall checks, "a packet names no place outside itself", "each run's verdict leaves the packet".
22. `benchmark.py selftest`: the acceptance-case checks.
23. `check_roles.py --selftest`: "a skill shows an agent's command without `--model`", "a skill shows a command with an option the tool does not have".
24. `explore.py selftest`: the checks under "the person's so what on a reviewed lead"; `verify_acts.py --selftest`: the five checks named "a so what"; `check_factory.py --selftest`: "a definition with no so what", "an agent that may call the so what"; `allow.py --selftest`: "no role may record a person's so what".
25. `sf.py selftest`: the checks of `_selftest_figures`; `explore.py selftest`: "the hand-over carries every figure the looks kept"; `verify_request.py --selftest`: "points each figure at the head of the pull request".
26. `sf.py selftest`: "the finding carries who did each step", "the contribution statement of a study"; `explore.py selftest`: "the contribution statement of a lead"; `knowledge.py selftest`: "does not say who did the work it rests on".
27. `sf.py selftest`: the checks of `_selftest_overclaiming`; `explore.py selftest`: "a lead that claims more than an exploration can show"; `check_factory.py --selftest`: "an overclaiming check that names no list of phrases", "a list of phrases with a pattern that does not compile".
28. `sf.py selftest`: the checks of `_selftest_fit`; `explore.py selftest`: "the coordinating agent's fit note is recorded at intake", "a fit note once the first look has run is refused".
29. `explore.py selftest`: the checks under "a look that proved useful becomes a method"; `check_factory.py --selftest`: the cases named "a promoted method".

## 2. Enforced only with the kernel fence, or inside a harness's check

**With the kernel fence: Linux 5.13 or later with Landlock, and nowhere else.** A small keeper process puts the fence up before a script starts and tries it: the script must fail to read a file put outside for the purpose, and to write into the tool's own environment or the tools' folder. Every receipt records that trial. On a machine that has Landlock, a fence that cannot be put up is a refusal. It was built and tested on one Linux machine.

| # | What holds, with the kernel fence |
|---|---|
| 2.1 | A look, or a command of a plan, cannot write anything the tools later run or import. |
| 2.2 | A script cannot open the set-aside paths, the exploration, the study log, the tools, the home folder, or anything outside its scratch folder, its interpreter and the system's folders. |
| 2.3 | A process a script leaves behind is ended before the step is logged, also one that detached itself (Linux only). |

What the kernel fence leaves open: the network; the system's folders (`/etc`, `/usr`); shared memory (`/dev/shm`, listed in the receipt); a service listening on a socket file. **Without it** (macOS, Windows, an older Linux) a script can open and write any path its user can. The tool compares what the tools run from before and after such a run and spoils the exploration when it changed, which catches a careless script and not a careful one; `status` and the lead say how many looks ran that way.

**Inside the Claude Code harness's per-call check (`factory/harnesses/claude-code/allow.py`), which Claude Code has never called.** Each line was tested by calling the check with a tool call written by hand.

| # | What holds, when the check is called |
|---|---|
| 2.4 | An agent runs only the commands its file lists, one plain line each, under its own name and its declared model. No agent may lock, sign, type a practice act, record a merge, or pass `--people-not-verified`. |
| 2.5 | No agent's write to a plan may change a held-out block on record; a path ever declared as held out or set aside is blocked for reading anywhere on the disk; a tool may not be handed a file the agent may not read. |
| 2.6 | An agent writes only where its file says; the review agent cannot read or search the place where the analysis agent keeps its account. |
| 2.7 | An agent types no person's name in any option; a command over 4,000 characters is refused unread. |

Tests, by row: 2.1 `explore.py selftest`, four checks named "N1" (R2-01). 2.2 `explore.py selftest`: "N2, N3, N14" (R2-02, R2-03). 2.3 `sf.py selftest`: "a job a step leaves behind to call the lock later" (R2-05). 2.4 `allow.py --selftest`: "no role may lock", "A3-1: no role opens held-out data on a lock whose people are not verified" (R1-02, R1-03). 2.5 checks named "N6" (R2-06). 2.6 checks named "N8", "N10", "N11"; `run_role.py --selftest` (R1-05, R2-10). 2.7 checks named "N14".

## 3. Held by people and GitHub

| What holds | Who holds it | What the tools add |
|---|---|---|
| The lock and the signature are made by named people | GitHub: a pull request approved and merged on a protected branch of the repository where the study lives | `sf.py request-lock` and `request-signature` write what a person reads (an evidence summary in plain words, the fresh-data proposal among it, and a manifest of checksums). The required check (`verify_request.py`) fails unless the manifest matches the files, somebody other than the author approves (no bot), and nothing an approval covered changed afterwards |
| That an act in a study log is such a pull request, and who approved it | GitHub, asked by `sf.py verify-acts`, which anybody with the clone, a network and a read token can run at any time | Each answer is recorded with every address asked and the name of the token's variable (never the token); with no network or token the result is `not checked`, never a pass |
| That a verification's answer was really GitHub's | Whoever ran it, on the machine it ran on | The entry names the proxy and certificate settings in force. An attestation that needs no such trust is proposed in [proposals/ATTESTED-ACTS.md](proposals/ATTESTED-ACTS.md), not built |
| Who may approve, and how many; that the branch is protected and nobody bypasses it | The repository's code owners and settings (`factory/harnesses/github/README.md` is the checklist) | `factory.yaml` declares the number; `verify-acts` asks whether the branch is protected, and says what it was not shown |
| That a lead's so what came from a person | GitHub: a comment on the tracking issue by an account of the repository | `explore.py verify-so-what` asks GitHub; whether the account is the right person is for whoever reads the name |
| That the fresh data proposed suits the question and is fair | The scientist and the steward, who approve it at the lock, and the review agent before them | The proposal in words, with the tool's caution for its kind and the size of test it allows |
| That a log was not rewritten before its first commit or posted fingerprint | Fingerprints posted on the tracking issue at the lock and after each opening; a protected branch | `check-log --anchor`. What remains: a log and its whole history rewritten before the first request, on a clone never pushed |
| That nobody reads the fresh data outside the tool | Nobody, for public data. A place where the analysis agent has no route to the withheld values is not built | Nothing |

## 4. Only an instruction to an agent

Nothing checks these. An agent is told, and the log shows afterwards what the tools saw.

- Which model wrote an event: declared by the caller, recorded, proven by nothing. A contribution statement says so, and cannot show thinking that left no event.
- That people look at each figure; that a fit note is a fair reading of the request; that a flagged word is rewritten, and that words the list lacks do not overclaim.
- That only knowledge is read before data is set aside; that nothing is looked at outside the tool; that a choice is written down when it is made; that every comparison inside a look is declared.
- That the agent proposing the fresh data opened no data file first; that a metadata file holds no values under the names the tool allows; that the reasons in a proposal are true; and that a confirmatory plan names a proposal at all (the lock request says so when it does not).
- That an agent started outside its rendered file keeps to its role; that the reviewer is a separate agent with a fresh context, and was passed nothing the author said; that the analysis agent had not already read an answer to its question.
- That the working data declared at the start of an exploration is working data. Where data is set aside by its dates alone and sits in a declared folder, only the reading of dates stands in the way (R3-04).
- That a number written out in words in a lead is true; only the forms row 1.16 lists are checked.
- That an agent or a person with a shell stays out of the acceptance set of blind cases. That its seed is outside the repository is the part that is not instruction.
- Everything, on a machine whose environment is hostile: code loaded when Python first starts runs before any check.

## What has never run

GitHub: the workflow, the required check, the recording job and the `so-what` job against real events, and `verify-acts` and `verify-so-what` against GitHub itself; every part of the route is tested on answers written by hand in GitHub's shapes. Claude Code: the harness's per-call check and launcher, and the judges' Claude Code path (a first trial ran the judges as agents reading packets by hand). Any of it on macOS, Windows or a Linux without Landlock. A real study, from request to signature.
