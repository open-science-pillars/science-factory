# The harness for Claude Code

A harness starts the right role with the right tools. This one does it with Claude Code subagents and skills. The roles and skills themselves are the neutral files in `factory/agents/` and the skills folders (`factory/skills/`, shared, and `factory/agents/<name>/skills/`, an agent's own); nothing a role needs is defined here. `harness.yaml` says which models an agent's file may declare under this harness; the rendered agent file carries the declared model, and the per-call check blocks a `--model` that is not it.

| File | What it does |
|---|---|
| `render.py` | writes `.claude/agents/<role>.md`, `.claude/skills/<name>/` and `.mcp.json` from the neutral files; `--check` fails when what is on disk is missing, stale, edited by hand, or has a role or skill with no source |
| `allow.py` | the decision each tool call of a role gets, read from the role file at the time of the call; Claude Code calls it as a PreToolUse hook that each rendered role carries |
| `run_role.py` | starts one role in a fresh context with `claude -p --agent <role>` and keeps the task, the answer and which model ran it, in the role's own place (`record/<role>/`); it refuses any other place, and refuses a task that names a path the role must never see, in either layout the author's account has been kept in |

The rendered files are committed, so the repository works when opened in Claude Code: start the coordinating role with `claude --agent coordinating`, or one role at a time with `run_role.py`. After changing a role or a skill, run `uv run factory/harnesses/claude-code/render.py` and commit both.

Each rendered role points to the knowledge base as a wiki (`openwiki/` in this repository), because its role file does, and is given the two read-only wiki tools, `openwiki_search` and `openwiki_read`, from the server `.mcp.json` names `openwiki`. By default that is this package's own read-only server (`tools/wiki_server.py`); to use the OpenWiki tool's server, change the one entry in `render.py` and render again. The per-call check lets a role use those two tools from any server and no other tool of any server.

## What this harness really enforces, and what stays instruction

**Enforced by the platform, when a role is started from its rendered file.**

- The role's tools. A rendered role lists only the tools its role file implies: the coordinating role has no Write or Edit; only the coordinating role may start other roles, and only the three named.
- A fresh context for each subagent. A role started as a subagent or by `run_role.py` begins with its role file and its task and nothing else. That is what gives the review role its distance from the work.

**Enforced by `allow.py`, when Claude Code calls the hook.**

- The role's commands. Bash may run one thing: `uv run tools/<tool>.py <command>` for a command in the role's `may_call`, then that command's own options. The check does not try to read a command the way a shell would, because an independent attack showed that any second reading is a way through (a `#` that the check took for a comment and the shell did not). It refuses outright a command that holds any of `` ` `` `$` `\` `;` `&` `|` `<` `>` `(` `)` `{` `}` `#` `!` or a line break, quoted or not, and anything outside quotes but letters, digits and `_ @ + : , . / = -`. What is left, every shell reads one way. So no role can run the lock or the signature, the review role cannot run a look, only the review role can record a review, and only the coordinating role can name a reviewer.
- The role's options. Each option must be one the tool's own argument parser has for that command, spelled out in full; the check loads the parser to find out, and the tools themselves no longer take a shortened option. So `--b human:someone` is neither let through here nor read as `--by` there.
- The role's name. A `--by` must be `agent:<role>` or `agent:<role>-<suffix>`, so a role cannot act under another role's name or a person's.
- What the role hands to a tool. A file or folder given to a command is checked as a read of it would be, so the review role cannot have a tool read the author's account for it.
- Where the role writes. Write and Edit only on paths matching the role's `writes`, and never on a log, the record of what has been opened, a receipt, a recorded lead or verdict, a role, a skill, a tool or the rendered files.
- Reading a path that an exploration beside it set aside or a study's plan holds out is blocked for Read, Grep and Glob, and so is a search over a folder that holds one. This covers only paths an exploration or a plan declares; data kept somewhere nobody declared is not known to the check.
- Reading a place the role file names under `must_never_see` as `path:<pattern>`. The review role's file names the analysis role's own account of the work two ways: `path:record/analysis/*`, a folder of its own, and `path:record/*analysis*`, flat files such as `record/02-analysis.answer.md`, the layout a run by one instance used. The review role can read neither, in any case of the letters, and cannot search a folder that holds one however far down (a search with no folder named is a search of the folder it stands in, and is judged the same way), nor over a folder too large to walk. This was added after a review assistant, in a run that did not use this harness, saw the author's account by accident and stopped itself; the flat layout and the broad search were added after the independent attack read the author's account through both.

**Enforced by `run_role.py`, whatever the platform does.**

- Each role's task and answer are kept in a folder named for the role; a record anywhere else is refused before anything is started.
- A task for a role that names a path the role must never see is refused before anything is started. It reads the task's text for the place and no further: a task that pastes the author's reasoning in is not caught.

**Tested and not exercised.** `allow.py`, `render.py` and `run_role.py` each test themselves (77, 11 and 10 checks). That Claude Code calls the hook from a subagent's front matter, applies `tools` to a role started with `--agent`, and loads the listed skills was **not exercised**: the environment this was built in could not start Claude Code against a model. Separate assistants have since been run from the role files (historical; the recipe is in `examples/baton-rouge` and the record at the branch `records-2026-11`), but they were started by a coordinating session that gave each one its role file's path and a task, not through this harness: their restrictions were by instruction. Until someone runs it, read "enforced by the platform" and "enforced by `allow.py`" above as "rendered to be enforced". The check itself was attacked once by an independent reviewer, who got a second command, another role's name and the author's account past it; those three are closed and tested, by their author only, and a second independent attack is owed.

**Still instruction, on one machine.**

- No route to held-out data. A script run through `sf.py test` can read anything the machine can reach once it is running. A script run through `explore.py look` runs in a scratch folder that holds only what its command names, and on Linux with Landlock the kernel keeps it from opening anything else of the user's; on any other machine it can open a path it builds itself, and everywhere it can use the network. The hook runs before the call and sees none of that. Only running the analysis role where the held-out values cannot be reached would close this, and that is not built.
- That a Bash command reaches the tool with no shell between. Claude Code hands the command to a shell, and this hook cannot change that; it can only refuse every command a shell could read two ways. The by-hand harness does run the words it checked, with no shell.
- A conversation started without the rendered role (plain `claude` in this repository) is held by nothing here. That is how the one run by separate assistants was made, and its record shows what instruction alone lets through: a look made outside the tool with a plain interpreter, and listings of folders an assistant had been told to keep out of. Both were declared by the assistants that made them.
- That a role with a fresh context has not been told the other role's reasoning: the coordinating role is instructed not to pass it on, and nothing checks what it passes.
- Who is behind a name. `agent:review` is typed, as every name in the study tool is. The exploring tool takes a review only from a name the coordinating role put in the log as reviewer before the lead existed, and this hook lets only the coordinating role do that; outside the hook one author can type both names.
