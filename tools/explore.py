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
     hash like the study log (the same code: this tool imports sf.py,
     which sits beside it in tools/).
     A look that names what was set aside, or names anything in a way the
     tool cannot confine, is refused, and the refusal is logged. A look runs
     in a scratch folder that holds only what its command names.
  3. Choices are recorded with their alternatives and what they rest on,
     and the log keeps when: the lead sets every choice beside the looks
     that had already run when it was written down, so a choice logged
     after the looks it governs reads as one.
  4. It ends in a lead, a note, a method or a stop. A lead says what looks
     true, how it was found, how many things were tried (counted from the
     log, not remembered), which choices would change it, and a proposed
     plan for a confirming study. A lead that quotes a decimal number that
     none of the looks it cites printed, as a whole number and not as part
     of a longer one, and that no knowledge page recorded as read holds,
     is refused. `hand-over` writes what `sf.py start` needs, and
     `check-study` refuses a study whose held-out data is not inside what
     was set aside or touches what was explored.
  5. Everything it writes says "exploring" on it. There is no command here
     that signs anything, and a lead is never a finding.

The order of work the tool holds. Before the start, only knowledge is
read (`knowledge.py about`, which reads pages and never data), so that the
boundary of what is set aside comes from a page and not from a guess.
`start` sets data aside. `known` and `read` then write into the log what
was listed and read; the first look is refused until they have. Looks,
choices and notes follow in any order. `reviewer` names who will review,
and is run by whoever coordinates, not by whoever explores. `lead` records
a lead, and is refused until a reviewer is named; the named reviewer
reviews it; a revised lead, and a lead corrected after its review, is
reviewed again. `end` as a lead is refused until the lead as it stands has
been reviewed, and `resolve` (the
curating agent's) is refused until the exploration has ended. Logs
written before the tool held this order still check out; `check-log` says
in a remark where an old log departs from it.

An exploration is one directory: exploration-log.jsonl, set-aside.json,
request.md, the scripts of its looks, receipts/, figures/, notes/, review/
(where the review agent writes), verdicts/ (the tool's copy of each
review, which is the record), the lead, and hand-over/. By convention explorations sit in `explorations/`
beside `studies/`, and the record is `studies/openings.jsonl`.

Commands.

  start          set data aside, bind the request, write the record
  fit            the coordinating agent's fit note at intake, before the first
                 look: how well the question suits agents, a verdict, and what
                 it needs from a person; advice that blocks nothing
  known          list the knowledge that bears on the question (calls
                 knowledge.py) and log what was listed; the first look is
                 refused until this has run
  read           say which concepts were read and what each changes
  look           run one script on working data; logged with checksums
  recheck        run a logged look again, on the same files by checksum, and
                 compare the output; adds nothing to the log (for the
                 review agent), and says what was pinned
  choice         a choice, its alternatives, what it rests on
  note           something missing or wrong in the data or the knowledge
  lead           record the lead from a lead file (YAML)
  correct        replace one phrase in the recorded lead without a new
                 version: no number may change, and the lead shows the
                 old and the new words; a correction made after a review
                 undoes that review
  reviewer       whoever coordinates the work names who will review, before a
                 lead exists; `lead` is refused until this has run
  review         a reviewer named that way, who did none of the exploring,
                 records whether it found holes, in the lead it read, which
                 it names by checksum (--read-lead)
  ask-so-what    an agent drafts the question a person is asked about a
                 reviewed lead: what it shows, why it might matter, what would
                 make it unremarkable
  so-what        a person's answer to the reviewed lead: worth-confirming,
                 try-instead (a direction), not-interesting (a reason; the
                 exploration ends as a lead noted) or needs-an-expert (which
                 kind). Typed it is practice; on the platform it is a person's
                 comment on the tracking issue, recorded by the job that
                 follows it (--record-comment, under platform:github)
  verify-so-what ask the platform about each so what that was a comment
  end            ended as a lead, a note, a method or a stop; as a lead only
                 after a person said the reviewed lead is worth confirming
  hand-over      what `sf.py start` needs, for a confirming study
  check-study    a study started from the lead keeps the fence
  curation-list  open notes, for the curating agent
  resolve        a note is drafted, linked or declined
  status         where the exploration stands and who is next
  check-log      everything re-checked from the files
  fingerprint    the log's fingerprint, to post outside the workspace
  promote        a look's script that proved useful becomes a method under
                 methods/<name>/: the script, the exploration's runs of it as
                 known-answer cases, the agent's README, a test file, and
                 where it came from; a change to the factory
  contribution   who did each step, from the log: a paragraph for a paper,
                 and what the log cannot show
  selftest       the tool tests itself, attacks included

What a look is. A launcher the study tool knows (`{python}` followed by a
script file, or `uv run` followed by a script file), then the script's own
arguments, exactly as in a plan. Paths in the command are read from the
exploration directory. The script does not run there. It runs in a scratch
folder made for that one look, which holds the script and the files the
command names (a file from outside the exploration is put under `outside/`
and the word that named it is rewritten) and the files given with
`--also-reads`, and nothing else: not the log, not the request, not a
neighbour of the script. `uv run` does not run the launcher beside the
script: before the look starts, uv builds a throwaway environment from the
script's own inline dependencies, from wheels only, and the script is
started with that environment's interpreter (tools/fence.py). What the
script prints is the look's output, kept by checksum; what it writes to
standard error is kept beside it and is not part of what a recheck
compares. What it writes in its folder is brought back into the
exploration, except into the places the tool or a reviewer keeps
(receipts/, verdicts/, review/, notes/, leads/, hand-over/, the log, the
lead), and except a link, which is not followed. A picture it writes into
`figures/` (.svg, .png, .pdf, .jpg) is a figure of that look: the receipt
lists it by checksum and a lead may show it. A line `comparisons: N` in the
output says how many fits or cuts the look held.

What the lead's number check covers. Numbers in the lead's own words (not
in the proposed plan, whose numbers are proposals), in these forms: 7.7777,
.8888, 8,8888, 8.888e0, 88888e-4, with a gap before the point or after it,
with a letter or a unit glued on, with a look-alike of the point (a middle
dot, an Arabic decimal mark, a full-width digit), and as a division by a
power of ten (77777/10000); and a whole number given as a share (105
percent, 105%). Each must be printed, digit for digit, whole and in that
form, by a look the lead cites, or stand in a page that was recorded as
read and lies in a wiki `known` listed. A page the explorer or any role
could have written (in the exploration, in a role's own place, in a queue
of drafts, in a study's folder, even inside a listed wiki) backs nothing.
Other whole numbers, other fractions, and numbers written out in words are
not checked: the list above is the whole of what is read.

What keeps set-aside data out of a look, in four layers, and what does not.

  What a look can be given at all. A look is given the exploration's own
  files and files in the places the exploration declared as working data
  when it started (`start --working-data`), and nothing else. A file that
  is in neither is refused whatever it holds. The declaration is the first
  event of the log, a place that is or holds a set-aside path cannot be
  declared, and the lead and the hand-over show what was declared. This,
  and not the reading of what a file holds, is the defence: data nobody
  declared as working data is not there to be named.

  Before a look runs, the tool also reads every word of the command and
  every file the look would be given: a second line, for set-aside data
  that got into the working data by mistake. It refuses a word that is a
  set-aside path, site or release, or a date inside the set-aside window;
  a site is matched the ways people write it (`USGS-06935965` set aside
  also refuses the bare `06935965`). A script or text file that names any
  of those things is refused, and so is a JSON data file whose `window`, or
  whose times, fall inside the set-aside window. Dates are read in these
  forms: year, month and day with a hyphen, a slash or a point between
  them, with or without leading zeros; the same eight digits run together;
  day or month first with the year last; a month by its English name; with
  any look-alike of a hyphen; as a key of a JSON mapping; and, under a time
  key of a JSON file, a number that is seconds or milliseconds since 1970.
  Not read: a day of the year, a week number, a month in another language,
  another calendar, a number that is a time outside a time key, and
  anything that is not text. Whatever could reach a file the tool did not
  read is refused outright and not interpreted: a folder, a pattern
  (* ? [ ] { }), a tilde path, a variable ($NAME), several paths joined
  into one word, and a path that leaves the exploration and is not an
  existing file.

  While it runs, the script is in the scratch folder described above, with
  an environment the tool builds: a fixed short list, and nothing of the
  caller's (no UV_ variable, no certificate setting, no cache folder), so
  no variable can hand it a path or widen what it may open. On Linux with
  Landlock (kernel 5.13 or later) the kernel keeps the script, and every
  process it starts, from opening anything but that folder, the system's
  own folders and its interpreter, and from writing anywhere but that
  folder. The fence is tried before the script starts: a file put outside
  for the purpose, the exploration, its log, this tool and every set-aside
  path must be unreadable, and the tool's own environment and folder
  unwritable. The receipt records that trial and what the script could
  read and write: `kernel`, or `scratch-only` with the reason. On a
  machine that has Landlock, a fence that cannot be put up or does not
  hold is a refusal, never a look that runs without it. The exploration
  log is held for as long as the script runs; the study tool, this tool
  and the knowledge tool refuse a command with a running look or a plan's
  step anywhere above it; and the script's keeper ends whatever it left
  running before the look is logged.

  After it has run, the tool reads what the look printed and every file it
  left, the same way. Output or a file that crosses the fence spoils the
  exploration (no lead and no hand-over can come from it), and that output
  is withheld: it is neither kept nor shown. A change to the exploration
  itself made from inside the script, the log included, spoils it too, and
  the log is put back as it stood.

  What it cannot do, said plainly. One user on one machine cannot be fenced
  from their own files by a program they run. Where there is no kernel
  fence (macOS, Windows, an old kernel) a script can open and write any
  path its user can, the tools and the environments they run from
  included; the tool compares those before and after each such look and
  spoils the exploration when they changed, which catches a careless script
  and not a careful one, and it catches set-aside data only when a date or
  a name comes back in the output: a script that prints a mean of set-aside
  rows and no date is not caught. `status`, the lead and the hand-over say
  how many looks ran that way. With the kernel fence, the script can still
  use the network, read what is kept in the system's folders (/etc, /usr),
  leave a file in shared memory (/dev/shm, which Python's multiprocessing
  needs; the receipt lists what appeared there), and ask a service that
  listens on a socket file to act for it. Data in the declared working
  places under a date spelling the list above does not name is not caught
  by the second line. A site under a wholly different name is not matched.
  And nothing here sees a look made outside the tool. Against all of that
  the barrier is instruction and the log. Names of who did what are typed,
  not proven, as in the study tool: the rule that a review comes from a
  reviewer named before the lead existed stops a name invented at the
  review, not a person or a process that types two names. A review names
  the lead the reviewer read by its checksum (`--read-lead`), so a verdict
  never stands for words changed while the reviewer worked.

Usage: explore.py <command> --exploration DIR [...]; explore.py selftest
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
if __name__ == "__main__" and not sys.flags.safe_path and sys.path:
    _own = __file__.replace("\\", "/").rpartition("/")[0]
    del sys.path[0]
    sys.path[:] = [p for p in sys.path if p != _own]

import argparse  # noqa: E402
import contextlib  # noqa: E402
import ctypes  # noqa: E402
import datetime as dt  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import signal  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
import tomllib  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402
import importlib.machinery  # noqa: E402
import importlib.util  # noqa: E402


class _SourceOnly(importlib.machinery.SourceFileLoader):
    """A module of this factory is loaded from its source text, compiled here, and never from cached bytecode beside it."""

    def get_code(self, fullname):
        return compile(self.get_data(self.path), self.path, "exec", dont_inherit=True)


def _source_spec(name, path):
    return importlib.util.spec_from_file_location(name, path, loader=_SourceOnly(name, str(path)))


HERE = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    """Another tool of this package, loaded by its path: nothing is copied, and nothing beside this file
    can stand in for it by name."""
    spec = _source_spec(name, path)
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
HOW = {  # the ways to hold data out (docs/HOW-IT-WORKS.md lists them), and what each has to name
    "a later period": "window",
    "a period of contrasting conditions": "window",
    "sites never opened": "sites",
    "a new release": "releases",
    "a different instrument or record": "releases",
    "forecasts scored later": "window",
    "a random set aside": "sites",   # drawn by tools/fresh_data.py, never chosen: `start` needs the proposal (`--fresh-data`)
}
OPEN_END = "9999-12-31"
TOOLS = ("sf.py", "explore.py", "knowledge.py", "system_trial.py")  # a look does not run these
TIME_KEYS = ("time", "t", "date", "datetime", "timestamp")
DATE = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
# The second line of the fence reads dates out of text. It is not the defence (a look is given only the exploration's
# own files and the working data declared at its start); it catches set-aside data that got into those by mistake.
# The forms it reads: year, month, day with a hyphen, a slash or a point between them, with or without leading zeros;
# the same eight digits run together; day or month first with the year last; a month by its English name; any
# look-alike of a hyphen; and, under a time key of a JSON file, a number that is seconds or milliseconds since 1970.
# The forms it does not read: a day of the year, a week number, a month in another language, another calendar, a
# number that is a time outside a time key, and anything that is not text.
YMD = re.compile(r"(?<![0-9A-Za-z])(\d{4})\s?[-/.]\s?(\d{1,2})\s?[-/.]\s?(\d{1,2})(?!\d)")
COMPACT = re.compile(r"(?<![0-9A-Za-z])(\d{4})(\d{2})(\d{2})(?![0-9A-Za-z])")
DMY = re.compile(r"(?<![0-9A-Za-z])(\d{1,2})\s?[-/.]\s?(\d{1,2})\s?[-/.]\s?(\d{4})(?!\d)")
MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
NAMED = re.compile(r"(?<![0-9A-Za-z])(?:(\d{1,2})(?:st|nd|rd|th)?[\s.-]*(" + "|".join(MONTHS) + r")[a-z]*[\s.,-]*(\d{4})"
                   r"|(" + "|".join(MONTHS) + r")[a-z]*[\s.-]*(\d{1,2})(?:st|nd|rd|th)?[\s.,-]*(\d{4})"
                   r"|(\d{4})[\s.-]*(" + "|".join(MONTHS) + r")[a-z]*[\s.-]*(\d{1,2}))(?![0-9])", re.I)
HYPHENS = dict.fromkeys(map(ord, "\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d\u2043"), "-")
NOTE_KINDS = ("missing", "wrong", "stale", "contradiction", "method", "dead-end")
OUTCOMES = ("lead", "note", "method", "stop", "lead-noted")  # lead-noted: a person said the reviewed lead is not interesting; not a failure
SO_WHAT = ("worth-confirming", "try-instead", "not-interesting", "needs-an-expert")  # a person's answer to a reviewed lead
SO_WHAT_NEEDS = {"try-instead": "direction", "not-interesting": "reason", "needs-an-expert": "expertise"}  # what each answer says in words
COMMENT = "comment"  # the route of a so what on the platform: a person's comment on the tracking issue, recorded by the workflow
COMMENT_FOUND = "comment recorded, person not verified"  # what the job that recorded it was handed: all a clone can show
SO_WHAT_STANDINGS = (sf.PRACTICE, COMMENT_FOUND, sf.VERIFIED)
QUESTION_KEYS = ("what_the_lead_shows", "why_it_might_matter", "what_would_make_it_unremarkable")
QUESTION_OPTIONAL = ("options",)  # the ways on the lead sets out for the person, none chosen
VERDICTS = ("holes-found", "no-holes-found")
DISPOSITIONS = ("drafted", "linked", "declined")
FIGURES = (".svg", ".png", ".pdf", ".jpg", ".jpeg")  # what a look may leave in figures/ as a picture
ID_PREFIX = re.compile(r"^[A-Za-z]{2,10}[-_:]")      # the agency in front of a site number (USGS-, usgs:)
COMPARISONS = re.compile(r"^comparisons:\s*(\d+)\s*$", re.I | re.M)
DEPTHS = ("whole", "skimmed")
NOT_THE_WORK = ("review.verdict", "note.resolved", "handed.over", "reviewer.named", "so-what.asked", "so-what.recorded", "so-what.verification",
                "fit.noted")  # kinds that do not make their actor part of the exploring
# A look runs in a scratch folder of its own, which holds its script and the files its command names and nothing else.
PATTERN = set("*?[]{}")  # what a script could expand into names the tool never read
JOINS = re.compile(r"[,:;@|]")  # what joins several paths into one word, or hides one behind a sign
KEPT_FILES = ("exploration-log.jsonl", "set-aside.json", "request.md", "lead.json", "lead.md", "curation-list.json", "contribution.md", "contribution.json")
KEPT_PLACES = ("receipts", "verdicts", "notes", "leads", "hand-over", "review", "outside", "so-what")  # where a look leaves nothing
PLACES_OF_THE_LAUNCHER = ("UV_CACHE_DIR", "UV_PYTHON_INSTALL_DIR", "UV_TOOL_DIR", "UV_TOOL_BIN_DIR", "UV_PYTHON_BIN_DIR",
                          "UV_CONFIG_FILE", "UV_PYTHON", "UV_INSTALL_DIR")  # variables whose whole purpose is to name a path
SYSTEM_FOLDERS = ("/usr", "/bin", "/sbin", "/lib", "/lib32", "/lib64", "/libx32", "/etc", "/opt", "/nix", "/proc", "/sys",
                  "/dev/null", "/dev/zero", "/dev/random", "/dev/urandom", "/dev/tty", "/run/systemd/resolve")
CONFINED_BY_THE_KERNEL = "kernel"   # Landlock was applied and tried: the script could open the system's folders, its interpreter and its scratch folder, nothing else
SCRATCH_ONLY = "scratch-only"       # no kernel fence here: the script ran in a scratch folder and could still open a path it built itself
AFTER_END = ("note.resolved", "handed.over", "review.verdict", "so-what.verification", "method.promoted")
LEAD_KEYS = ("summary", "what_looks_true", "how_it_was_found", "evidence", "choices_that_would_change_it", "choices_that_would_not",
             "pitfalls", "proposed_plan")
SUMMARY_KEYS = ("looks_true", "how_strong", "cannot_settle")  # the lead in a minute, at the top of lead.md, for the person's so what
SUMMARY_WORDS = 150
LEAD_OPTIONAL = ("what_does_not_hold", "open_explanations", "figures")
# words that mislead the person the lead is for, and what to write in their place
MISLEADING = (
    (re.compile(r"\bsampling intervals?\b", re.I),
     "`sampling interval` reads as the time between samples; write `confidence interval` and say which model it comes from"),
    (re.compile(r"\bunflagged\b|\bwithout a flag\b|\bnot flagged(?=\s*(?:[,.;:)]|$))", re.I),
     "`unflagged` and `not flagged` read as fully clean; say the flag's value (for example `reach_q equal to 1`), and if no "
     "observation in the record is at the flag's clean value, say that"),
)
PLAN_STUB_KEYS = ("question", "quantity_estimated", "difference_that_matters", "rule_sketch")


class Exploration(sf.Study):
    """An exploration is a directory with a log, like a study; the log is the study tool's chain under another name."""

    def __init__(self, d):
        super().__init__(d)
        self.log = self.d / "exploration-log.jsonl"
        self.set_aside_path = self.d / "set-aside.json"

    @contextlib.contextmanager
    def held(self):
        """The exploration log, held for one writer. A look holds it for as long as its script runs, so a command
        of this tool started meanwhile (from inside the script, or beside it) is refused and does not wait."""
        self.d.mkdir(parents=True, exist_ok=True)
        with self.log.open("a+") as f:
            if sf.fcntl:
                for attempt in range(60):
                    try:
                        sf.fcntl.flock(f, sf.fcntl.LOCK_EX | sf.fcntl.LOCK_NB)
                        break
                    except OSError:
                        time.sleep(0.05)
                else:
                    raise Refused("the exploration log is held: a look is running in this exploration, and no command writes "
                                  "to the exploration until it has ended. A look does not call the tools")
            yield f

    def add(self, actor: str, kind: str, data: dict) -> dict:
        self.check_actor(actor)
        if sf.PLATFORM_ACTOR.fullmatch(actor or "") and kind not in ("so-what.recorded", "so-what.verification") and not (
                kind == "exploration.ended" and data.get("outcome") == "lead-noted"):
            raise Refused("an actor `platform:<host>` writes one thing into an exploration: a person's so what that was a comment on the "
                          "platform, recorded by the job that follows the comment (`so-what --record-comment`), and the platform's answer "
                          "about it (`verify-so-what`). Everything else is written by human:<id> or agent:<id>")
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
            raise Refused("`--subject` is key=value,key=value (for example site=HARBOUR-1,sensor=B): "
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


def windows_of(sa: dict) -> list:
    """Every window this exploration must not look into: its own, and those other explorations set aside for the same subject."""
    return [w for w in [sa.get("window")] + list(sa.get("also_set_aside") or []) if w]


def in_any(day: dt.date, sa: dict) -> bool:
    return any(in_window(day, w) for w in windows_of(sa))


def dates_in(text: str) -> list:
    """Every date a piece of text holds, in the forms listed beside YMD above. A form that could be read two ways
    (3/4/2025) is read both ways."""
    import unicodedata
    text = unicodedata.normalize("NFKC", text).translate(HYPHENS)
    out = []

    def add(y, m, d) -> None:
        try:
            out.append(dt.date(int(y), int(m), int(d)))
        except ValueError:
            pass
    for m in YMD.finditer(text):
        add(m.group(1), m.group(2), m.group(3))
    for m in COMPACT.finditer(text):
        if 1900 <= int(m.group(1)) <= 2200:
            add(m.group(1), m.group(2), m.group(3))
    for m in DMY.finditer(text):
        add(m.group(3), m.group(2), m.group(1))
        add(m.group(3), m.group(1), m.group(2))
    for m in NAMED.finditer(text):
        g = m.groups()
        if g[0]:
            add(g[2], MONTHS.index(g[1].lower()) + 1, g[0])
        elif g[3]:
            add(g[5], MONTHS.index(g[3].lower()) + 1, g[4])
        else:
            add(g[6], MONTHS.index(g[7].lower()) + 1, g[8])
    return out


def date_of_a_number(n) -> dt.date | None:
    """A number under a time key that is seconds or milliseconds since 1970, or eight digits of a date, as a date."""
    try:
        if isinstance(n, bool) or not isinstance(n, (int, float)) or n != n:
            return None
        if isinstance(n, int) and 19000101 <= n <= 22001231:
            return dt.date(n // 10000, n // 100 % 100, n % 100)
        seconds = n / 1000 if n >= 1e11 else n
        if 3e8 <= seconds <= 8e9:
            return dt.datetime.fromtimestamp(seconds, dt.timezone.utc).date()
    except (ValueError, OverflowError, OSError):
        return None
    return None


# A month written as a year and a month (2026-08, 2026/08) is how a monthly record dates its rows, and no form above
# reads it. It is read only against the cut-off of a release, never against a window.
YEAR_MONTH = re.compile(r"(?<![0-9A-Za-z])(\d{4})[-/](\d{1,2})(?![0-9]|[-/.]\d)")


def past_cut_off(text: str, cut: str) -> list:
    """The dates and months a text holds that fall after a release's cut-off, in the forms `dates_in` reads and as a year
    and a month: a month is past the cut-off when its first day is."""
    import unicodedata
    out = {d.isoformat() for d in dates_in(text) if d.isoformat() > cut}
    for m in YEAR_MONTH.finditer(unicodedata.normalize("NFKC", text).translate(HYPHENS)):
        y, mo = int(m.group(1)), int(m.group(2))
        if 1000 <= y <= 2999 and 1 <= mo <= 12 and dt.date(y, mo, 1).isoformat() > cut:
            out.add(f"{y:04d}-{mo:02d}")
    return sorted(out)


def past_cut_off_in_json(obj, cut: str, keys: set) -> list:
    """The same, read the way the fence reads a JSON data file: a time under a declared time key anywhere, or under any key
    inside a list of rows, is a time of the data; a single date at the top of the file (when it was retrieved) is not."""
    out = set()

    def walk(o, key=None, in_rows=False):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, (dict, list)) and len(o) > 1:  # rows kept under their times: the keys are the times
                    out.update(past_cut_off(str(k).strip()[:64], cut))
                walk(v, k, in_rows)
        elif isinstance(o, list):
            for v in o:
                walk(v, key, True)
        elif isinstance(o, (int, float)) and not isinstance(o, bool) and key is not None and str(key).casefold() in keys:
            d = date_of_a_number(o)
            if d and d.isoformat() > cut:
                out.add(d.isoformat())
        elif isinstance(o, str) and key is not None and (str(key).casefold() in keys or in_rows):
            out.update(past_cut_off(o.strip()[:64], cut))
    walk(obj)
    return sorted(out)


def past_cut_off_in_file(f: Path, cut: str, keys: set) -> list:
    try:
        text = f.read_text(errors="replace")
    except OSError:
        return []
    if f.suffix.lower() == ".json":
        try:
            return past_cut_off_in_json(json.loads(text), cut, keys)
        except ValueError:
            pass
    return past_cut_off(text, cut)


def bound_files(places: list) -> list:
    """Every file in the declared places of working data, as it stands: (the file, its sha256), files of folders included."""
    out = []
    for q in places:
        q = Path(q)
        if q.is_file():
            out.append((q.resolve(), sf.sha_file(q)))
        elif q.is_dir():
            for base, dirs, files in os.walk(q):
                dirs.sort()
                out += [((Path(base) / n).resolve(), sf.sha_file(Path(base) / n)) for n in sorted(files) if (Path(base) / n).is_file()]
    return out


def cut_off_problems(x: "Exploration", sa: dict, files: dict) -> list:
    """Why a look may not be given these files under a release set aside: the release binds the data as it stood at the
    start. A working file whose checksum changed, or that was not there at the start, may hold the release; so may any
    file that holds a date or a month past the cut-off. Each is refused before anything runs."""
    cut = sa.get("cut_off")
    if not cut:
        return []
    bound = {str(Path(os.path.normpath(x.d / b["path"])).resolve()): b["sha256"] for b in sa.get("bound") or []}
    places = working_places(x)
    out = []
    for tok, f in files.items():
        real = f.resolve()
        if any(real == q or real.is_relative_to(q) for q in places) and not real.is_relative_to(x.d):
            if str(real) not in bound:
                out.append(f"`{tok}` was not in the working data when the exploration started, and a release set aside after "
                           f"{cut} may be in it")
            elif sf.sha_file(real) != bound[str(real)]:
                out.append(f"`{tok}` has changed since the exploration started (its sha256 is not the one bound at the start): the "
                           f"release set aside after {cut} may have arrived in it")
        later = past_cut_off_in_file(real, cut, {k.casefold() for k in sa.get("time_keys") or TIME_KEYS})
        if later:
            out.append(f"`{tok}` holds a date past the cut-off of the release set aside ({cut}): {', '.join(later[:3])}"
                       + (f", and {len(later) - 3} more" if len(later) > 3 else ""))
    return out


def tokens_of(sa: dict) -> list:
    return [str(x) for x in (sa.get("sites") or []) + (sa.get("releases") or []) if str(x).strip()]


def bare_forms(site: str) -> list:
    """The other ways people write a site: the number without the agency in front, and without its leading zeros."""
    m = ID_PREFIX.match(site)
    bare = site[m.end():] if m else ""
    if len(bare) < 4 or not any(c.isdigit() for c in bare):
        return []
    out = [bare.casefold()]
    if bare.isdigit() and len(bare.lstrip("0")) >= 4 and bare.lstrip("0") != bare:
        out.append(bare.lstrip("0"))
    return out


def names_token(low: str, tok: str, sa: dict) -> bool:
    """Does a piece of text (already in lower case) name a set-aside site or release, in any form people write it?"""
    if tok.casefold() in low:
        return True
    if tok in [str(s) for s in sa.get("sites") or []]:
        return any(re.search(r"(?<![0-9a-z])" + re.escape(b) + r"(?![0-9a-z])", low) for b in bare_forms(tok))
    return False


def text_problems(text: str, sa: dict, what: str) -> list:
    """Why a piece of text (a word of a command, a script, a text file) crosses the fence."""
    p, low = [], text.casefold()
    for tok in tokens_of(sa):
        if names_token(low, tok, sa):
            p.append(f"{what} names `{tok}`, which was set aside")
    for path in sa.get("paths") or []:
        if str(path).casefold() in low or Path(path).name.casefold() in low:
            p.append(f"{what} names the set-aside path `{path}`")
    inside = sorted({d.isoformat() for d in dates_in(text) if in_any(d, sa)})
    if inside:
        p.append(f"{what} names a date inside the set-aside window ({', '.join(inside[:3])}"
                 + (f", and {len(inside) - 3} more" if len(inside) > 3 else "") + ")")
    return p


def json_problems(obj, sa: dict, what: str) -> list:
    """Why a JSON data file crosses the fence: its declared window, the values under the time keys, or a
    set-aside site or release among its values. Other dates in it (when it was retrieved) are not data."""
    keys = {k.casefold() for k in sa.get("time_keys") or TIME_KEYS}
    toks = {t.casefold(): t for t in tokens_of(sa)}
    windows, hits, named = windows_of(sa), [], set()

    def walk(o, key=None, in_rows=False):
        if isinstance(o, dict):
            if windows and set(o) >= {"start", "end"} and sf.window_of({"start": o["start"], "end": o["end"]}):
                if key is None or str(key).casefold() == "window":
                    if any(sf.windows_overlap({"start": o["start"], "end": o["end"]}, core(w)) for w in windows):
                        hits.append(f"its window {o['start']} to {o['end']}")
            for k, v in o.items():
                if windows and isinstance(v, (dict, list)) and len(o) > 1:  # rows kept under their times: the keys are the times
                    for d in dates_in(str(k).strip()[:64]):
                        if in_any(d, sa):
                            hits.append(d.isoformat())
                walk(v, k, in_rows)
        elif isinstance(o, list):
            for v in o:
                walk(v, key, True)
        elif isinstance(o, bool):
            pass
        elif isinstance(o, (int, float)):  # a site kept as a number has lost its agency and its leading zeros
            for t in toks.values():
                if isinstance(o, int) and str(o) in bare_forms(t) and t in [str(s) for s in sa.get("sites") or []]:
                    named.add(t)
            if windows and key is not None and str(key).casefold() in keys:  # a time kept as a number, under a time key
                d = date_of_a_number(o)
                if d and in_any(d, sa):
                    hits.append(d.isoformat())
        elif isinstance(o, str):
            if o.casefold() in toks:
                named.add(toks[o.casefold()])
            elif len(o) <= 200:
                for t in toks.values():
                    if t in [str(s) for s in sa.get("sites") or []] and names_token(o.casefold(), t, sa):
                        named.add(t)
            # a date under a declared time key anywhere, or under any key inside a list of rows, is a time of the data;
            # a single date at the top of the file (when it was retrieved) is not
            if windows and key is not None and (str(key).casefold() in keys or in_rows):
                for d in dates_in(o.strip()[:64]):
                    if in_any(d, sa):
                        hits.append(d.isoformat())
    walk(obj)
    p = [f"{what} holds `{t}`, which was set aside" for t in sorted(named)]
    if hits:
        p.append(f"{what} holds data inside the set-aside window ({len(hits)} value(s), the first {hits[0]})")
    return p


def file_problems(f: Path, sa: dict, shown: str, figure: bool = False) -> list:
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
        if figure and f.suffix.lower() in FIGURES:
            return []  # a picture a look drew: the fence cannot read it, and the receipt keeps it by checksum
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


def fence_counts(ev: list) -> dict:
    """How many looks ran with the kernel fence applied and tried, and how many in a scratch folder only."""
    runs = [(e["data"].get("ran_in") or {}).get("confined") for e in ev if e["kind"] == "look.run"]
    return {"with_the_kernel_fence": runs.count(CONFINED_BY_THE_KERNEL), "in_a_scratch_folder_only": len(runs) - runs.count(CONFINED_BY_THE_KERNEL)}


def lead_on_file(ev: list):
    """The event that says what lead.json and lead.md are now: the latest lead, or the latest correction of its wording."""
    return next((e for e in reversed(ev) if e["kind"] in ("lead.recorded", "lead.corrected")), None)


def reviewed(ev: list) -> bool:
    """Has a review agent looked at the latest lead?"""
    lead = last(ev, "lead.recorded")
    return bool(lead) and any(e["kind"] == "review.verdict" and e["seq"] > lead["seq"] for e in ev)


def review_stands(ev: list) -> bool:
    """Has a review agent looked at the lead as it stands now? A new version and a correction of wording both
    come after the review that went before them: the review covers the words the reviewer saw and no others."""
    now = lead_on_file(ev)
    return bool(now) and any(e["kind"] == "review.verdict" and e["seq"] > now["seq"] for e in ev)


def reviewers(ev: list, before: int) -> dict:
    """Who was named as a reviewer of this exploration before a given point of the log, and by whom."""
    return {e["data"]["reviewer"].casefold(): e["actor"] for e in ev if e["kind"] == "reviewer.named" and e["seq"] < before}


def listed_not_read(ev: list) -> list:
    """Pages `known` listed that no `read` has recorded, by checksum."""
    read = {e["data"]["sha256"] for e in ev if e["kind"] == "knowledge.read"}
    out = []
    for e in ev:
        if e["kind"] == "knowledge.listed":
            for c in e["data"]["concepts"]:
                if c["sha256"] not in read and c["path"] not in out:
                    out.append(c["path"])
    return out


def order_of(ev: list) -> dict:
    """The order in which looks, choices, leads and reviews were written into the log. The log cannot say when a choice
    was made, only when it was written down; this sets each choice beside the looks that had already run."""
    steps, looks, per_choice = [], 0, {}
    for e in ev:
        k, d = e["kind"], e["data"]
        if k == "look.run":
            looks += 1
            steps.append(("look", d["id"]))
        elif k == "choice.recorded":
            prev = next((s[1] for s in reversed(steps) if s[0] == "look"), None)
            per_choice[d["id"]] = {"after_looks": looks, "after": prev, "at": e["at"]}
            steps.append(("choice", d["id"]))
        elif k == "lead.recorded":
            steps.append(("lead", f"lead version {d['version']}"))
        elif k == "review.verdict":
            steps.append(("review", f"REVIEW-{d['n']:03d}"))
    runs = []
    for kind, name in steps:
        if runs and runs[-1][0] == kind and kind in ("look", "choice"):
            runs[-1][2] = name
            runs[-1][3] += 1
        else:
            runs.append([kind, name, name, 1])
    words = [first if n == 1 else f"{first} to {end_} ({n} {kind}s)" if kind == "look" else f"{first} to {end_}"
             for kind, first, end_, n in runs]
    late = [c for c, v in per_choice.items() if v["after_looks"] > 0]
    return {"sequence": words, "choices": per_choice, "choices_recorded_after_looks": len(late), "choices_in_all": len(per_choice)}


def breached(ev: list) -> list:
    return [e for e in ev if e["kind"] == "fence.breached"]


def count(ev: list, kind: str) -> int:
    return sum(1 for e in ev if e["kind"] == kind)


def open_notes(ev: list) -> list:
    done = {e["data"]["id"] for e in ev if e["kind"] == "note.resolved"}
    return [e for e in ev if e["kind"] == "note.raised" and e["data"]["id"] not in done]


# ---- a look runs in a folder of its own ---------------------------------------
def inside(folder: Path, f: Path) -> bool:
    """Is a path, read as it is written and not through its links, inside a folder?"""
    return Path(os.path.normpath(f)).is_relative_to(Path(os.path.normpath(folder)))


def working_places(x: Exploration) -> list:
    """The places outside the exploration that it declared, at its start, as working data: files and folders."""
    places = (x.started()["data"]["set_aside"].get("working") or {}).get("places") or []
    return [Path(os.path.normpath(x.d / p)).resolve() for p in places]


def place_problem(x: Exploration, shown: str, f: Path) -> str | None:
    """Why a look may not be given a file: it is neither one of the exploration's own files nor in a place the
    exploration declared as working data when it started. This, and not the reading of what a file holds, is what
    keeps set-aside data out of a look: data nobody declared as working data is not there to be named."""
    real = f.resolve()
    if real.is_relative_to(x.d) or any(real == q or real.is_relative_to(q) for q in working_places(x)):
        return None
    return (f"`{shown}` is outside the exploration and is not in a place this exploration declared as working data when it started "
            "(`start --working-data`): a look reads the exploration's own files and the declared working data, and nothing else")


def word_problems(x: Exploration, word: str) -> tuple:
    """Read one word of a look's command the way the fence reads it: (why it cannot be confined, the existing files
    it names). A word names a file as itself or after an `=`. Everything else a script could turn into a path the
    tool never read is refused: a folder, a pattern, a tilde, a variable, several paths joined into one word, and a
    path that leaves the exploration and is not an existing file."""
    problems, files = [], []
    whole = (x.d / word).exists() or (x.d / word).is_symlink() or "=" not in word
    for c in [word if whole else word.split("=", 1)[1]]:
        if not c or c == "{python}":
            continue
        f = x.d / c
        if c.startswith("~"):
            problems.append(f"the word `{word}` is a tilde path, which a script would expand itself: name the file by its path")
        elif "$" in c or re.fullmatch(r"%\w+%", c):
            problems.append(f"the word `{word}` names a variable, which a script would expand itself: name the file by its path")
        elif set(c) & PATTERN:
            problems.append(f"the word `{word}` holds a pattern ({' '.join(sorted(set(c) & PATTERN))}), which a script would expand "
                            "into files the tool never read: name each file")
        elif c.casefold().startswith("file:"):
            problems.append(f"the word `{word}` is a file address: name the file by its path")
        elif f.is_symlink() or f.exists():
            if f.is_file():
                files.append((c, f))
            elif f.is_dir():
                problems.append(f"the word `{word}` names a folder (`{c}`): a look names each file it reads, so the tool can read it first")
            else:
                problems.append(f"the word `{word}` names something that is neither a file nor a folder")
        else:
            pieces = [q for q in JOINS.split(c) if q and q != c]
            held = [q for q in pieces if (x.d / q).exists() and ("/" in q or (x.d / q).is_file())]
            if held:
                problems.append(f"the word `{word}` holds the path `{held[0]}` joined to other things: name each file as a word of "
                                "its own, or after an `=`")
            elif Path(c).is_absolute() or ".." in Path(c).parts or any(".." in Path(q).parts or Path(q).is_absolute() for q in pieces):
                problems.append(f"the word `{word}` names a place outside the exploration that is not an existing file: a look "
                                "reads the files its command names and writes inside its own folder")
    return problems, files[:1]


def environment_problems(env: dict, sa: dict) -> list:
    """Why the environment a look would be given cannot be passed on: a variable that names an existing path is a
    way to hand a script a file the tool never read."""
    p = []
    for k, v in sorted(env.items()):
        if k in PLACES_OF_THE_LAUNCHER:  # the launcher's own places: a file among them is read like a named file
            p += file_problems(Path(v), sa, f"the file the variable {k} names") if os.path.isfile(v) else []
            continue
        if (k in ("PATH", "HOME", "TMPDIR", "TERM", "USER", "LOGNAME", "LANG", "LC_ALL", "LC_CTYPE", "TZ") or k.startswith("XDG_")
                or k.upper() in sf.CERTIFICATES_AND_PROXIES):
            continue
        if os.sep in v and os.path.exists(os.path.expanduser(v)):
            p.append(f"the variable {k} names an existing path ({v}), which a script could read without the command naming it: "
                     "unset it, and name the file in the command")
        p += text_problems(v, sa, f"the variable {k}")
    return p


def place(x: Exploration, src: Path, taken: dict, prefix: str = "") -> str:
    """Where a file goes in the scratch folder: its own place when it is inside the exploration, `outside/` when not."""
    if inside(x.d, src) and Path(os.path.normpath(src)) != x.d:
        at = Path(os.path.normpath(src)).relative_to(x.d).as_posix()
    else:
        at = f"outside/{prefix}{src.name}"
    if at in taken and taken[at] != src:
        raise Refused(f"two files of this look would land at `{at}` in its scratch folder ({taken[at]} and {src}): give them different names")
    if at.split("/")[0] == "outside" and inside(x.d, src):
        raise Refused(f"`{at}`: a look keeps the folder `outside/` for files from outside the exploration; name that file another way")
    taken[at] = src
    return at


fence = sf.fence  # how a script the tools do not trust is run (tools/fence.py); the study tool runs a plan's commands the same way


def landlock() -> int:
    """The version of the kernel's Landlock this machine has, or 0."""
    return fence.landlock()


def children() -> list:
    return fence.children()


def kept_place(rel: str) -> bool:
    return rel in KEPT_FILES or rel.split("/")[0] in KEPT_PLACES


def run_in_scratch(x: Exploration, sa: dict, argv_as_run: list, launcher_words: list, placed: list, merged: bool = False) -> dict:
    """Run a look's command in a new scratch folder that holds the files it was given and nothing else, with the
    exploration log held so that no command of this tool can write to the exploration meanwhile. The script gets an
    interpreter prepared before it starts, an environment the tool builds, and the kernel fence where the machine has
    one (tools/fence.py). Returns what happened; nothing the script wrote is put into the exploration here."""
    scratch = fence.make_scratch("sf-look-")
    work = scratch / "work"
    try:
        (work / "figures").mkdir()
        for f in placed:
            dest = work / f["at"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(Path(os.path.normpath(x.d / f["from"])), dest)
        script = next((work / f["at"] for f in placed if f.get("role") == "script"), work / placed[0]["at"])
        try:
            ready = fence.prepare_interpreter(list(launcher_words), script, scratch / "private")
        except fence.Cannot as why:
            raise Refused(f"the look was not run: {why}")
        words = [ready["python"], *argv_as_run[len(launcher_words):]]
        env = fence.minimal_environment(scratch, ready["python"], mark=("SF_INSIDE_A_LOOK", x.d.name))
        never_read = [str(x.d), str(x.log), str(HERE / "explore.py")] + [str(q) for q in sa.get("paths") or []]
        before = x.listing()
        with x.held():  # the log is held for as long as the script runs: a tool called from inside it cannot add to the log
            log_before = x.log.read_bytes()
            try:
                ran = fence.run_fenced(words, work, env, scratch, [*ready["read"], str(scratch / "private")],
                                       [str(scratch / sub) for sub in ("work", "tmp", "cache", "home")], never_read=never_read,
                                       never_write=[str(x.d)], kernel=bool(landlock()), merged=merged)
            except fence.Cannot as why:
                raise Refused(f"the look was not run: {why}")
            log_changed = not x.log.is_file() or x.log.is_symlink() or x.log.read_bytes() != log_before
        if log_changed:  # put back, byte for byte, what stood before the script ran
            if x.log.is_symlink() or x.log.is_dir():
                x.log.unlink() if x.log.is_symlink() else shutil.rmtree(x.log)
            x.log.write_bytes(log_before)
        if ran["not_run"]:
            raise Refused("the look was not run: this machine has a kernel fence, and it could not be put up or did not hold ("
                          + str(ran["fence"].get("why_not")) + "). A look does not fall back to running without it")
        code, out, err, ended = ran["code"], ran["out"], ran["err"], ran["ended"]
        after = x.listing()
        meddled = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
        for k in meddled:  # a file the script put into the exploration itself is taken out again; one it changed cannot be put back
            if k not in before:
                with contextlib.suppress(OSError):
                    (x.d / k).unlink()
        given = {f["at"]: f["sha256"] for f in placed}
        new, changed, odd = {}, [], []
        for base, dirs, files in os.walk(work):
            dirs.sort()
            for name in sorted(files) + [d for d in dirs if (Path(base) / d).is_symlink()]:
                q = Path(base) / name
                rel = q.relative_to(work).as_posix()
                if q.is_symlink() or not q.is_file():
                    odd.append(rel)
                elif rel in given:
                    if sf.sha_file(q) != given[rel]:
                        changed.append(rel)
                else:
                    new[rel] = q
        return {"code": code, "out": out, "err": err, "ended": ended, "confined": ran["confined"], "fence": ran["fence"],
                "left_alive": ran["left_alive"], "interpreter": ready["how"], "settings": ready["settings"], "environment": sorted(env),
                "log_changed": log_changed, "meddled": meddled, "new": new, "changed": changed, "odd": odd, "scratch": scratch}
    except BaseException:
        shutil.rmtree(scratch, ignore_errors=True)
        raise


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
        if how == "a random set aside" and not getattr(a, "fresh_data", None):
            raise Refused("a random set aside is drawn by `tools/fresh_data.py propose --kind random`, never chosen by anybody: name its "
                          "proposal with `--fresh-data`, and set aside exactly the members it drew")
    if window and working and sf.windows_overlap(core(working), core(window)):
        raise Refused("the working window and the set-aside window overlap: data that is explored cannot also be held out")
    cut = str(getattr(a, "release_cut_off", None) or "").strip() or None
    if cut and how != "a new release":
        raise Refused("`--release-cut-off` is the last date of the data as it stands before a new release; it goes with `--how \"a new release\"`")
    if cut and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", cut):
        raise Refused("`--release-cut-off` is a date, YYYY-MM-DD")
    studies_here = Path(os.path.abspath(a.studies)) if a.studies else x.d.parent.parent / "studies"
    fresh, prop = None, None
    if getattr(a, "fresh_data", None):
        if a.nothing_set_aside:
            raise Refused("`--fresh-data` names what is set aside, and `--nothing-set-aside` says nothing is; choose one")
        fpath = Path(os.path.abspath(a.fresh_data))
        prop, wrong = fresh_data_problems(fpath, studies_here, how, window, sites, releases)
        if not wrong and prop and prop["kind"] == "next-release":
            fixed = (prop.get("rule") or {}).get("cut_off")
            if cut and fixed and cut != fixed:
                wrong.append(f"the cut-off given ({cut}) is not the one the proposal fixed ({fixed})")
            cut = cut or fixed
        if wrong:
            raise Refused("the proposal of the fresh data does not match this start: " + "; ".join(wrong) + ". Nothing was started")
        fresh = {"file": str(fpath), "sha256": sf.sha_file(fpath), "kind": prop["kind"], "kind_in_words": prop["kind_in_words"],
                 "proposed_by": (prop.get("proposed") or {}).get("by"), "proposed_at": (prop.get("proposed") or {}).get("at"),
                 "seed_sha256": (prop.get("draw") or {}).get("seed_sha256")}
    if how == "a new release" and not cut:
        raise Refused("a new release set aside binds the data as it stands: give the last date of the working data before the release "
                      "(`--release-cut-off YYYY-MM-DD`, or a proposal that fixes it). A release that arrives as new rows of the same "
                      "file carries no mark of its own, so without a cut-off nothing in the file would be set aside")
    if cut and working and working["end"] > cut:
        raise Refused(f"the working window runs to {working['end']}, past the cut-off of the release ({cut}): what is explored is the data as it stands")
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
    others = []
    for ln in record_lines(record):  # what another exploration set aside for this subject is fenced here too
        if ln.get("kind") == "set-aside" and ln.get("subject") == key and (ln.get("set_aside") or {}).get("window"):
            w = ln["set_aside"]["window"]
            if working and sf.windows_overlap(core(working), core(w)):
                raise Refused(f"{ln.get('exploration')} set aside {w['start']} to {'onward' if w.get('open_ended') else w['end']} for this subject, and "
                              "the working window given here reaches into it: what one exploration set aside, another does not explore")
            if w != window and w not in others:
                others.append(w)
        if ln.get("kind") == "set-aside" and ln.get("subject") == key and (ln.get("set_aside") or {}).get("cut_off"):
            c = ln["set_aside"]["cut_off"]
            if working and working["end"] > c:
                raise Refused(f"{ln.get('exploration')} set aside the release after {c} for this subject, and the working window given here "
                              "runs past it: what one exploration set aside, another does not explore")
    paths = [os.path.abspath(p) for p in a.set_aside_path or []]
    places = []  # where the working data is, outside the exploration: the only outside files a look may be given
    for given in getattr(a, "working_data", None) or []:
        q = Path(os.path.abspath(given)).resolve()
        if not q.exists():
            raise Refused(f"`--working-data {given}` names nothing that exists: it is the file or the folder that holds the data to explore")
        if x.d.resolve().is_relative_to(q) or studies.resolve().is_relative_to(q) or q.is_relative_to(studies.resolve()):
            raise Refused(f"`--working-data {given}` holds the exploration itself or the studies: name the folder or the file the "
                          "working data is in, and nothing wider")
        if any(Path(p).resolve() == q or Path(p).resolve().is_relative_to(q) or q.is_relative_to(Path(p).resolve()) for p in paths):
            raise Refused(f"`--working-data {given}` is, holds or lies in a set-aside path: data that is set aside is not working data")
        places.append(os.path.relpath(q, x.d.resolve()))
    present = [p for p in paths if Path(p).exists()]
    if present:
        raise Refused(f"set-aside data is already here ({present[0]}); it is set aside before it is fetched, and it is not fetched by an exploration")
    bound = []
    if cut:  # the data as it stands, bound by checksum: a look given a working file that changed afterwards is refused
        named = dict((prop or {}).get("rule", {}).get("files") or {})
        for f, sha in bound_files([Path(os.path.normpath(x.d / q)) for q in places] if places else []):
            later = past_cut_off_in_file(f, cut, {k.strip().casefold() for k in (a.time_keys or ",".join(TIME_KEYS)).split(",") if k.strip()})
            if later:
                raise Refused(f"the working data already holds dates past the cut-off of the release ({cut}) in {f.name}: "
                              f"{', '.join(later[:3])}. The cut-off is the last date of the data as it stands; nothing was started")
            if f.name in named and named[f.name] != sha:
                raise Refused(f"{f.name} is not the file the metadata describes: its sha256 is {sha[:16]}, the metadata's {str(named[f.name])[:16]}. "
                              "The release binds the data as the metadata saw it; nothing was started")
            bound.append({"path": os.path.relpath(f, x.d.resolve()), "sha256": sha})
        if named and not any(Path(b["path"]).name in named for b in bound):
            raise Refused(f"the metadata the proposal was made from names {', '.join(sorted(named))}, and none is among the working data "
                          "declared here (`--working-data`): the release binds the files the metadata describes; nothing was started")
    pages = []  # what was read before setting aside: knowledge pages only, never data
    for page in getattr(a, "boundary_from", None) or []:
        f = Path(os.path.abspath(page))
        fm = knowledge_tool().front_matter(f)[0] if f.is_file() and f.suffix.lower() == ".md" else None
        if fm is None:
            raise Refused(f"`--boundary-from {page}` is not a knowledge page (a Markdown page with front matter). Before data is set "
                          "aside only knowledge is read, never data: the boundary comes from a page, or it is the widest honest one")
        signed, people = knowledge_tool().signed_by(fm, "")
        pages.append({"path": os.path.relpath(f, x.d), "sha256": sf.sha_file(f), "signed": signed, "signed_by": people})
    gap = None  # data that is neither explored nor set aside: nothing protects it, so say so
    if window and working and working["end"] < window["start"]:
        first = dt.date.fromisoformat(working["end"]) + dt.timedelta(days=1)
        final = dt.date.fromisoformat(window["start"]) - dt.timedelta(days=1)
        if first <= final:
            gap = {"start": first.isoformat(), "end": final.isoformat()}
    sa = {"how": how, "subject": subject, "window": window, "sites": sites, "releases": releases, "paths": paths, "also_set_aside": others,
          "time_keys": [k.strip() for k in (a.time_keys or ",".join(TIME_KEYS)).split(",") if k.strip()],
          "why": a.why or a.nothing_set_aside,
          "working": {"description": a.working, "window": working, "places": places}}
    if gap:
        sa["in_neither"] = gap
    if cut:
        sa["cut_off"], sa["bound"] = cut, bound
    if fresh:
        sa["fresh_data"] = fresh
    if pages:
        sa["boundary_read_from"] = pages
    x.d.mkdir(parents=True, exist_ok=True)
    for sub in ("receipts", "notes", "verdicts", "looks", "review", "figures"):
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
                      "set_aside": {"how": how, "window": window, "sites": sites, "releases": releases, **({"cut_off": cut} if cut else {})},
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
          + (f", {'from ' + window['start'] + ' onward' if window.get('open_ended') else window['start'] + ' to ' + window['end']}" if window else "")
          + (f", sites {sites}" if sites else "") + (f", {releases}" if releases else "")
          + (f", after the cut-off {cut}, with {len(bound)} working file(s) bound by checksum" if cut else "")
          + f". Written to {rel_record}. Next: `known` and `read`, then look.")
    if gap:
        print(f"Note: {gap['start']} to {gap['end']} is neither explored nor set aside. Nothing protects it: a later study "
              "cannot hold it out as unseen unless nobody looks at it, and this tool will not stop a look there.")


def knowledge_tool():
    return _load("knowledge", HERE / "knowledge.py")


def fresh_tool():
    return sys.modules.get("fresh_data") or _load("fresh_data", HERE / "fresh_data.py")


def fresh_data_problems(path: Path, studies: Path, how: str, window, sites: list, releases: list) -> tuple:
    """(the proposal, what is wrong): the proposal of the fresh data that this start sets aside is on the record beside
    the studies, checks out (a random draw comes from its seed), and is the same as what the start sets aside."""
    tool = fresh_tool()
    try:
        prop = tool.load(path)
        found = tool.problems(path, studies)
    except tool.Refused as r:
        return None, [str(r)]
    rule, kind = prop.get("rule") or {}, prop["kind"]
    want = {"later-period": "a later period", "another-site": "sites never opened", "next-release": "a new release", "random": "a random set aside"}[kind]
    if how != want:
        found.append(f"the proposal is {prop['kind_in_words']}, which is set aside as `--how \"{want}\"`, not `{how}`")
    elif kind == "later-period" and (not window or window["start"] != rule.get("from")
                                     or (rule.get("until") and window.get("end") != rule["until"]) or (not rule.get("until") and not window.get("open_ended"))):
        found.append(f"the window set aside is not the later period the proposal names ({rule.get('from')} to {rule.get('until') or 'onward'})")
    elif kind in ("another-site", "random") and sorted(sites) != sorted(prop["members"]):
        found.append("the sites set aside are not the members the proposal names" + (": a random set aside is drawn by the tool, and "
                     "nobody adds a site to it or takes one out" if kind == "random" else ""))
    elif kind == "next-release" and rule.get("release") not in releases:
        found.append(f"the release set aside is not the one the proposal names ({rule.get('release')})")
    return prop, found


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
          "then record what it changes with `read --concept <the path as listed above, or the file>`. The first look waits for a `read`.")


def listed_file(x: Exploration, ev: list, concept: str):
    """The file behind a concept named the way `known` prints it (repository/wiki/path), or by its path below a listed wiki."""
    k = knowledge_tool()
    for e in reversed(ev):
        if e["kind"] != "knowledge.listed":
            continue
        for rel in list(e["data"].get("bundles") or []) + list(e["data"].get("drafts") or []):
            root = Path(os.path.normpath(x.d / rel))
            if not root.is_dir():
                continue
            if (root / concept).is_file():
                return root / concept
            for p, _fm, _body in k.concepts(root):
                if k.shown(root, p) == concept:
                    return p
    return None


def cmd_read(x: Exploration, a) -> None:
    x.started()
    k = knowledge_tool()
    depth = getattr(a, "depth", None) or "whole"
    if depth not in DEPTHS:
        raise Refused(f"`--depth` is one of {DEPTHS}: say whether the page was read whole or skimmed")
    f = Path(os.path.abspath(a.concept))  # the path as it was given: a link is not followed, so one page has one spelling in the log
    if not f.is_file():
        f = listed_file(x, x.events(), str(a.concept))
    if f is None or not f.is_file():
        raise Refused(f"the concept {a.concept} does not exist: give the path `known` printed for it, its path below the wiki, or the file")
    fm, _body = k.front_matter(f)
    fm = fm or {}
    signed, by = k.signed_by(fm, _body)
    sha = sf.sha_file(f)
    # A page the search did not list may be read too (one a listed page leans on, say): it is recorded, and the lead says
    # that the search did not list it, so a reader can see the list was not the whole of the reading.
    listed = any(c.get("sha256") == sha and Path(str(c.get("path"))).name == f.name
                 for e in x.events() if e["kind"] == "knowledge.listed" for c in e["data"].get("concepts") or [])
    x.add(a.by, "knowledge.read", {"path": os.path.relpath(f, x.d), "sha256": sha, "status": k.status_of(fm, _body),
                                   "signed": signed, "signed_by": by, "takes": a.takes, "depth": depth, "listed": listed})
    print(f"read: {f.name} ({'signed by ' + ', '.join(by) if signed else 'NOT SIGNED, status ' + str(k.status_of(fm, _body))}), "
          f"recorded ({WAY})" + ("" if listed else "; the search did not list it, and the lead will say so"))


def cmd_look(x: Exploration, a) -> None:
    ev = x.events()
    start = x.started()
    sa = start["data"]["set_aside"]
    if breached(ev):
        raise Refused("this exploration is spoiled: set-aside data reached it (see fence.breached in the log). Nothing more is looked at here")
    if not last(ev, "knowledge.listed"):
        raise Refused("nothing has been looked up yet: run `known` first, so the exploring starts from what is already known")
    if not last(ev, "knowledge.read") and any(e["data"]["concepts"] for e in ev if e["kind"] == "knowledge.listed"):
        raise Refused("pages were listed and none is recorded as read: read what is known and record what each page changes "
                      "with `read`, then look. Listing is not reading")
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
    if (x.d / script).resolve().parent == HERE and (x.d / script).resolve().name in TOOLS:
        raise Refused(f"`{script}` is a tool of this package, not a look: the study tool, this tool and the knowledge tool are "
                      "called by a role under its own name, never from inside a look")
    here = set_aside_present(sa)
    if here:
        raise Refused(f"set-aside data is in the workspace ({here[0]}); an exploration does not fetch it and does not run beside it")
    at_script = argv.index(script, 1)
    problems, named, taken = [], [], {}
    for word in argv:
        problems += text_problems(word, sa, f"the word `{word}`")
    for i, word in enumerate(argv[at_script + 1:], at_script + 1):
        why_not, files = word_problems(x, word)
        problems += why_not
        named += [(i, c, f) for c, f in files]
    also = [str(w) for w in getattr(a, "also_reads", None) or []]
    for w in also:
        if not (x.d / w).is_file() or set(w) & PATTERN or w.startswith("~"):
            problems.append(f"`--also-reads {w}` does not name one existing file (paths are read from the exploration directory)")
    files = {script: x.d / script, **{c: f for _i, c, f in named}, **{w: x.d / w for w in also if (x.d / w).is_file()}}
    for tok, f in files.items():
        problems += file_problems(f, sa, tok)
    for tok, f in files.items():  # the data a look is given; its own script, a Python file, may be a shared one from elsewhere
        if not (tok == script and script.endswith(".py")):
            problems += [q for q in [place_problem(x, tok, f)] if q]
    problems += cut_off_problems(x, sa, files)
    if problems:
        x.add(a.by, "look.refused", {"argv": argv, "why": a.why, "refused_because": problems})
        raise Refused("this look names what was set aside, or names it in a way the tool cannot confine, so it is not run "
                      "(the refusal is logged): " + "; ".join(problems[:4]))
    # what goes into the scratch folder, and the command as it runs there: a file from outside the exploration is
    # given to the script under `outside/`, and the word that named it is rewritten to say so
    placed, argv_as_run = [], list(argv)

    def give(word: str, f: Path, role: str, prefix: str = "") -> str:
        at = place(x, f, taken, prefix)
        placed.append({"word": word, "from": os.path.relpath(f, x.d), "at": at, "sha256": sf.sha_file(f), "bytes": f.stat().st_size, "role": role})
        return at

    argv_as_run[at_script] = give(script, x.d / script, "script")
    for n, (i, c, f) in enumerate(named, 1):
        at = give(c, f, "named", f"{n:02d}-")
        if at != Path(os.path.normpath(c)).as_posix():
            argv_as_run[i] = argv_as_run[i][:len(argv_as_run[i]) - len(c)] + at
    for w in also:
        give(w, x.d / w, "also-reads")
    n = count(ev, "look.run") + 1
    lid = f"LOOK-{n:03d}"
    out_rel, err_rel = f"receipts/{lid}.out.txt", f"receipts/{lid}.err.txt"
    ran = run_in_scratch(x, sa, argv_as_run, argv[:at_script], placed)
    try:
        code, out, err = ran["code"], ran["out"], ran["err"]
        crossing, wrote, not_kept = [], {}, []
        crossing += text_problems(out, sa, "what the look printed") + text_problems(err, sa, "what the look wrote to standard error")
        withheld = bool(crossing)  # set-aside data that came back in the output is not kept and is not shown to whoever ran the look
        if ran["log_changed"]:
            crossing.append("the exploration log was changed while the look ran, and the tool put it back as it stood: a look does not call the tools")
        if ran["left_alive"]:
            crossing.append(f"the look left {ran['left_alive']} process(es) running that could not be ended")
        if ran["fence"].get("tools_changed"):
            crossing.append("the look ran without a kernel fence, and what the tools run from changed while it ran ("
                            + ", ".join(ran["fence"]["tools_changed"][:5]) + "): look at those files before any tool of this "
                            "package is run again")
        if ran["meddled"]:
            crossing.append("the look changed files in the exploration itself, outside its scratch folder ("
                            + ", ".join(ran["meddled"][:5]) + "): a look writes only into its own folder. A file it added was "
                            "taken out again; a file it changed or removed could not be put back")
        for rel, q in sorted(ran["new"].items()):
            if kept_place(rel):
                not_kept.append({"file": rel, "why": "a look leaves nothing in a place the tool or another role keeps"})
                continue
            crossed = file_problems(q, sa, rel, figure=rel.startswith("figures/"))
            if crossed:
                crossing += crossed
                not_kept.append({"file": rel, "why": "it crosses the fence"})
                continue
            wrote[rel] = sf.sha_file(q)
            (x.d / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(q, x.d / rel)
        not_kept += [{"file": rel, "why": "a link, or not a plain file"} for rel in ran["odd"]]
        not_kept += [{"file": rel, "why": "a file the look was given, changed in the scratch folder; the original is untouched"} for rel in ran["changed"]]
    finally:
        shutil.rmtree(ran["scratch"], ignore_errors=True)
    if withheld:
        out = err = "[withheld by the tool: what the look printed crosses the fence, so it is neither kept nor shown]\n"
    (x.d / out_rel).write_text(f"[{WAY}: output of {lid}]\n" + out)
    if err.strip():
        (x.d / err_rel).write_text(f"[{WAY}: standard error of {lid}; not part of the output a recheck compares]\n" + err)
    figures = [{"file": rel, "sha256": sha_, "bytes": (x.d / rel).stat().st_size} for rel, sha_ in sorted(wrote.items())
               if rel.startswith("figures/") and Path(rel).suffix.lower() in FIGURES]
    crossing += [f"set-aside data appeared at {p}" for p in set_aside_present(sa)]
    inputs = [{"word": f["word"], "sha256": f["sha256"], "bytes": f["bytes"]} for f in placed if f["role"] != "script"]
    declared = sum(int(n) for n in COMPARISONS.findall(out))
    how = {"folder": "a scratch folder that held the files below and nothing else", "confined": ran["confined"], "placed": placed,
           "argv_as_run": argv_as_run, "not_kept": not_kept, "processes_ended": ran["ended"],
           "fence": ran["fence"], "interpreter": ran["interpreter"], "environment": ran["environment"],
           "launcher_settings": ran["settings"]}
    receipt = {"id": lid, "why": a.why, "argv": argv, "launcher": launcher, "script": {"word": script, "sha256": placed[0]["sha256"]},
               "inputs": inputs, "exit_code": code, "output": {"file": out_rel, "sha256": sf.sha_file(x.d / out_rel)},
               "standard_error": {"file": err_rel, "sha256": sf.sha_file(x.d / err_rel)} if err.strip() else None,
               "figures": figures, "comparisons_declared": declared, "wrote": wrote, "ran_in": how, "at": sf.now(), "by": a.by}
    sha = write_json(x.d / f"receipts/{lid}.json", receipt)
    x.add(a.by, "look.run", {"id": lid, "why": a.why, "argv": argv, "script_sha": receipt["script"]["sha256"], "inputs": inputs,
                             "exit_code": code, "output_sha": receipt["output"]["sha256"], "receipt_sha": sha,
                             "streams": "separate", "err_sha": receipt["standard_error"]["sha256"] if err.strip() else None,
                             "figures": figures, "comparisons_declared": declared,
                             "wrote": wrote, "ran_in": how, "out_head": out[:1500]})
    if crossing:
        x.add(a.by, "fence.breached", {"look": lid, "what": crossing})
    print(out, end="" if out.endswith("\n") or not out else "\n")
    if err.strip():
        print(err, end="" if err.endswith("\n") else "\n", file=sys.stderr)
    print(f"[{lid} logged ({WAY}), exit {code}, {len(inputs)} file(s) named, output in {out_rel}"
          + (f", {len(figures)} figure(s): {', '.join(f_['file'] for f_ in figures)}" if figures else "")
          + ("; the script could open only the system's folders and its own scratch folder" if ran["confined"] == CONFINED_BY_THE_KERNEL
             else "; NOT confined by the kernel on this machine: the script ran in a scratch folder, and a path it built itself was not stopped ("
                  + str(ran["fence"].get("why_not")) + ")")
          + (f"; {len(not_kept)} file(s) it wrote were not kept" if not_kept else "")
          + (f"; {ran['ended']} process(es) it left running were ended" if ran["ended"] else "") + "]")
    if crossing:
        raise Refused(f"{lid} crossed the fence ({crossing[0]}). The exploration is spoiled: no lead and "
                      "no hand-over can come from it, and the data it held out is no longer held out for this subject")


def without_warnings(text: str) -> str:
    return "\n".join(ln for ln in text.splitlines() if not ln.startswith("warning: "))


def run_variant(x: Exploration, sa: dict, d: dict, receipt: dict, variant: str) -> None:
    """A reviewer's variant of a logged look: its own script in the look's place, in the same scratch folder with the same
    files by checksum and the same fence, logged nowhere. The reviewer lists each one in the review with what it showed."""
    how_run = d.get("ran_in")
    if not how_run:
        raise Refused(f"{d['id']} was logged before looks ran in a scratch folder: a variant runs only in a look's scratch folder")
    f = Path(os.path.normpath(x.d / variant))
    if not (f.is_file() and not f.is_symlink() and f.suffix == ".py" and f.parent == x.d / "review"):
        raise Refused("`--variant` is a Python script the reviewer wrote in the exploration's review/ folder")
    problems = text_problems(f.read_text(errors="replace"), sa, f"the variant `{variant}`")
    problems += cut_off_problems(x, sa, {variant: f})
    for g in how_run["placed"]:
        if g["role"] != "script" and sf.sha_file(Path(os.path.normpath(x.d / g["from"]))) != g["sha256"]:
            problems.append(f"`{g['from']}` is not the file {d['id']} was given")
    if problems:
        raise Refused("the variant is not run: " + "; ".join(problems[:4]))
    placed = [dict(g, **{"from": os.path.relpath(f, x.d), "sha256": sf.sha_file(f)}) if g["role"] == "script" else g for g in how_run["placed"]]
    at_script = d["argv"].index(receipt["script"]["word"], 1)
    ran = run_in_scratch(x, sa, how_run["argv_as_run"], d["argv"][:at_script], placed)
    shutil.rmtree(ran["scratch"], ignore_errors=True)
    if ran["log_changed"] or ran["meddled"]:
        raise Refused("the variant changed the exploration while it ran: a script writes only into its own scratch folder")
    crossing = text_problems(ran["out"], sa, "what the variant printed") + text_problems(ran["err"], sa, "what the variant wrote to standard error")
    if crossing:
        raise Refused("what the variant printed crosses the fence, so it is not shown: " + crossing[0])
    print(ran["out"], end="" if ran["out"].endswith("\n") else "\n")
    print(f"[a variant of {d['id']} ({WAY}), run by the reviewer in the look's scratch folder with the same {len(placed) - 1} file(s) by "
          f"checksum: exit {ran['code']}. It is not logged and changes nothing in the exploration: list it in your review, with what it showed]")


def cmd_recheck(x: Exploration, a) -> None:
    """Run a logged look again and compare what comes out, without adding a look: for the review agent. With
    `--variant`, run the reviewer's own script in the look's place instead, unlogged."""
    ev = x.events()
    sa = x.started()["data"]["set_aside"]
    e = next((e for e in ev if e["kind"] == "look.run" and e["data"]["id"] == a.look), None)
    if e is None:
        raise Refused(f"there is no {a.look} in the log")
    d = e["data"]
    receipt = json.loads((x.d / f"receipts/{d['id']}.json").read_text())
    if getattr(a, "variant", None):
        if set_aside_present(sa):
            raise Refused("set-aside data is in the workspace; nothing is run")
        return run_variant(x, sa, d, receipt, a.variant)
    script = x.d / receipt["script"]["word"]
    if sf.sha_file(script) != d["script_sha"]:
        raise Refused(f"the script of {d['id']} is not the script that was logged; nothing is run")
    for i in d["inputs"]:
        if sf.sha_file(x.d / i["word"]) != i["sha256"]:
            raise Refused(f"`{i['word']}` is not the file {d['id']} read; nothing is run")
    if set_aside_present(sa):
        raise Refused("set-aside data is in the workspace; nothing is run")
    late = cut_off_problems(x, sa, {f["from"]: Path(os.path.normpath(x.d / f["from"])) for f in (d.get("ran_in") or {}).get("placed") or []}
                            or {i["word"]: x.d / i["word"] for i in d["inputs"]})
    if late:
        raise Refused("nothing is run: " + "; ".join(late[:3]))
    head = f"[{WAY}: output of {d['id']}]\n"
    how_run = d.get("ran_in")
    if how_run:  # the look ran in a scratch folder: the same folder is built again from the same files, by checksum
        for f in how_run["placed"]:
            if sf.sha_file(Path(os.path.normpath(x.d / f["from"]))) != f["sha256"]:
                raise Refused(f"`{f['from']}` is not the file {d['id']} was given; nothing is run")
        at_script = d["argv"].index(receipt["script"]["word"], 1)
        ran = run_in_scratch(x, sa, how_run["argv_as_run"], d["argv"][:at_script], how_run["placed"])
        shutil.rmtree(ran["scratch"], ignore_errors=True)
        if ran["log_changed"] or ran["meddled"]:
            raise Refused(f"the script of {d['id']} changed the exploration while it was run again ("
                          + ", ".join((["the log, which the tool put back"] if ran["log_changed"] else []) + ran["meddled"][:5])
                          + "): a look writes only into its own scratch folder")
        code, out = ran["code"], ran["out"]
        pinned = (f"it ran in a scratch folder holding the {len(how_run['placed'])} file(s) the look was given, each the same by checksum, "
                  + ("and the kernel kept it from opening anything else but the system's folders"
                     if ran["confined"] == CONFINED_BY_THE_KERNEL else
                     "but this machine has no kernel fence, so a file the script opens by a path it builds itself is not pinned"))
        same = sf.sha_text(head + out) == d["output_sha"] and code == d["exit_code"]
        how = "the output is identical to what was logged"
    else:  # a look logged before looks ran in a scratch folder: run the old way, in a copy of the exploration
        old = fence.make_scratch("sf-recheck-")
        copy = x.d.parent / f".recheck-{os.getpid()}"  # a copy at the same depth, so the look's relative paths still resolve
        separate = d.get("streams") == "separate"  # a look logged before the tool kept standard error apart has both in its output
        try:
            shutil.copytree(x.d, copy, symlinks=True)
            at_script = d["argv"].index(receipt["script"]["word"], 1)
            ready = fence.prepare_interpreter(d["argv"][:at_script], copy / receipt["script"]["word"], old / "private")
            again = fence.run_fenced([ready["python"], *d["argv"][at_script:]], copy, fence.minimal_environment(old, ready["python"], mark=("SF_INSIDE_A_LOOK", x.d.name)),
                                     old, ready["read"], [str(copy)], kernel=False, merged=not separate)
            code, out = again["code"], again["out"]
        except fence.Cannot as why:
            raise Refused(f"the look was not run again: {why}")
        finally:
            shutil.rmtree(old, ignore_errors=True)
            shutil.rmtree(copy, ignore_errors=True)
        pinned = ("this look was logged before looks ran in a scratch folder: only its script and the files its command names are "
                  "the same by checksum, and a file the script opens without the command naming it is not pinned")
        same = sf.sha_text(head + out) == d["output_sha"] and code == d["exit_code"]
        how = "the output is identical to what was logged"
        if not same and not separate and code == d["exit_code"]:
            # an old receipt holds the launcher's warnings in its output; they come and go with the machine, the numbers do not
            logged = (x.d / f"receipts/{d['id']}.out.txt").read_text(errors="replace")
            if sf.sha_text(logged) == d["output_sha"] and without_warnings(logged) == without_warnings(head + out):
                same, how = True, ("the output is identical to what was logged once the launcher's `warning:` lines are set aside "
                                   "(this look was logged before the tool kept standard error apart)")
    print(out, end="" if out.endswith("\n") else "\n")
    print(f"[recheck of {d['id']} ({WAY}): exit {code}; " + (how if same else "THE OUTPUT DIFFERS from what was logged") + f"; {pinned}]")
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
    looks = [e["data"]["id"] for e in ev if e["kind"] == "look.run"]
    x.add(a.by, "choice.recorded", {"id": cid, "choice": a.choice, "alternatives": alts, "rests_on": a.rests_on, "look": a.look,
                                    "after_looks": len(looks), "after": looks[-1] if looks else None})
    print(f"{cid} recorded ({WAY}): {a.choice}\n"
          + (f"[written down after {looks[-1]}: {len(looks)} look(s) had run, and the lead will say so]" if looks
             else "[written down before any look, and the lead will say so]"))


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
    p += [f"`{k}` is not a key of a lead" for k in lead if k not in LEAD_KEYS + LEAD_OPTIONAL]
    if p:
        return p
    for k in ("what_does_not_hold", "open_explanations"):
        if k in lead and (not isinstance(lead[k], str) or not lead[k].strip()):
            p.append(f"`{k}`, when given, is words: leave the key out when there is nothing to say")
    for rx, instead in MISLEADING:
        hit = rx.search(json.dumps(lead, ensure_ascii=False))
        if hit:
            p.append(f"the lead says `{hit.group(0)}`: {instead}")
    for k in ("what_looks_true", "how_it_was_found"):
        if not isinstance(lead[k], str) or len(lead[k].split()) < 5:
            p.append(f"`{k}` is a sentence or more, in words")
    summ = lead["summary"]
    if not isinstance(summ, dict) or set(map(str, summ)) != set(SUMMARY_KEYS):
        p.append("`summary` is the lead in a minute, with exactly these keys: " + ", ".join(SUMMARY_KEYS)
                 + " (what looks true, how strong the evidence is, what it cannot settle)")
    else:
        short = [k for k in SUMMARY_KEYS if not isinstance(summ[k], str) or len(summ[k].split()) < 5]
        if short:
            p.append("each part of `summary` is a sentence, in words: " + ", ".join(short))
        elif sum(len(summ[k].split()) for k in SUMMARY_KEYS) > SUMMARY_WORDS:
            p.append(f"`summary` is under {SUMMARY_WORDS} words in all, so that a person can read it in a minute; it has "
                     f"{sum(len(summ[k].split()) for k in SUMMARY_KEYS)}")
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
    drawn = {f["file"]: e["data"]["id"] for e in ev if e["kind"] == "look.run" for f in e["data"].get("figures") or []}
    for fig in lead.get("figures") or [] if isinstance(lead.get("figures", []), list) else [None]:
        if not isinstance(fig, dict) or not fig.get("file") or not str(fig.get("shows") or "").strip():
            p.append("each entry of `figures` is {file: figures/name.svg, shows: what the picture shows, in words}")
        elif fig["file"] not in drawn:
            p.append(f"`figures` names {fig['file']}, which no logged look drew (a figure is a file a look wrote into figures/)")
        elif drawn[fig["file"]] not in cited:
            p.append(f"`figures` names {fig['file']}, drawn by {drawn[fig['file']]}, which `evidence` does not cite")
    stub = lead["proposed_plan"]
    if not isinstance(stub, dict):
        p.append("`proposed_plan` is a mapping")
    else:
        p += [f"`proposed_plan.{k}` is missing" for k in PLAN_STUB_KEYS if not str(stub.get(k) or "").strip()]
        if str(stub.get("question") or "").strip() and not str(stub["question"]).strip().endswith("?"):
            p.append("`proposed_plan.question` is one sentence ending in a question mark")
    return p


# A number as a lead may quote it, in the forms this tool reads (the description at the top lists them): 7.7777, .8888, 8,8888, 8.888e0, 88888e-4, and
# with a gap before the point (8 .8888). What stands before or after it (a letter, a unit, a sign) does not hide it.
QUOTED = re.compile(r"(?<![\d.,])(?:\d+\s+\.\d+|(?:\d+,\d+|\d*\.\d+)(?:[eE][+-]?\d+)?|(?<![A-Za-z])\d+[eE][+-]?\d+)")
PERCENT = re.compile(r"(?<![\d.,])(\d+)\s*(?:%|per ?cent\b|per-cent\b)", re.I)  # a whole number given as a share
PRINTED = re.compile(r"(?<![\d.])(?:\d+,\d+|\d*\.\d+|\d+)(?:[eE][+-]?\d+)?(?!\d)")  # a number as a look printed it, whole
# a page under one of these is somebody's working file, whatever wiki it was put in
NOT_KNOWLEDGE = ("explorations", "looks", "record", "knowledge-queue", "knowledge-queue-reviews", "studies", "finding-draft", "review",
                 "hand-over", "methods", "receipts", "verdicts", "notes")
DECIMAL_MARKS = dict.fromkeys(map(ord, "\u00b7\u066b\u2027\u2219\u22c5\u30fb\uff0e\u2024\u02d9\u0387"), ".")  # what else stands for a decimal point
SPLIT = re.compile(r"(\d)\.\s+(\d{3,})")              # 7. 7777
RATIO = re.compile(r"(?<![\d.,/])(\d+)\s*/\s*(10{2,})(?![\d/])")  # 77777/10000: a decimal written as a division by a power of ten


def number_forms(text: str) -> str:
    """A lead's words with the other ways of writing a number with a fraction turned into the plain one, so that the
    check below reads them: a look-alike of the decimal point, a gap after the point, a division by a power of ten.
    The check reads these forms and the ones QUOTED names; a number written out in words it does not read."""
    import unicodedata
    text = unicodedata.normalize("NFKC", text).translate(DECIMAL_MARKS)
    text = SPLIT.sub(r"\1.\2", text)

    def as_decimal(m) -> str:
        digits, zeros = m.group(1), len(m.group(2)) - 1
        digits = digits.rjust(zeros + 1, "0")
        return f"{digits[:-zeros]}.{digits[-zeros:]}"
    return RATIO.sub(as_decimal, text)


def as_written(number: str) -> str:
    """One spelling for comparing: no gap, a point for a decimal comma, a small e."""
    return re.sub(r"\s+", "", number).replace(",", ".").lower()


# Numbers a method names that are not results: the normal quantiles and the usual levels, and those levels as shares. They
# pass without a receipt in the lead's method text (how it was found, the choices, the pitfalls, a quoted plan sentence),
# never where it says what looks true. A count written with a thousands comma there (5,000 draws) is a whole number.
CONSTANTS = ("1.645", "1.96", "2.576", "0.05", "0.01", "0.95", "0.99")
CONSTANT_SHARES = ("90", "95", "99")
COUNT = re.compile(r"(?<![\d.,])\d{1,3}(?:,\d{3})+(?![\d.,])(?=\s+[A-Za-z])")
LOOK_NAMED = re.compile(r"\bLOOK-\d{3,}\b")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def own_words(lead: dict) -> list:
    """The lead's own words: everything but the proposed plan, whose numbers are proposals and not things that were seen
    (a plan sentence that names a look quotes it, and is read by `plan_quotes`)."""
    return result_words(lead) + method_words(lead)


def result_words(lead: dict) -> list:
    """Where the lead says what it saw: every number there is a result."""
    texts = [str(lead.get(k)) for k in ("what_looks_true", "what_does_not_hold", "open_explanations") if lead.get(k)]
    texts += [str(v) for v in (lead.get("summary") or {}).values()] if isinstance(lead.get("summary"), dict) else []
    texts += [str(f.get("shows")) for f in lead.get("figures") or [] if isinstance(f, dict)]
    return texts


def method_words(lead: dict) -> list:
    """Where the lead says how: a number there may also be a listed constant or a count."""
    texts = [str(lead.get("how_it_was_found"))] if lead.get("how_it_was_found") else []
    texts += [str(t) for t in lead.get("pitfalls") or []]
    texts += [str(c.get("how") or c.get("why")) for key in ("choices_that_would_change_it", "choices_that_would_not")
              for c in lead.get(key) or [] if isinstance(c, dict)]
    return texts


def plan_quotes(lead: dict) -> list:
    """(sentence, the looks it names) for each sentence of the proposed plan that names a look: it quotes that look, so its
    numbers are checked against what the look printed. A sentence that names no look proposes, and is not checked."""
    out = []
    for v in (lead.get("proposed_plan") or {}).values() if isinstance(lead.get("proposed_plan"), dict) else []:
        for sentence in SENTENCE_END.split(" ".join(str(v).split())):
            named = sorted(set(LOOK_NAMED.findall(sentence)))
            if named:
                out.append((sentence, named))
    return out


def loose_in(text: str, backed: set, method: bool) -> set:
    t = number_forms(COUNT.sub(" ", text) if method else text)
    out = {n.strip() for n in QUOTED.findall(t) if as_written(n) not in backed and not (method and as_written(n) in CONSTANTS)}
    out |= {m.group(0).strip() for m in PERCENT.finditer(t) if m.group(1) not in backed and not (method and m.group(1) in CONSTANT_SHARES)}
    return out


def backing_pages(x: Exploration, ev: list) -> list:
    """The pages recorded as read that can back a number: each stands, unchanged, inside a wiki that `known` listed,
    and is not a file of this exploration, of a queue of drafts or of any role's own place. A page the explorer could
    have written (a note in `looks/`, an account in `record/`, a draft) backs nothing."""
    wikis = {Path(os.path.normpath(x.d / b)).resolve() for e in ev if e["kind"] == "knowledge.listed" for b in e["data"].get("bundles") or []}
    out = []
    for e in ev:
        if e["kind"] == "knowledge.read":
            f = Path(os.path.normpath(x.d / e["data"]["path"])).resolve()
            if (f.is_file() and sf.sha_file(f) == e["data"]["sha256"] and any(f.is_relative_to(w) for w in wikis)
                    and not f.is_relative_to(x.d) and not set(f.parts) & set(NOT_KNOWLEDGE)):
                out.append(f)
    return out


def unbacked_numbers(x: Exploration, lead: dict, ev: list | None = None) -> list:
    """Numbers in the lead's own words that no look it cites printed and no knowledge page recorded as read holds.
    A number counts only when it was printed whole and in the form the lead gives it: 1.4 is not backed by a look that
    printed 1.4826, and .8888 is not backed by 0.8888. A whole number given as a share (105 percent) is checked too."""
    def printed(texts: list) -> set:
        return {as_written(n) for t in texts for n in PRINTED.findall(t)}

    def out_of(lid: str) -> list:
        f = x.d / f"receipts/{lid}.out.txt"
        return [f.read_text(errors="replace")] if re.fullmatch(r"LOOK-\d{3,}", lid) and f.is_file() else []
    pages = printed([f.read_text(errors="replace") for f in backing_pages(x, ev or [])])
    backed = printed([t for lid in lead.get("evidence") or [] for t in out_of(str(lid))]) | pages
    loose = {n for t in result_words(lead) for n in loose_in(t, backed, False)}
    loose |= {n for t in method_words(lead) for n in loose_in(t, backed, True)}
    logged = {e["data"]["id"] for e in ev or [] if e["kind"] == "look.run"}
    for sentence, named in plan_quotes(lead):
        quoted = printed([t for lid in named if lid in logged for t in out_of(lid)]) | pages
        loose |= {f"{n} (in the proposed plan, in a sentence that quotes {', '.join(named)})" for n in loose_in(sentence, quoted, True)}
    return sorted(loose)


def render_lead(lead: dict) -> str:
    sa, tried = lead["set_aside"], lead["tried"]
    w = sa.get("window")
    aside = (f"{sa['how']}: {w['start']} to {'onward (the window stays open)' if w.get('open_ended') else w['end']}" if w
             else f"{sa['how']}: {', '.join(sa.get('sites') or sa.get('releases') or []) or 'nothing'}")
    if sa.get("cut_off"):
        aside += (f", after the cut-off {sa['cut_off']} (the working data was bound by checksum at the start, {len(sa.get('bound') or [])} "
                  "file(s), and a look at a file that changed or holds a later date is refused)")
    order = lead.get("order") or {"sequence": [], "choices": {}, "choices_recorded_after_looks": 0, "choices_in_all": 0}
    summ = lead.get("summary") or {}
    lines = [f"# Lead from {lead['exploration']} (exploring; version {lead['version']})", "", BANNER, ""]
    if summ:
        lines += ["## In short", "", f"**What looks true.** {' '.join(str(summ.get('looks_true')).split())}", "",
                  f"**How strong the evidence is.** {' '.join(str(summ.get('how_strong')).split())}", "",
                  f"**What it cannot settle.** {' '.join(str(summ.get('cannot_settle')).split())}", "",
                  "The rest of this page is the lead in full, with every choice and number behind it.", ""]
    lines += [f"**The question.** {lead['question']}", "",
             f"**What looks true.** {lead['what_looks_true'].strip()}", ""]
    if lead.get("what_does_not_hold"):
        lines += [f"**What does not hold.** {lead['what_does_not_hold'].strip()}", ""]
    if lead.get("open_explanations"):
        lines += [f"**Open explanations, not things seen.** {lead['open_explanations'].strip()}", ""]
    lines += [f"**How it was found.** {lead['how_it_was_found'].strip()}", "",
              f"**How many things were tried.** {tried['looks']} looks were run and logged, {tried['failed']} of them failed, and "
              f"{tried['refused']} more were refused at the fence. The lead rests on {', '.join(lead['evidence'])}. The count is "
              "taken from the exploration log, not from memory."
              + (f" The looks themselves declare {tried['comparisons_declared']} comparisons inside them (fits, cuts, groups)."
                 if tried.get("comparisons_declared") else "")
              + (f" {lead['fenced']['in_a_scratch_folder_only']} of the looks ran in a scratch folder only, with no kernel fence: on that "
                 "machine a script could open any file its user can, and the tool would not have seen it."
                 if (lead.get("fenced") or {}).get("in_a_scratch_folder_only") else ""), "",
              f"**What was set aside, and never looked at.** {aside}. Why: {sa.get('why')}"
              + (f" Neither explored nor set aside, and so protected by nothing: {sa['in_neither']['start']} to {sa['in_neither']['end']}."
                 if sa.get("in_neither") else ""), "",
              f"**What was explored.** {sa['working'].get('description') or 'see the log'}"
              + (" Working data outside the exploration, as declared at its start: " + ", ".join(f"`{q}`" for q in sa["working"]["places"]) + "."
                 if sa["working"].get("places") else ""), ""]
    for fig in lead.get("figures") or []:
        lines += [f"![{fig['shows']}]({fig['file']})", "", f"*Figure, drawn by {fig.get('look')} (sha256 {str(fig.get('sha256'))[:12]}): {fig['shows']}*", ""]
    if lead.get("corrections"):
        lines += ["## Corrections of wording since this version was recorded", "",
                  "No number was changed by any of these; a correction that changed one would have been refused.", ""]
        lines += [f"- Correction {c['n']}: \"{c['old']}\" now reads \"{c['new']}\". Why: {c['why']}" for c in lead["corrections"]] + [""]
    lines += ["## The order of looks and choices, from the log", "",
              (", then ".join(order["sequence"]) or "nothing yet") + ".", "",
              f"{order['choices_recorded_after_looks']} of {order['choices_in_all']} choices were written into the log after one or "
              "more looks had run. The log knows when a choice was written down, not when it was made: a choice written down "
              "after a look was either made knowing what the look showed or made earlier and logged late, and it is read as the first.", "",
              "## Choices that would change it", ""]
    by_id = {c["id"]: c for c in lead["choices"]}

    def when(cid: str) -> str:
        o = order["choices"].get(cid)
        if not o:
            return ""
        return (f" Written down after {o['after']}, when {o['after_looks']} look(s) had run." if o["after_looks"]
                else " Written down before any look.")

    for c in lead["choices_that_would_change_it"]:
        full = by_id[c["choice"]]
        lines += [f"- **{c['choice']}: {full['choice']}** Alternatives: {'; '.join(full['alternatives'])}. Rests on: "
                  f"{full['rests_on']}. How it would change the answer: {c['how']}{when(c['choice'])}"]
    lines += ["", "## Choices that would not", ""]
    for c in lead["choices_that_would_not"]:
        full = by_id[c["choice"]]
        lines += [f"- **{c['choice']}: {full['choice']}** Alternatives: {'; '.join(full['alternatives'])}. Why not: {c['why']}{when(c['choice'])}"]
    lines += ["", "## Pitfalls met", ""] + ([f"- {x}" for x in lead["pitfalls"]] or ["- none recorded"])
    lines += ["", "## Knowledge read before looking", ""]
    lines += [f"- `{k['path']}`: {'signed by ' + ', '.join(k['signed_by']) if k['signed'] else 'NOT SIGNED (status ' + str(k['status']) + ')'}"
              + (" (skimmed, not read whole)" if k.get("depth") == "skimmed" else "")
              + (" (read, though the search did not list it)" if k.get("listed") is False else "")
              + (f". Takes from it: {k['takes']}" if k.get("takes") else "") for k in lead["knowledge_read"]] or ["- none recorded as read"]
    if lead.get("listed_not_read"):
        lines += ["", "Listed by the search and not recorded as read: " + ", ".join(f"`{q}`" for q in lead["listed_not_read"]) + "."]
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
    if not reviewers(ev, len(ev)):
        raise Refused("no reviewer is named for this exploration. Whoever coordinates the work names the reviewer before a lead "
                      "exists (`explore.py reviewer --by <the coordinating agent> --reviewer agent:review-...`), so that the "
                      "name a review comes under was not chosen by the author once the lead was written. Hand the exploration "
                      "back for that, then record the lead")
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
    loose = unbacked_numbers(x, given, ev)
    if loose:
        raise Refused("the lead quotes numbers that none of the looks it cites under `evidence` printed (whole, digit for digit), "
                      "that no page of a listed wiki recorded as read holds, and, in a sentence of the proposed plan that names a look, "
                      "that the look named did not print: " + "; ".join(loose[:12])
                      + ". Every number in a lead comes from a look or a page of the knowledge base that was read; cite the look, "
                      "run it, or quote the number as it was printed: not rounded, not in another form (a decimal comma, an "
                      "exponent, a missing zero), and a share (`5 percent`) only when a look printed that number")
    drawn = {f["file"]: (e["data"]["id"], f["sha256"]) for e in ev if e["kind"] == "look.run" for f in e["data"].get("figures") or []}
    for fig in given.get("figures") or []:
        if sf.sha_file(x.d / fig["file"]) != drawn[fig["file"]][1]:
            raise Refused(f"{fig['file']} is not the picture {drawn[fig['file']][0]} drew; a figure in a lead is the file the look left")
    if given.get("figures"):
        given = {**given, "figures": [{**fig, "look": drawn[fig["file"]][0], "sha256": drawn[fig["file"]][1]} for fig in given["figures"]]}
    version = count(ev, "lead.recorded") + 1
    reads = [e["data"] for e in ev if e["kind"] == "knowledge.read"]
    lead = {"kind": "lead", "status": LEAD_STATUS, "version": version, "exploration": start["data"]["id"],
            "question": start["data"]["question"], "request_sha": start["data"]["request"]["sha"], **given,
            "tried": {"looks": count(ev, "look.run"), "failed": sum(1 for e in ev if e["kind"] == "look.run" and e["data"]["exit_code"] != 0),
                      "refused": count(ev, "look.refused"), "ids": [e["data"]["id"] for e in ev if e["kind"] == "look.run"],
                      "comparisons_declared": sum(int(e["data"].get("comparisons_declared") or 0) for e in ev if e["kind"] == "look.run")},
            "fenced": fence_counts(ev),
            "choices": [{k: e["data"][k] for k in ("id", "choice", "alternatives", "rests_on", "look")} for e in ev if e["kind"] == "choice.recorded"],
            "order": order_of(ev),
            "knowledge_read": [{k: r.get(k) for k in ("path", "sha256", "status", "signed", "signed_by", "takes", "depth", "listed")} for r in reads],
            "listed_not_read": listed_not_read(ev),
            "set_aside": start["data"]["set_aside"], "log_fingerprint": f"{ev[-1]['seq']}:{ev[-1]['hash']}"}
    sha = write_json(x.d / "lead.json", lead)
    md = render_lead(lead)
    (x.d / "lead.md").write_text(md)
    (x.d / "leads").mkdir(exist_ok=True)
    shutil.copyfile(x.d / "lead.json", x.d / "leads" / f"lead-v{version}.json")
    shutil.copyfile(x.d / "lead.md", x.d / "leads" / f"lead-v{version}.md")
    x.add(a.by, "lead.recorded", {"version": version, "json_sha": sha, "md_sha": sf.sha_file(x.d / "lead.md"),
                                  "source_sha": sf.sha_file(src), "tried": lead["tried"]})
    for line in sf.flags_in_words([f for f in lead_overclaiming(x, x.events()) if f["what"] == "lead.md"]):
        print(f"overclaiming check (a warning, not a refusal): {line}")
    print(f"lead version {version} recorded ({WAY}): lead.md, lead.json. {lead['tried']['looks']} looks behind it. "
          "Next: a review agent that did none of this picks holes in it. Do not `end` yet: an exploration ends as a lead "
          "only after its latest lead has been reviewed.")


def lead_overclaiming(x: Exploration, ev: list) -> list:
    """The overclaiming check of an exploration: the lead as it stands and every review of it. A lead is tested on nothing, so
    `confirms` is always flagged. A warning: nothing is refused on it."""
    name, listing = sf.overclaiming_listing(sf.FACTORY, "exploration")
    if not name or not lead_on_file(ev):
        return []
    flags = sf.overclaiming_flags((x.d / "lead.md").read_text(errors="replace"), listing, False, "lead.md")
    for e in ev:
        if e["kind"] == "review.verdict" and (x.d / e["data"]["file"]).is_file():
            flags += sf.overclaiming_flags((x.d / e["data"]["file"]).read_text(errors="replace"), listing, False, e["data"]["file"])
    return flags


def cmd_correct(x: Exploration, a) -> None:
    """One phrase of the recorded lead replaced, without a new version: for a slip of wording seen after recording.
    No number may change, the old words must be there exactly once, and the lead shows the old and the new."""
    ev = x.events()
    x.started()
    lead_ev, on_file = last(ev, "lead.recorded"), lead_on_file(ev)
    if not lead_ev:
        raise Refused("no lead is recorded; there is nothing to correct")
    old, new, why = str(a.old or ""), str(a.new or ""), str(a.why or "").strip()
    if not old.strip() or not new.strip() or old == new or not why:
        raise Refused("a correction names the words as they stand (`--old`), the words to put in their place (`--new`) and why (`--why`)")
    if max(len(old), len(new)) > 300:
        raise Refused("a correction is one phrase (300 characters at most); a larger change is a new version of the lead")
    digits = lambda t: re.findall(r"\d+|[.,](?=\d)|(?<=\d)[eE](?=[+-]?\d)|(?<=[eE])[+-](?=\d)|%|\bper ?cent\b", t)  # noqa: E731
    if digits(old) != digits(new):
        raise Refused("a correction changes words, never numbers: the numbers in `--old` and `--new` differ. A changed number "
                      "is a new version of the lead, which is reviewed again")
    for rx, instead in MISLEADING:
        if rx.search(new):
            raise Refused(f"the new words say `{rx.search(new).group(0)}`: {instead}")
    for name, key in (("lead.json", "json_sha"), ("lead.md", "md_sha")):
        if sf.sha_file(x.d / name) != on_file["data"][key]:
            raise Refused(f"{name} is not the lead that was recorded; nothing is corrected")
    lead = json.loads((x.d / "lead.json").read_text())
    lead.pop("way", None)
    spots = 0

    def swap(v):
        nonlocal spots
        if isinstance(v, str):
            spots += v.count(old)
            return v.replace(old, new)
        if isinstance(v, list):
            return [swap(i) for i in v]
        if isinstance(v, dict):
            return {k: swap(i) for k, i in v.items()}
        return v

    words = ("summary", "what_looks_true", "how_it_was_found", "what_does_not_hold", "open_explanations", "pitfalls",
             "choices_that_would_change_it", "choices_that_would_not", "proposed_plan")
    for k in words:
        if k in lead:
            lead[k] = swap(lead[k])
    if spots != 1:
        raise Refused(f"the words in `--old` stand {spots} time(s) in the lead's own words; a correction names words that stand there exactly once")
    n = len(lead.get("corrections") or []) + 1
    lead["corrections"] = list(lead.get("corrections") or []) + [{"n": n, "old": old, "new": new, "why": why, "by": a.by, "at": sf.now()}]
    sha = write_json(x.d / "lead.json", lead)
    (x.d / "lead.md").write_text(render_lead(lead))
    version = lead_ev["data"]["version"]
    shutil.copyfile(x.d / "lead.json", x.d / "leads" / f"lead-v{version}-correction-{n}.json")
    shutil.copyfile(x.d / "lead.md", x.d / "leads" / f"lead-v{version}-correction-{n}.md")
    x.add(a.by, "lead.corrected", {"version": version, "n": n, "old": old, "new": new, "why": why, "json_sha": sha,
                                   "md_sha": sf.sha_file(x.d / "lead.md")})
    print(f"lead version {version} corrected ({WAY}; correction {n}): one phrase, no number changed. The lead file you wrote "
          "(lead.yaml) is yours to bring in line, so a later version starts from the corrected words."
          + (" A review recorded before this correction no longer covers the lead: it is reviewed again before the exploration "
             "ends as a lead." if any(e["kind"] == "review.verdict" and e["seq"] > lead_ev["seq"] for e in ev) else ""))


def cmd_review(x: Exploration, a) -> None:
    ev = x.events()
    x.started()
    if a.verdict not in VERDICTS:
        raise Refused(f"the verdict is one of {VERDICTS}")
    if not last(ev, "lead.recorded") and not last(ev, "exploration.ended"):
        raise Refused("there is nothing to review yet: no lead is recorded and the exploration has not ended")
    if a.by.casefold() in did_the_work(ev):
        raise Refused(f"{a.by} did part of this exploration; the review is by an agent that did none of it")
    target = last(ev, "lead.recorded") or last(ev, "exploration.ended")
    named = reviewers(ev, target["seq"])
    if a.by.casefold() not in named:
        raise Refused(f"{a.by} was not named as a reviewer of this exploration before "
                      + (f"lead version {target['data']['version']} was recorded" if target["kind"] == "lead.recorded" else "it ended")
                      + ". A review comes from a reviewer the coordinating step named in the log beforehand (`explore.py reviewer`), "
                      "never from a name first typed at the review"
                      + (f". Named in time: {', '.join(sorted(named))}" if named else ""))
    if named[a.by.casefold()].casefold() in did_the_work(ev):
        raise Refused(f"{a.by} was named as a reviewer by {named[a.by.casefold()]}, who did part of this exploration; a reviewer "
                      "is named by someone who did none of it")
    src = Path(a.file).resolve()
    if not src.is_file():
        raise Refused(f"the review file {a.file} does not exist")
    on_file = lead_on_file(ev)
    if on_file:  # the verdict is for the words the reviewer read, not for whatever stands when the command arrives
        read = str(getattr(a, "read_lead", None) or "").strip().lower()
        if not read:
            raise Refused("`--read-lead` gives the sha256 of the lead.json you read (`status` prints it as `lead_json_sha256`): a "
                          "review is recorded for the words the reviewer read")
        if read != on_file["data"]["json_sha"]:
            raise Refused(f"the lead on file (lead.json, sha256 {on_file['data']['json_sha']}) is not the one you read (sha256 {read}): it "
                          "was revised or its wording corrected since. Read the lead as it stands and review that")
    n = count(ev, "review.verdict") + 1
    dest = x.d / "verdicts" / f"REVIEW-{n:03d}.md"
    if src != dest:
        shutil.copyfile(src, dest)
    lead = last(ev, "lead.recorded")
    x.add(a.by, "review.verdict", {"n": n, "verdict": a.verdict, "file": f"verdicts/{dest.name}", "sha": sf.sha_file(dest),
                                   "of_lead_version": lead["data"]["version"] if lead else None,
                                   "of_lead_json_sha": lead_on_file(ev)["data"]["json_sha"] if lead else None,
                                   "corrections_seen": sum(1 for e in ev if lead and e["kind"] == "lead.corrected" and e["seq"] > lead["seq"])})
    print(f"review {n} recorded ({WAY}): {a.verdict}")
    for line in sf.flags_in_words([f for f in lead_overclaiming(x, x.events()) if f["what"] == f"verdicts/{dest.name}"]):
        print(f"overclaiming check (a warning, not a refusal): {line}")


def cmd_reviewer(x: Exploration, a) -> None:
    """Name who will review this exploration. It is done by whoever coordinates the work, before a lead exists."""
    ev = x.events()
    x.started()
    x.check_actor(a.by)
    x.check_actor(a.reviewer)
    worked = did_the_work(ev)
    if a.by.casefold() in worked:
        raise Refused(f"{a.by} did part of this exploration; the reviewer is named by the coordinating step, which did none of it")
    if a.reviewer.casefold() in worked:
        raise Refused(f"{a.reviewer} did part of this exploration; a reviewer did none of it")
    if a.reviewer.casefold() == a.by.casefold():
        raise Refused("whoever names the reviewer is not the reviewer")
    if a.reviewer.casefold() in reviewers(ev, len(ev)):
        raise Refused(f"{a.reviewer} is already named as a reviewer of this exploration")
    x.add(a.by, "reviewer.named", {"reviewer": a.reviewer})
    lead = last(ev, "lead.recorded")
    print(f"reviewer named ({WAY}): {a.reviewer}"
          + (f". Lead version {lead['data']['version']} was recorded before this, so {a.reviewer} can review the next version, not that one"
             if lead else ". A review of any lead recorded from now on is taken from this name"))


# ---- the person's so what on a reviewed lead -------------------------------
def so_what_declared(factory=None) -> dict:
    """The definition's `procedure.so_what` block: who answers, by which route, through which harness, for which repository."""
    try:
        block = sf.definition_of(Path(factory or sf.FACTORY))["procedure"].get("so_what")
    except (Refused, KeyError, TypeError, AttributeError):
        return {}
    return block if isinstance(block, dict) else {}


def so_what_standing(ev: list, e: dict | None) -> str | None:
    """One of the three standings of a so what: typed (practice), a comment the job recorded, or a comment the platform confirmed."""
    if not e:
        return None
    if e["data"].get("route") != COMMENT:
        return sf.PRACTICE
    checks = [v for v in ev if v["kind"] == "so-what.verification" and (v["data"].get("of") or {}).get("seq") == e["seq"]]
    return sf.VERIFIED if checks and checks[-1]["data"].get("result") == sf.VERIFIED else COMMENT_FOUND


def so_what_now(ev: list):
    """The so what that stands for the lead as it stands: given on the lead on file, after its latest review. A new version,
    a correction of wording or a later review leaves the lead without one, because the person answered other words."""
    on = lead_on_file(ev)
    if not on or not review_stands(ev):
        return None
    after = max([on["seq"]] + [e["seq"] for e in ev if e["kind"] == "review.verdict"])
    given = [e for e in ev if e["kind"] == "so-what.recorded" and e["seq"] > after and e["data"].get("of_lead_json_sha") == on["data"]["json_sha"]]
    return given[-1] if given else None


def so_what_in_words(ev: list, e: dict | None) -> str:
    if not e:
        return "no person has said whether the lead as it stands is worth confirming"
    d = e["data"]
    words = d.get(SO_WHAT_NEEDS.get(d["answer"], ""), "")
    return (f"{d['answer']}" + (f" ({SO_WHAT_NEEDS[d['answer']]}: {words})" if words else "") + f", by {e['actor']}"
            + (f" (the comment's author on the platform: {d['comment']['author']})" if d.get("comment") else "")
            + f", on lead version {d['of_lead_version']}; standing: {so_what_standing(ev, e)}")


def so_what_problems(ev: list) -> list:
    """Why the lead as it stands may not go to a confirming study: no person said it is worth confirming."""
    now = so_what_now(ev)
    if now is None:
        return ["no person has said that the lead as it stands is worth confirming (`explore.py so-what`, a person's answer after the "
                "review; an agent may draft the question with `ask-so-what` and never records the answer)"]
    if now["data"]["answer"] != "worth-confirming":
        return [f"the person's so what on the lead as it stands is {so_what_in_words(ev, now)}, not worth-confirming"]
    return []


def practice_so_what(a) -> bool:
    return bool(getattr(a, "local_practice", False) or sf.Study.default_route == sf.PRACTICE or so_what_declared().get("route") == sf.PRACTICE)


def render_question(lead: dict, q: dict, x: Exploration, verdict: dict) -> str:
    sha = sf.sha_file(x.d / "lead.json")
    rel = os.path.relpath(x.d, Path.cwd()) if x.d.is_relative_to(Path.cwd()) else str(x.d)
    return "\n".join([
        f"# The so what: is lead version {lead['version']} of {lead['exploration']} worth confirming?", "",
        "An agent drafted this question; the answer is a person's, and no agent records it. The lead was reviewed "
        f"(verdict `{verdict['data']['verdict']}`, `{verdict['data']['file']}`). Read the lead (`lead.md`) and look at its figures yourself before you answer.", "",
        f"**What the lead shows.** {' '.join(str(q['what_the_lead_shows']).split())}", "",
        f"**Why it might matter.** {' '.join(str(q['why_it_might_matter']).split())}", "",
        f"**What would make it unremarkable.** {' '.join(str(q['what_would_make_it_unremarkable']).split())}", ""]
        + ((["**The options the lead sets out, none chosen.**", ""] + [f"{chr(97 + i)}. {' '.join(str(o).split())}" for i, o in enumerate(q["options"])] + [""])
           if q.get("options") else []) + [
        "## How to answer", "",
        "One of four: `worth-confirming` (it goes to a confirming study); `try-instead` with the direction in words (the exploration "
        "goes on, with that as its next question); `not-interesting` with a reason (the exploration ends as a lead noted, which is not "
        "a failure); `needs-an-expert` with the kind of expertise wanted.", "",
        "On the platform, as a comment on the tracking issue, with these lines (the job that follows the comment records it):", "",
        "```", "so-what: worth-confirming", f"exploration: {rel}", f"lead: {sha[:16]}", "```", "",
        "with `direction:`, `reason:` or `expertise:` on its own line for the other three. For trying the tools out, typed (practice): "
        f"`uv run tools/explore.py so-what --exploration {rel} --by human:<you> --answer worth-confirming --read-lead {sha} --local-practice`.", ""])


def cmd_ask_so_what(x: Exploration, a) -> None:
    """An agent drafts the question a person is asked about a reviewed lead: what it shows, why it might matter, what would
    make it unremarkable. The answer is not this command's: `so-what` is a person's."""
    ev = x.events()
    x.started()
    on = lead_on_file(ev)
    if not on:
        raise Refused("no lead is recorded; a so what is asked about a lead")
    if not review_stands(ev):
        raise Refused("the lead as it stands has not been reviewed: a person is asked about a lead after a reviewer has picked holes in it")
    if str(getattr(a, "read_lead", None) or "").strip().lower() != on["data"]["json_sha"]:
        raise Refused(f"`--read-lead` gives the sha256 of the lead.json the question is about, and the lead on file is {on['data']['json_sha']}")
    try:
        q = yaml.safe_load(Path(a.file).read_text())
    except (OSError, yaml.YAMLError) as err:
        raise Refused(f"the question file cannot be read as YAML ({err})")
    if not isinstance(q, dict) or not set(QUESTION_KEYS) <= set(q) or set(q) - set(QUESTION_KEYS) - set(QUESTION_OPTIONAL):
        raise Refused("the question file has these keys: " + ", ".join(QUESTION_KEYS) + ", and may have `options`: the ways on "
                      "the lead sets out for the person, none chosen")
    short = [k for k in QUESTION_KEYS if not isinstance(q[k], str) or len(q[k].split()) < 5]
    if short:
        raise Refused("each part of the question is a sentence or more, in words: " + ", ".join(short))
    if "options" in q and (not isinstance(q["options"], list) or len(q["options"]) < 2
                           or any(not isinstance(o, str) or len(o.split()) < 3 for o in q["options"])):
        raise Refused("`options` is a list of two or more ways on, each in words; leave the key out when the lead sets out none")
    lead = json.loads((x.d / "lead.json").read_text())
    n = count(ev, "so-what.asked") + 1
    out = x.d / "so-what"
    out.mkdir(exist_ok=True)
    dest = out / f"QUESTION-{n:03d}.md"
    dest.write_text(render_question(lead, q, x, last(ev, "review.verdict")))
    x.add(a.by, "so-what.asked", {"n": n, "file": f"so-what/{dest.name}", "sha": sf.sha_file(dest), "of_lead_version": on["data"]["version"],
                                  "of_lead_json_sha": on["data"]["json_sha"]})
    print(f"so-what question {n} written ({WAY}): so-what/{dest.name}. It is for a person; the answer is theirs (`explore.py so-what`), "
          "and no agent records it")


def comment_answer(path: Path, x: Exploration, on: dict, declared: dict) -> tuple:
    """(answer, words, comment) from the comment the job that follows a comment was handed, as the platform's API gives it. The names
    in it are what the job was handed: the so what stands as `comment recorded, person not verified` until the platform is asked."""
    try:
        rec = json.loads(Path(path).read_text())
    except (OSError, ValueError, TypeError):
        raise Refused("`--record-comment` names the JSON of the comment as the platform gives it (its issues/comments API); it could not be read")
    if not isinstance(rec, dict):
        raise Refused("the comment is not a mapping in the platform's shape")
    body = str(rec.get("body") or "")
    fields = {}
    for ln in body.splitlines():
        k, sep, v = ln.partition(":")
        k = k.strip().lower()
        if sep and k in ("so-what", "exploration", "lead", *SO_WHAT_NEEDS.values()) and k not in fields:
            fields[k] = v.strip()
    first = next((ln.strip() for ln in body.splitlines() if ln.strip()), "")
    user = rec.get("user") if isinstance(rec.get("user"), dict) else {}
    login, repo = str(user.get("login") or ""), str(declared.get("repository") or "")
    if not first.lower().startswith("so-what:"):
        raise Refused("the comment does not begin with a line `so-what: <answer>`, so it is no so what")
    if user.get("type") != "User" or not login or login.endswith("[bot]"):
        raise Refused("the platform does not call the comment's author a user: an app or a bot gives no person's so what")
    if str(rec.get("author_association") or "") not in ("OWNER", "MEMBER", "COLLABORATOR"):
        raise Refused("the comment's author does not belong to the repository, so the comment is no so what of this factory's people")
    if not repo or not str(rec.get("html_url") or "").startswith(f"https://github.com/{repo}/issues/") or not isinstance(rec.get("id"), int):
        raise Refused(f"the comment is not an issue comment of the repository the definition names ({repo or 'none is named'}), with its number")
    if fields.get("exploration", "").rstrip("/").rpartition("/")[2] not in (x.d.name, x.started()["data"]["id"]):
        raise Refused(f"the comment names the exploration `{fields.get('exploration')}`, not this one ({x.d.name})")
    lead = fields.get("lead", "").lower()
    if not re.fullmatch(r"[0-9a-f]{12,64}", lead) or not on["data"]["json_sha"].startswith(lead):
        raise Refused(f"the comment names the lead `{lead or 'nothing'}`; the lead on file is {on['data']['json_sha'][:16]}: a so what is for "
                      "the words the person read, and these are not them")
    answer = fields.get("so-what", "")
    comment = {"platform": "github", "id": rec["id"], "url": rec["html_url"], "author": login, "association": rec["author_association"],
               "created_at": rec.get("created_at"), "body_sha256": sf.sha_text(body),
               "people_source": "the comment the job was handed, on the machine where the command ran: not checked with the platform"}
    return answer, fields.get(SO_WHAT_NEEDS.get(answer, ""), ""), comment


def cmd_so_what(x: Exploration, a) -> None:
    """A person's answer to a reviewed lead: worth-confirming, try-instead (with a direction), not-interesting (with a reason)
    or needs-an-expert (with the kind of expertise). No agent records it: typed, it is practice; on the platform it is a
    person's comment on the tracking issue, which the job that follows the comment records here."""
    ev = x.events()
    start = x.started()
    if breached(ev):
        raise Refused("this exploration is spoiled (set-aside data reached it); there is no lead to answer")
    if last(ev, "exploration.ended"):
        raise Refused("this exploration has ended; a so what is given on a reviewed lead before the end")
    on = lead_on_file(ev)
    if not on:
        raise Refused("no lead is recorded; a so what answers a lead")
    if not review_stands(ev):
        raise Refused("the lead as it stands has not been reviewed: a person answers a lead after a reviewer has picked holes in it")
    declared = so_what_declared(getattr(a, "factory", None))
    if getattr(a, "record_comment", None):
        if not sf.PLATFORM_ACTOR.fullmatch(str(a.by)):
            raise Refused("a so what that was a comment is recorded under the platform's name (`--by platform:github`), by the job that "
                          "follows the comment; the person is read from the platform's record, not typed")
        answer, words, comment = comment_answer(Path(a.record_comment), x, on, declared)
        route = COMMENT
    else:
        if not str(a.by).startswith("human:") or str(a.by).lower() in sf.PLACEHOLDER_ACTORS:
            raise Refused("the so what is a person's answer, under human:<their id>. An agent drafts the question (`ask-so-what`) and "
                          "never records the answer, by any route")
        if not practice_so_what(a):
            raise Refused("on this factory a so what is a person's comment on the tracking issue, which the job that follows the comment "
                          "records (`so-what --record-comment`) and the platform confirms (`verify-so-what`). Typed at a command line it is "
                          "practice, and says so: add `--local-practice` to try the tools out")
        if str(getattr(a, "read_lead", None) or "").strip().lower() != on["data"]["json_sha"]:
            raise Refused(f"`--read-lead` gives the sha256 of the lead.json you read (`status` prints it); the lead on file is {on['data']['json_sha']}")
        answer, comment, route = a.answer, None, sf.PRACTICE
        words = getattr(a, SO_WHAT_NEEDS.get(a.answer, "") or "direction", None) if a.answer in SO_WHAT_NEEDS else None
        for k in set(SO_WHAT_NEEDS.values()) - {SO_WHAT_NEEDS.get(a.answer)}:
            if getattr(a, k, None):
                raise Refused(f"`--{k}` goes with {next(w for w, n in SO_WHAT_NEEDS.items() if n == k)}, not with {a.answer}")
    if answer not in SO_WHAT:
        raise Refused(f"the answer is one of {', '.join(SO_WHAT)}")
    words = " ".join(str(words or "").split())
    if answer in SO_WHAT_NEEDS and len(words.split()) < 3:
        raise Refused(f"{answer} says its {SO_WHAT_NEEDS[answer]} in words (`--{SO_WHAT_NEEDS[answer]}`, or a line `{SO_WHAT_NEEDS[answer]}:` in the comment)")
    asked = [e for e in ev if e["kind"] == "so-what.asked" and e["data"]["of_lead_json_sha"] == on["data"]["json_sha"]]
    data = {"answer": answer, "of_lead_version": on["data"]["version"], "of_lead_json_sha": on["data"]["json_sha"], "route": route,
            "question": {k: asked[-1]["data"][k] for k in ("n", "file", "sha")} if asked else None}
    if answer in SO_WHAT_NEEDS:
        data[SO_WHAT_NEEDS[answer]] = words
    if comment:
        data["comment"] = comment
    e = x.add(a.by, "so-what.recorded", data)
    if answer == "not-interesting":
        x.add(a.by, "exploration.ended", {"outcome": "lead-noted", "summary": words, "so_what": {"seq": e["seq"], "hash": e["hash"]}})
    then = {"worth-confirming": "the analysis agent may end the exploration as a lead, and the coordinating agent may hand it over",
            "try-instead": f"the exploration goes on, with this as its next question: {words}. A new lead is reviewed and answered again",
            "not-interesting": "the exploration has ended as a lead noted: not a failure, and nothing is handed over",
            "needs-an-expert": f"the lead waits for someone with this expertise: {words}. Their so what, on the same lead, decides"}[answer]
    print(f"so what recorded ({WAY}): {answer}" + (" (practice: typed at a command line)" if route == sf.PRACTICE else
                                                   f" (a comment by {comment['author']}; standing `{COMMENT_FOUND}` until `verify-so-what`)")
          + f". Next: {then}")


def so_what_harness(declared: dict):
    """The verifier of the harness the definition names for the so what, from this factory's own definition."""
    name = str(declared.get("harness") or "")
    folder = sf.FACTORY.resolve() / "harnesses" / name
    try:
        block = (yaml.safe_load((folder / "harness.yaml").read_text()) or {}).get("platform") if re.fullmatch(r"[a-z][a-z0-9-]{0,40}", name) else None
    except (OSError, yaml.YAMLError):
        block = None
    if not isinstance(block, dict) or not str(block.get("api") or "").startswith("https://") or not (folder / "verify_acts.py").is_file():
        raise Refused("the definition names no harness for the so what that can ask a platform (`procedure.so_what.harness`)")
    return _load(f"sf_verify_so_what_{name.replace('-', '_')}", folder / "verify_acts.py"), block


def cmd_verify_so_what(x: Exploration, a) -> None:
    """Ask the platform about each so what that was a comment, and record what it said. Anybody may run it, at any time."""
    ev = x.events()
    x.started()
    targets = [e for e in ev if e["kind"] == "so-what.recorded" and e["data"].get("route") == COMMENT]
    if not targets:
        print("verify-so-what: nothing to ask the platform about: every so what here was typed (practice), or there is none")
        return
    declared = so_what_declared(getattr(a, "factory", None))
    mod, block = so_what_harness(declared)
    name, token = mod.token_from(os.environ)
    for e in targets:
        c = e["data"]["comment"]
        data = {"of": {"seq": e["seq"], "hash": e["hash"], "comment": c["id"]}, "result": sf.NOT_CHECKED, "problems": [], "told": {}, "asked": [],
                "platform": block.get("name"), "api": block["api"], "repository": declared.get("repository"), "token_from": name,
                "through": mod.through(os.environ), "stand_in_for_the_platform": sf.PLATFORM_CALL is not None}
        if sf.PLATFORM_CALL is None and not token:
            data["problems"] = ["no token: the platform is asked with a token from the environment (" + ", ".join(mod.TOKEN_NAMES)
                                + "), and none of those is set. Nothing was asked, so nothing is verified"]
        else:
            got = mod.verify_comment(sf.PLATFORM_CALL or mod.platform_call, block["api"], token or "a-self-test",
                                     {"repository": declared.get("repository"), "id": c["id"], "author": c["author"], "body_sha256": c["body_sha256"]})
            data.update({k: got[k] for k in ("result", "problems", "told", "asked", "answers_sha256")})
        if not getattr(a, "report_only", False):
            x.add(a.by, "so-what.verification", data)
        print(f"so what at event {e['seq']} ({e['data']['answer']}): {data['result']}" + (": " + "; ".join(data["problems"]) if data["problems"] else ""))


def cmd_end(x: Exploration, a) -> None:
    ev = x.events()
    x.started()
    if a.outcome not in OUTCOMES:
        raise Refused(f"an exploration ends as one of {OUTCOMES}")
    if a.outcome == "lead-noted":
        raise Refused("an exploration ends as a lead noted when a person says the reviewed lead is not interesting (`so-what --answer "
                      "not-interesting`), and that ends it; no agent ends one so")
    data = {"outcome": a.outcome, "summary": a.summary}
    if a.outcome == "lead":
        if breached(ev):
            raise Refused("this exploration is spoiled; it can end as a stop, not as a lead")
        if not last(ev, "lead.recorded"):
            raise Refused("no lead is recorded; record it with `lead`, or end as a note, a method or a stop")
        if not reviewed(ev):
            raise Refused("the latest lead has not been reviewed: an exploration ends as a lead only after a review agent "
                          "has looked at the lead it ends on. Hand it back for review; `end` comes after the review is answered")
        if not review_stands(ev):
            raise Refused("the lead was corrected after it was reviewed: the review covers the words the reviewer saw, not the "
                          "words that stand now. Hand it back for review; `end` comes after the corrected lead has been reviewed")
        wanting = so_what_problems(ev)
        if wanting:
            raise Refused("an exploration ends as a lead once a person has said the reviewed lead is worth confirming: "
                          + wanting[0] + ". Results that are technically right are often unremarkable until somebody who knows the "
                          "field says why they matter; the coordinating agent asks the person (the question can be drafted with `ask-so-what`)")
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
    print(f"ended ({WAY}) as a {a.outcome}." + (" Next: `hand-over`, by the coordinating agent." if a.outcome == "lead" else ""))


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
            p.append("no review agent has looked at the latest lead")
        elif not review_stands(ev):
            p.append("the lead was corrected after its latest review, so no review covers the lead as it stands")
        for name, key in (("lead.json", "json_sha"), ("lead.md", "md_sha")):
            if sf.sha_file(x.d / name) != lead_on_file(ev)["data"][key]:
                p.append(f"{name} is not the lead that was recorded")
        p += so_what_problems(ev)
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
        raise Refused(f"{a.by} did the exploring; the hand-over is made by the coordinating agent, which did not")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", a.study_id or "") or a.study_id == x.d.name:
        raise Refused("`--study-id` names the confirming study (for example STUDY-0002); it is not the exploration's name")
    said = so_what_now(ev)
    if so_what_standing(ev, said) == sf.PRACTICE and not practice_so_what(a):
        raise Refused("the person's so what on this lead was typed at a command line (practice), and on this factory a so what is a "
                      "person's comment on the tracking issue. A hand-over from a practice so what says so: add `--local-practice`, and the "
                      "lock request will show it")
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
        f"{lead['tried']['failed']} failed, {lead['tried']['refused']} were refused at the fence."
        + (f" {lead['fenced']['in_a_scratch_folder_only']} of the looks ran in a scratch folder only, with no kernel fence."
           if (lead.get("fenced") or {}).get("in_a_scratch_folder_only") else ""), "",
        f"**The question proposed for the confirming study.** {stub['question']}", "",
        f"**The difference that matters, as proposed.** {stub['difference_that_matters']}", "",
        "**Already looked at (working data from now on).** " + str(sa["working"].get("description") or "see the exploration log") + "", "",
        *([f"**The fresh data, as proposed.** {sa['fresh_data']['kind_in_words'].capitalize()}, proposed by {sa['fresh_data']['proposed_by']} "
           f"at {sa['fresh_data']['proposed_at']} from metadata only; the proposal is `hand-over/fresh-data.yaml`, and the lock shows it in words.", ""]
          if sa.get("fresh_data") else []),
        "**Held out.** Only what the exploration set aside: " + (f"{w['start']} to {'onward' if w.get('open_ended') else w['end']}" if w
                                                               else ", ".join(sa.get("sites") or sa.get("releases") or []))
        + (f", after the cut-off {sa['cut_off']}; the study takes the cut-off and the working data's checksums from this exploration's "
           "start" if sa.get("cut_off") else "") + f". {sa.get('why')}", "",
        f"**The review of the lead.** {verdict['data']['verdict']} ({verdict['data']['file']} in the exploration), recorded "
        f"under the name {verdict['actor']}"
        + (f", who was named as a reviewer by {reviewers(ev, len(ev)).get(verdict['actor'].casefold())} before the lead was recorded"
           if verdict["actor"].casefold() in reviewers(ev, len(ev)) else "")
        + (f". The lead's wording was corrected {len(lead['corrections'])} time(s) before that review, and not since" if lead.get("corrections") else "")
        + f"; the exploring was done under {', '.join(sorted({e['actor'] for e in ev if e['kind'] in ('look.run', 'lead.recorded')}))}. "
        "Names are typed, not proven: whether the reviewer was a separate agent with a fresh context is in the run's record, not in this line.", "",
        f"**The so what.** {so_what_in_words(ev, said)}.", "",
        f"**The fit note.** {' '.join(sf.fit_in_words(last(ev, 'fit.noted'))[:2])}", "",
        f"Lead checksum (lead.json): {sf.sha_file(x.d / 'lead.json')}. Exploration log fingerprint: {ev[-1]['seq']}:{ev[-1]['hash']}.", ""])
    (out / "request.md").write_text(request)
    held = {"pair": sa["subject"], "why_this_window": sa.get("why")}
    fd = sa.get("fresh_data")
    if fd:  # the proposal and its seed travel with the hand-over, byte for byte, so the plan can name them and the lock show them
        src = Path(fd["file"])
        if sf.sha_file(src) != fd["sha256"]:
            raise Refused(f"the proposal of the fresh data this exploration set aside ({src}) is missing or changed since the start")
        shutil.copyfile(src, out / "fresh-data.yaml")
        if fresh_tool().seed_path(src).is_file():
            shutil.copyfile(fresh_tool().seed_path(src), out / "fresh-data.seed")
        held["fresh_data"] = os.path.relpath(out / "fresh-data.yaml", x.record().parent / a.study_id)
    if w:
        held["window"] = {"start": w["start"], "end": "CHOOSE: a date inside the set-aside window" if w.get("open_ended") else w["end"]}
    if sa.get("cut_off"):  # the release: its window starts the day after the cut-off
        held["window"] = {"start": (dt.date.fromisoformat(sa["cut_off"]) + dt.timedelta(days=1)).isoformat(),
                          "end": "CHOOSE: the last day of the last period the plan needs"}
    plan_stub = {"study": a.study_id, "question": stub["question"], "quantity_estimated": stub["quantity_estimated"],
                 "data": {"working": str(sa["working"].get("description") or "") + " Explored in " + start["data"]["id"]
                          + ": already seen, never held out.", "held_out": held},
                 "from_the_lead": {k: v for k, v in stub.items() if k not in ("question", "quantity_estimated")},
                 "choices_to_fix_in_the_plan": [f"{c['choice']}: {c['how']}" for c in lead["choices_that_would_change_it"]],
                 "pitfalls_to_make_hard_cases": lead["pitfalls"]}
    (out / "analysis-plan.stub.yaml").write_text(
        f"# Exploring: a stub from {start['data']['id']}, not an analysis plan. The study tool will not read this file.\n"
        "# The analysis agent writes analysis-plan.yaml from factory/templates/analysis-plan.yaml at the plan stage and takes\n"
        "# from here the question, the quantity, the data and the choices to fix. The held-out data may only be what the\n"
        "# exploration set aside; `explore.py check-study` refuses anything else.\n"
        + yaml.safe_dump(plan_stub, sort_keys=False, allow_unicode=True, width=110))
    study_dir = os.path.relpath(x.record().parent / a.study_id, x.d)
    command = ["uv", "run", "tools/sf.py", "start", "--study", f"<the exploration>/{study_dir}", "--id", a.study_id,
               "--question", stub["question"], "--request", "<the exploration>/hand-over/request.md", "--by", "agent:<the coordinating agent>", "--model", "<the model it runs as>"]
    figs = []
    (out / "figures").mkdir(exist_ok=True)
    for e in ev:  # every figure a look kept, by checksum, with the look's own reason as its caption: the lock shows them all
        if e["kind"] == "look.run":
            for fig in e["data"].get("figures") or []:
                src_fig = x.d / fig["file"]
                if sf.sha_file(src_fig) != fig["sha256"]:
                    raise Refused(f"the figure {fig['file']} of {e['data']['id']} is not the picture the look kept; nothing is handed over")
                name = f"{e['data']['id']}-{Path(fig['file']).name}"
                shutil.copyfile(src_fig, out / "figures" / name)
                figs.append({"file": f"figures/{name}", "sha256": fig["sha256"], "look": e["data"]["id"],
                             "caption": " ".join(str(e["data"].get("why") or "").split())[:300]})
    write_json(out / "figures.json", {"kind": "the exploration's figures, for the lock", "figures": figs})
    sha = write_json(out / "hand-over.json", {
        "kind": "hand-over", "from": start["data"]["id"], "for": "sf.py start", "study_id": a.study_id,
        "study_directory_from_exploration": study_dir, "question": stub["question"],
        "request": {"file": "hand-over/request.md", "sha256": sf.sha_file(out / "request.md")},
        "plan_stub": {"file": "hand-over/analysis-plan.stub.yaml", "sha256": sf.sha_file(out / "analysis-plan.stub.yaml")},
        "lead": {"version": lead["version"], "sha256": sf.sha_file(x.d / "lead.json"), "status": LEAD_STATUS},
        "review": verdict["data"], "so_what": {"seq": said["seq"], "hash": said["hash"], "answer": said["data"]["answer"], "by": said["actor"],
                                              "standing": so_what_standing(ev, said)},
        "set_aside": sa, "record": start["data"]["record"], "start_command": command,
        "then": "after the plan is written: explore.py check-study --exploration <this> --study <the study>"})
    x.add(a.by, "handed.over", {"study_id": a.study_id, "hand_over_sha": sha,
                                "request_sha": sf.sha_file(out / "request.md"), "study_directory_from_exploration": study_dir})
    print(f"handed over ({WAY}): hand-over/request.md, hand-over/analysis-plan.stub.yaml, hand-over/hand-over.json.\n"
          f"Start the study with:\n  uv run tools/sf.py start --study {study_dir} --id {a.study_id} --question \"{stub['question']}\" "
          "--request hand-over/request.md --by agent:<the coordinating agent> --model <the model it runs as>\n(paths from the exploration directory)")


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
    if sa.get("cut_off"):  # the release the exploration set aside, as its start bound it, is the one the study started with
        rel = sf.release_of(sev) or {}
        bound = sorted(b["sha256"] for b in sa.get("bound") or [])
        if rel.get("cut_off") != sa["cut_off"] or sorted(w["sha256"] for w in rel.get("working") or []) != bound:
            p.append(f"the exploration set aside the release after {sa['cut_off']} and bound {len(bound)} working file(s) at its start, and "
                     "the study did not start with that cut-off and those files: start it from hand-over/request.md, which brings them")
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
    if sa.get("fresh_data"):
        named = held.get("fresh_data")
        if not named or sf.sha_file(study.d / str(named)) != sa["fresh_data"]["sha256"]:
            p.append("the exploration set aside the fresh data a proposal named, and the plan's `data.held_out.fresh_data` does not name "
                     "that proposal, byte for byte (hand-over/fresh-data.yaml)")
    names = json.dumps(pair or {}).casefold() + " " + str(held.get("path") or "").casefold()
    if sa.get("sites") and not any(names_token(names, str(s), sa) for s in sa["sites"]):
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
        "contract": "the curating agent drafts at status draft with its own generated event; it never merges and never "
                    "signs. A lead is never drafted as a finding: what may be drafted from it is its pitfalls and what it "
                    "learned about the data, each marked as seen while exploring"})
    print(f"curation list ({WAY}): {len(notes)} open note(s); curation-list.json sha256 {sha[:12]}")


def cmd_resolve(x: Exploration, a) -> None:
    ev = x.events()
    if a.disposition not in DISPOSITIONS:
        raise Refused(f"the disposition is one of {DISPOSITIONS}")
    if a.note not in {e["data"]["id"] for e in open_notes(ev)}:
        raise Refused(f"{a.note} is not an open note of this exploration")
    if not last(ev, "exploration.ended"):
        raise Refused("this exploration has not ended: its notes can still change and its lead can still be revised after a "
                      "review. The curating agent waits until `status` says the exploration has ended (stage `learn`, "
                      "`hand-over` or `ended`), then resolves each note")
    if a.disposition != "declined" and not a.ref:
        raise Refused("a drafted or linked note names the draft or the concept (`--ref`)")
    if a.disposition == "declined" and not str(a.comment or "").strip():
        raise Refused("a declined note says why (`--comment`)")
    x.add(a.by, "note.resolved", {"id": a.note, "disposition": a.disposition, "ref": a.ref, "comment": a.comment})
    print(f"{a.note}: {a.disposition} ({WAY})")


def stage_of(x: Exploration) -> dict:
    ev = x.events()
    if not ev:
        return {"way": WAY, "stage": "set-aside", "who": "analysis agent",
                "does": "decide what will not be looked at and start the exploration (explore.py start)"}
    start = ev[0]["data"]
    lead, ended, over = last(ev, "lead.recorded"), last(ev, "exploration.ended"), last(ev, "handed.over")
    verdict = last(ev, "review.verdict")
    counts = {"looks": count(ev, "look.run"), "looks_failed": sum(1 for e in ev if e["kind"] == "look.run" and e["data"]["exit_code"] != 0),
              "looks_refused_at_the_fence": count(ev, "look.refused"), "choices": count(ev, "choice.recorded"),
              "knowledge_read": count(ev, "knowledge.read"), "listed_and_not_read": len(listed_not_read(ev)),
              "open_notes": [e["data"]["id"] for e in open_notes(ev)]}
    if count(ev, "reviewer.named"):
        counts["reviewers_named"] = sorted({e["data"]["reviewer"] for e in ev if e["kind"] == "reviewer.named"})
    if lead and count(ev, "lead.corrected"):
        counts["wording_corrections_to_the_latest_lead"] = sum(1 for e in ev if e["kind"] == "lead.corrected" and e["seq"] > lead["seq"])
    if breached(ev) and not ended:
        here = {"stage": "spoiled", "who": "analysis agent", "does": "set-aside data reached the exploration: end it as a stop and say so"}
    elif not last(ev, "knowledge.listed"):
        here = {"stage": "read-what-is-known", "who": "analysis agent", "does": "list and read the knowledge that bears on the question (explore.py known, read)"}
    elif ended:
        if ended["data"]["outcome"] == "lead" and not over:
            here = {"stage": "hand-over", "who": "coordinating agent", "does": "hand the lead to the confirming way (explore.py hand-over), or leave it"}
            blockers = handover_problems(x, ev)
            if blockers:
                here.update(stage="review", who="review agent", still_needs=blockers)
        elif open_notes(ev):
            here = {"stage": "learn", "who": "curating agent", "does": "every open note drafted, linked or declined (explore.py curation-list, resolve)"}
        else:
            here = {"stage": "ended"}
        here["outcome"] = ended["data"]["outcome"]
        if over:
            here["handed_over_to"] = over["data"]["study_id"]
    elif not lead:
        here = {"stage": "explore", "who": "analysis agent", "does": "look, record choices and notes, then write up the lead or end as a note, a method or a stop"}
        if not reviewers(ev, len(ev)):
            here["before_a_lead"] = ("the coordinating agent names the reviewer (explore.py reviewer); `lead` is refused until "
                                     "a reviewer is named")
    elif not verdict or verdict["seq"] < lead_on_file(ev)["seq"]:
        here = {"stage": "review", "who": "review agent", "does": "pick holes in the lead (explore.py review)",
                "not_yet": "the analysis agent does not `end`, and the curating agent does not `resolve`, until the latest lead is reviewed"}
    else:
        said = so_what_now(ev)
        answer = said["data"]["answer"] if said else None
        if answer == "worth-confirming":
            here = {"stage": "revise-or-end", "who": "analysis agent", "last_review": verdict["data"]["verdict"],
                    "does": "a person said the lead is worth confirming: end the exploration on it (explore.py end --outcome lead), or "
                            "revise it (a new version is reviewed and answered again)",
                    "not_yet": "the curating agent waits for the end"}
        elif answer == "try-instead":
            here = {"stage": "explore", "who": "analysis agent", "next_question": said["data"]["direction"],
                    "does": "a person asked for another direction: explore it, then write up a new version of the lead, which is reviewed and answered again"}
        elif answer == "needs-an-expert":
            here = {"stage": "so-what", "who": "people", "waiting_for": said["data"]["expertise"],
                    "does": "the lead waits for a person with this expertise; their so what on the same lead decides"}
        else:
            here = {"stage": "so-what", "who": "people", "last_review": verdict["data"]["verdict"],
                    "does": "a person says whether the reviewed lead is worth confirming (explore.py so-what; on the platform, a comment on "
                            "the tracking issue). The coordinating agent asks them, and may have the question drafted (explore.py ask-so-what)",
                    "not_yet": "no agent ends the exploration as a lead, or hands it over, before a person says it is worth confirming"}
        if said:
            here["so_what"] = so_what_in_words(ev, said)
    if lead:
        counts["lead_json_sha256"] = lead_on_file(ev)["data"]["json_sha"]
    if lead:
        counts["overclaiming"] = sf.flags_in_words(lead_overclaiming(x, ev))[:20]
    given = [e for e in ev if e["kind"] == "so-what.recorded"]
    if given:
        counts["so_whats"] = [{"seq": e["seq"], "answer": e["data"]["answer"], "by": e["actor"], "of_lead_version": e["data"]["of_lead_version"],
                               "standing": so_what_standing(ev, e)} for e in given]
    counts["looks_by_fence"] = fence_counts(ev)
    counts["working_data_declared"] = (start["set_aside"].get("working") or {}).get("places") or []
    counts["fit"] = " ".join(sf.fit_in_words(last(ev, "fit.noted"))[:2])
    return {"way": WAY, "exploration": start["id"], "question": start["question"], **here, **counts,
            "models_recorded": {"by_actor": sf.models_recorded(ev), "note": "declared by whoever called the tool; nothing proves which model answered"},
            "set_aside": {k: start["set_aside"].get(k) for k in ("how", "window", "sites", "releases", "cut_off")},
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
    p += [f"event {e['seq']} ({e['kind']}) was written by an agent and names no model: every event an agent writes records the model that wrote it"
          for e in ev if str(e["actor"]).startswith("agent:") and not e.get("model")]
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
        elif e["kind"] == "so-what.asked" and sf.sha_file(x.d / d["file"]) != d["sha"]:
            p.append(f"the so-what question {d['file']} is missing or was changed")
    for e in ev:
        if e["kind"] == "look.run":
            for fig in e["data"].get("figures") or []:
                if sf.sha_file(x.d / fig["file"]) != fig["sha256"]:
                    p.append(f"the figure {fig['file']} of {e['data']['id']} is missing or was changed")
            if e["data"].get("err_sha") and sf.sha_file(x.d / f"receipts/{e['data']['id']}.err.txt") != e["data"]["err_sha"]:
                p.append(f"the standard error of {e['data']['id']} is missing or was changed")
    lead = lead_on_file(ev)
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
    _tracked, committed = x.committed_log()
    if committed is not None and not x.log.read_text().startswith(committed):
        p.append("the exploration log is not the log that was last committed with more added to it: it was rewritten or cut "
                 "short since the commit. A log is only ever added to")
    return p


def remarks(ev: list) -> list:
    """Where a log that checks out departs from the order the tool now holds. Such a log was written before the tool
    refused these things; it is kept as it was written and stays readable, and the remark says what a reader should know."""
    r = []
    ended = last(ev, "exploration.ended")
    early = [e for e in ev if e["kind"] == "note.resolved" and (not ended or e["seq"] < ended["seq"])]
    if early:
        r.append(f"{len(early)} note(s) were resolved (events {early[0]['seq']} to {early[-1]['seq']}) before the exploration had ended"
                 + ("" if reviewed([e for e in ev if e["seq"] < early[0]["seq"]]) or not last(ev[:early[0]["seq"]], "lead.recorded")
                    else ", and before the latest lead of that moment had been reviewed")
                 + ". The tool now refuses that: the curating agent waits for the end")
    if ended and ended["data"]["outcome"] == "lead" and not reviewed([e for e in ev if e["seq"] < ended["seq"]]):
        r.append("the exploration ended as a lead before its latest lead had been reviewed. The tool now refuses that")
    merged = [e["data"]["id"] for e in ev if e["kind"] == "look.run" and e["data"].get("streams") != "separate"]
    if merged:
        r.append(f"{len(merged)} look(s) ({merged[0]} to {merged[-1]}) were logged when the tool kept standard error inside a look's output, "
                 "so a launcher's `warning:` lines may stand in their outputs. `recheck` compares such a look with those lines set aside")
    if any(e["kind"] == "look.run" for e in ev) and not last(ev, "knowledge.read"):
        r.append("looks were run with no page recorded as read. The tool now refuses the first look until a `read` is recorded")
    return r


def cmd_check_log(x: Exploration, a) -> None:
    problems = check_log(x, a.anchor)
    for q in problems:
        print("check-log:", q)
    if problems:
        raise Refused(f"{len(problems)} problem(s): the exploration log or its files do not check out")
    ev = x.events()
    for q in remarks(ev):
        print("check-log: remark (the log is kept as it was written):", q)
    print(f"check-log: PASS ({WAY}; {len(ev)} events, fingerprint {ev[-1]['seq']}:{ev[-1]['hash']}). As with the study log, "
          "a rewritten log shows only against a fingerprint posted outside the workspace or, in git, against the last commit and no "
          "earlier one: a log rewritten and then committed again passes this check.")


README_PARTS = ("**What it computes.**", "**On what inputs.**", "**Known limits.**")  # what the agent's README of a promoted method says
KNOWN_ANSWER_TESTS = """# /// script
# requires-python = ">=3.11"
# dependencies = DEPENDENCIES
# ///
\"\"\"Known-answer tests of the promoted method NAME, written by `explore.py promote`.

Each case is a look of the exploration the method came from: the files it was given and the output its script
printed. This runs the script on each case's files, in a folder of its own, and compares what it prints with what
the look printed, byte for byte. The checksum of every case file is written below, so a case changed after the
promotion fails here, and the lock that binds this file binds the cases with it.

  uv run known_answer_tests.py [--out RECEIPT.json]

Exit 0 when every case reproduces; 1 otherwise.
\"\"\"
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / SCRIPT_NAME
CASES = CASE_SHAS


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    results = []
    for case, files in sorted(CASES.items()):
        folder = HERE / "known-answers" / case
        changed = [rel for rel, h in files.items() if not (folder / rel).is_file() or sha(folder / rel) != h]
        if changed:
            results.append({"case": case, "passed": False, "why": "case files changed since the promotion: " + ", ".join(changed)})
            continue
        c = json.loads((folder / "case.json").read_text())
        with tempfile.TemporaryDirectory() as t:
            for rel in c["inputs"]:
                (Path(t) / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(folder / "inputs" / rel, Path(t) / rel)
            done = subprocess.run([sys.executable, str(SCRIPT), *c["args"]], cwd=t, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        same = done.returncode == 0 and done.stdout == (folder / "expected.out.txt").read_text()
        results.append({"case": case, "passed": same, "why": "" if same else f"exit {done.returncode}; the output differs from what the look printed"})
    passed = sum(r["passed"] for r in results)
    receipt = {"method": NAME_JSON, "script_sha256": sha(SCRIPT), "cases": len(results), "passed": passed, "results": results}
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(receipt, indent=1) + "\\n")
    for r in results:
        print(("pass  " if r["passed"] else "FAIL  ") + r["case"] + (f": {r['why']}" if r["why"] else ""))
    good = bool(results) and passed == len(results)
    print(f"known-answer tests of NAME: {'PASS' if good else 'FAIL'} ({passed} of {len(results)})")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
"""


def inline_dependencies(script: Path) -> list:
    """The `dependencies` of a script's inline header (PEP 723), so the method's tests run in the same environment."""
    text = script.read_text(errors="replace")
    block = re.search(r"^# /// script\n((?:#.*\n)+?)# ///", text, re.M)
    if not block:
        return []
    try:
        meta = tomllib.loads("\n".join(ln[2:] if ln.startswith("# ") else ln[1:] for ln in block.group(1).splitlines()))
    except (tomllib.TOMLDecodeError, ValueError):
        return []
    deps = meta.get("dependencies") or []
    return [str(d) for d in deps] if isinstance(deps, list) else []


def cmd_promote(x: Exploration, a) -> None:
    """A look's script that proved useful becomes a method: copied under methods/<name>/, with the exploration's runs of it as its
    first known-answer cases, the agent's README, a test file the study tool can run, and where it came from. It is a change
    to the factory: `sf.py log-change` records it with a prediction, and `check_factory.py` validates it."""
    ev = x.events()
    start = x.started()
    if breached(ev):
        raise Refused("this exploration is spoiled (set-aside data reached it); nothing from it becomes a method")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,40}", str(a.name or "")):
        raise Refused("`--name` names the method: lower-case letters, digits and hyphens, such as gain-with-intercept")
    e = next((e for e in ev if e["kind"] == "look.run" and e["data"]["id"] == a.look), None)
    if e is None or e["data"]["exit_code"] != 0 or not e["data"].get("ran_in"):
        raise Refused(f"{a.look} is not a look of this exploration that ran in a scratch folder and passed; a method is promoted from one that did")
    receipt = json.loads((x.d / f"receipts/{e['data']['id']}.json").read_text())
    script = Path(os.path.normpath(x.d / receipt["script"]["word"]))
    if sf.sha_file(script) != e["data"]["script_sha"]:
        raise Refused(f"the script of {a.look} is not the script that was logged; nothing is promoted")
    methods = Path(os.path.abspath(a.methods))
    dest = methods / a.name
    if dest.exists():
        raise Refused(f"{dest} exists; a promoted method is a new folder, and a change to an existing method is a change of its own")
    try:
        readme = Path(a.readme).read_text()
    except (OSError, TypeError):
        raise Refused("`--readme` names the README you wrote: what it computes, on what inputs, and its known limits")
    missing = [part for part in README_PARTS if not re.search(re.escape(part) + r"\s+\S+(\s+\S+){3,}", readme)]
    if missing:
        raise Refused("the README says, each in a sentence or more: " + ", ".join(missing))
    runs = [r for r in ev if r["kind"] == "look.run" and r["data"]["script_sha"] == e["data"]["script_sha"] and r["data"]["exit_code"] == 0
            and r["data"].get("ran_in")]
    dest.mkdir(parents=True)
    try:
        shutil.copyfile(script, dest / script.name)
        cases = {}
        for r in runs:
            how, lid = r["data"]["ran_in"], r["data"]["id"]
            folder = dest / "known-answers" / lid
            (folder / "inputs").mkdir(parents=True)
            at_script = next(f["at"] for f in how["placed"] if f["role"] == "script")
            inputs = []
            for f in how["placed"]:
                if f["role"] == "script":
                    continue
                src = Path(os.path.normpath(x.d / f["from"]))
                if sf.sha_file(src) != f["sha256"]:
                    raise Refused(f"`{f['from']}` is not the file {lid} was given; nothing is promoted")
                (folder / "inputs" / f["at"]).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, folder / "inputs" / f["at"])
                inputs.append(f["at"])
            out = (x.d / f"receipts/{lid}.out.txt").read_text()
            if sf.sha_text(out) != r["data"]["output_sha"]:
                raise Refused(f"the output of {lid} is not what was logged; nothing is promoted")
            (folder / "expected.out.txt").write_text(out.split("\n", 1)[1] if out.startswith(f"[{WAY}: output of {lid}]\n") else out)
            words = how["argv_as_run"]
            (folder / "case.json").write_text(json.dumps({"look": lid, "why": r["data"]["why"], "args": words[words.index(at_script) + 1:],
                                                          "inputs": inputs, "from_exploration": start["data"]["id"]}, indent=1) + "\n")
            cases[lid] = {rel.relative_to(folder).as_posix(): sf.sha_file(rel) for rel in sorted(folder.rglob("*")) if rel.is_file()}
        test = (KNOWN_ANSWER_TESTS.replace("DEPENDENCIES", json.dumps(inline_dependencies(script))).replace("SCRIPT_NAME", repr(script.name))
                .replace("CASE_SHAS", json.dumps(cases, indent=1, sort_keys=True)).replace("NAME_JSON", json.dumps(a.name)).replace("NAME", a.name))
        (dest / "known_answer_tests.py").write_text(test)
        provenance = (f"\n\n## Where it came from\n\nPromoted by {a.by}" + (f" (model {x.model} as declared)" if x.model else "")
                      + f" from {start['data']['id']} ({WAY}), the script of {a.look} (sha256 {e['data']['script_sha']}). Its first known-answer "
                      f"cases are the {len(cases)} look(s) of that exploration that ran it: {', '.join(sorted(cases))}. They hold the exploration's "
                      "working data, never data it set aside. `known_answer_tests.py` runs them; a confirming study that uses this method runs "
                      "it as a rehearsal, and the study tool refuses its tests and its lock until that passes. A lead is not a finding, and "
                      "neither is a method: it is a tool that worked here.\n")
        (dest / "README.md").write_text(readme.rstrip() + provenance)
        method = {"promoted": True, "name": a.name, "script": {"file": script.name, "sha256": e["data"]["script_sha"]},
                  "tests": {"file": "known_answer_tests.py", "sha256": sf.sha_file(dest / "known_answer_tests.py")},
                  "readme": {"file": "README.md", "sha256": sf.sha_file(dest / "README.md")},
                  "from": {"exploration": start["data"]["id"], "look": a.look, "looks": sorted(cases), "log_fingerprint": f"{ev[-1]['seq']}:{ev[-1]['hash']}"},
                  "cases": cases, "by": a.by, "model": x.model, "at": sf.now(),
                  "change_log": "a promotion is a change to the factory: record it with `sf.py log-change`, naming methods/" + a.name + ", with a prediction"}
        (dest / "method.json").write_text(json.dumps(method, indent=1, sort_keys=True) + "\n")
    except BaseException:
        shutil.rmtree(dest, ignore_errors=True)
        raise
    x.add(a.by, "method.promoted", {"name": a.name, "folder": os.path.relpath(dest, x.d), "look": a.look, "cases": sorted(cases),
                                    "script_sha": e["data"]["script_sha"], "method_json_sha": sf.sha_file(dest / "method.json")})
    print(f"promoted {a.look} to the method {a.name} ({WAY}): {dest} with {len(cases)} known-answer case(s). This is a change to the factory: "
          f"record it with `sf.py log-change` naming methods/{a.name}, with a prediction, then run `check_factory.py`, which validates the method")


def cmd_fit(x: Exploration, a) -> None:
    """The coordinating agent's fit note at intake: how well the question suits agents, a verdict, and what it needs from a person."""
    ev = x.events()
    x.started()
    data = sf.record_fit(x, ev, a.by, a.file)
    x.add(a.by, "fit.noted", data)
    print(f"fit note recorded ({WAY}; advice, it blocks nothing): " + sf.fit_in_words(last(x.events(), "fit.noted"))[0])


def cmd_contribution(x: Exploration, a) -> None:
    """Write who did each step of this exploration, drawn from its log, as contribution.md and contribution.json: a paragraph
    a scientist can paste into a paper, and what the log cannot show."""
    ev = x.events()
    start = x.started()
    fresh = (start["data"]["set_aside"].get("fresh_data") or {})
    model = None
    with contextlib.suppress(OSError, ValueError, KeyError, TypeError, AttributeError, yaml.YAMLError):
        model = yaml.safe_load(Path(fresh["file"]).read_text())["proposed"]["model"]
    extra = [{"kind": "fresh-data.proposed", "actor": fresh["proposed_by"], "model": model, "data": {}}] if fresh.get("proposed_by") else []
    c = sf.contribution([(f"the exploration {start['data']['id']}", ev)], sf.roles_of(sf.FACTORY), extra)
    lines = sf.contribution_lines(c, f"{start['data']['id']} ({WAY}; a lead, not a finding)")
    (x.d / "contribution.md").write_text("\n".join(lines))
    write_json(x.d / "contribution.json", c)
    print("\n".join(lines))


def cmd_fingerprint(x: Exploration, a) -> None:
    ev = x.events()
    if not ev:
        raise Refused("the exploration is not started")
    print(f"{ev[-1]['seq']}:{ev[-1]['hash']}")


# ---- the self-test --------------------------------------------------------
class A:
    def __init__(self, **kw):
        defaults = dict(by="agent:tester-analysis", how="a later period", set_aside_window="2025-04-28:", working_window="2024-01-01:2024-12-31",
                        set_aside_sites=None, set_aside_release=None, release_cut_off=None, set_aside_path=None, nothing_set_aside=None, time_keys=None,
                        subject="reach_id=R1,gauge=G1", working="calendar 2024", why="the next period, never read", studies=None,
                        asked_by=None, question="How well does A follow B?", id="EXPLORATION-T", request=None, anchor=None,
                        why_look=None, look=None, alternative=None, evidence=None, file=None, summary=None, comment=None, ref=None,
                        bundle=[], drafts=[], tag=[], takes=None, boundary_from=None, depth=None, old=None, new=None,
                        also_reads=None, variant=None, reviewer=None, working_data=None, read_lead=None, fresh_data=None, answer=None, direction=None,
                        reason=None, expertise=None, local_practice=None, record_comment=None, report_only=None)
        self.__dict__.update(defaults)
        self.__dict__.update(kw)


def _refusal(fn, *args) -> str:
    try:
        fn(*args)
    except Refused as r:
        return str(r) or "refused"
    return ""


def selftest() -> int:
    import io
    results = []
    sf.Study.default_model = "selftest-model"  # every agent event of this self-test is written under this name, except where a check says otherwise

    def ok(name: str, cond) -> None:
        results.append((name, bool(cond)))

    def quiet(fn, *args):
        with contextlib.redirect_stdout(io.StringIO()):
            return fn(*args)

    def said(fn, *args) -> str:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
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
            "status: stable\n---\n\n# A and B\n\nScore changes, not levels. The two sit 0.44 km apart.\n")
        page = bundle / "gotchas" / "follow-datum.md"

        def known(x_: Exploration) -> None:
            quiet(cmd_known, x_, A(bundle=[str(bundle)], question=None))
            quiet(cmd_read, x_, A(concept=str(page), takes="score changes, not levels"))

        data = tmp / "a_b_2024.json"
        data.write_text(json.dumps({"window": {"start": "2024-01-01", "end": "2024-12-31"}, "retrieved": "2026-09-08T00:00:00Z",
                                    "rows": [{"time": f"2024-{m:02d}-15T00:00:00Z", "a": m * 1.0, "b": m * 1.1} for m in range(1, 13)]}))
        later = tmp / "a_b_later.json"
        later.write_text(json.dumps({"rows": [{"time": "2025-06-01T00:00:00Z", "a": 1.0, "b": 1.0}]}))
        declared = tmp / "a_b_declared.json"
        declared.write_text(json.dumps({"window": {"start": "2025-01-01", "end": "2025-12-31"}, "rows": []}))

        def fresh(name: str, reviewer: str | None = "agent:tester-review", **kw) -> Exploration:
            x = Exploration(work / "explorations" / name)
            kw.setdefault("working_data", [str(data)])  # the one file of working data these explorations declare
            quiet(cmd_start, x, A(request=str(req), id=name, **kw))
            if reviewer:  # the coordinating step names the reviewer before any lead exists
                quiet(cmd_reviewer, x, A(by="agent:tester-coordinating", reviewer=reviewer))
            return x

        PERSON = "human:throwaway-placeholder"  # nobody: the only person's name these self-tests type, in a scratch folder

        def so_what(x_: Exploration, answer: str = "worth-confirming", **kw) -> str:
            """A person's so what, typed (practice), on the lead as it stands."""
            return said(cmd_so_what, x_, A(**{"by": PERSON, "answer": answer, "read_lead": sf.sha_file(x_.d / "lead.json"), "local_practice": True, **kw}))

        def RA(x_: Exploration, **kw) -> A:
            """The arguments of a review, with the lead the reviewer read: the one on file, unless a check says otherwise."""
            return A(**{"read_lead": sf.sha_file(x_.d / "lead.json"), **kw})

        def script(x: Exploration, name: str, body: str) -> str:
            (x.d / "looks" / name).write_text(body)
            return f"looks/{name}"

        def look(x: Exploration, words: list, why: str = "to see how A follows B", by: str = "agent:tester-analysis"):
            return said(cmd_look, x, A(argv=["--", *words], why=why, by=by))

        # ---- the model that wrote each event ----------------------------------------------------------
        sf.Study.default_model = None
        (tmp / "work-models" / "explorations").mkdir(parents=True)
        try:
            xm = Exploration(tmp / "work-models" / "explorations" / "E-MODEL")
            ok("an agent that names no model cannot start an exploration: no event is written (the command line refuses before anything is)",
               "names the model that wrote it" in said(cmd_start, xm, A(request=str(req), id="E-MODEL")) and xm.events() == [])
            shutil.rmtree(xm.d, ignore_errors=True)
            shutil.rmtree(tmp / "work-models" / "studies", ignore_errors=True)
            xm.model = "claude-sonnet-5-5"
            quiet(cmd_start, xm, A(request=str(req), id="E-MODEL"))
            ok("an agent's event in the exploration log records the model its caller declared, and status shows it",
               xm.events()[0]["model"] == "claude-sonnet-5-5" and stage_of(xm)["models_recorded"]["by_actor"] == {xm.events()[0]["actor"]: ["claude-sonnet-5-5"]})
            xm.model = None
            ok("a later event by an agent with no model is refused", "names the model that wrote it" in said(
                cmd_note, xm, A(by="agent:tester-analysis", kind="missing", about="a", text="b", evidence=None)))
            for left in (xm.d / "notes").glob("NOTE-*"):  # the command line refuses before a note file is written; called directly, the file is left
                left.unlink()
            quiet(cmd_note, xm, A(by="human:tester", kind="missing", about="a", text="a person's note", evidence=None))
            ok("a person exploring needs no model, and the event carries none", "model" not in xm.events()[-1] and check_log(xm) == [])
            ev_ = xm.events()
            body_ = {"seq": len(ev_), "at": sf.now(), "actor": "agent:quiet", "kind": "remark.added", "data": {"way": WAY, "text": "by hand"}}
            with xm.log.open("a") as f_:
                f_.write(json.dumps({**body_, "prev": ev_[-1]["hash"], "hash": sf.Study._digest(ev_[-1]["hash"], body_)}, sort_keys=True) + "\n")
            ok("an agent event with no model, added by hand with the right hash, fails the log check", any("names no model" in q for q in check_log(xm)))
        finally:
            sf.Study.default_model = "selftest-model"
        cli = subprocess.run([sys.executable, str(HERE / "explore.py"), "note", "--exploration", str(work / "explorations" / "E-CLI"), "--by", "agent:x",
                              "--kind", "missing", "--about", "a", "--text", "b"], capture_output=True, text=True)
        ok("on the command line an agent with no --model is refused before anything is written",
           cli.returncode == 2 and "names the model that wrote it" in cli.stderr and not (work / "explorations" / "E-CLI").exists())

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
        # ---- the fresh data proposed from metadata (tools/fresh_data.py) and set aside at the start --------
        fdt = fresh_tool()
        fwork = tmp / "work-fresh"  # a record of its own, so these starts touch nothing the checks below read
        (fwork / "explorations").mkdir(parents=True)
        meta = tmp / "fd-metadata.json"
        meta.write_text(json.dumps({"subject": {"reach_id": "R9", "gauge": "G9"}, "items": [
            {"id": f"USGS-0{n}-{y}", "site": f"USGS-0{n}", "start": f"{y}-01-01", "end": f"{y}-12-31", "count": 10}
            for n in range(1000001, 1000011) for y in (2025, 2026)]}))

        def proposal(name: str, **k) -> Path:
            out = tmp / "proposals" / f"{name}.yaml"
            quiet(fdt.cmd_propose, fdt.A(metadata=str(meta), what="w", why="y", unfair="u", studies=str(fwork / "studies"), out=str(out), **k))
            return out
        xr = Exploration(fwork / "explorations" / "E-RANDOM")
        ok("a random set aside cannot be typed: without the tool's proposal (`--fresh-data`) the start is refused",
           "never chosen by anybody" in said(cmd_start, xr, A(request=str(req), how="a random set aside", set_aside_window=None,
                                                              set_aside_sites="USGS-01000001", subject="reach_id=R9,gauge=G9"))
           and not xr.log.exists())
        rp = proposal("random", kind="random", fraction=0.3)
        drawn = fdt.load(rp)["members"]
        others = [m for m in fdt.load(rp)["draw"]["drawn_from"] if m not in drawn]
        ok("a random set aside with one site swapped for a site of one's own choosing is refused: nobody adds a site or takes one out",
           "nobody adds a site" in said(cmd_start, xr, A(request=str(req), how="a random set aside", set_aside_window=None, subject="reach_id=R9,gauge=G9",
                                                          set_aside_sites=",".join(drawn[1:] + others[:1]), fresh_data=str(rp)))
           and not xr.log.exists())
        quiet(cmd_start, xr, A(request=str(req), how="a random set aside", set_aside_window=None, subject="reach_id=R9,gauge=G9", working_window=None,
                               set_aside_sites=",".join(drawn), fresh_data=str(rp), working_data=[str(data)]))
        got_sa = xr.set_aside()
        ok("with the proposal and exactly its members the random set aside starts, and the start records the proposal by checksum",
           got_sa["how"] == "a random set aside" and sorted(got_sa["sites"]) == drawn and got_sa["fresh_data"]["sha256"] == sf.sha_file(rp)
           and got_sa["fresh_data"]["seed_sha256"] == fdt.load(rp)["draw"]["seed_sha256"])
        lp = proposal("later", kind="later-period", from_="2026-01-01")
        xl = Exploration(fwork / "explorations" / "E-LATER")
        ok("a proposal is set aside as it was proposed: a later period with another window than the proposal's is refused",
           "not the later period the proposal names" in said(cmd_start, xl, A(request=str(req), subject="reach_id=R9,gauge=G9", fresh_data=str(lp),
                                                                              set_aside_window="2025-06-01:", working_window=None)))
        ok("and so is a proposal of another kind than the way the start holds data out",
           "is set aside as" in said(cmd_start, xl, A(request=str(req), subject="reach_id=R9,gauge=G9", fresh_data=str(rp),
                                                      set_aside_window="2026-01-01:", working_window=None)))
        lp2 = tmp / "proposals" / "later-edited.yaml"
        lp2.write_text(lp.read_text().replace("what: w", "what: a wider window, edited by hand"))
        ok("a proposal edited after the tool wrote it is refused at the start: it is not on the record beside the studies",
           "not on the record" in said(cmd_start, xl, A(request=str(req), subject="reach_id=R9,gauge=G9", fresh_data=str(lp2),
                                                        set_aside_window="2026-01-01:", working_window=None)))
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
        odd = tmp / "odd_keys.json"
        odd.write_text(json.dumps({"retrieved": "2026-09-08", "rows": [{"when": "2025-06-01T00:00:00Z", "a": 1.0}]}))
        ok("a data file that keeps its times under a key nobody declared is still refused when they sit in its rows",
           "inside the set-aside window" in look(x, ["{python}", s1, str(odd)]))
        link = x.d / "looks" / "innocent.json"
        link.symlink_to(later)
        ok("a link with an innocent name that points at set-aside data is refused", "set aside" in look(x, ["{python}", s1, "looks/innocent.json"]))
        link.unlink()
        ok("a look cannot run the study tool, this tool or the knowledge tool",
           "not a look" in look(x, ["{python}", str(HERE / "sf.py"), "lock", "--study", "s", "--by", "human:someone"])
           and "not a look" in look(x, ["uv", "run", str(HERE / "explore.py"), "review", "--exploration", str(x.d), "--by", "agent:other", "--verdict", "no-holes-found", "--file", "x"]))
        ok("another exploration of the same subject cannot explore what this one set aside",
           "another does not explore" in said(cmd_start, Exploration(work / "explorations" / "E-REACH"),
                                              A(request=str(req), set_aside_window="2027-01-01:2027-12-31", working_window="2025-05-01:2025-12-31")))
        xo = fresh("E-OTHER", set_aside_window="2027-01-01:2027-12-31", working_window="2023-01-01:2023-12-31")
        known(xo)
        so = script(xo, "p.py", "print('ok')\n")
        ok("an exploration is also fenced from what another exploration set aside for the same subject",
           xo.set_aside()["also_set_aside"] and "set aside" in look(xo, ["{python}", so, str(later)]))
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
        known(xs)
        ss = script(xs, "p.py", "print('ok')\n")
        site_file = tmp / "sites.json"
        site_file.write_text(json.dumps({"gauge": "g7", "rows": []}))
        ok("a look that names a set-aside site is refused", "set aside" in look(xs, ["{python}", ss, "--gauge", "G7"]))
        ok("a look on a data file that holds a set-aside site is refused", "set aside" in look(xs, ["{python}", ss, str(site_file)]))
        ok("a new release set aside without a cut-off is refused: a release that arrives as rows of the same file carries no mark",
           "--release-cut-off" in said(cmd_start, Exploration(work / "explorations" / "E-REL-0"), A(
               request=str(req), id="E-REL-0", how="a new release", set_aside_window=None, set_aside_release=["PRODUCT_v3"], working_window=None,
               subject="reach_id=R3,gauge=G3", working_data=[str(data)])) and not (work / "explorations" / "E-REL-0").exists())
        xr = fresh("E-REL", how="a new release", set_aside_window=None, set_aside_release=["PRODUCT_v3"], working_window=None,
                   subject="reach_id=R3,gauge=G3", release_cut_off="2024-12-31")
        known(xr)
        sr = script(xr, "p.py", "print('ok')\n")
        ok("a look that names a set-aside release is refused", "set aside" in look(xr, ["{python}", sr, "--collection", "product_V3"]))
        ok("a look that names another release runs", look(xr, ["{python}", sr, "--collection", "PRODUCT_v2"]) == "")
        # the release binds the data as it stands (found by the first real run: the next monthly update would have come in as
        # plain dated rows of the same file, and any look could have read them)
        ok("a month written as a year and a month is read against the cut-off, and a range of years is not a month",
           past_cut_off("A,2024-12,1.0\nA,2025-01,1.1\n1970-2010 2025-02-03", "2024-12-31") == ["2025-01", "2025-02-03"]
           and past_cut_off("A,2024-12,1.0 in 1970-2010", "2024-12-31") == [])
        monthly = tmp / "monthly"
        monthly.mkdir()
        rows = "Source,Year,Mean\n" + "".join(f"A,2024-{m:02d},{m / 10}\n" for m in range(1, 13))
        (monthly / "monthly.csv").write_text(rows)
        rel = dict(how="a new release", set_aside_window=None, set_aside_release=["next-update"], working_window=None, subject="reach_id=R70,gauge=G70")
        ok("a release whose cut-off is before what the working data holds is refused at the start: the data already goes past it",
           "already holds dates past the cut-off" in said(cmd_start, Exploration(work / "explorations" / "E-CUT-0"), A(
               request=str(req), id="E-CUT-0", working_data=[str(monthly)], release_cut_off="2024-06-30", **rel)))
        ok("and so is a working window that runs past the cut-off",
           "past the cut-off" in said(cmd_start, Exploration(work / "explorations" / "E-CUT-0"), A(
               request=str(req), id="E-CUT-0", working_data=[str(monthly)], release_cut_off="2024-12-31", **{**rel, "working_window": "2024-01-01:2025-06-30"})))
        xc = fresh("E-CUT", working_data=[str(monthly)], release_cut_off="2024-12-31", **rel)
        known(xc)
        sc = script(xc, "tail.py", "import sys\nprint(open(sys.argv[1]).read().splitlines()[-1])\n")
        ok("the start binds every working file by checksum and records the cut-off",
           xc.set_aside()["cut_off"] == "2024-12-31" and [b["sha256"] for b in xc.set_aside()["bound"]] == [sf.sha_file(monthly / "monthly.csv")])
        ok("a look over the working data as it stood runs", look(xc, ["{python}", sc, str(monthly / "monthly.csv")]) == "")
        (monthly / "monthly.csv").write_text(rows + "A,2025-01,9.9\nA,2025-02,9.8\n")  # the source publishes; the file is refreshed in place
        before = len(xc.events())
        got = look(xc, ["{python}", sc, str(monthly / "monthly.csv")])
        ok("a look over a working file refreshed with months past the cut-off is refused, and the refusal is logged, not a breach",
           "has changed since the exploration started" in got and "2025-01" in got and len(xc.events()) == before + 1
           and xc.events()[-1]["kind"] == "look.refused" and not breached(xc.events()))
        ok("a recheck over the refreshed file runs nothing", "nothing is run" in said(cmd_recheck, xc, A(look="LOOK-001")))
        (xc.d / "looks" / "copy.csv").write_text((monthly / "monthly.csv").read_text())
        ok("a copy of the refreshed file put in the exploration is refused too: it holds months past the cut-off",
           "holds a date past the cut-off" in look(xc, ["{python}", sc, "looks/copy.csv"]))
        (monthly / "monthly.csv").write_text(rows)
        (monthly / "extra.csv").write_text("Source,Year,Mean\nA,2024-12,1.0\n")
        ok("a file that was not in the working data at the start is refused, whatever its dates",
           "was not in the working data when the exploration started" in look(xc, ["{python}", sc, str(monthly / "extra.csv")]))
        (monthly / "extra.csv").unlink()
        ok("another exploration of the same subject cannot explore past the cut-off of the release set aside",
           "another does not explore" in said(cmd_start, Exploration(work / "explorations" / "E-CUT-2"), A(
               request=str(req), id="E-CUT-2", **{**rel, "set_aside_release": ["a-later-update"], "working_window": "2024-01-01:2025-06-30"},
               release_cut_off="2025-06-30", working_data=[str(monthly)])))
        rmeta = tmp / "fd-release.json"
        rmeta.write_text(json.dumps({"subject": {"reach_id": "R71", "gauge": "G71"}, "files": [{"name": "monthly.csv", "sha256": sf.sha_file(monthly / "monthly.csv")}],
                                     "items": [{"id": "A-2024", "series": "A", "start": "2024-01-01", "end": "2024-12-31", "count": 12}],
                                     "releases": [{"name": "next-update", "cadence": "monthly"}]}))
        rp_ = tmp / "proposals" / "release.yaml"
        quiet(fdt.cmd_propose, fdt.A(metadata=str(rmeta), kind="next-release", release="next-update", what="w", why="y", unfair="u",
                                     studies=str(fwork / "studies"), out=str(rp_)))
        rstart = dict(request=str(req), how="a new release", set_aside_window=None, set_aside_release=["next-update"], working_window=None,
                      subject="reach_id=R71,gauge=G71", fresh_data=str(rp_), studies=str(fwork / "studies"))
        ok("a proposal of the next release fixes the cut-off from the metadata, and a start with another cut-off is refused",
           fdt.load(rp_)["rule"]["cut_off"] == "2024-12-31" and "is not the one the proposal fixed" in said(
               cmd_start, Exploration(fwork / "explorations" / "E-RP-0"), A(id="E-RP-0", working_data=[str(monthly)], release_cut_off="2024-11-30", **rstart)))
        other = tmp / "other-monthly"
        other.mkdir()
        (other / "monthly.csv").write_text(rows.replace("A,2024-03,0.3", "A,2024-03,0.4"))
        ok("a start whose working file is not the file the metadata described, by checksum, is refused",
           "not the file the metadata describes" in said(cmd_start, Exploration(fwork / "explorations" / "E-RP-0"), A(id="E-RP-0", working_data=[str(other)], **rstart)))
        xrp = Exploration(fwork / "explorations" / "E-RP")
        quiet(cmd_start, xrp, A(id="E-RP", working_data=[str(monthly)], **rstart))
        ok("with the proposal, the start takes the cut-off it fixed and binds the file the metadata described",
           xrp.set_aside()["cut_off"] == "2024-12-31" and xrp.set_aside()["bound"][0]["sha256"] == sf.sha_file(monthly / "monthly.csv"))
        # a site is written many ways: the fence reads the ways people type it (found by the hydrologist's review)
        xu = fresh("E-USGS", how="sites never opened", set_aside_window=None, set_aside_sites="USGS-06935965,USGS-06909000", working_window=None,
                   subject="reach_id=R9,gauge=USGS-07374000")
        known(xu)
        su = script(xu, "p.py", "print('ok')\n")
        ok("a look that names a set-aside site with its agency in front is refused", "set aside" in look(xu, ["{python}", su, "--gauge", "usgs-06935965"]))
        ok("a look that names a set-aside site by its bare number, the way a fetch script takes it, is refused",
           "set aside" in look(xu, ["{python}", su, "--gauge", "06935965"]))
        ok("a look that names it with the leading zero dropped is refused", "set aside" in look(xu, ["{python}", su, "--gauge=6935965"]))
        sn = script(xu, "fetch_site.py", "SITE = '06909000'\nprint('would fetch', SITE)\n")
        ok("a look whose script names a set-aside site by its bare number is refused", "set aside" in look(xu, ["{python}", sn]))
        bare_file = tmp / "bare_site.json"
        bare_file.write_text(json.dumps({"site_no": "06935965", "rows": []}))
        ok("a data file that holds a set-aside site as a bare number is refused", "set aside" in look(xu, ["{python}", su, str(bare_file)]))
        bare_file.write_text(json.dumps({"site_no": 6935965, "rows": []}))
        ok("a data file that holds it as a number, zeros lost, is refused", "set aside" in look(xu, ["{python}", su, str(bare_file)]))
        ok("a longer number that only contains a set-aside site number is not that site, and the working site runs",
           look(xu, ["{python}", su, "--gauge", "07374000", "--n", "106935965"]) == "")
        ok("a study's plan may name a set-aside site by its bare number", names_token('{"gauge": "06935965"}', "USGS-06935965", xu.set_aside())
           and not names_token('{"gauge": "07374000"}', "USGS-06935965", xu.set_aside()))
        xn = fresh("E-NOTHING", nothing_set_aside="one record and all of it has been seen", set_aside_window=None, working_window=None,
                   subject="reach_id=R4,gauge=G4")
        ok("an exploration with nothing set aside says so and writes no set-aside line",
           xn.set_aside()["how"] == "nothing" and not any(ln.get("exploration") == "E-NOTHING" and ln.get("kind") == "set-aside" for ln in record_lines(record)))

        # ---- choices, notes, the lead ----------------------------------------------------------------
        y = fresh("E-2", subject="reach_id=R5,gauge=G5")
        known(y)
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
        lead = {"summary": {"looks_true": "The second record seems to track the first in twelve months.", "how_strong": "One look on one year of working data.",
                            "cannot_settle": "Whether it holds in another year or at another site."}, "what_looks_true": "A follows B closely over the year, on changes.", "how_it_was_found": "By pairing the two records and scoring changes.",
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
        lead["what_looks_true"] = "A follows B closely over the year, with a gain of 1.0123 on changes."
        lf.write_text(yaml.safe_dump(lead))
        ok("a lead that quotes a number no cited look printed is refused", "1.0123" in said(cmd_lead, y, A(file=str(lf))))
        lead["what_looks_true"] = "A follows B closely over the year, on changes, across 12 rows."
        lf.write_text(yaml.safe_dump(lead))
        ok("ending as a lead before a lead is recorded is refused", "no lead" in said(cmd_end, y, A(outcome="lead", summary="x")))
        ok("a review before there is anything to review is refused", "nothing to review" in said(cmd_review, y, RA(y, by="agent:tester-review", verdict="holes-found", file=str(req))))
        quiet(cmd_lead, y, A(file=str(lf)))
        got = json.loads((y.d / "lead.json").read_text())
        ok("the lead counts what was tried from the log, not from the lead file",
           got["tried"] == {"looks": 2, "failed": 1, "refused": 1, "ids": ["LOOK-001", "LOOK-002"], "comparisons_declared": 0})
        ok("the lead says it is exploring and is not a finding", got["way"] == WAY and "not a finding" in got["status"]
           and "not a finding" in (y.d / "lead.md").read_text() and "cannot be signed" in (y.d / "lead.md").read_text())
        ok("the lead carries the knowledge that was read and what was set aside", got["set_aside"]["window"]["start"] == "2025-04-28" and len(got["knowledge_read"]) == 1)
        ok("there is no command that signs, locks or attaches a finding",
           not {"signature", "sign", "lock", "attach", "open-held-out"} & set(build_parser()._subparsers._group_actions[0].choices))

        # ---- review, end, hand-over ------------------------------------------------------------------
        ok("the hand-over is refused before the exploration has ended as a lead",
           "has not ended as a lead" in said(cmd_hand_over, y, A(by="agent:tester-coordinating", study_id="STUDY-T")))
        vf = tmp / "verdict.md"
        vf.write_text("# Review (exploring)\n\nHoles: the gain rests on one year.\n")
        ok("the agent that explored cannot review its own lead", "did part of this exploration" in said(cmd_review, y, RA(y, verdict="holes-found", file=str(vf))))
        ok("the same agent under another case of its name cannot either",
           "did part of this exploration" in said(cmd_review, y, RA(y, by="agent:TESTER-analysis", verdict="holes-found", file=str(vf))))
        ok("a verdict outside the two is refused", "one of" in said(cmd_review, y, RA(y, by="agent:tester-review", verdict="approve", file=str(vf))))
        quiet(cmd_review, y, RA(y, by="agent:tester-review", verdict="holes-found", file=str(vf)))
        ok("status after a review asks a person for the so what", stage_of(y)["stage"] == "so-what" and stage_of(y)["who"] == "people")
        quiet(cmd_lead, y, A(file=str(lf)))
        ok("a revised lead is a new version, and the first is kept", (y.d / "leads/lead-v1.json").is_file() and json.loads((y.d / "lead.json").read_text())["version"] == 2)
        ok("ending as a lead is refused until the latest lead has been reviewed",
           "has not been reviewed" in said(cmd_end, y, A(outcome="lead", summary="A follows B on changes; worth a test")))
        ok("status names the review agent when the latest lead is not reviewed", stage_of(y)["who"] == "review agent")
        ok("a note is not resolved while the lead can still be revised: the curating agent waits for the end",
           "has not ended" in said(cmd_resolve, y, A(by="agent:tester-curating", note="NOTE-001", disposition="drafted", ref="knowledge-queue/gotchas/a-flag.md")))
        quiet(cmd_review, y, RA(y, by="agent:tester-review", verdict="no-holes-found", file=str(vf)))
        ok("ending as a lead is refused until a person has said the reviewed lead is worth confirming",
           "worth confirming" in said(cmd_end, y, A(outcome="lead", summary="A follows B on changes; worth a test")))
        so_what(y)
        quiet(cmd_end, y, A(outcome="lead", summary="A follows B on changes; worth a test"))
        ok("after the end nothing more is looked at", "has ended" in look(y, ["{python}", sy, str(data)]))
        ok("the agent that explored cannot make the hand-over", "did the exploring" in said(cmd_hand_over, y, A(study_id="STUDY-T")))
        ok("the hand-over refuses the exploration's own name for the study", "study-id" in said(cmd_hand_over, y, A(by="agent:tester-coordinating", study_id="E-2")))
        ok("a hand-over on a so what that was typed (practice) is refused unless it says practice too",
           "--local-practice" in said(cmd_hand_over, y, A(by="agent:tester-coordinating", study_id="STUDY-T")))
        quiet(cmd_hand_over, y, A(by="agent:tester-coordinating", study_id="STUDY-T", local_practice=True))
        ho = json.loads((y.d / "hand-over/hand-over.json").read_text())
        ok("the hand-over holds what `sf.py start` needs: an id, a question, a request by checksum",
           ho["study_id"] == "STUDY-T" and ho["question"].endswith("?") and ho["request"]["sha256"] == sf.sha_file(y.d / "hand-over/request.md"))
        ok("the handed-over request says where it came from and that the lead is not a finding",
           "exploring, not a finding" in (y.d / "hand-over/request.md").read_text())
        ok("the handed-over request names who reviewed and who explored, and says names are typed",
           "agent:tester-review" in (y.d / "hand-over/request.md").read_text() and "agent:tester-analysis" in (y.d / "hand-over/request.md").read_text()
           and "typed, not proven" in (y.d / "hand-over/request.md").read_text())
        ok("nothing is handed over from an exploration that set nothing aside",
           "nothing was set aside" in said(cmd_hand_over, xn, A(by="agent:tester-coordinating", study_id="STUDY-N")))

        # ---- the confirming study keeps the fence ----------------------------------------------------
        study = sf.Study(work / "studies" / "STUDY-T")
        quiet(sf.cmd_start, study, argparse.Namespace(id="STUDY-T", question=ho["question"], by="agent:tester-coordinating",
                                                      request=str(y.d / "hand-over/request.md"), asked_by=None))
        ok("the study tool starts a study from the hand-over", study.events()[0]["data"]["request"]["sha"] == ho["request"]["sha256"])
        whole = sf.study_contribution(study, sf.FACTORY)
        ok("a study started from a hand-over knows the exploration it came from, and its contribution statement reads both logs",
           study.events()[0]["data"]["from_exploration"]["id"] == y.started()["data"]["id"] and len(whole["logs"]) == 2
           and any(w["actor"].startswith("agent:tester-analysis") for r in whole["rows"] if r["work"] == "exploring" for w in r["who"]))
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

        # ---- a release set aside, carried into the confirming study (the first real run's shape, made-up numbers) ----------
        monthly_ho = tmp / "monthly-ho"
        monthly_ho.mkdir()
        (monthly_ho / "monthly.csv").write_text(rows)
        xh = fresh("E-REL-HO", how="a new release", set_aside_window=None, set_aside_release=["next-update"], working_window=None,
                   subject="reach_id=R72,gauge=G72", working_data=[str(monthly_ho)], release_cut_off="2024-12-31")
        known(xh)
        look(xh, ["{python}", script(xh, "tail.py", "import sys\nprint(open(sys.argv[1]).read().splitlines()[-1])\n"), str(monthly_ho / "monthly.csv")])
        hlead = {**lead, "evidence": ["LOOK-001"], "choices_that_would_change_it": [], "choices_that_would_not": [],
                 "what_looks_true": "The series rises through the year."}
        (xh.d / "lead.yaml").write_text(yaml.safe_dump(hlead))
        quiet(cmd_lead, xh, A(file=str(xh.d / "lead.yaml")))
        quiet(cmd_review, xh, RA(xh, by="agent:tester-review", verdict="no-holes-found", file=str(vf)))
        so_what(xh)
        quiet(cmd_end, xh, A(outcome="lead", summary="the series rises; worth a test on the next update"))
        quiet(cmd_hand_over, xh, A(by="agent:tester-coordinating", study_id="STUDY-REL", local_practice=True))
        hreq = xh.d / "hand-over" / "request.md"
        ok("the hand-over of a release says its cut-off, and that the study takes it from the exploration's start",
           "after the cut-off 2024-12-31; the study takes the cut-off" in hreq.read_text())

        def study_from(name: str, request: Path, **kw):
            s_ = sf.Study(work / "studies" / name)
            quiet(sf.cmd_start, s_, argparse.Namespace(id=name, question=hlead["proposed_plan"]["question"], by="agent:tester-coordinating",
                                                       request=str(request), asked_by=None, **kw))
            return s_

        srel = study_from("STUDY-REL", hreq)
        rel = srel.events()[0]["data"].get("release") or {}
        ok("a study started from the hand-over of a release takes the cut-off and the working file's checksum from the exploration's "
           "start, and says them in the words the lock uses", rel.get("cut_off") == "2024-12-31" and rel.get("exploration") is True
           and [w["sha256"] for w in rel.get("working") or []] == [sf.sha_file(monthly_ho / "monthly.csv")]
           and f"fresh data is the release after 2024-12-31; the data seen while exploring was monthly.csv with checksum "
               f"{sf.sha_file(monthly_ho / 'monthly.csv')}" in sf.release_in_words(rel)
           and not any("did not start with that cut-off" in q for q in study_problems(xh, srel.d)))
        ok("a cut-off or working data an agent gives at the start of a study from a hand-over is refused: they come from the exploration",
           "not given with a hand-over" in _refusal(lambda: study_from("STUDY-REL-1", hreq, fresh_data=str(rp_), working_data=None))
           and not (work / "studies" / "STUDY-REL-1").exists())
        (monthly_ho / "monthly.csv").write_text(rows + "A,2025-01,9.9\n")
        ok("a study from the hand-over of a release whose working file has changed since the exploration started is refused at its start",
           "has changed since the exploration started" in _refusal(lambda: study_from("STUDY-REL-2", hreq)))
        (monthly_ho / "monthly.csv").write_text(rows)
        (tmp / "copied").mkdir()
        shutil.copyfile(hreq, tmp / "copied" / "request.md")
        ok("check-study refuses a study started from a copy of the request, which brought no cut-off",
           any("did not start with that cut-off" in q for q in study_problems(xh, study_from("STUDY-REL-C", tmp / "copied" / "request.md").d)))

        # ---- notes for curating, status, the log ------------------------------------------------------
        quiet(cmd_curation_list, y, A())
        cl = json.loads((y.d / "curation-list.json").read_text())
        ok("the curation list holds the open notes and says a lead is never drafted as a finding",
           cl["open_notes"] == 1 and "never drafted as a finding" in cl["contract"] and cl["way"] == WAY)
        ok("status after the hand-over sends the notes to the curating agent", stage_of(y)["stage"] == "learn" and stage_of(y)["who"] == "curating agent")
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
        # ---- what real agents and a hydrologist found: order, numbers, words, figures, corrections ----
        data_page = tmp / "not-a-page.json"
        data_page.write_text("{}")
        w0 = Exploration(work / "explorations" / "E-5")
        ok("before data is set aside only knowledge is read: a data file given as the source of the boundary is refused",
           "not a knowledge page" in said(cmd_start, w0, A(request=str(req), id="E-5", subject="reach_id=R8,gauge=G8", boundary_from=[str(data_page)])))
        w = fresh("E-5", subject="reach_id=R8,gauge=G8", boundary_from=[str(page)])
        ok("the page the boundary was read from is recorded at the start, by checksum",
           w.set_aside()["boundary_read_from"][0]["sha256"] == sf.sha_file(page))
        ok("data that is neither explored nor set aside is named at the start",
           w.set_aside()["in_neither"] == {"start": "2025-01-01", "end": "2025-04-27"})
        ok("the start makes a place for the review agent to write and a place for figures", (w.d / "review").is_dir() and (w.d / "figures").is_dir())
        quiet(cmd_known, w, A(bundle=[str(bundle)], question=None))
        sw = script(w, "fit.py", "import sys\nfrom pathlib import Path\nprint('gain 1.4826 on 12 rows')\nprint('comparisons: 9')\n"
                                 "print('warning: a launcher grumbles', file=sys.stderr)\n"
                                 "Path('figures').mkdir(exist_ok=True)\nPath('figures/scatter.svg').write_text('<svg xmlns=\"http://www.w3.org/2000/svg\"/>')\n"
                                 "Path('figures/photo.png').write_bytes(bytes([137, 80, 78, 71, 13, 10, 26, 10, 255, 254, 0, 1]))\n")
        ok("listing is not reading: the first look is refused until a page is recorded as read",
           "none is recorded as read" in look(w, ["{python}", sw]))
        listed_as = last(w.events(), "knowledge.listed")["data"]["concepts"][0]["path"]
        ok("`read` refuses a page that does not exist", "does not exist" in said(cmd_read, w, A(concept="gotchas/no-such-page.md", takes="x")))
        ok("`read` takes a page by the path `known` printed for it",
           said(cmd_read, w, A(concept=listed_as, takes="score changes, not levels")) == "" and last(w.events(), "knowledge.read")["data"]["sha256"] == sf.sha_file(page))
        ok("`read` takes a page by its path below the wiki, and records that it was only skimmed",
           said(cmd_read, w, A(concept="gotchas/follow-datum.md", takes="nothing more", depth="skimmed")) == "" and last(w.events(), "knowledge.read")["data"]["depth"] == "skimmed")
        ok("`read` refuses a depth that is neither whole nor skimmed", "whole" in said(cmd_read, w, A(concept=listed_as, takes="x", depth="glanced")))
        unlisted = bundle / "gotchas" / "units.md"
        unlisted.write_text("---\ntype: dataset-gotcha\ntitle: \"Units of the toy record\"\nstatus: draft\n---\n\n# Units\n\nMetres.\n")
        ok("`read` takes a page the search did not list, and records that it was not listed (found by the first real run)",
           said(cmd_read, w, A(concept=str(unlisted), takes="the units")) == "" and last(w.events(), "knowledge.read")["data"]["listed"] is False
           and [e["data"]["listed"] for e in w.events() if e["kind"] == "knowledge.read"][0] is True)
        quiet(cmd_choice, w, A(choice="fit a line with an intercept", alternative=["through the origin"], rests_on="the page read"))
        ok("a look runs once a page is recorded as read", look(w, ["{python}", sw]) == "")
        e = last(w.events(), "look.run")
        out_text = (w.d / "receipts/LOOK-001.out.txt").read_text()
        ok("what a look writes to standard error is kept beside its output, not inside it",
           "grumbles" not in out_text and "gain 1.4826" in out_text and "grumbles" in (w.d / "receipts/LOOK-001.err.txt").read_text()
           and e["data"]["streams"] == "separate" and e["data"]["err_sha"] == sf.sha_file(w.d / "receipts/LOOK-001.err.txt"))
        ok("a look logged before standard error was kept apart is rechecked with the launcher's warnings set aside",
           without_warnings("[exploring: output of LOOK-001]\nwarning: a launcher grumbles\ngain 1.0\n") == without_warnings("[exploring: output of LOOK-001]\ngain 1.0\n"))
        ok("a look that draws a figure has it in its receipt and in the log, by checksum, a picture that is not text included",
           [f["file"] for f in e["data"]["figures"]] == ["figures/photo.png", "figures/scatter.svg"]
           and e["data"]["figures"][0]["sha256"] == sf.sha_file(w.d / "figures/photo.png")
           and json.loads((w.d / "receipts/LOOK-001.json").read_text())["figures"] == e["data"]["figures"] and not breached(w.events()))
        ok("a look with a figure and a warning reproduces", said(cmd_recheck, w, A(look="LOOK-001")) == "")
        (w.d / "review" / "check.py").write_text("print('a variant: the gain again, by another route')\n")
        n_before = len(w.events())
        with contextlib.redirect_stdout(io.StringIO()) as shown:
            got = _refusal(cmd_recheck, w, A(look="LOOK-001", variant="review/check.py"))
        ok("a reviewer's variant of a look runs in its scratch folder on the same files, and nothing is logged (found by the first real run)",
           got == "" and "by another route" in shown.getvalue() and "not logged" in shown.getvalue() and len(w.events()) == n_before)
        (w.d / "review" / "reach.py").write_text("START = '2025-05-01'\nprint(START)\n")
        (w.d / "looks" / "variant.py").write_text("print('x')\n")
        ok("a variant that names a date inside the set-aside window is refused, and so is one outside the review folder",
           "date inside" in said(cmd_recheck, w, A(look="LOOK-001", variant="review/reach.py"))
           and "review/ folder" in said(cmd_recheck, w, A(look="LOOK-001", variant="looks/variant.py")) and len(w.events()) == n_before)
        ok("a look says how many comparisons it held", e["data"]["comparisons_declared"] == 9)
        quiet(cmd_choice, w, A(choice="keep every row", alternative=["drop the first"], rests_on="LOOK-001", look="LOOK-001"))
        ok("a choice is logged with the looks that had run when it was written down",
           last(w.events(), "choice.recorded")["data"]["after_looks"] == 1 and last(w.events(), "choice.recorded")["data"]["after"] == "LOOK-001")
        quiet(cmd_note, w, A(kind="missing", about="the A product", text="no page says what the flag values mean", evidence=None))
        wl = {"summary": {"looks_true": "The second record seems to track the first in twelve months.", "how_strong": "One look on one year of working data.",
                            "cannot_settle": "Whether it holds in another year or at another site."}, "what_looks_true": "A looks as if it follows B with a gain of 1.4826 over the year.",
              "how_it_was_found": "By fitting one line to the twelve paired rows.", "evidence": ["LOOK-001"],
              "choices_that_would_change_it": [{"choice": "CHOICE-002", "how": "not tried"}],
              "choices_that_would_not": [{"choice": "CHOICE-001", "why": "the intercept is small"}], "pitfalls": [],
              "proposed_plan": {"question": "Is the gain of A on B within five percent of one?", "quantity_estimated": "the gain",
                                "difference_that_matters": "five percent", "rule_sketch": "interval inside 0.95 to 1.05"}}
        wf = w.d / "lead.yaml"

        def lead_says(**change) -> str:
            wf.write_text(yaml.safe_dump({**wl, **change}))
            return said(cmd_lead, w, A(file=str(wf)))

        ok("a lead that quotes a number which is only part of a longer printed number is refused",
           "1.4" in lead_says(what_looks_true="A looks as if it follows B with a gain of 1.4 over the year."))
        ok("a lead that calls an interval a sampling interval is refused, with the words to use",
           "confidence interval" in lead_says(how_it_was_found="By fitting one line, with a 95 percent sampling interval."))
        ok("a lead that calls observations unflagged is refused, with the words to use",
           "flag's value" in lead_says(what_looks_true="A looks as if it follows B on the unflagged rows of the year."))
        ok("a lead with a key that is not a lead's is still refused", "not a key of a lead" in lead_says(conclusions="x"))
        # the lead in a minute, at the top (found by the first real run: its lead ran to 4,700 words before the so what)
        ok("a lead without a summary is refused", "`summary` is missing" in said(cmd_lead, w, A(file=str(
            (lambda f: (f.write_text(yaml.safe_dump({k: v for k, v in wl.items() if k != "summary"})), f)[1])(wf)))))
        ok("a summary without what it cannot settle is refused", "exactly these keys" in lead_says(summary={k: v for k, v in wl["summary"].items() if k != "cannot_settle"}))
        ok("a summary over 150 words is refused", "under 150 words" in lead_says(summary={**wl["summary"], "how_strong": "weak " * 150}))
        ok("a summary is checked like the rest: a number in it that no look printed is refused",
           "1.4827" in lead_says(summary={**wl["summary"], "looks_true": "A looks as if it follows B with a gain of 1.4827."}))
        # constants and counts in method text, and numbers the plan quotes (found by the same run: 1.96 was refused)
        def loose(**change) -> list:  # the number check alone, without recording a version
            return unbacked_numbers(w, {**wl, **change}, w.events())
        ok("a listed constant (1.96) and a count with a thousands comma pass in the method's words without a receipt",
           loose(how_it_was_found="By fitting one line to the paired rows, with 1.96 standard errors and 5,000 draws.") == [])
        ok("an unprinted result number is still refused in the method's words, and a listed constant where the lead says what looks true",
           "0.8123" in lead_says(how_it_was_found="By fitting one line, with a slope of 0.8123 dropped.")
           and "1.96" in lead_says(what_looks_true="A looks as if it follows B, with a z of 1.96 over the year."))
        ok("a plan sentence that names a look quotes it: a number that look did not print is refused, one it printed passes",
           "1.4827 (in the proposed plan" in lead_says(proposed_plan={**wl["proposed_plan"], "hard_cases": "a gain of 1.4827 as in LOOK-001."})
           and loose(proposed_plan={**wl["proposed_plan"], "hard_cases": "a gain of 1.4826 as in LOOK-001. A gain of 0.8123 is proposed here."}) == [])
        ok("a lead that shows a figure no look drew is refused",
           "no logged look drew" in lead_says(figures=[{"file": "figures/other.svg", "shows": "something"}]))
        ok("a lead may quote a number from a page that was read, may say what does not hold, and may show a figure a look drew",
           lead_says(what_does_not_hold="The two sit 0.44 km apart by the page read, so a gain of exactly one is not the expectation.",
                     open_explanations="A gain and a distance fit equally well.",
                     figures=[{"file": "figures/scatter.svg", "shows": "A against B, every row"}]) == "")
        got = json.loads((w.d / "lead.json").read_text())
        md = (w.d / "lead.md").read_text()
        ok("the lead shows the order of looks and choices from the log, and which choices were written down after looking",
           got["order"]["choices"]["CHOICE-001"]["after_looks"] == 0 and got["order"]["choices"]["CHOICE-002"]["after"] == "LOOK-001"
           and got["order"]["choices_recorded_after_looks"] == 1 and "Written down before any look." in md
           and "Written down after LOOK-001" in md and "CHOICE-001, then LOOK-001, then CHOICE-002" in md)
        ok("the lead adds up the comparisons its looks declared, and carries the figure by checksum",
           got["tried"]["comparisons_declared"] == 9 and got["figures"][0]["sha256"] == sf.sha_file(w.d / "figures/scatter.svg")
           and got["figures"][0]["look"] == "LOOK-001" and "](figures/scatter.svg)" in md)
        ok("the lead names what was neither explored nor set aside, and what the search listed that was not read",
           "protected by nothing: 2025-01-01 to 2025-04-27" in md and got["listed_not_read"] == [])
        n_events = len(w.events())
        ok("a correction that changes a number is refused: that is a new version",
           "never numbers" in said(cmd_correct, w, A(old="a gain of 1.4826", new="a gain of 1.5", why="rounding")))
        ok("a correction of words that are not in the lead is refused",
           "exactly once" in said(cmd_correct, w, A(old="follows B closely", new="tracks B", why="x")))
        ok("a correction to misleading words is refused",
           "confidence interval" in said(cmd_correct, w, A(old="over the year", new="over the year, with a sampling interval", why="x")))
        quiet(cmd_correct, w, A(old="looks as if it follows B", new="looks as if it rises and falls with B", why="'follows' was too loose"))
        got = json.loads((w.d / "lead.json").read_text())
        ok("the summary stands at the top of lead.md, before the question", (lambda md: md.index("## In short") < md.index("**The question.**"))(
            (w.d / "lead.md").read_text()))
        ok("the lead says which page was read though the search did not list it",
           "units.md`: NOT SIGNED (status draft) (read, though the search did not list it)" in (w.d / "lead.md").read_text())
        ok("a one-phrase correction of wording does not cost a lead version, and the lead shows the old and the new words",
           got["version"] == 1 and count(w.events(), "lead.recorded") == 1 and len(w.events()) == n_events + 1
           and "rises and falls with B" in got["what_looks_true"] and "Corrections of wording" in (w.d / "lead.md").read_text()
           and "\"looks as if it follows B\" now reads" in (w.d / "lead.md").read_text() and (w.d / "leads/lead-v1-correction-1.md").is_file())
        ok("a corrected lead checks out, and still says it is not a finding", check_log(w) == [] and "not a finding" in (w.d / "lead.md").read_text())
        ok("status counts the corrections made to the latest lead", stage_of(w)["wording_corrections_to_the_latest_lead"] == 1)
        quiet(cmd_review, w, RA(w, by="agent:tester-review", verdict="holes-found", file=str(vf)))
        so_what(w)
        quiet(cmd_end, w, A(outcome="lead", summary="A rises and falls with B; worth a test"))
        ok("once the exploration has ended a note can be resolved",
           said(cmd_resolve, w, A(by="agent:tester-curating", note="NOTE-001", disposition="linked", ref="gotchas/follow-datum.md")) == "")
        ok("a log that was written in the order the tool holds draws no remark", remarks(w.events()) == [])
        old_log = [{"seq": 0, "kind": "exploration.started", "data": {}}, {"seq": 1, "kind": "look.run", "data": {"id": "LOOK-001"}},
                   {"seq": 2, "kind": "lead.recorded", "data": {"version": 1}}, {"seq": 3, "kind": "note.resolved", "data": {"id": "NOTE-001"}}]
        ok("a log written before the tool held this order stays readable, and the check says in a remark where it departs",
           any("before the exploration had ended, and before the latest lead" in q for q in remarks(old_log))
           and any("standard error inside" in q for q in remarks(old_log)) and any("no page recorded as read" in q for q in remarks(old_log)))
        (w.d / "figures/scatter.svg").write_text("<svg/>")
        ok("check-log catches a changed figure", any("figure figures/scatter.svg" in q for q in check_log(w)))
        wb = fresh("E-6", subject="reach_id=R10,gauge=G10")
        known(wb)
        sb = script(wb, "blob.py", "from pathlib import Path\nPath('blob.bin').write_bytes(bytes([255, 254, 0, 1]))\n")
        ok("a file that is not text still spoils the exploration when it is not a figure in figures/", "spoiled" in look(wb, ["{python}", sb]))
        m = fresh("E-4", subject="reach_id=R7,gauge=G7")
        ok("ending as a method names the method's script", "names the method" in said(cmd_end, m, A(outcome="method", summary="a method", file=None)))
        sm = script(m, "method.py", "print('m')\n")
        quiet(cmd_end, m, A(outcome="method", summary="a method that pairs passes", file=sm))
        ok("an exploration can end as a method, bound by checksum", last(m.events(), "exploration.ended")["data"]["method"]["sha256"] == sf.sha_file(m.d / sm))
        # ---- what an independent attack found (docs/reviews/README.md, R1) ----------------
        # B1: set-aside data reached through a folder, a pattern, a tilde, a key=value word, a variable, a built path
        k = fresh("E-7", subject="reach_id=R11,gauge=G11")
        known(k)
        held_dir = tmp / "kept-apart"
        held_dir.mkdir()
        shutil.copyfile(later, held_dir / "record.json")
        anyp = script(k, "any.py", "import glob, json, os, sys\nfor a in sys.argv[1:]:\n    a = os.path.expanduser(os.path.expandvars(a.split('=', 1)[-1]))\n"
                                   "    names = glob.glob(a) if set(a) & set('*?[') else [a]\n    for n in names:\n"
                                   "        if os.path.isdir(n):\n            names += [os.path.join(n, f) for f in os.listdir(n)]\n            continue\n"
                                   "        print('rows', len(json.load(open(n))['rows']))\n")
        n_looks = count(k.events(), "look.run")
        ok("a look that names a folder is refused: a folder is a way to reach a file the fence never read",
           "names a folder" in look(k, ["{python}", anyp, str(held_dir)]) and "names a folder" in look(k, ["{python}", anyp, str(held_dir) + "/."]))
        ok("a look that names set-aside data after an `=` is refused, because the file after the `=` is read by the fence",
           "inside the set-aside window" in look(k, ["{python}", anyp, f"data={held_dir / 'record.json'}"])
           and "inside the set-aside window" in look(k, ["{python}", anyp, f"--data={held_dir / 'record.json'}"]))
        ok("a look that names a pattern is refused", "holds a pattern" in look(k, ["{python}", anyp, str(held_dir / "rec*.json")])
           and "holds a pattern" in look(k, ["{python}", anyp, str(held_dir / "{record,other}.json")]))
        ok("a look that names a tilde path is refused", "tilde path" in look(k, ["{python}", anyp, "~/somewhere/record.json"])
           and "tilde path" in look(k, ["{python}", anyp, "data=~/somewhere/record.json"]))
        ok("a look that names a variable for the script to expand is refused", "names a variable" in look(k, ["{python}", anyp, "$HOME/somewhere/record.json"]))
        ok("a look that hides a path behind a sign, or joins several into one word, is refused",
           "joined to other things" in look(k, ["{python}", anyp, f"@{held_dir / 'record.json'}"])
           and "joined to other things" in look(k, ["{python}", anyp, f"{data},{held_dir / 'record.json'}"]))
        ok("a look that names a place outside the exploration that is not an existing file is refused",
           "outside the exploration" in look(k, ["{python}", anyp, "../../../nowhere/record.json"]))
        ok("none of those looks ran, and every refusal is in the log", count(k.events(), "look.run") == n_looks and count(k.events(), "look.refused") >= 10)
        # a variable that names an existing path used to be refused, because looks were given the caller's variables. A look
        # is now given a fixed environment the tool builds, so the variable never arrives: stronger than refusing it
        seen = script(k, "seen.py", "import os\nprint('given', os.environ.get('UV_SF_SELFTEST_DATA'), os.environ.get('SSL_CERT_DIR'), sorted(os.environ))\n")
        kept_env = {n: os.environ.get(n) for n in ("UV_SF_SELFTEST_DATA", "SSL_CERT_DIR")}
        os.environ.update(UV_SF_SELFTEST_DATA=str(held_dir / "record.json"), SSL_CERT_DIR=str(held_dir))
        try:
            ran_seen = look(k, ["{python}", seen])
        finally:
            for n, v in kept_env.items():
                os.environ.pop(n, None) if v is None else os.environ.__setitem__(n, v)
        e_seen = last(k.events(), "look.run")["data"]
        ok("a variable of the caller's that names an existing path never reaches a look: a look is given the environment the tool "
           "builds, and its receipt lists that environment by name",
           ran_seen == "" and "given None None" in e_seen["out_head"] and "UV_SF_SELFTEST_DATA" not in e_seen["ran_in"]["environment"]
           and "SSL_CERT_DIR" not in e_seen["ran_in"]["environment"] and "SF_INSIDE_A_LOOK" in e_seen["ran_in"]["environment"])
        ok("a file named after an `=` runs when it is working data, and is logged as a file the look was given",
           look(k, ["{python}", anyp, f"data={data}"]) == "" and last(k.events(), "look.run")["data"]["inputs"][0]["sha256"] == sf.sha_file(data)
           and "rows 12" in last(k.events(), "look.run")["data"]["out_head"])
        ran_in = last(k.events(), "look.run")["data"]["ran_in"]
        ok("a look runs in a scratch folder that holds its script and the files it names, and the log says where each was put",
           [f["at"] for f in ran_in["placed"]] == ["looks/any.py", "outside/01-a_b_2024.json"] and ran_in["argv_as_run"][-1] == "data=outside/01-a_b_2024.json"
           and ran_in["confined"] in (CONFINED_BY_THE_KERNEL, SCRATCH_ONLY))
        (k.d / "side.json").write_text(json.dumps({"rows": [1, 2, 3]}))
        lister = script(k, "lister.py", "import os\nprint(sorted(os.path.join(b, f) for b, _d, fs in os.walk('.') for f in fs))\n")
        look(k, ["{python}", lister])
        ok("the scratch folder holds nothing the command did not name: not the log, not the request, not a file beside the script",
           "side.json" not in last(k.events(), "look.run")["data"]["out_head"] and "exploration-log" not in last(k.events(), "look.run")["data"]["out_head"]
           and "any.py" not in last(k.events(), "look.run")["data"]["out_head"] and "lister.py" in last(k.events(), "look.run")["data"]["out_head"])
        built = script(k, "built.py", "import json, os\np = os.path.join(" + ", ".join(repr(q) for q in (held_dir / "record.json").parts) + ")\n"
                                      "rows = json.load(open(p))['rows']\nprint('first time', rows[0]['time'])\n")
        said_built = look(k, ["{python}", built])
        e = last(k.events(), "look.run")
        ok("a script that builds the path of set-aside data itself gets nothing usable: the kernel keeps it out where it can, and "
           "where it cannot the set-aside values in what the look printed spoil the exploration and are withheld",
           "2025-06-01" not in (k.d / f"receipts/{e['data']['id']}.out.txt").read_text() and "2025-06-01" not in e["data"]["out_head"]
           and ((e["data"]["ran_in"]["confined"] == CONFINED_BY_THE_KERNEL and e["data"]["exit_code"] != 0 and not breached(k.events()))
                or (e["data"]["ran_in"]["confined"] == SCRATCH_ONLY and "spoiled" in said_built and breached(k.events()))))

        # the same attacks on a machine with no kernel fence, which the self-test stands in for by switching it off
        real_landlock = globals()["landlock"]
        globals()["landlock"] = lambda: 0
        try:
            kb = fresh("E-8", subject="reach_id=R12,gauge=G12")
            known(kb)
            builtb = script(kb, "built.py", (k.d / built).read_text())
            ok("with no kernel fence, a script that reads set-aside data by a path it built spoils the exploration when it prints it, "
               "and what it printed is withheld from the record and from whoever ran the look",
               "spoiled" in look(kb, ["{python}", builtb]) and last(kb.events(), "look.run")["data"]["ran_in"]["confined"] == SCRATCH_ONLY
               and "what the look printed names a date inside the set-aside window" in last(kb.events(), "fence.breached")["data"]["what"][0]
               and "2025-06-01" not in (kb.d / "receipts/LOOK-001.out.txt").read_text() and "withheld" in (kb.d / "receipts/LOOK-001.out.txt").read_text())
            kc = fresh("E-9", subject="reach_id=R13,gauge=G13")
            known(kc)
            log_was = kc.log.read_bytes()
            forge = script(kc, "forge.py", "import json\nfrom pathlib import Path\n"
                                           f"d = Path({str(kc.d)!r})\n"
                                           "(d / 'verdicts' / 'REVIEW-001.md').write_text('no holes')\n"
                                           "with (d / 'exploration-log.jsonl').open('a') as f:\n"
                                           "    f.write(json.dumps({'kind': 'review.verdict', 'actor': 'agent:review-b'}) + chr(10))\n")
            said_forge = look(kc, ["{python}", forge])
            ok("with no kernel fence, a script that writes into the exploration itself (a forged line in the log, a forged verdict) "
               "spoils the exploration, and the log is put back as it stood",
               "spoiled" in said_forge and kc.log.read_bytes().startswith(log_was) and not any(e_["kind"] == "review.verdict" for e_ in kc.events())
               and not (kc.d / "verdicts" / "REVIEW-001.md").exists()
               and any("put it back" in q for q in last(kc.events(), "fence.breached")["data"]["what"])
               and any("verdicts/REVIEW-001.md" in q for q in last(kc.events(), "fence.breached")["data"]["what"]))
        finally:
            globals()["landlock"] = real_landlock

        # a look leaves nothing where the tool or another role keeps its files, and no process behind it
        kd = fresh("E-10", subject="reach_id=R14,gauge=G14")
        known(kd)
        places = script(kd, "places.py", "import os\nfrom pathlib import Path\n"
                                         "for p in ('verdicts/REVIEW-001.md', 'review/r.md', 'exploration-log.jsonl', 'lead.md', 'receipts/LOOK-009.json', 'notes/NOTE-001.json'):\n"
                                         "    Path(p).parent.mkdir(parents=True, exist_ok=True)\n    Path(p).write_text('forged')\n"
                                         "Path('figures').mkdir(exist_ok=True)\nos.symlink('/etc/hostname', 'figures/link.svg')\n"
                                         "Path('table.csv').write_text('a,b' + chr(10) + '1,2' + chr(10))\nprint('done')\n")
        ok("a look runs", look(kd, ["{python}", places]) == "")
        e = last(kd.events(), "look.run")
        ok("what a look writes where the tool or a reviewer keeps files is not kept, a link it leaves is not followed, and its own files are",
           not (kd.d / "verdicts/REVIEW-001.md").exists() and not (kd.d / "review/r.md").exists() and not (kd.d / "lead.md").exists()
           and not (kd.d / "receipts/LOOK-009.json").exists() and not (kd.d / "figures/link.svg").exists() and (kd.d / "table.csv").is_file()
           and list(e["data"]["wrote"]) == ["table.csv"] and len(e["data"]["ran_in"]["not_kept"]) == 7 and check_log(kd) == [])
        if sys.platform.startswith("linux"):
            stay = script(kd, "stay.py", "import subprocess, sys\np = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True,\n"
                                         "                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\nprint('left', p.pid)\n")
            look(kd, ["{python}", stay])
            e = last(kd.events(), "look.run")
            left = int(e["data"]["out_head"].split("left")[1].split()[0])
            ok("a process a look detaches, to act once the look is over, is ended with the look",
               e["data"]["ran_in"]["processes_ended"] >= 1 and not Path(f"/proc/{left}").exists())
        else:
            ok("a process a look detaches is ended with the look (checked on Linux only; elsewhere its process group is ended)", True)

        # M4: a file a script reads without the command naming it is declared, read by the fence and pinned
        knob = script(kd, "knob.py", "print('gain', float(open('knob.txt').read()))\n")
        (kd.d / "knob.txt").write_text("1.25\n")
        look(kd, ["{python}", knob])
        ok("a script that reads a file its command does not name does not find it in its scratch folder",
           last(kd.events(), "look.run")["data"]["exit_code"] != 0)
        ok("the same look runs when the file is declared with --also-reads, and the receipt holds it by checksum",
           said(cmd_look, kd, A(argv=["--", "{python}", knob], why="the gain with its setting", also_reads=["knob.txt"])) == ""
           and "gain 1.25" in last(kd.events(), "look.run")["data"]["out_head"]
           and any(f["at"] == "knob.txt" and f["role"] == "also-reads" for f in last(kd.events(), "look.run")["data"]["ran_in"]["placed"]))
        knob_look = last(kd.events(), "look.run")["data"]["id"]
        ok("that look reproduces", said(cmd_recheck, kd, A(look=knob_look)) == "")
        (kd.d / "knob.txt").write_text("1.50\n")
        ok("a recheck is refused when a file the look read without naming it has changed: it is not run on another setting",
           "is not the file" in said(cmd_recheck, kd, A(look=knob_look)))
        (kd.d / "knob.txt").write_text("1.25\n")
        ok("a file declared with --also-reads is read by the fence like any other",
           "inside the set-aside window" in said(cmd_look, kd, A(argv=["--", "{python}", knob], why="x", also_reads=[str(later)])))

        # S2: a look cannot call the tools, and a review comes only from a reviewer named before the lead existed
        fake = tmp / "fake" / "explore.py"  # a process whose command line reads `explore.py look`, as a real look's does
        fake.parent.mkdir()
        fake.write_text("import os, subprocess, sys\nenv = {k: v for k, v in os.environ.items() if not k.startswith(('PYTHON', 'SF_'))}\n"
                        "for tool in sys.argv[2:]:\n"
                        "    r = subprocess.run([sys.executable, tool, 'status', '--study' if tool.endswith('sf.py') else '--exploration', 'x'],\n"
                        "                       env=env, capture_output=True, text=True)\n"
                        "    print(r.returncode, 'inside a look' in r.stderr)\n")
        nested = subprocess.run([sys.executable, str(fake), "look", str(HERE / "sf.py"), str(HERE / "explore.py")], capture_output=True, text=True,
                                env={k_: v for k_, v in os.environ.items() if not k_.startswith("SF_")})
        ok("a tool started from under a look refuses, whatever the script took out of its environment: it reads its own ancestry",
           nested.stdout.split() == ["2", "True", "2", "True"])
        kn = subprocess.run([sys.executable, str(HERE / "knowledge.py"), "about", "--question", "does A follow B?", "--wiki", str(bundle)],
                            capture_output=True, text=True, env={**os.environ, "SF_INSIDE_A_LOOK": "E"})
        ok("the knowledge tool refuses inside a look too", kn.returncode == 2 and "inside a look" in kn.stderr)
        r = fresh("E-11", subject="reach_id=R15,gauge=G15", reviewer=None)
        known(r)
        selfreview = script(r, "selfreview.py",
                            "import os, subprocess, sys\nenv = {k: v for k, v in os.environ.items() if not k.startswith(('PYTHON', 'SF_'))}\n"
                            f"x, tool = {str(r.d)!r}, {str(HERE / 'explore.py')!r}\n"
                            "for words in (['reviewer', '--exploration', x, '--by', 'agent:coordinating-b', '--reviewer', 'agent:review-b'],\n"
                            "              ['note', '--exploration', x, '--by', 'agent:review-b', '--kind', 'missing', '--about', 'a', '--text', 'b']):\n"
                            "    r = subprocess.run([sys.executable, tool, *words], env=env, capture_output=True, text=True)\n"
                            "    print('nested exit', r.returncode)\nprint('rows 12')\n")
        real = subprocess.run([sys.executable, str(HERE / "explore.py"), "look", "--exploration", str(r.d), "--by", "agent:tester-analysis", "--model", "selftest-model", "--why",
                               "a look that tries to call the tool", "--", "{python}", selfreview], capture_output=True, text=True)
        ok("a look whose script shells out to this tool gets nowhere: both calls fail, and nothing but the look is added to the log",
           real.returncode == 0 and real.stdout.count("nested exit") == 2 and "nested exit 0" not in real.stdout
           and [e_["kind"] for e_ in r.events()][-1] == "look.run" and not count(r.events(), "reviewer.named") and not count(r.events(), "note.raised"))
        with r.held():
            waiting = subprocess.run([sys.executable, str(HERE / "explore.py"), "note", "--exploration", str(r.d), "--by", "agent:tester-analysis", "--model", "selftest-model",
                                      "--kind", "missing", "--about", "a", "--text", "b"], capture_output=True, text=True)
        ok("while a look holds the exploration log, a command that would write to it is refused and does not wait",
           waiting.returncode == 2 and "log is held" in waiting.stderr and not count(r.events(), "note.raised"))
        rl = {"summary": {"looks_true": "The second record seems to track the first in twelve months.", "how_strong": "One look on one year of working data.",
                            "cannot_settle": "Whether it holds in another year or at another site."}, "what_looks_true": "A follows B closely over the year, on changes, across 12 rows.", "how_it_was_found": "By pairing the two records and counting rows.",
              "evidence": ["LOOK-001"], "choices_that_would_change_it": [], "choices_that_would_not": [], "pitfalls": [],
              "proposed_plan": {"question": "Is the gain of A on B within five percent of one?", "quantity_estimated": "the gain",
                                "difference_that_matters": "five percent", "rule_sketch": "interval inside the band"}}
        rf = r.d / "lead.yaml"
        rf.write_text(yaml.safe_dump(rl))
        ok("a lead is refused until a reviewer has been named: the name a review comes under is fixed before the lead exists",
           "no reviewer is named" in said(cmd_lead, r, A(file=str(rf))) and "before_a_lead" in stage_of(r))
        ok("whoever did the exploring cannot name the reviewer, and cannot be named",
           "did part of this exploration" in said(cmd_reviewer, r, A(by="agent:tester-analysis", reviewer="agent:review-b"))
           and "did part of this exploration" in said(cmd_reviewer, r, A(by="agent:tester-coordinating", reviewer="agent:TESTER-analysis"))
           and "is not the reviewer" in said(cmd_reviewer, r, A(by="agent:review-b", reviewer="agent:review-b")))
        quiet(cmd_reviewer, r, A(by="agent:tester-coordinating", reviewer="agent:tester-review"))
        quiet(cmd_lead, r, A(file=str(rf)))
        ok("a review under a fresh name, never named as a reviewer, is refused",
           "was not named as a reviewer" in said(cmd_review, r, RA(r, by="agent:review-b", verdict="no-holes-found", file=str(vf))))
        quiet(cmd_reviewer, r, A(by="agent:tester-coordinating", reviewer="agent:review-late"))
        ok("a reviewer named after the lead was recorded cannot review that lead",
           "was not named as a reviewer of this exploration before lead version 1" in said(cmd_review, r, RA(r, by="agent:review-late", verdict="no-holes-found", file=str(vf))))
        ok("the reviewer named before the lead may review it, and status lists who is named",
           said(cmd_review, r, RA(r, by="agent:tester-review", verdict="no-holes-found", file=str(vf))) == ""
           and stage_of(r)["reviewers_named"] == ["agent:review-late", "agent:tester-review"])
        rs = fresh("E-12", subject="reach_id=R16,gauge=G16", reviewer=None)
        quiet(cmd_reviewer, rs, A(by="agent:sock-coordinating", reviewer="agent:sock-review"))
        known(rs)
        quiet(cmd_note, rs, A(by="agent:sock-coordinating", kind="dead-end", about="x", text="the namer now does part of the work", evidence=None))
        quiet(cmd_end, rs, A(outcome="note", summary="ended as a note"))
        ok("a reviewer named by a name that then did part of the work is not taken",
           "who did part of this exploration" in said(cmd_review, rs, RA(rs, by="agent:sock-review", verdict="no-holes-found", file=str(vf))))

        # S5: a correction made after the review undoes the review
        ok("a correction made after the review is taken, and says the lead must be reviewed again",
           said(cmd_correct, r, A(old="follows B closely", new="is beyond any doubt identical to B", why="wording")) == "")
        ok("after it the lead is no longer reviewed: the exploration does not end as a lead, and status names the review agent",
           "corrected after it was reviewed" in said(cmd_end, r, A(outcome="lead", summary="x")) and stage_of(r)["stage"] == "review")
        quiet(cmd_review, r, RA(r, by="agent:tester-review", verdict="holes-found", file=str(vf)))
        so_what(r)
        quiet(cmd_end, r, A(outcome="lead", summary="A follows B; worth a test"))
        quiet(cmd_hand_over, r, A(by="agent:tester-coordinating", study_id="STUDY-R", local_practice=True))
        handed = (r.d / "hand-over/request.md").read_text()
        ok("the hand-over then carries the verdict of the review that saw the corrected words, and says so",
           "holes-found" in handed and "no-holes-found" not in handed and "corrected 1 time(s) before that review, and not since" in handed
           and "named as a reviewer by agent:tester-coordinating" in handed and last(r.events(), "review.verdict")["data"]["corrections_seen"] == 1)
        ok("a correction cannot change a number written another way: a decimal comma, a missing zero, an exponent, a share",
           all("never numbers" in said(cmd_correct, w, A(old="a gain of 1.4826", new=new_, why="x"))
               for new_ in ("a gain of 1,4826", "a gain of 1.4826e1", "a gain of 1.4826 percent", "a gain of 11.4826", "a gain of .4826")))

        # ---- the person's so what on a reviewed lead ------------------------------------------------
        sw = fresh("E-SO-WHAT", subject="reach_id=R40,gauge=G40")
        ff = tmp / "fit.yaml"
        ff.write_text(yaml.safe_dump({"answer_is": "a judgement", "data_at_hand": "partly", "mostly": "judgement",
                                      "person_must_supply": "what would make agreement between A and B surprising",
                                      "verdict": "fit-with-a-person-steering", "why": "the counting is easy and the question is what matters",
                                      "taste_needed": "someone who knows how A and B are maintained"}))
        quiet(cmd_fit, sw, A(by="agent:tester-coordinating", file=str(ff)))
        ok("the coordinating agent's fit note is recorded at intake and shown in status, and writing it does not make it part of the work",
           "fit-with-a-person-steering" in stage_of(sw)["fit"] and "agent:tester-coordinating" not in did_the_work(sw.events()))
        known(sw)
        ssw = script(sw, "rows.py", "import json, sys\nd = json.load(open(sys.argv[1]))\nprint('rows', len(d['rows']))\n")
        sfig = script(sw, "draw.py", "from pathlib import Path\nPath('figures').mkdir(exist_ok=True)\n"
                                     "Path('figures/a-on-b.svg').write_text('<svg xmlns=\"http://www.w3.org/2000/svg\"/>')\nprint('drawn')\n")
        look(sw, ["{python}", sfig], why="a picture of A against B, every row")
        ok("a fit note once the first look has run is refused", "work has started" in said(cmd_fit, sw, A(by="agent:tester-coordinating", file=str(ff))))
        look(sw, ["{python}", ssw, str(data)])
        swf = sw.d / "lead.yaml"
        swf.write_text(yaml.safe_dump(rl))
        quiet(cmd_lead, sw, A(file=str(swf)))
        qf = tmp / "so-what-question.yaml"
        qf.write_text(yaml.safe_dump({"what_the_lead_shows": "A follows B over the year on changes, across twelve rows.",
                                      "why_it_might_matter": "If it holds, B could stand in for A where A is missing.",
                                      "what_would_make_it_unremarkable": "A and B are known to share a source, which would make agreement expected."}))
        ok("a so what before the lead is reviewed is refused, and so is the question",
           "has not been reviewed" in so_what(sw) and "has not been reviewed" in said(cmd_ask_so_what, sw, A(file=str(qf), read_lead=sf.sha_file(sw.d / "lead.json"))))
        quiet(cmd_review, sw, RA(sw, by="agent:tester-review", verdict="holes-found", file=str(vf)))
        asked_q = yaml.safe_load(qf.read_text())
        qf.write_text(yaml.safe_dump({**asked_q, "options": "test one idea"}))
        ok("the question's options are a list of ways on, in words", "`options` is a list" in said(
            cmd_ask_so_what, sw, A(by="agent:tester-coordinating", file=str(qf), read_lead=sf.sha_file(sw.d / "lead.json"))))
        qf.write_text(yaml.safe_dump({**asked_q, "options": ["test the gain on next year's data", "look at the low-stage readings first"],
                                      "mood": "words that are no part of the question"}))
        ok("a key that is not a question's is still refused", "may have `options`" in said(
            cmd_ask_so_what, sw, A(by="agent:tester-coordinating", file=str(qf), read_lead=sf.sha_file(sw.d / "lead.json"))))
        qf.write_text(yaml.safe_dump({**asked_q, "options": ["test the gain on next year's data", "look at the low-stage readings first"]}))
        quiet(cmd_ask_so_what, sw, A(by="agent:tester-coordinating", file=str(qf), read_lead=sf.sha_file(sw.d / "lead.json")))
        ok("an agent drafts the question for the person: what the lead shows, why it might matter, what would make it unremarkable",
           (sw.d / "so-what" / "QUESTION-001.md").is_file() and "What would make it unremarkable" in (sw.d / "so-what" / "QUESTION-001.md").read_text()
           and last(sw.events(), "so-what.asked")["actor"] == "agent:tester-coordinating")
        ok("the question shows the options the lead sets out, none chosen (found by the first real run: they had no key of their own)",
           "b. look at the low-stage readings first" in (sw.d / "so-what" / "QUESTION-001.md").read_text())
        ok("an agent cannot record the answer, by any route: not under its own name, not as practice, not as the platform without a comment",
           "a person's answer" in so_what(sw, by="agent:tester-coordinating") and "a person's answer" in so_what(sw, by="agent:tester-review")
           and "platform's name" in said(cmd_so_what, sw, A(by="agent:tester-coordinating", record_comment=str(tmp / "none.json")))
           and not count(sw.events(), "so-what.recorded"))
        ok("typed without saying practice, a so what is refused on a factory whose so what is a comment on the platform",
           "--local-practice" in so_what(sw, local_practice=False) and so_what_declared().get("route") == COMMENT)
        ok("a so what for a lead the person did not read is refused", "--read-lead" in so_what(sw, read_lead="0" * 64))
        ok("each answer that needs words is refused without them, and words that belong to another answer are refused",
           "direction" in so_what(sw, "try-instead") and "reason" in so_what(sw, "not-interesting") and "expertise" in so_what(sw, "needs-an-expert")
           and "goes with" in so_what(sw, "worth-confirming", direction="look at low flows instead") and "one of" in so_what(sw, "maybe"))
        so_what(sw, "needs-an-expert", expertise="someone who knows how the B gauge is maintained")
        ok("needs-an-expert holds the lead for a person with that expertise, and the end as a lead is refused",
           stage_of(sw)["stage"] == "so-what" and "B gauge" in stage_of(sw)["waiting_for"]
           and "not worth-confirming" in said(cmd_end, sw, A(outcome="lead", summary="x")))
        so_what(sw, "try-instead", direction="look at the changes in low flow only, where the two differ most")
        ok("try-instead returns the exploration to exploring, with the direction recorded as its next question",
           stage_of(sw)["stage"] == "explore" and "low flow" in stage_of(sw)["next_question"]
           and last(sw.events(), "so-what.recorded")["data"]["direction"].startswith("look at the changes"))
        look(sw, ["{python}", ssw, str(data)])
        quiet(cmd_lead, sw, A(file=str(swf)))
        ok("a new version of the lead has no so what until it is reviewed and answered again",
           so_what_now(sw.events()) is None and stage_of(sw)["stage"] == "review")
        quiet(cmd_review, sw, RA(sw, by="agent:tester-review", verdict="no-holes-found", file=str(vf)))
        so_what(sw)
        quiet(cmd_correct, sw, A(old="follows B closely", new="follows B on changes", why="wording"))
        ok("a correction after the so what undoes it with the review: the person answered other words",
           so_what_now(sw.events()) is None and "worth confirming" in str(so_what_problems(sw.events())))
        quiet(cmd_review, sw, RA(sw, by="agent:tester-review", verdict="no-holes-found", file=str(vf)))
        so_what(sw)
        quiet(cmd_end, sw, A(outcome="lead", summary="A follows B on changes; a person says it is worth confirming"))
        quiet(cmd_hand_over, sw, A(by="agent:tester-coordinating", study_id="STUDY-SO-WHAT", local_practice=True))
        swho = (sw.d / "hand-over/request.md").read_text()
        figs = json.loads((sw.d / "hand-over/figures.json").read_text())["figures"]
        ok("the hand-over carries every figure the looks kept, by checksum, with the reason of the look that drew it as its caption",
           figs == [{"file": "figures/LOOK-001-a-on-b.svg", "sha256": sf.sha_file(sw.d / "figures/a-on-b.svg"), "look": "LOOK-001",
                     "caption": "a picture of A against B, every row"}] and (sw.d / "hand-over/figures/LOOK-001-a-on-b.svg").is_file())
        quiet(cmd_contribution, sw, A())
        said_c = (sw.d / "contribution.md").read_text()
        ok("the contribution statement of a lead names who did each kind of work, with counts, the agents with the model they declared, "
           "and says what the log cannot show",
           "| the so what | human:throwaway-placeholder (a person, by the name typed) |" in said_c
           and "| exploring | agent:tester-analysis (an AI agent, model selftest-model as declared) |" in said_c
           and "| reviewing | agent:tester-review (an AI agent, model selftest-model as declared) | 3 |" in said_c
           and "What the logs cannot show" in said_c and "a lead, not a finding" in said_c
           and json.loads((sw.d / "contribution.json").read_text())["rows"][0]["work"] == "asking the question")
        ok("the hand-over carries the so what, who gave it and its standing, and the fit note, and the log checks out",
           "**The so what.** worth-confirming, by human:throwaway-placeholder" in swho and "**The fit note.** **fit-with-a-person-steering**" in swho and "standing: practice" in swho
           and json.loads((sw.d / "hand-over/hand-over.json").read_text())["so_what"]["standing"] == sf.PRACTICE and check_log(sw) == [])
        # ---- a look that proved useful becomes a method, and a study may use it once its own tests pass there
        methods = tmp / "repo" / "methods"
        rd = tmp / "method-readme.md"
        rd.write_text("# rows-counted\n\n**What it computes.** How many rows a record holds, printed as one line.\n\n")
        ok("a method is promoted only with a README that says what it computes, on what inputs and its known limits, under a proper name",
           "**On what inputs.**" in said(cmd_promote, sw, A(by="agent:tester-analysis", look="LOOK-002", name="rows-counted", readme=str(rd), methods=str(methods)))
           and "`--name`" in said(cmd_promote, sw, A(by="agent:tester-analysis", look="LOOK-002", name="Rows Counted", readme=str(rd), methods=str(methods)))
           and not methods.exists())
        rd.write_text("# rows-counted\n\n**What it computes.** How many rows a record holds, printed as one line.\n\n"
                      "**On what inputs.** One JSON file of working data with a list under `rows`.\n\n"
                      "**Known limits.** It checks no row and reads nothing but the one file.\n")
        quiet(cmd_promote, sw, A(by="agent:tester-analysis", look="LOOK-002", name="rows-counted", readme=str(rd), methods=str(methods)))
        mdir = methods / "rows-counted"
        mj = json.loads((mdir / "method.json").read_text())
        ok("the promoted method holds the script by checksum, the exploration's runs of it as known-answer cases with their inputs and "
           "outputs, the agent's README with where it came from, and a test file",
           sf.sha_file(mdir / "rows.py") == last(sw.events(), "look.run")["data"]["script_sha"] and sorted(mj["cases"]) == ["LOOK-002", "LOOK-003"]
           and (mdir / "known-answers" / "LOOK-002" / "expected.out.txt").read_text() == "rows 12\n"
           and "## Where it came from" in (mdir / "README.md").read_text() and mj["from"]["exploration"] == "E-SO-WHAT"
           and last(sw.events(), "method.promoted")["data"]["name"] == "rows-counted")
        ran = subprocess.run([sys.executable, str(mdir / "known_answer_tests.py")], capture_output=True, text=True)
        ok("the method's known-answer tests reproduce every case", ran.returncode == 0 and "PASS (2 of 2)" in ran.stdout)
        exp = mdir / "known-answers" / "LOOK-003" / "expected.out.txt"
        kept_exp = exp.read_text()
        exp.write_text("rows 13\n")
        ran = subprocess.run([sys.executable, str(mdir / "known_answer_tests.py")], capture_output=True, text=True)
        exp.write_text(kept_exp)
        ok("a case changed after the promotion fails the tests", ran.returncode == 1 and "changed since the promotion" in ran.stdout)
        ok("a second promotion under the same name is refused",
           "exists" in said(cmd_promote, sw, A(by="agent:tester-analysis", look="LOOK-002", name="rows-counted", readme=str(rd), methods=str(methods))))
        uses = json.loads(json.dumps(sf.PLAN))
        uses["code"] = uses["code"] + [str(mdir / "rows.py")]
        uses["data"]["held_out"]["pair"] = "uses-a-promoted-method"
        ps = sf._fresh(work / "studies", "STUDY-USES-METHOD", plan=uses, start=A(id="STUDY-USES-METHOD", question=sf.PLAN["question"], by="agent:tester-coordinating"))
        ok("a plan that uses a promoted method without running its tests as a rehearsal fails the plan check",
           any("promoted method `rows-counted`" in q for q in sf.check_plan(ps.plan(), ps)))
        uses["rehearsals"] = [{"id": "method-rows-counted", "why": "the promoted method's own known-answer tests, in this study",
                               "steps": [["{python}", str(mdir / "known_answer_tests.py")]]}]
        ps.plan_path.write_text(yaml.safe_dump(uses, sort_keys=False))
        ok("with the rehearsal declared, the study's tests are refused until the method's own tests have passed in this study",
           sf.check_plan(ps.plan(), ps) == [] and "have not passed in this study" in said(sf.cmd_test, ps, A(what="known-answers", by="agent:tester-analysis")))
        quiet(sf.cmd_rehearse, ps, A(id="method-rows-counted", by="agent:tester-analysis"))
        ok("once the method's tests pass as a rehearsal of this study, the study's tests run",
           ps.last("rehearsal.run", id="method-rows-counted")["data"]["exit"] == 0
           and said(sf.cmd_test, ps, A(what="known-answers", by="agent:tester-analysis")) == "")
        (mdir / "rows.py").write_text((mdir / "rows.py").read_text() + "# changed\n")
        ok("a promoted method changed after its tests passed is refused again: the code they passed on is not the code now",
           "have not passed in this study" in said(sf.cmd_test, ps, A(what="working-data", by="agent:tester-analysis")))

        no = fresh("E-SO-WHAT-NO", subject="reach_id=R41,gauge=G41")
        known(no)
        look(no, ["{python}", script(no, "rows.py", "import json, sys\nprint('rows', len(json.load(open(sys.argv[1]))['rows']))\n"), str(data)])
        (no.d / "lead.yaml").write_text(yaml.safe_dump(rl))
        quiet(cmd_lead, no, A(file=str(no.d / "lead.yaml")))
        quiet(cmd_review, no, RA(no, by="agent:tester-review", verdict="no-holes-found", file=str(vf)))
        ok("no agent ends an exploration as a lead noted", "no agent ends one so" in said(cmd_end, no, A(outcome="lead-noted", summary="x")))
        so_what(no, "not-interesting", reason="the agreement is what a shared source would give, so nothing new is learned")
        ok("not-interesting ends the exploration as a lead noted, with the reason, and nothing is handed over",
           last(no.events(), "exploration.ended")["data"]["outcome"] == "lead-noted" and "shared source" in last(no.events(), "exploration.ended")["data"]["summary"]
           and "has not ended as a lead" in said(cmd_hand_over, no, A(by="agent:tester-coordinating", study_id="STUDY-NO", local_practice=True)))
        # the platform route: a comment on the tracking issue, recorded by the job that follows it, verified by asking the platform
        pc = fresh("E-SO-WHAT-PR", subject="reach_id=R42,gauge=G42")
        known(pc)
        look(pc, ["{python}", script(pc, "rows.py", "import json, sys\nprint('rows', len(json.load(open(sys.argv[1]))['rows']))\n"), str(data)])
        (pc.d / "lead.yaml").write_text(yaml.safe_dump({**rl, "what_looks_true": "A clearly follows B over the year, which confirms the idea, across 12 rows."}))
        quiet(cmd_lead, pc, A(file=str(pc.d / "lead.yaml")))
        over = stage_of(pc)["overclaiming"]
        ok("a lead that claims more than an exploration can show is recorded all the same, and status names each phrase and its line: "
           "`confirms` always, since a lead is tested on nothing",
           count(pc.events(), "lead.recorded") == 1 and any("`clearly`" in f and f.startswith("lead.md, line ") for f in over)
           and any("`confirms`" in f for f in over))
        quiet(cmd_review, pc, RA(pc, by="agent:tester-review", verdict="no-holes-found", file=str(vf)))
        repo = so_what_declared()["repository"]
        body = f"so-what: worth-confirming\nexploration: explorations/{pc.d.name}\nlead: {sf.sha_file(pc.d / 'lead.json')[:16]}\n"
        cm = {"id": 77, "html_url": f"https://github.com/{repo}/issues/3#issuecomment-77", "user": {"login": "a-scientist", "type": "User"},
              "author_association": "MEMBER", "created_at": "2026-11-26T10:00:00Z", "body": body}
        cf = tmp / "comment.json"

        def comment(**change) -> str:
            cf.write_text(json.dumps({**cm, **change}))
            return said(cmd_so_what, pc, A(by="platform:github", record_comment=str(cf)))
        ok("a comment by a bot, by an account outside the repository, for another lead or for another exploration is not recorded",
           "not call the comment's author a user" in comment(user={"login": "helper[bot]", "type": "Bot"})
           and "does not belong to the repository" in comment(author_association="NONE")
           and "the lead on file" in comment(body=body.replace(sf.sha_file(pc.d / "lead.json")[:16], "0" * 16))
           and "not this one" in comment(body=body.replace(pc.d.name, "EXPLORATION-ELSE"))
           and not count(pc.events(), "so-what.recorded"))
        ok("the platform writes nothing else into an exploration", "writes one thing" in said(cmd_note, pc, A(by="platform:github", kind="missing", about="a", text="b")))
        comment()
        got_sw = last(pc.events(), "so-what.recorded")
        ok("a person's comment is recorded under the platform's name, with its author as handed, standing `comment recorded, person not verified`",
           got_sw["actor"] == "platform:github" and got_sw["data"]["comment"]["author"] == "a-scientist" and so_what_standing(pc.events(), got_sw) == COMMENT_FOUND)
        quiet(cmd_end, pc, A(outcome="lead", summary="worth a test, a person said on the platform"))
        ok("a hand-over on a comment needs no word of practice", said(cmd_hand_over, pc, A(by="agent:tester-coordinating", study_id="STUDY-PR")) == "")
        vmod = so_what_harness(so_what_declared())[0]
        sf.PLATFORM_CALL = lambda api, path, token: ({"status": 200, "body": cm} if path == f"/repos/{repo}/issues/comments/77" else {"status": 404, "body": None})
        try:
            quiet(cmd_verify_so_what, pc, A(by="agent:tester-coordinating"))
        finally:
            sf.PLATFORM_CALL = None
        ok("asked, the platform confirms the comment, and the so what stands as verified", so_what_standing(pc.events(), got_sw) == sf.VERIFIED
           and last(pc.events(), "so-what.verification")["data"]["asked"][0]["endpoint"].endswith("/comments/77") and vmod.PEOPLE)
        saved_tokens = {k: os.environ.pop(k) for k in ("SF_PLATFORM_TOKEN", "GH_TOKEN", "GITHUB_TOKEN") if k in os.environ}
        try:
            quiet(cmd_verify_so_what, pc, A(by="agent:tester-coordinating"))
        finally:
            os.environ.update(saved_tokens)
        ok("with no token nothing is asked, the result is `not checked`, and the standing falls back to what the job was handed",
           last(pc.events(), "so-what.verification")["data"]["result"] == sf.NOT_CHECKED and so_what_standing(pc.events(), got_sw) == COMMENT_FOUND)

        # M1: a number is a number however it is written, and a page the explorer wrote backs nothing
        m1 = fresh("E-13", subject="reach_id=R17,gauge=G17")
        known(m1)
        look(m1, ["{python}", script(m1, "fit.py", "print('gain 1.4826 on 12 rows')\n")])
        m1f = m1.d / "lead.yaml"

        def m1_says(text: str) -> str:
            m1f.write_text(yaml.safe_dump({**rl, "what_looks_true": f"A looks as if it follows B, {text}, over the whole year."}))
            return said(cmd_lead, m1, A(file=str(m1f)))

        forms = ("7.7777x", "3.3333m", ".8888", "8,8888", "8.888e0", "88888e-4", "8 .8888", "105 percent", "105%", "x7.7777", "1.4826e0", "1.48")
        refused = {f_: "quotes numbers" in m1_says(f"with a gain of {f_}") for f_ in forms}
        ok("a number no look printed is refused in every form it can be written: " + ", ".join(forms)
           + (f" (let through: {[f_ for f_, hit in refused.items() if not hit]})" if not all(refused.values()) else ""), all(refused.values()))
        own = m1.d / "looks" / "my-note.md"
        own.write_text("# A note of my own\n\nThe gain is 6.6666.\n")
        quiet(cmd_read, m1, A(concept=str(own), takes="my own note"))
        stray = bundle.parent / "stray.md"
        stray.write_text("# A page in no wiki\n\nThe gain is 5.5555.\n")
        quiet(cmd_read, m1, A(concept=str(stray), takes="a page outside every listed wiki"))
        ok("a page the explorer wrote and recorded as read backs no number, and neither does a page outside every listed wiki",
           "6.6666" in m1_says("with a gain of 6.6666") and "5.5555" in m1_says("with a gain of 5.5555"))
        ok("a number a cited look printed, and one from a page of a listed wiki that was read, are still taken",
           m1_says("with a gain of 1.4826 at sites 0.44 km apart") == "")

        # ================= the second independent attack (TOOL-ATTACK-2), finding by finding =================
        kernel = bool(landlock())
        own_env = fence.own_environment()
        site = next(iter(sorted(own_env.glob("lib/python*/site-packages"))), own_env)
        held2 = tmp / "held-elsewhere"  # a place nobody declared, as in the attack
        held2.mkdir()
        (tmp / "to-come").mkdir()
        rows2025 = [(f"2025-{m:02d}-{d:02d}", 5.0 + m / 10, 5.5 + m / 10) for m in range(1, 13) for d in (3, 17)]
        (held2 / "record-2025.json").write_text(json.dumps({"rows": [{"time": f"{t}T00:00:00Z", "a": a_, "b": b_} for t, a_, b_ in rows2025]}))

        # N1: a look has no write access to anything the tools later run or import
        n1 = fresh("E-N1", subject="reach_id=R30,gauge=G30")
        known(n1)
        plant = script(n1, "plant.py", "import glob, os, sys\n"
                       f"places = [{str(site)!r}, {str(own_env.parent)!r}, {str(HERE)!r}, os.path.expanduser('~/.cache/uv'), os.environ.get('UV_CACHE_DIR') or '/nonexistent']\n"
                       f"places += glob.glob({str(own_env.parent)!r} + '/*/lib/python*/site-packages')\n"
                       "got = {}\nfor p in places:\n    try:\n        open(os.path.join(p, 'sf_selftest_probe.pth'), 'w').write('# planted by a self-test\\n')\n        got[p] = 'WROTE'\n"
                       "    except OSError as e:\n        got[p] = type(e).__name__\n"
                       "print('planted', sorted(set(got.values())), 'cache variable', os.environ.get('UV_CACHE_DIR'))\n")

        def planted() -> list:
            found = [q for q in [site / "sf_selftest_probe.pth", own_env.parent / "sf_selftest_probe.pth", HERE / "sf_selftest_probe.pth"] if q.exists()]
            return found + [Path(q) for q in __import__("glob").glob(str(own_env.parent) + "/*/lib/python*/site-packages/sf_selftest_probe.pth")]
        if kernel:
            look(n1, ["{python}", plant])
            e = last(n1.events(), "look.run")["data"]
            left_behind = planted()
            for q in left_behind:
                q.unlink(missing_ok=True)
            ok("N1: with the kernel fence, a look cannot write a start-up file into the environment the tools run from, into any other "
               "environment beside it, into the launcher's cache or beside the tools; nothing is planted",
               "planted ['PermissionError']" in e["out_head"].replace("'FileNotFoundError', ", "").replace(", 'FileNotFoundError'", "")
               and not left_behind and "cache variable None" in e["out_head"])
            ok("N1: the receipt records the fence as applied and tried: it could not write the tool's own environment or the tools' folder",
               e["ran_in"]["confined"] == CONFINED_BY_THE_KERNEL and e["ran_in"]["fence"]["applied"] is True
               and f"write {own_env}" in e["ran_in"]["fence"]["tried_and_kept_out"] and f"write {HERE}" in e["ran_in"]["fence"]["tried_and_kept_out"]
               and not any(str(own_env.parent) == w or str(own_env).startswith(w + "/") for w in e["ran_in"]["fence"]["could_write"]))
            dep = script(n1, "with_dependency.py", "# /// script\n# requires-python = \">=3.11\"\n# dependencies = [\"pyyaml\"]\n# ///\n"
                         "import os, sys, yaml\ntry:\n    open(os.path.join(os.path.dirname(yaml.__file__), 'planted.py'), 'w').write('x')\n    wrote = 'WROTE'\n"
                         "except OSError as e:\n    wrote = type(e).__name__\nprint('yaml', bool(yaml.__version__), wrote, 'uv' in os.path.basename(sys.argv[0]))\n")
            ran_dep = look(n1, ["uv", "run", dep])
            e = last(n1.events(), "look.run")["data"]
            ok("N1: `uv run` in a look does not run the launcher inside the fence: the script's own dependencies are installed beforehand "
               "into a throwaway environment the script can import from and cannot write, and the receipt says so"
               + (f" (the look said: {ran_dep[:200]})" if ran_dep else ""),
               "yaml True PermissionError" in e["out_head"] and "throwaway environment" in e["ran_in"]["interpreter"]
               and not any("uv" == Path(q).name for q in e["ran_in"]["fence"]["could_write"]))
            second = script(n1, "second.py", "import glob, os\nprint('left by an earlier look:', sorted(glob.glob(os.path.expanduser('~') + '/*')), "
                            "sorted(glob.glob(os.environ['TMPDIR'] + '/*')))\n")
            first = script(n1, "first.py", "import os\nfor p in (os.path.expanduser('~/note.txt'), os.environ['TMPDIR'] + '/note.txt'):\n    open(p, 'w').write('left by a look')\nprint('left')\n")
            look(n1, ["{python}", first])
            look(n1, ["{python}", second])
            ok("N1: what one look leaves in its home, its temporary folder or a cache is gone before the next: there is no place two looks share",
               "left by an earlier look: [] []" in last(n1.events(), "look.run")["data"]["out_head"])
        real_landlock = globals()["landlock"]
        globals()["landlock"] = lambda: 0
        try:
            n1b = fresh("E-N1B", subject="reach_id=R31,gauge=G31")
            known(n1b)
            unfenced = script(n1b, "plant.py", f"open({str(site / 'sf_selftest_probe.pth')!r}, 'w').write('# planted by a self-test\\n')\nprint('planted')\n")
            said_plant = look(n1b, ["{python}", unfenced])
            for q in planted():
                q.unlink(missing_ok=True)
            e = last(n1b.events(), "look.run")["data"]
            ok("N1, where there is no kernel fence: a look that plants a start-up file in the tools' environment is not stopped, and the "
               "tool says so: the look spoils the exploration, and the breach names the file",
               "spoiled" in said_plant and e["ran_in"]["confined"] == SCRATCH_ONLY and breached(n1b.events())
               and any("sf_selftest_probe.pth" in q for q in last(n1b.events(), "fence.breached")["data"]["what"]))
        finally:
            globals()["landlock"] = real_landlock

        # N2 and N3: no variable of the caller's turns the kernel fence off or widens it, and the receipt says what was applied
        n2 = fresh("E-N2", subject="reach_id=R32,gauge=G32")
        known(n2)
        reach = script(n2, "reach.py", "import os\nparts = " + repr(list((held2 / "record-2025.json").parts)) + "\n"
                       "try:\n    n = len(open(os.path.join(*parts)).read())\n    print('READ', n)\nexcept OSError as e:\n    print('kept out', type(e).__name__)\n"
                       "print('names', sorted(k for k in os.environ if k.startswith(('UV_', 'SSL', 'REQUESTS', 'CURL'))))\n")
        if kernel:
            variables = {"UV_CACHE_DIR": str(tmp), "SSL_CERT_DIR": str(held2), "SSL_CERT_FILE": str(held2 / "record-2025.json"),
                         "REQUESTS_CA_BUNDLE": str(held2 / "record-2025.json"), "UV_TOOL_DIR": str(held2), "UV_PYTHON_INSTALL_DIR": str(held2),
                         "UV_ENV_FILE": str(held2 / "record-2025.json"), "UV_KNOB": "5"}
            kept_env = {n: os.environ.get(n) for n in variables}
            results_n = {}
            for name, value in variables.items():
                os.environ[name] = value
                try:
                    look(n2, ["{python}", reach])
                finally:
                    os.environ.pop(name, None) if kept_env[name] is None else os.environ.__setitem__(name, kept_env[name])
                e = last(n2.events(), "look.run")["data"]
                results_n[name] = ("kept out PermissionError" in e["out_head"] and "names []" in e["out_head"]
                                   and e["ran_in"]["confined"] == CONFINED_BY_THE_KERNEL and name not in e["ran_in"]["environment"])
            ok("N2, N3, N14: a cache setting that lies above the exploration, the three certificate variables, two launcher folders, a "
               "file of variables and a knob, each set by the caller, do not reach a look: the set-aside file stays kept out, the fence "
               "stays on, and the receipt lists the environment the look was really given"
               + (f" (failed for: {[n for n, good in results_n.items() if not good]})" if not all(results_n.values()) else ""),
               all(results_n.values()) and not breached(n2.events()))
        real_run = fence.run_fenced
        fence.run_fenced = lambda *a_, **k_: {**real_run(*a_, **{**k_, "kernel": False}), "not_run": True, "confined": SCRATCH_ONLY,
                                              "fence": {"applied": False, "why_not": "a stand-in: the fence could not be put up"}}
        try:
            before_n = count(n2.events(), "look.run")
            said_off = look(n2, ["{python}", reach])
            ok("N2: on a machine with a kernel fence, a fence that cannot be put up is a refusal and not a quiet fall-back: no look is logged",
               "could not be put up or did not hold" in said_off and count(n2.events(), "look.run") == before_n)
        finally:
            fence.run_fenced = real_run
        ok("N2: `status` says how many looks ran with the kernel fence and how many in a scratch folder only",
           stage_of(n2)["looks_by_fence"]["with_the_kernel_fence"] + stage_of(n2)["looks_by_fence"]["in_a_scratch_folder_only"] == count(n2.events(), "look.run"))

        # N4: set-aside data under another spelling of its dates. First the structure, then the second line.
        n4 = fresh("E-N4", subject="reach_id=R33,gauge=G33", set_aside_window="2025-01-01:2025-12-31")
        known(n4)
        show = script(n4, "show.py", "import sys\nprint(open(sys.argv[1]).read()[:200])\n")
        shapes = {
            "slashes.csv": "time,a,b\n" + "\n".join(f"{t.replace('-', '/')},{a_},{b_}" for t, a_, b_ in rows2025),
            "compact.csv": "time,a,b\n" + "\n".join(f"{t.replace('-', '')},{a_},{b_}" for t, a_, b_ in rows2025),
            "no-zeros.csv": "time,a,b\n" + "\n".join(f"{int(t[:4])}-{int(t[5:7])}-{int(t[8:])},{a_},{b_}" for t, a_, b_ in rows2025),
            "day-first.csv": "time,a,b\n" + "\n".join(f"{t[8:]}.{t[5:7]}.{t[:4]},{a_},{b_}" for t, a_, b_ in rows2025),
            "named.csv": "time,a,b\n" + "\n".join(f"{int(t[8:])} {MONTHS[int(t[5:7]) - 1].title()} {t[:4]};{a_};{b_}" for t, a_, b_ in rows2025),
            "keyed.json": json.dumps({"readings": {f"{t}T12:00:00Z": {"a": a_, "b": b_} for t, a_, b_ in rows2025}}),
            "padded.json": json.dumps({"rows": [{"time": " " * 33 + t, "a": a_} for t, a_, _b in rows2025]}),
            "hyphen.json": json.dumps({"rows": [{"time": t.replace("-", "\u2010"), "a": a_} for t, a_, _b in rows2025]}),
            "epoch.json": json.dumps({"rows": [{"time": int(dt.datetime.fromisoformat(t + "T00:00:00+00:00").timestamp()), "a": a_} for t, a_, _b in rows2025]}),
            "epoch-ms.json": json.dumps({"rows": [{"time": int(dt.datetime.fromisoformat(t + "T00:00:00+00:00").timestamp()) * 1000, "a": a_} for t, a_, _b in rows2025]}),
        }
        before_n = count(n4.events(), "look.run")
        outside_refused = {}
        for name, body in shapes.items():
            (held2 / name).write_text(body)
            outside_refused[name] = "is not in a place this exploration declared as working data" in look(n4, ["{python}", show, str(held2 / name)])
        ok("N4, the structure: a file that is neither in the exploration nor in the working data it declared at its start is not given to a "
           "look, whatever it holds and however its dates are written: " + ", ".join(shapes)
           + (f" (let through: {[n for n, hit in outside_refused.items() if not hit]})" if not all(outside_refused.values()) else ""),
           all(outside_refused.values()) and count(n4.events(), "look.run") == before_n)
        ok("N4: a place that holds the exploration, the studies or a set-aside path cannot be declared as working data, and neither can a place that is not there",
           "holds the exploration itself" in said(cmd_start, Exploration(work / "explorations" / "E-N4W"), A(request=str(req), id="E-N4W", working_data=[str(work)]))
           and "set-aside path" in said(cmd_start, Exploration(work / "explorations" / "E-N4W"),
                                        A(request=str(req), id="E-N4W", working_data=[str(tmp / "to-come")], set_aside_path=[str(tmp / "to-come" / "next.json")]))
           and "names nothing that exists" in said(cmd_start, Exploration(work / "explorations" / "E-N4W"), A(request=str(req), id="E-N4W", working_data=[str(tmp / "nowhere")]))
           and not (work / "explorations" / "E-N4W" / "exploration-log.jsonl").exists())
        inside_refused = {}
        for name, body in shapes.items():  # the second line: the same files, put inside the exploration by hand
            (n4.d / name).write_text(body)
            inside_refused[name] = "set-aside window" in look(n4, ["{python}", show, name])
            (n4.d / name).unlink()
        ok("N4, the second line: set-aside data put inside the exploration is still read by the fence and refused, with its dates written with "
           "slashes, run together, without leading zeros, day first, with the month by name, as keys, behind spaces, with a look-alike hyphen, "
           "and as seconds or milliseconds under a time key"
           + (f" (let through: {[n for n, hit in inside_refused.items() if not hit]})" if not all(inside_refused.values()) else ""),
           all(inside_refused.values()) and count(n4.events(), "look.run") == before_n)
        ok("N4: a date outside the window, a number that is not a time, and a checksum with eight digits in it are not taken for set-aside dates",
           not [d for d in dates_in("on 2024/03/01 we read 12345678 rows; sha a20250314b7; version 1.2.3; 31/12/2024") if in_any(d, n4.set_aside())]
           and date_of_a_number(1.02) is None and date_of_a_number(52) is None)
        printer = script(n4, "printer.py", "y = str(2000 + 25)\nprint('first row ' + '/'.join([y, '01', '03']) + ', then ' + y + '0117, then 3 Feb ' + y)\n")
        ok("N4: output that carries a set-aside date in another spelling spoils the exploration and is withheld",
           "spoiled" in look(n4, ["{python}", printer]) and "withheld" in (n4.d / "receipts" / f"LOOK-{count(n4.events(), 'look.run'):03d}.out.txt").read_text())

        # N7: a review is recorded for the lead the reviewer read
        n7 = fresh("E-N7", subject="reach_id=R34,gauge=G34")
        known(n7)
        look(n7, ["{python}", script(n7, "fit.py", "print('gain 1.4826 on 12 rows')\n")])
        n7f = n7.d / "lead.yaml"
        n7f.write_text(yaml.safe_dump({**rl, "what_looks_true": "A looks as if it follows B with a gain of 1.4826 over the whole year."}))
        quiet(cmd_lead, n7, A(file=str(n7f)))
        read_sha = sf.sha_file(n7.d / "lead.json")
        (n7.d / "review" / "r.md").write_text("holes: none found\n")
        quiet(cmd_correct, n7, A(old="a gain of", new="a proven, final and certain gain of", why="wording"))
        ok("N7: a review that names no lead is refused, and so is one that names the lead as it stood before a correction",
           "--read-lead" in said(cmd_review, n7, A(by="agent:tester-review", verdict="no-holes-found", file=str(n7.d / "review" / "r.md")))
           and "is not the one you read" in said(cmd_review, n7, A(by="agent:tester-review", verdict="no-holes-found", file=str(n7.d / "review" / "r.md"), read_lead=read_sha))
           and not last(n7.events(), "review.verdict"))
        ok("N7: `status` gives the reviewer the checksum of the lead as it stands, and a review that names it is recorded",
           stage_of(n7)["lead_json_sha256"] == sf.sha_file(n7.d / "lead.json")
           and said(cmd_review, n7, RA(n7, by="agent:tester-review", verdict="no-holes-found", file=str(n7.d / "review" / "r.md"))) == "")

        # N8: four more ways to write a number, and a page planted where a role may write
        more = ("7\u00b77777", "7\u066b7777", "7. 7777", "77777/10000", "7\u22c57777", "77777 / 10000", "\uff17.\uff17\uff17\uff17\uff17")
        refused = {f_: "quotes numbers" in m1_says(f"with a gain of {f_}") for f_ in more}
        ok("N8: a number no look printed is refused with a middle dot or an Arabic decimal mark for the point, a gap after the point, "
           "and as a division by a power of ten" + (f" (let through: {[f_ for f_, hit in refused.items() if not hit]})" if not all(refused.values()) else ""),
           all(refused.values()))
        ok("N8: an ordinary fraction and a sentence that ends in a year are not taken for decimals",
           m1_says("in 3/4 of the looks, in 2024. 12 rows were read, and 1.4826 was the gain") == "")
        for folder in ("studies/s/finding-draft", "knowledge-queue-reviews", "review"):
            (bundle / folder).mkdir(parents=True, exist_ok=True)
            (bundle / folder / "numbers.md").write_text("---\ntype: note\n---\n\n# numbers\n\nThe gain is 4.4444.\n")
            quiet(cmd_read, m1, A(concept=str(bundle / folder / "numbers.md"), takes="a page in a role's own place inside the wiki"))
        ok("N8: a page under a folder a role writes into (a study's finding draft, a queue of reviews, a review folder) backs no number, "
           "even inside a listed wiki", "4.4444" in m1_says("with a gain of 4.4444"))

        # M5: a rewritten log shows against the commit, with no fingerprint given
        if sf.git("--version") is not None:
            repo = tmp / "repo"
            gx = Exploration(repo / "explorations" / "E-G")
            (repo / "explorations").mkdir(parents=True)
            quiet(cmd_start, gx, A(request=str(req), id="E-G", subject="reach_id=R18,gauge=G18"))
            quiet(cmd_known, gx, A(bundle=[str(bundle)], question=None))
            quiet(cmd_note, gx, A(kind="missing", about="a", text="b", evidence=None))
            sf.git("-C", str(repo), "init", "-q")
            sf.git("-C", str(repo), "add", "-A")
            sf.git("-C", str(repo), "-c", "user.name=selftest", "-c", "user.email=selftest@example.invalid", "commit", "-q", "-m", "an exploration")
            ok("a committed exploration log checks out, and still does once more is added to it",
               check_log(gx) == [] and said(cmd_note, gx, A(kind="missing", about="c", text="d", evidence=None)) == "" and check_log(gx) == [])
            ev_ = gx.events()[:2]  # cut short, and chained again from the first line: every hash is right
            ev_[1]["data"]["question"] = "another question?"
            prev = ev_[0]["hash"]
            body = {k_: ev_[1][k_] for k_ in ("seq", "at", "actor", "kind", "data")}
            ev_[1] = {**body, "prev": prev, "hash": gx._digest(prev, body)}
            gx.log.write_text("".join(json.dumps(e_, sort_keys=True) + "\n" for e_ in ev_))
            (gx.d / "notes").rename(gx.d / "notes-gone")
            ok("a log rewritten with every hash right, or cut short, passes its own chain and is caught against the commit",
               gx._chain(gx.events()) == [] and any("last committed" in q for q in check_log(gx)))
        else:
            ok("a log rewritten with every hash right is caught against the commit (not run: no git here)", True)

        # S1: no option is taken by its first letters
        def parses(words: list) -> bool:
            try:
                with contextlib.redirect_stderr(io.StringIO()):
                    build_parser().parse_args(words)
            except SystemExit:
                return False
            return True

        ok("an option is taken only when it is spelled out: `--b` is not `--by`",
           parses(["note", "--exploration", "x", "--by", "agent:a", "--kind", "missing", "--about", "a", "--text", "b"])
           and not parses(["note", "--exploration", "x", "--b", "agent:review-9", "--kind", "missing", "--about", "a", "--text", "b"])
           and not parses(["note", "--exploration", "x", "--b=human:someone", "--kind", "missing", "--about", "a", "--text", "b"])
           and not parses(["status", "--explor", "x"]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    sf.Study.default_model = None
    failed = [n for n, good in results if not good]
    for n in failed:
        print("FAIL:", n)
    print(f"selftest: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)} of {len(results)})")
    return 0 if not failed else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, *args):
        p = sub.add_parser(name, allow_abbrev=False)  # no option is taken by its first letters: `--b` is not `--by`
        p.add_argument("--exploration", required=True, help="the exploration directory")
        if by in args:
            args = (*args, model)
        for names, kw in args:
            p.add_argument(*names, **kw)
        p.set_defaults(fn=fn)
        return p

    by = (["--by"], {"required": True, "help": "who acts: agent:<id> (or human:<id> for a person exploring)"})
    model = (["--model"], {"default": None, "help": "the model that acts, when an agent does: required with --by agent:<id>, declared by "
                                                    "the caller and recorded in the event; a person's event needs none"})
    add("start", cmd_start, by, (["--id"], {"required": True}), (["--question"], {"required": True}),
        (["--request"], {"required": True, "help": "the request, in the scientist's own words; bound by checksum"}),
        (["--subject"], {"required": True, "help": "key=value,key=value: what the data is about. The keys are yours to choose "
                                                   "(reach_id, gauge, product); a later plan's `pair` must carry the same keys and values, "
                                                   "and they are matched through case and spacing, not through other spellings"}),
        (["--boundary-from"], {"action": "append", "default": None, "dest": "boundary_from",
                               "help": "a knowledge page the boundary of the set-aside was read from; repeatable. Only knowledge is "
                                       "read before data is set aside, never data"}),
        (["--how"], {"default": None, "help": "how the data is held out: " + "; ".join(HOW)}),
        (["--set-aside-window"], {"default": None, "help": "START:END, or START: for a window that stays open"}),
        (["--set-aside-sites"], {"default": None, "help": "site identifiers, separated by commas"}),
        (["--set-aside-release"], {"action": "append", "default": None, "help": "a release, collection or record name; repeatable"}),
        (["--release-cut-off"], {"default": None, "dest": "release_cut_off",
                                 "help": "with a new release: the last date of the data as it stands; the start binds the working data by "
                                         "checksum and a look at a file that changed or holds a later date is refused"}),
        (["--set-aside-path"], {"action": "append", "default": None, "help": "where the set-aside data would land if fetched; repeatable"}),
        (["--nothing-set-aside"], {"default": None, "help": "the reason nothing can be set aside; such an exploration hands nothing over"}),
        (["--fresh-data"], {"default": None, "dest": "fresh_data",
                            "help": "the proposal of the fresh data (tools/fresh_data.py propose) that this start sets aside; required for a random set aside"}),
        (["--why"], {"default": None, "help": "why this is the data to set aside"}),
        (["--working"], {"default": None, "help": "what will be explored, in words"}),
        (["--working-data"], {"action": "append", "default": None, "dest": "working_data",
                              "help": "a file or a folder outside the exploration that holds the data to explore; repeatable. A look "
                                      "is given the exploration's own files and files in these places, and nothing else"}),
        (["--working-window"], {"default": None, "help": "START:END of the data that will be explored"}),
        (["--time-keys"], {"default": None, "help": "the keys under which a data file carries its times (default: " + ",".join(TIME_KEYS) + ")"}),
        (["--studies"], {"default": None, "help": "the folder of confirming studies, where the record is (default: ../../studies from the exploration)"}))
    add("fit", cmd_fit, by, (["--file"], {"required": True, "help": "the fit note (YAML): " + ", ".join(sf.FIT_KEYS)}))
    add("promote", cmd_promote, by, (["--look"], {"required": True, "help": "the look whose script becomes a method, such as LOOK-002"}),
        (["--name"], {"required": True, "help": "the method's name: lower-case letters, digits and hyphens"}),
        (["--readme"], {"required": True, "help": "the README you wrote: " + ", ".join(README_PARTS)}),
        (["--methods"], {"required": True, "help": "the methods folder of the repository, such as methods"}))
    add("known", cmd_known, by, (["--wiki", "--bundle"], {"dest": "bundle", "action": "append", "required": True,
                                                         "help": "a wiki: a directory of Markdown pages; repeatable"}),
        (["--drafts"], {"action": "append", "default": None, "help": "a queue of drafted pages, listed as drafts; repeatable"}),
        (["--question"], {"default": None}), (["--tag"], {"action": "append", "default": None}))
    add("read", cmd_read, by, (["--concept"], {"required": True, "help": "the page: the path `known` printed for it, its path below the wiki, or the file"}),
        (["--takes"], {"required": True, "help": "what this concept rules in, rules out or warns about, for this question"}),
        (["--depth"], {"default": "whole", "help": "whole (the default) or skimmed: a page that came in on a stray word may be skimmed, and the lead says so"}))
    look = add("look", cmd_look, by, (["--why"], {"required": True, "help": "what this look is trying to find out"}),
               (["--also-reads"], {"action": "append", "default": None, "dest": "also_reads",
                                   "help": "a file the script reads without the command naming it (a helper it imports, a "
                                           "settings file); repeatable. It is read by the fence, put in the look's scratch "
                                           "folder and pinned by checksum like a named file"}))
    look.add_argument("argv", nargs=argparse.REMAINDER, help="-- LAUNCHER SCRIPT [arguments]")
    add("recheck", cmd_recheck, (["--look"], {"required": True, "help": "the look to run again, such as LOOK-003"}),
        (["--variant"], {"default": None, "help": "a script of the reviewer's own in review/, run in the look's place on the same files, "
                                                  "in its scratch folder; logged nowhere, and listed in the review"}))
    add("choice", cmd_choice, by, (["--choice"], {"required": True}), (["--alternative"], {"action": "append", "default": None}),
        (["--rests-on"], {"required": True, "dest": "rests_on"}), (["--look"], {"default": None}))
    add("note", cmd_note, by, (["--kind"], {"required": True}), (["--about"], {"required": True}), (["--text"], {"required": True}),
        (["--evidence"], {"default": None}))
    add("lead", cmd_lead, by, (["--file"], {"required": True, "help": "the lead file (YAML)"}))
    add("correct", cmd_correct, by, (["--old"], {"required": True, "help": "the words as they stand in the lead, exactly once"}),
        (["--new"], {"required": True, "help": "the words to put in their place; the numbers in them are the same"}),
        (["--why"], {"required": True, "help": "why the old words were wrong"}))
    add("reviewer", cmd_reviewer, by, (["--reviewer"], {"required": True, "help": "the name the review will come under, such as agent:review-01"}))
    add("review", cmd_review, by, (["--verdict"], {"required": True, "help": " or ".join(VERDICTS)}), (["--file"], {"required": True}),
        (["--read-lead"], {"default": None, "dest": "read_lead", "help": "the sha256 of the lead.json the reviewer read; `status` prints it"}))
    add("ask-so-what", cmd_ask_so_what, by, (["--file"], {"required": True, "help": "the question (YAML): " + ", ".join(QUESTION_KEYS) + ", and `options` if the lead sets some out"}),
        (["--read-lead"], {"required": True, "dest": "read_lead", "help": "the sha256 of the lead.json the question is about"}))
    add("so-what", cmd_so_what, by, (["--answer"], {"default": None, "help": ", ".join(SO_WHAT)}),
        (["--direction"], {"default": None, "help": "for try-instead: the direction, in words"}),
        (["--reason"], {"default": None, "help": "for not-interesting: why, in words"}),
        (["--expertise"], {"default": None, "help": "for needs-an-expert: the kind of expertise wanted"}),
        (["--read-lead"], {"default": None, "dest": "read_lead", "help": "the sha256 of the lead.json you read; `status` prints it"}),
        (["--local-practice"], {"action": "store_true", "dest": "local_practice",
                                "help": "typed at a command line, for trying the tools: the so what says it is practice"}),
        (["--record-comment"], {"default": None, "dest": "record_comment",
                                "help": "for the job that follows a comment on the platform (--by platform:github): the comment's JSON"}))
    add("verify-so-what", cmd_verify_so_what, by, (["--report-only"], {"action": "store_true", "dest": "report_only"}))
    add("end", cmd_end, by, (["--outcome"], {"required": True, "help": ", ".join(OUTCOMES)}), (["--summary"], {"required": True}),
        (["--file"], {"default": None}))
    add("hand-over", cmd_hand_over, by, (["--study-id"], {"required": True, "dest": "study_id"}),
        (["--local-practice"], {"action": "store_true", "dest": "local_practice",
                                "help": "hand over on a so what that was typed (practice); the request and the lock say so"}))
    add("check-study", cmd_check_study, (["--study"], {"required": True}))
    add("curation-list", cmd_curation_list)
    add("resolve", cmd_resolve, by, (["--note"], {"required": True}), (["--disposition"], {"required": True, "help": ", ".join(DISPOSITIONS)}),
        (["--ref"], {"default": None, "help": "for drafted: the draft's path in the queue; for linked: the page's path below the wiki"}),
        (["--comment"], {"default": None, "help": "for declined: why; for a linked note about a stale or wrong signed page: what the steward should do"}))
    add("status", cmd_status)
    add("check-log", cmd_check_log, (["--anchor"], {"action": "append", "default": None, "help": "SEQ:HASH posted outside the workspace; repeatable"}))
    add("fingerprint", cmd_fingerprint)
    add("contribution", cmd_contribution)
    sub.add_parser("selftest", allow_abbrev=False)
    return ap


def main() -> int:
    a = build_parser().parse_args()
    try:
        sf.refuse_dirty_environment()
        sf.refuse_inside_a_look()
        if a.cmd == "selftest":
            return selftest()
        x = Exploration(a.exploration)
        x.model = getattr(a, "model", None)
        if str(getattr(a, "by", "")).startswith("agent:") and not x.model:
            raise Refused(sf.NO_MODEL)  # said before anything is run or written
        a.fn(x, a)
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
