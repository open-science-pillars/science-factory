# Runners

A runner starts a role from its file in `assistants/` with that role's tools. The roles do not depend on any runner.

- `claude-code/`: Claude Code subagents and skills. Rendered files, a per-call check, a fresh context for each role, each role's record in its own place. Its README says what it is built to enforce and what stays instruction. It has not been exercised against Claude Code.
- `by-hand/`: one command, one write or one read at a time, checked against the role file with the same decision, with no assistant started and so no fresh context. For a person, or for one assistant playing the roles in turn, and for seeing what a role file allows.

A third way has been used once and is not a runner: a coordinating session started each role as a separate subagent and gave it the path of its role file and a task. That gives fresh contexts and holds a role to its file by instruction only. `examples/baton-rouge/README.md` says what that did and did not show; the record of that run is at the branch `records-2026-11`.
