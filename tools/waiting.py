#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml", "duckdb"]
# ///
"""waiting: everything in a workspace that waits on a person, with the next step.

A workspace is the folder where the science lives: `studies/`, `explorations/`
and `knowledge-queue/`, as the tools make them. This tool reads them and writes
nothing. It runs no language model. For each study and exploration it asks the
study tool and the exploring tool where the work stands (`sf.py status`,
`explore.py status`, the same functions), and lists what wants a person, or
what is stuck, grouped by study or exploration, oldest first, each with what
is wanted, since when, who acts next and the exact next step:

  so-what-wanted               a reviewed lead with no person's so what
  expert-wanted                a lead a person said needs an expert, waiting for one
  try-instead-not-picked-up    a person said try instead, and no agent has looked since
  lock-request-not-merged      a lock request written, and no lock recorded after it
  lock-merged-not-verified     a lock merged on GitHub, its people not verified
  signature-request-not-merged a signature request written, and no signature after it
  signature-merged-not-verified a signature merged, its people not verified
  waiting-on-a-data-release    a locked study whose release cannot be out yet: the
                               cut-off, the periods the plan needs and how many have
                               not ended, from the metadata's cadence
  opening-refused              the last opening asked GitHub and was refused
  opening-blocked              the definition, the tools, the plan or the code is not
                               what the lock bound, so the opening is refused
  opening-fetch-failed         an opening whose fetch failed: voidable by a person,
                               or used up
  a-test-failed                the last run of a test or a rehearsal did not pass
  exploration-spoiled          set-aside data reached an exploration
  draft-awaiting-the-steward   a drafted page in the queue, for a steward

An item leaves the list when what it waits for is done: the so what given,
the request merged and recorded, the act verified, the release out, the
draft accepted or removed.

Standings of the acts are as the tools compute them now: asked of GitHub
when a token is in the environment (GH_TOKEN, GITHUB_TOKEN or
SF_PLATFORM_TOKEN), and otherwise `merge found, people not verified`, with
what the log says GitHub answered when last asked marked "not re-checked
now".

Tracking issues. A file `tracking-issues.yaml` at the top of a workspace may
map a study or exploration (its path from the workspace) to the number of
its tracking issue on GitHub, such as `studies/STUDY-1: 12`. Each group then
names its issue, and the JSON lists every issue with whether it waits, for
the workflow that keeps the label `waiting-on-a-person` in step
(factory/harnesses/github/waiting.workflow.yml).

Usage:
  waiting.py [--workspace DIR ...] [--factory DIR] [--json]
  waiting.py --selftest

The JSON (`--json`), schema `science-factory/waiting/v1`:
  {"schema", "asked_at", "standings": {"asked_now": bool, "words"},
   "workspaces": [path], "repository": "owner/name" or null,
   "groups": [{"workspace", "kind": "study"|"exploration"|"queue", "id", "path",
               "stage", "tracking_issue": {"number", "url"} or null,
               "items": [{"what", "wanted", "since", "who", "next_step":
                          {"command"?, "open"?, "do"}, "standing"?, "details"}]}],
   "tracking_issues": [{"workspace", "path", "number", "url", "waiting": bool}],
   "counts": {"groups", "items", "by_what": {what: n}},
   "says"}
Groups hold at least one item and come oldest first, as do their items; an
item whose time is unknown goes last.
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
import datetime as dt  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
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


HERE = Path(__file__).resolve().parent


def neighbour(name: str):
    """A tool of this folder, loaded by its path, once: the exploring tool loads the study tool itself, and both are used
    as that one copy, so a setting of the study tool is the same for both."""
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py", loader=_SourceOnly(name, str(HERE / f"{name}.py")))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


explore = neighbour("explore")  # it loads sf.py beside it and keeps it as explore.sf
sf = explore.sf
sys.modules.setdefault("sf", sf)
Refused = sf.Refused
SCHEMA = "science-factory/waiting/v1"
LABEL = "waiting-on-a-person"
TRACKING = "tracking-issues.yaml"
QUEUE = "knowledge-queue"
NOT_RECHECKED = "not re-checked now"
SAYS = ("Read from the workspace's own files and logs; nothing here is written or decided. A standing is GitHub's answer only "
        "when it was asked now, with a token; otherwise it is what git here shows, and an earlier answer in the log is " + NOT_RECHECKED + ".")


def token_present() -> bool:
    return any(str(os.environ.get(n) or "").strip() for n in ("SF_PLATFORM_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"))


def at_key(t) -> tuple:
    """Oldest first, an unknown time last."""
    return (t is None, str(t or ""))


# ---------------------------------------------------------------- the workspace
def workspace_parts(ws: Path) -> tuple:
    """(study folders, exploration folders, queue folders) of a workspace: each a folder with its own log."""
    studies = sorted(p.parent for p in (ws / "studies").glob("*/study-log.jsonl")) if (ws / "studies").is_dir() else []
    xs = sorted(p.parent for p in (ws / "explorations").glob("*/exploration-log.jsonl")) if (ws / "explorations").is_dir() else []
    queues = [ws / QUEUE] if (ws / QUEUE).is_dir() else []
    return studies, xs, queues


def tracking_issues(ws: Path) -> dict:
    """{path from the workspace: issue number} from tracking-issues.yaml, or nothing."""
    f = ws / TRACKING
    if not f.is_file():
        return {}
    try:
        got = yaml.safe_load(f.read_text()) or {}
    except yaml.YAMLError as e:
        raise Refused(f"{f} is not YAML ({e}); it maps a study or exploration (studies/NAME) to its issue number")
    if not isinstance(got, dict) or any(not isinstance(v, int) or isinstance(v, bool) or v < 1 for v in got.values()):
        raise Refused(f"{f} maps each study or exploration (studies/NAME, explorations/NAME) to its issue number, a whole number")
    return {str(k).strip("/"): v for k, v in got.items()}


def repository_of(factory: Path) -> str | None:
    try:
        return str((sf.acts_declared(factory).get("lock") or {}).get("repository") or "") or None
    except Refused:
        return None


def pin_of(ws: Path) -> dict:
    """The factory pin of a study repository (tools/factory_update.py writes it), or nothing."""
    f = ws / "factory-pin.yaml"
    try:
        got = yaml.safe_load(f.read_text()) if f.is_file() else {}
    except yaml.YAMLError:
        got = {}
    return got if isinstance(got, dict) else {}


class Ctx:
    """What every item of one workspace needs to say its next step."""

    def __init__(self, ws: Path, factory: Path):
        self.ws, self.factory = ws, factory
        self.repo = repository_of(factory)
        self.tools = "tools" if (ws / "tools" / "sf.py").is_file() else str(HERE)
        self.issues = tracking_issues(ws)
        self.pin = pin_of(ws)
        self.so_what_route = (explore.so_what_declared(factory) or {}).get("route")
        try:
            acts = sf.acts_declared(factory)
        except Refused:
            acts = {}
        self.routes = {k: (v or {}).get("route") for k, v in acts.items()}
        self.branch = (acts.get("lock") or {}).get("protected_branch") or "main"

    def rel(self, p: Path) -> str:
        try:
            return p.resolve().relative_to(self.ws.resolve()).as_posix()
        except ValueError:
            return str(p)

    def tool(self, name: str) -> str:
        return f"uv run {self.tools}/{name}"

    def pulls(self, words: str) -> str | None:
        return f"https://github.com/{self.repo}/pulls?q=is%3Apr+{words}" if self.repo else None

    def issue(self, path: str) -> dict | None:
        n = self.issues.get(path)
        return {"number": n, "url": f"https://github.com/{self.repo}/issues/{n}" if self.repo else None} if n else None


def item(what: str, wanted: str, since, who: str, do: str, command: str | None = None, open_: str | None = None, **details) -> dict:
    step = {"do": do}
    if command:
        step["command"] = command
    if open_:
        step["open"] = open_
    out = {"what": what, "wanted": wanted, "since": since, "who": who, "next_step": step}
    standing = details.pop("standing", None)
    if standing is not None:
        out["standing"] = standing
    out["details"] = details
    return out


# ---------------------------------------------------------------- a study
def act_standing_words(st: dict, act: str) -> str:
    a = (st.get("acts") or {}).get(act)
    if not isinstance(a, dict):
        return str(a)
    words = a.get("standing") or ""
    if a.get("standing") != sf.VERIFIED:
        asked = a.get("asked_now")
        if not isinstance(asked, dict) or asked.get("result") == sf.NOT_CHECKED:
            words += f"; {a['last_checked']}" if a.get("last_checked") else f"; {NOT_RECHECKED}"
    return words


def study_items(c: Ctx, d: Path) -> tuple:
    study = sf.Study(d)
    ev = study.events()
    rel = c.rel(d)
    S = f"--study {rel}"
    try:
        st = sf.stage_of(study, c.factory)
    except Refused as r:
        return {"stage": f"cannot be read: {r}"}, []
    out = []
    last = lambda kind: next((e for e in reversed(ev) if e["kind"] == kind), None)  # noqa: E731
    lock, sig = last("lock.recorded"), last("signature.recorded")
    closed = last("study.closed")
    started = sf.standing_openings(ev)
    try:
        plan = sf.checked_plan(study)
    except Refused:
        plan = None

    # the two acts: a request written and not merged; merged and not verified
    for act, kind, made in (("lock", "lock.requested", lock), ("signature", "signature.requested", sig)):
        asked = last(kind)
        if asked and not (made and made["seq"] > asked["seq"]) and not closed:
            if c.routes.get(act) == sf.PRACTICE:
                out.append(item(f"{act}-request-not-merged", f"the {act}: this factory's {act} is typed (practice)", asked["at"], "people",
                                f"read {rel}/{act}-request/EVIDENCE.md and look at each figure; the {act} is then typed, and stays practice",
                                command=f"{c.tool('sf.py')} {act} {S} --by human:YOUR-ID --evidence https://... --local-practice"))
                continue
            stale = []
            with contextlib.suppress(Refused, OSError, ValueError, KeyError, TypeError):
                stale = sf.request_problems(study, act, c.factory)
            if stale:
                out.append(item(f"{act}-request-not-merged", f"the {act} request, written again: it no longer matches the files", asked["at"],
                                "agent:coordinating", f"nobody approves this request as it stands ({'; '.join(stale[:2])}); the coordinating "
                                f"agent writes it again, then people approve and merge the new one",
                                command=f"{c.tool('sf.py')} request-{act} {S} --by agent:coordinating --model MODEL"
                                        + (" --decision signed" if act == "signature" else ""), stale=stale[:4]))
                continue
            who = "the scientist and the steward" if act == "lock" else "the steward"
            out.append(item(f"{act}-request-not-merged", f"the {act}: {who} read the request, approve and merge its pull request into "
                            f"`{c.branch}`", asked["at"], "people",
                            f"read {rel}/{act}-request/EVIDENCE.md (the pull request shows it) and look at each figure yourself; approve and "
                            "merge. If no pull request carries it yet, commit the study on a branch and open one", open_=c.pulls(f"{d.name}+{act}-request")))
        if made and sf.route_of(made) == sf.PULL_REQUEST and (st.get("acts") or {}).get(act, {}).get("standing") == sf.MERGE_FOUND:
            words = act_standing_words(st, act)
            m = made["data"].get("merge") or {}
            out.append(item(f"{act}-merged-not-verified", f"the {act} was merged; GitHub has not confirmed the people who approved it",
                            made["at"], "people", "ask GitHub, with a read token for this repository (Contents and Pull requests, read), "
                            "and record its answer; the act is verified only on GitHub's answer",
                            command=f"GH_TOKEN=YOUR-READ-TOKEN {c.tool('sf.py')} verify-acts {S} --by human:YOUR-ID",
                            open_=m.get("url") or m.get("pull_request") if str(m.get("url") or "").startswith("https://") else None,
                            standing=words, merge_commit=m.get("commit")))

    if lock and not started and not closed:
        # a release that cannot be out yet
        rel_ = sf.release_of(ev)
        spec = ((plan or {}).get("tests") or {}).get("held-out") or {}
        window = sf.window_for(plan, spec) if plan else None
        said = sf.release_waiting(rel_, window) if rel_ and window else None
        if said:
            n, first, end = sf.periods_needed(rel_, window)
            today = sf._today()
            left = None
            if n:
                fd = sf.fresh_tool()
                left = sum(1 for i in range(1, n + 1) if fd.add_period(first, rel_["cadence"], i) - dt.timedelta(days=1) >= today)
            due = max([end] + ([dt.date.fromisoformat(rel_["expected_on"])] if rel_.get("expected_on") else []))
            out.append(item("waiting-on-a-data-release", f"the release after {rel_['cut_off']}: "
                            + (f"{left} of {n} {rel_['cadence']} period(s) the plan needs have not ended" if n else
                               f"the plan needs data to {end}, and the release declares no cadence"),
                            lock["at"], "a data release", f"nothing until {due + dt.timedelta(days=1)} at the earliest; then the coordinating "
                            "agent opens the fresh data once, with a read token",
                            command=f"GH_TOKEN=YOUR-READ-TOKEN {c.tool('sf.py')} open-held-out {S} --by agent:coordinating --model MODEL",
                            cut_off=rel_["cut_off"], cadence=rel_.get("cadence"), periods_needed=n, periods_not_ended=left,
                            first_day=str(first), last_day=str(end), expected_on=rel_.get("expected_on"), status=said))
        # what the lock bound is no longer what is here
        blocked = []
        if plan and lock["data"].get("plan_sha") != study.plan_sha():
            blocked.append("the analysis plan changed after the lock")
        elif plan and not sf.same_code(lock["data"].get("code"), study.code_hashes(plan)):
            blocked.append("the code changed after the lock: " + "; ".join(sf.code_difference(lock["data"]["code"], study.code_hashes(plan))[:3]))
        stamp = st.get("definition") or {}
        if stamp.get("same_as_locked") is False:
            blocked += [r for r in stamp.get("remarks") or [] if "lock recorded" in r][:3] or ["the definition is not the one the lock recorded"]
        if blocked:
            carried = next((x for x in c.pin.get("carried_on_old_version") or [] if isinstance(x, dict) and str(x.get("study")).strip("/") == rel), None)
            do = ("this study was carried on its old definition when the factory was updated: open it from a checkout of commit "
                  f"{carried.get('commit_before_update')}, where the definition it was locked to stands" if carried and carried.get("commit_before_update") else
                  "the opening is refused until what the lock bound is back: check out the commit the lock was made on and open from there, "
                  "or write a new lock request, which people approve as a new pull request")
            out.append(item("opening-blocked", "the fresh data cannot be opened: what the lock bound is not what is here", lock["at"], "people",
                            do, command=(f"git worktree add ../{d.name}-as-locked {carried['commit_before_update']}" if carried and carried.get("commit_before_update")
                                         else f"{c.tool('sf.py')} request-lock {S} --by agent:coordinating --model MODEL"), reasons=blocked))
        # the last opening attempt asked GitHub and was refused
        tried = [e for e in ev if e["kind"] == "act.verification" and e["data"].get("asked_at") == "the opening" and e["seq"] > lock["seq"]]
        if tried and tried[-1]["data"].get("result") != sf.VERIFIED:
            t = tried[-1]
            refuted = t["data"].get("result") == sf.REFUTED
            out.append(item("opening-refused", "the opening was refused: GitHub " + ("does not bear the lock out" if refuted else "could not be asked about the lock"),
                            t["at"], "people", ("read what GitHub said; this is not waived, and a new lock is a new pull request" if refuted else
                                                "give the opening a read token and a network, and the coordinating agent opens again; nothing was used up"),
                            command=None if refuted else f"GH_TOKEN=YOUR-READ-TOKEN {c.tool('sf.py')} open-held-out {S} --by agent:coordinating --model MODEL",
                            result=t["data"].get("result"), problems=(t["data"].get("problems") or [])[:3]))

    # an opening whose fetch failed
    voids = {(e["data"]["test"], e["data"]["n"]) for e in ev if e["kind"] == "opening.voided"}
    for o in started:
        if (o["data"]["test"], o["data"]["n"]) in voids:
            continue
        fin = next((e for e in ev if e["kind"] == "opening.finished" and e["data"]["test"] == o["data"]["test"] and e["data"].get("n") == o["data"]["n"]), None)
        if fin is None:
            out.append(item("opening-fetch-failed", f"opening {o['data']['n']} of {o['data']['test']} started and never finished: it is used up",
                            o["at"], "people", "the steward decides what the study records: the tool cannot say what the opening read, so it is not voided"))
            continue
        fd_ = fin["data"]
        if isinstance(fd_.get("fetch_exit"), int) and fd_["fetch_exit"] != 0:
            voidable = not fd_.get("data_sha") and fd_.get("exit") is None and fd_.get("fetch_wrote") == []
            out.append(item("opening-fetch-failed", f"the fetch of opening {fd_['n']} ({fd_['test']}) failed (exit {fd_['fetch_exit']})", fin["at"], "people",
                            ("a person voids it, on the record, with the reason and a link; the coordinating agent then opens again" if voidable else
                             "it wrote files during the fetch, so it is used up and cannot be voided; the steward decides what the study records"),
                            command=(f"{c.tool('sf.py')} void-unread {S} --test {fd_['test']} --by human:YOUR-ID --reason \"WHY\" --evidence https://..."
                                     if voidable else None), voidable=voidable))
        elif (fd_.get("release") or {}).get("refused"):
            out.append(item("opening-fetch-failed", "the release fetched is not the one the plan needs, and the opening is used up", fin["at"], "people",
                            "the steward decides what the study records; the next chance is the next data held out", problems=fd_["release"]["refused"][:3]))

    # a test or a rehearsal whose last run did not pass, before the lock
    if not lock and not closed and plan:
        names = [("test.run", {"test": t}) for t in sf.FREE_TESTS] + [("rehearsal.run", {"id": r.get("id")}) for r in plan.get("rehearsals") or [] if isinstance(r, dict)]
        for kind, match in names:
            e = study.last(kind, **match)
            if e and e["data"].get("exit") not in (0, None):
                what = sf.TEST_NAMES.get(match.get("test")) or f"rehearsal {match.get('id')}"
                cmd = (f"{c.tool('sf.py')} test {match['test']} {S} --by agent:analysis --model MODEL" if "test" in match else
                       f"{c.tool('sf.py')} rehearse {S} --id {match['id']} --by agent:analysis --model MODEL")
                out.append(item("a-test-failed", f"{what}: the last run did not pass (exit {e['data']['exit']})", e["at"], "agent:analysis",
                                "the analysis agent reads the receipt, changes the method or its tests, and runs it again; nothing is locked "
                                "until every test passes", command=cmd))
    return {"stage": st.get("stage"), "outcome": st.get("outcome")}, out


# ---------------------------------------------------------------- an exploration
def exploration_items(c: Ctx, d: Path) -> tuple:
    x = explore.Exploration(d)
    rel = c.rel(d)
    try:
        xs = explore.stage_of(x)
    except Refused as r:
        return {"stage": f"cannot be read: {r}"}, []
    ev = x.events()
    out = []
    on = explore.lead_on_file(ev)
    stage = xs.get("stage")
    if stage == "so-what" and xs.get("who") == "people":
        said = explore.so_what_now(ev)
        sha = (on or {}).get("data", {}).get("json_sha") or ""
        verdicts = [e for e in ev if e["kind"] == "review.verdict" and on and e["seq"] > on["seq"]]
        asked = [e for e in ev if e["kind"] == "so-what.asked" and on and e["seq"] > on["seq"]]
        question = asked[-1]["data"]["file"] if asked else None
        expert = said is not None and said["data"].get("answer") == "needs-an-expert"
        lines = ["so-what: worth-confirming", f"exploration: {rel}", f"lead: {sha[:16]}"]
        if c.so_what_route == sf.PRACTICE:
            step = dict(command=f"{c.tool('explore.py')} so-what --exploration {rel} --by human:YOUR-ID --answer ANSWER --read-lead {sha} --local-practice")
            do = "a person who knows the field reads the lead and answers; this factory's so what is typed (practice)"
        else:
            iss = c.issue(rel)
            step = dict(open_=(iss or {}).get("url"))
            do = ("a person who knows the field reads the lead and its figures, then comments on the tracking issue with these lines "
                  "(one of worth-confirming, try-instead with `direction:`, not-interesting with `reason:`, needs-an-expert with "
                  "`expertise:`): " + " / ".join(lines))
        out.append(item("expert-wanted" if expert else "so-what-wanted",
                        (f"a so what from a person with this expertise: {said['data'].get('expertise')}" if expert else
                         "a person's so what on the reviewed lead: is it worth confirming?"),
                        (said["at"] if expert else (verdicts[-1]["at"] if verdicts else None)), "people", do, **step,
                        question=question, lead=f"{rel}/lead.md", lead_sha256=sha,
                        standing=(explore.so_what_in_words(ev, said, explore.so_what_ask_now(x, said)) if said else None)))
    if stage == "explore" and xs.get("next_question"):
        said = explore.so_what_now(ev) or explore.last(ev, "so-what.recorded")
        picked = [e for e in ev if said and e["seq"] > said["seq"] and str(e["actor"]).startswith("agent:")
                  and e["kind"] in ("look.run", "look.refused", "choice.recorded", "note.raised", "lead.recorded", "knowledge.read")]
        if said and not picked:
            out.append(item("try-instead-not-picked-up", f"a person asked to try instead: {xs['next_question']}", said["at"], "agent:analysis",
                            "the coordinating agent starts the analysis agent on that direction; it looks, records choices, and writes up a "
                            "new version of the lead, which is reviewed and answered again",
                            command=f"{c.tool('explore.py')} look --exploration {rel} --by agent:analysis --model MODEL --why \"{xs['next_question'][:60]}\" -- uv run SCRIPT DATA",
                            direction=xs["next_question"], standing=explore.so_what_in_words(ev, said, explore.so_what_ask_now(x, said))))
    if stage == "spoiled":
        br = explore.breached(ev)
        out.append(item("exploration-spoiled", "set-aside data reached the exploration: no lead and no hand-over can come from it",
                        br[0]["at"] if br else None, "agent:analysis", "the analysis agent ends it as a stop and says so; a person decides "
                        "whether a new exploration, with something else set aside, is worth starting",
                        command=f"{c.tool('explore.py')} end --exploration {rel} --by agent:analysis --model MODEL --outcome stop --summary \"spoiled: WHY\""))
    return {"stage": stage, "outcome": xs.get("outcome")}, out


# ---------------------------------------------------------------- the queue of drafts
def draft_items(c: Ctx, q: Path) -> list:
    """[(group path, item)] for every page at status draft in a queue, grouped by the study or exploration it was drafted from."""
    knowledge = neighbour("knowledge")
    out = []
    for p in sorted(q.rglob("*.md")):
        if p.name == "index.md":
            continue
        fm, _body = knowledge.front_matter(p)
        if not isinstance(fm, dict) or fm.get("status") != "draft":
            continue
        frm = fm.get("drafted_from") if isinstance(fm.get("drafted_from"), dict) else {}
        group = (f"explorations/{frm['exploration']}" if frm.get("exploration") else f"studies/{frm['study']}" if frm.get("study") else c.rel(q))
        gen = fm.get("generated") if isinstance(fm.get("generated"), dict) else {}
        since = str(gen.get("at")) if gen.get("at") else None
        out.append((group, item("draft-awaiting-the-steward", f"a drafted page for the wiki: {fm.get('title') or p.stem}", since, "people",
                                "a steward reads it and its sources; to accept, moves it into the wiki by a pull request and adds their own "
                                "`verified` line; to decline, removes it from the queue by a pull request, with the reason",
                                open_=None, page=c.rel(p), drafted_by=frm.get("by"))))
    return out


# ---------------------------------------------------------------- all of it
def waiting(workspaces: list, factory: Path) -> dict:
    asked_now = token_present()
    groups, issues = [], []
    repo = None
    for ws in workspaces:
        ws = Path(ws).resolve()
        if not ws.is_dir():
            raise Refused(f"{ws} is not a folder")
        c = Ctx(ws, factory)
        repo = repo or c.repo
        studies, xs, queues = workspace_parts(ws)
        found = {}
        for d in xs:
            info, items = exploration_items(c, d)
            found[c.rel(d)] = {"kind": "exploration", "id": d.name, **info, "items": items}
        for d in studies:
            info, items = study_items(c, d)
            found[c.rel(d)] = {"kind": "study", "id": d.name, **info, "items": items}
        for q in queues:
            for group, it in draft_items(c, q):
                found.setdefault(group, {"kind": "queue" if group == c.rel(q) else group.split("/")[0].rstrip("s").replace("studie", "study"),
                                         "id": Path(group).name, "stage": None, "items": []})["items"].append(it)
        for path, g in found.items():
            g["items"].sort(key=lambda i: at_key(i["since"]))
            g.update(workspace=str(ws), path=path, tracking_issue=c.issue(path))
            if g["items"]:
                groups.append(g)
        for path, n in sorted(c.issues.items()):
            issues.append({"workspace": str(ws), "path": path, "number": n, "url": f"https://github.com/{c.repo}/issues/{n}" if c.repo else None,
                           "waiting": bool((found.get(path) or {}).get("items"))})
    groups.sort(key=lambda g: at_key(g["items"][0]["since"]))
    by = {}
    for g in groups:
        for i in g["items"]:
            by[i["what"]] = by.get(i["what"], 0) + 1
    order = ("workspace", "kind", "id", "path", "stage", "outcome", "tracking_issue", "items")
    return {"schema": SCHEMA, "asked_at": sf.now(),
            "standings": {"asked_now": asked_now, "words": ("asked of GitHub now, with the token in the environment" if asked_now else
                                                            "not re-checked now: no token in the environment (GH_TOKEN, GITHUB_TOKEN or "
                                                            "SF_PLATFORM_TOKEN), so a merged act stands at what git here shows")},
            "workspaces": [str(Path(w).resolve()) for w in workspaces], "repository": repo,
            "groups": [{k: g.get(k) for k in order} for g in groups], "tracking_issues": issues,
            "counts": {"groups": len(groups), "items": sum(by.values()), "by_what": dict(sorted(by.items()))}, "says": SAYS}


def in_words(w: dict) -> str:
    """The list in plain words, as Markdown: what the workflow writes to its job summary."""
    n = w["counts"]["items"]
    lines = [f"# Waiting on a person: {n} item(s) in {w['counts']['groups']} group(s)", "",
             f"Asked at {w['asked_at']}. Standings: {w['standings']['words']}.", ""]
    if not n:
        lines += ["Nothing waits on a person.", ""]
    for g in w["groups"]:
        iss = g.get("tracking_issue")
        lines += [f"## {g['path']} ({g['kind']}" + (f", stage {g['stage']}" if g.get("stage") else "") + ")"
                  + (f", tracking issue #{iss['number']}" if iss else ""), ""]
        for i in g["items"]:
            s = i["next_step"]
            lines.append(f"- **{i['wanted']}** ({i['what']}), since {i['since'] or 'a time the files do not say'}; who acts: {i['who']}.")
            lines.append(f"  {s['do'][0].upper() + s['do'][1:]}.")
            if s.get("command"):
                lines.append(f"  `{s['command']}`")
            if s.get("open"):
                lines.append(f"  Open {s['open']}")
            if i.get("standing"):
                lines.append(f"  Standing: {i['standing']}.")
        lines.append("")
    lines.append(SAYS)
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- self-test
def selftest() -> int:
    """Scratch workspaces in each state: each item appears once, with the right next step, and leaves when done."""
    results = []

    def check(name: str, ok) -> None:
        results.append((name, bool(ok)))

    A, XA, person = sf.A, explore.A, "human:throwaway-placeholder"
    sf.Study.default_model = "selftest-model"
    sf.Study.default_route = sf.PRACTICE
    sf.PLATFORM_CALL = sf._dead_platform
    sf.STAND_INS_COUNT = True
    quiet = contextlib.redirect_stdout(io.StringIO())
    with tempfile.TemporaryDirectory() as t, quiet:
        tmp = Path(t).resolve()
        ws = tmp / "ws"
        (ws / "studies").mkdir(parents=True)

        def now_() -> dict:
            return waiting([ws], sf.FACTORY)

        def items(what: str, path: str | None = None) -> list:
            return [i for g in now_()["groups"] for i in g["items"] if i["what"] == what and (path is None or g["path"] == path)]

        check("an empty workspace waits on nobody", now_()["counts"]["items"] == 0 and "Nothing waits" in in_words(now_()))
        # a study whose known-answer tests fail
        bad = sf._fresh(ws / "studies", "FAILING", start=A(id="FAILING", question=sf.PLAN["question"], by="agent:coordinating"))
        toy = (bad.d / "toy.py").read_text()
        (bad.d / "toy.py").write_text("import sys\nif sys.argv[1] == 'known-answers':\n    sys.exit(3)\n" + toy)
        with contextlib.suppress(Refused):
            sf.cmd_test(bad, A(what="known-answers", by="agent:analysis"))
        got = items("a-test-failed", "studies/FAILING")
        check("a failed known-answer test appears once, for the analysis agent, with the command to run it again",
              len(got) == 1 and got[0]["who"] == "agent:analysis" and "test known-answers --study studies/FAILING" in got[0]["next_step"]["command"])
        (bad.d / "toy.py").write_text(toy)
        sf.cmd_test(bad, A(what="known-answers", by="agent:analysis"))
        check("and leaves once the tests pass", not items("a-test-failed", "studies/FAILING"))
        # a lock request written and not merged
        s = sf._fresh(ws / "studies", "LOCKING", start=A(id="LOCKING", question=sf.PLAN["question"], by="agent:coordinating"))
        sf.cmd_test(s, A(what="known-answers", by="agent:analysis"))
        sf.cmd_test(s, A(what="working-data", by="agent:analysis"))
        check("a study whose tests pass and whose request is not written waits on no person", not [g for g in now_()["groups"] if g["path"] == "studies/LOCKING"])
        sf.cmd_request_lock(s, A(by="agent:coordinating"))
        got = items("lock-request-not-merged", "studies/LOCKING")
        check("a lock request written and not merged appears once, for people, with the evidence to read and the pull requests to open",
              len(got) == 1 and got[0]["who"] == "people" and "studies/LOCKING/lock-request/EVIDENCE.md" in got[0]["next_step"]["do"]
              and got[0]["next_step"]["open"].startswith("https://github.com/example-org/example-studies/pulls?q=")
              and got[0]["since"] == s.last("lock.requested")["at"])
        (s.d / "toy.py").write_text((s.d / "toy.py").read_text() + "\n# changed after the request\n")
        got = items("lock-request-not-merged", "studies/LOCKING")
        check("a request that no longer matches the files is not offered for approval: the coordinating agent writes it again",
              len(got) == 1 and got[0]["who"] == "agent:coordinating" and "request-lock --study studies/LOCKING" in got[0]["next_step"]["command"])
        (s.d / "toy.py").write_text((s.d / "toy.py").read_text().replace("\n# changed after the request\n", ""))
        sf.cmd_lock(s, A(by=person, evidence=sf.URL, local_practice=True))
        check("the item leaves when the lock is recorded", not items("lock-request-not-merged", "studies/LOCKING"))
        check("a practice lock is no act to verify, and the study waits on nobody", not [g for g in now_()["groups"] if g["path"] == "studies/LOCKING"])
        # a definition change blocking the opening
        planted = tmp / "factory-copy"
        shutil.copytree(sf.FACTORY, planted)
        w = waiting([ws], planted)
        got = [i for g in w["groups"] for i in g["items"] if i["what"] == "opening-blocked" and g["path"] == "studies/LOCKING"]
        check("the same definition copied elsewhere is the same tree: nothing blocks", not got)
        (planted / "agents" / "review" / "agent.md").write_text((planted / "agents" / "review" / "agent.md").read_text() + "\nAn edit after the lock.\n")
        w = waiting([ws], planted)
        got = [i for g in w["groups"] for i in g["items"] if i["what"] == "opening-blocked" and g["path"] == "studies/LOCKING"]
        check("a definition changed after the lock appears as blocking the opening, with what changed and a new lock request as the way on",
              len(got) == 1 and any("lock recorded" in r for r in got[0]["details"]["reasons"]) and "request-lock" in got[0]["next_step"]["command"])
        (ws / "factory-pin.yaml").write_text(yaml.safe_dump({"carried_on_old_version": [{"study": "studies/LOCKING", "commit_before_update": "a" * 40}]}))
        w = waiting([ws], planted)
        got = [i for g in w["groups"] for i in g["items"] if i["what"] == "opening-blocked" and g["path"] == "studies/LOCKING"]
        check("a study the factory update carried on its old version is told to open from a checkout of the commit before the update",
              len(got) == 1 and got[0]["next_step"]["command"] == f"git worktree add ../LOCKING-as-locked {'a' * 40}")
        (ws / "factory-pin.yaml").unlink()
        # an opening whose fetch failed, voidable
        (s.d / "fetch-is-down").write_text("down\n")
        with contextlib.suppress(Refused):
            sf.cmd_open_held_out(s, A(test="held-out", by="agent:coordinating", local_practice=True))
        got = items("opening-fetch-failed", "studies/LOCKING")
        check("an opening whose fetch failed and left nothing appears once, for a person, with the command that voids it",
              len(got) == 1 and got[0]["details"]["voidable"] and "void-unread --study studies/LOCKING --test held-out" in got[0]["next_step"]["command"])
        (s.d / "fetch-is-down").unlink()
        sf.cmd_void_unread(s, A(test="held-out", by=person, evidence=sf.URL, reason="the provider was down"))
        check("and leaves once a person voids it", not items("opening-fetch-failed", "studies/LOCKING"))
        sf.cmd_open_held_out(s, A(test="held-out", by="agent:coordinating", local_practice=True))
        sf.cmd_attach(s, A(by="agent:analysis", file=str(_file(tmp, "finding.md", sf.PRACTICE_WORDS + "\n\na finding\n"))))
        sf.cmd_review(s, A(by="agent:review", verdict="approve", file=str(_file(tmp, "v.md", "APPROVE"))))
        sf.cmd_request_signature(s, A(by="agent:coordinating", decision="signed", anchor=sf._posted(s), comment=None, evidence=None))
        got = items("signature-request-not-merged", "studies/LOCKING")
        check("a signature request written and not merged appears once, for the steward",
              len(got) == 1 and "the steward" in got[0]["wanted"] and "signature-request/EVIDENCE.md" in got[0]["next_step"]["do"])
        sf.cmd_signature(s, A(by=person, evidence=sf.URL, decision="signed", anchor=sf._posted(s), comment=None, local_practice=True))
        check("and leaves once the signature is recorded", not items("signature-request-not-merged", "studies/LOCKING"))

        # a study waiting on a release
        fd = sf.fresh_tool()
        src = tmp / "source"
        src.mkdir()
        months = [f"{y}-{m:02d}" for y in range(2020, 2027) for m in range(1, 13) if f"{y}-{m:02d}" <= "2026-07"]
        csv = src / "monthly.csv"
        csv.write_text("Source,Year,Mean\n" + "".join(f"A,{mo},{(i % 7) / 10:.4f}\n" for i, mo in enumerate(months)))
        meta = tmp / "metadata.yaml"
        fd.cmd_describe(fd.A(csv=str(csv), date_column="Year", series_column="Source", period="year", subject="record=toy-monthly",
                             what="a made-up monthly series", release="next-update", cadence="monthly", out=str(meta)))
        prop = tmp / "proposals" / "next.yaml"
        fd.cmd_propose(fd.A(metadata=str(meta), what="the next monthly updates", why="they come after every month explored",
                            unfair="a reprocessing of the old months would make it unfair", studies=str(ws / "studies"), out=str(prop),
                            kind="next-release", release="next-update", periods=3))
        r = sf.Study(ws / "studies" / "RELEASE")
        sf.cmd_start(r, A(id="RELEASE", question=sf.PLAN["question"], by="agent:coordinating", fresh_data=str(prop), working_data=[str(csv)]))
        plan = json.loads(json.dumps(sf.PLAN))
        plan["data"]["held_out"].update(window={"start": "2026-08-01", "end": "2026-10-31"}, pair={"record": "toy-monthly", "case": "RELEASE"},
                                        fresh_data=os.path.relpath(prop, r.d))
        (r.d / "toy.py").write_text(sf.TOY.replace("POWER", "0.9").replace("TESTED", "None"))
        r.plan_path.write_text(yaml.safe_dump(plan, sort_keys=False))
        sf.cmd_test(r, A(what="known-answers", by="agent:analysis"))
        sf.cmd_test(r, A(what="working-data", by="agent:analysis"))
        sf.cmd_lock(r, A(by=person, evidence=sf.URL, local_practice=True))
        try:
            sf.TODAY = "2026-09-15"
            got = items("waiting-on-a-data-release", "studies/RELEASE")
            check("a locked study whose release cannot be out yet appears once, with the cut-off, the periods the plan needs from the "
                  "metadata's cadence and how many have not ended", len(got) == 1 and got[0]["details"]["cut_off"] == "2026-07-31"
                  and got[0]["details"]["periods_needed"] == 3 and got[0]["details"]["periods_not_ended"] == 2
                  and "the release after 2026-07-31: 2 of 3 monthly period(s)" in got[0]["wanted"] and "2026-11-01" in got[0]["next_step"]["do"])
            sf.TODAY = "2026-11-27"
            check("and leaves when the last period has ended", not items("waiting-on-a-data-release", "studies/RELEASE"))
        finally:
            sf.TODAY = None

        # a merge found, not verified; and verified
        if shutil.which("git"):
            repo = tmp / "repo"
            (repo / "studies").mkdir(parents=True)
            g = lambda *w_: sf.git("-C", str(repo), "-c", "user.name=selftest", "-c", "user.email=s@example.invalid", "-c", "commit.gpgsign=false", *w_)  # noqa: E731
            sha = lambda ref="HEAD": g("rev-parse", ref).stdout.strip()  # noqa: E731
            g("init", "-q", "-b", "main")
            (repo / "README.md").write_text("throwaway\n")
            g("add", "-A"), g("commit", "-q", "-m", "start")
            g("checkout", "-q", "-b", "lock/M")
            m = sf._fresh(repo / "studies", "MERGED", start=A(id="MERGED", question=sf.PLAN["question"], by="agent:coordinating"))
            sf.cmd_test(m, A(what="known-answers", by="agent:analysis"))
            sf.cmd_test(m, A(what="working-data", by="agent:analysis"))
            sf.cmd_request_lock(m, A(by="agent:coordinating"))
            g("add", "-A"), g("commit", "-q", "-m", "lock request")
            head = sha()
            g("checkout", "-q", "main")
            g("merge", "-q", "--no-ff", "-m", "Merge the lock request", "lock/M")
            merge = sha()
            rec = tmp / "record.json"
            rec.write_text(json.dumps({"platform": "github", "pull_request": 7, "url": "https://github.example/o/r/pull/7", "author": "octo-author",
                                       "merged": True, "merge_commit": merge, "base": "main", "merged_by": "octo-steward",
                                       "approved": [{"login": "octo-steward", "commit_id": head}]}))
            route = sf.Study.default_route
            sf.Study.default_route = None
            try:
                sf.cmd_lock(m, A(by="platform:github", record_merge=merge, platform_record=str(rec), evidence=None))
                g("add", "-A"), g("commit", "-q", "-m", "record the lock")
                got = [i for gr in waiting([repo], sf.FACTORY)["groups"] for i in gr["items"] if i["what"] == "lock-merged-not-verified"]
                check("a lock merged and not verified appears once, standing as a merge found, not re-checked now, with the command "
                      "that asks GitHub", len(got) == 1 and got[0]["standing"].startswith(sf.MERGE_FOUND) and NOT_RECHECKED in got[0]["standing"]
                      and "verify-acts --study studies/MERGED" in got[0]["next_step"]["command"])
                check("its request is no longer listed as waiting to be merged",
                      not [i for gr in waiting([repo], sf.FACTORY)["groups"] for i in gr["items"] if i["what"] == "lock-request-not-merged"])
                with contextlib.suppress(Refused):
                    sf.cmd_open_held_out(m, A(test="held-out", by="agent:coordinating"))
                got = [i for gr in waiting([repo], sf.FACTORY)["groups"] for i in gr["items"] if i["what"] == "opening-refused"]
                check("an opening refused because GitHub could not be asked appears once, with the token as the way on, nothing used up",
                      len(got) == 1 and got[0]["details"]["result"] == sf.NOT_CHECKED and "GH_TOKEN=YOUR-READ-TOKEN" in got[0]["next_step"]["command"]
                      and "open-held-out --study studies/MERGED" in got[0]["next_step"]["command"] and not m.last("opening.started"))
                sf.PLATFORM_CALL = sf._stand_in_platform(m, "lock", merge, head)
                got = waiting([repo], sf.FACTORY)
                check("asked now and confirmed (a stand-in's answer, in this self-test only), the lock is verified and the item leaves",
                      not [i for gr in got["groups"] for i in gr["items"] if i["what"] == "lock-merged-not-verified"])
                sf.cmd_open_held_out(m, A(test="held-out", by="agent:coordinating"))
                check("and once the opening is made, the refused opening leaves too",
                      not [i for gr in waiting([repo], sf.FACTORY)["groups"] for i in gr["items"] if i["what"] == "opening-refused"])
            finally:
                sf.PLATFORM_CALL = sf._dead_platform
                sf.Study.default_route = route
        else:
            check("git is needed for the merged-lock checks", False)

        # explorations: a reviewed lead with no so what, try-instead, and an expert
        xw = tmp / "xw"
        (xw / "studies").mkdir(parents=True)
        x = _exploration_to_review(tmp, xw)
        got = [i for gr in waiting([xw], sf.FACTORY)["groups"] for i in gr["items"]]
        sw = [i for i in got if i["what"] == "so-what-wanted"]
        check("a reviewed lead with no so what appears once, for a person, with the lines of the comment for the tracking issue",
              len(sw) == 1 and sw[0]["who"] == "people" and f"lead: {sf.sha_file(x.d / 'lead.json')[:16]}" in sw[0]["next_step"]["do"]
              and "exploration: explorations/X1" in sw[0]["next_step"]["do"] and len(got) == 1)
        (xw / TRACKING).write_text("explorations/X1: 14\n")
        w = waiting([xw], sf.FACTORY)
        check("with tracking-issues.yaml, the group names its issue, the step opens it, and the issue is listed as waiting",
              w["groups"][0]["tracking_issue"]["number"] == 14 and w["groups"][0]["items"][0]["next_step"]["open"].endswith("/issues/14")
              and w["tracking_issues"] == [{"workspace": str(xw.resolve()), "path": "explorations/X1", "number": 14,
                                            "url": "https://github.com/example-org/example-studies/issues/14", "waiting": True}])
        lead = sf.sha_file(x.d / "lead.json")
        explore.cmd_so_what(x, XA(by=person, answer="try-instead", direction="look at the low end of the record", read_lead=lead, local_practice=True))
        got = [i for gr in waiting([xw], sf.FACTORY)["groups"] for i in gr["items"]]
        check("after try-instead, the so what is no longer wanted, and the direction waits for an agent to pick it up",
              [i["what"] for i in got] == ["try-instead-not-picked-up"] and got[0]["details"]["direction"] == "look at the low end of the record")
        explore.cmd_note(x, XA(by="agent:analysis-x", kind="missing", about="the low end", text="Looked at the low end, as asked.", evidence=None))
        check("and leaves once an agent has worked on it", not [i for gr in waiting([xw], sf.FACTORY)["groups"] for i in gr["items"]])
        w = waiting([xw], sf.FACTORY)
        check("an issue whose work waits on nobody is listed as not waiting, for the label to come off", w["tracking_issues"][0]["waiting"] is False)
        y = _exploration_to_review(tmp, xw, "X2")
        explore.cmd_so_what(y, XA(by=person, answer="needs-an-expert", expertise="someone who knows the gauge at low stage",
                                  read_lead=sf.sha_file(y.d / "lead.json"), local_practice=True))
        got = [i for gr in waiting([xw], sf.FACTORY)["groups"] for i in gr["items"] if gr["path"] == "explorations/X2"]
        check("a lead that needs an expert appears once, naming the expertise, its standing practice",
              [i["what"] for i in got] == ["expert-wanted"] and "the gauge at low stage" in got[0]["wanted"] and "practice" in got[0]["standing"])
        explore.cmd_so_what(y, XA(by=person, answer="not-interesting", reason="a shared source of error explains it",
                                  read_lead=sf.sha_file(y.d / "lead.json"), local_practice=True))
        check("and leaves once the expert answers", not [i for gr in waiting([xw], sf.FACTORY)["groups"] for i in gr["items"] if gr["path"] == "explorations/X2"])

        # a draft in the queue
        pages = xw / QUEUE / "pages"
        pages.mkdir(parents=True)
        page = pages / "a-pitfall.md"
        page.write_text("---\n" + yaml.safe_dump({"type": "pitfall", "title": "A pitfall seen while exploring", "status": "draft",
                                                  "generated": {"by": "selftest-model", "at": "2026-11-20T00:00:00Z"},
                                                  "drafted_from": {"exploration": "X1", "notes": ["NOTE-001"], "by": "agent:curating"}}) + "---\n\n# A pitfall\n")
        (pages.parent / "index.md").write_text("# Drafts waiting for the steward\n")
        got = [(gr["path"], i) for gr in waiting([xw], sf.FACTORY)["groups"] for i in gr["items"] if i["what"] == "draft-awaiting-the-steward"]
        check("a drafted page appears once, under the exploration it was drafted from, for a steward, since the time it was drafted",
              len(got) == 1 and got[0][0] == "explorations/X1" and got[0][1]["since"] == "2026-11-20T00:00:00Z"
              and got[0][1]["details"]["page"] == "knowledge-queue/pages/a-pitfall.md")
        w = waiting([xw], sf.FACTORY)
        check("the oldest group comes first", [gr["path"] for gr in w["groups"]][0] == "explorations/X1")
        page.unlink()
        check("and leaves when the steward has taken it out of the queue", not [i for gr in waiting([xw], sf.FACTORY)["groups"] for i in gr["items"]
                                                                               if i["what"] == "draft-awaiting-the-steward"])
        both = waiting([ws, xw], sf.FACTORY)
        check("several workspaces are listed together, each group saying its own", {gr["workspace"] for gr in both["groups"]} <= {str(ws.resolve()), str(xw.resolve())}
              and both["workspaces"] == [str(ws.resolve()), str(xw.resolve())])
        text = in_words(waiting([xw], sf.FACTORY))
        check("the plain words say how the standings were asked, and nothing is written into the workspace",
              NOT_RECHECKED in text and not (xw / "waiting.json").exists())
        z = _exploration_to_review(tmp, xw, "X3")
        breach = {"look": "LOOK-009", "what": ["a set-aside date"]}
        z.add("agent:analysis-x", "fence.breached", breach)
        got = [i for gr in waiting([xw], sf.FACTORY)["groups"] for i in gr["items"] if gr["path"] == "explorations/X3"]
        check("a spoiled exploration appears as blocked, for the analysis agent to end it as a stop", [i["what"] for i in got] == ["exploration-spoiled"]
              and "--outcome stop" in got[0]["next_step"]["command"])
        explore.cmd_end(z, XA(by="agent:analysis-x", outcome="stop", summary="spoiled: a set-aside date reached a look"))
        check("and leaves once it is ended as a stop", not [i for gr in waiting([xw], sf.FACTORY)["groups"] for i in gr["items"] if gr["path"] == "explorations/X3"])
        cli = sf.subprocess.run([sys.executable, str(Path(__file__).resolve()), "--workspace", str(xw), "--json"], capture_output=True, text=True,
                                env={k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN", "SF_PLATFORM_TOKEN")})
        check("the command prints the JSON its docstring documents", cli.returncode == 0 and json.loads(cli.stdout)["schema"] == SCHEMA
              and set(json.loads(cli.stdout)) == {"schema", "asked_at", "standings", "workspaces", "repository", "groups", "tracking_issues", "counts", "says"})
    failed = [n for n, ok in results if not ok]
    for n, ok in results:
        print(("PASS  " if ok else "FAIL  ") + n)
    print(f"selftest: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)} of {len(results)})")
    return 0 if not failed else 1


def _file(tmp: Path, name: str, text: str) -> Path:
    p = tmp / name
    p.write_text(text)
    return p


def _exploration_to_review(tmp: Path, ws: Path, name: str = "X1"):
    """An exploration in a workspace, taken to a reviewed lead: started with a year set aside, one look, a lead, a review."""
    A = explore.A
    x = explore.Exploration(ws / "explorations" / name)
    data = ws / "data" / name / "record.json"
    data.parent.mkdir(parents=True, exist_ok=True)
    data.write_text(json.dumps({"window": {"start": "2024-01-01", "end": "2024-12-31"},
                                "rows": [{"time": f"2024-{m:02d}-15T00:00:00Z", "x": m * 1.0, "y": m * 2.0} for m in range(1, 13)]}))
    request = _file(tmp, f"request-{name}.md", "# Request\n\nDoes y follow x, and where does it not?\n")
    explore.cmd_start(x, A(by="agent:analysis-x", request=str(request), id=name, subject=f"record=toy,case={name}",
                           set_aside_window="2025-01-01:2025-12-31", working_data=[str(data)], question="Does y follow x?"))
    explore.cmd_reviewer(x, A(by="agent:coordinating-x", reviewer="agent:review-x"))
    explore.cmd_known(x, A(by="agent:analysis-x", bundle=[]))
    (x.d / "looks").mkdir(exist_ok=True)
    (x.d / "looks" / "ratio.py").write_text("import json, sys\nrows = json.load(open(sys.argv[1]))['rows']\n"
                                            "print('rows', len(rows))\n")
    explore.cmd_look(x, A(by="agent:analysis-x", argv=["--", "{python}", "looks/ratio.py", str(data)], why="how many rows there are"))
    lead = {"summary": {"looks_true": "In 2024 y seems to follow x over twelve months.", "how_strong": "One look at one year of working data.",
                        "cannot_settle": "Whether it holds in 2025, which was set aside."},
            "what_looks_true": "y looks as if it follows x over the 2024 rows.", "how_it_was_found": "One look at the rows.",
            "evidence": ["LOOK-001"], "choices_that_would_change_it": [], "choices_that_would_not": [], "pitfalls": ["one year only"],
            "proposed_plan": {"question": "Over 2025, does y follow x within five percent?", "quantity_estimated": "the ratio of y to x",
                              "difference_that_matters": "five percent, proposed", "rule_sketch": "supported if the interval lies inside the band"}}
    lf = _file(tmp, f"lead-{name}.yaml", yaml.safe_dump(lead, sort_keys=False))
    explore.cmd_lead(x, A(by="agent:analysis-x", file=str(lf)))
    rv = _file(tmp, f"review-{name}.md", "# Review (exploring)\n\nChecked the log and the look. One hole: one year only.\n")
    explore.cmd_review(x, A(by="agent:review-x", verdict="holes-found", file=str(rv), read_lead=sf.sha_file(x.d / "lead.json")))
    return x


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    ap.add_argument("--workspace", action="append", type=Path, default=None, help="a workspace (studies/, explorations/, knowledge-queue/); repeatable (default: .)")
    ap.add_argument("--factory", type=Path, default=sf.FACTORY, help="the factory's definition (default: factory/ beside tools/)")
    ap.add_argument(sf.USE_ITS_CODE, dest="use_workspace_code", action="store_true", help=sf.USE_ITS_CODE_HELP)
    ap.add_argument("--json", action="store_true", help="print the JSON this docstring documents")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    try:
        sf.refuse_dirty_environment()
        sf.refuse_inside_a_look()
        if a.selftest:
            return selftest()
        sf.refuse_foreign_definition(a.factory, a.use_workspace_code, "waiting.py")
        sf.LIVE = {}  # each act is asked about once in this command
        w = waiting(a.workspace or [Path(".")], a.factory)
    except Refused as r:
        print(f"REFUSED: {r}", file=sys.stderr)
        return 2
    print(json.dumps(w, indent=1) if a.json else in_words(w), end="" if not a.json else "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
