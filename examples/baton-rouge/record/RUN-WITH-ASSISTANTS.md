# Running this example with real assistants

The record here was made by one instance playing every role (WHO-RAN-THIS.md). To make it with real assistants, each in a fresh context and held to its role's tools, from the repository root, with the hydrology and nasa-daac-knowledge checkouts beside the repository:

With Claude Code subagents. Open the repository in Claude Code started as the coordinating role (`claude --agent coordinating`) and give it the text of `01-coordinating.task.md` with a new work folder. It may start only the analysis, review and curating roles, each from `.claude/agents/<role>.md`.

One role at a time, keeping the record:

```
uv run runners/claude-code/run_role.py --role analysis \
  --task-file examples/baton-rouge/record/02-analysis.task.md \
  --record <new work folder>/record/02-analysis
```

Use the task files in this folder in order (02 to 08), changing the work folder in each to a new one so that this record is not overwritten. `run_role.py` writes the task, the answer and which model ran the role. Between roles, `uv run mvp/loops/explore.py status --exploration <dir>` says who is next.

What to compare with this record: whether a review assistant with no memory of the exploring finds the same nine holes or others; and whether an analysis assistant that never saw the first exploration finds the two drafts, says they are drafts, and uses them.
