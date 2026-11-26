#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""knowledge: the two deterministic helpers of the knowledge loop.

The organization's signed knowledge bundles are the long-term memory. This
tool adds no store. It reads a bundle before work starts and checks drafted
pages after, and it runs no language model: the assistants do the reading
and the drafting, and a steward signs.

  about          before work: list the concepts that bear on a question, by
                 tags, title, description, dataset and links, each with its
                 status and who signed it, so the work starts from what is
                 known, pitfalls included. With --drafts it also lists the
                 pages waiting in a queue, marked as drafts and not signed.
  check-drafts   after work: run the organization's own checker
                 (check_okf_v02.py) on a queue of drafted pages and apply
                 the rules of a queue. A draft is refused when it is not at
                 status draft, carries any `verified` event, has no sources,
                 does not say what it was drafted from, is a finding, or
                 bears on the same subject as a concept already in the
                 bundle without saying how it relates to it. Writes the
                 queue's index for the steward.
  selftest       the tool tests itself

What "signed" means here: a concept carries a `verified` event by a person
(`by: human:...`), the organization's rule. Only the organization's signing
tool writes one. Nothing in this package does, and a draft that arrives
with one is refused.

What the overlap check is, and is not. It finds a draft that shares a name,
a title, or several specific tags with a concept in the bundle. It cannot
read meaning, so it cannot find a contradiction: it makes the draft say how
it relates to each concept it overlaps (extends, narrows, corrects or
contradicts it), and a draft that says `contradicts` is listed first for
the steward. A draft that would only repeat a concept (`duplicates`) is
refused: the note is linked to the concept instead.

Usage: knowledge.py about --question "..." --bundle DIR [--drafts DIR]
       knowledge.py check-drafts --queue DIR --bundle DIR [--checker FILE]
       knowledge.py selftest [--checker FILE]
"""
import sys

sys.dont_write_bytecode = True
if __name__ == "__main__" and not sys.flags.safe_path and sys.path:
    _own = __file__.replace("\\", "/").rpartition("/")[0]
    del sys.path[0]
    sys.path[:] = [p for p in sys.path if p != _own]

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402

HERE = Path(__file__).resolve().parent
CHECKER = HERE.parent.parent / "nasa-daac-knowledge" / "tools" / "check_okf_v02.py"  # beside the package, as in README.md
NOT_CONCEPTS = ("index.md", "log.md", "DIGEST.md")
WORD = re.compile(r"[a-z0-9]+")
STOP = set("""a about above after again all also an and any are as at be because been before being below between both but by can could
did do does doing down during each few for from further had has have having he her here hers him his how i if in into is it its
just me more most my no nor not now of off on once only or other our out over own same she should so some such than that the
their them then there these they this those through to too under until up very was we well were what when where which while who
whom why will with would you your much many good bad""".split())
RELATIONS = ("extends", "narrows", "corrects", "contradicts", "duplicates")
MD_PATH = re.compile(r"[\w./-]+\.md")
GENERIC_SHARE = 0.25   # a tag carried by more than this share of a bundle says nothing about a subject
SHARED_TAGS = 3        # this many specific tags in common is the same subject


class Refused(Exception):
    pass


def sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def front_matter(path: Path) -> tuple:
    """(the front matter as a mapping or None, the body)."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, text
    lines = text.split("\n")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            try:
                fm = yaml.safe_load("\n".join(lines[1:i])) or {}
            except yaml.YAMLError:
                return None, text
            return (fm if isinstance(fm, dict) else None), "\n".join(lines[i + 1:])
    return None, text


def events_of(fm: dict) -> list:
    v = fm.get("verified")
    return [e for e in (v if isinstance(v, list) else [v] if v else []) if isinstance(e, dict)]


def signed_by(fm: dict) -> tuple:
    """(signed?, the people who signed). Signed means a `verified` event by a person."""
    people = [str(e["by"]) for e in events_of(fm) if str(e.get("by", "")).startswith("human:")]
    return bool(people), people


def words(text) -> set:
    return {w for w in WORD.findall(str(text or "").casefold()) if len(w) > 2 and w not in STOP}


def concepts(root: Path) -> list:
    """Every concept under a bundle or a queue: (path, front matter, body)."""
    out = []
    for p in sorted(Path(root).rglob("*.md")):
        if p.name in NOT_CONCEPTS:
            continue
        fm, body = front_matter(p)
        if fm is not None:
            out.append((p, fm, body))
    return out


def shown(root: Path, p: Path) -> str:
    """A concept's path as people cite it: the repository, the bundle folder, the path below it."""
    root = Path(root).resolve()
    return (Path(root.parent.name) / root.name / p.resolve().relative_to(root)).as_posix()


def tags_of(fm: dict) -> set:
    t = fm.get("tags")
    return {str(x).casefold() for x in t} if isinstance(t, list) else set()


def links_of(p: Path, fm: dict, body: str, root: Path) -> set:
    """The concepts one concept points at: its `dataset`, and every .md path its body names that exists in the bundle."""
    out, root = set(), Path(root).resolve()
    for ref in [str(fm.get("dataset") or "")] + MD_PATH.findall(body):
        if not ref:
            continue
        for base in (p.parent, root, root.parent):
            q = (base / ref).resolve()
            if q.is_file() and q.is_relative_to(root) and q != p.resolve():
                out.add(q)
                break
    return out


def about(question: str, bundles: list, drafts: list | None = None, tags: list | None = None, limit: int = 12) -> list:
    """The concepts that bear on a question, best match first, then the concepts those link to."""
    asked = words(question) | {str(t).casefold() for t in tags or []}
    if not asked:
        raise Refused("the question has no words to search by")
    found = []
    for root, queued in [(Path(b), False) for b in bundles] + [(Path(d), True) for d in drafts or []]:
        if not Path(root).is_dir():
            raise Refused(f"{root} is not a directory")
        entries = concepts(root)
        by_path = {p.resolve(): (p, fm, body) for p, fm, body in entries}
        hits = {}
        for p, fm, body in entries:
            why = []
            for label, got, weight in (("tags", tags_of(fm) & asked, 3), ("name", words(p.stem.replace("-", " ")) & asked, 2),
                                       ("title", words(fm.get("title")) & asked, 2), ("description", words(fm.get("description")) & asked, 1)):
                if got:
                    why.append((label, sorted(got), weight * len(got)))
            score = sum(w for _, _, w in why)
            if score >= 4:
                hits[p.resolve()] = (score, "; ".join(f"{label}: {', '.join(got)}" for label, got, _ in why))
        top = dict(sorted(hits.items(), key=lambda kv: (-kv[1][0], str(kv[0])))[:limit])
        linked = {}
        for q in top:
            p, fm, body = by_path[q]
            for target in links_of(p, fm, body, root):
                if target in by_path and target not in top:
                    linked.setdefault(target, (0, f"linked from {p.name}"))
        for q, (score, why) in {**top, **linked}.items():
            p, fm, _ = by_path[q]
            signed, people = signed_by(fm)
            at = next((str(e.get("at")) for e in events_of(fm) if str(e.get("by", "")).startswith("human:")), None)
            found.append({"path": shown(root, p), "file": str(p.resolve()), "sha256": sha_file(p), "type": fm.get("type"),
                          "title": fm.get("title"), "status": fm.get("status"), "signed": signed, "signed_by": people, "signed_at": at,
                          "generated_by": (fm.get("generated") or {}).get("by") if isinstance(fm.get("generated"), dict) else None,
                          "severity": fm.get("severity"), "stale_after": str(fm.get("stale_after")) if fm.get("stale_after") else None,
                          "in_queue": queued, "score": score,
                          "why": why + ("; a DRAFT in the steward's queue, not signed" if queued else "")})
    found.sort(key=lambda c: (-c["score"], c["path"]))
    return found


def trust(c: dict) -> str:
    if c["in_queue"]:
        return f"DRAFT IN THE QUEUE, NOT SIGNED (status {c['status']}; drafted by {c['generated_by']}): use it as a draft and say so"
    if c["signed"]:
        return f"SIGNED by {', '.join(c['signed_by'])}" + (f" at {c['signed_at']}" if c["signed_at"] else "") + f"; status {c['status']}"
    return f"NOT SIGNED (status {c['status']}; written by {c['generated_by']})"


def render(found: list) -> str:
    if not found:
        return "nothing in the knowledge bears on this question by tags, name, title or description. That is a result: say so, and raise a note if something should be there."
    out = [f"{len(found)} concept(s) bear on the question. Read each before looking at data.", ""]
    for i, c in enumerate(found, 1):
        out += [f"{i}. {c['path']}  [{c['type']}" + (f", severity {c['severity']}" if c["severity"] else "") + "]",
                f"   {trust(c)}", f"   {c['title']}", f"   bears on the question by {c['why']}", f"   file: {c['file']}", ""]
    return "\n".join(out).rstrip()


def cmd_about(a) -> int:
    found = about(a.question, a.bundle, a.drafts or [], a.tag or [], a.limit)
    print(json.dumps(found, indent=1) if a.json else render(found))
    return 0


# ---- the queue of drafts --------------------------------------------------
def overlaps(draft: tuple, bundle_entries: list, generic: set) -> list:
    """The bundle concepts a draft bears on the same subject as, each with why."""
    p, fm, _ = draft
    mine, title = tags_of(fm) - generic, " ".join(sorted(words(fm.get("title"))))
    out = []
    for q, other, _ in bundle_entries:
        theirs = tags_of(other) - generic
        shared = mine & theirs
        why = None
        if q.stem == p.stem:
            why = "the same file name"
        elif title and title == " ".join(sorted(words(other.get("title")))):
            why = "the same title"
        elif len(shared) >= SHARED_TAGS or (len(shared) >= 2 and len(shared) / max(1, len(mine | theirs)) >= 0.5):
            why = "shared tags: " + ", ".join(sorted(shared))
        if why:
            out.append((q, other, why))
    return out


def draft_problems(draft: tuple, queue: Path, bundles: list, bundle_entries: dict, generic: dict) -> tuple:
    """(problems, the relations the draft declares, the concepts it overlaps)."""
    p, fm, body = draft
    name, problems = p.relative_to(queue).as_posix(), []
    if fm.get("status") != "draft":
        problems.append(f"{name}: status is `{fm.get('status')}`; a page in the queue is at status draft until a steward signs it")
    if "verified" in fm:
        problems.append(f"{name}: it carries a `verified` event. No assistant signs: only the steward's signing tool adds one, after the merge")
    gen = fm.get("generated")
    if not isinstance(gen, dict) or not str(gen.get("by") or "").strip() or not gen.get("at"):
        problems.append(f"{name}: `generated` says who drafted it and when ({{by: ..., at: ...}})")
    elif str(gen["by"]).startswith("human:"):
        problems.append(f"{name}: `generated.by` names a person; a draft from this loop is generated by the assistant that wrote it")
    sources = fm.get("sources")
    if not isinstance(sources, list) or not sources or not all(isinstance(s, dict) and str(s.get("resource") or "").strip() for s in sources):
        problems.append(f"{name}: it has no sources; every drafted page cites where each thing it says comes from")
    if str(fm.get("type") or "").strip().casefold() == "finding":
        problems.append(f"{name}: it is a finding. A finding comes from a confirming study and a steward's signature, never from a draft")
    src = fm.get("drafted_from")
    if not isinstance(src, dict) or not (src.get("exploration") or src.get("study")) or not (src.get("notes") or src.get("lead")):
        problems.append(f"{name}: `drafted_from` names the exploration or study and the notes or the lead it was drafted from")
    elif src.get("exploration") and "exploring" not in str(fm.get("seen_while") or "") + body.casefold():
        problems.append(f"{name}: it was drafted from an exploration and does not say so; say what was seen while exploring and is not tested")
    declared = fm.get("relates_to") or []
    relations = {}
    if not isinstance(declared, list):
        problems.append(f"{name}: `relates_to` is a list of {{concept, relation, why}}")
        declared = []
    for r in declared:
        if not isinstance(r, dict) or r.get("relation") not in RELATIONS or not str(r.get("why") or "").strip() or not r.get("concept"):
            problems.append(f"{name}: each `relates_to` entry is {{concept: a path in the bundle, relation: one of {', '.join(RELATIONS)}, why: words}}")
            continue
        target = next(((b / str(r["concept"])).resolve() for b in bundles if (b / str(r["concept"])).is_file()), None)
        if target is None:
            problems.append(f"{name}: `relates_to` names {r['concept']}, which is not in the bundle")
            continue
        relations[target] = r
        if r["relation"] == "duplicates":
            problems.append(f"{name}: it says it duplicates {r['concept']}. A duplicate is not queued: link the note to that concept instead")
    over = []
    for b in bundles:
        over += overlaps(draft, bundle_entries[b], generic[b])
    for q, other, why in over:
        if q.resolve() not in relations:
            signed, people = signed_by(other)
            problems.append(f"{name}: it bears on the same subject as {shown(next(b for b in bundles if q.resolve().is_relative_to(b.resolve())), q)} "
                            f"({'signed by ' + ', '.join(people) if signed else 'not signed, status ' + str(other.get('status'))}; {why}) and does "
                            "not say how it relates to it. Add a `relates_to` entry: extends, narrows, corrects or contradicts")
    return problems, relations, over


def check_drafts(queue: Path, bundles: list, checker: Path) -> tuple:
    """(problems, the queue as a mapping). Nothing is written when there is a problem."""
    queue, bundles = Path(queue).resolve(), [Path(b).resolve() for b in bundles]
    if not queue.is_dir():
        raise Refused(f"the queue {queue} is not a directory")
    if not Path(checker).is_file():
        raise Refused(f"the organization's checker is not at {checker}; name it with --checker (it is tools/check_okf_v02.py in nasa-daac-knowledge)")
    problems = []
    run = subprocess.run([sys.executable, "-I", str(checker), str(queue)], capture_output=True, text=True)
    report = run.stdout.strip().splitlines()
    if run.returncode != 0:
        problems += ["the organization's checker: " + ln for ln in report if re.match(r"^[EF]\d", ln)] or [
            "the organization's checker failed: " + (run.stderr.strip() or run.stdout.strip())[-300:]]
    for p in sorted(queue.rglob("*.md")):
        if p.name not in NOT_CONCEPTS and front_matter(p)[0] is None:
            problems.append(f"{p.relative_to(queue).as_posix()}: no front matter that parses; the queue holds concepts only")
    drafts = concepts(queue)
    bundle_entries = {b: concepts(b) for b in bundles}
    generic = {}
    for b, entries in bundle_entries.items():
        counts = {}
        for _, fm, _ in entries:
            for t in tags_of(fm):
                counts[t] = counts.get(t, 0) + 1
        generic[b] = {t for t, n in counts.items() if n > GENERIC_SHARE * max(1, len(entries))}
    listing, seen = [], {}
    for d in drafts:
        probs, relations, _ = draft_problems(d, queue, bundles, bundle_entries, generic)
        problems += probs
        p, fm, _ = d
        key = " ".join(sorted(words(fm.get("title"))))
        if key in seen or p.stem in {q.stem for q in seen.values()}:
            problems.append(f"{p.relative_to(queue).as_posix()}: the queue already holds a draft with this title or name")
        seen[key] = p
        listing.append({"path": p.relative_to(queue).as_posix(), "sha256": sha_file(p), "type": fm.get("type"), "title": fm.get("title"),
                        "status": fm.get("status"), "signed": False, "generated_by": (fm.get("generated") or {}).get("by") if isinstance(fm.get("generated"), dict) else None,
                        "drafted_from": fm.get("drafted_from"),
                        "relates_to": [{"concept": r["concept"], "relation": r["relation"], "why": r["why"]} for r in relations.values()],
                        "contradicts_a_concept": any(r["relation"] == "contradicts" for r in relations.values())})
    listing.sort(key=lambda d: (not d["contradicts_a_concept"], d["path"]))
    return problems, {"for": "the steward", "drafts": listing, "signed": 0, "checker": {"file": Path(checker).name, "sha256": sha_file(Path(checker)),
                                                                                        "last_line": report[-1] if report else ""},
                      "says": "every page here is a draft. None is signed, and no assistant signs: a steward reads each, merges it "
                              "into the bundle by pull request, and signs with the organization's signing tool"}


def write_queue(queue: Path, q: dict) -> None:
    (queue / "queue.json").write_text(json.dumps(q, indent=1) + "\n")
    lines = ['---', 'okf_version: "0.2"', '---', '', '# Drafts waiting for the steward', '',
             q["says"][0].upper() + q["says"][1:] + ".", ""]
    for d in q["drafts"]:
        rel = "; ".join(f"{r['relation']} {r['concept']}" for r in d["relates_to"])
        lines.append(f"- [{d['title']}]({d['path']}), status: draft, not signed" + (f" ({rel})" if rel else "")
                     + (" **contradicts a concept in the bundle: steward review first**" if d["contradicts_a_concept"] else ""))
    (queue / "index.md").write_text("\n".join(lines) + "\n")


def cmd_check_drafts(a) -> int:
    problems, q = check_drafts(Path(a.queue), [Path(b) for b in a.bundle], Path(a.checker))
    for p in problems:
        print("check-drafts:", p)
    if problems:
        raise Refused(f"{len(problems)} problem(s): the queue is not ready for the steward, and its index is not written")
    write_queue(Path(a.queue).resolve(), q)
    print(f"check-drafts: PASS. {len(q['drafts'])} draft(s) in the queue for the steward, none signed"
          + (f", {sum(d['contradicts_a_concept'] for d in q['drafts'])} of them say they contradict a concept in the bundle"
             if any(d["contradicts_a_concept"] for d in q["drafts"]) else "") + f". The organization's checker: {q['checker']['last_line']}")
    return 0


# ---- the self-test --------------------------------------------------------
def selftest(checker: Path) -> int:
    results = []

    def ok(name: str, cond) -> None:
        results.append((name, bool(cond)))

    if not Path(checker).is_file():
        print(f"selftest: FAIL (the organization's checker is not at {checker}; name it with --checker)")
        return 1
    tmp = Path(tempfile.mkdtemp(prefix="knowledge-selftest-")).resolve()
    try:
        bundle = tmp / "hydro" / "knowledge"
        for sub in ("gotchas", "recipes", "datasets"):
            (bundle / sub).mkdir(parents=True)
        (bundle / "index.md").write_text('---\nokf_version: "0.2"\n---\n\n# toy\n')

        def concept(rel: str, title: str, tags: str, extra: str = "", body: str = "Body.") -> Path:
            p = bundle / rel
            p.write_text(f"---\ntype: {'recipe' if rel.startswith('recipes') else 'dataset' if rel.startswith('datasets') else 'dataset-gotcha'}\n"
                         f"spheres: [hydrosphere]\ntitle: \"{title}\"\ndescription: \"{title}\"\ntags: [{tags}]\n"
                         f"generated: {{ by: claude-code/test, at: 2026-01-01T00:00:00Z }}\n{extra}status: stable\n---\n\n# {title}\n\n{body}\n")
            return p

        signed = "verified: { by: human:toy-steward, at: 2026-01-02T00:00:00Z }\n"
        concept("recipes/river-gauge-confrontation.md", "Confronting a satellite river elevation with a gauge", "swot, confrontation, gauge, stage, hydrology",
                signed, "See `knowledge/datasets/reach-product.md` and the datum gotcha.")
        concept("datasets/reach-product.md", "The reach product", "riversp, product, hydrology", signed)
        concept("gotchas/datum.md", "A satellite elevation and a gauge are on different datums", "swot, datum, gauge, elevation, hydrology",
                "dataset: ../datasets/reach-product.md\n")
        concept("gotchas/soil.md", "Soil moisture radar loss", "smap, radar, hydrology", signed)
        concept("gotchas/machine.md", "Gauge stage is provisional", "gauge, provisional, stage, hydrology", "verified: { by: process:ci, at: 2026-01-02T00:00:00Z }\n")

        found = about("How well does SWOT river height follow the gauge?", [bundle])
        paths = [c["path"] for c in found]
        ok("about finds the concepts that bear on the question", "hydro/knowledge/recipes/river-gauge-confrontation.md" in paths and "hydro/knowledge/gotchas/datum.md" in paths)
        ok("about leaves out what does not bear on it", "hydro/knowledge/gotchas/soil.md" not in paths)
        ok("about follows a link to a concept the words did not find", any(c["path"].endswith("datasets/reach-product.md") and "linked from" in c["why"] for c in found))
        by = {c["path"].rsplit("/", 1)[1]: c for c in found}
        ok("about says who signed a signed concept", by["river-gauge-confrontation.md"]["signed"] and by["river-gauge-confrontation.md"]["signed_by"] == ["human:toy-steward"])
        ok("about says a concept nobody signed is not signed", not by["datum.md"]["signed"] and "NOT SIGNED" in trust(by["datum.md"]))
        ok("a machine's `verified` event is not a signature", not by["machine.md"]["signed"])
        ok("about puts the best match first", found[0]["path"].endswith("river-gauge-confrontation.md"))
        ok("about says so when nothing bears on the question", "nothing in the knowledge bears" in render(about("Does the ocean close its heat budget?", [bundle])))
        ok("about refuses a question with no words", _refuses(about, "is it?", [bundle]))

        queue = tmp / "queue"
        (queue / "gotchas").mkdir(parents=True)
        base = {"type": "dataset-gotcha", "spheres": ["hydrosphere"], "title": "Passes flagged degraded sit at low stage",
                "description": "what was seen while exploring one year at one reach", "tags": ["reach_q", "low-stage", "quality"],
                "generated": {"by": "claude-code/test", "at": "2026-11-25T00:00:00Z"}, "status": "draft", "seen_while": "exploring",
                "drafted_from": {"exploration": "EXPLORATION-0001", "notes": ["NOTE-001"]},
                "sources": [{"id": "look", "resource": "https://example.invalid/exploration/receipts/LOOK-003.json", "title": "the look"}]}

        def draft(name: str = "gotchas/degraded-at-low-stage.md", body: str = "Seen while exploring.[^look]\n\n[^look]: the look", **change) -> Path:
            fm = {k: v for k, v in {**base, **change}.items() if v is not None}
            p = queue / name
            p.write_text("---\n" + yaml.safe_dump(fm, sort_keys=False) + "---\n\n# " + str(fm.get("title")) + "\n\n" + body + "\n")
            return p

        def problems() -> list:
            return check_drafts(queue, [bundle], checker)[0]

        d = draft()
        ok("a complete draft passes, and the organization's checker ran on it", problems() == [])
        q = check_drafts(queue, [bundle], checker)[1]
        ok("the queue lists the draft as not signed", q["drafts"][0]["signed"] is False and q["signed"] == 0 and "conformant" in q["checker"]["last_line"])
        draft(status="stable")
        ok("a draft marked stable is refused", any("status is `stable`" in p for p in problems()))
        draft(verified={"by": "human:someone", "at": "2026-11-25T00:00:00Z"})
        ok("a draft marked as signed by a person is refused", any("`verified` event" in p for p in problems()))
        draft(verified={"by": "process:ci", "at": "2026-11-25T00:00:00Z"})
        ok("a draft with any `verified` event is refused", any("`verified` event" in p for p in problems()))
        draft(sources=None)
        ok("a draft without sources is refused", any("no sources" in p for p in problems()))
        draft(sources=[{"id": "look", "title": "no resource"}])
        ok("a draft whose source names no resource is refused, by this tool and by the organization's checker",
           any("no sources" in p for p in problems()) and any("organization's checker: E7" in p for p in problems()))
        draft(drafted_from=None)
        ok("a draft that does not say what it was drafted from is refused", any("drafted_from" in p for p in problems()))
        draft(seen_while=None, body="A claim.[^look]\n\n[^look]: the look")
        ok("a draft from an exploration that does not say it was exploring is refused", any("does not say so" in p for p in problems()))
        draft(type="finding")
        ok("a draft that is a finding is refused", any("it is a finding" in p for p in problems()))
        draft(generated={"by": "human:someone", "at": "2026-11-25T00:00:00Z"})
        ok("a draft that says a person generated it is refused", any("names a person" in p for p in problems()))
        draft(status="verified")
        ok("a status outside the format is refused", any("status is `verified`" in p for p in problems()))
        draft(spheres=None)
        ok("a draft the organization's checker fails is refused with the checker's own line", any("organization's checker: E10" in p for p in problems()))
        draft(tags=["swot", "datum", "gauge", "elevation"])
        ok("a draft on the same subject as a bundle concept, without saying so, is refused", any("same subject as hydro/knowledge/gotchas/datum.md" in p for p in problems()))
        draft(tags=["swot", "datum", "gauge", "elevation"], relates_to=[{"concept": "gotchas/datum.md", "relation": "extends", "why": "adds the river case"}])
        ok("the same draft passes once it says how it relates", problems() == [])
        draft(tags=["swot", "datum", "gauge", "elevation"], relates_to=[{"concept": "gotchas/datum.md", "relation": "contradicts", "why": "the offset is not constant here"}])
        probs, q = check_drafts(queue, [bundle], checker)
        ok("a draft that says it contradicts a concept is queued and flagged for the steward", probs == [] and q["drafts"][0]["contradicts_a_concept"])
        draft(tags=["swot", "datum", "gauge", "elevation"], relates_to=[{"concept": "gotchas/datum.md", "relation": "duplicates", "why": "the same"}])
        ok("a draft that says it duplicates a concept is refused", any("A duplicate is not queued" in p for p in problems()))
        draft(relates_to=[{"concept": "gotchas/nowhere.md", "relation": "extends", "why": "x"}])
        ok("a relation to a concept that is not in the bundle is refused", any("not in the bundle" in p for p in problems()))
        draft(relates_to=[{"concept": "gotchas/datum.md", "relation": "agrees", "why": "x"}])
        ok("a relation outside the list is refused", any("each `relates_to` entry" in p for p in problems()))
        draft(title="A satellite elevation and a gauge are on different datums")
        ok("a draft with the title of a bundle concept is refused", any("the same title" in p for p in problems()))
        d.unlink()
        draft(name="gotchas/datum.md")
        ok("a draft with the file name of a bundle concept is refused", any("the same file name" in p for p in problems()))
        (queue / "gotchas/datum.md").unlink()
        draft()
        draft(name="gotchas/again.md")
        ok("two drafts with one title are refused", any("already holds a draft" in p for p in problems()))
        (queue / "gotchas/again.md").unlink()
        (queue / "notes.md").write_text("# loose notes\n")
        ok("a page in the queue that is not a concept is refused", any("no front matter" in p for p in problems()))
        (queue / "notes.md").unlink()
        ok("check-drafts refuses and writes no index when there is a problem",
           (draft(status="stable") and _refuses(cmd_check_drafts, argparse.Namespace(queue=str(queue), bundle=[str(bundle)], checker=str(checker)))
            and not (queue / "index.md").exists()))
        draft()
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_check_drafts(argparse.Namespace(queue=str(queue), bundle=[str(bundle)], checker=str(checker)))
        ok("check-drafts writes the queue's index for the steward, and the queue still passes with it there",
           "not signed" in (queue / "index.md").read_text() and problems() == [])
        both = about("Where do passes flagged degraded sit, by stage?", [bundle], [queue])
        ok("about lists a queued draft as a draft that is not signed",
           any(c["in_queue"] and "DRAFT IN THE QUEUE, NOT SIGNED" in trust(c) for c in both))
        ok("check-drafts refuses when the organization's checker is missing", _refuses(check_drafts, queue, [bundle], tmp / "no-checker.py"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, good in results if not good]
    for n in failed:
        print("FAIL:", n)
    print(f"selftest: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)} of {len(results)})")
    return 0 if not failed else 1


def _refuses(fn, *args) -> bool:
    try:
        fn(*args)
    except Refused:
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("about")
    p.add_argument("--question", required=True)
    p.add_argument("--bundle", action="append", required=True, type=Path, help="a knowledge bundle directory; repeatable")
    p.add_argument("--drafts", action="append", default=None, type=Path, help="a queue of drafted pages; repeatable")
    p.add_argument("--tag", action="append", default=None, help="a tag to search by as well; repeatable")
    p.add_argument("--limit", type=int, default=12)
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_about)
    p = sub.add_parser("check-drafts")
    p.add_argument("--queue", required=True)
    p.add_argument("--bundle", action="append", required=True, help="the bundle the drafts would join; repeatable")
    p.add_argument("--checker", default=str(CHECKER), help="the organization's checker (default: nasa-daac-knowledge beside this package)")
    p.set_defaults(fn=cmd_check_drafts)
    p = sub.add_parser("selftest")
    p.add_argument("--checker", default=str(CHECKER))
    a = ap.parse_args()
    try:
        if a.cmd == "selftest":
            return selftest(Path(a.checker))
        return a.fn(a)
    except Refused as r:
        print(f"REFUSED: {r}", file=sys.stderr)
        return 2
    except (KeyError, TypeError, ValueError, AttributeError, OSError) as e:
        print(f"REFUSED: a file could not be read ({type(e).__name__}: {e})", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
