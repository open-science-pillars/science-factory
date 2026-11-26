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
  uv run factory/harnesses/claude-code/run_role.py --role analysis --task-file TASK.md --record DIR/record/analysis/NN
  uv run factory/harnesses/claude-code/run_role.py --selftest

`--record` names a path without extension: the task is copied to
<record>.task.md, the answer goes to <record>.answer.md, and what ran goes
to <record>.run.json. `--claude` names the Claude Code program (default
`claude`).

Each role's account has its own place. The record of a role goes in a
folder named for the role (`record/analysis/01`, `record/review/02`), and
this script refuses any other place, so that the account of the assistant
that did the work never sits where the assistant that checks it writes.
It also refuses a task that names a path the role file lists under
`must_never_see` as `path:<pattern>`: a task for the review role that
points at `record/analysis/` hands the reviewer the author's account, and
is not started.
"""
import argparse
import datetime as dt
import fnmatch
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent  # the repository: this file is in factory/harnesses/<harness>/


def never_seen(role: str, root: Path) -> list:
    """The `path:<pattern>` entries under `must_never_see` in the role file, read without a YAML library."""
    f = root / "factory" / "agents" / role / "agent.md"
    head = f.read_text(encoding="utf-8").split("\n---\n", 1)[0] if f.is_file() else ""
    return [m.strip() for m in re.findall(r"""^\s*-\s*["']?path:([^"'\n]+)""", head, re.M)]


def names_place(posix: str, pat: str) -> bool:
    """Does a path lie at, or below, a place a pattern names? Matched piece by piece against every run of folders in
    the path, in any case: the same reading the per-call check makes (allow.py), kept here so this script needs
    nothing beside it."""
    parts = [q for q in posix.casefold().split("/") if q]
    for want in {pat.casefold(), pat.casefold().removesuffix("/*")}:
        pieces = [q for q in want.split("/") if q]
        for start in range(0, len(parts) - len(pieces) + 1):
            if all(fnmatch.fnmatchcase(parts[start + k], pieces[k]) for k in range(len(pieces))):
                return True
    return False


def run(role: str, task: str, record: Path, claude: str, root: Path = ROOT) -> int:
    if not (root / ".claude" / "agents" / f"{role}.md").is_file():
        print(f"there is no rendered role .claude/agents/{role}.md; run factory/harnesses/claude-code/render.py", file=sys.stderr)
        return 2
    if record.parent.name != role:
        print(f"the record of the {role} role goes in a folder named `{role}` (for example record/{role}/{record.name}), not in "
              f"`{record.parent.name}/`: each role's account has its own place, so that one role's account never sits where "
              "another role writes", file=sys.stderr)
        return 2
    for word in re.findall(r"""[^\s'"`<>()\[\]{},;]+""", task.replace("\\", "/")):
        for pat in never_seen(role, root):
            if "/" in word and names_place(word.rstrip(".:"), pat):
                print(f"the task names `{word}`, which the {role} role must never see (factory/agents/{role}/agent.md, must_never_see: {pat}). "
                      "Give this role the work as files and nothing the other assistant said about it; the task is not started", file=sys.stderr)
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
        (tmp / "factory" / "agents" / "review").mkdir(parents=True)
        (tmp / "factory" / "agents" / "review" / "agent.md").write_text('---\ndescription: review\nmust_never_see:\n  - "held-out data"\n  - "path:record/analysis/*"\n  - "path:record/*analysis*"\n---\n\nbody\n')
        code = run("review", "Check EXPLORATION-1.", tmp / "record" / "review" / "03", str(fake), tmp)
        meta = json.loads((tmp / "record" / "review" / "03.run.json").read_text())
        results.append(("a role runs and its answer is kept, in the role's own place", code == 0 and (tmp / "record/review/03.answer.md").read_text().strip() == "two holes found"))
        results.append(("the task is kept as it was given", (tmp / "record/review/03.task.md").read_text() == "Check EXPLORATION-1." and (tmp / "seen-task.txt").read_text() == "Check EXPLORATION-1."))
        results.append(("a record outside the role's own folder is refused, and nothing is started",
                        run("review", "x", tmp / "record" / "analysis" / "04", str(fake), tmp) == 2 and run("review", "x", tmp / "record" / "04-review", str(fake), tmp) == 2
                        and not (tmp / "record" / "analysis").exists()))
        (tmp / "seen-task.txt").unlink()
        results.append(("a task that hands the review role the author's account is refused, and nothing is started",
                        run("review", "Check EXPLORATION-1. The author's notes are in examples/w/record/analysis/01.answer.md.", tmp / "record" / "review" / "06", str(fake), tmp) == 2
                        and not (tmp / "seen-task.txt").exists() and not (tmp / "record/review/06.task.md").exists()))
        results.append(("a task that names the author's account where a run keeps it as a flat file in record/ is refused too",
                        run("review", "Check EXPLORATION-1; see examples/demo/record/02-analysis.answer.md.", tmp / "record" / "review" / "07", str(fake), tmp) == 2
                        and run("review", "Read `examples/w/Record/04-Analysis-second.answer.md`", tmp / "record" / "review" / "07", str(fake), tmp) == 2
                        and not (tmp / "seen-task.txt").exists() and not (tmp / "record/review/07.task.md").exists()))
        results.append(("a review task that names the work, and the reviewer's own earlier account, is started",
                        run("review", "Check examples/w/explorations/E1 again; your earlier review is examples/w/record/review/02.answer.md.",
                            tmp / "record" / "review" / "08", str(fake), tmp) == 0))
        results.append(("the role is started from its role file, in print mode", (tmp / "seen-args.txt").read_text().split()[:3] == ["-p", "--agent", "review"]))
        results.append(("the model that ran the role is recorded", meta["models"] == ["claude-test-1"] and meta["role"] == "review"))
        results.append(("a role with no rendered file is refused", run("auditing", "x", tmp / "record" / "auditing" / "04", str(fake), tmp) == 2))
        bad = tmp / "bad-claude"
        bad.write_text("#!/bin/sh\necho '{\"result\": \"Authentication error\", \"is_error\": true}'\n")
        bad.chmod(bad.stat().st_mode | stat.S_IXUSR)
        results.append(("a run that fails is recorded as failed and returns an error",
                        run("review", "x", tmp / "record" / "review" / "05", str(bad), tmp) == 1 and json.loads((tmp / "record/review/05.run.json").read_text())["failed"]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, good in results if not good]
    for n in failed:
        print("FAIL:", n)
    print(f"selftest: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)} of {len(results)})")
    return 0 if not failed else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
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
