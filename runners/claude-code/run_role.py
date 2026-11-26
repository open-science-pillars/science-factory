#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""run_role: start one role as a Claude Code assistant in a fresh context, and keep the record.

It runs `claude -p --agent <role>` from the repository root with the task
given to it, so the role starts from its rendered role file with that
file's tools and hook, and with no memory of any other conversation. It
writes what the brief of a working example asks to be kept: the task as it
was given, what the assistant answered, which model ran it, and when.

Usage:
  uv run runners/claude-code/run_role.py --role analysis --task-file TASK.md --record DIR/NN-analysis
  uv run runners/claude-code/run_role.py --selftest

`--record` names a path without extension: the task is copied to
<record>.task.md, the answer goes to <record>.answer.md, and what ran goes
to <record>.run.json. `--claude` names the Claude Code program (default
`claude`).
"""
import argparse
import datetime as dt
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def run(role: str, task: str, record: Path, claude: str, root: Path = ROOT) -> int:
    if not (root / ".claude" / "agents" / f"{role}.md").is_file():
        print(f"there is no rendered role .claude/agents/{role}.md; run runners/claude-code/render.py", file=sys.stderr)
        return 2
    record.parent.mkdir(parents=True, exist_ok=True)
    Path(f"{record}.task.md").write_text(task)
    started = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        done = subprocess.run([claude, "-p", "--agent", role, "--output-format", "json"], input=task, cwd=root,
                              capture_output=True, text=True)
    except OSError as e:
        print(f"could not start `{claude}`: {e}", file=sys.stderr)
        return 2
    try:
        out = json.loads(done.stdout)
    except ValueError:
        out = {"is_error": True, "result": done.stdout + done.stderr}
    answer = str(out.get("result") or "")
    models = sorted((out.get("modelUsage") or {}).keys())
    failed = bool(out.get("is_error")) or done.returncode != 0
    Path(f"{record}.answer.md").write_text(answer + ("\n" if not answer.endswith("\n") else ""))
    Path(f"{record}.run.json").write_text(json.dumps({
        "role": role, "runner": "claude-code", "started_from": f".claude/agents/{role}.md", "fresh_context": True,
        "models": models, "started": started, "finished": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "turns": out.get("num_turns"), "failed": failed, "claude_session": out.get("session_id")}, indent=1) + "\n")
    print(answer)
    if failed:
        print(f"the {role} assistant did not finish: {answer[:200]}", file=sys.stderr)
        return 1
    return 0


def selftest() -> int:
    results = []
    tmp = Path(tempfile.mkdtemp(prefix="run-role-selftest-")).resolve()
    try:
        (tmp / ".claude" / "agents").mkdir(parents=True)
        (tmp / ".claude" / "agents" / "review.md").write_text("---\nname: review\n---\n")
        fake = tmp / "fake-claude"
        fake.write_text("#!/bin/sh\ncat > \"$PWD/seen-task.txt\"\necho \"$@\" > \"$PWD/seen-args.txt\"\n"
                        "echo '{\"result\": \"two holes found\", \"modelUsage\": {\"claude-test-1\": {}}, \"num_turns\": 3, \"is_error\": false}'\n")
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
        code = run("review", "Check EXPLORATION-1.", tmp / "record" / "03-review", str(fake), tmp)
        meta = json.loads((tmp / "record" / "03-review.run.json").read_text())
        results.append(("a role runs and its answer is kept", code == 0 and (tmp / "record/03-review.answer.md").read_text().strip() == "two holes found"))
        results.append(("the task is kept as it was given", (tmp / "record/03-review.task.md").read_text() == "Check EXPLORATION-1." and (tmp / "seen-task.txt").read_text() == "Check EXPLORATION-1."))
        results.append(("the role is started from its role file, in print mode", (tmp / "seen-args.txt").read_text().split()[:3] == ["-p", "--agent", "review"]))
        results.append(("the model that ran the role is recorded", meta["models"] == ["claude-test-1"] and meta["role"] == "review"))
        results.append(("a role with no rendered file is refused", run("auditing", "x", tmp / "record" / "04", str(fake), tmp) == 2))
        bad = tmp / "bad-claude"
        bad.write_text("#!/bin/sh\necho '{\"result\": \"Authentication error\", \"is_error\": true}'\n")
        bad.chmod(bad.stat().st_mode | stat.S_IXUSR)
        results.append(("a run that fails is recorded as failed and returns an error",
                        run("review", "x", tmp / "record" / "05-review", str(bad), tmp) == 1 and json.loads((tmp / "record/05-review.run.json").read_text())["failed"]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, good in results if not good]
    for n in failed:
        print("FAIL:", n)
    print(f"selftest: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)} of {len(results)})")
    return 0 if not failed else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--role")
    ap.add_argument("--task-file", type=Path)
    ap.add_argument("--record", type=Path)
    ap.add_argument("--claude", default=os.environ.get("CLAUDE_BIN", "claude"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.role and a.task_file and a.record):
        ap.error("--role, --task-file and --record are required")
    return run(a.role, a.task_file.read_text(), a.record.resolve(), a.claude)


if __name__ == "__main__":
    sys.exit(main())
