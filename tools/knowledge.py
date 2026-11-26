#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""knowledge: the two deterministic helpers of the knowledge loop.

A knowledge base is reached as a wiki: a directory of Markdown pages that
assistants read as files, or through the two read-only tools
`openwiki_search` and `openwiki_read` (wiki_server.py, beside this file,
serves them from the search below). This tool adds no store and runs no
language model: the assistants do the reading and the drafting, and a
person signs.

  about          before work: list the pages that bear on a question, each
                 with its status and who signed it, so the work starts from
                 what is known, pitfalls included. With --drafts it also
                 lists the pages waiting in a queue, marked as drafts. A
                 page is listed when it shares two or more words with the
                 question and scores near the best match (a word most of
                 the wiki uses counts for little), when a listed page links
                 to it, or when it is filed against a listed page. A page
                 with tags is matched on its tags, name, title and
                 description; a plain page on its name, title and text.
  check-drafts   after work: apply the rules of a queue to drafted pages. A
                 draft is refused when it is not at status draft, carries
                 any signature, has no sources, does not say what it was
                 drafted from, is a finding, or bears on the same subject as
                 a page already in the wiki without saying how it relates to
                 it, or names as a source a path where no file is. With
                 --checker it also runs the organization's own checker for
                 its knowledge format (check_okf_v02.py) on the queue and
                 refuses what that refuses. A checker is a program, so it is
                 run only when the checksum of the file named is pinned in
                 factory/checkers.yaml; any other file is refused and not
                 run, and the bytes that were checked are the bytes that
                 run. Writes the queue's index for the steward.
  import         copy the pages of another knowledge base into a wiki
                 directory, byte for byte, and write beside them where each
                 came from, its checksum, its status and who signed it. A
                 page in the wiki that a person signed is never written
                 over by other words: such an import is refused whole.
  selftest       the tool tests itself (with --checker, the parts that need
                 the organization's checker too)

A wiki page is working memory, and may be a draft. What counts as signed
is decided by the page's own signature lines, which only a person adds:
either a `verified` event by a person in the page's front matter (the
Open Knowledge Format), or a line in the page of the form
`Signed-by: human:<id>, <date>`. Nothing in this package writes either,
and a draft that arrives with one is refused. A page's status is its
front matter `status`, or a line `Status: <word>`, or nothing.

Which part of this is whose. The wiki's form is OpenWiki's, which is
the Open Knowledge Format v0.2, a form other knowledge bases share: a directory (`openwiki/` in a repository) of Markdown pages, each
with front matter carrying a non-empty `type` and, where present,
`generated`, `sources`, `verified`, `status` and `stale_after`; `index.md`
and `log.md` reserved; `quickstart.md` to start from; `INSTRUCTIONS.md`
the owner's brief; and files whose names begin with a dot, which belong to
the tool that manages the wiki and are neither read nor written here.
This follows the OpenWiki repository's README as it was read on 2026-11-25
and relayed to the assistant that built this; it was not run against the
OpenWiki tool. This tool reads that form and is forgiving beyond it: a
page with no front matter is still read, as working memory. What is this
project's own, laid on top: the matching rules, the rule that only a page
signed by a person is established, the queue of drafts outside the wiki
(assistants never write into the wiki), the `Signed-by` line for a page
without front matter, and the import.

What the overlap check is, and is not. It finds a draft that shares a name,
a title, or several specific tags with a page in the wiki. It cannot read
meaning, so it cannot find a contradiction: it makes the draft say how it
relates to each page it overlaps (extends, narrows, corrects or contradicts
it, or stands beside it: the same subject, another point, no conflict), and
a draft that says `contradicts` is listed first for the steward. A draft
that would only repeat a page (`duplicates`) is refused: the note is linked
to the page instead.

Usage: knowledge.py about --question "..." --wiki DIR [--drafts DIR]
       knowledge.py check-drafts --queue DIR --wiki DIR [--checker FILE]
       knowledge.py import --from DIR --to DIR
       knowledge.py selftest [--checker FILE]
"""
import sys

sys.dont_write_bytecode = True
if __name__ == "__main__" and not sys.flags.safe_path and sys.path:
    _own = __file__.replace("\\", "/").rpartition("/")[0]
    del sys.path[0]
    sys.path[:] = [p for p in sys.path if p != _own]

import argparse  # noqa: E402
import datetime as dt  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402

HERE = Path(__file__).resolve().parent
CHECKERS = HERE.parent / "factory" / "checkers.yaml"  # the checkers check-drafts will run, each pinned by checksum
ADDRESS = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")  # a source that is an address (https:, doi:) and not a path
NOT_CONCEPTS = ("index.md", "log.md", "DIGEST.md", "README.md", "INSTRUCTIONS.md")  # reserved documents, not pages
HEADING = re.compile(r"^#\s+(.+?)\s*$", re.M)
SIGNED_LINE = re.compile(r"^Signed-by:\s*(human:[A-Za-z0-9_.@/-]+)(?:[,\s]+(\S+))?", re.M)
STATUS_LINE = re.compile(r"^Status:\s*([A-Za-z-]+)", re.M)
WORD = re.compile(r"[a-z0-9]+")
STOP = set("""a about above after again all also an and any are as at be because been before being below between both but by can could
did do does doing down during each few for from further had has have having he her here hers him his how i if in into is it its
just me more most my no nor not now of off on once only or other our out over own same she should so some such than that the
their them then there these they this those through to too under until up very was we well were what when where which while who
whom why will with would you your much many good bad""".split())
RELATIONS = ("extends", "narrows", "corrects", "contradicts", "beside", "duplicates")
MD_PATH = re.compile(r"[\w./-]+\.md")
GENERIC_SHARE = 0.25   # a tag carried by more than this share of a bundle says nothing about a subject
KEEP_SHARE = 0.3       # a page is listed when it scores at least this share of the best match
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


def signed_by(fm: dict, body: str = "") -> tuple:
    """(signed?, the people who signed). Signed means the page's own signature lines name a person: a
    `verified` event by a person in its front matter, or a `Signed-by: human:<id>` line in the page."""
    people = [str(e["by"]) for e in events_of(fm or {}) if str(e.get("by", "")).startswith("human:")]
    people += [m.group(1) for m in SIGNED_LINE.finditer(body or "")]
    return bool(people), people


def status_of(fm: dict, body: str = ""):
    if (fm or {}).get("status"):
        return fm["status"]
    m = STATUS_LINE.search(body or "")
    return m.group(1) if m else None


def title_of(p: Path, fm: dict, body: str) -> str:
    if (fm or {}).get("title"):
        return str(fm["title"])
    m = HEADING.search(body or "")
    return m.group(1) if m else p.stem.replace("-", " ")


def words(text) -> set:
    return {w for w in WORD.findall(str(text or "").casefold()) if len(w) > 2 and w not in STOP}


def concepts(root: Path) -> list:
    """Every page under a wiki or a queue: (path, front matter or an empty mapping, body). A page needs no front matter."""
    out = []
    for p in sorted(Path(root).rglob("*.md")):
        if p.name in NOT_CONCEPTS or any(part.startswith(".") for part in p.relative_to(root).parts):
            continue
        fm, body = front_matter(p)
        out.append((p, fm or {}, body))
    return out


def shown(root: Path, p: Path) -> str:
    """A concept's path as people cite it: the repository, the bundle folder, the path below it."""
    root = Path(root).resolve()
    return (Path(root.parent.name) / root.name / p.resolve().relative_to(root)).as_posix()


def tags_of(fm: dict) -> set:
    t = (fm or {}).get("tags")
    return {str(x).casefold() for x in t} if isinstance(t, list) else set()


def subject_of(p: Path, fm: dict, body: str) -> set:
    """What a page is about, for the overlap check: its tags, or for a plain page the words of its title."""
    return tags_of(fm) or words(title_of(p, fm, body))


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
        fields = {p.resolve(): (("tags", tags_of(fm), 3), ("name", words(p.stem.replace("-", " ")), 2), ("title", words(title_of(p, fm, body)), 2),
                                ("description", words(fm.get("description")), 1),
                                ("text", set() if tags_of(fm) else words(body), 1)) for p, fm, body in entries}
        seen_in = {w: sum(1 for f in fields.values() if any(w in got for _, got, _ in f)) for w in asked}
        rare = {w: math.log((len(entries) + 1) / (n + 1)) + 0.1 for w, n in seen_in.items()}  # a word half the bundle uses says little
        hits = {}
        for q, f in fields.items():
            why = [(label, sorted(got & asked), weight * sum(rare[w] for w in got & asked)) for label, got, weight in f if got & asked]
            distinct = set().union(*[set(got) for _, got, _ in why]) if why else set()
            if len(distinct) >= min(2, len(asked)):  # one shared word is a coincidence; two is a subject
                hits[q] = (round(sum(w for _, _, w in why), 2), "; ".join(f"{label}: {', '.join(got)}" for label, got, _ in why))
        best = max((v[0] for v in hits.values()), default=0)
        hits = {q: v for q, v in hits.items() if v[0] >= KEEP_SHARE * best}
        top = dict(sorted(hits.items(), key=lambda kv: (-kv[1][0], str(kv[0])))[:limit])
        linked = {}
        for q in top:
            p, fm, body = by_path[q]
            for target in links_of(p, fm, body, root):
                if target in by_path and target not in top:
                    linked.setdefault(target, (0, f"linked from {p.name}"))
        for p, fm, body in entries:  # a pitfall filed against a dataset in play bears on the question whatever its words
            ref = str(fm.get("dataset") or "")
            target = (p.parent / ref).resolve() if ref else None
            if target in top and p.resolve() not in top:
                linked.setdefault(p.resolve(), (0, f"its dataset is {target.name}"))
        for q, (score, why) in {**top, **linked}.items():
            p, fm, body = by_path[q]
            signed, people = signed_by(fm, body)
            at = next((str(e.get("at")) for e in events_of(fm) if str(e.get("by", "")).startswith("human:")), None)
            found.append({"path": shown(root, p), "file": str(p.resolve()), "sha256": sha_file(p), "type": fm.get("type") or "page",
                          "title": title_of(p, fm, body), "status": status_of(fm, body), "signed": signed, "signed_by": people, "signed_at": at,
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
    return f"NOT SIGNED: working memory (status {c['status'] or 'not stated'}; written by {c['generated_by'] or 'not stated'})"


def render(found: list) -> str:
    if not found:
        return "nothing in the knowledge bears on this question by tags, name, title, description or text. That is a result: say so, and raise a note if something should be there."
    out = [f"{len(found)} page(s) bear on the question. Read each before looking at data.", ""]
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
    p, fm, body = draft
    mine, title = subject_of(p, fm, body) - generic, " ".join(sorted(words(fm.get("title"))))
    out = []
    for q, other, other_body in bundle_entries:
        theirs = subject_of(q, other, other_body) - generic
        shared = mine & theirs
        why = None
        if q.stem == p.stem:
            why = "the same file name"
        elif title and title == " ".join(sorted(words(title_of(q, other, other_body)))):
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
    if any(re.search(r"verif|sign", str(k), re.I) for k in fm) or re.search(r"^Signed-by:", body, re.I | re.M):
        problems.append(f"{name}: it carries a signature (a `verified` event or a `Signed-by` line). No assistant signs: only a person adds one, after the merge")
    gen = fm.get("generated")
    if not isinstance(gen, dict) or not str(gen.get("by") or "").strip() or not gen.get("at"):
        problems.append(f"{name}: `generated` says who drafted it and when ({{by: ..., at: ...}})")
    elif str(gen["by"]).startswith("human:"):
        problems.append(f"{name}: `generated.by` names a person; a draft from this loop is generated by the assistant that wrote it")
    elif str(gen["by"]).startswith("agent:"):
        problems.append(f"{name}: `generated.by` is `{gen['by']}`, the name you act under in the logs. The knowledge format wants the "
                        "platform and the model there, as `<platform>/<model>` (for example claude-code/<model>), and the organization's "
                        f"checker refuses anything else. Write that in `generated.by`, and put your own name in `drafted_from.by: {gen['by']}`: "
                        "it is the same name `resolve --by` takes, so the page and the log name one actor")
    else:
        at = gen.get("at")
        try:
            when = at if isinstance(at, dt.datetime) else dt.datetime.fromisoformat(str(at).replace("Z", "+00:00"))
            when = when if when.tzinfo else when.replace(tzinfo=dt.timezone.utc)
            if when > dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=10):
                problems.append(f"{name}: `generated.at` ({at}) is later than now. It is read as a clock reading: write the time the "
                                "page was drafted, from the clock, not a round time ahead of it")
        except (ValueError, TypeError):
            problems.append(f"{name}: `generated.at` is a time (2026-01-01T00:00:00Z)")
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
    if isinstance(src, dict) and "by" in src and not re.fullmatch(r"agent:\S+", str(src["by"])):
        problems.append(f"{name}: `drafted_from.by` is `{src['by']}`; it is the drafting assistant's own name, agent:<role>-<suffix>, "
                        "the one it acts under in the logs. A person does not draft into this queue")
    # footnotes: what the body cites and what the header lists as sources are the same things
    ids = {str(s.get("id")) for s in sources if isinstance(s, dict) and s.get("id")} if isinstance(sources, list) else set()
    cited = set(re.findall(r"\[\^([^\]]+)\](?!:)", body))
    for missing in sorted(cited - ids):
        problems.append(f"{name}: the body cites [^{missing}], which is not the `id` of any source in the header")
    for unused in sorted(ids - cited):
        problems.append(f"{name}: the source `{unused}` is cited nowhere in the body; every source is there because a statement rests on it")
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
            signed, people = signed_by(other, next((b_ for q_, _, b_ in sum(bundle_entries.values(), []) if q_ == q), ""))
            problems.append(f"{name}: it bears on the same subject as {shown(next(b for b in bundles if q.resolve().is_relative_to(b.resolve())), q)} "
                            f"({'signed by ' + ', '.join(people) if signed else 'not signed'}; {why}) and does "
                            "not say how it relates to it. Add a `relates_to` entry: extends, narrows, corrects, contradicts or beside")
    return problems, relations, over


def pinned_checkers(pins: Path = CHECKERS) -> dict:
    """The checksums of the checkers this factory will run, each with the name it is listed under."""
    try:
        listed = (yaml.safe_load(pins.read_text(encoding="utf-8")) or {}).get("checkers") or []
    except (OSError, yaml.YAMLError, AttributeError):
        return {}
    return {str(c["sha256"]).lower(): str(c.get("name") or "") for c in listed if isinstance(c, dict) and re.fullmatch(r"[0-9a-fA-F]{64}", str(c.get("sha256") or ""))}


def run_checker(checker: Path, queue: Path, pins: Path = CHECKERS) -> tuple:
    """(exit code, what it printed, what it wrote to standard error, its checksum). The file is read once; the bytes
    that were read are the bytes whose checksum is looked up and the bytes that run, from a private copy, so the file
    cannot be exchanged between the look-up and the run. A file whose checksum is not pinned is not run."""
    try:
        code_bytes = Path(checker).read_bytes()
    except OSError:
        raise Refused(f"the organization's checker is not at {checker} (name the file of the checker your knowledge format has; factory/checkers.yaml lists the ones this factory will run)")
    sha = hashlib.sha256(code_bytes).hexdigest()
    pinned = pinned_checkers(pins)
    if sha not in pinned:
        raise Refused(f"`{checker}` is not a checker this factory runs: its checksum ({sha[:12]}...) is not pinned in "
                      f"factory/checkers.yaml, so it is not run. check-drafts runs a checker only when its bytes are listed there "
                      f"({', '.join(sorted(set(pinned.values()))) or 'none is listed'}); a new checker is pinned by a reviewed change "
                      "to that file, never named on the command line by whoever wants the queue to pass")
    private = Path(tempfile.mkdtemp(prefix="sf-checker-"))
    try:
        copy = private / (pinned[sha] or "checker.py")
        copy.write_bytes(code_bytes)
        run = subprocess.run([sys.executable, "-I", str(copy), str(queue)], capture_output=True, text=True, stdin=subprocess.DEVNULL,
                             cwd=private)
    finally:
        shutil.rmtree(private, ignore_errors=True)
    return run.returncode, run.stdout, run.stderr, sha


def source_problems(name: str, p: Path, queue: Path, bundles: list, sources) -> list:
    """A source that is a path names a file that exists: read from the folders above the queue (a path from the top
    of the repository), from the draft's own folder, or from the folder the page would have in the wiki."""
    out = []
    rel_dir = p.parent.relative_to(queue)
    for s_ in sources if isinstance(sources, list) else []:
        res = str(s_.get("resource") or "").strip() if isinstance(s_, dict) else ""
        if not res or ADDRESS.match(res):
            continue
        path = res.split("#", 1)[0]
        bases = [p.parent, *list(queue.parents)[:8], queue] + [b / rel_dir for b in bundles]
        if Path(path).is_absolute() or not any((b / path).exists() for b in bases):
            out.append(f"{name}: the source `{res}` is a path and no file is there (read from the folders above the queue, the "
                       "draft's own folder and its place in the wiki). A source exists: give the path of the receipt, or an address")
    return out


def check_drafts(queue: Path, bundles: list, checker: Path | None = None, pins: Path = CHECKERS) -> tuple:
    """(problems, the queue as a mapping). Nothing is written when there is a problem."""
    queue, bundles = Path(queue).resolve(), [Path(b).resolve() for b in bundles]
    if not queue.is_dir():
        raise Refused(f"the queue {queue} is not a directory")
    problems, report, checker_sha = [], [], None
    if checker is not None:
        code, printed, complained, checker_sha = run_checker(Path(checker), queue, pins)
        report = printed.strip().splitlines()
        if code != 0:
            problems += ["the organization's checker: " + ln for ln in report if re.match(r"^[EF]\d", ln)] or [
                "the organization's checker failed: " + (complained.strip() or printed.strip())[-300:]]
    for p in sorted(queue.rglob("*.md")):
        if p.name not in NOT_CONCEPTS and front_matter(p)[0] is None:
            problems.append(f"{p.relative_to(queue).as_posix()}: no front matter that parses; a drafted page carries the queue's header")
    drafts = [d for d in concepts(queue) if d[1]]
    bundle_entries = {b: concepts(b) for b in bundles}
    generic = {}
    for b, entries in bundle_entries.items():
        counts = {}
        for q_, fm, b_ in entries:
            for t in subject_of(q_, fm, b_):
                counts[t] = counts.get(t, 0) + 1
        generic[b] = {t for t, n in counts.items() if n > max(2, GENERIC_SHARE * len(entries))}  # in a small wiki nothing is generic
    listing, seen = [], {}
    for d in drafts:
        probs, relations, _ = draft_problems(d, queue, bundles, bundle_entries, generic)
        problems += probs
        p, fm, _ = d
        problems += source_problems(p.relative_to(queue).as_posix(), p, queue, bundles, fm.get("sources"))
        key = " ".join(sorted(words(fm.get("title"))))
        if key in seen or p.stem in {q.stem for q in seen.values()}:
            problems.append(f"{p.relative_to(queue).as_posix()}: the queue already holds a draft with this title or name")
        seen[key] = p
        listing.append({"path": p.relative_to(queue).as_posix(), "sha256": sha_file(p), "type": fm.get("type"), "title": fm.get("title"),
                        "status": fm.get("status"), "signed": False, "generated_by": (fm.get("generated") or {}).get("by") if isinstance(fm.get("generated"), dict) else None,
                        "drafted_from": fm.get("drafted_from"),
                        **({"drafted_by": fm["drafted_from"]["by"]} if isinstance(fm.get("drafted_from"), dict) and fm["drafted_from"].get("by") else {}),
                        "relates_to": [{"concept": r["concept"], "relation": r["relation"], "why": r["why"]} for r in relations.values()],
                        "contradicts_a_concept": any(r["relation"] == "contradicts" for r in relations.values())})
    listing.sort(key=lambda d: (not d["contradicts_a_concept"], d["path"]))
    return problems, {"for": "the steward", "drafts": listing, "signed": 0, "checker": ({"file": Path(checker).name, "sha256": checker_sha, "last_line": report[-1] if report else ""}
                                                                            if checker is not None else None),
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
    problems, q = check_drafts(Path(a.queue), [Path(b) for b in a.bundle], Path(a.checker) if a.checker else None)
    for p in problems:
        print("check-drafts:", p)
    if problems:
        raise Refused(f"{len(problems)} problem(s): the queue is not ready for the steward, and its index is not written")
    write_queue(Path(a.queue).resolve(), q)
    print(f"check-drafts: PASS. {len(q['drafts'])} draft(s) in the queue for the steward, none signed"
          + (f", {sum(d['contradicts_a_concept'] for d in q['drafts'])} of them say they contradict a concept in the bundle"
             if any(d["contradicts_a_concept"] for d in q["drafts"]) else "")
          + (f". The organization's checker: {q['checker']['last_line']}" if q["checker"] else ". The organization's checker was not run (no --checker)"))
    return 0


def import_pages(source: Path, wiki: Path) -> list:
    """Copy every page of another knowledge base into a wiki directory, unchanged, and record where each came
    from. The pages keep their own signature lines, so what is signed there is signed here and nothing else is."""
    source, wiki = Path(source).resolve(), Path(wiki).resolve()
    if not source.is_dir():
        raise Refused(f"{source} is not a directory")
    out, in_the_way = [], []
    for p, fm, body in concepts(source):  # look before anything is written: a signed page is never replaced by an import
        dest = wiki / p.relative_to(source)
        if dest.is_symlink() or (dest.exists() and not dest.is_file()):
            in_the_way.append(f"{dest.relative_to(wiki).as_posix()} is a link or is not a file")
        elif dest.is_file() and dest.read_bytes() != p.read_bytes():
            there_fm, there_body = front_matter(dest)
            signed, people = signed_by(there_fm or {}, there_body)
            if signed:
                in_the_way.append(f"{dest.relative_to(wiki).as_posix()} is signed by {', '.join(people)} and the page that would replace it differs")
    if in_the_way:
        raise Refused("nothing is imported: " + "; ".join(in_the_way[:6]) + (f"; and {len(in_the_way) - 6} more" if len(in_the_way) > 6 else "")
                      + ". An import does not write over a page a person signed; a signed page is changed by its steward, by pull request")
    for p, fm, body in concepts(source):
        rel = p.relative_to(source)
        dest = wiki / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
        signed, people = signed_by(fm, body)
        out.append({"page": rel.as_posix(), "from": shown(source, p), "sha256": sha_file(p), "status": status_of(fm, body),
                    "signed": signed, "signed_by": people})
    (wiki / "imported.json").write_text(json.dumps({"from": f"{source.parent.name}/{source.name}", "pages": out,
                                                    "says": "copied unchanged; each page's own signature lines decide what is signed"}, indent=1) + "\n")
    return out


def cmd_import(a) -> int:
    pages = import_pages(Path(a.source), Path(a.to))
    print(f"imported {len(pages)} page(s), {sum(p['signed'] for p in pages)} of them signed by a person where they came from; "
          f"imported.json says where each came from")
    return 0


# ---- the self-test --------------------------------------------------------
def selftest(checker: Path | None) -> int:
    results = []

    def ok(name: str, cond) -> None:
        results.append((name, bool(cond)))

    if checker is not None and not Path(checker).is_file():
        print(f"selftest: FAIL (the organization's checker is not at {checker})")
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
        concept("gotchas/machine.md", "River gauge stage is provisional", "gauge, provisional, stage, hydrology", "verified: { by: process:ci, at: 2026-01-02T00:00:00Z }\n")

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
        ok("a complete draft passes" + (", and the organization's checker ran on it" if checker else ""), problems() == [])
        q = check_drafts(queue, [bundle], checker)[1]
        ok("the queue lists the draft as not signed", q["drafts"][0]["signed"] is False and q["signed"] == 0 and (checker is None or "conformant" in q["checker"]["last_line"]))
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
           any("no sources" in p for p in problems()) and (checker is None or any("organization's checker: E7" in p for p in problems())))
        draft(drafted_from=None)
        ok("a draft that does not say what it was drafted from is refused", any("drafted_from" in p for p in problems()))
        draft(seen_while=None, body="A claim.[^look]\n\n[^look]: the look")
        ok("a draft from an exploration that does not say it was exploring is refused", any("does not say so" in p for p in problems()))
        draft(type="finding")
        ok("a draft that is a finding is refused", any("it is a finding" in p for p in problems()))
        draft(generated={"by": "human:someone", "at": "2026-11-25T00:00:00Z"})
        ok("a draft that says a person generated it is refused", any("names a person" in p for p in problems()))
        draft(generated={"by": "agent:curating-0101", "at": "2026-11-25T00:00:00Z"})
        ok("a draft that gives the assistant's own name as `generated.by` is told what to write there and where its name goes",
           any("<platform>/<model>" in p and "drafted_from.by: agent:curating-0101" in p for p in problems()))
        draft(drafted_from={"exploration": "EXPLORATION-0001", "notes": ["NOTE-001"], "by": "agent:curating-0101"})
        ok("a draft that names the drafting assistant in `drafted_from.by` passes, and the queue lists who drafted it",
           problems() == [] and check_drafts(queue, [bundle], checker)[1]["drafts"][0]["drafted_by"] == "agent:curating-0101")
        draft(drafted_from={"exploration": "EXPLORATION-0001", "notes": ["NOTE-001"], "by": "human:someone"})
        ok("a draft that names a person as the drafter is refused", any("A person does not draft" in p for p in problems()))
        draft(generated={"by": "claude-code/test", "at": "2999-01-01T00:00:00Z"})
        ok("a draft stamped later than the clock is refused: the stamp is read as a clock reading", any("later than now" in p for p in problems()))
        draft(body="Seen while exploring.[^look] A second thing.[^other]\n\n[^look]: the look\n[^other]: nowhere")
        ok("a draft that cites a footnote which is no source in its header is refused", any("cites [^other]" in p for p in problems()))
        draft(body="Seen while exploring, with no citation.")
        ok("a draft with a source that no statement cites is refused", any("cited nowhere in the body" in p for p in problems()))
        draft(status="verified")
        ok("a status outside the format is refused", any("status is `verified`" in p for p in problems()))
        draft(spheres=None)
        if checker:
            ok("a draft the organization's checker fails is refused with the checker's own line", any("organization's checker: E10" in p for p in problems()))
        else:
            ok("without the organization's checker the queue's own rules still run, and say the checker was not run",
               problems() == [] and check_drafts(queue, [bundle], None)[1]["checker"] is None)
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
           (draft(status="stable") and _refuses(cmd_check_drafts, argparse.Namespace(queue=str(queue), bundle=[str(bundle)], checker=str(checker) if checker else None))
            and not (queue / "index.md").exists()))
        draft()
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_check_drafts(argparse.Namespace(queue=str(queue), bundle=[str(bundle)], checker=str(checker) if checker else None))
        ok("check-drafts writes the queue's index for the steward, and the queue still passes with it there",
           "not signed" in (queue / "index.md").read_text() and problems() == [])
        both = about("Where do passes flagged degraded sit, by stage?", [bundle], [queue])
        ok("about lists a queued draft as a draft that is not signed",
           any(c["in_queue"] and "DRAFT IN THE QUEUE, NOT SIGNED" in trust(c) for c in both))
        ok("check-drafts refuses when a checker is named and is not there", _refuses(check_drafts, queue, [bundle], tmp / "no-checker.py"))
        draft(body="Seen while exploring.[^look]\n\nSigned-by: human:someone, 2026-11-25\n\n[^look]: the look")
        ok("a draft with a `Signed-by` line is refused", any("carries a signature" in p for p in problems()))
        draft(Verified_by="human:someone")
        ok("a draft with a signature under another spelling of the key is refused", any("carries a signature" in p for p in problems()))
        draft()
        # a wiki of plain Markdown pages: no front matter, no layout
        wiki = tmp / "plainwiki"
        wiki.mkdir()
        (wiki / "tide-gauge-drift.md").write_text("# The harbour tide gauge drifts in summer\n\nThe harbour gauge reads high in warm months. Compare changes, not levels.\n\nSee [the sensor page](sensor.md).\n")
        (wiki / "sensor.md").write_text("# The pressure sensor\n\nStatus: reviewed\nSigned-by: human:toy-steward, 2026-01-02\n\nA pressure sensor on the quay.\n")
        (wiki / "cooking.md").write_text("# Soup\n\nOnions, then stock.\n")
        plain = about("Does the harbour tide gauge drift in warm months?", [wiki])
        names = {c["path"].rsplit("/", 1)[1]: c for c in plain}
        ok("about reads a wiki of plain Markdown pages with no front matter", "tide-gauge-drift.md" in names and "cooking.md" not in names)
        ok("a plain page takes its title from its first heading and is working memory, not signed",
           names["tide-gauge-drift.md"]["title"] == "The harbour tide gauge drifts in summer" and not names["tide-gauge-drift.md"]["signed"]
           and "working memory" in trust(names["tide-gauge-drift.md"]))
        ok("a plain page reached by a link is listed, and its own `Signed-by` line by a person makes it signed",
           "sensor.md" in names and names["sensor.md"]["signed_by"] == ["human:toy-steward"] and names["sensor.md"]["status"] == "reviewed")
        draft(title="The harbour tide gauge drifts in summer", tags=["tide", "harbour"])
        ok("a draft with the title of a plain wiki page is refused until it says how it relates",
           any("same subject as" in p and "tide-gauge-drift.md" in p for p in check_drafts(queue, [wiki], None)[0]))
        draft()
        got = import_pages(bundle, tmp / "imported")
        by_page = {g["page"]: g for g in got}
        ok("import copies pages unchanged and keeps where each came from, its status and who signed it",
           (tmp / "imported/gotchas/datum.md").read_bytes() == (bundle / "gotchas/datum.md").read_bytes()
           and by_page["recipes/river-gauge-confrontation.md"]["signed_by"] == ["human:toy-steward"] and not by_page["gotchas/datum.md"]["signed"]
           and json.loads((tmp / "imported/imported.json").read_text())["pages"][0]["from"].startswith("hydro/knowledge/"))
        ok("an imported wiki answers the same question with the same pages",
           {c["path"].rsplit("/", 1)[1] for c in about("How well does SWOT river height follow the gauge?", [tmp / "imported"])}
           == {c["path"].rsplit("/", 1)[1] for c in found})
        # ---- what an independent attack found (docs/reviews/ASSISTANTS-AND-EXPLORING.md, round 4) ----------------
        draft()
        ran_here = tmp / "CHECKER-RAN.txt"
        evil = queue / "gotchas" / "evil_checker.py"
        evil.write_text(f"from pathlib import Path\nPath({str(ran_here)!r}).write_text('ran')\nprint('F001 pretending to be a checker line')\n")
        ok("a file named as the checker that is not pinned in the factory's files is refused, and it is not run",
           _refuses(check_drafts, queue, [bundle], evil) and not ran_here.exists())
        evil.unlink()
        pins = tmp / "checkers.yaml"
        good = tmp / "good_checker.py"
        good.write_text("import sys\nprint('conformant, says the test checker')\nsys.exit(0)\n")
        pins.write_text(yaml.safe_dump({"checkers": [{"name": "good_checker.py", "sha256": sha_file(good)}]}))
        probs, q = check_drafts(queue, [bundle], good, pins)
        ok("a checker whose checksum is pinned runs, and the queue records which bytes ran",
           probs == [] and q["checker"]["sha256"] == sha_file(good) and q["checker"]["last_line"] == "conformant, says the test checker")
        good.write_text(good.read_text() + f"from pathlib import Path\nPath({str(ran_here)!r}).write_text('ran')\n")
        ok("the pinned file with one line added is another file: refused, and not run",
           _refuses(check_drafts, queue, [bundle], good, pins) and not ran_here.exists())
        other = tmp / "elsewhere" / "check_okf_v02.py"
        other.parent.mkdir()
        other.write_text(f"from pathlib import Path\nPath({str(ran_here)!r}).write_text('ran')\n")
        ok("a file that only carries the pinned checker's name is refused, and not run",
           _refuses(check_drafts, queue, [bundle], other) and _refuses(check_drafts, queue, [bundle], other, pins) and not ran_here.exists())
        shipped = pinned_checkers()
        ok("the factory's own list of pinned checkers parses and names the organization's checker",
           "check_okf_v02.py" in shipped.values() and (checker is None or sha_file(Path(checker)) in shipped))
        draft(sources=[{"id": "look", "resource": "explorations/NOPE/does-not-exist.json", "title": "nowhere"}])
        ok("a draft whose source is a path with no file there is refused", any("no file is there" in p for p in check_drafts(queue, [bundle], None)[0]))
        (tmp / "explorations" / "E1" / "receipts").mkdir(parents=True)
        (tmp / "explorations" / "E1" / "receipts" / "LOOK-001.json").write_text("{}")
        draft(sources=[{"id": "look", "resource": "explorations/E1/receipts/LOOK-001.json", "title": "the look"}])
        ok("a draft whose source is a path from a folder above the queue passes when the file is there", check_drafts(queue, [bundle], None)[0] == [])
        draft(sources=[{"id": "look", "resource": "../datasets/reach-product.md", "title": "a page of the wiki"}])
        ok("a source may be a page of the wiki, by its path from the place the draft would have there", check_drafts(queue, [bundle], None)[0] == [])
        draft(sources=[{"id": "look", "resource": str(tmp / "explorations/E1/receipts/LOOK-001.json"), "title": "an absolute path"}])
        ok("a source given as a path from the top of the disk is refused: it is true on one machine only",
           any("no file is there" in p for p in check_drafts(queue, [bundle], None)[0]))
        draft()
        # import never writes over a page a person signed
        wiki2 = tmp / "wiki2"
        import_pages(bundle, wiki2)
        signed_page = wiki2 / "recipes" / "river-gauge-confrontation.md"
        was = signed_page.read_bytes()
        incoming = tmp / "incoming"
        (incoming / "recipes").mkdir(parents=True)
        (incoming / "gotchas").mkdir()
        (incoming / "recipes" / "river-gauge-confrontation.md").write_text("---\ntype: recipe\ntitle: replaced\nstatus: draft\n---\n\n# Replaced\n\nUnsigned words.\n")
        (incoming / "gotchas" / "datum.md").write_text("---\ntype: dataset-gotcha\ntitle: newer\nstatus: draft\n---\n\n# Newer\n")
        unsigned_was = (wiki2 / "gotchas" / "datum.md").read_bytes()
        ok("an import that would write over a signed page with other words is refused, and writes nothing at all",
           _refuses(import_pages, incoming, wiki2) and signed_page.read_bytes() == was and (wiki2 / "gotchas" / "datum.md").read_bytes() == unsigned_was)
        (incoming / "recipes" / "river-gauge-confrontation.md").write_text(
            "---\ntype: recipe\ntitle: replaced\nverified: { by: human:someone-else, at: 2026-01-02T00:00:00Z }\nstatus: stable\n---\n\n# Replaced\n")
        ok("a page that says it is signed does not replace a signed page either", _refuses(import_pages, incoming, wiki2) and signed_page.read_bytes() == was)
        (incoming / "recipes" / "river-gauge-confrontation.md").unlink()
        ok("a page nobody signed may be replaced by an import, and a signed page is copied again when it is the same bytes",
           len(import_pages(incoming, wiki2)) == 1 and b"Newer" in (wiki2 / "gotchas" / "datum.md").read_bytes() and len(import_pages(bundle, tmp / "imported")) == len(got))
        outside = tmp / "outside-the-wiki.md"
        outside.write_text("kept")
        (wiki2 / "gotchas" / "datum.md").unlink()
        (wiki2 / "gotchas" / "datum.md").symlink_to(outside)
        ok("an import does not write through a link in the wiki", _refuses(import_pages, incoming, wiki2) and outside.read_text() == "kept")

        def parses(words: list) -> bool:
            try:
                with contextlib.redirect_stderr(io.StringIO()):
                    build_parser().parse_args(words)
            except SystemExit:
                return False
            return True

        ok("an option is taken only when it is spelled out: `--check` is not `--checker`",
           parses(["check-drafts", "--queue", "q", "--wiki", "w", "--checker", "c"]) and not parses(["check-drafts", "--queue", "q", "--wiki", "w", "--check", "c"])
           and not parses(["about", "--quest", "what?", "--wiki", "w"]))
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


def build_parser() -> argparse.ArgumentParser:
    """Every command and every option, spelled out; no option is taken by its first letters."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("about", allow_abbrev=False)
    p.add_argument("--question", required=True)
    p.add_argument("--wiki", "--bundle", dest="bundle", action="append", required=True, type=Path,
                   help="a wiki: a directory of Markdown pages (any directory of pages in the Open Knowledge Format is one); repeatable")
    p.add_argument("--drafts", action="append", default=None, type=Path, help="a queue of drafted pages; repeatable")
    p.add_argument("--tag", action="append", default=None, help="a tag to search by as well; repeatable")
    p.add_argument("--limit", type=int, default=12)
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_about)
    p = sub.add_parser("check-drafts", allow_abbrev=False)
    p.add_argument("--queue", required=True)
    p.add_argument("--wiki", "--bundle", dest="bundle", action="append", required=True, help="the wiki the drafts would join; repeatable")
    p.add_argument("--checker", default=None, help="the organization's checker for its knowledge format, a program of yours or of whoever keeps the format; run only when its checksum is pinned in factory/checkers.yaml")
    p.set_defaults(fn=cmd_check_drafts)
    p = sub.add_parser("selftest", allow_abbrev=False)
    p.add_argument("--checker", default=None)
    p = sub.add_parser("import", allow_abbrev=False)
    p.add_argument("--from", dest="source", required=True, help="the knowledge base to copy pages from")
    p.add_argument("--to", required=True, help="the wiki directory to copy them into")
    p.set_defaults(fn=cmd_import)
    return ap


def refuse_inside_a_look() -> None:
    """A look runs a script on working data and calls no tool of this package; the study tool, beside this file,
    holds the one reading of whether a process was started from inside a look."""
    spec = importlib.util.spec_from_file_location("sf", HERE / "sf.py")
    sf = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("sf", sf)
    spec.loader.exec_module(sf)
    why = sf.started_from_a_look()
    if why:
        raise Refused(f"this command was started from inside a look ({why}). A look runs a script on working data; it does "
                      "not call the tools of this package")


def main() -> int:
    ap = build_parser()
    a = ap.parse_args()
    try:
        refuse_inside_a_look()
        if a.cmd == "selftest":
            return selftest(Path(a.checker) if a.checker else None)
        return a.fn(a)
    except Refused as r:
        print(f"REFUSED: {r}", file=sys.stderr)
        return 2
    except (KeyError, TypeError, ValueError, AttributeError, OSError) as e:
        print(f"REFUSED: a file could not be read ({type(e).__name__}: {e})", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
