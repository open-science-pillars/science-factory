# Harnesses

A harness starts an agent from its file (`factory/agents/<name>/agent.md`) and holds it to that file while it works, or carries the two acts by people. The agent files depend on no harness. Each harness has a `harness.yaml` that says what it starts, which models an agent's file may declare under it, and what it holds as against what stays instruction; `tools/check_factory.py` checks each agent's harness and model against it. What each one enforces is in list 2 and list 3 of `docs/WHAT-IS-ENFORCED.md`.

- `claude-code/`: Claude Code subagents and skills, rendered from the agent files, with a per-call check and a fresh context for each agent. Claude Code has never run it.
- `github/`: starts no agent. It carries the lock and the signature as pull requests on GitHub, and asks GitHub who approved. It has never run on GitHub.
- `by-hand/`: the same per-call check for one command, one write or one read at a time, with no agent started: for a person, or one agent playing each part in turn, and for seeing what an agent file allows.
