#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""fresh_data: the fresh data for a confirming study, proposed from metadata only.

Fresh data is data that is fresh to the people asking: nobody has looked at
it, so it can check an idea that was found by looking at other data. The
tools call it held-out data. Most people do not arrive with any, so an agent
proposes it, and people approve the choice when they lock the plan.

The agent proposes from metadata only: a file that lists what data exists
(an identifier, a site or region, dates, a release, a count of observations
for each item) and no measured value. This tool reads that one file and
nothing else, and refuses a file that carries any other field, because a
field it does not know may be a value. It runs no language model.

There are four kinds of fresh data:

  next-release   wait for the next release of the data, and check on it
  later-period   a period after the one that is explored
  another-site   a site or region that is not explored
  random         a random set aside of the items (sites, as a rule)

For each proposal the agent writes, in words: exactly what data, why it
suits the question, and what would make it unfair. The tool counts what the
metadata says about the size of the test (items and observations, fresh and
working), says plainly what it does not compute (the power of the plan's
rules at that size, which the method's known-answer tests measure), adds a
caution for the kind, and gives the arguments that set the data aside in
`explore.py start` and the block for the plan.

A random set aside is drawn from something nobody working on the question
can choose or try again: the merge commit GitHub creates when a person
merges the lock request, read through the platform's own answer at the
opening. The seed is the sha256 of that commit and the proposal's checksum;
every item is ranked by the sha256 of the seed and its identifier, and the
first part is taken. So the proposal draws nothing: it names the items the
draw is made from and how many, and says the members are to be drawn at the
lock. No seed is made or kept, and a seed handed to the tool is refused. A
seed a proposing tool could make (as this one once did) can be drawn again
and again until the members suit somebody, record or no record. A study
whose lock is typed (practice) draws from the practice lock's own log
entry, which whoever typed it could have made again: such a draw could be
chosen, and the study says so.

Commands.

  describe  write the metadata of one long CSV file from its date column (and
            a column that names each series): one item for each series and
            year or month, with its count, the file by its sha256, and the
            release the file grows by, with its cadence. It keeps no other
            column. It is the step before a proposal, done at intake
  propose   write a proposal from a metadata file; add it to the record
            beside the studies
  show      a proposal in plain words
  reveal    draw a random set aside from a merge commit (`--merge-commit`),
            as the opening drew it, so anybody can check the members; a seed
            handed in is refused
  check     what a reviewer asks of a proposal: it is on the record, its
            words are written, a random set aside is still to be drawn, and it
            was written before the exploration or study it serves started
  selftest  the tool tests itself

Usage: fresh_data.py <command> [...]; fresh_data.py selftest
"""
import sys

sys.dont_write_bytecode = True
if __name__ == "__main__" and not (sys.flags.isolated and sys.flags.no_site and "sf-no-bytecode" in str(sys.pycache_prefix)):
    # A clean start, as in the other tools: run again in a Python that reads no PYTHON variable, no user site and no
    # start-up file. What a hostile environment ran before this line has already run (docs/WHAT-IS-ENFORCED.md).
    import os
    _again = [sys.executable, "-I", "-S", "-B", "-X", "pycache_prefix=" + ("/dev/null/sf-no-bytecode" if os.name == "posix" else os.path.join(os.environ.get("TEMP", "."), f"sf-no-bytecode-{os.getpid()}")), os.path.abspath(__file__), *sys.argv[1:]]
    if os.name == "posix":
        os.execv(sys.executable, _again)
    import subprocess
    sys.exit(subprocess.call(_again))
if __name__ == "__main__":
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
import datetime as dt  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import secrets  # noqa: E402
import shutil  # noqa: E402
import tempfile  # noqa: E402
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
TOOL = Path(__file__).resolve()


class Refused(Exception):
    pass


def _fence():
    """tools/fence.py, by its path: what says whether this process was started from inside a look."""
    if "fence" not in sys.modules:
        spec = _source_spec("fence", HERE / "fence.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["fence"] = mod
        spec.loader.exec_module(mod)
    return sys.modules["fence"]


KINDS = {  # the name on the command line: (the words people read, a caution the tool adds, how explore.py sets it aside)
    "next-release": ("the next data release (wait for it)",
                     "A new release can reprocess the old data too: if the working data changes with it, compare like with like, "
                     "and say which version of the working data the method was built on.", "a new release"),
    "later-period": ("a later period",
                     "A later period checks the idea only if nothing else changed at the same time: a new sensor, new processing, "
                     "a dam, a land-use change or a climate regime shift between the periods makes the check unfair, in either direction.",
                     "a later period"),
    "another-site": ("another site or region",
                     "Another site checks the idea only where the idea should hold: a site unlike the working sites in climate, "
                     "instrument, processing or the way it was chosen tests something else.", "sites never opened"),
    "random": ("a random set aside",
               "Neighbouring sites and times are not independent: a random part of one record checks less than it seems, and "
               "least of all when the items are close in time or space to the working data.", "a random set aside"),
}
TOP_KEYS = ("what", "subject", "items", "releases", "files", "source", "note")  # a metadata file has these keys and no others
ITEM_KEYS = ("id", "site", "region", "series", "start", "end", "time", "date", "release", "version", "count", "lat", "lon", "name", "note")
TEXT_ITEM_KEYS = ("id", "site", "region", "series", "release", "version", "name", "note")
RELEASE_KEYS = ("name", "date", "cadence", "after", "per_period", "expected_items", "expected_count", "note")
FILE_KEYS = ("name", "sha256", "rows", "note")                                # a file the items are in, by its checksum
CADENCES = {"daily": (0, 1), "weekly": (0, 7), "monthly": (1, 0), "quarterly": (3, 0), "yearly": (12, 0)}  # (months, days) a period lasts
SHA256 = re.compile(r"^[0-9a-f]{64}$")
NUMERIC_ITEM_KEYS = ("lat", "lon")                                            # a position is metadata, not a measurement
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ACTOR = re.compile(r"(human|agent):[A-Za-z0-9_.@/-]+")
PLACEHOLDERS = ("human:you", "human:name", "human:id", "agent:name", "agent:id")
RECORD = "fresh-data.jsonl"
NOT_COMPUTED = ("the power of the plan's rules at this size. This tool counts; it does not know the method. The method's "
                "known-answer tests are where power is measured: run them on synthetic cases of this size before the lock "
                "(for the built-in gain method, `methods/gain/known_answer_tests.py --passes N`) and compare")
DRAW = "every item ranked by the sha256 of the seed, a line break and the item's identifier; the first k taken"
DRAWN_AT = ("the opening, after the lock: the seed is the sha256 of `science-factory random set aside`, the merge commit GitHub created "
            "for the lock request (as the platform says when asked then) and this proposal's sha256, each on its own line")
VARIABILITY = (". Nor does it use the record's own variability: that is a measured value, which a metadata file never holds and a "
               "proposal never reads. Take it from the working data in the method's known-answer tests, at the size counted here")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str | None:
    p = Path(p)
    return sha_bytes(p.read_bytes()) if p.is_file() else None


def subject_key(subject) -> str:
    """The subject written one way, so that two spellings of the same keys and values match (case and spacing)."""
    if not isinstance(subject, dict):
        return json.dumps(" ".join(str(subject).split()).casefold())
    return json.dumps({" ".join(str(k).split()).casefold(): " ".join(str(v).split()).casefold() for k, v in subject.items()}, sort_keys=True)


# ---- metadata, and nothing else ----------------------------------------------------
def read_metadata(path) -> dict:
    """The one file this tool reads to make a proposal. It is metadata only: what exists, never what was measured.
    Any key the form does not have is refused, because a field nobody named may hold values."""
    f = Path(path)
    if not f.is_file():
        raise Refused(f"`--metadata {path}` names no file")
    raw = f.read_bytes()
    try:
        meta = json.loads(raw) if f.suffix.lower() == ".json" else yaml.safe_load(raw)
    except (ValueError, yaml.YAMLError):
        raise Refused(f"`--metadata {path}` is not JSON or YAML that parses")
    if not isinstance(meta, dict):
        raise Refused("a metadata file is a mapping with `subject` and `items`")
    other = sorted(set(map(str, meta)) - set(TOP_KEYS))
    if other:
        raise Refused(f"`{other[0]}` is not a key of a metadata file (it has {', '.join(TOP_KEYS)}): this looks like data, not a "
                      "description of data. A proposal is made from metadata only: identifiers, sites, regions, dates, releases "
                      "and counts, never a measured value")
    if not isinstance(meta.get("subject"), dict) or not meta["subject"]:
        raise Refused("`subject` says what the data is about, as key: value (the same keys a later plan's `pair` carries)")
    items = meta.get("items")
    if not isinstance(items, list) or not items:
        raise Refused("`items` lists what data exists, one mapping for each item (a site, a granule, a month of passes)")
    ids = set()
    for n, it in enumerate(items, 1):
        if not isinstance(it, dict):
            raise Refused(f"item {n} is not a mapping")
        bad = sorted(set(map(str, it)) - set(ITEM_KEYS))
        if bad:
            raise Refused(f"item {n} has the key `{bad[0]}`, which is not metadata this tool knows ({', '.join(ITEM_KEYS)}). A field "
                          "it does not know may be a measured value, and a proposal never reads one")
        if not isinstance(it.get("id"), str) or not it["id"].strip():
            raise Refused(f"item {n} has no `id`: each item is named, so that a set aside can say which items it holds")
        if it["id"] in ids:
            raise Refused(f"the identifier `{it['id']}` is given twice")
        ids.add(it["id"])
        for k in TEXT_ITEM_KEYS:
            if k in it and not isinstance(it[k], str):
                raise Refused(f"item {it['id']}: `{k}` is text")
        for k in ("start", "end", "time", "date"):
            if k in it and not (isinstance(it[k], (str, dt.date)) and DATE.fullmatch(str(it[k]))):
                raise Refused(f"item {it['id']}: `{k}` is a date written YYYY-MM-DD")
        if "count" in it and not (isinstance(it["count"], int) and not isinstance(it["count"], bool) and it["count"] >= 0):
            raise Refused(f"item {it['id']}: `count` is a whole number of observations, never a measured value")
        for k in NUMERIC_ITEM_KEYS:
            if k in it and not (isinstance(it[k], (int, float)) and not isinstance(it[k], bool)):
                raise Refused(f"item {it['id']}: `{k}` is a number (a position)")
    for r in meta.get("releases") or []:
        if not isinstance(r, dict) or not isinstance(r.get("name"), str) or set(map(str, r)) - set(RELEASE_KEYS):
            raise Refused(f"each entry of `releases` is a mapping with `name` and at most {', '.join(RELEASE_KEYS)}")
        if "cadence" in r and r["cadence"] not in CADENCES:
            raise Refused(f"release {r['name']}: `cadence` is one of {', '.join(CADENCES)}")
        for k in ("date", "after"):
            if k in r and not (isinstance(r[k], (str, dt.date)) and DATE.fullmatch(str(r[k]))):
                raise Refused(f"release {r['name']}: `{k}` is a date written YYYY-MM-DD")
        for k in ("per_period", "expected_items", "expected_count"):
            if k in r and not (isinstance(r[k], int) and not isinstance(r[k], bool) and r[k] >= 0):
                raise Refused(f"release {r['name']}: `{k}` is a whole number")
    for fl in meta.get("files") or []:
        if (not isinstance(fl, dict) or set(map(str, fl)) - set(FILE_KEYS) or not isinstance(fl.get("name"), str)
                or not SHA256.fullmatch(str(fl.get("sha256") or ""))):
            raise Refused(f"each entry of `files` is a mapping with `name` and `sha256` (64 hexadecimal digits), and at most {', '.join(FILE_KEYS)}")
        if "rows" in fl and not (isinstance(fl["rows"], int) and not isinstance(fl["rows"], bool) and fl["rows"] >= 0):
            raise Refused(f"file {fl['name']}: `rows` is a whole number")
    return {"meta": meta, "sha256": sha_bytes(raw), "path": str(f.resolve())}


def span(it: dict) -> tuple | None:
    first = it.get("start") or it.get("time") or it.get("date")
    last = it.get("end") or it.get("time") or it.get("date")
    return (str(first), str(last)) if first and last else None


def last_date(items: list) -> str | None:
    """The last date the metadata lists: where the data as it stands ends."""
    ends = [s[1] for s in map(span, items) if s]
    return max(ends) if ends else None


def add_period(day: dt.date, cadence: str, n: int) -> dt.date:
    """The day n periods of a cadence after a day (a month after 31 January is the last day of February)."""
    months, days = CADENCES[cadence]
    if not months:
        return day + dt.timedelta(days=days * n)
    m = day.month - 1 + months * n
    y, m = day.year + m // 12, m % 12 + 1
    last = (dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)).day
    return dt.date(y, m, min(day.day, last))


def series_of(it: dict) -> str:
    return str(it.get("series") or it.get("site") or it["id"])


def draw(seed: str, population: list, k: int) -> list:
    """The random set aside: deterministic in the seed and the population, and in nothing else (not the order of the file)."""
    ranked = sorted(set(population), key=lambda u: hashlib.sha256(f"{seed}\n{u}".encode()).hexdigest())
    return sorted(ranked[:k])


def seed_at_the_lock(merge_commit: str, proposal_sha256: str) -> str:
    """The seed of a random set aside: from the merge commit of the lock request and the proposal, nothing else."""
    if not re.fullmatch(r"[0-9a-f]{40,64}", str(merge_commit)) or not re.fullmatch(r"[0-9a-f]{64}", str(proposal_sha256)):
        raise Refused("a random set aside is drawn from the lock's merge commit (its full checksum) and the proposal's sha256")
    return sha_bytes(f"science-factory random set aside\n{merge_commit}\n{proposal_sha256}".encode())


def draw_at_the_lock(p: dict, merge_commit: str, proposal_sha256: str) -> dict:
    """The members of a random set aside, drawn from the lock's merge commit: {seed, members, k, of}."""
    d, rule = p.get("draw") or {}, p.get("rule") or {}
    seed = seed_at_the_lock(merge_commit, proposal_sha256)
    return {"seed": seed, "merge_commit": merge_commit, "proposal_sha256": proposal_sha256, "k": int(rule.get("k") or 0),
            "of": len(d.get("drawn_from") or []), "members": draw(seed, list(d.get("drawn_from") or []), int(rule.get("k") or 0))}


def observations(items: list) -> int | None:
    return sum(it["count"] for it in items) if items and all("count" in it for it in items) else None


# ---- the proposal ----------------------------------------------------------------
def propose(a) -> dict:
    """Make a proposal. Returns {proposal, seed or None}; writes nothing. Reads the metadata file and nothing else."""
    if a.kind not in KINDS:
        raise Refused(f"`--kind` is one of {', '.join(KINDS)}")
    for name, text in (("--what", a.what), ("--why", a.why), ("--unfair", a.unfair)):
        if not str(text or "").strip():
            raise Refused(f"`{name}` is written in words: " + {"--what": "exactly what data is kept for the check",
                                                                 "--why": "why that data suits the question",
                                                                 "--unfair": "what would make it unfair as a check (a regime change, "
                                                                             "a new sensor, a site unlike the others)"}[name])
    if not ACTOR.fullmatch(str(a.by or "")) or str(a.by).lower() in PLACEHOLDERS:
        raise Refused("`--by` is human:<id> or agent:<id>, the actor's own name")
    if str(a.by).startswith("agent:") and not str(a.model or "").strip():
        raise Refused("an agent says which model it is: pass --model <the model's name>")
    got = read_metadata(a.metadata)
    meta = got["meta"]
    items = meta["items"]
    rule, fresh, working, neither, members, seed, population = {}, [], [], [], [], None, []
    explore = ["--how", KINDS[a.kind][2]]
    if a.kind == "later-period":
        if not (a.from_ and DATE.fullmatch(a.from_)) or (a.until and not DATE.fullmatch(a.until)):
            raise Refused("a later period starts on a date: `--from YYYY-MM-DD`, and may end on one (`--until YYYY-MM-DD`)")
        if a.until and a.until < a.from_:
            raise Refused("`--until` is before `--from`")
        rule = {"from": a.from_, "until": a.until}
        for it in items:
            s = span(it)
            if s is None:
                raise Refused(f"item {it['id']} has no dates (`start` and `end`, or `time`): a later period is chosen by dates")
            if s[0] >= a.from_ and (not a.until or s[1] <= a.until):
                fresh.append(it)
            elif s[1] < a.from_:
                working.append(it)
            else:
                neither.append(it)
        members = [it["id"] for it in fresh]
        explore += ["--set-aside-window", f"{a.from_}:{a.until or ''}"]
    elif a.kind == "another-site":
        sites = [s.strip() for s in (a.sites or "").split(",") if s.strip()]
        regions = [s.strip() for s in (a.regions or "").split(",") if s.strip()]
        if not sites and not regions:
            raise Refused("another site or region names it: `--sites a,b` or `--regions r`")
        rule = {"sites": sites, "regions": regions}
        for it in items:
            (fresh if (it.get("site") in sites or it.get("region") in regions) else working).append(it)
        members = sorted({it.get("site") or it["id"] for it in fresh})
        explore += ["--set-aside-sites", ",".join(members)]
    elif a.kind == "next-release":
        if not str(a.release or "").strip():
            raise Refused("the next release is named: `--release NAME`, as the provider names it")
        name = a.release.strip()
        declared = [r for r in meta.get("releases") or [] if r.get("name") == name]
        if not declared:
            raise Refused(f"the release `{name}` is not declared in the metadata's `releases`: a release set aside is one the "
                          "metadata says is coming (its name, and its cadence or its date)")
        fresh = [it for it in items if it.get("release") == name]
        working = [it for it in items if it.get("release") != name]
        # The data as it stands: the release is what comes after its last date. A release that arrives as new rows of the
        # same file carries no mark of its own, so the cut-off and the files' checksums are what the start binds.
        cut = str(declared[0].get("after") or last_date(working) or "")
        if not cut:
            raise Refused("a release set aside is fixed by the last date of the data as it stands, and no item of the working data "
                          "has a date (`start` and `end`, `time` or `date`) and the release no `after`: the metadata cannot fix it")
        later = [it["id"] for it in working if span(it) and span(it)[1] > cut]
        if later:
            raise Refused(f"the release `{name}` comes after {cut}, and the metadata lists working data after that ({later[0]})")
        rule = {"release": name, "cut_off": cut, "files": {fl["name"]: fl["sha256"] for fl in meta.get("files") or []}}
        for k, v in (("cadence", declared[0].get("cadence")), ("expected_on", declared[0].get("date"))):
            if v:  # the confirming study reads these at its opening, to say it is waiting for the release
                rule[k] = str(v)
        if a.periods is not None:
            cadence = declared[0].get("cadence")
            if not cadence:
                raise Refused(f"`--periods {a.periods}` counts periods of the release's cadence, and `{name}` declares none in the metadata")
            if a.periods < 1:
                raise Refused("`--periods` is a whole number of periods, one or more")
            first = dt.date.fromisoformat(cut) + dt.timedelta(days=1)
            final = add_period(first, cadence, a.periods) - dt.timedelta(days=1)
            months, days = CADENCES[cadence]
            reach = add_period(dt.date.fromisoformat(cut), cadence, -1).isoformat()
            going = sorted({series_of(it) for it in working if span(it) and span(it)[1] > reach})
            per = declared[0].get("per_period")
            rule["periods"] = {"n": a.periods, "cadence": cadence, "from": first.isoformat(), "until": final.isoformat(),
                               "per_period": per if per is not None else len(going),
                               "per_period_from": "the release's `per_period`" if per is not None else
                               "the series whose items reach the last period before the cut-off: " + (", ".join(going) or "none")}
        members = [it["id"] for it in fresh]
        explore += ["--set-aside-release", name, "--release-cut-off", cut]
    else:  # random
        f = 0.2 if a.fraction is None else a.fraction
        if not 0 < f < 1:
            raise Refused("`--fraction` is between 0 and 1: the share of the items set aside")
        unit = a.draw_over or ("site" if all(it.get("site") for it in items) else "id")
        if unit not in ("site", "id"):
            raise Refused("`--draw-over` is site or id")
        if unit == "site" and not all(it.get("site") for it in items):
            raise Refused("a draw over sites needs a `site` on every item")
        population = sorted({it[unit] for it in items})
        k = max(1, round(f * len(population)))
        if k >= len(population):
            raise Refused(f"a set aside of {k} of {len(population)} leaves nothing to explore")
        members = []  # to be drawn at the lock, from what nobody here can choose; no seed is made
        rule = {"fraction": f, "draw_over": unit, "k": k, "of": len(population), "method": DRAW, "drawn_at": DRAWN_AT}
        working = list(items)  # until the draw, every item may still be drawn: an exploration cannot set any aside, nor explore one
        explore = []
    if not working and a.kind != "random":
        raise Refused("this proposal leaves no working data: everything the metadata lists would be kept unopened")
    if not fresh and a.kind not in ("next-release", "random"):
        raise Refused("this proposal keeps nothing: no item in the metadata falls in it")
    releases = [r for r in meta.get("releases") or [] if r.get("name") == rule.get("release")]
    size = {"fresh_items": len(fresh), "working_items": len(working), "fresh_observations": observations(fresh),
            "working_observations": observations(working)}
    if neither:
        size["items_in_neither"] = [it["id"] for it in neither]
    if a.kind == "next-release" and not fresh:
        size["fresh_items"] = releases[0].get("expected_items") if releases else None
        size["fresh_observations"] = releases[0].get("expected_count") if releases else None
        size["expected_on"] = releases[0].get("date") if releases else None
        if rule.get("periods"):
            pr = rule["periods"]
            size["fresh_periods"] = pr["n"]
            size["fresh_observations"] = pr["n"] * pr["per_period"]
            size["fresh_window"] = {"start": pr["from"], "end": pr["until"]}
    size["computed_here"] = "counts of items and of observations (the `count` of each item), from the metadata" + (
        "; for a stated number of periods of the release's cadence, the periods and the observations they bring"
        if rule.get("periods") else "")
    size["not_computed_here"] = NOT_COMPUTED + (VARIABILITY if a.kind == "next-release" else "")
    held = {"pair": meta["subject"]}
    if a.kind == "later-period":
        held["window"] = {"start": a.from_, "end": a.until or "CHOOSE: the last date of the later period"}
    proposal = {
        "says": "a proposal of the fresh data for a confirming study, made from metadata only; written by tools/fresh_data.py",
        "kind": a.kind, "kind_in_words": KINDS[a.kind][0],
        "what": " ".join(str(a.what).split()), "why_it_suits": " ".join(str(a.why).split()),
        "what_would_make_it_unfair": " ".join(str(a.unfair).split()), "caution": KINDS[a.kind][1],
        "subject": meta["subject"], "rule": rule, "members": members, "test_size": size,
        "metadata": {"file": os.path.basename(got["path"]), "sha256": got["sha256"], "items": len(items),
                     "fields": sorted({k for it in items for k in it}), "what": meta.get("what")},
        "set_aside_with": explore, "held_out_for_the_plan": held,
        "proposed": {"by": a.by, "model": a.model, "at": now(), "tool_sha256": sha_file(TOOL)},
    }
    if a.kind == "random":
        size.update(fresh_items=rule["k"], working_items=None, fresh_observations=None, working_observations=None,
                    to_be_drawn=f"{rule['k']} of {rule['of']} ({unit}s), drawn at the lock")
        proposal["draw"] = {"at": "the lock", "drawn_from": population, "seed_from": DRAWN_AT,
                            "not_before_the_lock": "no seed exists before the lock request is merged, so nobody can draw again until the members suit them"}
    return {"proposal": proposal, "seed": None}


# ---- describe: the metadata of one long file, from its date column ------------------
WHEN = re.compile(r"^(\d{4})(?:-(\d{1,2})(?:-(\d{1,2}))?)?$")   # a year, a month (YYYY-MM) or a day (YYYY-MM-DD)


def span_of_cell(text: str) -> tuple | None:
    """The first and last day a date cell stands for: a day, a whole month or a whole year."""
    m = WHEN.fullmatch(str(text).strip())
    if not m:
        return None
    try:
        y, mo, d = int(m.group(1)), int(m.group(2) or 0), int(m.group(3) or 0)
        if d:
            day = dt.date(y, mo, d)
            return day, day
        if mo:
            return dt.date(y, mo, 1), add_period(dt.date(y, mo, 1), "monthly", 1) - dt.timedelta(days=1)
        return dt.date(y, 1, 1), dt.date(y, 12, 31)
    except ValueError:
        return None


def describe(path, date_column: str, series_column: str | None, period: str) -> dict:
    """The items of one CSV file by series and period, with counts, and the file by checksum. Only the date column and the
    series column are kept; every other column is read past and kept nowhere, so the metadata holds no measured value."""
    import csv
    f = Path(path)
    if not f.is_file():
        raise Refused(f"`--csv {path}` names no file")
    if period not in ("year", "month"):
        raise Refused("`--period` is year or month: one item for each series and period")
    raw = f.read_bytes()
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig", errors="replace"))))
    if not rows:
        raise Refused(f"{f.name} is empty")
    head = [c.strip() for c in rows[0]]
    for col in [date_column] + ([series_column] if series_column else []):
        if col not in head:
            raise Refused(f"`{col}` is not a column of {f.name} (its header names {', '.join(head)})")
    di, si = head.index(date_column), (head.index(series_column) if series_column else None)
    groups, bad, names = {}, 0, set()
    for r in rows[1:]:
        if not any(c.strip() for c in r):
            continue
        got = span_of_cell(r[di]) if di < len(r) else None
        if got is None:
            bad += 1
            continue
        name = r[si].strip() if si is not None and si < len(r) else ""
        if si is not None:
            try:
                float(name)
                raise Refused(f"the column `{series_column}` holds numbers ({name!r}): a series is named, not measured, so this "
                              "is not a series column, and nothing was written")
            except ValueError:
                pass
            if not name:
                bad += 1
                continue
            names.add(name)
        key = (name, got[0].strftime("%Y" if period == "year" else "%Y-%m"))
        first, final, n = groups.get(key, (got[0], got[1], 0))
        groups[key] = (min(first, got[0]), max(final, got[1]), n + 1)
    if bad:
        raise Refused(f"{bad} row(s) of {f.name} have no date in `{date_column}` that reads as YYYY, YYYY-MM or YYYY-MM-DD"
                      + (f", or no name in `{series_column}`" if series_column else "") + ": this file cannot be described this way")
    if len(names) > 100:
        raise Refused(f"`{series_column}` names {len(names)} series: more than a hundred is a column of values, not of names")
    if not groups:
        raise Refused(f"{f.name} has no rows to describe")
    items = []
    for (name, label), (first, final, n) in sorted(groups.items()):
        it = {"id": f"{name}-{label}" if name else label}
        if name:
            it["series"] = name
        items.append({**it, "start": first.isoformat(), "end": final.isoformat(), "count": n})
    return {"items": items, "file": {"name": f.name, "sha256": sha_bytes(raw), "rows": sum(g[2] for g in groups.values())},
            "series": sorted(names)}


def cmd_describe(a) -> None:
    out = Path(os.path.abspath(a.out))
    if out.suffix.lower() not in (".yaml", ".yml"):
        raise Refused("`--out` is the metadata file to write, a .yaml file")
    if out.exists():
        raise Refused(f"{out} already exists: describe writes a new metadata file and never changes one")
    subject = {}
    for part in str(a.subject or "").split(","):
        k, eq, v = part.partition("=")
        if not eq or not k.strip() or not v.strip():
            raise Refused("`--subject` is key=value,key=value: what the data is about, the keys a later plan's `pair` carries")
        subject[k.strip()] = v.strip()
    if a.release and a.cadence not in CADENCES:
        raise Refused(f"a release this file will grow by has a cadence: `--cadence` is one of {', '.join(CADENCES)}")
    got = describe(a.csv, a.date_column, a.series_column, a.period)
    meta = {"what": " ".join(str(a.what).split()), "subject": subject,
            "source": f"written by tools/fresh_data.py describe from the column `{a.date_column}`"
                      + (f" and the series column `{a.series_column}`" if a.series_column else "")
                      + f" of {got['file']['name']}; no other column was kept, and no measured value is here",
            "files": [got["file"]], "items": got["items"]}
    if a.release:
        meta["releases"] = [{"name": a.release, "cadence": a.cadence, "after": max(it["end"] for it in got["items"]),
                             "note": f"the {a.cadence} update that adds rows after the last date of {got['file']['name']} as it stands"}]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("# Metadata only, written by tools/fresh_data.py describe: what exists, never a measured value.\n"
                   + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=110))
    read_metadata(out)  # what it wrote is a metadata file the proposing step accepts
    print(f"metadata written: {out}: {len(got['items'])} item(s) by {a.period}" + (f" for {len(got['series'])} series ({', '.join(got['series'])})" if got["series"] else "")
          + f", {got['file']['rows']} rows, the last date {max(it['end'] for it in got['items'])}, {got['file']['name']} sha256 {got['file']['sha256'][:16]}"
          + (f"; release `{a.release}` declared, {a.cadence}" if a.release else ""))


def seed_path(proposal_path: Path) -> Path:
    return Path(proposal_path).with_suffix(".seed")


def record_lines(studies: Path) -> list:
    out, f = [], Path(studies) / RECORD
    if f.is_file():
        for ln in f.read_text().splitlines():
            try:
                e = json.loads(ln)
            except ValueError:
                continue
            if isinstance(e, dict):
                out.append(e)
    return out


def cmd_propose(a) -> None:
    out = Path(os.path.abspath(a.out))
    if out.suffix.lower() not in (".yaml", ".yml"):
        raise Refused("`--out` is the proposal's path, a .yaml file")
    if out.exists() or seed_path(out).exists():
        raise Refused(f"{out} (or its .seed) already exists: a proposal is written once, and a second proposal is a new file on the record")
    studies = Path(os.path.abspath(a.studies))
    got = propose(a)
    p, seed = got["proposal"], got["seed"]
    out.parent.mkdir(parents=True, exist_ok=True)
    body = ("# A proposal of the fresh data for a confirming study, written by tools/fresh_data.py from metadata only.\n"
            "# Do not edit it: the record beside the studies holds its checksum, and the study tool and the exploring tool\n"
            "# refuse a proposal that is not on it. A new choice is a new proposal.\n"
            + yaml.safe_dump(p, sort_keys=False, allow_unicode=True, width=110))
    out.write_text(body)
    studies.mkdir(parents=True, exist_ok=True)
    line = {"kind": "fresh-data.proposed", "fresh_kind": p["kind"], "subject": subject_key(p["subject"]), "proposal_sha256": sha_bytes(body.encode()),
            "seed_sha256": (p.get("draw") or {}).get("seed_sha256"), "members": len(p["members"]), "by": p["proposed"]["by"],
            "model": p["proposed"]["model"], "at": p["proposed"]["at"], "file": os.path.relpath(out, studies)}
    with (studies / RECORD).open("a") as f:
        f.write(json.dumps(line, sort_keys=True) + "\n")
    same = [ln for ln in record_lines(studies) if ln.get("subject") == line["subject"]]
    print("\n".join(in_words(p)))
    print(f"\nproposal written: {out}" + (" (a random set aside: to be drawn at the lock, from the merge commit; no seed exists)" if p["kind"] == "random" else "")
          + f". On the record beside the studies ({studies / RECORD}): proposal {len(same)} for this subject.")
    if p["kind"] == "random":
        print("A random set aside is for a confirming study's plan (`data.held_out.fresh_data`): an exploration cannot set aside members "
              "that are drawn only at the lock, so it cannot start on this proposal")
        return
    print("To set it aside when the exploration starts: uv run tools/explore.py start ... " + " ".join(
        w if re.fullmatch(r"[A-Za-z0-9_.:,/@=-]+", w) else json.dumps(w) for w in p["set_aside_with"]) + f" --fresh-data {out}")


def load(path) -> dict:
    f = Path(path)
    try:
        p = yaml.safe_load(f.read_text())
    except (OSError, yaml.YAMLError):
        raise Refused(f"{path} is not a proposal that can be read")
    if not isinstance(p, dict) or p.get("kind") not in KINDS or not isinstance(p.get("members"), list):
        raise Refused(f"{path} is not a proposal written by tools/fresh_data.py")
    return p


def on_record(path, studies) -> dict:
    """Is this proposal file, byte for byte, one the tool recorded beside these studies? And how many proposals does
    that record hold for the same subject?"""
    p = load(path)
    sha = sha_file(Path(path))
    lines = record_lines(Path(studies))
    mine = [ln for ln in lines if ln.get("proposal_sha256") == sha]
    same = [ln for ln in lines if ln.get("subject") == subject_key(p.get("subject"))]
    return {"on_record": bool(mine), "sha256": sha, "for_this_subject": len(same),
            "position": (same.index(mine[0]) + 1) if mine and mine[0] in same else None}


def problems(path, studies=None, seed=None) -> list:
    """What is wrong with a proposal, in words; empty when nothing is. With `studies`, that it is on the record there.
    A random set aside draws nothing before the lock: one that lists members, names a seed or has a seed file beside it
    was drawn where its proposer could draw again, and is refused; so is a seed handed in."""
    p, out = load(path), []
    for k in ("what", "why_it_suits", "what_would_make_it_unfair"):
        if not str(p.get(k) or "").strip():
            out.append(f"`{k}` is not written")
    if studies is not None and not on_record(path, studies)["on_record"]:
        out.append(f"this proposal is not on the record beside the studies ({Path(studies) / RECORD}), byte for byte: it was not "
                   "written by the tool there, or it was edited afterwards")
    if p["kind"] == "next-release" and not DATE.fullmatch(str((p.get("rule") or {}).get("cut_off") or "")):
        out.append("this proposal of the next release fixes no cut-off: nothing binds the data as it stands, so the release could "
                   "arrive in the working data as plain dated rows. Propose again, from metadata that declares the release")
    if p["kind"] == "random":
        d = p.get("draw") or {}
        if p.get("members") or d.get("seed_sha256") or seed_path(Path(path)).exists() or seed is not None:
            out.append("this random set aside was drawn when its proposal was written, from a seed its proposer could make again and again "
                       "until the members suited them (or a seed is handed in): propose again with this tool, which draws nothing until "
                       "the lock, from the merge commit GitHub creates for the lock request")
        if d.get("at") != "the lock" or not isinstance(d.get("drawn_from"), list) or not d.get("drawn_from"):
            out.append("this random set aside does not name the items it will be drawn from, to be drawn at the lock")
    return out


def in_words(p: dict, revealed: str | None = None, record: dict | None = None) -> list:
    """A proposal as a person reads it before approving the lock."""
    size = p.get("test_size") or {}
    def n(v):  # noqa: E306
        return "not given in the metadata" if v is None else str(v)
    rule = p.get("rule") or {}
    lines = [f"**What kind of fresh data.** {str(p.get('kind_in_words', p.get('kind'))).capitalize()}.", "",
             f"**Exactly what.** {p.get('what')}", "",
             f"**Why it suits the question.** {p.get('why_it_suits')}", "",
             f"**What would make it unfair.** {p.get('what_would_make_it_unfair')} The tool adds, for this kind: {p.get('caution')}", ""]
    if p.get("kind") == "next-release" and not p.get("members"):
        pr = rule.get("periods")
        lines += [f"**How large a test it allows.** The release `{rule.get('release')}` is not out: "
                  + (f"for the {pr['n']} {pr['cadence']} period(s) stated, {pr['from']} to {pr['until']}, {n(size.get('fresh_observations'))} "
                     f"observations ({pr['per_period']} a period, from {pr['per_period_from']})" if pr else
                     f"expected items {n(size.get('fresh_items'))}, expected observations {n(size.get('fresh_observations'))}"
                     + (f", on {size['expected_on']}" if size.get("expected_on") else "")
                     + ". Give `--periods N` to have the size of N periods of its cadence counted")
                  + f". Working data: {n(size.get('working_items'))} items, {n(size.get('working_observations'))} observations."]
    else:
        lines += [f"**How large a test it allows.** Fresh: {n(size.get('fresh_items'))} items, {n(size.get('fresh_observations'))} observations. "
                  f"Working: {n(size.get('working_items'))} items, {n(size.get('working_observations'))} observations."
                  + (f" In neither (they cross the boundary, and nothing protects them): {', '.join(size['items_in_neither'])}." if size.get("items_in_neither") else "")]
    lines += [f"Counted here: {size.get('computed_here')}. Not computed here: {size.get('not_computed_here')}.", ""]
    if p.get("kind") == "later-period":
        what = f"from {rule.get('from')}" + (f" to {rule.get('until')}" if rule.get("until") else " onward")
    elif p.get("kind") == "another-site":
        what = "the sites " + ", ".join(rule.get("sites") or []) + (("; the regions " + ", ".join(rule["regions"])) if rule.get("regions") else "")
    elif p.get("kind") == "next-release":
        what = f"the release `{rule.get('release')}`, after the cut-off {rule.get('cut_off') or 'NOT FIXED'}" + (
            "; the working data is bound at the start as it stands, by checksum, and the metadata gives "
            + ", ".join(f"{k} (sha256 {str(v)[:12]})" for k, v in (rule.get("files") or {}).items()) if rule.get("files") else
            "; the working data is bound at the start as it stands, by checksum")
    else:
        what = f"{rule.get('k')} of {rule.get('of')} ({'sites' if rule.get('draw_over') == 'site' else 'items'}), to be drawn at the lock"
    lines += [f"**The members.** {what}: " + (", ".join(map(str, p.get("members") or [])) or ("to be drawn at the lock" if p.get("kind") == "random"
                                                                                              else "none listed yet")) + ".", ""]
    prop = p.get("proposed") or {}
    meta = p.get("metadata") or {}
    lines += [f"**Who chose it, and from what.** Proposed by {prop.get('by')}" + (f" (model {prop.get('model')})" if prop.get("model") else "")
              + f" at {prop.get('at')}, from the metadata file {meta.get('file')} (sha256 {str(meta.get('sha256'))[:16]}, {meta.get('items')} items, "
              f"fields {', '.join(meta.get('fields') or [])}). No measured value was read: the tool reads only that file, and refuses one with "
              "any other field."]
    if p.get("kind") == "random":
        d = p.get("draw") or {}
        lines += ["", f"**Nobody can choose the members.** They are to be drawn at the lock: {rule.get('k')} of the {len(d.get('drawn_from') or [])} "
                  f"items this proposal names, at {rule.get('drawn_at') or DRAWN_AT}. {rule.get('method')}. No seed exists before the lock "
                  "request is merged, so nobody can draw again until the members suit them; the opening records the commit, the seed and the "
                  "members, and anybody can draw again from them (`uv run tools/fresh_data.py reveal --proposal <this proposal> "
                  "--merge-commit <the commit>`). A practice lock is typed, not merged: its draw comes from its own log entry, which whoever "
                  "typed it could have made again, so a practice study's draw could be chosen, and it says so."]
    if record is not None:
        lines += ["", f"**On the record.** " + ("This proposal is on the record beside the studies, byte for byte" if record.get("on_record")
                                                else "THIS PROPOSAL IS NOT ON THE RECORD beside the studies")
                  + f"; the record holds {record.get('for_this_subject')} proposal(s) for this subject"
                  + (f", and this is number {record['position']}" if record.get("position") else "") + "."]
    return lines


def cmd_show(a) -> None:
    p = load(a.proposal)
    rec = on_record(a.proposal, a.studies) if a.studies else None
    print("\n".join(in_words(p, record=rec)))


def cmd_reveal(a) -> None:
    p = load(a.proposal)
    if p["kind"] != "random":
        raise Refused("only a random set aside is drawn: this proposal is " + p["kind_in_words"])
    if getattr(a, "seed_file", None):
        raise Refused("a seed handed in is refused: a random set aside is drawn from the lock's merge commit and the proposal, and from "
                      "nothing anybody chooses. Give `--merge-commit` (the opening records it) to draw again as the opening drew")
    found = problems(a.proposal)
    if found:
        raise Refused("; ".join(found))
    if not getattr(a, "merge_commit", None):
        raise Refused("the members are drawn at the lock: give `--merge-commit` (the commit GitHub created when the lock request was "
                      "merged, which the opening records) to draw them as the opening did")
    got = draw_at_the_lock(p, a.merge_commit.strip().lower(), sha_file(Path(a.proposal)))
    print(json.dumps(got, indent=1))


def first_event(log: Path) -> tuple:
    """(the event that started the work the proposal serves, the first look or test after it), from a log file."""
    events = [json.loads(ln) for ln in Path(log).read_text().splitlines() if ln.strip()]
    start = next((e for e in events if e.get("kind") in ("exploration.started", "study.started")), None)
    first = next((e for e in events if e.get("kind") in ("look.run", "look.refused", "test.run", "rehearsal.run")), None)
    return start, first


def cmd_check(a) -> None:
    found = problems(a.proposal, a.studies)
    p = load(a.proposal)
    said = []
    if a.log:
        start, first = first_event(Path(a.log))
        at = (p.get("proposed") or {}).get("at") or ""
        if start is None:
            found.append("the log given has no start event")
        else:
            if at > str(start.get("at")):
                found.append(f"the proposal was written at {at}, after the work it serves started ({start.get('at')}): it may have been "
                             "chosen after looking")
            fd = ((start.get("data") or {}).get("set_aside") or {}).get("fresh_data")
            if start.get("kind") == "exploration.started" and (not fd or fd.get("sha256") != sha_file(Path(a.proposal))):
                found.append("the exploration did not set this proposal aside (`explore.py start --fresh-data`)")
            said.append(f"written at {at}; the work started at {start.get('at')}" + (f"; the first look or test at {first.get('at')}" if first else "; nothing looked at yet"))
    for q in found:
        print("fresh-data check:", q)
    print(f"fresh-data check: {'PASS' if not found else 'FAIL'} ({p['kind_in_words']}; " + ("; ".join(said) or "no log given") + ")")
    if found:
        raise Refused(f"{len(found)} problem(s) with the proposal: " + "; ".join(found))


# ---- self-test ---------------------------------------------------------------------
class A:
    def __init__(self, **k):  # the arguments of a command, as the parser gives them
        self.__dict__.update({"from_": None, "until": None, "sites": None, "regions": None, "release": None, "fraction": None, "periods": None,
                              "draw_over": None, "model": "selftest-model", "by": "agent:analysis", "studies": None, **k})


def _metadata(tmp: Path) -> Path:
    items = []
    for site in ("S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10"):
        for year in (2023, 2024):
            items.append({"id": f"{site}-{year}", "site": site, "region": "north" if site < "S06" else "south",
                          "start": f"{year}-01-01", "end": f"{year}-12-31", "count": 40 + int(site[1:]), "release": "v1"})
    m = tmp / "metadata.json"
    m.write_text(json.dumps({"what": "test sites", "subject": {"record": "synthetic"}, "items": items,
                             "releases": [{"name": "v2", "date": "2027-03-01", "expected_items": 20, "expected_count": 900}]}))
    return m


def selftest() -> int:
    results = []

    def check(name, ok):
        results.append((name, bool(ok)))

    def refused(fn, *args):
        try:
            fn(*args)
        except Refused as r:
            return str(r)
        return ""

    tmp = Path(tempfile.mkdtemp(prefix="fresh-data-selftest-")).resolve()
    quiet = contextlib.redirect_stdout(io.StringIO())  # what the commands print is not the self-test's report
    try:
        quiet.__enter__()
        meta = _metadata(tmp)
        studies = tmp / "studies"
        base = dict(metadata=str(meta), what="w", why="y", unfair="u", studies=str(studies))
        # what the proposing step may read
        values = tmp / "values.json"
        values.write_text(json.dumps({"subject": {"record": "synthetic"}, "items": [{"id": "a", "start": "2024-01-01", "end": "2024-01-02", "elevation": 3.2}]}))
        check("a file that carries a measured value (a key that is not metadata) is refused, and the key is named",
              "`elevation`" in refused(propose, A(kind="later-period", from_="2024-01-01", **{**base, "metadata": str(values)})))
        data = tmp / "record.json"
        data.write_text(json.dumps({"what": "a record", "window": {}, "units": "m", "rows": [{"t": "2024-01-01", "h": 1.0}]}))
        check("a data file passed as metadata is refused before anything is counted",
              "this looks like data" in refused(propose, A(kind="later-period", from_="2024-01-01", **{**base, "metadata": str(data)})))
        sneaky = tmp / "sneaky.json"
        sneaky.write_text(json.dumps({"subject": {"r": "s"}, "items": [{"id": "a", "start": "2024-01-01", "end": "2024-01-02", "count": 2.71}]}))
        check("a count that is not a whole number (a value in a count's place) is refused",
              "whole number" in refused(propose, A(kind="later-period", from_="2024-01-01", **{**base, "metadata": str(sneaky)})))
        opened = []

        def hook(event, args):
            if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
                mode = str(args[1] if len(args) > 1 and args[1] is not None else "r")
                if "r" in mode and "+" not in mode and "w" not in mode and "a" not in mode:
                    opened.append(os.path.realpath(os.fsdecode(args[0])))
        watching = {"on": False}
        sys.addaudithook(lambda e, a_: hook(e, a_) if watching["on"] else None)
        (tmp / "set-aside-values.json").write_text("{}")
        watching["on"] = True
        try:
            propose(A(kind="random", **base))
            propose(A(kind="later-period", from_="2024-01-01", **base))
        finally:
            watching["on"] = False
        own = [p for p in opened if not p.startswith((os.path.realpath(sys.prefix), os.path.realpath(sys.base_prefix)))
               and not p.endswith((".py", ".pyc", ".so"))]
        check("the proposing step opens one file to read, the metadata, and nothing beside it (watched by an audit hook)",
              own and set(own) == {str(meta.resolve())})
        # the words are required
        check("a proposal without the reason it suits the question, or without what would make it unfair, is refused",
              "`--why`" in refused(propose, A(kind="later-period", from_="2024-01-01", **{**base, "why": " "}))
              and "`--unfair`" in refused(propose, A(kind="later-period", from_="2024-01-01", **{**base, "unfair": ""})))
        check("an agent that does not say which model it is cannot propose",
              "--model" in refused(propose, A(kind="later-period", from_="2024-01-01", model=None, **base)))
        # the four kinds
        later = propose(A(kind="later-period", from_="2024-01-01", **base))["proposal"]
        check("a later period counts what it keeps and what is left to explore, from the metadata",
              later["test_size"]["fresh_items"] == 10 and later["test_size"]["working_items"] == 10
              and later["test_size"]["fresh_observations"] == sum(40 + i for i in range(1, 11))
              and later["set_aside_with"] == ["--how", "a later period", "--set-aside-window", "2024-01-01:"]
              and "Not computed here" in "\n".join(in_words(later)))
        site = propose(A(kind="another-site", regions="south", **base))["proposal"]
        check("another region keeps every item of that region, by site", site["members"] == ["S06", "S07", "S08", "S09", "S10"]
              and site["set_aside_with"][-1] == "S06,S07,S08,S09,S10")
        nxt = propose(A(kind="next-release", release="v2", **base))["proposal"]
        check("the next release keeps nothing that exists yet and gives the size the metadata expects, saying so",
              nxt["members"] == [] and nxt["test_size"]["fresh_items"] == 20 and "is not out" in "\n".join(in_words(nxt)))
        check("a proposal that would keep everything, or nothing, is refused",
              "no working data" in refused(propose, A(kind="later-period", from_="2020-01-01", **base))
              and "keeps nothing" in refused(propose, A(kind="later-period", from_="2030-01-01", **base)))
        # the random draw: at the lock, from the merge commit, and nobody's choice (A4-06)
        a1 = A(kind="random", fraction=0.3, out=str(tmp / "p" / "random.yaml"), **base)
        cmd_propose(a1)
        pfile = Path(a1.out)
        p = load(pfile)
        line = [ln for ln in record_lines(studies) if ln.get("proposal_sha256") == sha_file(pfile)][0]
        check("A4-06: a random set aside draws nothing when it is proposed: no members, no seed and no seed file; it names the items it "
              "will be drawn from and how many, to be drawn at the lock",
              p["members"] == [] and not seed_path(pfile).exists() and line["seed_sha256"] is None and line["members"] == 0
              and p["draw"]["at"] == "the lock" and p["rule"]["k"] == 3 and len(p["draw"]["drawn_from"]) == 10 and "seed_sha256" not in p["draw"])
        tries = []
        for i in range(6):
            ai = A(kind="random", fraction=0.2, out=str(tmp / f"try-{i}" / "p.yaml"), studies=str(tmp / f"try-{i}" / "studies"),
                   **{k: v for k, v in base.items() if k != "studies"})
            cmd_propose(ai)
            tries.append(load(Path(ai.out)))
        kept_hex = secrets.token_hex
        secrets.token_hex = lambda n=32: "0" * (2 * n)  # the fourth attack's choose.py: the randomness the tool once drew a seed from
        try:
            cmd_propose(A(kind="random", fraction=0.2, out=str(tmp / "chosen" / "p.yaml"), studies=str(tmp / "chosen" / "studies"),
                          **{k: v for k, v in base.items() if k != "studies"}))
        finally:
            secrets.token_hex = kept_hex
        chosen = load(tmp / "chosen" / "p.yaml")
        check("A4-06: proposing again and again gives nothing to choose from (six proposals, six times no members), and the randomness the "
              "tool once drew its seed from, replaced, changes nothing", all(x["members"] == [] for x in tries + [chosen])
              and all(x["draw"]["drawn_from"] == tries[0]["draw"]["drawn_from"] for x in tries + [chosen]))
        commit, other = "a" * 40, "b" * 40
        got = draw_at_the_lock(p, commit, sha_file(pfile))
        check("the members come from the lock's merge commit and the proposal alone: the same commit draws the same, another commit "
              "another, and the order of the metadata changes nothing",
              got == draw_at_the_lock(p, commit, sha_file(pfile)) and len(got["members"]) == 3
              and any(draw_at_the_lock(p, c * 40, sha_file(pfile))["members"] != got["members"] for c in "bcdef")
              and draw(got["seed"], list(reversed(p["draw"]["drawn_from"])), 3) == got["members"]
              and got["seed"] == seed_at_the_lock(commit, sha_file(pfile)) and got["seed"] != seed_at_the_lock(other, sha_file(pfile)))
        check("a random proposal on the record, still to be drawn, has no problems", problems(pfile, studies) == [])
        drawn_early = tmp / "p" / "drawn-early.yaml"
        drawn_early.write_text(yaml.safe_dump({**p, "members": ["S01", "S02", "S03"], "draw": {**p["draw"], "seed_sha256": "0" * 64}}))
        seed_path(drawn_early).write_text("0" * 64 + "\n")
        check("A4-06: a random set aside drawn when it was proposed (members listed, a seed recorded or beside it), as the tool once drew "
              "one, is refused: its proposer could draw again until the members suited them",
              any("drawn when its proposal was written" in q for q in problems(drawn_early)))
        check("A4-06: a seed handed in is refused, and so is a reveal with no merge commit; with it, the reveal draws as the opening does",
              "a seed handed in is refused" in refused(cmd_reveal, A(proposal=str(pfile), seed_file=str(seed_path(drawn_early)), merge_commit=commit))
              and "give `--merge-commit`" in refused(cmd_reveal, A(proposal=str(pfile), seed_file=None, merge_commit=None))
              and refused(cmd_reveal, A(proposal=str(pfile), seed_file=None, merge_commit=commit)) == ""
              and any("drawn when its proposal was written" in q for q in problems(pfile, seed="0" * 64)))
        a2 = A(kind="random", fraction=0.2, out=str(tmp / "p" / "random-2.yaml"), **base)
        cmd_propose(a2)
        check("a second proposal for the same subject is a new line on the record, and the record says how many there are",
              on_record(a2.out, studies) == {"on_record": True, "sha256": sha_file(Path(a2.out)), "for_this_subject": 2, "position": 2})
        check("a proposal is written once: the same path is refused", "already exists" in refused(cmd_propose, a2))
        words = "\n".join(in_words(p, record=on_record(pfile, studies)))
        check("in words, a random set aside says nobody can choose the members, that they are drawn at the lock from the merge commit, "
              "that a practice draw could be chosen, and where it stands on the record",
              "Nobody can choose the members" in words and "to be drawn at the lock" in words and "merge commit" in words
              and "could be chosen" in words and "number 1" in words and "{" not in words and "Nobody chose the members" not in words)
        # a release binds the data as it stands (found by the first real run of the factory)
        check("a release the metadata does not declare is refused: a set aside is a release the metadata says is coming",
              "not declared in the metadata" in refused(propose, A(kind="next-release", release="v9", **base)))
        check("the next release fixes the cut-off, the last date the metadata lists, and the start is told it",
              nxt["rule"]["cut_off"] == "2024-12-31" and nxt["set_aside_with"][-2:] == ["--release-cut-off", "2024-12-31"]
              and "after the cut-off 2024-12-31" in "\n".join(in_words(nxt)))
        old_kind = tmp / "p" / "old-release.yaml"
        old_kind.parent.mkdir(parents=True, exist_ok=True)
        old_kind.write_text(yaml.safe_dump({**nxt, "rule": {"release": "v2"}}))
        check("a proposal of the next release that fixes no cut-off (as the tool wrote one before) has a problem",
              any("fixes no cut-off" in q for q in problems(old_kind)))
        badfile = tmp / "badfile.json"
        badfile.write_text(json.dumps({"subject": {"r": "s"}, "files": [{"name": "a.csv", "sha256": "abc"}],
                                       "items": [{"id": "a", "start": "2024-01-01", "end": "2024-01-02"}]}))
        check("a file in the metadata is named with its sha256, 64 hexadecimal digits", "sha256" in refused(read_metadata, badfile))
        # a single long file released monthly, described from its date column
        csvf = tmp / "monthly.csv"
        csvf.write_text("Source,Year,Mean\n" + "".join(f"{src},{y}-{m:02d},{7 + m / 1000:.4f}\n" for src in ("NOAA", "NASA")
                                                        for y in (2023, 2024, 2025) for m in range(1, 13) if (y, src) != (2025, "NASA") and (y, m) <= (2025, 7)))
        cmeta = tmp / "described.yaml"
        cmd_describe(A(csv=str(csvf), date_column="Year", series_column="Source", period="year", subject="record=toy-temperature",
                       what="a toy monthly record", release="next-update", cadence="monthly", out=str(cmeta)))
        cm = yaml.safe_load(cmeta.read_text())
        check("describe writes one item for each series and year from the date column, with counts, the file by sha256 and the release with its cadence",
              [(i["id"], i["count"], i["end"]) for i in cm["items"] if i["series"] == "NOAA"] == [("NOAA-2023", 12, "2023-12-31"), ("NOAA-2024", 12, "2024-12-31"),
                                                                                                ("NOAA-2025", 7, "2025-07-31")]
              and cm["files"] == [{"name": "monthly.csv", "sha256": sha_file(csvf), "rows": 12 * 4 + 7}]
              and cm["releases"][0]["cadence"] == "monthly" and cm["releases"][0]["after"] == "2025-07-31")
        check("describe keeps no other column: no measured value is in the metadata it writes", "7.00" not in cmeta.read_text())
        num = tmp / "numeric.csv"
        num.write_text("Source,Year,Mean\nA,2024-01,0.5\n")
        check("describe refuses a series column that holds numbers: a series is named, not measured",
              "holds numbers" in refused(describe, num, "Year", "Mean", "year"))
        num.write_text("Source,Year,Mean\nA,January,0.5\n")
        check("describe refuses a file whose date column does not read as dates", "no date" in refused(describe, num, "Year", "Source", "year"))
        cbase = {**base, "metadata": str(cmeta)}
        lp = propose(A(kind="later-period", from_="2025-01-01", **cbase))["proposal"]
        check("a later period on a long series described by year works, without a derived copy of the metadata",
              lp["members"] == ["NOAA-2025"] and lp["test_size"]["fresh_observations"] == 7 and lp["test_size"]["working_items"] == 4)
        nr = propose(A(kind="next-release", release="next-update", periods=24, **cbase))["proposal"]
        check("the next release of a long series gives the size of a stated number of periods from its cadence, from the series still published",
              nr["test_size"]["fresh_periods"] == 24 and nr["test_size"]["fresh_observations"] == 24
              and nr["test_size"]["fresh_window"] == {"start": "2025-08-01", "end": "2027-07-31"} and "NOAA" in nr["rule"]["periods"]["per_period_from"]
              and nr["rule"]["files"] == {"monthly.csv": sha_file(csvf)})
        check("and says why it cannot use the record's own variability", "the record's own variability" in nr["test_size"]["not_computed_here"])
        check("the next release keeps the cadence the metadata declares in its rule, for the confirming study to count the periods it waits for",
              nr["rule"].get("cadence") == "monthly" and propose(A(kind="next-release", release="next-update", **cbase))["proposal"]["rule"].get("cadence") == "monthly")
        check("a number of periods for a release with no cadence is refused, and says why",
              "declares none" in refused(propose, A(kind="next-release", release="v2", periods=12, **base)))
        # the reviewer's check: written before the work started
        log = tmp / "log.jsonl"
        log.write_text(json.dumps({"kind": "exploration.started", "at": "2000-01-01T00:00:00Z", "data": {"set_aside": {}}}) + "\n")
        check("the reviewer's check finds a proposal written after the work it serves started",
              "after the work it serves started" in refused(cmd_check, A(proposal=str(pfile), studies=str(studies), log=str(log))))
    finally:
        quiet.__exit__(None, None, None)
        shutil.rmtree(tmp, ignore_errors=True)
    for name, ok in results:
        print(("PASS  " if ok else "FAIL  ") + name)
    good = all(ok for _, ok in results)
    print(f"selftest: {'PASS' if good else 'FAIL'} ({sum(ok for _, ok in results)} of {len(results)})")
    return 0 if good else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("propose", allow_abbrev=False, help="write a proposal from a metadata file")
    p.add_argument("--metadata", required=True, help="the metadata file (JSON or YAML): subject, items, releases; no values")
    p.add_argument("--kind", required=True, help=", ".join(KINDS))
    p.add_argument("--from", dest="from_", default=None, help="later-period: the first date, YYYY-MM-DD")
    p.add_argument("--until", default=None, help="later-period: the last date, if it ends")
    p.add_argument("--sites", default=None, help="another-site: the sites, separated by commas")
    p.add_argument("--regions", default=None, help="another-site: the regions, separated by commas")
    p.add_argument("--release", default=None, help="next-release: the release's name, as the metadata's `releases` declares it")
    p.add_argument("--periods", type=int, default=None, help="next-release: count the size of this many periods of the release's cadence")
    p.add_argument("--fraction", type=float, default=None, help="random: the share set aside (default 0.2)")
    p.add_argument("--draw-over", dest="draw_over", default=None, help="random: site (the default when every item has one) or id")
    p.add_argument("--what", required=True, help="exactly what data is kept for the check, in words")
    p.add_argument("--why", required=True, help="why that data suits the question, in words")
    p.add_argument("--unfair", required=True, help="what would make it unfair as a check, in words")
    p.add_argument("--by", required=True, help="who proposes: agent:<id> (or human:<id>)")
    p.add_argument("--model", default=None, help="the model, when an agent proposes")
    p.add_argument("--out", required=True, help="where the proposal is written (a .yaml file; a random draw's seed goes beside it)")
    p.add_argument("--studies", default="studies", help="the folder of studies, where the record of proposals is kept (default: studies)")
    p.set_defaults(fn=cmd_propose)
    p = sub.add_parser("describe", allow_abbrev=False, help="write the metadata of one CSV file from its date column")
    p.add_argument("--csv", required=True, help="the data file; only its date column and its series column are kept")
    p.add_argument("--date-column", dest="date_column", required=True, help="the column of dates: YYYY, YYYY-MM or YYYY-MM-DD")
    p.add_argument("--series-column", dest="series_column", default=None, help="a column that names the series a row belongs to")
    p.add_argument("--period", default="year", help="year (the default) or month: one item for each series and period")
    p.add_argument("--subject", required=True, help="key=value,key=value: what the data is about")
    p.add_argument("--what", required=True, help="what the file holds, in words")
    p.add_argument("--release", default=None, help="the name of the update the file grows by, declared under `releases`")
    p.add_argument("--cadence", default=None, help="the release's cadence: " + ", ".join(CADENCES))
    p.add_argument("--out", required=True, help="the metadata file to write (.yaml)")
    p.set_defaults(fn=cmd_describe)
    p = sub.add_parser("show", allow_abbrev=False, help="a proposal in plain words")
    p.add_argument("--proposal", required=True)
    p.add_argument("--studies", default=None, help="say where the proposal stands on the record kept there")
    p.set_defaults(fn=cmd_show)
    p = sub.add_parser("reveal", allow_abbrev=False, help="draw a random set aside from the lock's merge commit, as the opening drew it")
    p.add_argument("--proposal", required=True)
    p.add_argument("--merge-commit", dest="merge_commit", default=None, help="the commit GitHub created when the lock request was merged")
    p.add_argument("--seed-file", dest="seed_file", default=None, help="refused: a seed is never handed in")
    p.set_defaults(fn=cmd_reveal)
    p = sub.add_parser("check", allow_abbrev=False, help="what a reviewer asks of a proposal")
    p.add_argument("--proposal", required=True)
    p.add_argument("--studies", default="studies", help="the folder of studies where the record is (default: studies)")
    p.add_argument("--log", default=None, help="the exploration log or study log of the work it serves")
    p.set_defaults(fn=cmd_check)
    sub.add_parser("selftest", allow_abbrev=False, help="the tool tests itself")
    return ap


def main() -> int:
    a = build_parser().parse_args()
    try:
        why = _fence().started_under()
        if why:
            raise Refused(f"this command was started from inside a look or a step of a plan ({why}); a script the tools run does not call them")
        if a.cmd == "selftest":
            return selftest()
        a.fn(a)
    except Refused as r:
        print(f"REFUSED: {r}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
