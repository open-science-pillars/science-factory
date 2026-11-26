# Who ran each role in this example

**Every role was played by one model instance, in one conversation.** The model was `claude-fable-5-2` (Claude Fable 5.2), running as a Claude Code agent. It could not start other assistants: it had no tool for starting a subagent, and the `claude` program in its environment could not authenticate, so `runners/claude-code/run_role.py` could not be used. This is the closest honest thing to what was asked, and it is less than what was asked.

| Role | Model | Runner | Started from | Fresh context |
|---|---|---|---|---|
| coordinating | claude-fable-5-2 | by-hand | assistants/coordinating.md, read by the same instance | no |
| analysis (first question) | claude-fable-5-2 | by-hand | assistants/analysis.md and its three skills | no |
| review (twice) | claude-fable-5-2 | by-hand | assistants/review.md and skills/review-work | **no** |
| curating | claude-fable-5-2 | by-hand | assistants/curating.md and skills/draft-a-knowledge-page | no |
| analysis (second question) | claude-fable-5-2 | by-hand | assistants/analysis.md | no |

What was real. The data, the knowledge, every look and its numbers, every refusal. Each command a role ran went through `runners/by-hand/as_role.py`, which checks it against the role file with the same decision the Claude Code runner uses and does not run what the file does not allow; `commands.jsonl` is that record, blocked commands included. The role's name in every `--by` was held to the role by that check.

What was not. No role had a fresh context, so the two reviews are the author checking their own work with the review checklist, and the second question was asked by an instance that remembered the first. The second exploration's use of the drafted pages is therefore shown mechanically (the pages were listed as drafts, read, recorded and used, and the log says so) and not as evidence that a fresh assistant would have found and trusted them. The files written by a role (look scripts, the lead file, the review files, the drafts, the plan) were written by the operator directly after asking the same check whether the role may write that path; the check's answers are in `commands.jsonl`.

The task and answer files in this folder are what was handed to each role and what it handed back, written by the same instance at the time. The tool changed while the example ran (the check of a lead's numbers against its cited looks was added between lead versions 3 and 4, and four holes were closed afterwards); the logs were not rewritten. The two new tools were also moved from `mvp/` into `mvp/loops/` after most of the example had run, so the earlier lines of `commands.jsonl` name them at their first path; the last lines, after the move, rerun the study's two tests and the checks on the code as it now stands.

To run it with real assistants: `RUN-WITH-ASSISTANTS.md` beside this file.
