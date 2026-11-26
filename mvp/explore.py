#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""explore: the exploring tool. It keeps the exploration log and holds the fence.

Exploring is looking at data to find out what is there. This tool does not
slow that down and holds no opinion about what is found. It runs no language
model. It makes five things true, whoever or whatever is exploring:

  1. Data is set aside first. `start` records what will not be looked at
     (a window, sites, a release) before anything is looked at, and writes
     it to the record a later confirming study respects: the record of what
     has been opened, beside the studies (openings.jsonl), which the study
     tool reads. The data that will be explored is written there too, as
     explored, so the study tool treats it as already seen.
  2. Every look is logged: what was run, on which data by checksum, and
     what came out, in a log that is only ever added to and is chained by
     hash like the study log (the same code: this tool imports sf.py).
     A look that names what was set aside is refused, and the refusal is
     logged.
  3. Choices are recorded as they are made: the choice, the alternatives,
     and what it rests on.
  4. It ends in a lead, a note, a method or a stop. A lead says what looks
     true, how it was found, how many things were tried (counted from the
     log, not remembered), which choices would change it, and a proposed
     plan for a confirming study. `hand-over` writes what `sf.py start`
     needs, and `check-study` refuses a study whose held-out data is not
     inside what was set aside or touches what was explored.
  5. Everything it writes says "exploring" on it. There is no command here
     that signs anything, and a lead is never a finding.

An exploration is one directory: exploration-log.jsonl, set-aside.json,
request.md, the scripts of its looks, receipts/, notes/, verdicts/, the
lead, and hand-over/. By convention explorations sit in `explorations/`
beside `studies/`, and the record is `studies/openings.jsonl`.

Commands.

  start          set data aside, bind the request, write the record
  known          list the knowledge that bears on the question (calls
                 knowledge.py) and log what was listed; the first look is
                 refused until this has run
  read           say which concepts were read and what each changes
  look           run one script on working data; logged with checksums
  recheck        run a logged look again, in a copy, and compare the output;
                 adds nothing to the log (for the review assistant)
  choice         a choice, its alternatives, what it rests on
  note           something missing or wrong in the data or the knowledge
  lead           record the lead from a lead file (YAML)
  review         a review assistant that did none of the exploring records
                 whether it found holes
  end            ended as a lead, a note, a method or a stop
  hand-over      what `sf.py start` needs, for a confirming study
  check-study    a study started from the lead keeps the fence
  curation-list  open notes, for the curating assistant
  resolve        a note is drafted, linked or declined
  status         where the exploration stands and who is next
  check-log      everything re-checked from the files
  fingerprint    the log's fingerprint, to post outside the workspace
  selftest       the tool tests itself, attacks included

What a look is. A launcher the study tool knows (`{python}` followed by a
script file, or `uv run` followed by a script file), then the script's own
arguments, exactly as in a plan. It runs in the exploration directory with
the environment the study tool builds for a command.

What the fence checks, and what it cannot. Before a look runs, the tool
reads every word of the command and every existing file the command names.
It refuses a word that is a set-aside path, a set-aside site or release, or
a date inside the set-aside window; a script or text file that names any
of those; and a JSON data file whose `window`, or whose values under the
time keys declared at the start, fall inside the set-aside window. After a
look it reads every file the look left in the exploration directory the
same way, and a file that crosses the fence spoils the exploration: no
lead and no hand-over can come from it. What it cannot do is the first
limit of the study tool, repeated here plainly: it cannot stop a script
from reading public data from somewhere the command does not name, such
as the network. Against that the barrier is instruction and the log.
Names of who did what are typed, not proven, as in the study tool.

Usage: explore.py <command> --exploration DIR [...]; explore.py selftest
"""
import sys

sys.dont_write_bytecode = True
if __name__ == "__main__" and not sys.flags.safe_path and sys.path:
    _own = __file__.replace("\\", "/").rpartition("/")[0]
    del sys.path[0]
    sys.path[:] = [p for p in sys.path if p != _own]

import argparse  # noqa: E402
import datetime as dt  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402

HERE = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    """Another tool of this package, loaded by its path: nothing is copied, and nothing beside this file
    can stand in for it by name."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


sf = _load("sf", HERE / "sf.py")  # the log chain, the record of what has been opened, the launcher rule
Refused = sf.Refused

WAY = "exploring"
LEAD_STATUS = "a lead, not a finding: found by exploring, tested on nothing, and it cannot be signed"
BANNER = ("**Exploring.** This is a lead, not a finding. It was found by looking at data, every choice in it was made "
          "after looking, and it has been tested on nothing. It cannot be signed. To become a finding it goes through "
          "a confirming study on the data that was set aside.")
HOW = {  # the ways to hold data out that TWO-WAYS-OF-WORKING.md lists, and what each has to name
    "a later period": "window",
    "a period of contrasting conditions": "window",
    "sites never opened": "sites",
    "a new release": "releases",
    "a different instrument or record": "releases",
    "forecasts scored later": "window",
}
OPEN_END = "9999-12-31"
TIME_KEYS = ("time", "t", "date", "datetime", "timestamp")
DATE = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
NOTE_KINDS = ("missing", "wrong", "stale", "contradiction", "method", "dead-end")
OUTCOMES = ("lead", "note", "method", "stop")
VERDICTS = ("holes-found", "no-holes-found")
DISPOSITIONS = ("drafted", "linked", "declined")
NOT_THE_WORK = ("review.verdict", "note.resolved", "handed.over")  # kinds that do not make their actor part of the exploring
AFTER_END = ("note.resolved", "handed.over", "review.verdict")
LEAD_KEYS = ("what_looks_true", "how_it_was_found", "evidence", "choices_that_would_change_it", "choices_that_would_not",
             "pitfalls", "proposed_plan")
PLAN_STUB_KEYS = ("question", "quantity_estimated", "difference_that_matters", "rule_sketch")


class Exploration(sf.Study):
    """An exploration is a directory with a log, like a study; the log is the study tool's chain under another name."""

    def __init__(self, d):
        super().__init__(d)
        self.log = self.d / "exploration-log.jsonl"
        self.set_aside_path = self.d / "set-aside.json"

    def add(self, actor: str, kind: str, data: dict) -> dict:
        self.check_actor(actor)
        with self.held() as f:
            ev = self.read_held(f)
            if any(e["kind"] == "exploration.ended" for e in ev) and kind not in AFTER_END:
                raise Refused("this exploration has ended; a new question is a new exploration that cites it")
            return self._append(f, actor, kind, {"way": WAY, **data})

    def started(self) -> dict:
        ev = self.events()
        if not ev or ev[0]["kind"] != "exploration.started":
            raise Refused("this exploration is not started: `start` sets data aside before anything is looked at")
        return ev[0]

    def set_aside(self) -> dict:
        return self.started()["data"]["set_aside"]

    def record(self) -> Path:
        """The record of what has been opened that this exploration wrote to, beside the studies."""
        return Path(os.path.normpath(self.d / self.started()["data"]["record"]["path_from_exploration"]))


# ---- small helpers --------------------------------------------------------
def write_json(p: Path, obj: dict) -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"way": WAY, **obj}, indent=1, sort_keys=False) + "\n")
    return sf.sha_file(p)


def parse_window(text: str | None) -> dict | None:
    """START:END as two ISO dates; an empty END means the window is open and runs on from START."""
    if not text:
        return None
    a, _, b = str(text).partition(":")
    w = sf.window_of({"start": a.strip(), "end": (b.strip() or OPEN_END)})
    if w is None:
        raise Refused(f"`{text}` is not a window: write START:END as dates (2025-04-28:2026-04-27), or START: for one that stays open")
    return {**w, "open_ended": not b.strip()} if not b.strip() else w


def parse_subject(text: str) -> dict:
    """key=value,key=value: the thing the data is about, in the same form as a plan's `pair`."""
    out = {}
    for part in str(text or "").split(","):
        k, eq, v = part.partition("=")
        if not eq or not k.strip() or not v.strip():
            raise Refused("`--subject` is key=value,key=value (for example reach_id=74210000331,gauge=USGS-07374000): "
                          "the same keys a plan's `pair` will carry, because the record matches on them")
        out[k.strip()] = v.strip()
    return out


def core(w) -> dict | None:
    """A window as the study tool reads one: its two dates and nothing else."""
    return {"start": w["start"], "end": w["end"]} if isinstance(w, dict) and "start" in w and "end" in w else w


def subject_key(subject: dict) -> str:
    return sf.subject_key({}, {"pair": subject})


def in_window(day: dt.date, w: dict | None) -> bool:
    return bool(w) and w["start"] <= day.isoformat() <= w["end"]


def dates_in(text: str) -> list:
    out = []
    for m in DATE.finditer(text):
        try:
            out.append(dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
        except ValueError:
            pass
    return out


def tokens_of(sa: dict) -> list:
    return [str(x) for x in (sa.get("sites") or []) + (sa.get("releases") or []) if str(x).strip()]


def text_problems(text: str, sa: dict, what: str) -> list:
    """Why a piece of text (a word of a command, a script, a text file) crosses the fence."""
    p, low = [], text.casefold()
    for tok in tokens_of(sa):
        if tok.casefold() in low:
            p.append(f"{what} names `{tok}`, which was set aside")
    for path in sa.get("paths") or []:
        if str(path).casefold() in low or Path(path).name.casefold() in low:
            p.append(f"{what} names the set-aside path `{path}`")
    inside = sorted({d.isoformat() for d in dates_in(text) if in_window(d, sa.get("window"))})
    if inside:
        p.append(f"{what} names a date inside the set-aside window ({', '.join(inside[:3])}"
                 + (f", and {len(inside) - 3} more" if len(inside) > 3 else "") + ")")
    return p


def json_problems(obj, sa: dict, what: str) -> list:
    """Why a JSON data file crosses the fence: its declared window, the values under the time keys, or a
    set-aside site or release among its values. Other dates in it (when it was retrieved) are not data."""
    keys = {k.casefold() for k in sa.get("time_keys") or TIME_KEYS}
    toks = {t.casefold(): t for t in tokens_of(sa)}
    window, hits, named = sa.get("window"), [], set()

    def walk(o, key=None):
        if isinstance(o, dict):
            if window and set(o) >= {"start", "end"} and sf.window_of({"start": o["start"], "end": o["end"]}):
                if key is None or str(key).casefold() == "window":
                    if sf.windows_overlap({"start": o["start"], "end": o["end"]}, {"start": window["start"], "end": window["end"]}):
                        hits.append(f"its window {o['start']} to {o['end']}")
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, key)
        elif isinstance(o, str):
            if o.casefold() in toks:
                named.add(toks[o.casefold()])
            if window and key is not None and str(key).casefold() in keys:
                for d in dates_in(o[:32]):
                    if in_window(d, window):
                        hits.append(d.isoformat())
    walk(obj)
    p = [f"{what} holds `{t}`, which was set aside" for t in sorted(named)]
    if hits:
        p.append(f"{what} holds data inside the set-aside window ({len(hits)} value(s), the first {hits[0]})")
    return p


def file_problems(f: Path, sa: dict, shown: str) -> list:
    """Read one existing file the way the fence reads it."""
    for path in sa.get("paths") or []:
        if f.resolve() == Path(path).resolve() or f.resolve().is_relative_to(Path(path).resolve()):
            return [f"`{shown}` is a set-aside path"]
    try:
        raw = f.read_bytes()
    except OSError:
        return []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return [f"`{shown}` is not text, so the fence cannot read it: a look names text files (JSON, CSV, scripts)"]
    if f.suffix.lower() == ".json":
        try:
            return json_problems(json.loads(text), sa, f"`{shown}`")
        except ValueError:
            pass
    return text_problems(text, sa, f"`{shown}`")


def set_aside_present(sa: dict) -> list:
    return [str(p) for p in sa.get("paths") or [] if Path(p).exists()]


def record_lines(path: Path) -> list:
    out = []
    if path.is_file():
        for ln in path.read_text().splitlines():
            if ln.strip():
                try:
                    e = json.loads(ln)
                    out.append(e if isinstance(e, dict) else {"unreadable": ln[:200]})
                except ValueError:
                    out.append({"unreadable": ln[:200]})
    return out


def did_the_work(ev: list) -> set:
    return {e["actor"].casefold() for e in ev if e["kind"] not in NOT_THE_WORK}


def last(ev: list, kind: str):
    return next((e for e in reversed(ev) if e["kind"] == kind), None)


def breached(ev: list) -> list:
    return [e for e in ev if e["kind"] == "fence.breached"]


def count(ev: list, kind: str) -> int:
    return sum(1 for e in ev if e["kind"] == kind)


def open_notes(ev: list) -> list:
    done = {e["data"]["id"] for e in ev if e["kind"] == "note.resolved"}
    return [e for e in ev if e["kind"] == "note.raised" and e["data"]["id"] not in done]


# ---- commands -----------------------------------------------------------
def cmd_start(x: Exploration, a) -> None:
    if x.log.exists():
        raise Refused("this exploration is already started")
    if not str(a.question).strip().endswith("?"):
        raise Refused("the question is not a question: `--question` is one sentence ending in a question mark")
    x.check_actor(a.by)
    how = a.how
    if how not in HOW and not a.nothing_set_aside:
        raise Refused(f"`--how` says how the data is held out, one of: {', '.join(HOW)}")
    window, working = parse_window(a.set_aside_window), parse_window(a.working_window)
    sites = [s.strip() for s in (a.set_aside_sites or "").split(",") if s.strip()]
    releases = [s.strip() for s in (a.set_aside_release or []) if s.strip()]
    subject = parse_subject(a.subject)
    if a.nothing_set_aside:
        if window or sites or releases:
            raise Refused("`--nothing-set-aside` and something set aside are both given; choose one")
        how = "nothing"
    else:
        need = HOW[how]
        if not {"window": window, "sites": sites, "releases": releases}[need]:
            raise Refused(f"holding out {how} names {'a window (--set-aside-window START:END)' if need == 'window' else 'the sites (--set-aside-sites a,b)' if need == 'sites' else 'the release or record (--set-aside-release NAME)'}"
                          ": nothing is looked at until what is set aside is written down")
        if not str(a.why or "").strip():
            raise Refused("`--why` says why this is the data to set aside; it goes into the later plan")
    if window and working and sf.windows_overlap(core(working), core(window)):
        raise Refused("the working window and the set-aside window overlap: data that is explored cannot also be held out")
    request = Path(a.request).resolve() if a.request else None
    if request is None or not request.is_file():
        raise Refused("`--request` names the request this exploration answers, in the scientist's own words; it is bound by checksum")
    studies = Path(os.path.abspath(a.studies)) if a.studies else x.d.parent.parent / "studies"
    if (studies / x.d.name).exists():
        raise Refused(f"a study directory named {x.d.name} exists beside the record; an exploration and a study do not share a name")
    record = studies / "openings.jsonl"
    key = subject_key(subject)
    for ln in record_lines(record):  # what was already opened or explored cannot be set aside now
        if ln.get("key") == key and window and sf.windows_overlap(ln.get("window"), core(window)):
            raise Refused(f"the record of what has been opened says this subject and an overlapping window were already "
                          f"{'explored' if ln.get('kind') == 'explored' else 'opened'} by {ln.get('study')}: data that has been "
                          "looked at cannot be set aside")
    paths = [os.path.abspath(p) for p in a.set_aside_path or []]
    present = [p for p in paths if Path(p).exists()]
    if present:
        raise Refused(f"set-aside data is already here ({present[0]}); it is set aside before it is fetched, and it is not fetched by an exploration")
    sa = {"how": how, "subject": subject, "window": window, "sites": sites, "releases": releases, "paths": paths,
          "time_keys": [k.strip() for k in (a.time_keys or ",".join(TIME_KEYS)).split(",") if k.strip()],
          "why": a.why or a.nothing_set_aside,
          "working": {"description": a.working, "window": working}}
    x.d.mkdir(parents=True, exist_ok=True)
    for sub in ("receipts", "notes", "verdicts", "looks"):
        (x.d / sub).mkdir(exist_ok=True)
    dest = x.d / "request.md"
    if request != dest:
        if dest.exists() and sf.sha_file(dest) != sf.sha_file(request):
            raise Refused("the exploration already holds a different request.md")
        shutil.copyfile(request, dest)
    rel_record = os.path.relpath(record, x.d)
    e = x.add(a.by, "exploration.started", {
        "id": a.id, "question": a.question, "request": {"file": "request.md", "sha": sf.sha_file(dest)},
        "set_aside": sa, "record": {"path_from_exploration": rel_record}, "tool": sf.sha_file(Path(__file__).resolve())})
    write_json(x.set_aside_path, {"exploration": a.id, "set_aside": sa, "started": f"{e['seq']}:{e['hash']}",
                                  "says": "what this exploration does not look at; a look that names it is refused"})
    studies.mkdir(parents=True, exist_ok=True)
    mark = f"{e['seq']}:{e['hash']}"
    lines = []
    if how != "nothing":
        lines.append({"way": WAY, "kind": "set-aside", "exploration": a.id, "exploration_dir": x.d.name, "subject": key,
                      "set_aside": {"how": how, "window": window, "sites": sites, "releases": releases},
                      "at": e["at"], "started": mark})
    explored = {"way": WAY, "kind": "explored", "study": a.id, "dir": x.d.name, "test": WAY, "key": key,
                "at": e["at"], "started": mark}
    if working:
        explored["window"] = {"start": working["start"], "end": working["end"]}
    lines.append(explored)  # the study tool reads `key` and `window`: a study that holds this out is marked exploratory
    with record.open("a") as rec:
        for ln in lines:
            rec.write(json.dumps(ln, sort_keys=True) + "\n")
        rec.flush()
        os.fsync(rec.fileno())
    print(f"started {a.id} ({WAY}). Set aside: {how}"
          + (f", {window['start']} to {'onward' if window.get('open_ended') else window['end']}" if window else "")
          + (f", sites {sites}" if sites else "") + (f", {releases}" if releases else "")
          + f". Written to {rel_record}. Next: `known`, then look.")


def knowledge_tool():
    return _load("knowledge", HERE / "knowledge.py")


def cmd_known(x: Exploration, a) -> None:
    start = x.started()
    k = knowledge_tool()
    found = k.about(a.question or start["data"]["question"], [Path(b) for b in a.bundle], [Path(d) for d in a.drafts or []],
                    tags=a.tag or [])
    x.add(a.by, "knowledge.listed", {
        "question": a.question or start["data"]["question"], "bundles": [os.path.relpath(b, x.d) for b in a.bundle],
        "drafts": [os.path.relpath(d, x.d) for d in a.drafts or []],
        "concepts": [{k_: c[k_] for k_ in ("path", "sha256", "type", "status", "signed", "signed_by", "why")} for c in found]})
    print(k.render(found))
    print(f"\nlisted {len(found)} concept(s) in the exploration log ({WAY}). Read each one that bears on the question, "
          "then record what it changes with `read`.")


def cmd_read(x: Exploration, a) -> None:
    x.started()
    k = knowledge_tool()
    f = Path(a.concept).resolve()
    if not f.is_file():
        raise Refused(f"the concept {a.concept} does not exist")
    fm, _ = k.front_matter(f)
    if fm is None:
        raise Refused(f"{a.concept} has no front matter: it is not a knowledge concept")
    signed, by = k.signed_by(fm)
    x.add(a.by, "knowledge.read", {"path": os.path.relpath(f, x.d), "sha256": sf.sha_file(f), "status": fm.get("status"),
                                   "signed": signed, "signed_by": by, "takes": a.takes})
    print(f"read: {f.name} ({'signed by ' + ', '.join(by) if signed else 'NOT SIGNED, status ' + str(fm.get('status'))}), "
          f"recorded ({WAY})")


def named_files(x: Exploration, argv: list) -> dict:
    """Every existing file a command names, by the word that names it, read from the exploration directory."""
    out = {}
    for word in argv:
        word = str(word)
        for tok in [word] + ([word.split("=", 1)[1]] if word.startswith("-") and "=" in word else []):
            if not tok or tok == "{python}":
                continue
            f = x.d / tok
            if f.is_file():
                out[tok] = f
    return out


def cmd_look(x: Exploration, a) -> None:
    ev = x.events()
    start = x.started()
    sa = start["data"]["set_aside"]
    if breached(ev):
        raise Refused("this exploration is spoiled: set-aside data reached it (see fence.breached in the log). Nothing more is looked at here")
    if not last(ev, "knowledge.listed"):
        raise Refused("nothing has been looked up yet: run `known` first, so the exploring starts from what is already known")
    argv = [str(w) for w in (a.argv[1:] if a.argv and a.argv[0] == "--" else a.argv or [])]
    if not argv:
        raise Refused("a look is `look ... -- LAUNCHER SCRIPT [arguments]`")
    if not str(a.why or "").strip():
        raise Refused("`--why` says what this look is trying to find out; the count of things tried is the count of looks")
    launcher, script = sf.launch(argv)
    if launcher is None:
        raise Refused(f"{script}. A look is {sf.LAUNCHERS}, then the script's own arguments")
    if not (x.d / script).is_file():
        raise Refused(f"the script `{script}` does not exist (paths are read from the exploration directory)")
    here = set_aside_present(sa)
    if here:
        raise Refused(f"set-aside data is in the workspace ({here[0]}); an exploration does not fetch it and does not run beside it")
    files = named_files(x, argv)
    problems = []
    for word in argv:
        problems += text_problems(word, sa, f"the word `{word}`")
    for tok, f in files.items():
        problems += file_problems(f, sa, tok)
    if problems:
        x.add(a.by, "look.refused", {"argv": argv, "why": a.why, "refused_because": problems})
        raise Refused("this look names what was set aside, so it is not run (the refusal is logged): " + "; ".join(problems[:4]))
    n = count(ev, "look.run") + 1
    lid = f"LOOK-{n:03d}"
    before = x.listing()
    out_rel = f"receipts/{lid}.out.txt"
    cache = tempfile.mkdtemp(prefix="sf-no-bytecode-")
    env = {k: os.environ[k] for k in sf.passed_names()}
    env.update(PYTHONPYCACHEPREFIX=cache, PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1")
    run = [sys.executable if w == "{python}" else w for w in argv]
    try:
        done = subprocess.run(run, cwd=x.d, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, errors="replace")
        code, out = done.returncode, done.stdout
    except OSError as err:
        code, out = 127, f"could not run: {err}"
    finally:
        shutil.rmtree(cache, ignore_errors=True)
    (x.d / out_rel).write_text(f"[{WAY}: output of {lid}]\n" + out)
    after = x.listing()
    wrote = {k: v for k, v in after.items() if before.get(k) != v and k != out_rel}
    crossing = []
    for rel in wrote:
        crossing += file_problems(x.d / rel, sa, rel)
    crossing += [f"set-aside data appeared at {p}" for p in set_aside_present(sa)]
    inputs = [{"word": tok, "sha256": sf.sha_file(f), "bytes": f.stat().st_size} for tok, f in files.items()]
    receipt = {"id": lid, "why": a.why, "argv": argv, "launcher": launcher, "script": {"word": script, "sha256": sf.sha_file(x.d / script)},
               "inputs": inputs, "exit_code": code, "output": {"file": out_rel, "sha256": sf.sha_file(x.d / out_rel)},
               "wrote": wrote, "at": sf.now(), "by": a.by}
    sha = write_json(x.d / f"receipts/{lid}.json", receipt)
    x.add(a.by, "look.run", {"id": lid, "why": a.why, "argv": argv, "script_sha": receipt["script"]["sha256"], "inputs": inputs,
                             "exit_code": code, "output_sha": receipt["output"]["sha256"], "receipt_sha": sha,
                             "wrote": wrote, "out_head": out[:1500]})
    if crossing:
        x.add(a.by, "fence.breached", {"look": lid, "what": crossing})
    print(out, end="" if out.endswith("\n") else "\n")
    print(f"[{lid} logged ({WAY}), exit {code}, {len(inputs)} file(s) named, output in {out_rel}]")
    if crossing:
        raise Refused(f"{lid} left set-aside data in the exploration ({crossing[0]}). The exploration is spoiled: no lead and "
                      "no hand-over can come from it, and the data it held out is no longer held out for this subject")


def cmd_recheck(x: Exploration, a) -> None:
    """Run a logged look again and compare what comes out, without adding a look: for the review assistant."""
    ev = x.events()
    sa = x.started()["data"]["set_aside"]
    e = next((e for e in ev if e["kind"] == "look.run" and e["data"]["id"] == a.look), None)
    if e is None:
        raise Refused(f"there is no {a.look} in the log")
    d = e["data"]
    receipt = json.loads((x.d / f"receipts/{d['id']}.json").read_text())
    script = x.d / receipt["script"]["word"]
    if sf.sha_file(script) != d["script_sha"]:
        raise Refused(f"the script of {d['id']} is not the script that was logged; nothing is run")
    for i in d["inputs"]:
        if sf.sha_file(x.d / i["word"]) != i["sha256"]:
            raise Refused(f"`{i['word']}` is not the file {d['id']} read; nothing is run")
    if set_aside_present(sa):
        raise Refused("set-aside data is in the workspace; nothing is run")
    cache = tempfile.mkdtemp(prefix="sf-no-bytecode-")
    env = {k: os.environ[k] for k in sf.passed_names()}
    env.update(PYTHONPYCACHEPREFIX=cache, PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1")
    copy = x.d.parent / f".recheck-{os.getpid()}"  # a copy at the same depth, so the look's relative paths still resolve
    try:
        shutil.copytree(x.d, copy, symlinks=True)
        done = subprocess.run([sys.executable if w == "{python}" else w for w in d["argv"]], cwd=copy, env=env,
                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    finally:
        shutil.rmtree(cache, ignore_errors=True)
        shutil.rmtree(copy, ignore_errors=True)
    same = sf.sha_text(f"[{WAY}: output of {d['id']}]\n" + done.stdout) == d["output_sha"] and done.returncode == d["exit_code"]
    print(done.stdout, end="" if done.stdout.endswith("\n") else "\n")
    print(f"[recheck of {d['id']} ({WAY}): exit {done.returncode}; " + ("the output is identical to what was logged]" if same
                                                                       else "THE OUTPUT DIFFERS from what was logged]"))
    if not same:
        raise Refused(f"{d['id']} does not reproduce: run again, the same script on the same files gives another output")


def cmd_choice(x: Exploration, a) -> None:
    ev = x.events()
    x.started()
    alts = [s.strip() for s in a.alternative or [] if s.strip()]
    if not alts:
        raise Refused("a choice has at least one alternative (`--alternative`, repeatable): what else could have been done")
    if a.look and not any(e["kind"] == "look.run" and e["data"]["id"] == a.look for e in ev):
        raise Refused(f"there is no {a.look} in the log")
    cid = f"CHOICE-{count(ev, 'choice.recorded') + 1:03d}"
    x.add(a.by, "choice.recorded", {"id": cid, "choice": a.choice, "alternatives": alts, "rests_on": a.rests_on, "look": a.look})
    print(f"{cid} recorded ({WAY}): {a.choice}")


def cmd_note(x: Exploration, a) -> None:
    ev = x.events()
    x.started()
    if a.kind not in NOTE_KINDS:
        raise Refused(f"kind is one of {NOTE_KINDS}")
    nid = f"NOTE-{count(ev, 'note.raised') + 1:03d}"
    evidence = None
    if a.evidence:
        f = (x.d / a.evidence).resolve()
        if not f.is_file():
            raise Refused(f"the evidence file {a.evidence} does not exist (paths are read from the exploration directory)")
        evidence = {"path": os.path.relpath(f, x.d), "sha256": sf.sha_file(f)}
    fp = x.d / "notes" / f"{nid}.json"
    if fp.exists():
        raise Refused(f"{fp.name} already exists and is not in the log")
    note = {"id": nid, "at": sf.now(), "by": a.by, "kind": a.kind, "about": a.about, "text": a.text, "evidence": evidence,
            "status": "open", "from": "an exploration: what it says was seen while exploring and is not a tested claim"}
    sha = write_json(fp, note)
    x.add(a.by, "note.raised", {"id": nid, "kind": a.kind, "about": a.about, "text": a.text, "evidence": evidence, "sha": sha})
    print(f"note {nid} recorded ({WAY}; {a.kind}: {a.about})")


def lead_problems(lead, ev: list) -> list:
    if not isinstance(lead, dict):
        return ["the lead file is not a mapping"]
    p = [f"`{k}` is missing" for k in LEAD_KEYS if k not in lead]
    p += [f"`{k}` is not a key of a lead" for k in lead if k not in LEAD_KEYS]
    if p:
        return p
    for k in ("what_looks_true", "how_it_was_found"):
        if not isinstance(lead[k], str) or len(lead[k].split()) < 5:
            p.append(f"`{k}` is a sentence or more, in words")
    looks = {e["data"]["id"]: e for e in ev if e["kind"] == "look.run"}
    cited = lead["evidence"] if isinstance(lead["evidence"], list) else []
    if not cited:
        p.append("`evidence` lists the looks the lead rests on (LOOK-001, ...): a lead with no look behind it is a guess")
    for lid in cited:
        if lid not in looks:
            p.append(f"`evidence` names {lid}, which is not in the log")
        elif looks[lid]["data"]["exit_code"] != 0:
            p.append(f"`evidence` names {lid}, which failed (exit {looks[lid]['data']['exit_code']})")
    choices = {e["data"]["id"] for e in ev if e["kind"] == "choice.recorded"}
    placed = []
    for key, word in (("choices_that_would_change_it", "how"), ("choices_that_would_not", "why")):
        entries = lead[key] if isinstance(lead[key], list) else None
        if entries is None:
            p.append(f"`{key}` is a list")
            continue
        for c in entries:
            if not isinstance(c, dict) or not c.get("choice") or not str(c.get(word) or "").strip():
                p.append(f"each entry of `{key}` is {{choice: CHOICE-001, {word}: words}}")
            elif c["choice"] not in choices:
                p.append(f"`{key}` names {c['choice']}, which is not in the log")
            else:
                placed.append(c["choice"])
    for cid in sorted(choices - set(placed)):
        p.append(f"{cid} is recorded in the log and the lead does not say whether it would change the answer")
    for cid in sorted({c for c in placed if placed.count(c) > 1}):
        p.append(f"{cid} is listed twice")
    if not isinstance(lead["pitfalls"], list):
        p.append("`pitfalls` is a list (empty when none was met)")
    stub = lead["proposed_plan"]
    if not isinstance(stub, dict):
        p.append("`proposed_plan` is a mapping")
    else:
        p += [f"`proposed_plan.{k}` is missing" for k in PLAN_STUB_KEYS if not str(stub.get(k) or "").strip()]
        if str(stub.get("question") or "").strip() and not str(stub["question"]).strip().endswith("?"):
            p.append("`proposed_plan.question` is one sentence ending in a question mark")
    return p


def render_lead(lead: dict) -> str:
    sa, tried = lead["set_aside"], lead["tried"]
    w = sa.get("window")
    aside = (f"{sa['how']}: {w['start']} to {'onward (the window stays open)' if w.get('open_ended') else w['end']}" if w
             else f"{sa['how']}: {', '.join(sa.get('sites') or sa.get('releases') or []) or 'nothing'}")
    lines = [f"# Lead from {lead['exploration']} (exploring; version {lead['version']})", "", BANNER, "",
             f"**The question.** {lead['question']}", "",
             f"**What looks true.** {lead['what_looks_true'].strip()}", "",
             f"**How it was found.** {lead['how_it_was_found'].strip()}", "",
             f"**How many things were tried.** {tried['looks']} looks were run and logged, {tried['failed']} of them failed, and "
             f"{tried['refused']} more were refused at the fence. The lead rests on {', '.join(lead['evidence'])}. The count is "
             "taken from the exploration log, not from memory.", "",
             f"**What was set aside, and never looked at.** {aside}. Why: {sa.get('why')}", "",
             f"**What was explored.** {sa['working'].get('description') or 'see the log'}", "",
             "## Choices that would change it", ""]
    by_id = {c["id"]: c for c in lead["choices"]}
    for c in lead["choices_that_would_change_it"]:
        full = by_id[c["choice"]]
        lines += [f"- **{c['choice']}: {full['choice']}** Alternatives: {'; '.join(full['alternatives'])}. Rests on: "
                  f"{full['rests_on']}. How it would change the answer: {c['how']}"]
    lines += ["", "## Choices that would not", ""]
    for c in lead["choices_that_would_not"]:
        full = by_id[c["choice"]]
        lines += [f"- **{c['choice']}: {full['choice']}** Alternatives: {'; '.join(full['alternatives'])}. Why not: {c['why']}"]
    lines += ["", "## Pitfalls met", ""] + ([f"- {x}" for x in lead["pitfalls"]] or ["- none recorded"])
    lines += ["", "## Knowledge read before looking", ""]
    lines += [f"- `{k['path']}`: {'signed by ' + ', '.join(k['signed_by']) if k['signed'] else 'NOT SIGNED (status ' + str(k['status']) + ')'}"
              + (f". Takes from it: {k['takes']}" if k.get("takes") else "") for k in lead["knowledge_read"]] or ["- none recorded as read"]
    stub = lead["proposed_plan"]
    lines += ["", "## Proposed plan for a confirming study (a stub, to be written properly at the plan stage)", "",
              f"- **Question:** {stub['question']}", f"- **Quantity estimated:** {stub['quantity_estimated']}",
              f"- **The difference that matters:** {stub['difference_that_matters']}", f"- **Rule, sketched:** {stub['rule_sketch']}"]
    lines += [f"- **{k.replace('_', ' ').capitalize()}:** {v}" for k, v in stub.items() if k not in PLAN_STUB_KEYS]
    lines += ["", f"Held-out data for that study: only what this exploration set aside ({aside}). The explored data is working data there.",
              "", f"*Exploration log fingerprint when this lead was recorded: {lead['log_fingerprint']}. Status: {LEAD_STATUS}.*", ""]
    return "\n".join(lines)


def cmd_lead(x: Exploration, a) -> None:
    ev = x.events()
    start = x.started()
    if breached(ev):
        raise Refused("this exploration is spoiled (set-aside data reached it); no lead comes from it")
    src = Path(a.file).resolve()
    if not src.is_file():
        raise Refused(f"the lead file {a.file} does not exist")
    try:
        given = yaml.safe_load(src.read_text())
    except yaml.YAMLError as err:
        raise Refused(f"the lead file does not parse as YAML: {err}")
    problems = lead_problems(given, ev)
    if problems:
        raise Refused("the lead is not complete: " + "; ".join(problems))
    version = count(ev, "lead.recorded") + 1
    reads = [e["data"] for e in ev if e["kind"] == "knowledge.read"]
    lead = {"kind": "lead", "status": LEAD_STATUS, "version": version, "exploration": start["data"]["id"],
            "question": start["data"]["question"], "request_sha": start["data"]["request"]["sha"], **given,
            "tried": {"looks": count(ev, "look.run"), "failed": sum(1 for e in ev if e["kind"] == "look.run" and e["data"]["exit_code"] != 0),
                      "refused": count(ev, "look.refused"), "ids": [e["data"]["id"] for e in ev if e["kind"] == "look.run"]},
            "choices": [{k: e["data"][k] for k in ("id", "choice", "alternatives", "rests_on", "look")} for e in ev if e["kind"] == "choice.recorded"],
            "knowledge_read": [{k: r.get(k) for k in ("path", "sha256", "status", "signed", "signed_by", "takes")} for r in reads],
            "set_aside": start["data"]["set_aside"], "log_fingerprint": f"{ev[-1]['seq']}:{ev[-1]['hash']}"}
    sha = write_json(x.d / "lead.json", lead)
    md = render_lead(lead)
    (x.d / "lead.md").write_text(md)
    (x.d / "leads").mkdir(exist_ok=True)
    shutil.copyfile(x.d / "lead.json", x.d / "leads" / f"lead-v{version}.json")
    shutil.copyfile(x.d / "lead.md", x.d / "leads" / f"lead-v{version}.md")
    x.add(a.by, "lead.recorded", {"version": version, "json_sha": sha, "md_sha": sf.sha_file(x.d / "lead.md"),
                                  "source_sha": sf.sha_file(src), "tried": lead["tried"]})
    print(f"lead version {version} recorded ({WAY}): lead.md, lead.json. {lead['tried']['looks']} looks behind it. "
          "Next: a review assistant that did none of this picks holes in it.")


def cmd_review(x: Exploration, a) -> None:
    ev = x.events()
    x.started()
    if a.verdict not in VERDICTS:
        raise Refused(f"the verdict is one of {VERDICTS}")
    if not last(ev, "lead.recorded") and not last(ev, "exploration.ended"):
        raise Refused("there is nothing to review yet: no lead is recorded and the exploration has not ended")
    if a.by.casefold() in did_the_work(ev):
        raise Refused(f"{a.by} did part of this exploration; the review is by an assistant that did none of it")
    src = Path(a.file).resolve()
    if not src.is_file():
        raise Refused(f"the review file {a.file} does not exist")
    n = count(ev, "review.verdict") + 1
    dest = x.d / "verdicts" / f"REVIEW-{n:03d}.md"
    if src != dest:
        shutil.copyfile(src, dest)
    lead = last(ev, "lead.recorded")
    x.add(a.by, "review.verdict", {"n": n, "verdict": a.verdict, "file": f"verdicts/{dest.name}", "sha": sf.sha_file(dest),
                                   "of_lead_version": lead["data"]["version"] if lead else None})
    print(f"review {n} recorded ({WAY}): {a.verdict}")


def cmd_end(x: Exploration, a) -> None:
    ev = x.events()
    x.started()
    if a.outcome not in OUTCOMES:
        raise Refused(f"an exploration ends as one of {OUTCOMES}")
    data = {"outcome": a.outcome, "summary": a.summary}
    if a.outcome == "lead":
        if breached(ev):
            raise Refused("this exploration is spoiled; it can end as a stop, not as a lead")
        if not last(ev, "lead.recorded"):
            raise Refused("no lead is recorded; record it with `lead`, or end as a note, a method or a stop")
    if a.outcome == "note" and not count(ev, "note.raised"):
        raise Refused("no note is recorded; record it with `note`")
    if a.outcome == "method":
        f = (x.d / (a.file or "")).resolve()
        if not a.file or not f.is_file() or not f.is_relative_to(x.d):
            raise Refused("ending as a method names the method's script inside the exploration (`--file`)")
        data["method"] = {"file": os.path.relpath(f, x.d), "sha256": sf.sha_file(f)}
    if not str(a.summary or "").strip():
        raise Refused("`--summary` says in a sentence what the exploration came to")
    x.add(a.by, "exploration.ended", data)
    print(f"ended ({WAY}) as a {a.outcome}." + (" Next: `hand-over`, by the coordinating assistant." if a.outcome == "lead" else ""))


def handover_problems(x: Exploration, ev: list) -> list:
    start, p = ev[0], []
    sa = start["data"]["set_aside"]
    ended, lead = last(ev, "exploration.ended"), last(ev, "lead.recorded")
    if sa["how"] == "nothing":
        p.append("nothing was set aside, so there is no data a confirming study could hold out")
    if breached(ev):
        p.append("set-aside data reached this exploration, so it is no longer held out")
    if not ended or ended["data"]["outcome"] != "lead":
        p.append("the exploration has not ended as a lead")
    if lead:
        verdicts = [e for e in ev if e["kind"] == "review.verdict" and e["seq"] > lead["seq"]]
        if not verdicts:
            p.append("no review assistant has looked at the latest lead")
        for name, key in (("lead.json", "json_sha"), ("lead.md", "md_sha")):
            if sf.sha_file(x.d / name) != lead["data"][key]:
                p.append(f"{name} is not the lead that was recorded")
    mark = f"{start['seq']}:{start['hash']}"
    lines = [ln for ln in record_lines(x.record()) if ln.get("started") == mark]
    if not any(ln.get("kind") == "explored" for ln in lines) or (sa["how"] != "nothing" and not any(ln.get("kind") == "set-aside" for ln in lines)):
        p.append(f"the record ({start['data']['record']['path_from_exploration']}) no longer holds this exploration's lines")
    here = set_aside_present(sa)
    if here:
        p.append(f"set-aside data is in the workspace ({here[0]})")
    return p


def cmd_hand_over(x: Exploration, a) -> None:
    ev = x.events()
    start = x.started()
    problems = handover_problems(x, ev)
    if problems:
        raise Refused("nothing is handed over: " + "; ".join(problems))
    if a.by.casefold() in did_the_work(ev):
        raise Refused(f"{a.by} did the exploring; the hand-over is made by the coordinating assistant, which did not")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", a.study_id or "") or a.study_id == x.d.name:
        raise Refused("`--study-id` names the confirming study (for example STUDY-0002); it is not the exploration's name")
    lead = json.loads((x.d / "lead.json").read_text())
    sa, stub = start["data"]["set_aside"], lead["proposed_plan"]
    verdict = [e for e in ev if e["kind"] == "review.verdict"][-1]
    out = x.d / "hand-over"
    out.mkdir(exist_ok=True)
    w = sa.get("window")
    request = (x.d / "request.md").read_text().rstrip() + "\n\n---\n\n" + "\n".join([
        f"## From {start['data']['id']} (exploring, not a finding)", "",
        f"This request was first explored. The exploration ended in a lead, version {lead['version']}, which is {LEAD_STATUS}.", "",
        f"**The lead.** {lead['what_looks_true'].strip()}", "",
        f"**How it was found.** {lead['how_it_was_found'].strip()} {lead['tried']['looks']} looks were run, "
        f"{lead['tried']['failed']} failed, {lead['tried']['refused']} were refused at the fence.", "",
        f"**The question proposed for the confirming study.** {stub['question']}", "",
        f"**The difference that matters, as proposed.** {stub['difference_that_matters']}", "",
        "**Already looked at (working data from now on).** " + str(sa["working"].get("description") or "see the exploration log") + "", "",
        "**Held out.** Only what the exploration set aside: " + (f"{w['start']} to {'onward' if w.get('open_ended') else w['end']}" if w
                                                               else ", ".join(sa.get("sites") or sa.get("releases") or [])) + f". {sa.get('why')}", "",
        f"**The review of the lead.** {verdict['data']['verdict']} ({verdict['data']['file']} in the exploration).", "",
        f"Lead checksum (lead.json): {sf.sha_file(x.d / 'lead.json')}. Exploration log fingerprint: {ev[-1]['seq']}:{ev[-1]['hash']}.", ""])
    (out / "request.md").write_text(request)
    held = {"pair": sa["subject"], "why_this_window": sa.get("why")}
    if w:
        held["window"] = {"start": w["start"], "end": "CHOOSE: a date inside the set-aside window" if w.get("open_ended") else w["end"]}
    plan_stub = {"study": a.study_id, "question": stub["question"], "quantity_estimated": stub["quantity_estimated"],
                 "data": {"working": str(sa["working"].get("description") or "") + " Explored in " + start["data"]["id"]
                          + ": already seen, never held out.", "held_out": held},
                 "from_the_lead": {k: v for k, v in stub.items() if k not in ("question", "quantity_estimated")},
                 "choices_to_fix_in_the_plan": [f"{c['choice']}: {c['how']}" for c in lead["choices_that_would_change_it"]],
                 "pitfalls_to_make_hard_cases": lead["pitfalls"]}
    (out / "analysis-plan.stub.yaml").write_text(
        f"# Exploring: a stub from {start['data']['id']}, not an analysis plan. The study tool will not read this file.\n"
        "# The analysis assistant writes analysis-plan.yaml from mvp/templates/analysis-plan.yaml at the plan stage and takes\n"
        "# from here the question, the quantity, the data and the choices to fix. The held-out data may only be what the\n"
        "# exploration set aside; `explore.py check-study` refuses anything else.\n"
        + yaml.safe_dump(plan_stub, sort_keys=False, allow_unicode=True, width=110))
    study_dir = os.path.relpath(x.record().parent / a.study_id, x.d)
    command = ["uv", "run", "mvp/sf.py", "start", "--study", f"<the exploration>/{study_dir}", "--id", a.study_id,
               "--question", stub["question"], "--request", "<the exploration>/hand-over/request.md", "--by", "agent:<the coordinating assistant>"]
    sha = write_json(out / "hand-over.json", {
        "kind": "hand-over", "from": start["data"]["id"], "for": "sf.py start", "study_id": a.study_id,
        "study_directory_from_exploration": study_dir, "question": stub["question"],
        "request": {"file": "hand-over/request.md", "sha256": sf.sha_file(out / "request.md")},
        "plan_stub": {"file": "hand-over/analysis-plan.stub.yaml", "sha256": sf.sha_file(out / "analysis-plan.stub.yaml")},
        "lead": {"version": lead["version"], "sha256": sf.sha_file(x.d / "lead.json"), "status": LEAD_STATUS},
        "review": verdict["data"], "set_aside": sa, "record": start["data"]["record"], "start_command": command,
        "then": "after the plan is written: explore.py check-study --exploration <this> --study <the study>"})
    x.add(a.by, "handed.over", {"study_id": a.study_id, "hand_over_sha": sha,
                                "request_sha": sf.sha_file(out / "request.md"), "study_directory_from_exploration": study_dir})
    print(f"handed over ({WAY}): hand-over/request.md, hand-over/analysis-plan.stub.yaml, hand-over/hand-over.json.\n"
          f"Start the study with:\n  uv run mvp/sf.py start --study {study_dir} --id {a.study_id} --question \"{stub['question']}\" "
          "--request hand-over/request.md --by agent:<the coordinating assistant>\n(paths from the exploration directory)")


def study_problems(x: Exploration, study_dir: Path) -> list:
    ev = x.events()
    start = x.started()
    sa, p = start["data"]["set_aside"], []
    study = sf.Study(study_dir)
    sev = study.events()
    if not sev or sev[0]["kind"] != "study.started":
        return ["the study is not started"]
    over = last(ev, "handed.over")
    if not over:
        return ["this exploration was never handed over"]
    if (sf.request_of(sev) or {}).get("sha") != over["data"]["request_sha"]:
        p.append("the study was not started from this exploration's hand-over (its request is not hand-over/request.md)")
    if sf.openings_path(study).resolve() != x.record().resolve():
        p.append(f"the study does not sit beside the record this exploration wrote to ({x.record()}), so the study tool "
                 "would not see what was explored")
    try:
        plan = study.plan()
    except Refused:
        return p + ["the study has no analysis plan yet: check it again when the plan is written"]
    held = (plan.get("data") or {}).get("held_out") or {}
    spec = (plan.get("tests") or {}).get("held-out") or {}
    pair = spec.get("pair") or held.get("pair")
    if not pair or sf.subject_key({}, {"pair": pair}) != subject_key(sa["subject"]):
        p.append("the plan's held-out subject (`pair`) is not the subject of this exploration, written the same way: the "
                 "record matches on it, so a different spelling would hide what was explored")
    window = sf.window_of(spec.get("window") or held.get("window"))
    working, aside = sa["working"].get("window"), sa.get("window")
    if aside:
        if window is None:
            p.append("the plan's held-out window is not two dates")
        elif not (aside["start"] <= window["start"] and window["end"] <= aside["end"]):
            p.append(f"the plan holds out {window['start']} to {window['end']}, which is not inside what the exploration set "
                     f"aside ({aside['start']} to {'onward' if aside.get('open_ended') else aside['end']})")
    if working and (window is None or sf.windows_overlap(window, core(working))):
        p.append("the plan's held-out window touches the window that was explored: data that was used to explore cannot "
                 "be used to confirm what the exploring found")
    names = json.dumps(pair or {}).casefold() + " " + str(held.get("path") or "").casefold()
    if sa.get("sites") and not any(str(s).casefold() in names for s in sa["sites"]):
        p.append(f"the plan's held-out subject names none of the sites that were set aside ({', '.join(sa['sites'])})")
    if sa.get("releases") and not any(str(s).casefold() in names for s in sa["releases"]):
        p.append(f"the plan's held-out subject names none of the releases that were set aside ({', '.join(sa['releases'])})")
    if pair and spec:
        try:
            for e in sf.earlier_openings(study, plan, spec, sev):
                p.append(f"the study tool's own record says this subject and window were already looked at by {e.get('study')} "
                         f"({e.get('test')}): the study would come out exploratory")
        except (KeyError, TypeError):
            pass
    finding = sf.attached_finding(sev) if hasattr(sf, "attached_finding") else None
    lead_shas = {e["data"][k] for e in ev if e["kind"] == "lead.recorded" for k in ("json_sha", "md_sha")}
    for e in sev:
        if e["kind"] == "finding.attached" or (finding is not None and e is finding):
            sha = e["data"].get("sha") or e["data"].get("sha256")
            f = study.d / str(e["data"].get("file") or e["data"].get("path") or "")
            text = f.read_text(errors="replace") if f.is_file() else ""
            if sha in lead_shas or LEAD_STATUS in text or BANNER[:40] in text:
                p.append("the finding attached to the study is the exploration's lead: a lead is never a finding")
    return p


def cmd_check_study(x: Exploration, a) -> None:
    problems = study_problems(x, Path(a.study))
    for q in problems:
        print("check-study:", q)
    if problems:
        raise Refused(f"{len(problems)} problem(s): the study does not keep the fence this exploration set")
    print("check-study: PASS. The study was started from the hand-over, its held-out data is inside what the exploration "
          "set aside, and none of it was explored.")


def cmd_curation_list(x: Exploration, a) -> None:
    ev = x.events()
    start = x.started()
    notes = []
    for e in open_notes(ev):
        notes.append({"id": e["data"]["id"], "at": e["at"], "by": e["actor"], "kind": e["data"]["kind"], "about": e["data"]["about"],
                      "text": e["data"]["text"], "evidence": e["data"].get("evidence"),
                      "route": "draft a concept at status draft for the steward's queue, link it to the concept that already says it, or decline it with a reason"})
    lead = last(ev, "lead.recorded")
    sha = write_json(x.d / "curation-list.json", {
        "exploration": start["data"]["id"], "generated": sf.now(), "open_notes": len(notes), "notes": notes,
        "lead": {"file": "lead.json", "version": lead["data"]["version"], "status": LEAD_STATUS} if lead else None,
        "log_fingerprint": f"{ev[-1]['seq']}:{ev[-1]['hash']}",
        "contract": "the curating assistant drafts at status draft with its own generated event; it never merges and never "
                    "signs. A lead is never drafted as a finding: what may be drafted from it is its pitfalls and what it "
                    "learned about the data, each marked as seen while exploring"})
    print(f"curation list ({WAY}): {len(notes)} open note(s); curation-list.json sha256 {sha[:12]}")


def cmd_resolve(x: Exploration, a) -> None:
    ev = x.events()
    if a.disposition not in DISPOSITIONS:
        raise Refused(f"the disposition is one of {DISPOSITIONS}")
    if a.note not in {e["data"]["id"] for e in open_notes(ev)}:
        raise Refused(f"{a.note} is not an open note of this exploration")
    if a.disposition != "declined" and not a.ref:
        raise Refused("a drafted or linked note names the draft or the concept (`--ref`)")
    if a.disposition == "declined" and not str(a.comment or "").strip():
        raise Refused("a declined note says why (`--comment`)")
    x.add(a.by, "note.resolved", {"id": a.note, "disposition": a.disposition, "ref": a.ref, "comment": a.comment})
    print(f"{a.note}: {a.disposition} ({WAY})")


def stage_of(x: Exploration) -> dict:
    ev = x.events()
    if not ev:
        return {"way": WAY, "stage": "set-aside", "who": "analysis assistant",
                "does": "decide what will not be looked at and start the exploration (explore.py start)"}
    start = ev[0]["data"]
    lead, ended, over = last(ev, "lead.recorded"), last(ev, "exploration.ended"), last(ev, "handed.over")
    verdict = last(ev, "review.verdict")
    counts = {"looks": count(ev, "look.run"), "looks_failed": sum(1 for e in ev if e["kind"] == "look.run" and e["data"]["exit_code"] != 0),
              "looks_refused_at_the_fence": count(ev, "look.refused"), "choices": count(ev, "choice.recorded"),
              "knowledge_read": count(ev, "knowledge.read"), "open_notes": [e["data"]["id"] for e in open_notes(ev)]}
    if breached(ev) and not ended:
        here = {"stage": "spoiled", "who": "analysis assistant", "does": "set-aside data reached the exploration: end it as a stop and say so"}
    elif not last(ev, "knowledge.listed"):
        here = {"stage": "read-what-is-known", "who": "analysis assistant", "does": "list and read the knowledge that bears on the question (explore.py known, read)"}
    elif ended:
        if ended["data"]["outcome"] == "lead" and not over:
            here = {"stage": "hand-over", "who": "coordinating assistant", "does": "hand the lead to the confirming way (explore.py hand-over), or leave it"}
            blockers = handover_problems(x, ev)
            if blockers:
                here.update(stage="review", who="review assistant", still_needs=blockers)
        elif open_notes(ev):
            here = {"stage": "learn", "who": "curating assistant", "does": "every open note drafted, linked or declined (explore.py curation-list, resolve)"}
        else:
            here = {"stage": "ended"}
        here["outcome"] = ended["data"]["outcome"]
        if over:
            here["handed_over_to"] = over["data"]["study_id"]
    elif not lead:
        here = {"stage": "explore", "who": "analysis assistant", "does": "look, record choices and notes, then write up the lead or end as a note, a method or a stop"}
    elif not verdict or verdict["seq"] < lead["seq"]:
        here = {"stage": "review", "who": "review assistant", "does": "pick holes in the lead (explore.py review)"}
    else:
        here = {"stage": "revise-or-end", "who": "analysis assistant", "last_review": verdict["data"]["verdict"],
                "does": "answer the review: revise the lead (a new version is reviewed again) or end the exploration"}
    return {"way": WAY, "exploration": start["id"], "question": start["question"], **here, **counts,
            "set_aside": {k: start["set_aside"][k] for k in ("how", "window", "sites", "releases")},
            "says": "nothing here is a finding; an exploration ends in a lead, a note, a method or a stop"}


def cmd_status(x: Exploration, a) -> None:
    print(json.dumps(stage_of(x), indent=1))


def check_log(x: Exploration, posted: list | None = None) -> list:
    try:
        ev = x.events()
        p = x._chain(ev)
    except Refused as r:
        return [str(r)]
    if p:
        return [q.replace("study log", "exploration log") for q in p]
    if not ev or ev[0]["kind"] != "exploration.started":
        return ["the log does not begin with the start of an exploration"]
    start = ev[0]
    sa = start["data"]["set_aside"]
    p += [f"event {e['seq']} ({e['kind']}) does not say it is exploring" for e in ev if e["data"].get("way") != WAY]
    try:
        on_file = json.loads(x.set_aside_path.read_text()).get("set_aside")
    except (OSError, ValueError):
        on_file = None
    if on_file != sa:
        p.append("set-aside.json is not what the log says was set aside")
    if sf.sha_file(x.d / "request.md") != start["data"]["request"]["sha"]:
        p.append("request.md is not the request the exploration was started with")
    mark = f"{start['seq']}:{start['hash']}"
    mine = [ln for ln in record_lines(x.record()) if ln.get("started") == mark]
    if not any(ln.get("kind") == "explored" and ln.get("key") == subject_key(sa["subject"]) for ln in mine):
        p.append("the record of what has been opened does not hold this exploration's explored line")
    if sa["how"] != "nothing" and not any(ln.get("kind") == "set-aside" and ln.get("set_aside", {}).get("window") == sa.get("window") for ln in mine):
        p.append("the record of what has been opened does not hold what this exploration set aside")
    for e in ev:
        d = e["data"]
        if e["kind"] == "look.run":
            if sf.sha_file(x.d / f"receipts/{d['id']}.json") != d["receipt_sha"]:
                p.append(f"the receipt of {d['id']} is missing or was changed")
            if sf.sha_file(x.d / f"receipts/{d['id']}.out.txt") != d["output_sha"]:
                p.append(f"the output of {d['id']} is missing or was changed")
        elif e["kind"] == "review.verdict" and sf.sha_file(x.d / d["file"]) != d["sha"]:
            p.append(f"review {d['n']} ({d['file']}) is missing or was changed")
        elif e["kind"] == "note.raised" and sf.sha_file(x.d / "notes" / f"{d['id']}.json") != d["sha"]:
            p.append(f"{d['id']} is missing or was changed (the log keeps its words)")
    lead = last(ev, "lead.recorded")
    if lead:
        for name, key in (("lead.json", "json_sha"), ("lead.md", "md_sha")):
            if sf.sha_file(x.d / name) != lead["data"][key]:
                p.append(f"{name} is not the lead the log recorded")
    over = last(ev, "handed.over")
    if over and sf.sha_file(x.d / "hand-over/request.md") != over["data"]["request_sha"]:
        p.append("hand-over/request.md is not what was handed over")
    p += [f"set-aside data is in the workspace ({q})" for q in set_aside_present(sa)]
    p += [f"set-aside data reached the exploration at {e['data']['look']}: {'; '.join(e['data']['what'][:2])}" for e in breached(ev)]
    for mark in posted or []:
        seq, _, h = str(mark).partition(":")
        if not (seq.isdigit() and int(seq) < len(ev) and ev[int(seq)]["hash"] == h):
            p.append(f"the log does not contain the posted fingerprint {mark}")
    return p


def cmd_check_log(x: Exploration, a) -> None:
    problems = check_log(x, a.anchor)
    for q in problems:
        print("check-log:", q)
    if problems:
        raise Refused(f"{len(problems)} problem(s): the exploration log or its files do not check out")
    ev = x.events()
    print(f"check-log: PASS ({WAY}; {len(ev)} events, fingerprint {ev[-1]['seq']}:{ev[-1]['hash']}). As with the study log, "
          "a rewritten log shows only against a commit or a fingerprint posted outside the workspace.")


def cmd_fingerprint(x: Exploration, a) -> None:
    ev = x.events()
    if not ev:
        raise Refused("the exploration is not started")
    print(f"{ev[-1]['seq']}:{ev[-1]['hash']}")


# ---- the self-test --------------------------------------------------------
class A:
    def __init__(self, **kw):
        defaults = dict(by="agent:tester-analysis", how="a later period", set_aside_window="2025-04-28:", working_window="2024-01-01:2024-12-31",
                        set_aside_sites=None, set_aside_release=None, set_aside_path=None, nothing_set_aside=None, time_keys=None,
                        subject="reach_id=R1,gauge=G1", working="calendar 2024", why="the next period, never read", studies=None,
                        asked_by=None, question="How well does A follow B?", id="EXPLORATION-T", request=None, anchor=None,
                        why_look=None, look=None, alternative=None, evidence=None, file=None, summary=None, comment=None, ref=None,
                        bundle=[], drafts=[], tag=[], takes=None)
        self.__dict__.update(defaults)
        self.__dict__.update(kw)


def _refusal(fn, *args) -> str:
    try:
        fn(*args)
    except Refused as r:
        return str(r) or "refused"
    return ""


def selftest() -> int:
    import contextlib
    import io
    results = []

    def ok(name: str, cond) -> None:
        results.append((name, bool(cond)))

    def quiet(fn, *args):
        with contextlib.redirect_stdout(io.StringIO()):
            return fn(*args)

    def said(fn, *args) -> str:
        with contextlib.redirect_stdout(io.StringIO()):
            return _refusal(fn, *args)

    tmp = Path(tempfile.mkdtemp(prefix="explore-selftest-")).resolve()
    try:
        work = tmp / "work"
        (work / "explorations").mkdir(parents=True)
        req = tmp / "request.md"
        req.write_text("# Request\n\nHow well does A follow B, and where does it not?\n")
        bundle = tmp / "bundle"
        (bundle / "gotchas").mkdir(parents=True)
        (bundle / "index.md").write_text('---\nokf_version: "0.2"\n---\n\n# toy bundle\n')
        (bundle / "gotchas" / "follow-datum.md").write_text(
            "---\ntype: dataset-gotcha\nspheres: [hydrosphere]\ntitle: \"A and B are on different datums\"\n"
            "description: \"how A follows B is not a level\"\ntags: [a, b, datum, follow]\n"
            "generated: { by: claude-code/test, at: 2026-01-01T00:00:00Z }\nverified: { by: human:toy-steward, at: 2026-01-02T00:00:00Z }\n"
            "status: stable\n---\n\n# A and B\n\nScore changes, not levels.\n")
        data = tmp / "a_b_2024.json"
        data.write_text(json.dumps({"window": {"start": "2024-01-01", "end": "2024-12-31"}, "retrieved": "2026-09-08T00:00:00Z",
                                    "rows": [{"time": f"2024-{m:02d}-15T00:00:00Z", "a": m * 1.0, "b": m * 1.1} for m in range(1, 13)]}))
        later = tmp / "a_b_later.json"
        later.write_text(json.dumps({"rows": [{"time": "2025-06-01T00:00:00Z", "a": 1.0, "b": 1.0}]}))
        declared = tmp / "a_b_declared.json"
        declared.write_text(json.dumps({"window": {"start": "2025-01-01", "end": "2025-12-31"}, "rows": []}))

        def fresh(name: str, **kw) -> Exploration:
            x = Exploration(work / "explorations" / name)
            quiet(cmd_start, x, A(request=str(req), id=name, **kw))
            return x

        def script(x: Exploration, name: str, body: str) -> str:
            (x.d / "looks" / name).write_text(body)
            return f"looks/{name}"

        def look(x: Exploration, words: list, why: str = "to see how A follows B", by: str = "agent:tester-analysis"):
            return said(cmd_look, x, A(argv=["--", *words], why=why, by=by))

        # ---- the start: data is set aside first -------------------------------------------------------
        x0 = Exploration(work / "explorations" / "E-NONE")
        ok("start is refused when nothing is set aside", "names a window" in said(cmd_start, x0, A(request=str(req), set_aside_window=None)))
        ok("a refused start writes nothing", not x0.log.exists() and not (work / "studies" / "openings.jsonl").exists())
        ok("start is refused when the way of holding out is not one of the listed ways",
           "how the data is held out" in said(cmd_start, x0, A(request=str(req), how="my own way")))
        ok("start is refused when the working window overlaps what is set aside",
           "overlap" in said(cmd_start, x0, A(request=str(req), working_window="2025-01-01:2025-12-31")))
        ok("start is refused without a request", "request" in said(cmd_start, x0, A(request=None)))
        ok("start is refused without a reason for what is set aside", "why" in said(cmd_start, x0, A(request=str(req), why="")))
        ok("start is refused when the question is not a question", "not a question" in said(cmd_start, x0, A(request=str(req), question="Look at A")))
        ok("start is refused for a name that is not an actor", "actor" in said(cmd_start, x0, A(request=str(req), by="someone")))
        early = tmp / "held" / "later.json"
        early.parent.mkdir()
        early.write_text("{}")
        ok("start is refused when the set-aside data is already in the workspace",
           "already here" in said(cmd_start, x0, A(request=str(req), set_aside_path=[str(early)])))
        early.unlink()
        x = fresh("E-1", set_aside_path=[str(early)])
        record = work / "studies" / "openings.jsonl"
        lines = record_lines(record)
        ok("start writes what is set aside to the record beside the studies",
           any(ln.get("kind") == "set-aside" and ln["set_aside"]["window"]["start"] == "2025-04-28" for ln in lines))
        ok("start writes what will be explored to the same record, in the form the study tool reads",
           any(ln.get("kind") == "explored" and ln.get("key") == subject_key({"reach_id": "R1", "gauge": "G1"})
               and ln.get("window") == {"start": "2024-01-01", "end": "2024-12-31"} for ln in lines))
        ok("the set-aside line carries no `key`, so the study tool does not count the set-aside data as opened",
           all("key" not in ln for ln in lines if ln.get("kind") == "set-aside"))
        ok("a second start in the same directory is refused", "already started" in said(cmd_start, x, A(request=str(req))))
        ok("a second exploration cannot set aside a window the first one explored",
           "cannot be set aside" in said(cmd_start, Exploration(work / "explorations" / "E-AGAIN"),
                                         A(request=str(req), set_aside_window="2024-06-01:2024-12-31", working_window="2023-01-01:2023-12-31")))
        ok("the request is bound by checksum", x.started()["data"]["request"]["sha"] == sf.sha_file(req))

        # ---- knowledge before looking --------------------------------------------------------------
        s1 = script(x, "pairs.py", "import json, sys\nd = json.load(open(sys.argv[1]))\nprint('rows', len(d['rows']))\n")
        ok("the first look is refused until the knowledge has been listed", "run `known` first" in look(x, ["{python}", s1, str(data)]))
        quiet(cmd_known, x, A(bundle=[str(bundle)], question=None))
        listed = last(x.events(), "knowledge.listed")["data"]["concepts"]
        ok("`known` logs the concepts that bear on the question, each with who signed it",
           len(listed) == 1 and listed[0]["signed"] and listed[0]["signed_by"] == ["human:toy-steward"])
        quiet(cmd_read, x, A(concept=str(bundle / "gotchas" / "follow-datum.md"), takes="score changes, not levels"))
        ok("`read` records what was read, by checksum", last(x.events(), "knowledge.read")["data"]["sha256"] == sf.sha_file(bundle / "gotchas" / "follow-datum.md"))

        # ---- looks: logged, and the fence ------------------------------------------------------------
        ok("a look on working data runs, though the file's retrieval date falls in the open set-aside window (only the declared time keys are data)",
           look(x, ["{python}", s1, str(data)]) == "")
        e = last(x.events(), "look.run")
        ok("the look is logged with the data by checksum", e["data"]["inputs"] and any(i["sha256"] == sf.sha_file(data) for i in e["data"]["inputs"]))
        ok("the look is logged with its script by checksum and what came out",
           e["data"]["script_sha"] == sf.sha_file(x.d / s1) and "rows 12" in e["data"]["out_head"])
        ok("a logged look reproduces when it is run again, and the recheck adds nothing to the log",
           (lambda n: said(cmd_recheck, x, A(look="LOOK-001")) == "" and len(x.events()) == n)(len(x.events())))
        ok("a look writes a receipt that says exploring", json.loads((x.d / "receipts/LOOK-001.json").read_text())["way"] == WAY)
        ok("a look without a reason is refused", "what this look is trying" in look(x, ["{python}", s1, str(data)], why=""))
        ok("a look through a shell is refused", "not a launcher" in look(x, ["bash", "-c", "cat x"]))
        ok("a look through `python -c` is refused", "followed directly by the script" in look(x, ["{python}", "-c", "print(1)"]))
        before = len(x.events())
        ok("a look that names data inside the set-aside window is refused", "set aside" in look(x, ["{python}", s1, str(later)]))
        ok("the refusal is logged", len(x.events()) == before + 1 and x.events()[-1]["kind"] == "look.refused")
        ok("a look that names a data file whose declared window overlaps the set-aside window is refused",
           "its window" in look(x, ["{python}", s1, str(declared)]))
        ok("a look that passes a date inside the set-aside window is refused",
           "date inside the set-aside window" in look(x, ["{python}", s1, str(data), "--start", "2025-05-01"]))
        ok("a look that names the set-aside path is refused", "set-aside path" in look(x, ["{python}", s1, str(early)]))
        s2 = script(x, "fetch_later.py", "START = '2025-05-01'\nprint('would fetch from', START)\n")
        ok("a look whose script names a date inside the set-aside window is refused", "date inside" in look(x, ["{python}", s2]))
        s3 = script(x, "sneak.py", "import json\njson.dump({'rows': [{'time': '20' + '25-07-01T00:00:00Z', 'a': 1}]}, open('got.json', 'w'))\n")
        ok("a look that leaves set-aside data in the exploration spoils it", "spoiled" in look(x, ["{python}", s3]))
        ok("the breach is logged", last(x.events(), "fence.breached") is not None)
        ok("a spoiled exploration takes no more looks", "spoiled" in look(x, ["{python}", s1, str(data)]))
        ok("a spoiled exploration cannot record a lead", "spoiled" in said(cmd_lead, x, A(file=str(req))))
        ok("a spoiled exploration cannot end as a lead", "spoiled" in said(cmd_end, x, A(outcome="lead", summary="x")))
        quiet(cmd_end, x, A(outcome="stop", summary="set-aside data reached the exploration"))
        ok("a spoiled exploration can end as a stop, and nothing is handed over from it",
           "nothing is handed over" in said(cmd_hand_over, x, A(by="agent:tester-coordinating", study_id="STUDY-T")))
        ok("check-log names the breach", any("reached the exploration" in q for q in check_log(x)))

        # ---- sites and releases ----------------------------------------------------------------------
        xs = fresh("E-SITES", how="sites never opened", set_aside_window=None, set_aside_sites="G7,G8", working_window=None,
                   subject="reach_id=R2,gauge=G2")
        quiet(cmd_known, xs, A(bundle=[str(bundle)], question=None))
        ss = script(xs, "p.py", "print('ok')\n")
        site_file = tmp / "sites.json"
        site_file.write_text(json.dumps({"gauge": "g7", "rows": []}))
        ok("a look that names a set-aside site is refused", "set aside" in look(xs, ["{python}", ss, "--gauge", "G7"]))
        ok("a look on a data file that holds a set-aside site is refused", "set aside" in look(xs, ["{python}", ss, str(site_file)]))
        xr = fresh("E-REL", how="a new release", set_aside_window=None, set_aside_release=["PRODUCT_v3"], working_window=None,
                   subject="reach_id=R3,gauge=G3")
        quiet(cmd_known, xr, A(bundle=[str(bundle)], question=None))
        sr = script(xr, "p.py", "print('ok')\n")
        ok("a look that names a set-aside release is refused", "set aside" in look(xr, ["{python}", sr, "--collection", "product_V3"]))
        ok("a look that names another release runs", look(xr, ["{python}", sr, "--collection", "PRODUCT_v2"]) == "")
        xn = fresh("E-NOTHING", nothing_set_aside="one record and all of it has been seen", set_aside_window=None, working_window=None,
                   subject="reach_id=R4,gauge=G4")
        ok("an exploration with nothing set aside says so and writes no set-aside line",
           xn.set_aside()["how"] == "nothing" and not any(ln.get("exploration") == "E-NOTHING" and ln.get("kind") == "set-aside" for ln in record_lines(record)))

        # ---- choices, notes, the lead ----------------------------------------------------------------
        y = fresh("E-2", subject="reach_id=R5,gauge=G5")
        quiet(cmd_known, y, A(bundle=[str(bundle)], question=None))
        sy = script(y, "pairs.py", "import json, sys\nd = json.load(open(sys.argv[1]))\nprint('rows', len(d['rows']))\n")
        sbad = script(y, "broken.py", "raise SystemExit(3)\n")
        look(y, ["{python}", sy, str(data)])
        look(y, ["{python}", sbad])
        look(y, ["{python}", sy, str(later)])
        ok("a choice without an alternative is refused", "alternative" in said(cmd_choice, y, A(choice="pair within 15 minutes", alternative=[], rests_on="x")))
        quiet(cmd_choice, y, A(choice="pair within 15 minutes", alternative=["60 minutes", "nearest reading"], rests_on="the gauge reports every 15 minutes", look="LOOK-001"))
        quiet(cmd_choice, y, A(choice="drop passes flagged degraded", alternative=["keep all"], rests_on="one degraded pass at low stage", look="LOOK-001"))
        ok("a choice is logged with its alternatives and what it rests on",
           last(y.events(), "choice.recorded")["data"]["alternatives"] == ["keep all"])
        quiet(cmd_note, y, A(kind="missing", about="the A product", text="the flag is not described", evidence="receipts/LOOK-001.json"))
        ok("a note is a file and a log event, and says it comes from exploring",
           json.loads((y.d / "notes/NOTE-001.json").read_text())["way"] == WAY and last(y.events(), "note.raised")["data"]["text"])
        lead = {"what_looks_true": "A follows B closely over the year, on changes.", "how_it_was_found": "By pairing the two records and scoring changes.",
                "evidence": ["LOOK-001"], "choices_that_would_change_it": [{"choice": "CHOICE-002", "how": "keeping all moves the gain"}],
                "choices_that_would_not": [], "pitfalls": ["levels are on different datums"],
                "proposed_plan": {"question": "Is the gain of A on B within five percent of one?", "quantity_estimated": "the gain",
                                  "difference_that_matters": "five percent", "rule_sketch": "interval inside 0.95 to 1.05"}}
        lf = y.d / "lead.yaml"
        lf.write_text(yaml.safe_dump(lead))
        ok("a lead that leaves a recorded choice unplaced is refused", "does not say whether it would change" in said(cmd_lead, y, A(file=str(lf))))
        lead["choices_that_would_not"] = [{"choice": "CHOICE-001", "why": "60 minutes gives the same pairs"}]
        lead["evidence"] = ["LOOK-002"]
        lf.write_text(yaml.safe_dump(lead))
        ok("a lead that rests on a failed look is refused", "which failed" in said(cmd_lead, y, A(file=str(lf))))
        lead["evidence"] = ["LOOK-009"]
        lf.write_text(yaml.safe_dump(lead))
        ok("a lead that rests on a look that is not in the log is refused", "not in the log" in said(cmd_lead, y, A(file=str(lf))))
        lead["evidence"] = ["LOOK-001"]
        lf.write_text(yaml.safe_dump({k: v for k, v in lead.items() if k != "proposed_plan"}))
        ok("a lead without a proposed plan is refused", "proposed_plan" in said(cmd_lead, y, A(file=str(lf))))
        lf.write_text(yaml.safe_dump(lead))
        ok("ending as a lead before a lead is recorded is refused", "no lead" in said(cmd_end, y, A(outcome="lead", summary="x")))
        ok("a review before there is anything to review is refused", "nothing to review" in said(cmd_review, y, A(by="agent:tester-review", verdict="holes-found", file=str(req))))
        quiet(cmd_lead, y, A(file=str(lf)))
        got = json.loads((y.d / "lead.json").read_text())
        ok("the lead counts what was tried from the log, not from the lead file",
           got["tried"] == {"looks": 2, "failed": 1, "refused": 1, "ids": ["LOOK-001", "LOOK-002"]})
        ok("the lead says it is exploring and is not a finding", got["way"] == WAY and "not a finding" in got["status"]
           and "not a finding" in (y.d / "lead.md").read_text() and "cannot be signed" in (y.d / "lead.md").read_text())
        ok("the lead carries the knowledge that was read and what was set aside", got["set_aside"]["window"]["start"] == "2025-04-28" and got["knowledge_read"] == [])
        ok("there is no command that signs, locks or attaches a finding",
           not {"signature", "sign", "lock", "attach", "open-held-out"} & set(build_parser()._subparsers._group_actions[0].choices))

        # ---- review, end, hand-over ------------------------------------------------------------------
        ok("the hand-over is refused before the exploration has ended as a lead",
           "has not ended as a lead" in said(cmd_hand_over, y, A(by="agent:tester-coordinating", study_id="STUDY-T")))
        vf = tmp / "verdict.md"
        vf.write_text("# Review (exploring)\n\nHoles: the gain rests on one year.\n")
        ok("the assistant that explored cannot review its own lead", "did part of this exploration" in said(cmd_review, y, A(verdict="holes-found", file=str(vf))))
        ok("the same assistant under another case of its name cannot either",
           "did part of this exploration" in said(cmd_review, y, A(by="agent:TESTER-analysis", verdict="holes-found", file=str(vf))))
        ok("a verdict outside the two is refused", "one of" in said(cmd_review, y, A(by="agent:tester-review", verdict="approve", file=str(vf))))
        quiet(cmd_review, y, A(by="agent:tester-review", verdict="holes-found", file=str(vf)))
        ok("status after a review sends the work back to the analysis assistant", stage_of(y)["stage"] == "revise-or-end")
        quiet(cmd_lead, y, A(file=str(lf)))
        ok("a revised lead is a new version, and the first is kept", (y.d / "leads/lead-v1.json").is_file() and json.loads((y.d / "lead.json").read_text())["version"] == 2)
        quiet(cmd_end, y, A(outcome="lead", summary="A follows B on changes; worth a test"))
        ok("the hand-over is refused until the latest lead has been reviewed",
           "no review assistant has looked at the latest lead" in said(cmd_hand_over, y, A(by="agent:tester-coordinating", study_id="STUDY-T")))
        ok("status names the review assistant when the latest lead is not reviewed", stage_of(y)["who"] == "review assistant")
        quiet(cmd_review, y, A(by="agent:tester-review", verdict="no-holes-found", file=str(vf)))
        ok("after the end nothing more is looked at", "has ended" in look(y, ["{python}", sy, str(data)]))
        ok("the assistant that explored cannot make the hand-over", "did the exploring" in said(cmd_hand_over, y, A(study_id="STUDY-T")))
        ok("the hand-over refuses the exploration's own name for the study", "study-id" in said(cmd_hand_over, y, A(by="agent:tester-coordinating", study_id="E-2")))
        quiet(cmd_hand_over, y, A(by="agent:tester-coordinating", study_id="STUDY-T"))
        ho = json.loads((y.d / "hand-over/hand-over.json").read_text())
        ok("the hand-over holds what `sf.py start` needs: an id, a question, a request by checksum",
           ho["study_id"] == "STUDY-T" and ho["question"].endswith("?") and ho["request"]["sha256"] == sf.sha_file(y.d / "hand-over/request.md"))
        ok("the handed-over request says where it came from and that the lead is not a finding",
           "exploring, not a finding" in (y.d / "hand-over/request.md").read_text())
        ok("nothing is handed over from an exploration that set nothing aside",
           "nothing was set aside" in said(cmd_hand_over, xn, A(by="agent:tester-coordinating", study_id="STUDY-N")))

        # ---- the confirming study keeps the fence ----------------------------------------------------
        study = sf.Study(work / "studies" / "STUDY-T")
        quiet(sf.cmd_start, study, argparse.Namespace(id="STUDY-T", question=ho["question"], by="agent:tester-coordinating",
                                                      request=str(y.d / "hand-over/request.md"), asked_by=None))
        ok("the study tool starts a study from the hand-over", study.events()[0]["data"]["request"]["sha"] == ho["request"]["sha256"])
        ok("check-study waits for the plan", any("no analysis plan yet" in q for q in study_problems(y, study.d)))

        def plan(window: dict, pair: dict | None = None) -> None:
            study.plan_path.write_text(yaml.safe_dump({
                "study": "STUDY-T", "question": ho["question"],
                "data": {"working": "calendar 2024", "held_out": {"window": window, "pair": pair or {"reach_id": "R5", "gauge": "G5"},
                                                                  "path": "data/held.json"}},
                "tests": {"held-out": {"fetch": ["{python}", "f.py"], "command": ["{python}", "c.py"], "receipt": "receipts/held-out.json"}}}))

        plan({"start": "2025-04-28", "end": "2026-04-27"})
        ok("a plan that holds out what was set aside passes check-study", study_problems(y, study.d) == [])
        plan({"start": "2024-01-01", "end": "2024-12-31"})
        problems = study_problems(y, study.d)
        ok("a plan that holds out the explored window is refused", any("cannot be used to confirm" in q for q in problems))
        ok("the study tool's own record, unedited, also says that window was already looked at",
           any("already looked at by E-2" in q for q in problems)
           and sf.earlier_openings(study, study.plan(), study.plan()["tests"]["held-out"], study.events())[0]["study"] == "E-2")
        plan({"start": "2024-10-01", "end": "2025-10-01"})
        ok("a plan whose held-out window only partly leaves the explored window is refused", any("cannot be used to confirm" in q for q in study_problems(y, study.d)))
        plan({"start": "2025-01-01", "end": "2025-04-27"})
        ok("a plan that holds out data nobody set aside is refused", any("not inside what the exploration set aside" in q for q in study_problems(y, study.d)))
        plan({"start": "2025-04-28", "end": "2026-04-27"}, {"reach_id": "R5", "gauge": "another"})
        ok("a plan about another subject is refused", any("not the subject of this exploration" in q for q in study_problems(y, study.d)))
        plan({"start": "2025-04-28", "end": "2026-04-27"}, {"Reach_ID": " r5", "GAUGE": "g5 "})
        ok("the subject matches through spacing and case, as in the study tool", study_problems(y, study.d) == [])
        other = sf.Study(tmp / "elsewhere" / "STUDY-T")
        quiet(sf.cmd_start, other, argparse.Namespace(id="STUDY-T", question=ho["question"], by="agent:tester-coordinating",
                                                      request=str(y.d / "hand-over/request.md"), asked_by=None))
        ok("a study that does not sit beside the record is refused", any("does not sit beside the record" in q for q in study_problems(y, other.d)))
        loose = sf.Study(work / "studies" / "STUDY-LOOSE")
        quiet(sf.cmd_start, loose, argparse.Namespace(id="STUDY-LOOSE", question=ho["question"], by="agent:tester-coordinating", request=str(req), asked_by=None))
        ok("a study that was not started from the hand-over is refused", any("not started from this exploration's hand-over" in q for q in study_problems(y, loose.d)))
        (study.d / "finding").mkdir()
        shutil.copyfile(y.d / "lead.md", study.d / "finding" / "finding.md")
        ok("a lead attached to a study as its finding is refused by the study tool before any opening",
           _refusal(lambda: quiet(sf.cmd_attach, study, argparse.Namespace(by="agent:tester-analysis", file=str(study.d / "finding" / "finding.md")))) != "")

        # ---- notes for curating, status, the log ------------------------------------------------------
        quiet(cmd_curation_list, y, A())
        cl = json.loads((y.d / "curation-list.json").read_text())
        ok("the curation list holds the open notes and says a lead is never drafted as a finding",
           cl["open_notes"] == 1 and "never drafted as a finding" in cl["contract"] and cl["way"] == WAY)
        ok("status after the hand-over sends the notes to the curating assistant", stage_of(y)["stage"] == "learn" and stage_of(y)["who"] == "curating assistant")
        ok("a drafted note names its draft", "names the draft" in said(cmd_resolve, y, A(by="agent:tester-curating", note="NOTE-001", disposition="drafted", ref=None)))
        quiet(cmd_resolve, y, A(by="agent:tester-curating", note="NOTE-001", disposition="drafted", ref="knowledge-queue/gotchas/a-flag.md"))
        ok("a resolved note leaves the list, and the exploration is then ended", stage_of(y)["stage"] == "ended" and stage_of(y)["handed_over_to"] == "STUDY-T")
        ok("a finished exploration checks out", check_log(y) == [])
        ok("every event in the log says exploring", all(e["data"].get("way") == WAY for e in y.events()))
        written = [p for p in y.d.rglob("*") if p.is_file() and p.suffix in (".json", ".md", ".yaml", ".txt") and p.name not in ("request.md", "lead.yaml")
                   and "looks" not in p.parts and p.parent.name != "verdicts"]
        silent = [p.relative_to(y.d).as_posix() for p in written if "xploring" not in p.read_text()]
        ok("every file the tool wrote says exploring" + (f" (not: {silent})" if silent else ""), written and not silent)
        fp = f"{y.events()[3]['seq']}:{y.events()[3]['hash']}"
        ok("check-log accepts a fingerprint the log contains", check_log(y, [fp]) == [])
        ok("check-log refuses a fingerprint the log does not contain", any("posted fingerprint" in q for q in check_log(y, ["3:" + "0" * 64])))
        keep = y.log.read_text()
        (y.d / "receipts/LOOK-001.out.txt").write_text("edited")
        ok("check-log catches an edited output", any("output of LOOK-001" in q for q in check_log(y)))
        (y.d / "lead.md").write_text((y.d / "lead.md").read_text().replace("not a finding", "a finding"))
        ok("check-log catches a lead edited to read as a finding", any("lead.md is not the lead" in q for q in check_log(y)))
        lines_ = keep.splitlines()
        y.log.write_text("\n".join(ln.replace("to see how", "to see hov") for ln in lines_) + "\n")
        ok("check-log catches an edited log line", any("broken at event" in q for q in check_log(y)))
        y.log.write_text(keep)
        record.write_text("\n".join(ln for ln in record.read_text().splitlines() if '"E-2"' not in ln) + "\n")
        ok("check-log catches the exploration's lines being taken out of the record", any("explored line" in q for q in check_log(y)))
        early.write_text("{}")
        ok("check-log catches set-aside data arriving in the workspace later", any("set-aside data is in the workspace" in q for q in check_log(x)))
        z = fresh("E-3", subject="reach_id=R6,gauge=G6")
        ok("status before the knowledge is listed says to read what is known", stage_of(z)["stage"] == "read-what-is-known")
        ok("status of a directory with no exploration says to set data aside", stage_of(Exploration(work / "explorations" / "E-NEW"))["stage"] == "set-aside")
        quiet(cmd_known, z, A(bundle=[str(bundle)], question=None))
        quiet(cmd_note, z, A(kind="dead-end", about="the method", text="pairing at 5 minutes leaves too few pairs", evidence=None))
        quiet(cmd_end, z, A(outcome="note", summary="a dead end worth recording"))
        ok("an exploration can end as a note", last(z.events(), "exploration.ended")["data"]["outcome"] == "note")
        ok("an exploration that ended as a note hands nothing over", "has not ended as a lead" in said(cmd_hand_over, z, A(by="agent:tester-coordinating", study_id="STUDY-Z")))
        m = fresh("E-4", subject="reach_id=R7,gauge=G7")
        ok("ending as a method names the method's script", "names the method" in said(cmd_end, m, A(outcome="method", summary="a method", file=None)))
        sm = script(m, "method.py", "print('m')\n")
        quiet(cmd_end, m, A(outcome="method", summary="a method that pairs passes", file=sm))
        ok("an exploration can end as a method, bound by checksum", last(m.events(), "exploration.ended")["data"]["method"]["sha256"] == sf.sha_file(m.d / sm))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, good in results if not good]
    for n in failed:
        print("FAIL:", n)
    print(f"selftest: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)} of {len(results)})")
    return 0 if not failed else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, *args):
        p = sub.add_parser(name)
        p.add_argument("--exploration", required=True, help="the exploration directory")
        for names, kw in args:
            p.add_argument(*names, **kw)
        p.set_defaults(fn=fn)
        return p

    by = (["--by"], {"required": True, "help": "who acts: agent:<id> (or human:<id> for a person exploring)"})
    add("start", cmd_start, by, (["--id"], {"required": True}), (["--question"], {"required": True}),
        (["--request"], {"required": True, "help": "the request, in the scientist's own words; bound by checksum"}),
        (["--subject"], {"required": True, "help": "key=value,key=value: what the data is about, as a plan's `pair` will say it"}),
        (["--how"], {"default": None, "help": "how the data is held out: " + "; ".join(HOW)}),
        (["--set-aside-window"], {"default": None, "help": "START:END, or START: for a window that stays open"}),
        (["--set-aside-sites"], {"default": None, "help": "site identifiers, separated by commas"}),
        (["--set-aside-release"], {"action": "append", "default": None, "help": "a release, collection or record name; repeatable"}),
        (["--set-aside-path"], {"action": "append", "default": None, "help": "where the set-aside data would land if fetched; repeatable"}),
        (["--nothing-set-aside"], {"default": None, "help": "the reason nothing can be set aside; such an exploration hands nothing over"}),
        (["--why"], {"default": None, "help": "why this is the data to set aside"}),
        (["--working"], {"default": None, "help": "what will be explored, in words"}),
        (["--working-window"], {"default": None, "help": "START:END of the data that will be explored"}),
        (["--time-keys"], {"default": None, "help": "the keys under which a data file carries its times (default: " + ",".join(TIME_KEYS) + ")"}),
        (["--studies"], {"default": None, "help": "the folder of confirming studies, where the record is (default: ../../studies from the exploration)"}))
    add("known", cmd_known, by, (["--bundle"], {"action": "append", "required": True, "help": "a knowledge bundle; repeatable"}),
        (["--drafts"], {"action": "append", "default": None, "help": "a queue of drafted pages, listed as drafts; repeatable"}),
        (["--question"], {"default": None}), (["--tag"], {"action": "append", "default": None}))
    add("read", cmd_read, by, (["--concept"], {"required": True}), (["--takes"], {"required": True, "help": "what this concept rules in, rules out or warns about, for this question"}))
    look = add("look", cmd_look, by, (["--why"], {"required": True, "help": "what this look is trying to find out"}))
    look.add_argument("argv", nargs=argparse.REMAINDER, help="-- LAUNCHER SCRIPT [arguments]")
    add("recheck", cmd_recheck, (["--look"], {"required": True, "help": "the look to run again, such as LOOK-003"}))
    add("choice", cmd_choice, by, (["--choice"], {"required": True}), (["--alternative"], {"action": "append", "default": None}),
        (["--rests-on"], {"required": True, "dest": "rests_on"}), (["--look"], {"default": None}))
    add("note", cmd_note, by, (["--kind"], {"required": True}), (["--about"], {"required": True}), (["--text"], {"required": True}),
        (["--evidence"], {"default": None}))
    add("lead", cmd_lead, by, (["--file"], {"required": True, "help": "the lead file (YAML)"}))
    add("review", cmd_review, by, (["--verdict"], {"required": True, "help": " or ".join(VERDICTS)}), (["--file"], {"required": True}))
    add("end", cmd_end, by, (["--outcome"], {"required": True, "help": ", ".join(OUTCOMES)}), (["--summary"], {"required": True}),
        (["--file"], {"default": None}))
    add("hand-over", cmd_hand_over, by, (["--study-id"], {"required": True, "dest": "study_id"}))
    add("check-study", cmd_check_study, (["--study"], {"required": True}))
    add("curation-list", cmd_curation_list)
    add("resolve", cmd_resolve, by, (["--note"], {"required": True}), (["--disposition"], {"required": True, "help": ", ".join(DISPOSITIONS)}),
        (["--ref"], {"default": None}), (["--comment"], {"default": None}))
    add("status", cmd_status)
    add("check-log", cmd_check_log, (["--anchor"], {"action": "append", "default": None, "help": "SEQ:HASH posted outside the workspace; repeatable"}))
    add("fingerprint", cmd_fingerprint)
    sub.add_parser("selftest")
    return ap


def main() -> int:
    a = build_parser().parse_args()
    try:
        sf.refuse_dirty_environment()
        if a.cmd == "selftest":
            return selftest()
        a.fn(Exploration(a.exploration), a)
    except Refused as r:
        print(f"REFUSED: {r}", file=sys.stderr)
        return 2
    except (KeyError, TypeError, ValueError, AttributeError, OSError) as e:
        print("REFUSED: a file in the exploration is malformed or missing, and the tool could not read it. Run check-log to "
              f"find which (for whoever maintains the tool: {type(e).__name__}: {e})", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
