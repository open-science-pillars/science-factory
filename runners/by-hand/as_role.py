#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""as_role: run one command as a role, with no agent platform at all.

The smallest runner. It checks one command against the role file with the
same decision the Claude Code runner uses (runners/claude-code/allow.py),
runs it from the repository root when the role file allows it, and adds a
line to a record: the role, the command, whether it was allowed, how it
ended, and the checksum of what it printed.

What it holds and what it does not. It holds the role's commands: a
command the role file does not allow is not run. It gives no fresh
context, because it starts no assistant: whoever calls it, a person or one
assistant playing several roles in turn, remembers everything. A review
made through this runner is therefore not an independent review, and the
record says which runner was used so that nobody reads it as one.

Usage:
  uv run runners/by-hand/as_role.py --role analysis --record DIR/commands.jsonl -- uv run mvp/loops/explore.py status --exploration X
  uv run runners/by-hand/as_role.py --role review --record DIR/commands.jsonl --write PATH   (asks only whether the role may write PATH)
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def decision():
    spec = importlib.util.spec_from_file_location("allow", ROOT / "runners" / "claude-code" / "allow.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.decide


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--role", required=True)
    ap.add_argument("--record", type=Path, required=True)
    ap.add_argument("--write", default=None, help="a path: ask whether the role may write it, and record the answer")
    ap.add_argument("argv", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    decide = decision()
    argv = a.argv[1:] if a.argv and a.argv[0] == "--" else a.argv
    line = {"at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "runner": "by-hand", "role": a.role}
    if a.write:
        why = decide(a.role, {"tool_name": "Write", "tool_input": {"file_path": a.write}, "cwd": str(ROOT)})
        line.update(write=a.write, allowed=why is None, blocked_because=why)
        code = 0 if why is None else 2
    else:
        command = shlex.join(argv)
        why = decide(a.role, {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(ROOT)})
        line.update(command=command, allowed=why is None, blocked_because=why)
        code = 2
        if why is None:
            done = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, stdin=subprocess.DEVNULL)
            sys.stdout.write(done.stdout)
            sys.stderr.write(done.stderr)
            code = done.returncode
            line.update(exit_code=code, output_sha256=hashlib.sha256((done.stdout + done.stderr).encode()).hexdigest())
    if why is not None:
        print(f"Blocked by the role file (assistants/{a.role}.md): {why}", file=sys.stderr)
    a.record.parent.mkdir(parents=True, exist_ok=True)
    with a.record.open("a") as f:
        f.write(json.dumps(line) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
