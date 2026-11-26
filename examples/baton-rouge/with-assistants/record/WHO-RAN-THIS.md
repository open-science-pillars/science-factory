# Who ran each role in the run with separate assistants

**Each role was a separate assistant, started from its role file with a task and with no memory of the others.** Every one of them was a subagent of the same model, `claude-fable-5-2` (Claude Fable 5.2), started by a coordinator that gave it the path of its role file (`assistants/<role>.md`), the skills that file names, and a task. Run on 2026-11-26. The requests were written for the example; no person asked them, and no person locked or signed anything.

| Step | Role | Acted as | Started from | Fresh context | What it handed back |
|---|---|---|---|---|---|
| 1 | analysis | `agent:analysis-0101` | `assistants/analysis.md` | yes | `01-analysis.answer.md`; lead version 1 |
| 2 | review | `agent:review-0101` | `assistants/review.md` | yes | `02-review.answer.md`; REVIEW-001, holes-found |
| 3 | analysis | `agent:analysis-0101` | `assistants/analysis.md` | yes: a new subagent with no memory of step 1, working from the log, the receipts, the review and its own earlier answer file | `03-analysis.answer.md`; lead versions 2 and 3 |
| 4 | review | `agent:review-0103` | `assistants/review.md` | yes | `04-review.answer.md`; REVIEW-002, holes-found |
| 5 | curating | `agent:curating-0101` | `assistants/curating.md` | yes | `05-curating.answer.md`; four drafts, one note linked, one declined |
| 6 | analysis, second question | `agent:analysis-0102` | `assistants/analysis.md` | yes | `06-analysis-second-question.answer.md`; lead version 1 of EXPLORATION-0102 |

The order on the clock, from the two exploration logs, was 1, 2, 3, 5, 6 and 4 overlapping: the curating assistant resolved the notes at 06:54 UTC, the second analysis assistant started at 06:57 and read the drafts, and the second review was recorded at 07:00. So the notes were resolved, and the drafts used, before the revised lead had been reviewed. The second review said so. The exploring tool now refuses to resolve a note before the exploration has ended; this log was written before that and is kept as it is, and `explore.py check-log` passes on it with a remark that says the same.

**One review assistant stopped itself.** For the second review a review assistant was started that saw, by accident, the analysis assistant's own account of the work, which sat in this folder, the same folder a reviewer was asked to write its answer into. Its role file says that a reviewer who has been given the author's reasoning says so and stops. It did. It recorded nothing in the exploration, so it does not appear in the log, and a fresh review assistant (`agent:review-0103`) was started in its place; that one's answer says it did not read this folder. It is also why each role now has its own place for its account (`record/<role>/`), why the review role's file names the analysis role's place under `must_never_see`, and why the runner refuses it. This folder keeps the flat layout the run had.

## What was real

- **Separate contexts.** No assistant had another's conversation. The review assistants did none of the work and worked from the files. The second analysis assistant had never seen the first exploration; what it knew of it came from the four drafted pages, which it found listed as drafts.
- **The tools.** Every look, choice, note, lead, review and resolution went through `mvp/loops/explore.py` and `mvp/loops/knowledge.py`, and the logs, receipts and checksums are theirs.
- **The data and the knowledge.** The 2024 confrontation fixture and the knowledge bundle of the hydrology checkout. Nothing from 2025-01-01 onward was fetched, read or asked about.
- **The answer files.** Each is what the assistant handed back, unedited, and each ends with what was unclear, wrong or in the way in the role files, the skills and the tools. Those endings, with the hydrologist's review, are what the tools were then changed for (`reviews/ASSISTANTS-AND-EXPLORING.md`).

## What was not, and what this run does not show

- **Tool restrictions were by instruction and by the role file, not by a runner.** Each subagent was told which role it was and read its role file; nothing outside it stopped a call the file does not allow. The Claude Code runner (`runners/claude-code/`: the rendered agent files, the per-call check `allow.py`, the launcher `run_role.py`) was not used to start these assistants and has still not been exercised against Claude Code. The answer files record small departures an enforcing runner would have stopped: a look made outside the tool with a plain interpreter and listings of folders the assistant had been told to keep out of (`06`), and a reviewer reading a page that summarised the earlier run in order to judge a declared leak (`02`).
- **The coordinating role was played by the person's session,** which read the status the tools printed, wrote each task and started each subagent. No assistant was started from `assistants/coordinating.md`. So nothing here shows that a coordinating assistant follows `status`, and the order in which the curating assistant and the second review ran was the session's choice.
- **One model.** Every role was the same model. Separate contexts are not separate minds: a blind spot the model has, every role shares.
- **Not blind to the earlier run.** The first analysis assistant read the example's page and the head of a method script before looking, both of which stated what the single-instance run had found. It says so in its answer and in the lead.
- **No hand-over.** The first exploration has not ended: it stands at `revise-or-end` after a second holes-found. The hand-over to a confirming study was not repeated in this run; the only hand-over in this example is the single-instance run's (`../explorations/EXPLORATION-0001/hand-over/`, `../studies/STUDY-0002/`).
- **The second lead is not reviewed.** EXPLORATION-0102 stands at `review`.
- **No task files.** The tasks were given to the subagents by the coordinating session and were not kept as files; the answer files say what each was asked. The launcher keeps the task beside the answer, which is one more reason to use it next time.
- **No person.** Nobody locked, signed, accepted a draft or asked a question.
