# The harness for Claude Code

This harness starts each agent as a Claude Code subagent with its skills, and checks every tool call it makes against its file. The agents and skills themselves are the files in `factory/agents/` and `factory/skills/`; nothing an agent needs is defined here. **Claude Code has never run it**: the scripts test themselves, and nothing more has been shown.

| File | What it does |
|---|---|
| `render.py` | writes `.claude/agents/<name>.md`, `.claude/skills/<name>/` and `.mcp.json` from the agent and skill files; `--check` fails when what is on disk is missing, stale, edited by hand, or has no source |
| `allow.py` | the per-call check: the decision each tool call of an agent gets, read from its file at the time of the call; each rendered agent carries it as a PreToolUse hook |
| `run_role.py` | starts one agent in a fresh context (`claude -p --agent <name>`) and keeps its task, its answer and the model that ran it in its own place, `record/<name>/` |
| `harness.yaml` | the models an agent may declare under this harness, and what it holds |

The rendered files are committed, so the repository works when opened in Claude Code: start the coordinating agent with `claude --agent coordinating`, or one agent at a time with `run_role.py`. After changing an agent or a skill, run `uv run factory/harnesses/claude-code/render.py` and commit both. Each rendered agent is given the two read-only wiki tools, `openwiki_search` and `openwiki_read`, from the server `.mcp.json` names `openwiki` (by default `tools/wiki_server.py`). `.mcp.json` also names `factory` (`tools/factory_server.py`), for a scientist's own session ([docs/USING-IT-FROM-CLAUDE.md](../../../docs/USING-IT-FROM-CLAUDE.md)); no rendered agent is given its tools, and `allow.py` blocks them for every agent.

**What the check holds**, when Claude Code calls it, is list 2 of `docs/WHAT-IS-ENFORCED.md`: an agent runs only the commands its file lists, as one plain line with every option spelled out, under its own name and declared model; it writes only where its file says; it cannot read what its file says it must never see, or have a tool read it for it; no agent may lock, sign, record a merge or pass `--people-not-verified`. Bash commands holding any sign a shell acts on are refused outright, because an attack showed a second reading of a command is a way through (R1-02 in `docs/reviews/README.md`).

**What stays instruction**, even with the check: a script run through a look or a plan's step can use the network and, without the kernel fence, open a path it builds; Claude Code hands each command to a shell, which this hook cannot change; a conversation started without the rendered agent (plain `claude`) is held by nothing here; and whether the coordinating agent passed the reviewer anything the author said is not checked.

```
uv run factory/harnesses/claude-code/render.py --check
uv run factory/harnesses/claude-code/render.py --selftest
uv run factory/harnesses/claude-code/allow.py --selftest
uv run factory/harnesses/claude-code/run_role.py --selftest
```
