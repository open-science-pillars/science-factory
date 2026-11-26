#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""allow: the decision a role's tool call gets under the Claude Code runner.

Claude Code calls this before every tool call a role makes (a PreToolUse
hook in the rendered `.claude/agents/<role>.md`). It reads the role file in
`assistants/` each time, so the neutral file is the rule and nothing is
copied into a setting. It runs no language model. It allows what the role
file allows and blocks everything else, with the reason.

  Bash     one plain command and nothing else, of one shape:
           `uv run [--script] tools/<tool>.py <command>` and then that
           command's own options, where `tools/<tool>.py <command>` is in
           the role's `may_call`. The check does not try to read a command
           as a shell would. It refuses outright any command that holds
           ` $ \\ ; & | < > ( ) { } # ! or a line break, quoted or not, and
           anything outside quotes but letters, digits and _ @ + : , . / =
           -, so there is nothing left for a shell to read another way.
           Each option must be one the tool's own argument parser has,
           spelled out in full (`--b` is not `--by`; the tools take no
           shortened option either). A `--by` must be the role's own name:
           agent:<role> or agent:<role>-<anything>. A file or folder given
           to a command is checked as a read would be.
  Run      the same rule for a command already in words, run with no
           shell (the by-hand runner): nothing is quoted, so a bracket in
           a value is only a bracket.
  Write,   only a path that matches one of the role's `writes` patterns,
  Edit     and never a file the tools keep: a log, the record of what has
           been opened, a receipt, a recorded verdict, a recorded lead, a
           role, a skill, a tool, or the rendered files.
  Read,    anything except a path that an exploration beside it set aside
  Grep,    or that a study's plan beside it holds out, and a path the role
  Glob     file names under `must_never_see` as `path:<pattern>` (the review
           role's file names the analysis role's own account that way,
           in a folder of its own, record/analysis/, and as flat files,
           record/*analysis*). A search over a folder that holds such a
           path, however far down, is blocked too, and so is a search with
           no folder named or over a folder too large to walk: search a
           narrower place.
  wiki     the two read-only wiki tools, openwiki_search and openwiki_read,
           from any server; no other tool of any server.
  Skill    only a skill in the role's `may_call`.
  Agent    only a role in the role's `may_call` (the coordinating role).
  other    blocked.

What this does not do. It decides one tool call at a time from the call's
own text. It cannot see what a script run through `explore.py look` or
`sf.py test` does once it is running; the tools' own fence and the log
stand there. Claude Code hands a Bash command to a shell, and this check
cannot change that: what it can do is take only commands a shell reads one
way. And it only runs when the role is started through the rendered agent
file: a conversation started without it is not held by it.

Usage: allow.py --role ROLE     (the tool call as JSON on standard input;
                                 exit 0 allows, exit 2 blocks with the reason)
       allow.py --selftest
"""
import sys

sys.dont_write_bytecode = True  # the tools are loaded from tools/ to read their options; no bytecode folder is left there

import argparse  # noqa: E402
import fnmatch  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
KEPT_BY_THE_TOOLS = ("*-log.jsonl", "openings.jsonl", "set-aside.json", "lead.json", "lead.md", "curation-list.json", "scorecard.json",
                     "queue.json", "hand-over.json")
KEPT_FOLDERS = ("receipts", "verdicts", "leads", "hand-over", "notes", ".claude", "assistants", "skills", "runners", "tools", "factory", "methods", "compute", ".git", ".github")
READ_TOOLS = ("Read", "Grep", "Glob", "NotebookRead")
WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
WIKI_TOOLS = ("openwiki_search", "openwiki_read")  # read-only, from any server
HARMLESS = ("TodoWrite", "TaskCreate", "TaskUpdate", "TaskList", "TaskGet")


def role_file(role: str, root: Path = ROOT) -> dict:
    path = root / "assistants" / f"{role}.md"
    if not re.fullmatch(r"[a-z][a-z-]*", role or "") or not path.is_file():
        raise ValueError(f"there is no role file assistants/{role}.md")
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    fm = yaml.safe_load(text[4:end]) if text.startswith("---\n") and end > 0 else None
    if not isinstance(fm, dict):
        raise ValueError(f"assistants/{role}.md has no front matter that parses")
    return fm


NEVER = set("`$\\;&|<>(){}#!")  # what a shell acts on, or reads as the start of a comment: refused anywhere, quoted or not
PLAIN = re.compile(r"[A-Za-z0-9_@+:,./=-]")  # what a word may hold outside quotes
SHAPE = ("a role runs one plain command and nothing else: `uv run tools/<tool>.py <command> ...` with each option spelled out. "
         "Write values in plain words. Outside quotes a word holds letters, digits and _ @ + : , . / = -; inside single or double "
         "quotes it may also hold spaces and ? * [ ] ~ % ^. Nowhere, quoted or not: ` $ \\ ; & | < > ( ) { } # ! or a line break")


def plain_words(command: str) -> tuple:
    """(the words of a command, None) or (None, why it is refused). This does not try to read a command the way a
    shell does. It takes only commands so plain that every shell reads them one way: words of harmless characters,
    whole quoted stretches with nothing a shell acts on inside them, single spaces between. Anything else is
    refused outright, so there is no second reading for a command to hide in."""
    for ch in command:
        if ch in NEVER or ord(ch) < 32 or ord(ch) == 127:
            shown = {"\n": "a line break", "\r": "a line break", "\t": "a tab"}.get(ch, f"`{ch}`" if ch in NEVER else "a control character")
            return None, f"the command holds {shown}. {SHAPE}"
    words, cur, i = [], None, 0
    while i < len(command):
        ch = command[i]
        if ch == " ":
            if cur is not None:
                words.append(cur)
                cur = None
        elif ch in "'\"":
            end = command.find(ch, i + 1)
            if end < 0:
                return None, "a quote in the command is not closed"
            cur = (cur or "") + command[i + 1:end]
            i = end
        elif PLAIN.fullmatch(ch):
            if cur is None and ch == "=":
                return None, f"a word of the command begins with `=` outside quotes, which one shell expands. {SHAPE}"
            cur = (cur or "") + ch
        else:
            return None, f"the command holds `{ch}` outside quotes. {SHAPE}"
        i += 1
    if cur is not None:
        words.append(cur)
    return words, None


_TOOLS = {}


def options_of(tool: Path, command: str) -> tuple | None:
    """(each option of one command of a tool and whether it takes a value, how many plain words it takes, whether it
    takes a command after `--`), read from the tool's own argument parser, so this check and the tool cannot read an
    option differently. None when the tool has no such command or its parser cannot be read."""
    if tool not in _TOOLS:
        try:
            spec = importlib.util.spec_from_file_location("allowed_" + tool.stem, tool)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            parser = mod.build_parser()
            _TOOLS[tool] = next(a.choices for a in parser._actions if isinstance(a, argparse._SubParsersAction))
        except Exception:  # a tool that cannot be read allows nothing
            _TOOLS[tool] = None
    commands = _TOOLS[tool]
    if not commands or command not in commands:
        return None
    options, plain, remainder = {}, 0, False
    for act in commands[command]._actions:
        if act.option_strings:
            options.update({o: act.nargs != 0 for o in act.option_strings})
        elif act.nargs == argparse.REMAINDER:
            remainder = True
        else:
            plain += 1
    return options, plain, remainder


def argv_problem(words: list, role: str, fm: dict, cwd: Path, root: Path = ROOT) -> str | None:
    """Why a command, already in words, is not one this role may run. One shape is taken: `uv run [--script]
    tools/<tool>.py <command>`, then that command's own options, each spelled out in full, and its plain words."""
    if words[:2] != ["uv", "run"]:
        return "a role's command starts with `uv run tools/<tool>.py <command>`"
    i = 2
    if i < len(words) and words[i] == "--script":
        i += 1
    if i + 1 >= len(words):
        return "a role's command is `uv run tools/<tool>.py <command> ...`"
    script = (cwd / words[i]).resolve()
    if script.parent != (root / "tools").resolve() or not script.is_file():
        return f"`{words[i]}` is not a tool of this package (under tools/ in {root})"
    call = f"{script.relative_to(root.resolve()).as_posix()} {words[i + 1]}"
    allowed = [str(c) for c in fm.get("may_call") or [] if not str(c).startswith(("skill:", "role:"))]
    if call not in allowed:
        return f"the {role} assistant may not call `{call}`. Its role file allows: {', '.join(allowed)}"
    known = options_of(script, words[i + 1])
    if known is None:
        return f"the options of `{call}` could not be read from the tool, so the command is not allowed"
    options, plain, remainder = known
    rest = words[i + 2:]
    if "--" in rest:
        if not remainder:
            return f"`{call}` takes no command after `--`"
        rest = rest[:rest.index("--")]  # the words of a look belong to the look; explore.py reads them
    values, j, seen = [], 0, 0
    while j < len(rest):
        w = rest[j]
        if w.startswith("-") and w != "-":
            name, eq, value = w.partition("=")
            if name not in options:
                return (f"`{name}` is not an option of `{call}`. Each option is spelled out in full ({', '.join(sorted(o for o in options if o.startswith('--')))}); "
                        "a shortened option is not taken")
            if options[name]:
                if not eq:
                    j += 1
                    if j >= len(rest) or rest[j].startswith("-"):
                        return f"`{name}` is followed by its value, and a value does not begin with a dash"
                    value = rest[j]
                values.append((name, value))
            elif eq:
                return f"`{name}` takes no value"
        else:
            seen += 1
            if seen > plain:
                return f"`{w}` is a word `{call}` has no place for: every value follows its option"
            values.append((None, w))
        j += 1
    for name, value in values:
        if name == "--by" and not (value == f"agent:{role}" or value.startswith(f"agent:{role}-")):
            return f"`--by {value}` is not this role's name: the {role} assistant acts as agent:{role} or agent:{role}-<suffix>"
        if value and (cwd / value).exists():  # a tool reads the files it is given: what the role may not read, it may not hand to a tool
            why = read_problem(value, fm, cwd, search=(cwd / value).is_dir())
            if why:
                return f"{name or 'the word'} `{value}`: {why}"
    return None


def bash_problem(command: str, role: str, fm: dict, cwd: Path, root: Path = ROOT) -> str | None:
    words, why = plain_words(command)
    return why if words is None else argv_problem(words, role, fm, cwd, root)


def write_problem(path: str, role: str, fm: dict, cwd: Path) -> str | None:
    p = Path(os.path.normpath(cwd / path))
    if any(fnmatch.fnmatch(p.name, pat) for pat in KEPT_BY_THE_TOOLS) or any(part in KEPT_FOLDERS for part in p.parts[:-1]):
        return f"`{path}` is kept by the tools or is part of the factory's own files; no role writes it by hand"
    posix = p.as_posix()
    for pat in fm.get("writes") or []:
        if fnmatch.fnmatch(posix, "*/" + str(pat)):
            return None
    return (f"the {role} assistant may not write `{path}`. Its role file lets it write: "
            + (", ".join(str(w) for w in fm.get("writes") or []) or "nothing"))


def fenced_paths(p: Path) -> list:
    """What explorations and studies beside a path say is set aside or held out, as paths."""
    out = []
    for up in list(p.parents)[:8]:
        for f in up.glob("explorations/*/set-aside.json"):
            try:
                out += [Path(q) for q in json.loads(f.read_text())["set_aside"].get("paths") or []]
            except (OSError, ValueError, KeyError, AttributeError):
                pass
        for f in up.glob("studies/*/analysis-plan.yaml"):
            try:
                plan = yaml.safe_load(f.read_text())
                rels = [plan["data"]["held_out"].get("path")] + [(t or {}).get("data") for t in (plan.get("tests") or {}).values()]
                out += [f.parent / r for r in rels if isinstance(r, str) and r]
            except (OSError, yaml.YAMLError, KeyError, TypeError, AttributeError):
                pass
    return out


def never_seen_patterns(fm: dict) -> list:
    """The `path:<pattern>` entries of a role's `must_never_see`: places the role has no business reading, as patterns."""
    return [str(x)[5:].strip() for x in fm.get("must_never_see") or [] if str(x).startswith("path:") and str(x)[5:].strip()]


def names_place(posix: str, pat: str) -> bool:
    """Does a path lie at, or below, a place a pattern names? The pattern is matched piece by piece against every run
    of folders in the path, in any case, so `record/*analysis*` names `x/record/02-analysis.answer.md`, the folder
    `x/record/analysis` and every file below it, and does not name `x/record/review/on-the-analysis.md`."""
    parts = [q for q in posix.casefold().split("/") if q]
    for want in {pat.casefold(), pat.casefold().removesuffix("/*")}:
        pieces = [q for q in want.split("/") if q]
        for start in range(0, len(parts) - len(pieces) + 1):
            if all(fnmatch.fnmatchcase(parts[start + k], pieces[k]) for k in range(len(pieces))):
                return True
    return False


TOO_BROAD = 50000  # files and folders: a search over more than this is not walked, and is refused as too broad


def read_problem(path: str | None, fm: dict, cwd: Path, search: bool = False, pattern: str | None = None) -> str | None:
    if not fm.get("must_never_see"):
        return None
    if not path and not search:
        return "the call names nothing to read"
    p = Path(os.path.normpath(cwd / (path or ".")))
    never = never_seen_patterns(fm)
    for shown, q in ((path, p), (path, Path(os.path.realpath(p)))):
        for pat in never:
            if names_place(q.as_posix(), pat):
                return (f"`{shown}` is in a place this role must never see ({pat}): the account of the assistant whose work it "
                        "checks. Work from the files of the work itself")
    if search and never:
        if pattern and (Path(pattern).is_absolute() or ".." in Path(pattern).parts or pattern.startswith("~")):
            return "a search pattern that leaves the folder it is given is not taken: name the folder in `path`"
        if p.is_dir():  # a search over a folder that holds such a place would read it, however far down it lies
            walked = 0
            for base, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
                walked += len(dirs) + len(files)
                if walked > TOO_BROAD:
                    return (f"a search over `{path or '.'}` is too broad to check for the places this role must never see; "
                            "search a narrower place, such as the exploration's own folder")
                for name in dirs + files:
                    for pat in never:
                        if names_place((Path(base) / name).as_posix(), pat):
                            return (f"a search over `{path or '.'}` would read a place this role must never see ({pat}); search a "
                                    "narrower place, such as the exploration's own folder")
    fenced = fenced_paths(p)
    if search and p.is_dir():  # what explorations and studies below the folder searched say is set aside or held out
        walked = 0
        for base, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
            walked += len(dirs) + len(files)
            if walked > TOO_BROAD:
                return f"a search over `{path or '.'}` is too broad to check for set-aside and held-out data; search a narrower place"
            if Path(base).name in ("explorations", "studies"):
                fenced += fenced_paths(Path(base) / "x")
    for q in fenced:
        q = Path(os.path.normpath(q))
        if p == q or q in p.parents:
            return f"`{path}` is set aside or held out; this role has no route to it"
        if search and p in q.parents and q.exists():
            return f"a search over `{path or '.'}` would read `{q}`, which is set aside or held out; search a narrower place"
    return None


def decide(role: str, call: dict, root: Path = ROOT) -> str | None:
    """None when the call is allowed, or the reason it is blocked."""
    try:
        fm = role_file(role, root)
    except (ValueError, OSError, yaml.YAMLError) as e:
        return f"{e}; with no role file nothing is allowed"
    tool, given = str(call.get("tool_name") or ""), call.get("tool_input") or {}
    cwd = Path(call.get("cwd") or os.getcwd())
    if tool == "Bash":
        return bash_problem(str(given.get("command") or ""), role, fm, cwd, root)
    if tool == "Run":  # a command already in words, run with no shell (the by-hand runner): the same rule, with nothing for a shell to read
        argv = given.get("argv")
        return argv_problem([str(w) for w in argv], role, fm, cwd, root) if isinstance(argv, list) and argv else "no command was given"
    if tool in WRITE_TOOLS:
        return write_problem(str(given.get("file_path") or given.get("notebook_path") or ""), role, fm, cwd)
    if tool in READ_TOOLS:
        return read_problem(given.get("file_path") or given.get("path"), fm, cwd, search=tool in ("Grep", "Glob"),
                            pattern=str(given.get("pattern") or "") if tool == "Glob" else None)
    if tool == "Skill":
        name = str(given.get("skill") or given.get("name") or "")
        return None if f"skill:{name}" in (fm.get("may_call") or []) else f"the {role} assistant may not use the skill `{name}`"
    if tool in ("Agent", "Task"):
        name = str(given.get("subagent_type") or "")
        return None if f"role:{name}" in (fm.get("may_call") or []) else f"the {role} assistant may not start `{name or 'an unnamed assistant'}`"
    if tool in HARMLESS or tool.rsplit("__", 1)[-1] in WIKI_TOOLS:
        return None
    return f"the {role} assistant has no use for the tool `{tool}`; it is not in its role"


def selftest() -> int:
    results = []
    cwd = str(ROOT)

    def blocked(role: str, tool: str, **given) -> bool:
        return decide(role, {"tool_name": tool, "tool_input": given, "cwd": cwd}) is not None

    def ok(name: str, cond) -> None:
        results.append((name, bool(cond)))

    x = "examples/w/explorations/E1"
    ok("analysis may run a look", not blocked("analysis", "Bash", command=f"uv run tools/explore.py look --exploration {x} --by agent:analysis --why 'see pairs' -- uv run looks/a.py d.json"))
    ok("analysis may start an exploration", not blocked("analysis", "Bash", command=f"uv run tools/explore.py start --exploration {x} --by agent:analysis-1 --id E1"))
    ok("analysis may not record a review", blocked("analysis", "Bash", command=f"uv run tools/explore.py review --exploration {x} --by agent:analysis --verdict no-holes-found --file r.md"))
    ok("analysis may not act under the review role's name", blocked("analysis", "Bash", command=f"uv run tools/explore.py note --exploration {x} --by agent:review --kind missing --about a --text b"))
    ok("analysis may not act under a person's name", blocked("analysis", "Bash", command=f"uv run tools/explore.py note --exploration {x} --by human:someone --kind missing --about a --text b"))
    ok("analysis may not make the hand-over", blocked("analysis", "Bash", command=f"uv run tools/explore.py hand-over --exploration {x} --by agent:analysis --study-id S"))
    ok("no role may lock", all(blocked(r, "Bash", command=f"uv run tools/sf.py lock --study s --by agent:{r} --evidence https://e.org/1") for r in ("coordinating", "analysis", "review", "curating")))
    ok("no role may sign", all(blocked(r, "Bash", command=f"uv run tools/sf.py signature --study s --by agent:{r} --decision signed") for r in ("coordinating", "analysis", "review", "curating")))
    ok("review may record a review", not blocked("review", "Bash", command=f"uv run tools/explore.py review --exploration {x} --by agent:review --verdict holes-found --file r.md"))
    ok("review may recheck a look", not blocked("review", "Bash", command=f"uv run tools/explore.py recheck --exploration {x} --look LOOK-001"))
    ok("review may not run a look", blocked("review", "Bash", command=f"uv run tools/explore.py look --exploration {x} --by agent:review --why w -- uv run looks/a.py"))
    ok("curating may check drafts", not blocked("curating", "Bash", command="uv run tools/knowledge.py check-drafts --queue q --bundle b"))
    ok("curating may not run a look", blocked("curating", "Bash", command=f"uv run tools/explore.py look --exploration {x} --by agent:curating --why w -- uv run looks/a.py"))
    ok("coordinating may make the hand-over", not blocked("coordinating", "Bash", command=f"uv run tools/explore.py hand-over --exploration {x} --by agent:coordinating --study-id S"))
    ok("coordinating may not run a look", blocked("coordinating", "Bash", command=f"uv run tools/explore.py look --exploration {x} --by agent:coordinating --why w -- uv run looks/a.py"))
    ok("a quoted reason in plain words is taken, a question mark and a comma included",
       not blocked("analysis", "Bash", command=f"uv run tools/explore.py look --exploration {x} --by agent:analysis --why 'do the pairs within 15 min, all of them, give one gain?' -- uv run looks/a.py"))
    ok("brackets and a semicolon are refused even inside quotes: nothing a shell acts on is taken anywhere",
       blocked("analysis", "Bash", command=f"uv run tools/explore.py look --exploration {x} --by agent:analysis --why 'pairs (within 15 min); then gain' -- uv run looks/a.py"))
    ok("a subshell is blocked", blocked("analysis", "Bash", command=f"(uv run tools/explore.py status --exploration {x})"))
    ok("a command after a semicolon is blocked", blocked("analysis", "Bash", command=f"uv run tools/explore.py status --exploration {x}; cat secret"))
    ok("a variable inside double quotes is blocked", blocked("analysis", "Bash", command='uv run tools/explore.py status --exploration "$HOME"'))
    ok("a chained command is blocked", blocked("analysis", "Bash", command=f"uv run tools/explore.py status --exploration {x} && cat secret"))
    ok("a piped command is blocked", blocked("analysis", "Bash", command=f"uv run tools/explore.py status --exploration {x} | tee out"))
    ok("a substitution is blocked", blocked("analysis", "Bash", command="uv run tools/explore.py status --exploration $(cat x)"))
    ok("a redirection is blocked", blocked("analysis", "Bash", command=f"uv run tools/explore.py status --exploration {x} > lead.md"))
    ok("a bare interpreter is blocked", blocked("analysis", "Bash", command="python3 looks/a.py held-out.json"))
    ok("a fetch is blocked", blocked("analysis", "Bash", command="curl https://example.org/data"))
    ok("a tool of the same name somewhere else is blocked", blocked("analysis", "Bash", command="uv run /tmp/tools/explore.py status --exploration x"))
    ok("an environment assignment in front is blocked", blocked("analysis", "Bash", command=f"X=1 uv run tools/explore.py status --exploration {x}"))
    ok("analysis may write a look script", not blocked("analysis", "Write", file_path=f"{x}/looks/pairs.py"))
    ok("analysis may write the lead file", not blocked("analysis", "Write", file_path=f"{x}/lead.yaml"))
    ok("analysis may not write the recorded lead", blocked("analysis", "Write", file_path=f"{x}/lead.md"))
    ok("analysis may not write the log", blocked("analysis", "Edit", file_path=f"{x}/exploration-log.jsonl"))
    ok("analysis may not write a receipt", blocked("analysis", "Write", file_path=f"{x}/receipts/LOOK-001.json"))
    ok("analysis may not write the record of what has been opened", blocked("analysis", "Write", file_path="examples/w/studies/openings.jsonl"))
    ok("analysis may not write a draft into the queue", blocked("analysis", "Write", file_path="examples/w/knowledge-queue/gotchas/a.md"))
    ok("analysis may not write a review", blocked("analysis", "Write", file_path=f"{x}/review/r.md"))
    ok("review may write its review file", not blocked("review", "Write", file_path=f"{x}/review/r.md"))
    ok("review may not write a look script", blocked("review", "Write", file_path=f"{x}/looks/pairs.py"))
    ok("review may not write the lead file", blocked("review", "Write", file_path=f"{x}/lead.yaml"))
    ok("review may not write a recorded verdict by hand", blocked("review", "Write", file_path=f"{x}/verdicts/REVIEW-001.md"))
    ok("curating may write a draft into the queue", not blocked("curating", "Write", file_path="examples/w/knowledge-queue/gotchas/a.md"))
    ok("curating may not write the queue's index by hand", blocked("curating", "Write", file_path="examples/w/knowledge-queue/queue.json"))
    ok("curating may not write a role file", blocked("curating", "Edit", file_path="assistants/curating.md"))
    ok("curating may not write into a path outside the queue", blocked("curating", "Write", file_path="../hydrology/knowledge/gotchas/a.md"))
    ok("coordinating writes nothing", blocked("coordinating", "Write", file_path=f"{x}/looks/a.py") and blocked("coordinating", "Write", file_path="notes.md")
       and blocked("coordinating", "Write", file_path=f"{x}/review/r.md"))
    ok("analysis may correct the wording of its lead, and no other role may",
       not blocked("analysis", "Bash", command=f"uv run tools/explore.py correct --exploration {x} --by agent:analysis --old a --new b --why c")
       and blocked("review", "Bash", command=f"uv run tools/explore.py correct --exploration {x} --by agent:review --old a --new b --why c"))
    ok("no role may edit the tools", all(blocked(r, "Edit", file_path="tools/explore.py") for r in ("coordinating", "analysis", "review", "curating")))
    ok("analysis may use its skills", not blocked("analysis", "Skill", skill="explore-a-record"))
    ok("analysis may not use the curating skill", blocked("analysis", "Skill", skill="draft-a-knowledge-page"))
    ok("coordinating may start the three other roles", not any(blocked("coordinating", "Agent", subagent_type=r) for r in ("analysis", "review", "curating")))
    ok("coordinating may not start an assistant that is not a role", blocked("coordinating", "Agent", subagent_type="general-purpose"))
    ok("analysis may not start another assistant", blocked("analysis", "Agent", subagent_type="review"))
    ok("a tool outside the role is blocked", blocked("analysis", "WebFetch", url="https://example.org") and blocked("review", "WebSearch", query="x"))
    ok("every role may search and read the wiki through the two read-only tools",
       not any(blocked(r, "mcp__openwiki__openwiki_search", query="x") or blocked(r, "mcp__openwiki__openwiki_read", path="a.md") for r in ("coordinating", "analysis", "review", "curating")))
    ok("any other tool of a server is blocked, a writing one included", blocked("curating", "mcp__openwiki__openwiki_write", path="a.md") and blocked("analysis", "mcp__other__fetch", url="x"))
    ok("a role with no file gets nothing", blocked("auditing", "Read", file_path="README.md"))
    # each role has its own place for its account, and the review role has no route to the author's
    ok("each role may write its account in its own place",
       not any(blocked(r, "Write", file_path=f"examples/w/record/{r}/01.answer.md") for r in ("analysis", "review", "curating"))
       and blocked("coordinating", "Write", file_path="examples/w/record/coordinating/01.task.md"))
    ok("no role may write in another role's place",
       blocked("review", "Write", file_path="examples/w/record/analysis/01.answer.md") and blocked("analysis", "Write", file_path="examples/w/record/review/02.answer.md")
       and blocked("curating", "Write", file_path="examples/w/record/review/02.answer.md"))
    ok("the review role may not read the analysis role's own account of the work",
       blocked("review", "Read", file_path="examples/w/record/analysis/01.answer.md") and blocked("review", "Grep", path="examples/w/record/analysis", pattern="gain"))
    ok("the review role may read the work itself, and its own earlier review",
       not blocked("review", "Read", file_path=f"{x}/lead.md") and not blocked("review", "Read", file_path="examples/w/record/review/02.answer.md"))
    ok("the analysis role may read its own account, and a review handed back to it",
       not blocked("analysis", "Read", file_path="examples/w/record/analysis/01.answer.md") and not blocked("analysis", "Read", file_path=f"{x}/verdicts/REVIEW-001.md"))
    # ---- what an independent attack found (docs/reviews/ASSISTANTS-AND-EXPLORING.md, round 4) --------------------
    status = f"uv run tools/explore.py status --exploration {x}"
    review = f"uv run tools/explore.py review --exploration {x} --by agent:review-smuggled --verdict no-holes-found --file r.md"
    lock = "uv run tools/sf.py lock --study s --by human:someone --evidence https://example.org/pull/1"
    ok("a second command hidden behind a `#` that a shell does not read as a comment is blocked: a review for the review role, the lock for the coordinating role",
       blocked("review", "Bash", command=f"{status}#x; {review}") and blocked("coordinating", "Bash", command=f"uv run tools/sf.py status --study s#x; {lock}")
       and blocked("analysis", "Bash", command=f"{status}#; touch /tmp/pwned"))
    hidden = {"a `#` after a space": f"{status} #x\n{review}", "a line break": f"{status}\n{review}", "a carriage return": f"{status}\r{review}",
              "a tab": f"{status}\t{review}", "a backslash and a line break": f"{status} \\\n; {review}", "ANSI quoting": f"{status} $'\\x3b' {review}",
              "a brace list a shell would expand into words": "uv run tools/explore.py {status,review} --exploration x",
              "a brace list inside a name": f"{status} --anchor agent:review{{,-x}}", "a star outside quotes": f"{status} *",
              "a tilde outside quotes": "uv run tools/explore.py status --exploration ~/x", "an exclamation mark": f"{status} !!",
              "a word that begins with `=`": f"{status} =ls", "a quote that is not closed": f"{status} 'x", "a `#` inside quotes": f"{status} --anchor '1:a#b'",
              "a semicolon inside double quotes": f'{status} --anchor "1:a; {review}"', "a space that is not a space": f"{status} {review}",
              "a here-string": f"{status} <<< x", "a background job": f"{status} & {review}", "a percent sign outside quotes": f"{status} %1"}
    let_through = [name for name, command in hidden.items() if not blocked("review", "Bash", command=command)]
    ok("every other way tried to make a shell read more than the check does is blocked" + (f" (let through: {let_through})" if let_through else ""), not let_through)
    note = f"uv run tools/explore.py note --exploration {x} --kind missing --about a --text b"
    ok("a shortened `--by` does not get past the name check: `--b` and `--b=` are blocked, under another role's name or a person's",
       blocked("analysis", "Bash", command=f"{note} --b agent:review-9") and blocked("analysis", "Bash", command=f"{note} --b=human:someone")
       and blocked("analysis", "Bash", command=f"uv run tools/sf.py note --study s --kind missing --about a --text b --b human:someone")
       and not blocked("analysis", "Bash", command=f"{note} --by agent:analysis-2"))
    ok("an option is taken only when the tool has it, spelled out: a shortened one, an unknown one, a value that begins with a dash and a stray word are blocked",
       blocked("analysis", "Bash", command="uv run tools/explore.py status --explor x") and blocked("analysis", "Bash", command=f"{status} --force")
       and blocked("analysis", "Bash", command=f"{note} --by agent:analysis --evidence --by=human:x") and blocked("analysis", "Bash", command=f"{status} extra")
       and blocked("curating", "Bash", command="uv run tools/knowledge.py check-drafts --queue q --wiki w --check evil.py")
       and blocked("review", "Bash", command=f"uv run tools/explore.py recheck --exploration {x} --look LOOK-001 -- uv run looks/a.py"))
    ok("the same rule holds for a command given in words and run with no shell, where a bracket in a value is only a bracket",
       decide("analysis", {"tool_name": "Run", "tool_input": {"argv": ["uv", "run", "tools/explore.py", "note", "--exploration", x, "--by", "agent:analysis", "--kind", "missing", "--about", "a", "--text", "pairs (15 min); then gain"]}, "cwd": cwd}) is None
       and decide("analysis", {"tool_name": "Run", "tool_input": {"argv": ["uv", "run", "tools/explore.py", "note", "--exploration", x, "--b", "human:someone", "--kind", "missing", "--about", "a", "--text", "b"]}, "cwd": cwd}) is not None
       and decide("analysis", {"tool_name": "Run", "tool_input": {"argv": ["bash", "-c", "uv run tools/explore.py status --exploration x"]}, "cwd": cwd}) is not None)
    ok("only the coordinating role names a reviewer, and the analysis role may say what else a look reads",
       not blocked("coordinating", "Bash", command=f"uv run tools/explore.py reviewer --exploration {x} --by agent:coordinating --reviewer agent:review-01")
       and blocked("analysis", "Bash", command=f"uv run tools/explore.py reviewer --exploration {x} --by agent:analysis --reviewer agent:review-01")
       and blocked("review", "Bash", command=f"uv run tools/explore.py reviewer --exploration {x} --by agent:review --reviewer agent:review-02")
       and not blocked("analysis", "Bash", command=f"uv run tools/explore.py look --exploration {x} --by agent:analysis --why 'see pairs' --also-reads looks/helper.py -- uv run looks/a.py d.json"))
    flat = [q for q in ("examples/baton-rouge/record/02-analysis.answer.md", "examples/baton-rouge/with-assistants/record/01-analysis.answer.md",
                        "examples/baton-rouge/record/07-analysis-second-question.answer.md") if (ROOT / q).is_file()]
    ok("the review role may not read the author's account where the kept example keeps it, as flat files in record/",
       len(flat) == 3 and all(blocked("review", "Read", file_path=q) for q in flat)
       and blocked("review", "Read", file_path="examples/w/record/04-analysis.answer.md") and blocked("review", "Read", file_path="examples/w/Record/Analysis/01.answer.md")
       and blocked("review", "Read", file_path="examples/w/record/analysis"))
    ok("the review role may still read its own account, a file of its own that only has the word in its name included, and the work",
       not blocked("review", "Read", file_path="examples/w/record/review/on-the-analysis.md") and not blocked("review", "Read", file_path="examples/w/record/03-review.answer.md")
       and not blocked("review", "Read", file_path="examples/baton-rouge/explorations/EXPLORATION-0001/lead.md"))
    ok("a search by the review role with no folder named, over the whole repository, or over the whole disk is blocked",
       blocked("review", "Grep", pattern="gain") and blocked("review", "Grep", path=".", pattern="gain") and blocked("review", "Grep", path="/", pattern="gain")
       and blocked("review", "Glob", pattern="**/*.md") and blocked("review", "Grep", path="examples/baton-rouge", pattern="gain")
       and blocked("review", "Glob", path="tools", pattern="../examples/baton-rouge/record/*") and blocked("review", "Read"))
    ok("the review role cannot have a tool read the author's account for it: a file or a folder given to a command is checked like a read",
       blocked("review", "Bash", command=f"uv run tools/explore.py review --exploration {x} --by agent:review --verdict holes-found --file {flat[0] if flat else 'x'}")
       and blocked("review", "Bash", command="uv run tools/knowledge.py about --question 'what did the author say' --wiki examples/baton-rouge/record")
       and not blocked("review", "Bash", command="uv run tools/knowledge.py about --question 'what is known' --wiki openwiki"))
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="allow-selftest-")).resolve()
    try:
        held = tmp / "held" / "later.json"
        (tmp / "explorations" / "E1").mkdir(parents=True)
        (tmp / "explorations" / "E1" / "set-aside.json").write_text(json.dumps({"set_aside": {"paths": [str(held.parent)]}}))
        (tmp / "studies" / "S1").mkdir(parents=True)
        (tmp / "studies" / "S1" / "analysis-plan.yaml").write_text("data:\n  held_out:\n    path: data/held.json\ntests: {}\n")
        ok("reading a path an exploration set aside is blocked", decide("analysis", {"tool_name": "Read", "tool_input": {"file_path": str(held)}, "cwd": str(tmp)}) is not None)
        ok("reading a study's held-out data path is blocked", decide("review", {"tool_name": "Read", "tool_input": {"file_path": str(tmp / "studies/S1/data/held.json")}, "cwd": str(tmp)}) is not None)
        ok("reading working data is allowed", decide("analysis", {"tool_name": "Read", "tool_input": {"file_path": str(tmp / "working.json")}, "cwd": str(tmp)}) is None)
        (tmp / "run" / "record" / "analysis").mkdir(parents=True)
        (tmp / "run" / "explorations" / "E2").mkdir(parents=True)
        ok("a search by the review role over a folder that holds the author's account is blocked",
           decide("review", {"tool_name": "Grep", "tool_input": {"path": str(tmp / "run"), "pattern": "gain"}, "cwd": str(tmp)}) is not None)
        ok("a search over a folder that holds set-aside data is blocked, for any role",
           (held.parent.mkdir(parents=True, exist_ok=True) or True) and (held.write_text("{}") or True)
           and decide("analysis", {"tool_name": "Grep", "tool_input": {"path": str(tmp), "pattern": "rows"}, "cwd": str(tmp)}) is not None)
        ok("a search by the review role inside the exploration is allowed",
           decide("review", {"tool_name": "Grep", "tool_input": {"path": str(tmp / "run" / "explorations" / "E2"), "pattern": "gain"}, "cwd": str(tmp)}) is None)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, good in results if not good]
    for n in failed:
        print("FAIL:", n)
    print(f"selftest: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)} of {len(results)})")
    return 0 if not failed else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    ap.add_argument("--role")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    try:
        call = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        print("the tool call could not be read, so it is blocked", file=sys.stderr)
        return 2
    why = decide(a.role or "", call if isinstance(call, dict) else {})
    if why:
        print(f"Blocked by the role file (assistants/{a.role}.md): {why}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
