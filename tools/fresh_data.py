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

A random set aside is drawn by this tool, not by anybody: it makes a seed
from the operating system's randomness, ranks every item by the sha256 of
the seed and the item's identifier, and takes the first part. The proposal
and the record keep only the seed's sha256; the seed itself goes into a
file of its own beside the proposal (`<proposal>.seed`). The lock request
prints the seed, and anybody can draw again from it (`reveal`) and get the
same members. The hash is a commitment: it shows the seed was fixed when
the proposal was written. It does not show that nobody ran the tool twice
and kept the draw they liked, which is why every proposal is also written to
a record beside the studies (`fresh-data.jsonl`), and the lock shows how
many proposals that record holds for the same subject.

Commands.

  propose   write a proposal from a metadata file (and, for a random set
            aside, its seed file); add it to the record beside the studies
  show      a proposal in plain words
  reveal    draw a random set aside again from its seed, and say whether it
            gives the same members
  check     what a reviewer asks of a proposal: it is on the record, its
            words are written, a random draw comes from its seed, and it
            was written before the exploration or study it serves started
  selftest  the tool tests itself

Usage: fresh_data.py <command> [...]; fresh_data.py selftest
"""
import sys

sys.dont_write_bytecode = True
if __name__ == "__main__" and not (sys.flags.isolated and sys.flags.no_site):
    # A clean start, as in the other tools: run again in a Python that reads no PYTHON variable, no user site and no
    # start-up file. What a hostile environment ran before this line has already run (docs/WHAT-IS-ENFORCED.md).
    import os
    _again = [sys.executable, "-I", "-S", "-B", os.path.abspath(__file__), *sys.argv[1:]]
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

HERE = Path(__file__).resolve().parent
TOOL = Path(__file__).resolve()


class Refused(Exception):
    pass


def _fence():
    """tools/fence.py, by its path: what says whether this process was started from inside a look."""
    if "fence" not in sys.modules:
        spec = importlib.util.spec_from_file_location("fence", HERE / "fence.py")
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
TOP_KEYS = ("what", "subject", "items", "releases", "source", "note")       # a metadata file has these keys and no others
ITEM_KEYS = ("id", "site", "region", "start", "end", "time", "date", "release", "version", "count", "lat", "lon", "name", "note")
TEXT_ITEM_KEYS = ("id", "site", "region", "release", "version", "name", "note")
RELEASE_KEYS = ("name", "date", "expected_items", "expected_count", "note")
NUMERIC_ITEM_KEYS = ("lat", "lon")                                            # a position is metadata, not a measurement
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ACTOR = re.compile(r"(human|agent):[A-Za-z0-9_.@/-]+")
PLACEHOLDERS = ("human:you", "human:name", "human:id", "agent:name", "agent:id")
RECORD = "fresh-data.jsonl"
NOT_COMPUTED = ("the power of the plan's rules at this size. This tool counts; it does not know the method. The method's "
                "known-answer tests are where power is measured: run them on synthetic cases of this size before the lock "
                "(for the built-in gain method, `methods/gain/known_answer_tests.py --passes N`) and compare")
DRAW = "every item ranked by the sha256 of the seed, a line break and the item's identifier; the first k taken"


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
    return {"meta": meta, "sha256": sha_bytes(raw), "path": str(f.resolve())}


def span(it: dict) -> tuple | None:
    first = it.get("start") or it.get("time") or it.get("date")
    last = it.get("end") or it.get("time") or it.get("date")
    return (str(first), str(last)) if first and last else None


def draw(seed: str, population: list, k: int) -> list:
    """The random set aside: deterministic in the seed and the population, and in nothing else (not the order of the file)."""
    ranked = sorted(set(population), key=lambda u: hashlib.sha256(f"{seed}\n{u}".encode()).hexdigest())
    return sorted(ranked[:k])


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
        rule = {"release": a.release.strip()}
        fresh = [it for it in items if it.get("release") == rule["release"]]
        working = [it for it in items if it.get("release") != rule["release"]]
        members = [it["id"] for it in fresh]
        explore += ["--set-aside-release", rule["release"]]
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
        seed = secrets.token_hex(32)
        members = draw(seed, population, k)
        rule = {"fraction": f, "draw_over": unit, "k": k, "of": len(population), "method": DRAW}
        for it in items:
            (fresh if it[unit] in members else working).append(it)
        explore += ["--set-aside-sites", ",".join(members)]
    if not working:
        raise Refused("this proposal leaves no working data: everything the metadata lists would be kept unopened")
    if not fresh and a.kind != "next-release":
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
    size["computed_here"] = "counts of items and of observations (the `count` of each item), from the metadata"
    size["not_computed_here"] = NOT_COMPUTED
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
    if seed is not None:
        proposal["draw"] = {"seed_sha256": sha_bytes(seed.encode()), "drawn_from": population,
                            "seed_file": "beside this file, with the same name and .seed in place of its ending; the lock request prints it"}
    return {"proposal": proposal, "seed": seed}


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
    if seed is not None:
        seed_path(out).write_text(seed + "\n")
    studies.mkdir(parents=True, exist_ok=True)
    line = {"kind": "fresh-data.proposed", "fresh_kind": p["kind"], "subject": subject_key(p["subject"]), "proposal_sha256": sha_bytes(body.encode()),
            "seed_sha256": (p.get("draw") or {}).get("seed_sha256"), "members": len(p["members"]), "by": p["proposed"]["by"],
            "model": p["proposed"]["model"], "at": p["proposed"]["at"], "file": os.path.relpath(out, studies)}
    with (studies / RECORD).open("a") as f:
        f.write(json.dumps(line, sort_keys=True) + "\n")
    same = [ln for ln in record_lines(studies) if ln.get("subject") == line["subject"]]
    print("\n".join(in_words(p)))
    print(f"\nproposal written: {out}" + (f" (its seed, kept for the lock: {seed_path(out)})" if seed else "")
          + f". On the record beside the studies ({studies / RECORD}): proposal {len(same)} for this subject.")
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


def redraw(p: dict, seed: str) -> dict:
    """Draw again from a revealed seed and compare with the proposal. The proposal alone is enough: it lists the
    identifiers the draw was made from, so the metadata file need not travel with it."""
    d = p.get("draw") or {}
    seed = str(seed).strip()
    hash_ok = sha_bytes(seed.encode()) == d.get("seed_sha256")
    again = draw(seed, list(d.get("drawn_from") or []), int((p.get("rule") or {}).get("k") or 0))
    return {"seed_matches_its_hash": hash_ok, "same_members": again == sorted(p["members"]), "members_again": again}


def problems(path, studies=None, seed: str | None = None) -> list:
    """What is wrong with a proposal, in words; empty when nothing is. With `studies`, that it is on the record there.
    A random set aside is checked against its seed: the one given, or the seed file beside the proposal."""
    p, out = load(path), []
    for k in ("what", "why_it_suits", "what_would_make_it_unfair"):
        if not str(p.get(k) or "").strip():
            out.append(f"`{k}` is not written")
    if studies is not None and not on_record(path, studies)["on_record"]:
        out.append(f"this proposal is not on the record beside the studies ({Path(studies) / RECORD}), byte for byte: it was not "
                   "written by the tool there, or it was edited afterwards")
    if p["kind"] == "random":
        if seed is None:
            s = seed_path(Path(path))
            seed = s.read_text() if s.is_file() else None
        if seed is None:
            out.append("the seed of this random set aside is missing (its .seed file), so nobody can show the members were drawn and not chosen")
        else:
            r = redraw(p, seed)
            if not r["seed_matches_its_hash"]:
                out.append("the seed given is not the one whose sha256 the proposal recorded")
            elif not r["same_members"]:
                out.append("drawing again from the seed does not give the members the proposal lists: they were changed after the draw")
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
        lines += [f"**How large a test it allows.** The release `{rule.get('release')}` is not out: expected items {n(size.get('fresh_items'))}, "
                  f"expected observations {n(size.get('fresh_observations'))}" + (f", on {size['expected_on']}" if size.get("expected_on") else "")
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
        what = f"the release `{rule.get('release')}`"
    else:
        what = f"{rule.get('k')} of {rule.get('of')} ({'sites' if rule.get('draw_over') == 'site' else 'items'}), drawn by the tool"
    lines += [f"**The members.** {what}: " + (", ".join(map(str, p.get("members") or [])) or "none listed yet") + ".", ""]
    prop = p.get("proposed") or {}
    meta = p.get("metadata") or {}
    lines += [f"**Who chose it, and from what.** Proposed by {prop.get('by')}" + (f" (model {prop.get('model')})" if prop.get("model") else "")
              + f" at {prop.get('at')}, from the metadata file {meta.get('file')} (sha256 {str(meta.get('sha256'))[:16]}, {meta.get('items')} items, "
              f"fields {', '.join(meta.get('fields') or [])}). No measured value was read: the tool reads only that file, and refuses one with "
              "any other field."]
    if p.get("kind") == "random":
        d = p.get("draw") or {}
        lines += ["", f"**Nobody chose the members.** The tool drew them: {rule.get('method')}. It recorded the seed's sha256 "
                  f"({str(d.get('seed_sha256'))[:16]}) when it wrote the proposal, and kept the seed apart."]
        if revealed is not None:
            r = redraw(p, revealed)
            lines += [f"The seed, revealed for this lock: `{revealed.strip()}`. Its sha256 is the one recorded: {'yes' if r['seed_matches_its_hash'] else 'NO'}. "
                      f"Drawing again from it gives the same members: {'yes' if r['same_members'] else 'NO'}. Anybody can draw again: "
                      "`uv run tools/fresh_data.py reveal --proposal <this proposal>`."]
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
        raise Refused("only a random set aside has a seed: this proposal is " + p["kind_in_words"])
    s = Path(a.seed_file) if a.seed_file else seed_path(Path(a.proposal))
    if not s.is_file():
        raise Refused(f"no seed file at {s}")
    r = redraw(p, s.read_text())
    print(json.dumps({"seed_matches_its_hash": r["seed_matches_its_hash"], "same_members": r["same_members"],
                      "members": r["members_again"]}, indent=1))
    if not (r["seed_matches_its_hash"] and r["same_members"]):
        raise Refused("the draw does not come out the same: the seed or the members were changed")


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
    def __init__(self, **k):
        self.__dict__.update({"from_": None, "until": None, "sites": None, "regions": None, "release": None, "fraction": None,
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
        # the random draw: by the tool, reproducible from the revealed seed, and nobody's choice
        a1 = A(kind="random", fraction=0.3, out=str(tmp / "p" / "random.yaml"), **base)
        cmd_propose(a1)
        pfile = Path(a1.out)
        p = load(pfile)
        seed = seed_path(pfile).read_text()
        check("a random set aside holds only the seed's sha256 in the proposal and the record; the seed is in its own file",
              seed.strip() not in pfile.read_text() and seed.strip() not in (studies / RECORD).read_text()
              and p["draw"]["seed_sha256"] == sha_bytes(seed.strip().encode()) and len(p["members"]) == 3)
        r = redraw(p, seed)
        check("the draw is reproducible from the revealed seed, from the proposal alone", r["seed_matches_its_hash"] and r["same_members"])
        check("another seed gives another draw (the members follow the seed, not anybody's wish), and a wrong seed is caught",
              not redraw(p, "0" * 64)["seed_matches_its_hash"]
              and any(draw(secrets.token_hex(32), p["draw"]["drawn_from"], 3) != p["members"] for _ in range(5)))
        check("the draw does not depend on the order of the metadata file", draw(seed.strip(), list(reversed(p["draw"]["drawn_from"])), 3) == p["members"])
        check("a proposal on the record, with its seed, has no problems", problems(pfile, studies) == [])
        edited = pfile.read_text().replace(f"- {p['members'][0]}\n", "- S99\n", 1)
        pfile2 = tmp / "p" / "edited.yaml"
        pfile2.write_text(edited)
        shutil.copyfile(seed_path(pfile), seed_path(pfile2))
        got = problems(pfile2, studies)
        check("members changed by hand after the draw are caught twice: the file is not on the record, and the seed does not give them",
              any("not on the record" in q for q in got) and any("does not give the members" in q for q in got))
        seed_path(pfile2).unlink()
        check("a random set aside whose seed is missing cannot show it was drawn", any("seed" in q and "missing" in q for q in problems(pfile2)))
        a2 = A(kind="random", fraction=0.3, out=str(tmp / "p" / "random-2.yaml"), **base)
        cmd_propose(a2)
        check("a second proposal for the same subject is a new line on the record, and the record says how many there are",
              on_record(a2.out, studies) == {"on_record": True, "sha256": sha_file(Path(a2.out)), "for_this_subject": 2, "position": 2})
        check("a proposal is written once: the same path is refused", "already exists" in refused(cmd_propose, a2))
        words = "\n".join(in_words(p, revealed=seed, record=on_record(pfile, studies)))
        check("in words, a random set aside says nobody chose the members, shows the revealed seed and that it draws the same, and says "
              "where it stands on the record", "Nobody chose the members" in words and seed.strip() in words
              and "Drawing again from it gives the same members: yes" in words and "number 1" in words and "{" not in words)
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
    p.add_argument("--release", default=None, help="next-release: the release's name")
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
    p = sub.add_parser("show", allow_abbrev=False, help="a proposal in plain words")
    p.add_argument("--proposal", required=True)
    p.add_argument("--studies", default=None, help="say where the proposal stands on the record kept there")
    p.set_defaults(fn=cmd_show)
    p = sub.add_parser("reveal", allow_abbrev=False, help="draw a random set aside again from its seed")
    p.add_argument("--proposal", required=True)
    p.add_argument("--seed-file", dest="seed_file", default=None, help="default: the .seed file beside the proposal")
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
