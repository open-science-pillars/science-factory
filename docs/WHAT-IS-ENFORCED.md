# What is enforced, and by what

*Science Factory, part of Open Science Pillars. Written 2026-11-26, after two independent attacks on the tools.*

This page sorts every protection the factory claims into three lists: what a tool enforces on any machine, what is enforced only where the kernel or a harness makes it so, and what people and the platform hold. A fourth, short list is what is only an instruction to an agent. Each line names the self-test that makes the attack, or the attack finding it answers (B, S and M are the first attack's findings, N the second's; both are in `docs/reviews/ASSISTANTS-AND-EXPLORING.md`).

Read the first two lists with this in mind. **The limits the tools set slow a careless agent and catch honest mistakes. They are not a security boundary against a determined agent, or person, that shares the user's account on the machine.** Two attack rounds showed the same thing twice: a defence that matches patterns loses to the next spelling, and a name typed on a command line cannot say who acted. So the two acts that must be a person's, the lock and the steward's signature, do not rest on any of it. They are pull requests, approved and merged on a protected branch, where the platform a person signs in to decides who that person is. That is the third list, and it is the one that carries the weight.

The fixes for the second attack were made and tested by their author only. A third independent attack is owed, and it has to include the pull request route. The GitHub workflow has never run on GitHub.

## 1. Enforced by the tools, on any machine

These hold wherever Python runs, because the tool refuses or records and nothing else is needed. "Refused" means the command ends with an error and writes nothing but, where said, a logged refusal.

| What holds | Backed by |
|---|---|
| A lock or a signature typed at a command line is refused unless it says it is practice (`--local-practice`), and a study with a typed lock or signature says so in `status`, on its scorecard and in its finding, opens its held-out data only when the caller says practice too, and never closes as a signed finding | `sf.py selftest`: "a lock typed at a command line with no word of practice is refused", "a practice study never closes as a signed finding"; N5 |
| The held-out data is opened only after a lock; with the pull request route, only when git shows the merge the lock cites on the protected branch, reachable from what is checked out, and the manifest in it matches the files | `sf.py selftest`: "no merge", "wrong branch", "manifest changed after the merge", "a checkout whose history does not hold the merge", "a practice lock presented as a real one"; `record_act.py --selftest` |
| A definition (`factory/`) changed between the lock and the opening blocks the opening, says what changed, and uses no opening up | `sf.py selftest`: "a definition changed between the lock and the opening blocks the opening"; the owner's decision of 2026-11-26 |
| A plan, a bound file, or anything new that Python could import beside one, changed after the lock, blocks the opening; one opening for each held-out test; an opening is logged before it fetches | `sf.py selftest`, the earlier rounds |
| A plan's held-out block is on record from the first time a tool sees it; a plan whose block differs is refused by the plan check, the tests and the lock request until the coordinating step records the change with its reason; whoever ran the tests cannot record it; the lock shows every change, and a change with no record of it | `sf.py selftest`: "after that, a plan whose held-out block differs is refused by the plan check, the tests and the request for a lock", "whoever ran the tests cannot record the change", "with the record beside the studies deleted, a later change still shows at the lock"; N6 |
| Every command of the study tool, the exploring tool and the knowledge tool refuses to run when its environment carries the mark of a look or a step | `sf.py selftest`: "the mark a step's environment carries is enough on its own to refuse"; S2, N5 |
| A command of a plan, and a look, runs in a scratch copy that holds no log, under an environment the tool builds: no `UV_` variable, certificate setting or folder of the caller's arrives, and the receipt lists the environment by name | `sf.py selftest`: "a command of a plan runs in a scratch copy"; `explore.py selftest`: "a variable of the caller's that names an existing path never reaches a look"; N3, N9, N14 |
| A step that rewrites the plan or writes a study log in its scratch copy changes neither, and the run fails | `sf.py selftest`: "a step that rewrites the analysis plan" |
| A look is given the exploration's own files and files in the places it declared as working data at its start, and nothing else, whatever a file holds and however its dates are written | `explore.py selftest`: "N4, the structure"; N4, B1 |
| Data is set aside before any look; a look whose command names a folder, a pattern, a tilde path, a variable or several paths in one word is refused; every look, its inputs, its environment and its output are logged by checksum | `explore.py selftest`, the first attack's B1 and M4 |
| The second line: a file a look would be given, and what a look prints or leaves, is read for set-aside names and for dates in the window, in the forms `tools/explore.py` lists (it lists what it does not read too); a hit refuses the look or spoils the exploration and withholds the output | `explore.py selftest`: "N4, the second line", "N4: output that carries a set-aside date in another spelling"; N4 |
| A review is recorded only for the lead the reviewer read, named by checksum; a lead corrected meanwhile is refused; the reviewer was named before the lead existed and did none of the work | `explore.py selftest`: two checks under "N7"; S5, N7 |
| A number with a fraction in a lead, in the forms the tool reads (listed in `tools/explore.py`), was printed whole by a look the lead cites or stands in a page of a listed wiki; a page under a folder any role writes into backs nothing | `explore.py selftest`: three checks under "N8"; M1, N8 |
| A draft's source is a file that exists inside the places it is read from, an `https` address with a host name, or a doi; a folder, a path that climbs out, and any other word with a colon are refused | `knowledge.py selftest`: two checks under "N12"; M3, N12 |
| An actor's name is matched whole (a line break after it is not a name); the actor `platform:<host>` writes nothing but a merged act | `sf.py selftest`: "an actor with a line break after the name"; N14 |
| The tools start themselves again in a Python that reads no `PYTHON` variable, no user site, no start-up file and not their own folder, so a module planted beside a tool or on `PYTHONPATH` is not imported by it | `sf.py selftest`: "a file named like a standard module beside the study tool is not imported by it"; N9. Code a hostile environment loads when Python first starts has already run: see list 4 |
| The validator refuses an act declared as a pull request with no harness, no protected branch or no approval by anybody else, and a factory that declares one act each way | `check_factory.py --selftest`: "an act that is a pull request and asks for no approval by anybody", "one act a pull request and the other practice", and four more |

## 2. Enforced only with the kernel fence, or only inside a harness's per-call check

**With the kernel fence: Linux 5.13 or later with Landlock, and nowhere else.** The fence is put up by a small keeper process before the script starts, and tried: it must fail to read a file put outside for the purpose and to write beside its scratch folder, into the tool's own environment and into the tools' folder. The receipt of every look and the event of every test record that trial. On a machine that has Landlock, a fence that cannot be put up or does not hold is a refusal, never a quiet run without it (N2). It was built and tested on one Linux machine.

| What holds, with the kernel fence | Backed by |
|---|---|
| A look, and a command of a plan, cannot write anything the tools later run or import: not the tool's own environment, not another environment in the launcher's cache, not the cache, not `tools/`. `uv run` does not run the launcher inside the fence; the script's dependencies are installed beforehand into a throwaway environment it can read and cannot write | `explore.py selftest`: four checks under "N1"; `sf.py selftest`: "with the kernel fence, a command of a plan cannot read the study log"; N1 |
| A script cannot open the set-aside paths, the exploration, the study log, the tools, the home folder or anything outside its scratch folder, its interpreter and the system's folders, whatever variable the caller had set | `explore.py selftest`: "N2, N3, N14"; N2, N3 |
| A process a script leaves behind is ended before the look or the step is logged, also one that detached itself; the tools refuse a command with a keeper, a look or a step anywhere above it, with the marks taken out of the environment | `sf.py selftest`: "a job a step leaves behind to call the lock later", "the study tool refuses the lock, and every other command, when a step of a plan is anywhere above it"; N5, S2. The ancestry rule is read from `/proc` and tested on Linux; the adoption of a detached process is Linux only |

What the kernel fence leaves open, on any machine: the network; what is kept in the system's folders (`/etc`, `/usr`); shared memory (`/dev/shm`, which Python's multiprocessing needs; the receipt lists what appeared there); a service that listens on a socket file.

**Without the kernel fence (macOS, Windows, an older Linux)** a script the tools run can open and write any path its user can, the tools and the environments they run from included. The tool compares its own environment, the tools' folder and the start-up files of the environments beside it before and after such a run, and fails the run or spoils the exploration when they changed (`explore.py selftest`: "N1, where there is no kernel fence"). That catches a careless script and not a careful one. `status`, the lead and the hand-over say how many looks ran that way.

**Inside the Claude Code harness's per-call check (`factory/harnesses/claude-code/allow.py`), when a platform calls it, which has never been exercised.** Every line here was tested by calling a function with a tool call written by hand.

| What holds, when the check is called | Backed by |
|---|---|
| A role runs only the commands its file lists, one plain line each, under its own name and its declared model; no role may lock, sign, type a practice lock or record a merge; only the coordinating role may write a request or record a change to what is held out | `allow.py --selftest`: "no role may lock", "the coordinating role may write a lock request"; B2, S1, N5 |
| No role's write to a plan may change a held-out block that is on record; a path a plan or an exploration ever declared as held out or set aside is blocked for reading, wherever on the disk it lies | `allow.py --selftest`: four checks under "N6"; N6 |
| A role writes only where its file says, a `*` standing for one name, read from the top of the work: no pattern is a way into the wiki or into another role's folder; the role files and the check agree | `allow.py --selftest`: "N8", "N11"; N8, N11 |
| The review role cannot read, search over or hand to a tool the folder where other roles keep their accounts, its own place there apart: not through a hard link, a linked folder, `node_modules`, another file name or a pattern | `allow.py --selftest`: four checks under "N10"; `run_role.py --selftest`; S3, N10 |
| A role does not type a person's name in any option; a command over 4,000 characters is refused unread | `allow.py --selftest`: two checks under "N14"; N14 |

## 3. Held by people and the platform

| What holds | Who holds it | What the tools add |
|---|---|---|
| The lock and the signature are made by named people | The platform: a pull request approved and merged on a protected branch of the repository where the study lives | `sf.py request-lock` and `request-signature` write what a person is shown (an evidence summary in plain words and a manifest of checksums). The required check (`factory/harnesses/github/verify_request.py`) fails unless the manifest matches the files, somebody other than the author approves, and nothing an approval covered changed afterwards. Tested on recorded payloads; never run on GitHub |
| Who may approve, and how many | The repository's code owners and branch protection (`factory/harnesses/github/README.md` is the checklist) | `factory/factory.yaml` declares the number, and the validator and the check read it |
| That the branch is protected, the check required, and no administrator bypasses it | The repository owner's settings | Nothing. git alone cannot show it; a local branch with the same name looks the same from a clone |
| That the people in a log entry are the people who approved | The platform's own record of the pull request | The recording job copies the names from that record (`record_act.py`); nothing typed names a person |
| That a study log was not rewritten before its first commit or posted fingerprint | Fingerprints posted on the tracking issue at the lock and after each opening | `check-log --anchor`. In git, `check-log` compares with the last commit only: a log rewritten and committed again passes (N13) |
| That nobody reads the held-out data outside the tool | Nobody, for public data. A place where the analysis assistant has no route to the withheld values is not built | Nothing |

## 4. Only an instruction to an agent

Nothing checks these. An agent is told, and the log shows afterwards what the tools saw of it.

- Which model wrote an event: declared by the caller, recorded under the log's hash, proven by nothing.
- That only knowledge is read before data is set aside; that nothing is looked at outside the tool; that a choice is written down when it is made.
- That a role started outside its rendered file keeps to its role, and that the reviewer is a separate assistant with a fresh context and not the author under another name. A task that pastes the author's words in is not caught, and nothing stops the author writing its account into a file the reviewer reads.
- That an agent with a shell, or a person, stays out of the acceptance set of blind cases. The seed being outside the repository is the part that is not instruction.
- That the working data declared at the start of an exploration is working data. The declaration is on the record from the first event and the reviewer and the lock see it; nothing knows what the files hold beyond the second line of list 1.
- Everything on a machine where the environment the tools start in is hostile: code loaded when Python first starts runs before any check, with the caller's rights.
