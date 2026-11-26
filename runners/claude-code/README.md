# The runner for Claude Code

A runner starts the right role with the right tools. This one does it with Claude Code subagents and skills. The roles and skills themselves are the neutral files in `assistants/` and `skills/`; nothing a role needs is defined here.

| File | What it does |
|---|---|
| `render.py` | writes `.claude/agents/<role>.md`, `.claude/skills/<name>/` and `.mcp.json` from the neutral files; `--check` fails when what is on disk is missing, stale, edited by hand, or has a role or skill with no source |
| `allow.py` | the decision each tool call of a role gets, read from the role file at the time of the call; Claude Code calls it as a PreToolUse hook that each rendered role carries |
| `run_role.py` | starts one role in a fresh context with `claude -p --agent <role>` and keeps the task, the answer and which model ran it |

The rendered files are committed, so the repository works when opened in Claude Code: start the coordinating role with `claude --agent coordinating`, or one role at a time with `run_role.py`. After changing a role or a skill, run `uv run runners/claude-code/render.py` and commit both.

Each rendered role points to the knowledge base as a wiki (`openwiki/` in this repository), because its role file does, and is given the two read-only wiki tools, `openwiki_search` and `openwiki_read`, from the server `.mcp.json` names `openwiki`. By default that is this package's own read-only server (`mvp/loops/wiki_server.py`); to use the OpenWiki tool's server, change the one entry in `render.py` and render again. The per-call check lets a role use those two tools from any server and no other tool of any server.

## What this runner really enforces, and what stays instruction

**Enforced by the platform, when a role is started from its rendered file.**

- The role's tools. A rendered role lists only the tools its role file implies: the coordinating role has no Write or Edit; only the coordinating role may start other roles, and only the three named.
- A fresh context for each subagent. A role started as a subagent or by `run_role.py` begins with its role file and its task and nothing else. That is what gives the review role its distance from the work.

**Enforced by `allow.py`, when Claude Code calls the hook.**

- The role's commands. Bash may run one thing: `uv run mvp/<tool>.py <command>` for a command in the role's `may_call`, with no pipes, chains, redirections, substitutions or variables. So no role can run the lock or the signature, the review role cannot run a look, and only the review role can record a review.
- The role's name. A `--by` must be `agent:<role>` or `agent:<role>-<suffix>`, so a role cannot act under another role's name or a person's.
- Where the role writes. Write and Edit only on paths matching the role's `writes`, and never on a log, the record of what has been opened, a receipt, a recorded lead or verdict, a role, a skill, a tool or the rendered files.
- Reading a path that an exploration beside it set aside or a study's plan holds out is blocked for Read, Grep and Glob.

**Tested and not exercised.** `allow.py`, `render.py` and `run_role.py` each test themselves (57, 11 and 6 checks). That Claude Code calls the hook from a subagent's front matter, applies `tools` to a role started with `--agent`, and loads the listed skills was **not exercised**: the environment this was built in could not start Claude Code against a model. Until someone runs it, read "enforced" above as "rendered to be enforced".

**Still instruction, on one machine.**

- No route to held-out data. A script run through `explore.py look` or `sf.py test` can read anything the machine can reach, including the network, once it is running. The tools check what a command names and what a look leaves behind; they cannot see inside a running script. Only running the analysis role where the held-out values cannot be reached would close this, and that is not built.
- A conversation started without the rendered role (plain `claude` in this repository) is held by nothing here.
- That a role with a fresh context has not been told the other role's reasoning: the coordinating role is instructed not to pass it on, and nothing checks what it passes.
- Who is behind a name. `agent:review` is typed, as every name in the study tool is.
