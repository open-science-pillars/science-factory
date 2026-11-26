#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""check_roles: the role files and the procedure say the same thing.

The roles are files in `assistants/`, one per role, in a form no agent
platform owns. The procedure (factory/procedure.yaml) has an `assistants` block
written for people. This check fails when the two disagree, so neither can
drift from the other unnoticed. It runs no language model and it edits
nothing.

What it checks:

  form        every role file has the seven front matter keys (name,
              purpose, may_call, must_never_see, reads, writes, hands_on),
              its name is its file name, and its purpose is one sentence
  same roles  the procedure's `assistants` block and `assistants/` name the
              same roles
  same words  each role file quotes, word for word, what the procedure says
              the role does, may not do and must be, and lists under
              `must_never_see` what the procedure says it never sees
  may_call    every command names a tool in tools/ and a command that tool
              has; every skill is in skills/; every role is a role
  the acts    no role may call the lock, the signature or the voiding of an
  of people   opening: those belong to people
  separations the review role calls nothing that does the work; only the
              review role records a review; the curating role is the only
              one that resolves notes; only the analysis role starts an
              exploration or runs a look
  the stages  each stage the procedure gives to a role has its command in
              that role's may_call
  own places  every role that writes may write its account in record/<role>/ and in no
              other role's place, and the review role's `must_never_see`
              names the analysis role's account as paths, both in a
              folder of its own and as flat files in record/, so a runner
              can refuse it
  reviewer    only the coordinating role names the reviewer of an
              exploration, and it may call nothing that is part of the
              exploring
  same words  where a role file and a skill both say in what order things
              are done (what is read before data is set aside, when an
              exploration is ended, where a review is written, when the
              curating assistant starts), they say it in the same words:
              the paragraph in the role file that begins with the label
              stands, word for word, in each skill named for it

Usage: check_roles.py [--root DIR]      check the repository
       check_roles.py --selftest        every disagreement it claims to catch is caught
"""
import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

KEYS = ("name", "purpose", "may_call", "must_never_see", "reads", "writes", "hands_on")
ACTS_OF_PEOPLE = ("tools/sf.py lock", "tools/sf.py signature", "tools/sf.py void-unread")
SAME_WORDS = {  # a role, the label that begins a paragraph of its file, and the skills that carry the same paragraph
    "analysis": {"**The order.**": ["explore-a-record"], "**When to end.**": ["explore-a-record", "write-up-a-lead"]},
    "review": {"**Where you write.**": ["review-work"]},
    "curating": {"**When you start.**": ["draft-a-knowledge-page"]},
}
DOES_THE_WORK = ("tools/explore.py start", "tools/explore.py look", "tools/explore.py choice", "tools/explore.py lead", "tools/explore.py end",
                 "tools/explore.py correct",
                 "tools/sf.py start", "tools/sf.py test", "tools/sf.py rehearse", "tools/sf.py attach", "tools/sf.py open-held-out")
ONLY = {  # a command and the one role that may call it
    "tools/explore.py review": "review", "tools/sf.py review": "review",
    "tools/explore.py resolve": "curating", "tools/sf.py resolve": "curating",
    "tools/explore.py start": "analysis", "tools/explore.py look": "analysis", "tools/explore.py lead": "analysis",
    "tools/explore.py correct": "analysis", "tools/explore.py end": "analysis",
    "tools/explore.py hand-over": "coordinating", "tools/sf.py open-held-out": "coordinating",
    "tools/explore.py reviewer": "coordinating",  # the reviewer is named by the role that does none of the exploring
}
NEVER_SEEN_BY_REVIEW = ("path:record/analysis/*", "path:record/*analysis*")  # the author's account: in its own folder, and as flat files in record/
STAGE_COMMANDS = {  # the stage of the procedure, the role named in `done_by`, the command that stage needs
    ("ask", "coordinating"): ["tools/sf.py start"],
    ("plan", "analysis"): ["tools/sf.py check-plan"],
    ("test", "analysis"): ["tools/sf.py test", "tools/sf.py rehearse"],
    ("open", "coordinating"): ["tools/sf.py open-held-out"],
    ("review", "analysis"): ["tools/sf.py attach"],
    ("review", "review"): ["tools/sf.py review"],
    ("learn", "curating"): ["tools/sf.py curation-list", "tools/sf.py resolve"],
    ("close", "coordinating"): ["tools/sf.py close"],
}


def squash(text) -> str:
    return " ".join(str(text).split())


def load_role(path: Path) -> tuple:
    """(front matter or None, body)."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return None, text
    try:
        fm = yaml.safe_load(text[4:end])
    except yaml.YAMLError:
        return None, text
    return (fm if isinstance(fm, dict) else None), text[end + 5:]


def roles_in(root: Path) -> dict:
    return {p.stem: load_role(p) for p in sorted((root / "assistants").glob("*.md"))}


def commands_of(tool: Path) -> set:
    """The commands a tool has, read from its source: every name it gives its argument parser."""
    text = tool.read_text(encoding="utf-8")
    return set(re.findall(r"""\badd\(\s*["']([a-z][a-z-]*)["']""", text)) | set(re.findall(r"""add_parser\(\s*["']([a-z][a-z-]*)["']""", text))


def problems(root: Path) -> list:
    p = []
    try:
        procedure = yaml.safe_load((root / "factory" / "procedure.yaml").read_text(encoding="utf-8"))
        block = procedure["assistants"]
        stages = procedure["stages"]
    except (OSError, yaml.YAMLError, KeyError, TypeError):
        return ["factory/procedure.yaml is missing, does not parse, or has no `assistants` block and `stages`"]
    roles = roles_in(root)
    for name in sorted(set(block) - set(roles)):
        p.append(f"the procedure names the {name} assistant and assistants/{name}.md does not exist")
    for name in sorted(set(roles) - set(block)):
        p.append(f"assistants/{name}.md is a role the procedure's `assistants` block does not name")
    tools = {}
    for name, (fm, body) in roles.items():
        where = f"assistants/{name}.md"
        if fm is None:
            p.append(f"{where}: no front matter that parses")
            continue
        missing = [k for k in KEYS if k not in fm]
        if missing:
            p.append(f"{where}: front matter lacks {', '.join(missing)}")
            continue
        if fm["name"] != name:
            p.append(f"{where}: its name is `{fm['name']}`, not its file name")
        purpose = str(fm["purpose"]).strip()
        if not purpose.endswith(".") or purpose.count(". ") > 0 or len(purpose.split()) < 5:
            p.append(f"{where}: `purpose` is one sentence")
        for k in ("may_call", "must_never_see", "reads", "writes", "hands_on"):
            if not isinstance(fm[k], list):
                p.append(f"{where}: `{k}` is a list")
        if any(not isinstance(fm[k], list) for k in ("may_call", "must_never_see", "reads", "writes", "hands_on")):
            continue
        for h in fm["hands_on"]:
            if not isinstance(h, dict) or not h.get("what") or not h.get("to"):
                p.append(f"{where}: each `hands_on` entry says what is handed on and to whom")
        calls = [str(c) for c in fm["may_call"]]
        for c in calls:
            if c.startswith("skill:"):
                if not (root / "skills" / c[6:] / "SKILL.md").is_file():
                    p.append(f"{where}: may_call names the skill `{c[6:]}`, and skills/{c[6:]}/SKILL.md does not exist")
            elif c.startswith("role:"):
                if c[5:] not in roles:
                    p.append(f"{where}: may_call names the role `{c[5:]}`, which is not a role")
            else:
                parts = c.split()
                tool = root / parts[0] if parts else root
                if len(parts) != 2 or not parts[0].startswith("tools/") or not tool.is_file():
                    p.append(f"{where}: may_call entry `{c}` is not `tools/<tool>.py <command>`, `skill:<name>` or `role:<name>`")
                    continue
                if parts[0] not in tools:
                    tools[parts[0]] = commands_of(tool)
                if parts[1] not in tools[parts[0]]:
                    p.append(f"{where}: may_call names `{c}`, and {parts[0]} has no command `{parts[1]}`")
        for act in ACTS_OF_PEOPLE:
            if act in calls:
                p.append(f"{where}: may_call holds `{act}`, which is an act of people; no assistant may call it")
        for cmd, only in ONLY.items():
            if cmd in calls and name != only:
                p.append(f"{where}: may_call holds `{cmd}`, which only the {only} assistant may call")
        if name == "review":
            for cmd in DOES_THE_WORK:
                if cmd in calls:
                    p.append(f"{where}: the review assistant may call `{cmd}`, which does the work it is there to check")
            for pat in NEVER_SEEN_BY_REVIEW:
                if pat not in [str(x) for x in fm["must_never_see"]]:
                    p.append(f"{where}: `must_never_see` does not name the analysis assistant's own account as a path ({pat}), "
                             "so no runner can keep the reviewer away from the author's account of the work")
        if "tools/explore.py reviewer" in calls:
            for cmd in DOES_THE_WORK:
                if cmd.startswith("tools/explore.py") and cmd in calls:
                    p.append(f"{where}: the role that names the reviewer may call `{cmd}`, which is part of the exploring; "
                             "whoever names the reviewer does none of it")
        if name == "coordinating" and "tools/explore.py reviewer" not in calls:
            p.append(f"{where}: may_call does not hold `tools/explore.py reviewer`: a lead is refused until the coordinating "
                     "assistant has named the reviewer, so no exploration could reach one")
        writes = [str(w) for w in fm["writes"]]
        if writes and f"record/{name}/*.md" not in writes:  # a role that writes nothing (the coordinating role) has its tasks kept by the launcher
            p.append(f"{where}: `writes` does not give the role its own place for its account (record/{name}/*.md)")
        for other in sorted(set(roles) - {name}):
            if any(w.startswith(f"record/{other}/") or w in ("record/*", "record/*.md", "record/*/*.md") for w in writes):
                p.append(f"{where}: `writes` lets this role write in the {other} role's place (record/{other}/); each role's account has its own place")
        text_ = squash(body)
        for label, skills in (SAME_WORDS.get(name) or {}).items():
            para = next((squash(q) for q in body.split("\n\n") if q.strip().startswith(label)), None)
            if para is None:
                p.append(f"{where}: it has no paragraph beginning {label}, which the skills {', '.join(skills)} must carry in the same words")
                continue
            for skill in skills:
                f = root / "skills" / skill / "SKILL.md"
                if f.is_file() and para not in squash(f.read_text(encoding="utf-8")):
                    p.append(f"{where} and skills/{skill}/SKILL.md do not say the same thing under {label}: the paragraph in the role "
                             "file must stand word for word in the skill, so that the two cannot give different orders")
        del text_
        if name in block:
            said = block[name] if isinstance(block[name], dict) else {}
            text = squash(body)
            for key in ("does", "may_not", "must", "runs"):
                if key in said and squash(said[key]) not in text:
                    p.append(f"{where}: it does not quote what the procedure says under `{key}` for this role (\"{squash(said[key])}\"); "
                             "the two have drifted apart")
            for item in said.get("never_sees") or []:
                if squash(item) not in [squash(x) for x in fm["must_never_see"]]:
                    p.append(f"{where}: the procedure says this role never sees \"{squash(item)}\", and `must_never_see` does not list it")
                if squash(item) not in text:
                    p.append(f"{where}: it does not quote what the procedure says this role never sees (\"{squash(item)}\")")
            if "may_not" in said and "sign" in str(said["may_not"]) and "tools/sf.py signature" in calls:
                p.append(f"{where}: the procedure says this role may not sign, and may_call holds the signature")
    for st in stages if isinstance(stages, list) else []:
        done_by = str(st.get("done_by") or "")
        for (stage, role), cmds in STAGE_COMMANDS.items():
            if st.get("id") == stage and f"{role} assistant" in done_by and role in roles and roles[role][0]:
                calls = [str(c) for c in roles[role][0].get("may_call") or []]
                for cmd in cmds:
                    if cmd not in calls:
                        p.append(f"the procedure gives the {stage} stage to the {role} assistant, and assistants/{role}.md may not call `{cmd}`")
    for st in stages if isinstance(stages, list) else []:
        for role in re.findall(r"(\w+) assistant", str(st.get("done_by") or "")):
            if role not in roles:
                p.append(f"the procedure gives the {st.get('id')} stage to the {role} assistant, which has no role file")
    return p


def selftest(root: Path) -> int:
    results = []
    tmp = Path(tempfile.mkdtemp(prefix="check-roles-")).resolve()
    try:
        def copy(name: str) -> Path:
            d = tmp / name
            for sub in ("assistants", "skills"):
                shutil.copytree(root / sub, d / sub)
            (d / "tools").mkdir()
            (d / "factory").mkdir()
            for f in (root / "tools").glob("*.py"):
                shutil.copyfile(f, d / f.relative_to(root))
            shutil.copyfile(root / "factory" / "procedure.yaml", d / "factory" / "procedure.yaml")
            return d

        def edit(d: Path, rel: str, old: str, new: str) -> None:
            f = d / rel
            text = f.read_text()
            assert old in text, (rel, old)
            f.write_text(text.replace(old, new, 1))

        def case(name: str, change, expect: str) -> None:
            d = copy(f"case-{len(results)}")
            change(d)
            got = problems(d)
            results.append((name, any(expect in q for q in got)))

        results.append(("the repository's own role files and procedure agree", problems(copy("clean")) == []))
        case("a role the procedure names has no file", lambda d: (d / "assistants/curating.md").unlink(), "curating.md does not exist")
        case("a role file the procedure does not name", lambda d: shutil.copyfile(d / "assistants/review.md", d / "assistants/auditing.md"),
             "a role the procedure's `assistants` block does not name")
        case("the procedure changes what a role does and the role file is not changed",
             lambda d: edit(d, "factory/procedure.yaml", "relays questions, keeps the study moving", "relays questions and decides what counts"),
             "does not quote what the procedure says under `does`")
        case("a role file changes its quotation of the procedure",
             lambda d: edit(d, "assistants/review.md", "and records approve or block", "and approves"), "does not quote what the procedure says under `does`")
        case("a role file drops what the procedure says it may not do",
             lambda d: edit(d, "assistants/curating.md", 'It may not: "merge or sign".', ""), "under `may_not`")
        case("a role file drops what the procedure says it must be",
             lambda d: edit(d, "assistants/review.md", 'It must: "have done none of this study".', ""), "under `must`")
        case("the analysis role no longer lists held-out data as never seen",
             lambda d: edit(d, "assistants/analysis.md", '  - "held-out data before it is opened"\n', ""), "`must_never_see` does not list it")
        case("a role may call the lock", lambda d: edit(d, "assistants/coordinating.md", '  - "tools/sf.py close"', '  - "tools/sf.py close"\n  - "tools/sf.py lock"'),
             "an act of people")
        case("a role may call the signature", lambda d: edit(d, "assistants/curating.md", '  - "tools/sf.py resolve"', '  - "tools/sf.py resolve"\n  - "tools/sf.py signature"'),
             "an act of people")
        case("the review role may run a look", lambda d: edit(d, "assistants/review.md", '  - "tools/explore.py recheck"', '  - "tools/explore.py look"'),
             "does the work it is there to check")
        case("the analysis role may record a review", lambda d: edit(d, "assistants/analysis.md", '  - "tools/explore.py lead"', '  - "tools/explore.py lead"\n  - "tools/explore.py review"'),
             "only the review assistant may call")
        case("the analysis role may make the hand-over", lambda d: edit(d, "assistants/analysis.md", '  - "tools/explore.py lead"', '  - "tools/explore.py lead"\n  - "tools/explore.py hand-over"'),
             "only the coordinating assistant may call")
        case("a role names a command the tool does not have", lambda d: edit(d, "assistants/analysis.md", '"tools/explore.py choice"', '"tools/explore.py decide"'),
             "has no command `decide`")
        case("a role names a skill that does not exist", lambda d: edit(d, "assistants/analysis.md", '"skill:explore-a-record"', '"skill:explore-everything"'),
             "SKILL.md does not exist")
        case("a role names a role that does not exist", lambda d: edit(d, "assistants/coordinating.md", '"role:review"', '"role:auditing"'), "which is not a role")
        case("a role file loses a front matter key", lambda d: edit(d, "assistants/review.md", "hands_on:", "gives:"), "front matter lacks hands_on")
        case("a stage's command is taken from the role the procedure gives it to",
             lambda d: edit(d, "assistants/analysis.md", '  - "tools/sf.py test"\n', ""), "may not call `tools/sf.py test`")
        case("the procedure gives a stage to a role with no file",
             lambda d: edit(d, "factory/procedure.yaml", "    done_by: curating assistant", "    done_by: librarian assistant"), "which has no role file")
        case("the review role's file stops naming the author's account as a place it must never see",
             lambda d: edit(d, "assistants/review.md", '  - "path:record/analysis/*"\n', ""), "does not name the analysis assistant's own account")
        case("the review role's file stops naming the author's account where it is kept as flat files",
             lambda d: edit(d, "assistants/review.md", '  - "path:record/*analysis*"\n', ""), "(path:record/*analysis*)")
        case("the analysis role may name its own reviewer",
             lambda d: edit(d, "assistants/analysis.md", '  - "tools/explore.py lead"', '  - "tools/explore.py lead"\n  - "tools/explore.py reviewer"'),
             "only the coordinating assistant may call")
        case("the coordinating role can no longer name a reviewer",
             lambda d: edit(d, "assistants/coordinating.md", '  - "tools/explore.py reviewer"\n', ""), "no exploration could reach one")
        case("a role loses its own place to write its account",
             lambda d: edit(d, "assistants/curating.md", '  - "record/curating/*.md"\n', ""), "its own place for its account")
        case("a role may write in another role's place",
             lambda d: edit(d, "assistants/review.md", '  - "record/review/*.md"', '  - "record/review/*.md"\n  - "record/analysis/*.md"'), "in the analysis role's place")
        case("the skill says to set aside in another order than the role file",
             lambda d: edit(d, "skills/explore-a-record/SKILL.md", "Read what is known before you set anything aside", "Set data aside before you read what is known"),
             "do not say the same thing under **The order.**")
        case("the role file and a skill disagree on when to call end",
             lambda d: edit(d, "skills/write-up-a-lead/SKILL.md", "do not call `end`: status names the review assistant", "call `end`: status then names the review assistant"),
             "do not say the same thing under **When to end.**")
        case("the role file drops the paragraph the skills must carry",
             lambda d: edit(d, "assistants/analysis.md", "**When to end.** After", "After"), "no paragraph beginning **When to end.**")
        case("the review skill says another place to write than the role file",
             lambda d: edit(d, "skills/review-work/SKILL.md", "Your account for the coordinating assistant goes in `record/review/`", "Your account goes beside the author's"),
             "do not say the same thing under **Where you write.**")
        case("the curating skill lets it start before the end",
             lambda d: edit(d, "skills/draft-a-knowledge-page/SKILL.md", "Start on an exploration only when", "Start on an exploration whenever notes are open, even before"),
             "do not say the same thing under **When you start.**")
        case("the curating role may end an exploration", lambda d: edit(d, "assistants/curating.md", '  - "tools/explore.py resolve"', '  - "tools/explore.py resolve"\n  - "tools/explore.py end"'),
             "only the analysis assistant may call")
        case("a purpose that is not one sentence", lambda d: edit(d, "assistants/review.md", "records what it found.\"", "records what it found. It also fixes it.\""),
             "`purpose` is one sentence")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, good in results if not good]
    for n in failed:
        print("FAIL:", n)
    print(f"selftest: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)} of {len(results)})")
    return 0 if not failed else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent, help="the repository (default: the one this file is in)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    root = a.root.resolve()
    if a.selftest:
        return selftest(root)
    found = problems(root)
    for q in found:
        print("check-roles:", q)
    if found:
        print(f"check-roles: FAIL ({len(found)} disagreement(s) between assistants/ and factory/procedure.yaml)")
        return 1
    print(f"check-roles: PASS ({len(roles_in(root))} roles; assistants/ and the procedure's `assistants` block say the same thing)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
