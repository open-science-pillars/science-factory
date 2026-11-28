#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""report: what a workspace's studies and explorations did, counted from their logs.

For one workspace (`studies/`, `explorations/`), read from the logs and
nothing else, with no language model:

  - studies and explorations by stage, and by outcome: supported, refuted,
    inconclusive and run failed (a study's primary rule at its opening);
    lead, lead noted (a person said not interesting), note, method and
    stopped (an exploration's end, or a study closed before any opening);
    and no outcome yet;
  - the time spent at each stage, and the time spent waiting on a person
    (a lock or signature request to its merge, a reviewed lead to its so
    what), from the event times in the logs;
  - the models the logs record at each stage, beside what the definition
    declares, and the token and cost figures where an agent's event carries
    them (`--cost` on the study and exploring tools, never required); it
    says plainly where none are recorded;
  - the overclaiming warnings and the results of the definition's checks.

It ranks nothing and gives the factory no score, and the first line of the
report says why. Plain Markdown by default; `--html FILE` writes one page
that needs nothing beside it (no JavaScript, no file it links to), its
figures as small tables, for GitHub Pages; `--json` prints the numbers.

A stage's time runs from its first event to the first event of the next
stage the log reached; the stage a study is at now runs to the time the
report is made, and says "so far". Event times are the tools' own clock,
in UTC; time a person spent away from the tools is in the stage they were in.

Usage:
  report.py --workspace DIR [--factory DIR] [--out FILE] [--html FILE] [--json]
  report.py --selftest

The JSON (`--json`), schema `science-factory/report/v1`:
  {"schema", "made_at", "workspace", "definition": {"version", "sha256"}, "why_no_score",
   "studies": [{"path", "id", "kind", "stage", "outcome", "periods": [{"stage", "first_event", "from", "to", "seconds",
                "so_far", "waiting_on_a_person"}], "waiting_on_a_person_seconds", "models": {stage: {model: events}},
                "cost": {stage: {name: sum}} or null, "overclaiming": n, "checks": {check: result}}],
   "explorations": [the same, with "checks" holding the lead's overclaiming check],
   "totals": {"by_stage", "by_outcome", "seconds_by_stage", "waiting_on_a_person_seconds",
              "models_by_stage", "models_declared", "cost_by_stage" or null, "cost_note",
              "overclaiming": {"studies", "explorations"}, "checks": {check: {result: n}}}}
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
import html  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

import importlib.machinery  # noqa: E402
import importlib.util  # noqa: E402


class _SourceOnly(importlib.machinery.SourceFileLoader):
    """A module of this factory is loaded from its source text, compiled here, and never from cached bytecode beside it."""

    def get_code(self, fullname):
        return compile(self.get_data(self.path), self.path, "exec", dont_inherit=True)


HERE = Path(__file__).resolve().parent


def neighbour(name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py", loader=_SourceOnly(name, str(HERE / f"{name}.py")))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


waiting = neighbour("waiting")  # it loads the exploring tool, which loads the study tool: one copy of each
explore, sf = waiting.explore, waiting.sf
Refused = sf.Refused
SCHEMA = "science-factory/report/v1"
WHY_NO_SCORE = ("This report counts and ranks nothing: it gives no factory a score by how many findings were supported, because a "
                "factory rewarded for supported findings drifts toward agreeing with its claims, and a refuted or inconclusive result "
                "is as much a result as a supported one.")
OUTCOMES = ("supported", "refuted", "inconclusive", "run failed", "lead", "lead noted (not interesting)", "note", "method", "stopped", "no outcome yet")
STUDY_STAGES = ("ask and plan", "test", "lock (waiting on people)", "open", "review", "signature (waiting on people)", "learn and close")
EXPLORATION_STAGES = ("set aside and read what is known", "explore", "lead, review and so what", "ended")
NO_COST = ("No event in these logs carries a token or cost figure: none was recorded. An agent's command takes `--cost "
           "NAME=NUMBER,...` to record what its harness reported, declared like the model and proven by nothing.")


def when(t: str) -> dt.datetime:
    return dt.datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)


def seconds(a: str, b: str) -> int:
    return max(0, int((when(b) - when(a)).total_seconds()))


def span(s: int | None) -> str:
    if s is None:
        return "none"
    if s < 120:
        return f"{s} s"
    if s < 7200:
        return f"{s // 60} min"
    if s < 172800:
        return f"{s / 3600:.1f} h"
    return f"{s / 86400:.1f} days"


def first(ev: list, *kinds, after: int = -1):
    return next((e for e in ev if e["kind"] in kinds and e["seq"] > after), None)


def periods(marks: list, end_at, made_at: str, waiting_stages: tuple) -> list:
    """[{stage, first_event, from, to, seconds, so_far, waiting_on_a_person}] from the first event of each stage the log reached,
    in the log's order."""
    got = sorted(((name, e) for name, e in marks if e), key=lambda m: m[1]["seq"])
    out = []
    for i, (name, e) in enumerate(got):
        nxt = got[i + 1][1]["at"] if i + 1 < len(got) else (end_at or made_at)
        out.append({"stage": name, "first_event": e["seq"], "from": e["at"], "to": nxt, "seconds": seconds(e["at"], nxt),
                    "so_far": i + 1 == len(got) and not end_at, "waiting_on_a_person": name in waiting_stages})
    return out


def models_and_cost(ev: list, ps: list) -> tuple:
    """The models agents' events recorded, and the cost they declared, by the stage each event falls in (by its place in the log)."""
    models, cost = {}, {}
    for e in ev:
        if not str(e.get("actor", "")).startswith("agent:"):
            continue
        stage = next((p["stage"] for p in reversed(ps) if p["first_event"] <= e["seq"]), ps[0]["stage"] if ps else "before any stage")
        m = models.setdefault(stage, {})
        m[e.get("model") or "none recorded"] = m.get(e.get("model") or "none recorded", 0) + 1
        for k, v in (e.get("cost") or {}).items():
            c = cost.setdefault(stage, {})
            c[k] = round(c.get(k, 0) + v, 6)
    return models, cost or None


def study_outcome(ev: list, plan: dict | None) -> str:
    live = sf.last_live_opening(ev)
    if live:
        outs = live["data"].get("outcomes") or {}
        rules = (plan or {}).get("rules") or []
        primary = next((r["id"] for r in rules if isinstance(r, dict) and r.get("role") == "primary"), None) or next(iter(outs), None)
        o = outs.get(primary)
        return {"run-failed": "run failed"}.get(o, o or "no outcome yet")
    if any(e["kind"] == "study.closed" for e in ev):
        return "stopped"
    return "no outcome yet"


def study_report(d: Path, ws: Path, factory: Path, made_at: str) -> dict:
    study = sf.Study(d)
    ev = study.events()
    try:
        plan = sf.checked_plan(study)
    except Refused:
        plan = None
    try:
        stage = sf.stage_of(study, factory).get("stage")
    except Refused as r:
        stage = f"cannot be read ({r})"
    closed = first(ev, "study.closed")
    opened = first(ev, "opening.started")
    marks = [("ask and plan", first(ev, "study.started")), ("test", first(ev, "test.run", "rehearsal.run")),
             ("lock (waiting on people)", first(ev, "lock.requested")), ("open", first(ev, "lock.recorded")),
             ("review", first(ev, "opening.finished") if opened else None),
             ("signature (waiting on people)", first(ev, "signature.requested")), ("learn and close", first(ev, "signature.recorded"))]
    ps = periods(marks, closed["at"] if closed else None, made_at, ("lock (waiting on people)", "signature (waiting on people)"))
    models, cost = models_and_cost(ev, ps)
    try:
        checks = sf.run_checks(study, factory)
    except (Refused, OSError, ValueError, KeyError, TypeError) as r:
        checks = {"(the checks)": f"could not be worked out: {r}"}
    over = sf.study_overclaiming(study, factory, ev) or {}
    return {"path": d.relative_to(ws).as_posix(), "id": d.name, "kind": "system trial" if sf.is_system_trial(plan) else "confirming",
            "stage": stage, "outcome": study_outcome(ev, plan), "periods": ps,
            "waiting_on_a_person_seconds": sum(p["seconds"] for p in ps if p["waiting_on_a_person"]),
            "models": models, "cost": cost, "overclaiming": len(over.get("flags") or []), "checks": checks}


def exploration_report(d: Path, ws: Path, made_at: str) -> dict:
    x = explore.Exploration(d)
    ev = x.events()
    try:
        xs = explore.stage_of(x)
    except Refused as r:
        xs = {"stage": f"cannot be read ({r})"}
    ended = first(ev, "exploration.ended")
    marks = [("set aside and read what is known", first(ev, "exploration.started")), ("explore", first(ev, "look.run", "look.refused")),
             ("lead, review and so what", first(ev, "lead.recorded"))]
    ps = periods(marks, ended["at"] if ended else None, made_at, ())
    # waiting on a person: from each review to the so what that answered it, or to now while none has
    waited = 0
    for v in [e for e in ev if e["kind"] == "review.verdict"]:
        nxt = next((e for e in ev if e["seq"] > v["seq"] and e["kind"] in ("review.verdict", "lead.recorded", "lead.corrected", "so-what.recorded")), None)
        if nxt is not None and nxt["kind"] == "so-what.recorded":
            waited += seconds(v["at"], nxt["at"])
        elif nxt is None and xs.get("stage") == "so-what":
            waited += seconds(v["at"], made_at)
    models, cost = models_and_cost(ev, ps)
    outcome = (ended or {}).get("data", {}).get("outcome")
    outcome = {"lead-noted": "lead noted (not interesting)", "stop": "stopped", None: "no outcome yet"}.get(outcome, outcome)
    flags = len(xs.get("overclaiming") or [])
    return {"path": d.relative_to(ws).as_posix(), "id": d.name, "kind": "exploring", "stage": xs.get("stage"), "outcome": outcome, "periods": ps,
            "waiting_on_a_person_seconds": waited, "models": models, "cost": cost, "overclaiming": flags,
            "checks": {"overclaiming-in-leads": ("pending" if not first(ev, "lead.recorded") else "warn" if flags else "pass")}}


def report(ws: Path, factory: Path) -> dict:
    ws = Path(ws).resolve()
    if not ws.is_dir():
        raise Refused(f"{ws} is not a folder")
    made_at = sf.now()
    studies, xs, _queues = waiting.workspace_parts(ws)
    st = [study_report(d, ws, factory, made_at) for d in studies]
    ex = [exploration_report(d, ws, made_at) for d in xs]
    stamp = sf.definition_stamp(factory)
    tot = {"by_stage": {}, "by_outcome": {o: 0 for o in OUTCOMES}, "seconds_by_stage": {}, "waiting_on_a_person_seconds": 0, "models_by_stage": {},
           "models_declared": {a: m.get("model") for a, m in (stamp.get("models") or {}).items()}, "cost_by_stage": {}, "checks": {},
           "overclaiming": {"studies": sum(s["overclaiming"] for s in st), "explorations": sum(x["overclaiming"] for x in ex)}}
    for r in st + ex:
        key = f"{r['kind']}: {r['stage']}"
        tot["by_stage"][key] = tot["by_stage"].get(key, 0) + 1
        tot["by_outcome"][r["outcome"]] = tot["by_outcome"].get(r["outcome"], 0) + 1
        tot["waiting_on_a_person_seconds"] += r["waiting_on_a_person_seconds"]
        for p in r["periods"]:
            k = f"{'study' if r['kind'] != 'exploring' else 'exploration'}: {p['stage']}"
            tot["seconds_by_stage"][k] = tot["seconds_by_stage"].get(k, 0) + p["seconds"]
        for stage, ms in r["models"].items():
            k = f"{'study' if r['kind'] != 'exploring' else 'exploration'}: {stage}"
            for m, n in ms.items():
                tot["models_by_stage"].setdefault(k, {})[m] = tot["models_by_stage"].setdefault(k, {}).get(m, 0) + n
        for stage, c in (r["cost"] or {}).items():
            k = f"{'study' if r['kind'] != 'exploring' else 'exploration'}: {stage}"
            for name, v in c.items():
                tot["cost_by_stage"].setdefault(k, {})[name] = round(tot["cost_by_stage"].setdefault(k, {}).get(name, 0) + v, 6)
        for name, result in r["checks"].items():
            tot["checks"].setdefault(name, {})[result] = tot["checks"].setdefault(name, {}).get(result, 0) + 1
    tot["cost_by_stage"] = tot["cost_by_stage"] or None
    tot["cost_note"] = NO_COST if not tot["cost_by_stage"] else ("Token and cost figures as agents' events declared them (`--cost`), summed by "
                                                                 "stage; declared by whoever called the tools, like the model, and proven by nothing. "
                                                                 "An event with none adds nothing, so a sum covers only the events that carried one.")
    return {"schema": SCHEMA, "made_at": made_at, "workspace": str(ws), "definition": {"version": stamp.get("version"), "sha256": stamp.get("sha256")},
            "why_no_score": WHY_NO_SCORE, "studies": st, "explorations": ex, "totals": tot}


# ---------------------------------------------------------------- rendering
def tables(r: dict) -> list:
    """[(heading, paragraph or None, header, rows)]: the report as small tables, for Markdown and for HTML alike."""
    t = r["totals"]
    out = [("What there is, by stage", None, ["kind: stage", "how many"], [[k, n] for k, n in sorted(t["by_stage"].items())]),
           ("By outcome", "A study's outcome is its primary rule at its opening; an exploration's is how it ended. Counted, and graded by nothing.",
            ["outcome", "how many"], [[o, n] for o, n in t["by_outcome"].items()]),
           ("Time at each stage", "Summed over the studies and explorations at that stage, from the logs' event times.",
            ["kind: stage", "time"], [[k, span(s)] for k, s in t["seconds_by_stage"].items()]),
           ("Waiting on a person", "From a lock or signature request to its merge being recorded, and from a reviewed lead to a person's so what.",
            ["", "time"], [["all of it", span(t["waiting_on_a_person_seconds"])]]
            + [[x["path"], span(x["waiting_on_a_person_seconds"])] for x in r["studies"] + r["explorations"] if x["waiting_on_a_person_seconds"]]),
           ("Models", "Declared by the definition, and recorded by the logs' agent events at each stage; both are declarations, and nothing proves "
                      "which model answered.", ["where", "model", "events"],
            [[f"declared for the {a} agent", m, ""] for a, m in sorted(t["models_declared"].items())]
            + [[k, m, n] for k, ms in t["models_by_stage"].items() for m, n in sorted(ms.items())]),
           ("Tokens and cost", t["cost_note"], ["kind: stage", "figure", "sum"],
            [[k, name, v] for k, c in (t["cost_by_stage"] or {}).items() for name, v in sorted(c.items())]),
           ("Overclaiming warnings", "The overclaiming checks warn and never block.", ["in", "warnings"],
            [["findings and reviews of studies", t["overclaiming"]["studies"]], ["leads of explorations", t["overclaiming"]["explorations"]]]),
           ("The checks", "Each check of the definition, and how many studies or explorations gave each result; `pending` is not a pass.",
            ["check", "results"], [[name, ", ".join(f"{k} {v}" for k, v in sorted(res.items()))] for name, res in sorted(t["checks"].items())])]
    out.append(("Each study and exploration", None, ["path", "kind", "stage", "outcome", "time so far or in all", "waiting on a person"],
                [[x["path"], x["kind"], x["stage"], x["outcome"], span(sum(p["seconds"] for p in x["periods"])) + (" so far" if any(p["so_far"] for p in x["periods"]) else ""),
                  span(x["waiting_on_a_person_seconds"])] for x in r["studies"] + r["explorations"]]))
    return out


def title(r: dict) -> str:
    n, m = len(r["studies"]), len(r["explorations"])
    return f"What this workspace did: {n} {'study' if n == 1 else 'studies'}, {m} {'exploration' if m == 1 else 'explorations'}"


def markdown(r: dict) -> str:
    lines = [f"# {title(r)}", "", r["why_no_score"], "",
             f"Made at {r['made_at']} from the logs in {r['workspace']}, under definition {r['definition']['version']} "
             f"(sha256 {str(r['definition']['sha256'])[:16]}).", ""]
    for head, para, cols, rows in tables(r):
        lines += [f"## {head}", ""]
        if para:
            lines += [para, ""]
        if not rows:
            lines += ["None.", ""]
            continue
        lines += ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        lines += ["| " + " | ".join(str(c).replace("|", "/") for c in row) + " |" for row in rows]
        lines.append("")
    return "\n".join(lines)


CSS = ("body{font:15px/1.45 system-ui,sans-serif;max-width:52rem;margin:2rem auto;padding:0 1rem;color:#1f2937}"
       "h1{font-size:1.4rem}h2{font-size:1.1rem;margin-top:1.8rem}table{border-collapse:collapse;margin:.5rem 0}"
       "td,th{border:1px solid #d1d5db;padding:.25rem .6rem;text-align:left;vertical-align:top}th{background:#f3f4f6}"
       "p.why{border-left:4px solid #b45309;padding-left:.8rem}")


def html_page(r: dict) -> str:
    e = html.escape
    parts = ["<!DOCTYPE html>", '<html lang="en"><head><meta charset="utf-8">', '<meta name="viewport" content="width=device-width, initial-scale=1">',
             f"<title>What this workspace did</title><style>{CSS}</style></head><body>",
             f"<h1>{e(title(r))}</h1>",
             f'<p class="why">{e(r["why_no_score"])}</p>',
             f"<p>Made at {e(r['made_at'])} from the logs, under definition {e(str(r['definition']['version']))} "
             f"(sha256 {e(str(r['definition']['sha256'])[:16])}).</p>"]
    for head, para, cols, rows in tables(r):
        parts.append(f"<h2>{e(head)}</h2>")
        if para:
            parts.append(f"<p>{e(para)}</p>")
        if not rows:
            parts.append("<p>None.</p>")
            continue
        parts.append("<table><thead><tr>" + "".join(f"<th>{e(str(c))}</th>" for c in cols) + "</tr></thead><tbody>")
        parts += ["<tr>" + "".join(f"<td>{e(str(c))}</td>" for c in row) + "</tr>" for row in rows]
        parts.append("</tbody></table>")
    parts.append("</body></html>")
    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------- self-test
def selftest() -> int:
    results = []

    def check(name: str, ok) -> None:
        results.append((name, bool(ok)))

    A, XA, person = sf.A, explore.A, "human:throwaway-placeholder"
    sf.Study.default_model, sf.Study.default_route, sf.PLATFORM_CALL = "selftest-model", sf.PRACTICE, sf._dead_platform
    with tempfile.TemporaryDirectory() as t, contextlib.redirect_stdout(io.StringIO()):
        t = Path(t).resolve()
        ws = t / "ws"
        (ws / "studies").mkdir(parents=True)
        empty = report(ws, sf.FACTORY)
        check("an empty workspace gives a report that counts nothing and still says why it scores nothing",
              not empty["studies"] and not empty["explorations"] and WHY_NO_SCORE in markdown(empty) and all(v == 0 for v in empty["totals"]["by_outcome"].values()))
        check("with no cost in any log, the report says plainly that none was recorded", NO_COST in markdown(empty) and empty["totals"]["cost_by_stage"] is None)
        # a study taken through the opening to its signature, in practice, with a cost on one agent event
        s = sf._fresh(ws / "studies", "DONE", start=A(id="DONE", question=sf.PLAN["question"], by="agent:coordinating"))
        s.cost = {"input_tokens": 1000, "output_tokens": 200}
        sf.cmd_test(s, A(what="known-answers", by="agent:analysis"))
        s.cost = {"input_tokens": 500, "cost_usd": 0.02}
        sf.cmd_test(s, A(what="working-data", by="agent:analysis"))
        s.cost = None
        sf.cmd_request_lock(s, A(by="agent:coordinating"))
        sf.cmd_lock(s, A(by=person, evidence=sf.URL, local_practice=True))
        sf.cmd_open_held_out(s, A(test="held-out", by="agent:coordinating", local_practice=True))
        (t / "finding.md").write_text(sf.PRACTICE_WORDS + "\n\nThe gain clearly holds.\n")
        sf.cmd_attach(s, A(by="agent:analysis", file=str(t / "finding.md")))
        (t / "v.md").write_text("APPROVE")
        sf.cmd_review(s, A(by="agent:review", verdict="approve", file=str(t / "v.md")))
        sf.cmd_request_signature(s, A(by="agent:coordinating", decision="signed", anchor=sf._posted(s), comment=None, evidence=None))
        sf.cmd_signature(s, A(by=person, evidence=sf.URL, decision="signed", anchor=sf._posted(s), comment=None, local_practice=True))
        # a study refuted, and a study closed before any opening
        r = sf._fresh(ws / "studies", "REFUTED", start=A(id="REFUTED", question=sf.PLAN["question"], by="agent:coordinating"))
        (r.d / "toy.py").write_text((r.d / "toy.py").read_text().replace('json.dump({"value": 1.02}, open(out, "w"))', 'json.dump({"value": 1.5}, open(out, "w"))', 1))
        sf.cmd_test(r, A(what="known-answers", by="agent:analysis"))
        sf.cmd_test(r, A(what="working-data", by="agent:analysis"))
        sf.cmd_lock(r, A(by=person, evidence=sf.URL, local_practice=True))
        sf.cmd_open_held_out(r, A(test="held-out", by="agent:coordinating", local_practice=True))
        early = sf._fresh(ws / "studies", "EARLY", start=A(id="EARLY", question=sf.PLAN["question"], by="agent:coordinating"))
        sf.cmd_close(early, A(by="agent:coordinating", outcome="answered-by-existing-knowledge", cite="https://example.invalid/finding", comment=None))
        pending = sf._fresh(ws / "studies", "PENDING", start=A(id="PENDING", question=sf.PLAN["question"], by="agent:coordinating"))
        sf.cmd_test(pending, A(what="known-answers", by="agent:analysis"))
        sf.cmd_test(pending, A(what="working-data", by="agent:analysis"))
        sf.cmd_request_lock(pending, A(by="agent:coordinating"))
        # explorations: one waiting on a so what, one ended as a lead noted
        x1 = waiting._exploration_to_review(t, ws, "X1")
        x2 = waiting._exploration_to_review(t, ws, "X2")
        explore.cmd_so_what(x2, XA(by=person, answer="not-interesting", reason="a shared source of error explains it",
                                   read_lead=sf.sha_file(x2.d / "lead.json"), local_practice=True))
        rep = report(ws, sf.FACTORY)
        by = rep["totals"]["by_outcome"]
        check("studies and explorations are counted by outcome: supported, refuted, stopped, no outcome yet, and a lead noted",
              (by["supported"], by["refuted"], by["stopped"], by["lead noted (not interesting)"], by["no outcome yet"]) == (1, 1, 1, 1, 2))
        check("and by stage", rep["totals"]["by_stage"].get("exploring: so-what") == 1 and rep["totals"]["by_stage"].get("confirming: lock") == 1
              and rep["totals"]["by_stage"].get("confirming: closed") == 1)
        done = next(x for x in rep["studies"] if x["id"] == "DONE")
        check("a study's periods run in the order of its stages, each from its first event, and the last says so far",
              [p["stage"] for p in done["periods"]] == ["ask and plan", "test", "lock (waiting on people)", "open", "review", "signature (waiting on people)",
                                                       "learn and close"] and done["periods"][-1]["so_far"] and not done["periods"][0]["so_far"])
        check("the time waiting on a person is the lock and the signature requests' time, and nothing else",
              done["waiting_on_a_person_seconds"] == sum(p["seconds"] for p in done["periods"] if p["stage"].endswith("(waiting on people)")))
        check("the models recorded at each stage are counted, and the definition's declared models are shown beside them",
              done["models"]["test"] == {"selftest-model": 2} and set(rep["totals"]["models_declared"]) == {"analysis", "coordinating", "curating", "review"})
        check("the cost declared on agent events is summed by stage, and only those events count",
              done["cost"] == {"test": {"input_tokens": 1500, "output_tokens": 200, "cost_usd": 0.02}}
              and rep["totals"]["cost_by_stage"] == {"study: test": {"input_tokens": 1500, "output_tokens": 200, "cost_usd": 0.02}}
              and "proven by nothing" in rep["totals"]["cost_note"])
        check("the overclaiming warning of the finding is counted", done["overclaiming"] >= 1 and rep["totals"]["overclaiming"]["studies"] >= 1)
        check("every check of the definition is summarised by result, pending kept apart from pass",
              "chain-of-custody" in rep["totals"]["checks"] and sum(rep["totals"]["checks"]["chain-of-custody"].values()) == len(rep["studies"])
              and "overclaiming-in-leads" in rep["totals"]["checks"])
        x1r = next(x for x in rep["explorations"] if x["id"] == "X1")
        check("an exploration waiting on a so what counts its time waiting, up to now", x1r["stage"] == "so-what" and x1r["outcome"] == "no outcome yet"
              and x1r["periods"][-1]["so_far"])
        md = markdown(rep)
        check("the Markdown says first why it scores nothing, and has no score or ranking in it",
              md.splitlines()[2] == WHY_NO_SCORE and "rank" not in md.replace(WHY_NO_SCORE, "").lower() and "score" not in md.replace(WHY_NO_SCORE, "").lower())
        page = html_page(rep)
        check("the HTML page is one file: no script, no link to anything, its figures as tables", page.startswith("<!DOCTYPE html>") and "<script" not in page
              and "href=" not in page and "src=" not in page and page.count("<table>") == len(tables(rep)) - sum(1 for h in tables(rep) if not h[3]))
        cli = sf.subprocess.run([sys.executable, str(Path(__file__).resolve()), "--workspace", str(ws), "--json"], capture_output=True, text=True,
                                env={k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN", "SF_PLATFORM_TOKEN")})
        got = json.loads(cli.stdout) if cli.returncode == 0 else {}
        check("the command prints the JSON its docstring documents", got.get("schema") == SCHEMA
              and set(got) == {"schema", "made_at", "workspace", "definition", "why_no_score", "studies", "explorations", "totals"})
        out, page_file = t / "report.md", t / "report.html"
        cli = sf.subprocess.run([sys.executable, str(Path(__file__).resolve()), "--workspace", str(ws), "--out", str(out), "--html", str(page_file)],
                                capture_output=True, text=True, env={k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN")})
        check("--out and --html write the two files, and nothing is written into the workspace",
              cli.returncode == 0 and out.read_text().startswith("# What this workspace did") and "<table>" in page_file.read_text()
              and not list(ws.glob("report*")))
        _ = x1
    failed = [n for n, ok in results if not ok]
    for n, ok in results:
        print(("PASS  " if ok else "FAIL  ") + n)
    print(f"selftest: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)} of {len(results)})")
    return 0 if not failed else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    ap.add_argument("--workspace", type=Path, default=Path("."), help="the workspace (studies/, explorations/); default .")
    ap.add_argument("--factory", type=Path, default=sf.FACTORY, help="the factory's definition (default: factory/ beside tools/)")
    ap.add_argument(sf.USE_ITS_CODE, dest="use_workspace_code", action="store_true", help=sf.USE_ITS_CODE_HELP)
    ap.add_argument("--out", type=Path, default=None, help="write the Markdown here instead of printing it")
    ap.add_argument("--html", type=Path, default=None, help="also write one self-contained HTML page here")
    ap.add_argument("--json", action="store_true", help="print the JSON this docstring documents")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    try:
        sf.refuse_dirty_environment()
        sf.refuse_inside_a_look()
        if a.selftest:
            return selftest()
        sf.refuse_foreign_definition(a.factory, a.use_workspace_code, "report.py")
        sf.LIVE = {}
        r = report(a.workspace, a.factory)
    except Refused as r_:
        print(f"REFUSED: {r_}", file=sys.stderr)
        return 2
    if a.html:
        a.html.write_text(html_page(r))
    if a.json:
        print(json.dumps(r, indent=1))
    elif a.out:
        a.out.write_text(markdown(r))
    else:
        print(markdown(r), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
