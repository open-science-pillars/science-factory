# Runners

A runner starts a role from its file in `assistants/` with that role's tools. The roles do not depend on any runner.

- `claude-code/`: Claude Code subagents and skills. Rendered files, a per-call check, a fresh context for each role. Its README says what it enforces and what stays instruction.
- `by-hand/`: one command at a time, checked against the role file with the same decision, with no assistant started and so no fresh context. For a person, or for one assistant playing the roles in turn, and for seeing what a role file allows.
