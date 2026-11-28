#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml", "pystac[validation]", "duckdb"]
# ///
"""openings: the shared registry of openings, a static STAC catalog in a repository of its own.

One window, one opening holds only if every factory that could open the
window reads the same record. The record of what has been opened beside one
workspace's studies (studies/openings.jsonl) is that workspace's own. The
registry is shared: a git repository of its own, holding a static STAC
catalog with one Collection for each dataset (the STAC Collection the fresh
data was described in) and one Item for each opening: its datetime, the
study and the factory, the lock (its merge commit, or practice), what was
opened (a set aside, a release, the query), links with the relation
`derived_from` to each data Item opened, with the checksum of each of its
files (File Info on the link), and whether it was practice. The record is
that STAC JSON in git, read in a pull request's diff. A stac-geoparquet
index of it (`index`) is generated, checksummed beside it, rebuilt at will
and never the record.

Who writes an opening into it. Never an agent. After a verified opening,
the workflow (factory/harnesses/github/openings.workflow.yml, a template
that has never run on GitHub) runs `record --by platform:github`, which
writes the Item into a branch of the registry for a person or the workflow
to merge by pull request. In practice, a person types `record --by
human:<id> --local-practice`: the Item is written into a branch of a local
registry, marked practice in its id and its properties, and it protects
nothing about people. This tool refuses `agent:` for `record`, refuses a
lock the platform does not confirm (unless practice), and refuses an
opening that has not finished.

Who reads it. `check` is asked before a lock (`sf.py request-lock
--registry`) and before an opening (`sf.py open-held-out --registry`), and
by `fresh_data.py propose --registry`: has any of these Items, or this
query, been opened before, and when, against this study's lock? Opened
before the lock (or before the proposal): not fresh, refused, in plain
words. Opened after this study's lock by a study also locked before it:
both were locked before either opened, so both openings stand, and the
opening says so. Only what is merged into the registry's checked-out
branch is read: a pull request still open is not yet the record.

Commands.

  init      make a registry: a git repository with catalog.json
  record    write a study's opening as an Item, into a branch of the registry
  check     what the registry says about a proposal's Items or query
  index     write the stac-geoparquet index of the registry (never the record)
  selftest  the tool tests itself, in throwaway git repositories

Usage: openings.py <command> [...]; openings.py selftest
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
import importlib.machinery  # noqa: E402
import importlib.util  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402


class _SourceOnly(importlib.machinery.SourceFileLoader):
    """A module of this factory is loaded from its source text, compiled here, and never from cached bytecode beside it."""

    def get_code(self, fullname):
        return compile(self.get_data(self.path), self.path, "exec", dont_inherit=True)


HERE = Path(__file__).resolve().parent


def _load(name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py", loader=_SourceOnly(name, str(HERE / f"{name}.py")))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


sf = _load("sf")
Refused = sf.Refused
st = _load("stac")  # loaded after the study tool: its refusals are the study tool's
ROOT_ID = "science-factory-openings"
ACTOR = re.compile(r"(human|platform):[A-Za-z0-9_.@/-]+")


def git(repo: Path, *args, check: bool = True) -> subprocess.CompletedProcess:
    """git in the registry, with an environment that holds no setting of the caller's that runs code or names a hook."""
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "LC_ALL", "TZ", "TMPDIR")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0", GIT_AUTHOR_NAME="science-factory openings",
               GIT_AUTHOR_EMAIL="openings@example.invalid", GIT_COMMITTER_NAME="science-factory openings",
               GIT_COMMITTER_EMAIL="openings@example.invalid")
    done = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", *args], cwd=str(repo), env=env,
                          capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if check and done.returncode != 0:
        raise Refused(f"git {' '.join(args[:2])} in the registry failed: {(done.stderr or done.stdout).strip()[:300]}")
    return done


# ---- the registry ---------------------------------------------------------------------------------------------
def init(registry: Path) -> Path:
    registry = Path(os.path.abspath(registry))
    if (registry / "catalog.json").exists():
        raise Refused(f"{registry} already holds a registry (catalog.json)")
    registry.mkdir(parents=True, exist_ok=True)
    if not (registry / ".git").exists():
        git(registry, "init", "-q", "-b", "main")
    cat = {"type": "Catalog", "stac_version": st.STAC_VERSION, "stac_extensions": [], "id": ROOT_ID,
           "description": "The shared registry of openings of the science factory: one Collection for each dataset, one Item for each "
                          "opening of fresh data, added by pull request after a verified opening. This STAC JSON in git is the record.",
           "links": [{"rel": "root", "href": "./catalog.json", "type": "application/json"}]}
    problems = st.validate_objects([cat])["problems"]
    if problems:
        raise Refused("the registry's catalog is not valid STAC: " + "; ".join(problems))
    (registry / "catalog.json").write_text(json.dumps(cat, indent=1) + "\n")
    (registry / "README.md").write_text("# The registry of openings\n\nA static STAC catalog: `catalog.json`, one folder for each dataset with its "
                                        "`collection.json`, and an Item for each opening under `items/`. Added to by pull request only, by the "
                                        "workflow after a verified opening, never by an agent. Written and read by `tools/openings.py` of the "
                                        "science factory.\n")
    git(registry, "add", "-A")
    git(registry, "commit", "-q", "-m", "A registry of openings, empty")
    return registry


def openings_in(registry: Path) -> list:
    """Every opening the registry's checked-out tree holds, as Items, read with DuckDB in this process."""
    registry = Path(os.path.abspath(registry))
    if not (registry / "catalog.json").is_file():
        raise Refused(f"{registry} is not a registry of openings (no catalog.json): `openings.py init` makes one")
    if not any(registry.glob("*/items/*.json")):
        return []
    con = st.duck([registry])
    try:
        rows = con.execute(f"SELECT json FROM read_json({st.sql_text(str(registry / '*' / 'items' / '*.json'))}, "
                           "format='unstructured', records=false, columns={'json': 'JSON'})").fetchall()
    except Exception as e:  # noqa: BLE001  DuckDB's errors
        raise Refused(f"the registry's Items could not be read ({type(e).__name__}: {str(e).splitlines()[0][:200]})")
    finally:
        con.close()
    return [json.loads(r[0]) for r in rows]


def wants_of(proposal: dict) -> dict:
    """What a proposal's fresh data is, as the registry matches it: the collection, the Item IDs and the checksums of their
    files, and the query (the time interval and the box)."""
    stx = (proposal or {}).get("stac")
    if not stx:
        raise Refused("the registry of openings matches data described as STAC: this proposal was made from the factory's own metadata "
                      "form, so it cannot be checked against the registry")
    items = stx.get("items") or []
    return {"collection": stx.get("collection"), "ids": {i["id"] for i in items},
            "sums": {v["sha256"] for i in items for v in (i.get("assets") or {}).values() if v.get("sha256")},
            "query": stx.get("query") or {}}


def touches(opening: dict, want: dict) -> list:
    """How one opening in the registry touches what a proposal wants: the same Item, a file by its checksum, or an overlapping
    query on the same collection. Empty when it does not."""
    pr = opening.get("properties") or {}
    if opening.get("collection") != want["collection"] and pr.get("sf:collection") != want["collection"]:
        return []
    out = []
    for ln in opening.get("links") or []:
        if ln.get("rel") != "derived_from":
            continue
        if ln.get("sf:item") in want["ids"]:
            out.append(f"the Item {ln['sf:item']}")
        elif st.sha_of(ln.get("file:checksum")) in want["sums"]:
            out.append(f"a file of {ln.get('sf:item')}, by its checksum")
    q, theirs = want["query"], pr.get("sf:query") or {}
    if not out and q.get("datetime") and theirs.get("datetime"):
        a0, a1 = st.interval_of(q)
        b0, b1 = st.interval_of(theirs)
        lo = max([d for d in (a0, b0) if d] or [dt.date.min])
        hi = min([d for d in (a1, b1) if d] or [dt.date.max])
        if lo <= hi and st.bbox_meets(q.get("bbox"), theirs.get("bbox")):
            out.append(f"the query {theirs['datetime']}, which overlaps {q['datetime']}")
    return out


def check(registry, proposal: dict, lock_at: str | None = None, study: str | None = None) -> dict:
    """What the registry says about a proposal's fresh data: {"before": [...], "after": [...], "words", "openings_read"}. An
    opening is `before` when it came before this study's lock (or there is no lock yet), and `after` when it came after it.
    An opening of this same study is left out."""
    want = wants_of(proposal)
    all_ = openings_in(Path(registry))
    before, after = [], []
    for o in all_:
        pr = o.get("properties") or {}
        if study and pr.get("sf:study") == study:
            continue
        how = touches(o, want)
        if not how:
            continue
        rec = {"id": o.get("id"), "study": pr.get("sf:study"), "factory": pr.get("sf:factory"), "at": pr.get("datetime"),
               "practice": bool(pr.get("sf:practice")), "how": how, "locked_at": (pr.get("sf:lock") or {}).get("at")}
        (after if lock_at and str(rec["at"]) > str(lock_at) else before).append(rec)  # the same second counts as before

    def said(r):
        return (f"{r['study']} of the factory {(r['factory'] or {}).get('alias') or (r['factory'] or {}).get('name')} opened "
                + "; ".join(r["how"]) + f" at {r['at']}" + (" (in practice)" if r["practice"] else ""))
    if before:
        words = ("NOT FRESH. The registry of openings says: " + "; ".join(said(r) for r in before)
                 + (f", before this study's lock at {lock_at}" if lock_at else ", before this study was locked")
                 + ". Data that has been opened is not fresh for a study locked after it.")
    elif after:
        words = ("The registry of openings says: " + "; ".join(said(r) for r in after) + f", after this study's lock at {lock_at}. Both "
                 "studies were locked before either opened, so both openings stand; each finding says the other exists.")
    else:
        words = (f"The registry of openings ({len(all_)} opening(s) merged there) records no opening of these Items or of this query "
                 f"in the collection `{want['collection']}`.")
    return {"before": before, "after": after, "words": words, "openings_read": len(all_), "registry": str(Path(registry).resolve())}


# ---- an opening, written as an Item ----------------------------------------------------------------------------
def factory_identity() -> dict:
    spec = yaml.safe_load((sf.FACTORY / "factory.yaml").read_text())
    acts = ((spec.get("procedure") or {}).get("acts_by_people") or {}).get("lock") or {}
    return {"name": spec.get("name"), "alias": spec.get("alias"), "version": str(spec.get("version")),
            "repository": acts.get("repository") if isinstance(acts, dict) else None}


def opening_item(study: "sf.Study", by: str, practice: bool) -> tuple:
    """(the Item of a study's latest finished opening, the dataset's Collection id, the plain words). Refuses an opening that
    has not finished, a plan whose fresh data was not described as STAC, and a lock the platform does not confirm unless the
    lock and this record are both practice."""
    ev = study.events()
    plan = sf.checked_plan(study)
    lock = study.last("lock.recorded")
    fin = next((e for e in reversed(ev) if e["kind"] == "opening.finished"), None)
    if not lock or not fin or fin["seq"] < lock["seq"]:
        raise Refused("the study has no finished opening after its lock: the registry records an opening that happened")
    standing = sf.standing_of(ev, lock, sf.ask_now(study, ev, lock, "lock") if sf.route_of(lock) == sf.PULL_REQUEST else None)
    if standing == sf.PRACTICE and not practice:
        raise Refused("the study's lock is practice (typed), so its opening is recorded only as practice: `--by human:<id> --local-practice`")
    if standing != sf.PRACTICE and practice:
        raise Refused("the study's lock is a pull request: its opening is recorded by the workflow under `platform:github`, not as practice")
    if standing not in (sf.PRACTICE, sf.VERIFIED):
        raise Refused(f"the study's lock stands at `{standing}`: the registry records an opening only after a verified one (GitHub, asked now, "
                      "confirms the lock), and nothing was written")
    fresh = sf.fresh_data_of(study, plan)
    if not fresh or not fresh["proposal"].get("stac"):
        raise Refused("the plan's fresh data was not proposed from a STAC description, so there are no Items to link the opening to")
    prop, stx = fresh["proposal"], fresh["proposal"]["stac"]
    opened = list(stx.get("items") or [])
    listed = "the Items the lock bound"
    if not opened:  # a query bound at the lock: the Items are those the catalog lists for it now, with their checksums
        got = st.search(sf.fresh_tool().catalog_of(prop, study.path(((plan.get("data") or {}).get("held_out") or {})["fresh_data"])),
                        stx.get("query") or {})
        opened = [{"id": it["id"], "assets": st.assets_of(it)} for it in got["items"]]
        listed = f"the Items the catalog listed for the query when this was recorded ({got['how']})"
    who = factory_identity()
    start = next((e for e in ev if e["kind"] == "opening.started" and e["data"]["n"] == fin["data"]["n"]), None)
    at = (start or fin)["at"]
    iid = ("practice--" if practice else "") + re.sub(r"[^A-Za-z0-9_.-]+", "-", f"{who['alias']}--{plan['study']}--{fin['data']['test']}-{fin['data']['n']}")
    links = [{"rel": "root", "href": "../../catalog.json", "type": "application/json"},
             {"rel": "parent", "href": "../collection.json", "type": "application/json"},
             {"rel": "collection", "href": "../collection.json", "type": "application/json"}]
    for i in opened:
        for key, a_ in (i.get("assets") or {}).items():
            links.append({"rel": "derived_from", "href": str(a_.get("href") or i["id"]), "title": f"the data Item {i['id']}, asset {key}",
                          "sf:item": i["id"], **({"file:checksum": st.multihash(a_["sha256"])} if a_.get("sha256") else {})})
    item = {"type": "Feature", "stac_version": st.STAC_VERSION, "stac_extensions": [st.FILE_EXT], "id": iid, "geometry": None,
            "properties": {"datetime": at, "sf:study": plan["study"], "sf:study_dir": study.d.name, "sf:factory": who,
                           "sf:collection": stx.get("collection"), "sf:opened": prop["kind_in_words"], "sf:query": stx.get("query"),
                           "sf:opened_items": listed, "sf:test": fin["data"]["test"], "sf:opening": fin["data"]["n"],
                           "sf:lock": {"at": lock["at"], "standing": standing, "merge_commit": (lock["data"].get("merge") or {}).get("commit"),
                                       "log_fingerprint": f"{lock['seq']}:{lock['hash']}"},
                           "sf:opening_fingerprint": f"{fin['seq']}:{fin['hash']}", "sf:data_sha256": fin["data"].get("data_sha"),
                           "sf:proposal_sha256": fresh["sha256"], "sf:practice": practice, "sf:recorded_by": by},
            "links": links, "assets": {}, "collection": stx.get("collection")}
    return item, stx.get("collection"), f"{plan['study']} opened {len(opened)} Item(s) of `{stx.get('collection')}` at {at}"


def record(registry, study_dir, by: str, practice: bool, branch: str | None = None) -> dict:
    """Write the study's latest opening into a new branch of the registry, for a person or the workflow to merge by pull request.
    The checked-out branch is not changed: the branch is made in a worktree of its own and removed after."""
    if sf.fence.started_under():
        raise Refused("this command was started from inside a look or a step of a plan; a script the tools run does not call them")
    if str(by).startswith("agent:"):
        raise Refused("an opening is written into the registry by the workflow after a verified opening, or typed by a person in practice; "
                      "never by an agent")
    if not ACTOR.fullmatch(str(by or "")):
        raise Refused("`--by` is platform:github (the workflow) or human:<id> with --local-practice")
    if str(by).startswith("human:") and not practice:
        raise Refused("a person types an opening into the registry only in practice (`--local-practice`); otherwise the workflow records it")
    if str(by).startswith("platform:") and practice:
        raise Refused("the workflow's record is not practice")
    registry = Path(os.path.abspath(registry))
    if not (registry / "catalog.json").is_file():
        raise Refused(f"{registry} is not a registry of openings")
    study = sf.Study(Path(study_dir))
    item, cid, words = opening_item(study, by, practice)
    problems = st.validate_objects([item])["problems"]
    if problems:
        raise Refused("the opening's Item is not valid STAC, and nothing was written: " + "; ".join(problems[:3]))
    if any(o.get("id") == item["id"] for o in openings_in(registry)):
        raise Refused(f"the registry already records {item['id']}")
    name = branch or ("practice/" if practice else "opening/") + item["id"]
    base = git(registry, "rev-parse", "HEAD").stdout.strip()
    tree = Path(tempfile.mkdtemp(prefix="sf-openings-"))
    shutil.rmtree(tree)
    git(registry, "worktree", "add", "-q", "-b", name, str(tree), base)
    try:
        cdir = tree / cid
        if not (cdir / "collection.json").is_file():
            cdir.mkdir(parents=True, exist_ok=True)
            col = {"type": "Collection", "stac_version": st.STAC_VERSION, "stac_extensions": [], "id": cid,
                   "description": f"The openings of the dataset `{cid}`: one Item for each opening of its fresh data.",
                   "license": "other", "extent": {"spatial": {"bbox": [list(st.GLOBAL)]}, "temporal": {"interval": [[item["properties"]["datetime"], None]]}},
                   "links": [{"rel": "root", "href": "../catalog.json", "type": "application/json"},
                             {"rel": "parent", "href": "../catalog.json", "type": "application/json"}]}
            cat = json.loads((tree / "catalog.json").read_text())
            cat["links"].append({"rel": "child", "href": f"./{cid}/collection.json", "type": "application/json"})
            (tree / "catalog.json").write_text(json.dumps(cat, indent=1) + "\n")
        else:
            col = json.loads((cdir / "collection.json").read_text())
        col["links"].append({"rel": "item", "href": f"./items/{item['id']}.json", "type": "application/geo+json"})
        problems = st.validate_objects([col])["problems"]
        if problems:
            raise Refused("the dataset's Collection is not valid STAC: " + "; ".join(problems[:3]))
        (cdir / "collection.json").write_text(json.dumps(col, indent=1) + "\n")
        (cdir / "items").mkdir(exist_ok=True)
        (cdir / "items" / f"{item['id']}.json").write_text(json.dumps(item, indent=1) + "\n")
        git(tree, "add", "-A")
        git(tree, "commit", "-q", "-m", ("PRACTICE: " if practice else "") + f"The opening {item['id']}: {words}")
        commit = git(tree, "rev-parse", "HEAD").stdout.strip()
    finally:
        git(registry, "worktree", "remove", "--force", str(tree), check=False)
    return {"branch": name, "commit": commit, "item": item["id"], "collection": cid, "words": words, "practice": practice}


def write_index(registry, out) -> dict:
    """The stac-geoparquet index of every opening in the registry: generated, checksummed beside it, never the record."""
    items = openings_in(Path(registry))
    tmp = Path(tempfile.mkdtemp(prefix="sf-openings-index-"))
    try:
        nd = tmp / "openings.ndjson"
        nd.write_text("".join(json.dumps({**it, "links": [ln for ln in it.get("links") or [] if ln.get("rel") == "derived_from"]}) + "\n" for it in items))
        side = st.write_index(nd, out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    side["generated_from"] = {"registry": str(Path(registry).resolve()), "commit": git(Path(registry), "rev-parse", "HEAD").stdout.strip(),
                              "openings": len(items)}
    Path(str(out) + ".json").write_text(json.dumps(side, indent=1) + "\n")
    return side


# ---- commands ---------------------------------------------------------------------------------------------------
def cmd_init(a) -> None:
    print(f"registry of openings made: {init(Path(a.registry))} (a git repository holding catalog.json; add to it by pull request)")


def cmd_record(a) -> None:
    got = record(a.registry, a.study, a.by, bool(a.local_practice), a.branch)
    print(("PRACTICE: " if got["practice"] else "") + f"the opening {got['item']} is written into the branch `{got['branch']}` of the registry "
          f"(commit {got['commit'][:12]}): {got['words']}. It is the record once a pull request of that branch is merged.")


def cmd_check(a) -> None:
    prop = sf.fresh_tool().load(a.proposal)
    lock_at = None
    if a.study:
        lock = sf.Study(Path(a.study)).last("lock.recorded")
        lock_at = lock["at"] if lock else None
    got = check(a.registry, prop, lock_at, Path(a.study).name if a.study else None)
    print(json.dumps(got, indent=1) if a.json else got["words"])


def cmd_index(a) -> None:
    side = write_index(a.registry, a.out)
    print(f"index written: {a.out}, {side['items']} opening(s), sha256 {side['index_sha256'][:16]}; it is generated and never the record")


# ---- self-test ----------------------------------------------------------------------------------------------------
def selftest() -> int:
    """Two factories, one dataset, one registry, in throwaway folders and git repositories. Every lock and opening is practice
    (typed by a placeholder person), so this tests the registry's logic, not GitHub."""
    results = []

    def ok(name, cond):
        results.append((name, bool(cond)))
    tmp = Path(tempfile.mkdtemp(prefix="openings-selftest-")).resolve()
    person, fd = "human:throwaway-placeholder", sf.fresh_tool()
    kept_today, kept_model = sf.TODAY, sf.Study.default_model
    sf.Study.default_model = "selftest-model"  # every agent event of this self-test is written under this name
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            reg = init(tmp / "registry")
            ok("a registry is a git repository holding a static STAC catalog, valid against the shipped schemas",
               (reg / ".git").is_dir() and json.loads((reg / "catalog.json").read_text())["type"] == "Catalog" and openings_in(reg) == [])
            # one dataset, described as STAC: two years published, a third to come
            data, cat = tmp / "data", tmp / "dataset"
            data.mkdir()
            col = {"type": "Collection", "stac_version": st.STAC_VERSION, "stac_extensions": [], "id": "river-gauge", "description": "a toy gauge",
                   "license": "other", "extent": {"spatial": {"bbox": [[-91.5, 30.0, -91.0, 31.0]]}, "temporal": {"interval": [["2024-01-01T00:00:00Z", None]]}},
                   "sf:subject": {"record": "river-gauge"}, "sf:releases": [{"name": "2026", "cadence": "yearly", "after": "2025-12-31"}]}
            files = {}
            for y in (2024, 2025):
                files[y] = data / f"{y}.csv"
                files[y].write_text("time,stage\n" + "".join(f"{y}-{m:02d}-01,{m}\n" for m in range(1, 13)))
            items = [st.make_item(f"gauge-{y}", "river-gauge", dt.date(y, 1, 1), dt.date(y, 12, 1), files[y], cat / "items",
                                  [-91.2, 30.5, -91.2, 30.5], "none", {"sf:count": 12}) for y in (2024, 2025)]
            st.write_description(cat, col, items)

            def workspace(name):
                (tmp / name / "studies").mkdir(parents=True)
                return tmp / name

            def proposal(ws, name, **k):
                out = ws / "proposals" / f"{name}.yaml"
                fd.cmd_propose(fd.A(metadata=str(cat / "collection.json"), what="w", why="y", unfair="u", studies=str(ws / "studies"), out=str(out), **k))
                return out

            def study(ws, name, prop, **start):
                s = sf.Study(ws / "studies" / name)
                sf.cmd_start(s, sf.A(id=name, question=sf.PLAN["question"], by="agent:coordinating", **start))
                plan = json.loads(json.dumps(sf.PLAN))
                plan["study"] = name
                window = {"start": "2025-01-01", "end": "2025-12-31"} if "later" in prop.name else {"start": "2026-01-01", "end": "2026-12-31"}
                plan["data"]["held_out"].update(window=window, pair={"record": "river-gauge", "case": name}, fresh_data=os.path.relpath(prop, s.d))
                (s.d / "toy.py").write_text(sf.TOY.replace("POWER", "0.9").replace("TESTED", "None"))
                s.plan_path.write_text(yaml.safe_dump(plan, sort_keys=False))
                sf.cmd_test(s, sf.A(what="known-answers", by="agent:analysis"))
                sf.cmd_test(s, sf.A(what="working-data", by="agent:analysis"))
                return s

            def lock(s, **k):
                sf.cmd_request_lock(s, sf.A(by="agent:coordinating", registry=k.get("registry")))
                sf.cmd_lock(s, sf.A(by=person, evidence=sf.URL, local_practice=True))

            def opening(s, **k):
                sf.cmd_open_held_out(s, sf.A(test="held-out", by="agent:coordinating", local_practice=True, **k))

            def merge(branch):  # a person merging the pull request, here by git alone
                git(reg, "merge", "-q", "--no-ff", "-m", f"Merge {branch}", branch)

            def refusal(fn, *args, **kw):
                try:
                    fn(*args, **kw)
                except Exception as r:  # noqa: BLE001  the refusal of whichever tool refused
                    if type(r).__name__ != "Refused":
                        raise
                    return str(r)
                return ""
            a_ws, b_ws = workspace("factory-a"), workspace("factory-b")
            sf.TODAY = "2027-03-01"
            # factory A sets aside 2025 (published Items), locks, opens, and the workflow records the opening
            pa = proposal(a_ws, "later-a", kind="later-period", from_="2025-01-01", until="2025-12-31")
            sa = study(a_ws, "STUDY-A", pa)
            lock(sa, registry=str(reg))
            ok("before a lock, the registry is asked and its answer is in the lock request in plain words",
               "records no opening of these Items" in (sa.d / "lock-request" / "EVIDENCE.md").read_text())
            opening(sa, registry=str(reg))
            ok("an agent never writes an opening into the registry", "never by an agent" in refusal(record, reg, sa.d, "agent:coordinating", False))
            ok("a person types one only in practice, and a practice lock is recorded only as practice",
               "only in practice" in refusal(record, reg, sa.d, person, False)
               and "only as practice" in refusal(record, reg, sa.d, "platform:github", False))
            got = record(reg, sa.d, person, True)
            item = json.loads(git(reg, "show", f"{got['branch']}:river-gauge/items/{got['item']}.json").stdout)
            ok("the opening is an Item in a branch of the registry: its datetime, the study, the lock, links derived_from each data Item opened "
               "with its file's checksum, marked practice; the checked-out branch is unchanged until it is merged",
               got["branch"].startswith("practice/") and item["properties"]["sf:study"] == "STUDY-A" and item["properties"]["sf:practice"] is True
               and [(ln["sf:item"], ln["file:checksum"]) for ln in item["links"] if ln["rel"] == "derived_from"] == [("gauge-2025", "1220" + st.sha_file(files[2025]))]
               and git(reg, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip() == "main" and openings_in(reg) == []
               and st.validate_objects([item])["problems"] == [])
            ok("an opening not yet merged is not yet the record: factory B may still propose the same set aside", refusal(
                proposal, b_ws, "later-b0", kind="later-period", from_="2025-01-01", until="2025-12-31", registry=str(reg)) == "")
            merge(got["branch"])
            ok("once merged, a set aside opened by one factory is refused as fresh by the other, in plain words",
               "NOT FRESH" in (r := refusal(proposal, b_ws, "later-b", kind="later-period", from_="2025-01-01", until="2025-12-31", registry=str(reg)))
               and "STUDY-A of the factory" in r and "the Item gauge-2025" in r)
            ok("the same file under another Item id is caught by its checksum", any("by its checksum" in h for o in openings_in(reg) for h in touches(o, {
                "collection": "river-gauge", "ids": {"other-id"}, "sums": {st.sha_file(files[2025])}, "query": {}})))
            ok("recording the same opening twice is refused", "already records" in refusal(record, reg, sa.d, person, True))
            # the next release, not yet published: two studies, one in each factory, locked before it; then a third locked after an opening
            sf.TODAY = "2026-06-01"
            pc, pd_ = proposal(a_ws, "next-c", kind="next-release", release="2026"), proposal(b_ws, "next-d", kind="next-release", release="2026")
            sc = study(a_ws, "STUDY-C", pc, fresh_data=str(pc), working_data=[str(files[2025])])
            sd = study(b_ws, "STUDY-D", pd_, fresh_data=str(pd_), working_data=[str(files[2025])])
            se = study(b_ws, "STUDY-E", pd_, fresh_data=str(pd_), working_data=[str(files[2025])])
            lock(sc, registry=str(reg))
            lock(sd, registry=str(reg))
            sf.cmd_request_lock(se, sf.A(by="agent:coordinating", registry=str(reg)))  # its request is written while nothing is merged
            sf.TODAY = "2027-03-01"
            files[2026] = data / "2026.csv"
            files[2026].write_text("time,stage\n" + "".join(f"2026-{m:02d}-01,{m}\n" for m in range(1, 13)))
            new = st.make_item("gauge-2026", "river-gauge", dt.date(2026, 1, 1), dt.date(2026, 12, 31), files[2026], cat / "items",
                               [-91.2, 30.5, -91.2, 30.5], "none", {"sf:count": 12})
            (cat / "items" / "gauge-2026.json").write_text(json.dumps(new))
            c = json.loads((cat / "collection.json").read_text())
            c["links"].append({"rel": "item", "href": "./items/gauge-2026.json", "type": "application/geo+json"})
            (cat / "collection.json").write_text(json.dumps(c))
            for s in (sc, sd, se):  # the fetch keeps the release's own rows
                plan = yaml.safe_load(s.plan_path.read_text())
                plan["tests"]["held-out"]["fetch"] = ["{python}", "{study}/toy.py", "fetch-release", "{study}/data/held-out.json"]
                (s.d / "release-rows.json").write_text(json.dumps([{"time": f"2026-{m:02d}", "Mean": 0.5} for m in range(1, 13)]))
                s.plan_path.write_text(yaml.safe_dump(plan, sort_keys=False))
            for s in (sc, sd, se):
                sf.cmd_test(s, sf.A(what="known-answers", by="agent:analysis"))
                sf.cmd_test(s, sf.A(what="working-data", by="agent:analysis"))
            for s in (sc, sd):
                sf.cmd_request_lock(s, sf.A(by="agent:coordinating", registry=str(reg)))
                sf.cmd_lock(s, sf.A(by=person, evidence=sf.URL, local_practice=True))
            import time
            time.sleep(1.1)  # the log's clock counts seconds, and an opening in the same second as a lock counts as before it
            opening(sc, registry=str(reg))
            gc = record(reg, sc.d, person, True)
            merge(gc["branch"])
            sf.cmd_request_lock(se, sf.A(by="agent:coordinating"))  # written without asking the registry: it says so
            ok("a lock request written without the registry says so plainly",
               "No registry of openings was named" in (se.d / "lock-request" / "EVIDENCE.md").read_text())
            time.sleep(1.1)
            sf.cmd_lock(se, sf.A(by=person, evidence=sf.URL, local_practice=True))
            sd_said = io.StringIO()
            with contextlib.redirect_stdout(sd_said):
                opening(sd, registry=str(reg))
            ok("two studies locked before a release both open it: the second is told, plainly, that the first opened it after its lock",
               sd.last("opening.finished") is not None and "after this study's lock" in sd_said.getvalue()
               and "both openings stand" in sd_said.getvalue() and "STUDY-C" in sd_said.getvalue())
            gd = record(reg, sd.d, person, True)
            item_d = json.loads(git(reg, "show", f"{gd['branch']}:river-gauge/items/{gd['item']}.json").stdout)
            ok("an opening of a query bound at the lock links the Items the catalog lists for it, with their checksums",
               [(ln["sf:item"], st.sha_of(ln.get("file:checksum"))) for ln in item_d["links"] if ln["rel"] == "derived_from"]
               == [("gauge-2026", st.sha_file(files[2026]))] and item_d["properties"]["sf:query"]["datetime"].startswith("2026-01-01"))
            e_said = refusal(opening, se, registry=str(reg))
            ok("a study locked after another opened and published the data is told so plainly, and its opening is refused unused",
               "NOT FRESH" in e_said and "STUDY-C" in e_said and "before this study's lock" in e_said and se.last("opening.started") is None)
            sf_ = study(a_ws, "STUDY-F", pc, fresh_data=str(pc), working_data=[str(files[2025])])
            ok("and a lock request that asks the registry after the opening was merged is refused as not fresh, and writes nothing",
               "NOT FRESH" in refusal(sf.cmd_request_lock, sf_, sf.A(by="agent:coordinating", registry=str(reg)))
               and not (sf_.d / "lock-request").exists())
            side = write_index(reg, tmp / "openings.parquet")
            back = st.read_description(tmp / "openings.parquet")
            ok("the stac-geoparquet index of the registry is generated from the merged JSON, checksummed beside it, and never the record",
               side["items"] == 2 and sorted(i["id"] for i in back["items"]) == sorted(o["id"] for o in openings_in(reg))
               and json.loads((tmp / "openings.parquet.json").read_text())["index_sha256"] == st.sha_file(tmp / "openings.parquet")
               and "never the record" in json.loads((tmp / "openings.parquet.json").read_text())["says"])
    finally:
        sf.TODAY, sf.Study.default_model = kept_today, kept_model
        shutil.rmtree(tmp, ignore_errors=True)
    for name, good in results:
        print(("PASS  " if good else "FAIL  ") + name)
    good = all(g for _n, g in results)
    print(f"selftest: {'PASS' if good else 'FAIL'} ({sum(g for _n, g in results)} of {len(results)})")
    return 0 if good else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init", allow_abbrev=False, help="make a registry of openings")
    p.add_argument("--registry", required=True)
    p.set_defaults(fn=cmd_init)
    p = sub.add_parser("record", allow_abbrev=False, help="write a study's opening into a branch of the registry (the workflow, or a person in practice)")
    p.add_argument("--registry", required=True)
    p.add_argument("--study", required=True)
    p.add_argument("--by", required=True, help="platform:github (the workflow), or human:<id> with --local-practice; never an agent")
    p.add_argument("--local-practice", dest="local_practice", action="store_true", help="practice: the Item is marked practice")
    p.add_argument("--branch", default=None, help="the branch to write it into (default: opening/<id>, or practice/<id>)")
    p.set_defaults(fn=cmd_record)
    p = sub.add_parser("check", allow_abbrev=False, help="what the registry says about a proposal's Items or query")
    p.add_argument("--registry", required=True)
    p.add_argument("--proposal", required=True, help="a proposal of the fresh data made from a STAC description")
    p.add_argument("--study", default=None, help="the study, for when its lock was")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_check)
    p = sub.add_parser("index", allow_abbrev=False, help="the stac-geoparquet index of the registry, generated")
    p.add_argument("--registry", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_index)
    sub.add_parser("selftest", allow_abbrev=False, help="the tool tests itself")
    return ap


def main() -> int:
    a = build_parser().parse_args()
    try:
        sf.refuse_dirty_environment()
        sf.refuse_inside_a_look()
        if a.cmd == "selftest":
            return selftest()
        a.fn(a)
    except Refused as r:
        print(f"REFUSED: {r}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
