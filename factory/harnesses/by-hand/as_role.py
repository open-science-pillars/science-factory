#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""as_role: run one command as a role, with no agent platform at all.

The smallest harness. It checks one command against the role file with the
same decision the Claude Code harness uses (factory/harnesses/claude-code/allow.py),
runs it from the repository root when the role file allows it, and adds a
line to a record: the role, the command, whether it was allowed, how it
ended, and the checksum of what it printed.

What it holds and what it does not. It holds the role's commands: a
command the role file does not allow is not run. It gives no fresh
context, because it starts no agent: whoever calls it, a person or one
agent playing several roles in turn, remembers everything. A review
made through this harness is therefore not an independent review, and the
record says which harness was used so that nobody reads it as one.

Usage:
  uv run factory/harnesses/by-hand/as_role.py --role analysis --record DIR/commands.jsonl -- uv run tools/explore.py status --exploration X
  uv run factory/harnesses/by-hand/as_role.py --role review --record DIR/commands.jsonl --write PATH   (asks only whether the role may write PATH)
  uv run factory/harnesses/by-hand/as_role.py --role review --record DIR/commands.jsonl --read PATH    (asks only whether the role may read PATH)
  uv run factory/harnesses/by-hand/as_role.py --selftest
"""
import sys

sys.dont_write_bytecode = True
if __name__ == "__main__" and not (sys.flags.isolated and sys.flags.no_site and "sf-no-bytecode" in str(sys.pycache_prefix)):
    # A clean start. This tool runs itself again in a Python that reads no PYTHON variable, no user site, no start-up
    # file (.pth, sitecustomize) and not the folder this file is in, so that none of those can change what it does.
    # What a hostile environment ran before this line has already run: a stated limit (docs/WHAT-IS-ENFORCED.md).
    import os
    _again = [sys.executable, "-I", "-S", "-B", "-X", "pycache_prefix=" + ("/dev/null/sf-no-bytecode" if os.name == "posix" else os.path.join(os.environ.get("TEMP", "."), f"sf-no-bytecode-{os.getpid()}")), os.path.abspath(__file__), *sys.argv[1:]]
    if os.name == "posix":
        os.execv(sys.executable, _again)
    import subprocess
    sys.exit(subprocess.call(_again))
if __name__ == "__main__":
    # The packages this tool declares, from the environment its interpreter belongs to, put on the import path by
    # hand and last: nothing in that folder is run at start-up.
    import os
    import sysconfig
    _env = os.path.dirname(os.path.dirname(os.path.abspath(sys.executable)))
    _lib = ([os.path.join(_env, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages"),
             os.path.join(_env, "Lib", "site-packages")] if os.path.isfile(os.path.join(_env, "pyvenv.cfg"))
            else [sysconfig.get_paths()["purelib"], sysconfig.get_paths()["platlib"]])
    sys.path += [p for p in dict.fromkeys(_lib) if os.path.isdir(p) and p not in sys.path]

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import shlex
import subprocess
import sys
from pathlib import Path
import importlib.machinery  # noqa: E402
import importlib.util  # noqa: E402


class _SourceOnly(importlib.machinery.SourceFileLoader):
    """A module of this factory is loaded from its source text, compiled here, and never from cached bytecode beside it."""

    def get_code(self, fullname):
        return compile(self.get_data(self.path), self.path, "exec", dont_inherit=True)


def _source_spec(name, path):
    return importlib.util.spec_from_file_location(name, path, loader=_SourceOnly(name, str(path)))


ROOT = Path(__file__).resolve().parent.parent.parent.parent  # the repository: this file is in factory/harnesses/<harness>/
sys.dont_write_bytecode = True  # the decision is loaded from allow.py beside the other harness; no bytecode folder is left there


def decision():
    spec = _source_spec("allow", ROOT / "factory" / "harnesses" / "claude-code" / "allow.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.decide


def selftest() -> int:
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="as-role-selftest-"))
    record = tmp / "commands.jsonl"

    def ask(*words) -> int:
        return subprocess.run([sys.executable, __file__, "--record", str(record), *words], capture_output=True, text=True).returncode

    results = [
        ("the review role is refused a read of the analysis role's own account", ask("--role", "review", "--read", "examples/w/record/analysis/01.answer.md") == 2),
        ("the review role may read the work itself", ask("--role", "review", "--read", "examples/w/explorations/E1/lead.md") == 0),
        ("a role may write in its own place and not in another's",
         ask("--role", "review", "--write", "examples/w/record/review/02.answer.md") == 0 and ask("--role", "review", "--write", "examples/w/record/analysis/02.answer.md") == 2),
        ("a command the role file does not allow is not run", ask("--role", "review", "--", "uv", "run", "tools/explore.py", "look", "--exploration", "x") == 2),
        ("a command with a shortened option is not run: `--b` is not `--by`",
         ask("--role", "analysis", "--", "uv", "run", "tools/explore.py", "note", "--exploration", "x", "--b", "human:someone", "--kind", "missing", "--about", "a", "--text", "b") == 2),
        ("a command is checked and run as its words, with no shell: one that only a shell could make into two is refused as one",
         ask("--role", "review", "--", "uv", "run", "tools/explore.py", "status", "--exploration", "x#x;", "uv", "run", "tools/explore.py", "review") == 2
         and ask("--role", "review", "--", "bash", "-c", "uv run tools/explore.py status --exploration x") == 2),
        ("a command the role file allows is run, and its own answer comes back (here the tool's refusal of a folder with no exploration in it)",
         ask("--role", "review", "--", "uv", "run", "tools/explore.py", "check-log", "--exploration", str(tmp / "none")) == 2
         and '"exit_code": 2' in record.read_text().splitlines()[-1] and '"allowed": true' in record.read_text().splitlines()[-1]),
        ("every answer is kept in the record, refusals included", len(record.read_text().splitlines()) == 9 and '"allowed": false' in record.read_text()),
        ("asking leaves no bytecode folder beside the decision it loads", not (ROOT / "factory" / "harnesses" / "claude-code" / "__pycache__").exists()),
    ]
    record.unlink()
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, good in results if not good]
    for n in failed:
        print("FAIL:", n)
    print(f"selftest: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)} of {len(results)})")
    return 0 if not failed else 1


def main() -> int:
    if sys.argv[1:] == ["--selftest"]:
        return selftest()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    ap.add_argument("--role", required=True)
    ap.add_argument("--record", type=Path, required=True)
    ap.add_argument("--write", default=None, help="a path: ask whether the role may write it, and record the answer")
    ap.add_argument("--read", default=None, help="a path: ask whether the role may read it, and record the answer")
    ap.add_argument("argv", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    decide = decision()
    argv = a.argv[1:] if a.argv and a.argv[0] == "--" else a.argv
    line = {"at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "harness": "by-hand", "role": a.role}
    if a.write:
        why = decide(a.role, {"tool_name": "Write", "tool_input": {"file_path": a.write}, "cwd": str(ROOT)})
        line.update(write=a.write, allowed=why is None, blocked_because=why)
        code = 0 if why is None else 2
    elif a.read:
        why = decide(a.role, {"tool_name": "Read", "tool_input": {"file_path": a.read}, "cwd": str(ROOT)})
        line.update(read=a.read, allowed=why is None, blocked_because=why)
        code = 0 if why is None else 2
    else:
        # the command is checked as the words it is and run as those words, with no shell between: nothing reads it a second way
        why = decide(a.role, {"tool_name": "Run", "tool_input": {"argv": argv}, "cwd": str(ROOT)})
        line.update(command=shlex.join(argv), argv=argv, allowed=why is None, blocked_because=why)
        code = 2
        if why is None:
            done = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, stdin=subprocess.DEVNULL)
            sys.stdout.write(done.stdout)
            sys.stderr.write(done.stderr)
            code = done.returncode
            line.update(exit_code=code, output_sha256=hashlib.sha256((done.stdout + done.stderr).encode()).hexdigest())
    if why is not None:
        print(f"Blocked by the role file (factory/agents/{a.role}/agent.md): {why}", file=sys.stderr)
    a.record.parent.mkdir(parents=True, exist_ok=True)
    with a.record.open("a") as f:
        f.write(json.dumps(line) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
