#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""check_old_records: do the records made before the layout changed still
say what they said?

Some study logs in this repository were written when the tools and the
method sat together in one folder. A log is chained by hash and names the
code it ran by path and checksum, and it is never rewritten. This check
answers two questions about those records, and edits nothing.

  1. The table. factory/moved-files.yaml lists every file a record names
     by an old path, where it stands now, and its checksum on the day of
     the move. Each line is checked against the file on disk. A file whose
     bytes changed with the move must be listed as changed, with a reason,
     and its earlier bytes must be kept, with the recorded checksum.

  2. The replay. The old layout is rebuilt in a scratch folder from the
     table: each moved file at its old path (its earlier bytes where they
     are kept), each record where it stood. The study tool as it stood then
     is asked for `check-log` and `status` on each record, and its answers
     are compared, byte for byte, with the answers it gave before the move
     (studies/exhibits/as-recorded/before-the-move/). The rebuilt layout is
     committed in a throwaway repository first (this needs `git`), as the
     records were committed when those answers were given.

Most of the replay depends on the hydrology and nasa-daac-knowledge
checkouts, because the records name files in them: a status compares their
checksums, and the log check of a plan that runs one of their scripts
reads the plan. With both beside this repository all seven answers are
compared. Without them only the log check of the system trial's practice
run is, and the rest are reported as not run, never as passed.

What this does not show: that the study tool of today would count the old
test runs. It does not, and should not, because the study tool itself
changed with the move; `tools/sf.py status` on those records says so.

Usage:
  check_old_records.py [--keep DIR]
  check_old_records.py --selftest
"""
import sys

sys.dont_write_bytecode = True

import argparse
import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
TABLE = REPO / "factory" / "moved-files.yaml"
BEFORE = REPO / "studies" / "exhibits" / "as-recorded" / "before-the-move"
BESIDE = ("hydrology", "nasa-daac-knowledge")


def sha(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def table_problems(repo: Path, table: dict) -> tuple:
    """(problems, the files whose bytes changed with the move). A problem is a line of the table that the
    files on disk do not bear out."""
    problems, changed = [], []
    for then, e in table["files"].items():
        now = repo / e["now"]
        if not now.is_file():
            problems.append(f"{then}: the table says it stands at {e['now']}, and no file is there")
        elif sha(now) == e["sha256"]:
            if "kept_as" in e or "changed" in e:
                problems.append(f"{then}: listed as changed, and {e['now']} has the checksum of the day of the move")
        else:
            kept = repo / e["kept_as"] if e.get("kept_as") else None
            if not e.get("changed") or kept is None:
                problems.append(f"{then}: {e['now']} does not have the recorded checksum, and the table does not list it as changed")
            elif sha(kept) != e["sha256"]:
                problems.append(f"{then}: the earlier bytes kept at {e['kept_as']} do not have the recorded checksum")
            else:
                changed.append(then)
    for now, then in table["studies"].items():
        if not (repo / now).is_dir():
            problems.append(f"{then}: the table says the record stands at {now}, and no folder is there")
    return problems, changed


def rebuild(repo: Path, table: dict, scratch: Path) -> Path:
    """The old layout in a scratch folder: `scratch/science-factory` with each moved file at its old path and
    each record where it stood, and the two checkouts the records name beside it when they are beside this one."""
    old = scratch / "science-factory"
    for then, now in table["folders"].items():
        shutil.copytree(repo / now, old / then, ignore=shutil.ignore_patterns("as-recorded", "__pycache__"))
    for then, e in table["files"].items():
        (old / then).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / (e.get("kept_as") or e["now"]), old / then)
    for name in BESIDE:
        if (repo.parent / name).is_dir():
            os.symlink((repo.parent / name).resolve(), scratch / name, target_is_directory=True)
    # The answers before the move were given in a repository with the records committed, and the log check
    # remarks on a study that is in no repository at all. So the rebuilt layout is committed too, in a
    # repository of its own that is thrown away with the scratch folder.
    for args in (["init", "-q"], ["add", "-A"], ["-c", "user.name=check-old-records", "-c", "user.email=check@example.invalid",
                                                 "-c", "commit.gpgsign=false", "commit", "-q", "-m", "the old layout, rebuilt"]):
        subprocess.run(["git", "-C", str(old), *args], check=True, capture_output=True, stdin=subprocess.DEVNULL)
    return old


def ask(old: Path, tool: str, *args) -> str:
    done = subprocess.run([sys.executable, str(old / tool), *args], capture_output=True, text=True, stdin=subprocess.DEVNULL,
                          cwd=old.parent, env={k: v for k, v in os.environ.items() if not k.startswith(("PYTHON", "SF_"))})
    return done.stdout + done.stderr


def replay(repo: Path, table: dict, before: Path, scratch: Path) -> tuple:
    """(lines to print, how many comparisons failed, how many were not run)."""
    old = rebuild(repo, table, scratch)
    beside = all((scratch / name).is_dir() for name in BESIDE)
    lines, failed, not_run = [], 0, 0
    for r in table["records"]:
        study = str(old / r["stood_at"])
        alone = beside or not r.get("plan_names_the_checkouts")
        asks = [("check_log", ("check-log", "--study", study), alone),
                ("check_log_with_change_log", ("check-log", "--study", study, "--change-log", str(old / "mvp" / "change-log.jsonl")), alone),
                ("status", ("status", "--study", study), beside)]
        for key, args, can in asks:
            if key not in r:
                continue
            what = f"{r['stood_at']}: {args[0]}" + (" with the change log" if "--change-log" in args else "")
            if not can:
                not_run += 1
                lines.append(f"NOT RUN  {what} (it reads files of the hydrology and nasa-daac-knowledge checkouts, which are not beside this repository)")
                continue
            same = ask(old, "mvp/sf.py", *args) == (before / r[key]).read_text()
            failed += not same
            lines.append(f"{'SAME    ' if same else 'DIFFERS '} {what}")
    return lines, failed, not_run


def run(repo: Path, keep: Path | None) -> int:
    table = yaml.safe_load((repo / "factory" / "moved-files.yaml").read_text())
    problems, changed = table_problems(repo, table)
    for p in problems:
        print(f"TABLE    {p}")
    same = len(table["files"]) - len(changed)
    print(f"the table: {same} of {len(table['files'])} moved files have the checksum of the day of the move; "
          f"{len(changed)} changed with the move and are kept as they were ({', '.join(changed) or 'none'})")
    if problems:
        print(f"check-old-records: FAIL ({len(problems)} line(s) of the table are not borne out by the files)")
        return 1
    with tempfile.TemporaryDirectory(prefix="old-layout-") as tmp:
        scratch = Path(keep).resolve() if keep else Path(tmp).resolve()
        scratch.mkdir(parents=True, exist_ok=True)
        lines, failed, not_run = replay(repo, table, repo / "studies" / "exhibits" / "as-recorded" / "before-the-move", scratch)
    print("\n".join(lines))
    done = len(lines) - not_run
    if failed:
        print(f"check-old-records: FAIL ({failed} of {done} answers differ from the answers given before the move)")
        return 1
    print(f"check-old-records: PASS ({done} of {done} answers are, byte for byte, the answers given before the move"
          + (f"; {not_run} not run" if not_run else "") + "). The study tool that answered is the one kept as recorded, in the old layout "
          "rebuilt from the table")
    return 0


def selftest() -> int:
    results = []

    def check(name: str, ok: bool) -> None:
        results.append((name, bool(ok)))
        print(("PASS  " if ok else "FAIL  ") + name)

    table = yaml.safe_load(TABLE.read_text())
    with tempfile.TemporaryDirectory(prefix="old-records-selftest-") as tmp:
        tmp = Path(tmp).resolve()
        copy = tmp / "copy"
        shutil.copytree(REPO, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", ".claude"))
        problems, changed = table_problems(copy, table)
        check("the table as it ships is borne out by the files, and lists as changed exactly the study tool and the system trial's script",
              problems == [] and sorted(changed) == ["mvp/sf.py", "mvp/system_trial.py"])
        gain = copy / "methods" / "gain" / "gain.py"
        text = gain.read_text()
        gain.write_text(text + "# one more line\n")
        check("a moved file that changed without the table saying so is a problem",
              any("mvp/gain.py" in p and "does not have the recorded checksum" in p for p in table_problems(copy, table)[0]))
        lines, failed, _ = replay(copy, table, BEFORE, tmp / "replay-changed")
        check("and the replay then differs where the record named that file",
              failed >= 1 or all(line.startswith("NOT RUN") for line in lines if ": status" in line))  # a status names it, and needs the checkouts
        gain.write_text(text)
        kept = copy / "studies" / "exhibits" / "as-recorded" / "sf.py"
        kept.write_text(kept.read_text() + "# one more line\n")
        check("earlier bytes that are not the recorded ones are a problem",
              any("mvp/sf.py" in p and "kept at" in p for p in table_problems(copy, table)[0]))
        log = copy / "studies" / "exhibits" / "system-trial-ready-STUDY-0000" / "study-log.jsonl"
        shutil.copyfile(REPO / "studies" / "exhibits" / "as-recorded" / "sf.py", kept)
        log.write_text(log.read_text().replace("agent:practice-analysis", "agent:practice-analyst", 1))
        lines, failed, _ = replay(copy, table, BEFORE, tmp / "replay-edited")
        check("a record whose log was edited no longer gives the answers it gave before the move",
              failed >= 1 and any(line.startswith("DIFFERS") and "system-trial-ready-STUDY-0000: check-log" in line for line in lines))
    good = all(ok for _, ok in results)
    print(f"selftest: {'PASS' if good else 'FAIL'} ({sum(ok for _, ok in results)} of {len(results)})")
    return 0 if good else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    ap.add_argument("--keep", type=Path, help="rebuild the old layout in this folder and leave it there to look at")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    return selftest() if a.selftest else run(REPO, a.keep)


if __name__ == "__main__":
    sys.exit(main())
