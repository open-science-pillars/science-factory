#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""check_roles: the role files and the procedure say the same thing.

The roles are files, `factory/agents/<name>/agent.md`, one per role, in a form no agent
platform owns. The procedure (factory/factory.yaml) has a `procedure.agents` block
written for people. This check fails when the two disagree, so neither can
drift from the other unnoticed. It runs no language model and it edits
nothing.

What it checks:

  form        every role file has the six front matter keys (description,
              may_call, must_never_see, reads, writes, hands_on), carries
              no `name` (its name is its folder), and its description is
              one sentence
  same roles  the procedure's `agents` block and `factory/agents/` name the
              same roles
  same words  each role file quotes, word for word, what the procedure says
              the role does, may not do and must be, and lists under
              `must_never_see` what the procedure says it never sees
  may_call    every command names a tool in tools/ and a command that tool
              has; every skill is a shared one or the
              role's own; every role is a role
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
import sys

sys.dont_write_bytecode = True
if __name__ == "__main__" and not (sys.flags.isolated and sys.flags.no_site):
    # A clean start. This tool runs itself again in a Python that reads no PYTHON variable, no user site, no start-up
    # file (.pth, sitecustomize) and not the folder this file is in, so that none of those can change what it does.
    # What a hostile environment ran before this line has already run: a stated limit (docs/WHAT-IS-ENFORCED.md).
    import os
    _again = [sys.executable, "-I", "-S", "-B", os.path.abspath(__file__), *sys.argv[1:]]
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

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

KEYS = ("description", "may_call", "must_never_see", "reads", "writes", "hands_on")
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


DEFINITION = {}  # a repository and the definition tree to read for it, when that is not its `factory/` folder


def definition_of(root: Path) -> Path:
    return DEFINITION.get(root, root / "factory")


def roles_in(root: Path) -> dict:
    return {p.parent.name: load_role(p) for p in sorted((definition_of(root) / "agents").glob("*/agent.md"))}


def skill_file(root: Path, role: str, skill: str) -> Path | None:
    """Where a skill a role names is: the shared folder, or the role's own. Another role's own skill is not this role's."""
    for f in (definition_of(root) / "skills" / skill / "SKILL.md", definition_of(root) / "agents" / role / "skills" / skill / "SKILL.md"):
        if f.is_file():
            return f
    return None


def commands_of(tool: Path) -> set:
    """The commands a tool has, read from its source: every name it gives its argument parser."""
    text = tool.read_text(encoding="utf-8")
    return set(re.findall(r"""\badd\(\s*["']([a-z][a-z-]*)["']""", text)) | set(re.findall(r"""add_parser\(\s*["']([a-z][a-z-]*)["']""", text))


def problems(root: Path, definition: Path | None = None) -> list:
    """Every disagreement, in words. `root` is the repository the tools are in (a command in `may_call` is a file
    there); `definition` is the definition tree, by default the repository's `factory/` folder."""
    if definition is not None:
        DEFINITION[root] = Path(definition)
    p = []
    try:
        procedure = yaml.safe_load((definition_of(root) / "factory.yaml").read_text(encoding="utf-8"))["procedure"]
        block = procedure["agents"]
        stages = procedure["stages"]
        if not isinstance(block, dict):
            raise TypeError
    except (OSError, yaml.YAMLError, KeyError, TypeError):
        return ["factory/factory.yaml is missing, does not parse, or has no `procedure.agents` block and `procedure.stages`"]
    roles = roles_in(root)
    for name in sorted(set(block) - set(roles)):
        p.append(f"the procedure names the {name} assistant and factory/agents/{name}/agent.md does not exist")
    for name in sorted(set(roles) - set(block)):
        p.append(f"factory/agents/{name}/agent.md is a role the procedure's `agents` block does not name")
    tools = {}
    for name, (fm, body) in roles.items():
        where = f"factory/agents/{name}/agent.md"
        if fm is None:
            p.append(f"{where}: no front matter that parses")
            continue
        missing = [k for k in KEYS if k not in fm]
        if missing:
            p.append(f"{where}: front matter lacks {', '.join(missing)}")
            continue
        if "name" in fm:  # the path is the name: the folder the file is in, and nothing else
            p.append(f"{where}: front matter carries `name`; an agent's name is the folder its file is in")
        purpose = str(fm["description"]).strip()
        if not purpose.endswith(".") or purpose.count(". ") > 0 or len(purpose.split()) < 5:
            p.append(f"{where}: `description` is one sentence")
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
                if skill_file(root, name, c[6:]) is None:
                    p.append(f"{where}: may_call names the skill `{c[6:]}`, and its SKILL.md does not exist in factory/skills/{c[6:]}/ "
                             f"or in factory/agents/{name}/skills/{c[6:]}/")
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
                f = skill_file(root, name, skill)
                if f is not None and para not in squash(f.read_text(encoding="utf-8")):
                    p.append(f"{where} and the skill {skill} (its SKILL.md) do not say the same thing under {label}: the paragraph in the role "
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
        done_by = st.get("done_by") if isinstance(st.get("done_by"), list) else []
        for (stage, role), cmds in STAGE_COMMANDS.items():
            if st.get("id") == stage and role in done_by and role in roles and roles[role][0]:
                calls = [str(c) for c in roles[role][0].get("may_call") or []]
                for cmd in cmds:
                    if cmd not in calls:
                        p.append(f"the procedure gives the {stage} stage to the {role} assistant, and factory/agents/{role}/agent.md may not call `{cmd}`")
    for st in stages if isinstance(stages, list) else []:
        for role in (st.get("done_by") if isinstance(st.get("done_by"), list) else []):
            if role not in roles:
                p.append(f"the procedure gives the {st.get('id')} stage to the {role} assistant, which has no role file")
    return p


def selftest(root: Path) -> int:
    results = []
    tmp = Path(tempfile.mkdtemp(prefix="check-roles-")).resolve()
    try:
        def copy(name: str) -> Path:
            d = tmp / name
            for sub in ("agents", "skills"):
                shutil.copytree(definition_of(root) / sub, d / "factory" / sub)
            (d / "tools").mkdir()
            for f in (root / "tools").glob("*.py"):
                shutil.copyfile(f, d / f.relative_to(root))
            shutil.copyfile(definition_of(root) / "factory.yaml", d / "factory" / "factory.yaml")
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
        case("a role the procedure names has no file", lambda d: (d / "factory/agents/curating/agent.md").unlink(), "curating/agent.md does not exist")
        case("a role file the procedure does not name", lambda d: shutil.copytree(d / "factory/agents/review", d / "factory/agents/auditing"),
             "a role the procedure's `agents` block does not name")
        case("the procedure changes what a role does and the role file is not changed",
             lambda d: edit(d, "factory/factory.yaml", "relays questions, keeps the study moving", "relays questions and decides what counts"),
             "does not quote what the procedure says under `does`")
        case("a role file changes its quotation of the procedure",
             lambda d: edit(d, "factory/agents/review/agent.md", "and records approve or block", "and approves"), "does not quote what the procedure says under `does`")
        case("a role file drops what the procedure says it may not do",
             lambda d: edit(d, "factory/agents/curating/agent.md", 'It may not: "merge or sign".', ""), "under `may_not`")
        case("a role file drops what the procedure says it must be",
             lambda d: edit(d, "factory/agents/review/agent.md", 'It must: "have done none of this study".', ""), "under `must`")
        case("the analysis role no longer lists held-out data as never seen",
             lambda d: edit(d, "factory/agents/analysis/agent.md", '  - "held-out data before it is opened"\n', ""), "`must_never_see` does not list it")
        case("a role may call the lock", lambda d: edit(d, "factory/agents/coordinating/agent.md", '  - "tools/sf.py close"', '  - "tools/sf.py close"\n  - "tools/sf.py lock"'),
             "an act of people")
        case("a role may call the signature", lambda d: edit(d, "factory/agents/curating/agent.md", '  - "tools/sf.py resolve"', '  - "tools/sf.py resolve"\n  - "tools/sf.py signature"'),
             "an act of people")
        case("the review role may run a look", lambda d: edit(d, "factory/agents/review/agent.md", '  - "tools/explore.py recheck"', '  - "tools/explore.py look"'),
             "does the work it is there to check")
        case("the analysis role may record a review", lambda d: edit(d, "factory/agents/analysis/agent.md", '  - "tools/explore.py lead"', '  - "tools/explore.py lead"\n  - "tools/explore.py review"'),
             "only the review assistant may call")
        case("the analysis role may make the hand-over", lambda d: edit(d, "factory/agents/analysis/agent.md", '  - "tools/explore.py lead"', '  - "tools/explore.py lead"\n  - "tools/explore.py hand-over"'),
             "only the coordinating assistant may call")
        case("a role names a command the tool does not have", lambda d: edit(d, "factory/agents/analysis/agent.md", '"tools/explore.py choice"', '"tools/explore.py decide"'),
             "has no command `decide`")
        case("a role names a skill that does not exist", lambda d: edit(d, "factory/agents/analysis/agent.md", '"skill:explore-a-record"', '"skill:explore-everything"'),
             "its SKILL.md does not exist")
        case("a role names a role that does not exist", lambda d: edit(d, "factory/agents/coordinating/agent.md", '"role:review"', '"role:auditing"'), "which is not a role")
        case("a role file loses a front matter key", lambda d: edit(d, "factory/agents/review/agent.md", "hands_on:", "gives:"), "front matter lacks hands_on")
        case("a stage's command is taken from the role the procedure gives it to",
             lambda d: edit(d, "factory/agents/analysis/agent.md", '  - "tools/sf.py test"\n', ""), "may not call `tools/sf.py test`")
        case("the procedure gives a stage to a role with no file",
             lambda d: edit(d, "factory/factory.yaml", "      done_by: [curating]", "      done_by: [librarian]"), "which has no role file")
        case("the review role's file stops naming the author's account as a place it must never see",
             lambda d: edit(d, "factory/agents/review/agent.md", '  - "path:record/analysis/*"\n', ""), "does not name the analysis assistant's own account")
        case("the review role's file stops naming the author's account where it is kept as flat files",
             lambda d: edit(d, "factory/agents/review/agent.md", '  - "path:record/*analysis*"\n', ""), "(path:record/*analysis*)")
        case("the analysis role may name its own reviewer",
             lambda d: edit(d, "factory/agents/analysis/agent.md", '  - "tools/explore.py lead"', '  - "tools/explore.py lead"\n  - "tools/explore.py reviewer"'),
             "only the coordinating assistant may call")
        case("the coordinating role can no longer name a reviewer",
             lambda d: edit(d, "factory/agents/coordinating/agent.md", '  - "tools/explore.py reviewer"\n', ""), "no exploration could reach one")
        case("a role loses its own place to write its account",
             lambda d: edit(d, "factory/agents/curating/agent.md", '  - "record/curating/*.md"\n', ""), "its own place for its account")
        case("a role may write in another role's place",
             lambda d: edit(d, "factory/agents/review/agent.md", '  - "record/review/*.md"', '  - "record/review/*.md"\n  - "record/analysis/*.md"'), "in the analysis role's place")
        case("the skill says to set aside in another order than the role file",
             lambda d: edit(d, "factory/agents/analysis/skills/explore-a-record/SKILL.md", "Read what is known before you set anything aside", "Set data aside before you read what is known"),
             "do not say the same thing under **The order.**")
        case("the role file and a skill disagree on when to call end",
             lambda d: edit(d, "factory/agents/analysis/skills/write-up-a-lead/SKILL.md", "do not call `end`: status names the review assistant", "call `end`: status then names the review assistant"),
             "do not say the same thing under **When to end.**")
        case("the role file drops the paragraph the skills must carry",
             lambda d: edit(d, "factory/agents/analysis/agent.md", "**When to end.** After", "After"), "no paragraph beginning **When to end.**")
        case("the review skill says another place to write than the role file",
             lambda d: edit(d, "factory/agents/review/skills/review-work/SKILL.md", "Your account for the coordinating assistant goes in `record/review/`", "Your account goes beside the author's"),
             "do not say the same thing under **Where you write.**")
        case("the curating skill lets it start before the end",
             lambda d: edit(d, "factory/agents/curating/skills/draft-a-knowledge-page/SKILL.md", "Start on an exploration only when", "Start on an exploration whenever notes are open, even before"),
             "do not say the same thing under **When you start.**")
        case("the curating role may end an exploration", lambda d: edit(d, "factory/agents/curating/agent.md", '  - "tools/explore.py resolve"', '  - "tools/explore.py resolve"\n  - "tools/explore.py end"'),
             "only the analysis assistant may call")
        case("a description that is not one sentence", lambda d: edit(d, "factory/agents/review/agent.md", "records what it found.\"", "records what it found. It also fixes it.\""),
             "`description` is one sentence")
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
        print(f"check-roles: FAIL ({len(found)} disagreement(s) between factory/agents/ and factory/factory.yaml)")
        return 1
    print(f"check-roles: PASS ({len(roles_in(root))} roles; factory/agents/ and the procedure's `agents` block say the same thing)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
